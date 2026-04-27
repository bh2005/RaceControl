from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from auth import verify_password, create_access_token
from database import get_db
from schemas import TokenResponse
from system_logger import log_event
import sqlite3

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[sqlite3.Connection, Depends(get_db)],
):
    ip = _client_ip(request)
    user = db.execute(
        "SELECT * FROM Users WHERE username = ? AND is_active = 1", (form.username,)
    ).fetchone()
    if not user or not verify_password(form.password, user["password_hash"]):
        log_event(
            "login_fail",
            level="warn",
            username=form.username,
            detail="Ungültige Zugangsdaten",
            ip=ip,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültige Zugangsdaten")

    log_event(
        "login_ok",
        username=user["username"],
        detail=f"Rolle: {user['role']}",
        ip=ip,
    )
    token = create_access_token({"sub": str(user["id"]), "role": user["role"]})
    return TokenResponse(access_token=token)
