from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, Optional
import sqlite3

from database import get_db
from deps import require_roles
from schemas import StartScheduleCreate, StartScheduleUpdate, StartScheduleResponse

router = APIRouter(prefix="/events", tags=["downhill"])

AdminOrZeit = Annotated[sqlite3.Row, Depends(require_roles("admin", "zeitnahme"))]
AdminOnly   = Annotated[sqlite3.Row, Depends(require_roles("admin"))]


def _schedule_row(db: sqlite3.Connection, schedule_id: int, event_id: int) -> dict:
    row = db.execute(
        """SELECT ss.*, p.first_name, p.last_name, p.start_number,
                  CASE WHEN rr.id IS NOT NULL THEN 1 ELSE 0 END AS finished
           FROM   StartSchedule ss
           JOIN   Participants p ON p.id = ss.participant_id
           LEFT JOIN RaceResults rr
                  ON rr.participant_id = ss.participant_id
                 AND rr.event_id = ss.event_id
                 AND rr.run_number >= 1
           WHERE  ss.id = ? AND ss.event_id = ?""",
        (schedule_id, event_id),
    ).fetchone()
    if not row:
        raise HTTPException(404, "Startplan-Eintrag nicht gefunden")
    return {**dict(row), "finished": bool(row["finished"])}


def _event_is_downhill(db: sqlite3.Connection, event_id: int) -> None:
    row = db.execute("SELECT timing_mode FROM Events WHERE id = ?", (event_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Veranstaltung nicht gefunden")
    if row["timing_mode"] != "downhill":
        raise HTTPException(400, "Veranstaltung ist kein Downhill-Event (timing_mode != downhill)")


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("/{event_id}/schedule", response_model=list[StartScheduleResponse])
def list_schedule(
    event_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOrZeit,
    lane: Optional[str] = None,
):
    query = """
        SELECT ss.*, p.first_name, p.last_name, p.start_number,
               CASE WHEN rr.id IS NOT NULL THEN 1 ELSE 0 END AS finished
        FROM   StartSchedule ss
        JOIN   Participants p ON p.id = ss.participant_id
        LEFT JOIN RaceResults rr
               ON rr.participant_id = ss.participant_id
              AND rr.event_id = ss.event_id
              AND rr.run_number >= 1
        WHERE  ss.event_id = ?
    """
    params: list = [event_id]
    if lane:
        query += " AND ss.lane = ?"
        params.append(lane)
    query += " ORDER BY ss.lane, ss.scheduled_start"
    rows = db.execute(query, params).fetchall()
    return [{**dict(r), "finished": bool(r["finished"])} for r in rows]


# ── Next unfinished (für Starter-View / Zeitnahme-Anzeige) ────────────────────

@router.get("/{event_id}/schedule/next", response_model=Optional[StartScheduleResponse])
def next_starter(
    event_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOrZeit,
    lane: Optional[str] = None,
):
    """Nächster unbeendeter Starter. lane=None → Single-Lane (alle Einträge ohne Spurfilter)."""
    row = db.execute(
        """SELECT ss.*, p.first_name, p.last_name, p.start_number, 0 AS finished
           FROM   StartSchedule ss
           JOIN   Participants p ON p.id = ss.participant_id
           LEFT JOIN RaceResults rr
                  ON rr.participant_id = ss.participant_id
                 AND rr.event_id = ss.event_id
                 AND rr.run_number >= 1
           WHERE  ss.event_id = ?
             AND  (ss.lane IS NULL OR ? IS NULL OR ss.lane = ?)
             AND  rr.id IS NULL
           ORDER  BY ss.scheduled_start
           LIMIT  1""",
        (event_id, lane, lane),
    ).fetchone()
    return dict(row) if row else None


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("/{event_id}/schedule", response_model=StartScheduleResponse, status_code=201)
def create_schedule_entry(
    event_id: int,
    body: StartScheduleCreate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    _event_is_downhill(db, event_id)
    part = db.execute(
        "SELECT id FROM Participants WHERE id = ? AND event_id = ?",
        (body.participant_id, event_id),
    ).fetchone()
    if not part:
        raise HTTPException(404, "Teilnehmer nicht zu dieser Veranstaltung gefunden")
    try:
        cur = db.execute(
            "INSERT INTO StartSchedule (event_id, participant_id, lane, scheduled_start) VALUES (?,?,?,?)",
            (event_id, body.participant_id, body.lane, body.scheduled_start),
        )
        db.commit()
    except Exception:
        raise HTTPException(409, "Teilnehmer ist bereits im Startplan eingetragen")
    return _schedule_row(db, cur.lastrowid, event_id)


# ── Bulk import ───────────────────────────────────────────────────────────────

@router.post("/{event_id}/schedule/bulk", response_model=list[StartScheduleResponse], status_code=201)
def bulk_import_schedule(
    event_id: int,
    body: list[StartScheduleCreate],
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    _event_is_downhill(db, event_id)
    created_ids: list[int] = []
    for entry in body:
        cur = db.execute(
            """INSERT INTO StartSchedule (event_id, participant_id, lane, scheduled_start)
               VALUES (?,?,?,?)
               ON CONFLICT(event_id, participant_id)
               DO UPDATE SET lane = excluded.lane, scheduled_start = excluded.scheduled_start""",
            (event_id, entry.participant_id, entry.lane, entry.scheduled_start),
        )
        created_ids.append(
            cur.lastrowid
            or db.execute(
                "SELECT id FROM StartSchedule WHERE event_id = ? AND participant_id = ?",
                (event_id, entry.participant_id),
            ).fetchone()["id"]
        )
    db.commit()
    return [_schedule_row(db, sid, event_id) for sid in created_ids]


# ── Update ────────────────────────────────────────────────────────────────────

@router.patch("/{event_id}/schedule/{schedule_id}", response_model=StartScheduleResponse)
def update_schedule_entry(
    event_id: int,
    schedule_id: int,
    body: StartScheduleUpdate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(422, "Keine Felder zum Aktualisieren")
    row = db.execute(
        "SELECT id FROM StartSchedule WHERE id = ? AND event_id = ?",
        (schedule_id, event_id),
    ).fetchone()
    if not row:
        raise HTTPException(404, "Startplan-Eintrag nicht gefunden")
    sets = ", ".join(f"{k} = ?" for k in updates)
    db.execute(f"UPDATE StartSchedule SET {sets} WHERE id = ?", (*updates.values(), schedule_id))
    db.commit()
    return _schedule_row(db, schedule_id, event_id)


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/{event_id}/schedule/{schedule_id}", status_code=204)
def delete_schedule_entry(
    event_id: int,
    schedule_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    row = db.execute(
        "SELECT id FROM StartSchedule WHERE id = ? AND event_id = ?",
        (schedule_id, event_id),
    ).fetchone()
    if not row:
        raise HTTPException(404, "Startplan-Eintrag nicht gefunden")
    db.execute("DELETE FROM StartSchedule WHERE id = ?", (schedule_id,))
    db.commit()
