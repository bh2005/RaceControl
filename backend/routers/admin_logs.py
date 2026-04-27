from __future__ import annotations
import sqlite3
from typing import Annotated, Optional

from fastapi import APIRouter, Depends

from database import get_db
from deps import CurrentUser, require_roles

router = APIRouter(prefix="/admin", tags=["admin"])

_AdminOnly = Annotated[object, Depends(require_roles("admin"))]
DbDep = Annotated[sqlite3.Connection, Depends(get_db)]


@router.get("/system-log")
def get_system_log(
    _user: CurrentUser,
    __: _AdminOnly,
    db: DbDep,
    level: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 300,
):
    query = "SELECT * FROM SystemLog"
    params: list = []
    conditions: list[str] = []
    if level:
        conditions.append("level = ?")
        params.append(level)
    if event_type:
        conditions.append("event_type = ?")
        params.append(event_type)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY ts DESC LIMIT ?"
    params.append(limit)
    return [dict(r) for r in db.execute(query, params).fetchall()]
