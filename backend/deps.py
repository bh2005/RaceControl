import sqlite3
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from auth import decode_token
from database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

DbDep = Annotated[sqlite3.Connection, Depends(get_db)]


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbDep,
) -> sqlite3.Row:
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ungültig")
    user = db.execute(
        "SELECT * FROM Users WHERE id = ? AND is_active = 1", (int(payload.get("sub")),)
    ).fetchone()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Benutzer nicht gefunden")
    return user


CurrentUser = Annotated[sqlite3.Row, Depends(get_current_user)]


def require_roles(*roles: str):
    def _check(user: CurrentUser):
        if user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Keine Berechtigung")
        return user
    return _check
