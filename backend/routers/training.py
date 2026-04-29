from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
import sqlite3

from database import get_db
from deps import require_roles
from broadcast import manager
from schemas import (
    TrainingSessionCreate, TrainingSessionUpdate, TrainingSessionResponse,
    TrainingRunCreate, TrainingRunUpdate, TrainingRunResponse,
    TrainingStandingRow,
)

router = APIRouter(prefix="/training", tags=["training"])

AdminOrZeit = Annotated[sqlite3.Row, Depends(require_roles("admin", "zeitnahme"))]
AdminOnly   = Annotated[sqlite3.Row, Depends(require_roles("admin"))]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _session_or_404(db: sqlite3.Connection, session_id: int) -> sqlite3.Row:
    row = db.execute("SELECT * FROM TrainingSessions WHERE id = ?", (session_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Training-Session nicht gefunden")
    return row


def _run_row(db: sqlite3.Connection, run_id: int) -> dict:
    row = db.execute(
        """SELECT r.*,
                  t.first_name, t.last_name,
                  COALESCE(cl.short_name, cl.name) AS club_name,
                  CASE WHEN r.status = 'valid' AND r.raw_time IS NOT NULL
                       THEN r.raw_time + r.penalty_seconds ELSE NULL END AS total_time
           FROM   TrainingRuns r
           JOIN   Trainees t  ON t.id  = r.trainee_id
           LEFT JOIN Clubs cl ON cl.id = t.club_id
           WHERE  r.id = ?""",
        (run_id,),
    ).fetchone()
    if not row:
        raise HTTPException(404, "Lauf nicht gefunden")
    return dict(row)


# ─── Sessions ─────────────────────────────────────────────────────────────────

@router.get("/sessions", response_model=list[TrainingSessionResponse])
def list_sessions(db: Annotated[sqlite3.Connection, Depends(get_db)], _: AdminOrZeit):
    rows = db.execute(
        "SELECT * FROM TrainingSessions ORDER BY date DESC, id DESC"
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/sessions/active", response_model=TrainingSessionResponse)
def get_active_session(db: Annotated[sqlite3.Connection, Depends(get_db)], _: AdminOrZeit):
    row = db.execute(
        "SELECT * FROM TrainingSessions WHERE status = 'active' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if not row:
        raise HTTPException(404, "Keine aktive Training-Session")
    return dict(row)


@router.get("/sessions/{session_id}", response_model=TrainingSessionResponse)
def get_session(session_id: int, db: Annotated[sqlite3.Connection, Depends(get_db)], _: AdminOrZeit):
    return dict(_session_or_404(db, session_id))


@router.post("/sessions", response_model=TrainingSessionResponse, status_code=201)
def create_session(
    body: TrainingSessionCreate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    user: AdminOnly,
):
    cur = db.execute(
        "INSERT INTO TrainingSessions (name, date, status, notes, created_by) VALUES (?,?,?,?,?)",
        (body.name, body.date, body.status, body.notes, user["id"]),
    )
    db.commit()
    return dict(db.execute("SELECT * FROM TrainingSessions WHERE id = ?", (cur.lastrowid,)).fetchone())


@router.patch("/sessions/{session_id}", response_model=TrainingSessionResponse)
def update_session(
    session_id: int,
    body: TrainingSessionUpdate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    _session_or_404(db, session_id)
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(422, "Keine Felder zum Aktualisieren")
    # Nur eine Session darf aktiv sein
    if updates.get("status") == "active":
        db.execute(
            "UPDATE TrainingSessions SET status = 'finished' WHERE status = 'active' AND id != ?",
            (session_id,),
        )
    sets = ", ".join(f"{k} = ?" for k in updates)
    db.execute(f"UPDATE TrainingSessions SET {sets} WHERE id = ?", (*updates.values(), session_id))
    db.commit()
    return dict(db.execute("SELECT * FROM TrainingSessions WHERE id = ?", (session_id,)).fetchone())


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    _session_or_404(db, session_id)
    db.execute("DELETE FROM TrainingSessions WHERE id = ?", (session_id,))
    db.commit()


# ─── Runs ─────────────────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/runs", response_model=list[TrainingRunResponse])
def list_runs(
    session_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOrZeit,
):
    _session_or_404(db, session_id)
    rows = db.execute(
        """SELECT r.*,
                  t.first_name, t.last_name,
                  COALESCE(cl.short_name, cl.name) AS club_name,
                  CASE WHEN r.status = 'valid' AND r.raw_time IS NOT NULL
                       THEN r.raw_time + r.penalty_seconds ELSE NULL END AS total_time
           FROM   TrainingRuns r
           JOIN   Trainees t  ON t.id  = r.trainee_id
           LEFT JOIN Clubs cl ON cl.id = t.club_id
           WHERE  r.session_id = ?
           ORDER  BY r.created_at DESC""",
        (session_id,),
    ).fetchall()
    return [dict(r) for r in rows]


@router.post("/sessions/{session_id}/runs", response_model=TrainingRunResponse, status_code=201)
async def create_run(
    session_id: int,
    body: TrainingRunCreate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    user: AdminOrZeit,
):
    _session_or_404(db, session_id)
    # Nächste run_number für diesen Trainee in dieser Session
    row = db.execute(
        "SELECT COALESCE(MAX(run_number), 0) + 1 AS next FROM TrainingRuns WHERE session_id = ? AND trainee_id = ?",
        (session_id, body.trainee_id),
    ).fetchone()
    next_run = row["next"]

    # Kart-Nummer: explizit angegeben oder aus Stammdaten
    kart = body.kart_number
    if not kart:
        t = db.execute("SELECT kart_number FROM Trainees WHERE id = ?", (body.trainee_id,)).fetchone()
        kart = t["kart_number"] if t else None

    cur = db.execute(
        """INSERT INTO TrainingRuns
           (session_id, trainee_id, kart_number, run_number, raw_time,
            penalty_seconds, status, source, entered_by)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (session_id, body.trainee_id, kart, next_run,
         body.raw_time, body.penalty_seconds, body.status, body.source, user["id"]),
    )
    db.commit()
    result = _run_row(db, cur.lastrowid)
    # Broadcast an alle Browser-Clients
    await manager.broadcast({"type": "training_run", "session_id": session_id, "run": result})
    return result


@router.patch("/sessions/{session_id}/runs/{run_id}", response_model=TrainingRunResponse)
async def update_run(
    session_id: int,
    run_id: int,
    body: TrainingRunUpdate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOrZeit,
):
    row = db.execute(
        "SELECT id FROM TrainingRuns WHERE id = ? AND session_id = ?", (run_id, session_id)
    ).fetchone()
    if not row:
        raise HTTPException(404, "Lauf nicht gefunden")
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(422, "Keine Felder")
    sets = ", ".join(f"{k} = ?" for k in updates)
    db.execute(f"UPDATE TrainingRuns SET {sets} WHERE id = ?", (*updates.values(), run_id))
    db.commit()
    result = _run_row(db, run_id)
    await manager.broadcast({"type": "training_run_updated", "session_id": session_id, "run": result})
    return result


@router.delete("/sessions/{session_id}/runs/{run_id}", status_code=204)
def delete_run(
    session_id: int,
    run_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOrZeit,
):
    row = db.execute(
        "SELECT id FROM TrainingRuns WHERE id = ? AND session_id = ?", (run_id, session_id)
    ).fetchone()
    if not row:
        raise HTTPException(404, "Lauf nicht gefunden")
    db.execute("DELETE FROM TrainingRuns WHERE id = ?", (run_id,))
    db.commit()


# ─── Standings ────────────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/standings", response_model=list[TrainingStandingRow])
def get_standings(
    session_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOrZeit,
):
    _session_or_404(db, session_id)
    rows = db.execute(
        """SELECT *,
                  RANK() OVER (ORDER BY best_time ASC NULLS LAST) AS rank
           FROM   v_training_standings
           WHERE  session_id = ?
           ORDER  BY best_time ASC NULLS LAST""",
        (session_id,),
    ).fetchall()
    return [dict(r) for r in rows]
