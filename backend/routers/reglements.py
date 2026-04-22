from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
import sqlite3

from database import get_db
from deps import require_roles
from schemas import ReglementCreate, ReglementResponse, PenaltyDefinitionCreate, PenaltyDefinitionResponse

router = APIRouter(prefix="/reglements", tags=["reglements"])

AdminOnly = Annotated[sqlite3.Row, Depends(require_roles("admin"))]


@router.get("/", response_model=list[ReglementResponse])
def list_reglements(db: Annotated[sqlite3.Connection, Depends(get_db)]):
    return [dict(r) for r in db.execute("SELECT * FROM Reglements ORDER BY id").fetchall()]


@router.get("/{reg_id}", response_model=ReglementResponse)
def get_reglement(reg_id: int, db: Annotated[sqlite3.Connection, Depends(get_db)]):
    row = db.execute("SELECT * FROM Reglements WHERE id = ?", (reg_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Reglement nicht gefunden")
    return dict(row)


@router.post("/", response_model=ReglementResponse, status_code=201)
def create_reglement(
    body: ReglementCreate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    cur = db.execute(
        "INSERT INTO Reglements (name, scoring_type, points_formula, runs_per_class, has_training) VALUES (?,?,?,?,?)",
        (body.name, body.scoring_type, body.points_formula, body.runs_per_class, int(body.has_training)),
    )
    db.commit()
    return dict(db.execute("SELECT * FROM Reglements WHERE id = ?", (cur.lastrowid,)).fetchone())


@router.delete("/{reg_id}", status_code=204)
def delete_reglement(
    reg_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    db.execute("DELETE FROM Reglements WHERE id = ?", (reg_id,))
    db.commit()


# ── PenaltyDefinitions ────────────────────────────────────────────────────────

@router.get("/{reg_id}/penalties", response_model=list[PenaltyDefinitionResponse])
def list_penalties(reg_id: int, db: Annotated[sqlite3.Connection, Depends(get_db)]):
    return [dict(r) for r in db.execute(
        "SELECT * FROM PenaltyDefinitions WHERE reglement_id = ? ORDER BY sort_order, id", (reg_id,)
    ).fetchall()]


@router.post("/{reg_id}/penalties", response_model=PenaltyDefinitionResponse, status_code=201)
def create_penalty(
    reg_id: int,
    body: PenaltyDefinitionCreate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    body.reglement_id = reg_id
    cur = db.execute(
        "INSERT INTO PenaltyDefinitions (reglement_id, label, seconds, shortcut_key, sort_order) VALUES (?,?,?,?,?)",
        (reg_id, body.label, body.seconds, body.shortcut_key, body.sort_order),
    )
    db.commit()
    return dict(db.execute("SELECT * FROM PenaltyDefinitions WHERE id = ?", (cur.lastrowid,)).fetchone())


@router.delete("/{reg_id}/penalties/{pen_id}", status_code=204)
def delete_penalty(
    reg_id: int,
    pen_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    db.execute("DELETE FROM PenaltyDefinitions WHERE id = ? AND reglement_id = ?", (pen_id, reg_id))
    db.commit()
