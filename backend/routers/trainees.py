from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, Optional
import sqlite3

from database import get_db
from deps import require_roles
from schemas import TraineeCreate, TraineeUpdate, TraineeResponse

router = APIRouter(prefix="/trainees", tags=["trainees"])

AdminOnly = Annotated[sqlite3.Row, Depends(require_roles("admin"))]


def _row_with_club(db: sqlite3.Connection, trainee_id: int) -> dict:
    row = db.execute(
        """SELECT t.*, COALESCE(c.short_name, c.name) AS club_name
           FROM Trainees t
           LEFT JOIN Clubs c ON c.id = t.club_id
           WHERE t.id = ?""",
        (trainee_id,),
    ).fetchone()
    if not row:
        raise HTTPException(404, "Trainee nicht gefunden")
    return dict(row)


@router.get("", response_model=list[TraineeResponse])
def list_trainees(
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
    active_only: bool = False,
    search: Optional[str] = None,
):
    query = """
        SELECT t.*, COALESCE(c.short_name, c.name) AS club_name
        FROM Trainees t
        LEFT JOIN Clubs c ON c.id = t.club_id
        WHERE 1=1
    """
    params: list = []
    if active_only:
        query += " AND t.is_active = 1"
    if search:
        query += " AND (t.first_name LIKE ? OR t.last_name LIKE ? OR t.license_number LIKE ?)"
        s = f"%{search}%"
        params += [s, s, s]
    query += " ORDER BY t.last_name, t.first_name"
    rows = db.execute(query, params).fetchall()
    return [dict(r) for r in rows]


@router.post("", response_model=TraineeResponse, status_code=201)
def create_trainee(
    body: TraineeCreate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    cur = db.execute(
        """INSERT INTO Trainees
           (first_name, last_name, birth_year, license_number,
            club_id, kart_number, is_active, notes)
           VALUES (?,?,?,?,?,?,?,?)""",
        (body.first_name, body.last_name, body.birth_year, body.license_number,
         body.club_id, body.kart_number, int(body.is_active), body.notes),
    )
    db.commit()
    return _row_with_club(db, cur.lastrowid)


@router.patch("/{trainee_id}", response_model=TraineeResponse)
def update_trainee(
    trainee_id: int,
    body: TraineeUpdate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(422, "Keine Felder zum Aktualisieren")
    if "is_active" in updates:
        updates["is_active"] = int(updates["is_active"])
    sets = ", ".join(f"{k} = ?" for k in updates)
    db.execute(
        f"UPDATE Trainees SET {sets} WHERE id = ?",
        (*updates.values(), trainee_id),
    )
    db.commit()
    return _row_with_club(db, trainee_id)


@router.delete("/{trainee_id}", status_code=204)
def delete_trainee(
    trainee_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    row = db.execute("SELECT id FROM Trainees WHERE id = ?", (trainee_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Trainee nicht gefunden")
    db.execute("DELETE FROM Trainees WHERE id = ?", (trainee_id,))
    db.commit()
