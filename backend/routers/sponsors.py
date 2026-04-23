from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
import sqlite3

from database import get_db
from deps import require_roles
from schemas import SponsorCreate, SponsorUpdate, SponsorResponse

router = APIRouter(prefix="/sponsors", tags=["sponsors"])

AdminOnly = Annotated[sqlite3.Row, Depends(require_roles("admin"))]


@router.get("/", response_model=list[SponsorResponse])
def list_sponsors(db: Annotated[sqlite3.Connection, Depends(get_db)]):
    return [dict(r) for r in db.execute(
        "SELECT * FROM Sponsors ORDER BY sort_order, name"
    ).fetchall()]


@router.post("/", response_model=SponsorResponse, status_code=201)
def create_sponsor(
    body: SponsorCreate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    cur = db.execute(
        "INSERT INTO Sponsors (name, logo_url, website_url, sort_order, is_active) VALUES (?,?,?,?,?)",
        (body.name, body.logo_url, body.website_url, body.sort_order, int(body.is_active)),
    )
    db.commit()
    return dict(db.execute("SELECT * FROM Sponsors WHERE id = ?", (cur.lastrowid,)).fetchone())


@router.patch("/{sponsor_id}", response_model=SponsorResponse)
def update_sponsor(
    sponsor_id: int,
    body: SponsorUpdate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    if not updates:
        raise HTTPException(422, "Keine Felder zum Aktualisieren")
    if "is_active" in updates:
        updates["is_active"] = int(updates["is_active"])
    sets = ", ".join(f"{k} = ?" for k in updates)
    db.execute(f"UPDATE Sponsors SET {sets} WHERE id = ?", (*updates.values(), sponsor_id))
    db.commit()
    row = db.execute("SELECT * FROM Sponsors WHERE id = ?", (sponsor_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Sponsor nicht gefunden")
    return dict(row)


@router.delete("/{sponsor_id}", status_code=204)
def delete_sponsor(
    sponsor_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    db.execute("DELETE FROM Sponsors WHERE id = ?", (sponsor_id,))
    db.commit()
