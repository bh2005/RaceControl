from __future__ import annotations
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from typing import Annotated, Optional
import sqlite3

from broadcast import manager
from database import get_db
from deps import require_roles
from schemas import EventCreate, EventUpdate, EventResponse, ClassCreate, ClassUpdate, ClassResponse

router = APIRouter(prefix="/events", tags=["events"])

AdminOnly = Annotated[sqlite3.Row, Depends(require_roles("admin"))]
AdminOrSchiri = Annotated[sqlite3.Row, Depends(require_roles("admin", "schiedsrichter"))]


@router.get("/", response_model=list[EventResponse])
def list_events(db: Annotated[sqlite3.Connection, Depends(get_db)]):
    return [dict(r) for r in db.execute("SELECT * FROM Events ORDER BY date DESC").fetchall()]


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Annotated[sqlite3.Connection, Depends(get_db)]):
    row = db.execute("SELECT * FROM Events WHERE id = ?", (event_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Veranstaltung nicht gefunden")
    return dict(row)


@router.post("/", response_model=EventResponse, status_code=201)
def create_event(
    body: EventCreate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    cur = db.execute(
        "INSERT INTO Events (name, date, location, reglement_id, status) VALUES (?,?,?,?,?)",
        (body.name, body.date, body.location, body.reglement_id, body.status),
    )
    db.commit()
    return dict(db.execute("SELECT * FROM Events WHERE id = ?", (cur.lastrowid,)).fetchone())


@router.patch("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    body: EventUpdate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    if not updates:
        raise HTTPException(422, "Keine Felder zum Aktualisieren")
    sets = ", ".join(f"{k} = ?" for k in updates)
    db.execute(f"UPDATE Events SET {sets} WHERE id = ?", (*updates.values(), event_id))
    db.commit()
    return dict(db.execute("SELECT * FROM Events WHERE id = ?", (event_id,)).fetchone())


@router.delete("/{event_id}", status_code=204)
def delete_event(
    event_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    db.execute("DELETE FROM Events WHERE id = ?", (event_id,))
    db.commit()


# ── Classes ───────────────────────────────────────────────────────────────────

@router.get("/{event_id}/classes", response_model=list[ClassResponse])
def list_classes(event_id: int, db: Annotated[sqlite3.Connection, Depends(get_db)]):
    return [dict(r) for r in db.execute(
        "SELECT * FROM Classes WHERE event_id = ? ORDER BY start_order", (event_id,)
    ).fetchall()]


@router.post("/{event_id}/classes", response_model=ClassResponse, status_code=201)
def create_class(
    event_id: int,
    body: ClassCreate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    body.event_id = event_id
    cur = db.execute(
        """INSERT INTO Classes (event_id, reglement_id, name, short_name,
           min_birth_year, max_birth_year, run_status, start_order)
           VALUES (?,?,?,?,?,?,?,?)""",
        (event_id, body.reglement_id, body.name, body.short_name,
         body.min_birth_year, body.max_birth_year, body.run_status, body.start_order),
    )
    db.commit()
    return dict(db.execute("SELECT * FROM Classes WHERE id = ?", (cur.lastrowid,)).fetchone())


@router.patch("/{event_id}/classes/{class_id}", response_model=ClassResponse)
def update_class(
    event_id: int,
    class_id: int,
    body: ClassUpdate,
    background_tasks: BackgroundTasks,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOrSchiri,
):
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    if not updates:
        raise HTTPException(422, "Keine Felder zum Aktualisieren")
    sets = ", ".join(f"{k} = ?" for k in updates)
    db.execute(
        f"UPDATE Classes SET {sets} WHERE id = ? AND event_id = ?",
        (*updates.values(), class_id, event_id),
    )
    db.commit()
    background_tasks.add_task(
        manager.broadcast,
        {"type": "classes", "event_id": event_id, "class_id": class_id},
    )
    return dict(db.execute("SELECT * FROM Classes WHERE id = ?", (class_id,)).fetchone())
