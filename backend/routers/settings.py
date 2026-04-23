from __future__ import annotations
from fastapi import APIRouter, Depends
from typing import Annotated, Optional
from pydantic import BaseModel
import sqlite3

from database import get_db
from deps import require_roles

router = APIRouter(prefix="/settings", tags=["settings"])

AdminOnly = Annotated[sqlite3.Row, Depends(require_roles("admin"))]


class SettingsUpdate(BaseModel):
    organizer_name: Optional[str] = None
    organizer_address: Optional[str] = None
    insurance_notice: Optional[str] = None
    parent_consent_text: Optional[str] = None


@router.get("/")
def get_settings(db: Annotated[sqlite3.Connection, Depends(get_db)]):
    rows = db.execute("SELECT key, value FROM Settings").fetchall()
    return {r["key"]: r["value"] for r in rows}


@router.patch("/")
def update_settings(
    body: SettingsUpdate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    updates = body.model_dump(exclude_none=True)
    for k, v in updates.items():
        db.execute("INSERT OR REPLACE INTO Settings (key, value) VALUES (?, ?)", (k, v))
    db.commit()
    rows = db.execute("SELECT key, value FROM Settings").fetchall()
    return {r["key"]: r["value"] for r in rows}
