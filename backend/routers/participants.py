from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, Optional
import sqlite3

from database import get_db
from deps import require_roles
from schemas import ParticipantCreate, ParticipantUpdate, ParticipantResponse

router = APIRouter(prefix="/events/{event_id}/participants", tags=["participants"])

AdminOrNennung = Annotated[sqlite3.Row, Depends(require_roles("admin", "nennung"))]


def _suggest_class(db: sqlite3.Connection, event_id: int, birth_year: Optional[int]) -> Optional[int]:
    """Return class_id matching birth_year for the event, or None."""
    if not birth_year:
        return None
    row = db.execute(
        """SELECT id FROM Classes
           WHERE event_id = ?
             AND (min_birth_year IS NULL OR birth_year >= min_birth_year)
             AND (max_birth_year IS NULL OR birth_year <= max_birth_year)
           ORDER BY start_order LIMIT 1""",
        (event_id, ),
    ).fetchone()
    # SQLite does not support named parameters in subqueries — use python-side replacement:
    row = db.execute(
        """SELECT id FROM Classes
           WHERE event_id = ?
             AND (min_birth_year IS NULL OR ? >= min_birth_year)
             AND (max_birth_year IS NULL OR ? <= max_birth_year)
           ORDER BY start_order LIMIT 1""",
        (event_id, birth_year, birth_year),
    ).fetchone()
    return row["id"] if row else None


@router.get("/", response_model=list[ParticipantResponse])
def list_participants(event_id: int, db: Annotated[sqlite3.Connection, Depends(get_db)]):
    return [dict(r) for r in db.execute(
        "SELECT * FROM Participants WHERE event_id = ? ORDER BY start_number", (event_id,)
    ).fetchall()]


@router.post("/", response_model=ParticipantResponse, status_code=201)
def create_participant(
    event_id: int,
    body: ParticipantCreate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOrNennung,
):
    body.event_id = event_id
    if body.class_id is None:
        body.class_id = _suggest_class(db, event_id, body.birth_year)
    try:
        cur = db.execute(
            """INSERT INTO Participants
               (event_id, class_id, start_number, first_name, last_name,
                birth_year, club, license_number, status)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (event_id, body.class_id, body.start_number, body.first_name, body.last_name,
             body.birth_year, body.club, body.license_number, body.status),
        )
        db.commit()
        return dict(db.execute("SELECT * FROM Participants WHERE id = ?", (cur.lastrowid,)).fetchone())
    except Exception:
        raise HTTPException(409, f"Startnummer {body.start_number} bereits vergeben")


@router.patch("/{participant_id}", response_model=ParticipantResponse)
def update_participant(
    event_id: int,
    participant_id: int,
    body: ParticipantUpdate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOrNennung,
):
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    if not updates:
        raise HTTPException(422, "Keine Felder zum Aktualisieren")
    sets = ", ".join(f"{k} = ?" for k in updates)
    db.execute(
        f"UPDATE Participants SET {sets} WHERE id = ? AND event_id = ?",
        (*updates.values(), participant_id, event_id),
    )
    db.commit()
    return dict(db.execute("SELECT * FROM Participants WHERE id = ?", (participant_id,)).fetchone())


@router.get("/suggest-class/{birth_year}")
def suggest_class(
    event_id: int,
    birth_year: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
):
    class_id = _suggest_class(db, event_id, birth_year)
    if not class_id:
        raise HTTPException(404, "Keine passende Klasse gefunden")
    row = db.execute("SELECT * FROM Classes WHERE id = ?", (class_id,)).fetchone()
    return {"class_id": class_id, "class_name": row["name"]}
