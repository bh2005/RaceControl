from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
import sqlite3

from database import get_db
from deps import require_roles
from schemas import DisciplineCreate, DisciplineUpdate, DisciplineResponse

router = APIRouter(prefix="/disciplines", tags=["disciplines"])

AdminOnly = Annotated[sqlite3.Row, Depends(require_roles("admin"))]
AnyAuth   = Annotated[sqlite3.Row, Depends(require_roles(
    "admin", "zeitnahme", "schiedsrichter", "nennung", "marshal", "speaker"
))]


@router.get("", response_model=list[DisciplineResponse])
def list_disciplines(
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AnyAuth,
):
    rows = db.execute(
        "SELECT * FROM Disciplines ORDER BY sort_order, name"
    ).fetchall()
    return [dict(r) for r in rows]


@router.post("", response_model=DisciplineResponse, status_code=201)
def create_discipline(
    body: DisciplineCreate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    try:
        cur = db.execute(
            "INSERT INTO Disciplines (name, sort_order, is_active) VALUES (?,?,?)",
            (body.name.strip(), body.sort_order, int(body.is_active)),
        )
        db.commit()
    except Exception:
        raise HTTPException(409, f"Disziplin '{body.name}' existiert bereits")
    return dict(db.execute("SELECT * FROM Disciplines WHERE id = ?", (cur.lastrowid,)).fetchone())


@router.patch("/{discipline_id}", response_model=DisciplineResponse)
def update_discipline(
    discipline_id: int,
    body: DisciplineUpdate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    if not db.execute("SELECT id FROM Disciplines WHERE id = ?", (discipline_id,)).fetchone():
        raise HTTPException(404, "Disziplin nicht gefunden")
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(422, "Keine Felder zum Aktualisieren")
    if "is_active" in updates:
        updates["is_active"] = int(updates["is_active"])
    sets = ", ".join(f"{k} = ?" for k in updates)
    db.execute(f"UPDATE Disciplines SET {sets} WHERE id = ?", (*updates.values(), discipline_id))
    db.commit()
    return dict(db.execute("SELECT * FROM Disciplines WHERE id = ?", (discipline_id,)).fetchone())


@router.delete("/{discipline_id}", status_code=204)
def delete_discipline(
    discipline_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    if not db.execute("SELECT id FROM Disciplines WHERE id = ?", (discipline_id,)).fetchone():
        raise HTTPException(404, "Disziplin nicht gefunden")
    count = db.execute(
        "SELECT COUNT(*) FROM TrainingSessions WHERE discipline_id = ?", (discipline_id,)
    ).fetchone()[0]
    if count > 0:
        raise HTTPException(
            409,
            f"Disziplin wird von {count} Session(s) verwendet und kann nicht gelöscht werden",
        )
    db.execute("DELETE FROM Disciplines WHERE id = ?", (discipline_id,))
    db.commit()
