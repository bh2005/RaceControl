from __future__ import annotations
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from typing import Annotated, Optional
import sqlite3

from broadcast import manager
from database import get_db
from deps import require_roles, get_current_user, CurrentUser
from schemas import (
    RaceResultCreate, RaceResultUpdate, RaceResultResponse,
    RunPenaltyCreate, RunPenaltyResponse,
    RunResultView, StandingRow,
)

router = APIRouter(prefix="/events/{event_id}", tags=["results"])

ZeitnahmeOrAbove = Annotated[sqlite3.Row, Depends(require_roles("admin", "schiedsrichter", "zeitnahme"))]
SchiriOrAdmin = Annotated[sqlite3.Row, Depends(require_roles("admin", "schiedsrichter"))]


def _get_class_row(db: sqlite3.Connection, class_id: int) -> sqlite3.Row:
    row = db.execute("SELECT run_status, is_exhibition FROM Classes WHERE id = ?", (class_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Klasse nicht gefunden")
    return row


def _require_class_running(db: sqlite3.Connection, class_id: int) -> None:
    """Zeitnahme darf nur buchen wenn Klasse läuft (Ausnahme: Vorstarter/Exhibition)."""
    cls = _get_class_row(db, class_id)
    if cls["is_exhibition"]:
        return
    if cls["run_status"] not in ("running", "paused"):
        raise HTTPException(
            409,
            "Klasse läuft nicht – Zeiteingabe erst nach Klassenstart möglich",
        )


def _require_class_not_official(db: sqlite3.Connection, class_id: int) -> None:
    """Korrekturen gesperrt sobald die Klasse offiziell freigegeben wurde."""
    cls = _get_class_row(db, class_id)
    if cls["run_status"] == "official":
        raise HTTPException(
            409,
            "Klasse ist offiziell freigegeben – keine Korrekturen mehr möglich",
        )


# ── RaceResults ───────────────────────────────────────────────────────────────

@router.get("/results", response_model=list[RaceResultResponse])
def list_results(
    event_id: int,
    class_id: Optional[int] = None,
    run_number: Optional[int] = None,
    db: Annotated[sqlite3.Connection, Depends(get_db)] = ...,
):
    query = "SELECT * FROM RaceResults WHERE event_id = ?"
    params: list = [event_id]
    if class_id is not None:
        query += " AND class_id = ?"
        params.append(class_id)
    if run_number is not None:
        query += " AND run_number = ?"
        params.append(run_number)
    query += " ORDER BY class_id, run_number, participant_id"
    return [dict(r) for r in db.execute(query, params).fetchall()]


@router.post("/results", response_model=RaceResultResponse, status_code=201)
def create_result(
    event_id: int,
    body: RaceResultCreate,
    background_tasks: BackgroundTasks,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    user: ZeitnahmeOrAbove,
):
    body.event_id = event_id
    _require_class_running(db, body.class_id)
    try:
        cur = db.execute(
            """INSERT INTO RaceResults
               (event_id, participant_id, class_id, run_number, raw_time, status, entered_by)
               VALUES (?,?,?,?,?,?,?)""",
            (event_id, body.participant_id, body.class_id, body.run_number,
             body.raw_time, body.status, user["id"]),
        )
        db.commit()
        background_tasks.add_task(
            manager.broadcast,
            {"type": "results", "event_id": event_id, "class_id": body.class_id},
        )
        return dict(db.execute("SELECT * FROM RaceResults WHERE id = ?", (cur.lastrowid,)).fetchone())
    except Exception:
        raise HTTPException(409, "Ergebnis für diesen Fahrer/Lauf bereits vorhanden")


@router.patch("/results/{result_id}", response_model=RaceResultResponse)
def update_result(
    event_id: int,
    result_id: int,
    body: RaceResultUpdate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    user: SchiriOrAdmin,
):
    existing = db.execute("SELECT * FROM RaceResults WHERE id = ? AND event_id = ?", (result_id, event_id)).fetchone()
    if not existing:
        raise HTTPException(404, "Ergebnis nicht gefunden")
    _require_class_not_official(db, existing["class_id"])

    updates: dict = {}
    if body.raw_time is not None:
        updates["raw_time"] = body.raw_time
    if body.status is not None:
        updates["status"] = body.status
    if body.is_official is not None:
        updates["is_official"] = int(body.is_official)

    if updates:
        sets = ", ".join(f"{k} = ?" for k in updates)
        db.execute(f"UPDATE RaceResults SET {sets} WHERE id = ?", (*updates.values(), result_id))

    # Audit each changed field
    for field, new_val in updates.items():
        old_val = existing[field]
        if old_val != new_val:
            db.execute(
                """INSERT INTO AuditLog (result_id, user_id, field_changed, old_value, new_value, reason)
                   VALUES (?,?,?,?,?,?)""",
                (result_id, user["id"], field, str(old_val), str(new_val), body.reason),
            )

    db.commit()
    return dict(db.execute("SELECT * FROM RaceResults WHERE id = ?", (result_id,)).fetchone())


# ── Penalties ─────────────────────────────────────────────────────────────────

@router.get("/results/{result_id}/penalties", response_model=list[RunPenaltyResponse])
def list_penalties(
    event_id: int,
    result_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
):
    return [dict(r) for r in db.execute(
        "SELECT * FROM RunPenalties WHERE result_id = ?", (result_id,)
    ).fetchall()]


@router.post("/results/{result_id}/penalties", response_model=RunPenaltyResponse, status_code=201)
def add_penalty(
    event_id: int,
    result_id: int,
    body: RunPenaltyCreate,
    background_tasks: BackgroundTasks,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    user: ZeitnahmeOrAbove,
):
    body.result_id = result_id
    cur = db.execute(
        "INSERT INTO RunPenalties (result_id, penalty_definition_id, count, entered_by) VALUES (?,?,?,?)",
        (result_id, body.penalty_definition_id, body.count, user["id"]),
    )
    db.commit()
    row = db.execute("SELECT class_id FROM RaceResults WHERE id = ?", (result_id,)).fetchone()
    background_tasks.add_task(
        manager.broadcast,
        {"type": "results", "event_id": event_id, "class_id": row["class_id"] if row else None},
    )
    return dict(db.execute("SELECT * FROM RunPenalties WHERE id = ?", (cur.lastrowid,)).fetchone())


@router.delete("/results/{result_id}/penalties/{penalty_id}", status_code=204)
def delete_penalty(
    event_id: int,
    result_id: int,
    penalty_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: SchiriOrAdmin,
):
    row = db.execute("SELECT class_id FROM RaceResults WHERE id = ?", (result_id,)).fetchone()
    if row:
        _require_class_not_official(db, row["class_id"])
    db.execute("DELETE FROM RunPenalties WHERE id = ? AND result_id = ?", (penalty_id, result_id))
    db.commit()


# ── Audit-Log ─────────────────────────────────────────────────────────────────

@router.get("/audit-log")
def get_audit_log(
    event_id: int,
    class_id: Optional[int] = None,
    limit: int = 100,
    db: Annotated[sqlite3.Connection, Depends(get_db)] = ...,
):
    query = """
        SELECT
            al.id,
            al.result_id,
            al.field_changed,
            al.old_value,
            al.new_value,
            al.reason,
            al.timestamp,
            COALESCE(u.display_name, u.username) AS user_name,
            p.start_number,
            p.first_name || ' ' || p.last_name   AS driver_name,
            r.class_id,
            r.run_number
        FROM AuditLog al
        JOIN  RaceResults  r ON r.id  = al.result_id
        LEFT JOIN Users       u ON u.id  = al.user_id
        LEFT JOIN Participants p ON p.id = r.participant_id
        WHERE r.event_id = ?
    """
    params: list = [event_id]
    if class_id is not None:
        query += " AND r.class_id = ?"
        params.append(class_id)
    query += " ORDER BY al.timestamp DESC LIMIT ?"
    params.append(limit)
    return [dict(r) for r in db.execute(query, params).fetchall()]


# ── Views ─────────────────────────────────────────────────────────────────────

@router.get("/run-results", response_model=list[RunResultView])
def run_results(
    event_id: int,
    class_id: Optional[int] = None,
    run_number: Optional[int] = None,
    db: Annotated[sqlite3.Connection, Depends(get_db)] = ...,
):
    query = "SELECT * FROM v_run_results WHERE event_id = ?"
    params: list = [event_id]
    if class_id is not None:
        query += " AND class_id = ?"
        params.append(class_id)
    if run_number is not None:
        query += " AND run_number = ?"
        params.append(run_number)
    query += " ORDER BY class_id, run_number, total_time NULLS LAST"
    return [dict(r) for r in db.execute(query, params).fetchall()]


@router.get("/standings", response_model=list[StandingRow])
def standings(
    event_id: int,
    class_id: Optional[int] = None,
    db: Annotated[sqlite3.Connection, Depends(get_db)] = ...,
):
    query = "SELECT * FROM v_class_standings_sum_all WHERE event_id = ?"
    params: list = [event_id]
    if class_id is not None:
        query += " AND class_id = ?"
        params.append(class_id)
    query += " ORDER BY class_id, rank"
    return [dict(r) for r in db.execute(query, params).fetchall()]
