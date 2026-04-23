from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, Optional
from pydantic import BaseModel
import sqlite3
from datetime import date

from database import get_db

router = APIRouter(prefix="/public", tags=["public"])


class SelfRegisterBody(BaseModel):
    first_name: str
    last_name: str
    birth_year: Optional[int] = None
    club_id: Optional[int] = None
    license_number: Optional[str] = None
    class_id: Optional[int] = None


@router.get("/active-event")
def get_active_event(db: Annotated[sqlite3.Connection, Depends(get_db)]):
    """Returns today's event with classes and clubs. No auth required."""
    today = date.today().isoformat()
    row = db.execute(
        "SELECT * FROM Events WHERE date = ? LIMIT 1", (today,)
    ).fetchone()
    if not row:
        # Fallback: most recent event
        row = db.execute(
            "SELECT * FROM Events ORDER BY date DESC LIMIT 1"
        ).fetchone()
    if not row:
        raise HTTPException(404, "Keine Veranstaltung gefunden")
    event = dict(row)
    classes = [dict(r) for r in db.execute(
        "SELECT id, name, short_name, min_birth_year, max_birth_year FROM Classes "
        "WHERE event_id = ? ORDER BY start_order",
        (event["id"],),
    ).fetchall()]
    clubs = [dict(r) for r in db.execute(
        "SELECT id, name, short_name FROM Clubs ORDER BY name"
    ).fetchall()]
    sponsors = [dict(r) for r in db.execute(
        "SELECT id, name, logo_url, website_url, sort_order FROM Sponsors "
        "WHERE is_active = 1 ORDER BY sort_order, name"
    ).fetchall()]
    return {"event": event, "classes": classes, "clubs": clubs, "sponsors": sponsors}


@router.post("/events/{event_id}/register", status_code=201)
def self_register(
    event_id: int,
    body: SelfRegisterBody,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
):
    """Self-registration for participants. Returns existing entry if duplicate."""
    # Validate event exists
    if not db.execute("SELECT id FROM Events WHERE id = ?", (event_id,)).fetchone():
        raise HTTPException(404, "Veranstaltung nicht gefunden")

    # Duplicate check: by license number
    if body.license_number and body.license_number.strip():
        dup = db.execute(
            """SELECT p.id, p.start_number, p.first_name, p.last_name, p.status,
                      c.name AS class_name
               FROM Participants p
               LEFT JOIN Classes c ON c.id = p.class_id
               WHERE p.event_id = ? AND p.license_number = ?""",
            (event_id, body.license_number.strip()),
        ).fetchone()
        if dup:
            return {"status": "duplicate", "participant": dict(dup)}

    # Duplicate check: by name + birth_year
    if body.birth_year:
        dup = db.execute(
            """SELECT p.id, p.start_number, p.first_name, p.last_name, p.status,
                      c.name AS class_name
               FROM Participants p
               LEFT JOIN Classes c ON c.id = p.class_id
               WHERE p.event_id = ?
                 AND LOWER(p.first_name) = LOWER(?)
                 AND LOWER(p.last_name)  = LOWER(?)
                 AND p.birth_year = ?""",
            (event_id, body.first_name, body.last_name, body.birth_year),
        ).fetchone()
        if dup:
            return {"status": "duplicate", "participant": dict(dup)}

    # Auto-suggest class from birth_year if not chosen
    class_id = body.class_id
    if not class_id and body.birth_year:
        row = db.execute(
            """SELECT id FROM Classes
               WHERE event_id = ?
                 AND (min_birth_year IS NULL OR ? >= min_birth_year)
                 AND (max_birth_year IS NULL OR ? <= max_birth_year)
               ORDER BY start_order LIMIT 1""",
            (event_id, body.birth_year, body.birth_year),
        ).fetchone()
        if row:
            class_id = row["id"]

    # start_number bleibt NULL — wird nach Auslosung vom Nennbüro eingetragen
    cur = db.execute(
        """INSERT INTO Participants
           (event_id, class_id, club_id, start_number, first_name, last_name,
            birth_year, license_number, status)
           VALUES (?,?,?,NULL,?,?,?,?,?)""",
        (
            event_id, class_id, body.club_id,
            body.first_name.strip(), body.last_name.strip(),
            body.birth_year, body.license_number, "registered",
        ),
    )
    db.commit()

    new_p = db.execute(
        """SELECT p.id, p.start_number, p.first_name, p.last_name, p.status,
                  c.name AS class_name
           FROM Participants p
           LEFT JOIN Classes c ON c.id = p.class_id
           WHERE p.id = ?""",
        (cur.lastrowid,),
    ).fetchone()
    return {"status": "created", "participant": dict(new_p)}
