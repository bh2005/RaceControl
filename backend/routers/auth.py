from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from auth import verify_password, create_access_token
from database import get_db
from schemas import TokenResponse
import sqlite3

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[sqlite3.Connection, Depends(get_db)],
):
    user = db.execute(
        "SELECT * FROM Users WHERE username = ? AND is_active = 1", (form.username,)
    ).fetchone()
    if not user or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültige Zugangsdaten")
    token = create_access_token({"sub": str(user["id"]), "role": user["role"]})
    return TokenResponse(access_token=token)
