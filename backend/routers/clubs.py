from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
import sqlite3

from database import get_db
from deps import require_roles
from schemas import ClubCreate, ClubUpdate, ClubResponse

router = APIRouter(prefix="/clubs", tags=["clubs"])

AdminOnly = Annotated[sqlite3.Row, Depends(require_roles("admin"))]


@router.get("/", response_model=list[ClubResponse])
def list_clubs(db: Annotated[sqlite3.Connection, Depends(get_db)]):
    return [dict(r) for r in db.execute(
        "SELECT * FROM Clubs ORDER BY name"
    ).fetchall()]


@router.post("/", response_model=ClubResponse, status_code=201)
def create_club(
    body: ClubCreate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    try:
        cur = db.execute(
            "INSERT INTO Clubs (name, short_name, city) VALUES (?,?,?)",
            (body.name, body.short_name, body.city),
        )
        db.commit()
        return dict(db.execute("SELECT * FROM Clubs WHERE id = ?", (cur.lastrowid,)).fetchone())
    except Exception:
        raise HTTPException(409, "Vereinsname bereits vorhanden")


@router.patch("/{club_id}", response_model=ClubResponse)
def update_club(
    club_id: int,
    body: ClubUpdate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    if not updates:
        raise HTTPException(422, "Keine Felder zum Aktualisieren")
    sets = ", ".join(f"{k} = ?" for k in updates)
    db.execute(f"UPDATE Clubs SET {sets} WHERE id = ?", (*updates.values(), club_id))
    db.commit()
    return dict(db.execute("SELECT * FROM Clubs WHERE id = ?", (club_id,)).fetchone())


@router.delete("/{club_id}", status_code=204)
def delete_club(
    club_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    # Teilnehmer behalten club_id = NULL (ON DELETE SET NULL im Schema)
    db.execute("DELETE FROM Clubs WHERE id = ?", (club_id,))
    db.commit()
