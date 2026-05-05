from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
import sqlite3

from auth import hash_password, verify_password
from database import get_db
from deps import require_roles, CurrentUser
from schemas import UserCreate, UserResponse, PasswordChangeAdmin, PasswordChangeSelf
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


@router.patch("/me/password", status_code=204)
def change_own_password(
    body: PasswordChangeSelf,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    user: CurrentUser,
):
    if not verify_password(body.current_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Aktuelles Passwort falsch")
    db.execute(
        "UPDATE Users SET password_hash = ? WHERE id = ?",
        (hash_password(body.new_password), user["id"]),
    )
    db.commit()
    log_event(
        "password_changed",
        username=user["username"],
        detail="Eigenes Passwort geändert",
    )


@router.patch("/{user_id}/password", status_code=204)
def change_user_password(
    user_id: int,
    body: PasswordChangeAdmin,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    actor: AdminOnly,
):
    row = db.execute("SELECT * FROM Users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    db.execute(
        "UPDATE Users SET password_hash = ? WHERE id = ?",
        (hash_password(body.new_password), user_id),
    )
    db.commit()
    log_event(
        "password_reset",
        username=row["username"],
        detail=f"Passwort geändert von {actor['username']}",
    )
