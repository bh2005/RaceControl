from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, Optional
import sqlite3

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
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    user: ZeitnahmeOrAbove,
):
    body.event_id = event_id
    try:
        cur = db.execute(
            """INSERT INTO RaceResults
               (event_id, participant_id, class_id, run_number, raw_time, status, entered_by)
               VALUES (?,?,?,?,?,?,?)""",
            (event_id, body.participant_id, body.class_id, body.run_number,
             body.raw_time, body.status, user["id"]),
        )
        db.commit()
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
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    user: ZeitnahmeOrAbove,
):
    body.result_id = result_id
    cur = db.execute(
        "INSERT INTO RunPenalties (result_id, penalty_definition_id, count, entered_by) VALUES (?,?,?,?)",
        (result_id, body.penalty_definition_id, body.count, user["id"]),
    )
    db.commit()
    return dict(db.execute("SELECT * FROM RunPenalties WHERE id = ?", (cur.lastrowid,)).fetchone())


@router.delete("/results/{result_id}/penalties/{penalty_id}", status_code=204)
def delete_penalty(
    event_id: int,
    result_id: int,
    penalty_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: SchiriOrAdmin,
):
    db.execute("DELETE FROM RunPenalties WHERE id = ? AND result_id = ?", (penalty_id, result_id))
    db.commit()


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
