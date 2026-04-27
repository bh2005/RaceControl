from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
import sqlite3

from auth import hash_password
from database import get_db
from deps import require_roles, CurrentUser
from schemas import UserCreate, UserResponse
from system_logger import log_event

router = APIRouter(prefix="/users", tags=["users"])

AdminOnly = Annotated[sqlite3.Row, Depends(require_roles("admin"))]


@router.get("/", response_model=list[UserResponse])
def list_users(db: Annotated[sqlite3.Connection, Depends(get_db)], _: AdminOnly):
    rows = db.execute("SELECT * FROM Users ORDER BY id").fetchall()
    return [dict(r) for r in rows]


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    body: UserCreate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    actor: AdminOnly,
):
    try:
        cur = db.execute(
            "INSERT INTO Users (username, password_hash, role, display_name) VALUES (?,?,?,?)",
            (body.username, hash_password(body.password), body.role, body.display_name),
        )
        db.commit()
        row = db.execute("SELECT * FROM Users WHERE id = ?", (cur.lastrowid,)).fetchone()
        log_event(
            "user_created",
            username=body.username,
            detail=f"Rolle: {body.role} — angelegt von {actor['username']}",
        )
        return dict(row)
    except Exception:
        raise HTTPException(status_code=409, detail="Benutzername bereits vergeben")


@router.delete("/{user_id}", status_code=204)
def deactivate_user(
    user_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    db.execute("UPDATE Users SET is_active = 0 WHERE id = ?", (user_id,))
    db.commit()
