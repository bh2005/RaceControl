from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

from broadcast import manager
from database import get_db
from deps import CurrentUser, require_roles

router = APIRouter(prefix="/marshal", tags=["marshal"])

_MarshalUser = Annotated[
    object,
    Depends(require_roles("marshal", "admin")),
]
_AdminOrSchiri = Annotated[
    object,
    Depends(require_roles("admin", "schiedsrichter")),
]
_ReportsReader = Annotated[
    object,
    Depends(require_roles("admin", "schiedsrichter", "zeitnahme")),
]

DbDep = Annotated[sqlite3.Connection, Depends(get_db)]


class MarshalReportIn(BaseModel):
    penalty_seconds: float
    station:         str
    event_id:        Optional[int]   = None
    class_id:        Optional[int]   = None
    class_name:      Optional[str]   = None
    penalty_id:      Optional[int]   = None
    penalty_label:   Optional[str]   = None

    @field_validator("station")
    @classmethod
    def not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Posten-Bezeichnung darf nicht leer sein")
        return v

    @field_validator("penalty_seconds")
    @classmethod
    def positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Fehlerpunkte müssen größer als 0 sein")
        return v


class MarshalCancelIn(BaseModel):
    ts:        str
    report_id: Optional[int] = None


@router.post("/report")
async def report_penalty(
    body: MarshalReportIn,
    user: CurrentUser,
    _: _MarshalUser,
    db: DbDep,
):
    ts = datetime.now(timezone.utc).isoformat()
    label = body.penalty_label or f"{body.penalty_seconds:.0f}s"

    cur = db.execute(
        """INSERT INTO MarshalReports
           (event_id, ts, station, marshal_user, penalty_seconds, penalty_label, class_id, class_name)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (body.event_id, ts, body.station, user["username"],
         body.penalty_seconds, label, body.class_id, body.class_name),
    )
    db.commit()
    report_id = cur.lastrowid

    await manager.broadcast({
        "type":            "marshal_penalty",
        "report_id":       report_id,
        "penalty_seconds": body.penalty_seconds,
        "penalty_label":   label,
        "penalty_id":      body.penalty_id,
        "station":         body.station,
        "class_id":        body.class_id,
        "class_name":      body.class_name,
        "marshal":         user["username"],
        "ts":              ts,
    })
    return {"ts": ts, "id": report_id}


@router.post("/cancel", status_code=204)
async def cancel_penalty(
    body: MarshalCancelIn,
    user: CurrentUser,
    _: _MarshalUser,
    db: DbDep,
):
    cancelled_at = datetime.now(timezone.utc).isoformat()
    if body.report_id:
        db.execute(
            """UPDATE MarshalReports
               SET cancelled = 1, cancelled_at = ?, cancelled_by = ?
               WHERE id = ?""",
            (cancelled_at, user["username"], body.report_id),
        )
        db.commit()

    await manager.broadcast({
        "type":    "marshal_cancel",
        "ts":      body.ts,
        "marshal": user["username"],
    })


@router.get("/reports")
def list_reports(
    user: CurrentUser,
    _: _ReportsReader,
    db: DbDep,
    event_id: Optional[int] = None,
    cancelled: Optional[int] = None,
    limit: int = 200,
):
    conditions: list[str] = []
    params: list = []
    if event_id is not None:
        conditions.append("event_id = ?")
        params.append(event_id)
    if cancelled is not None:
        conditions.append("cancelled = ?")
        params.append(cancelled)
    query = "SELECT * FROM MarshalReports"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY ts DESC LIMIT ?"
    params.append(limit)
    return [dict(r) for r in db.execute(query, params).fetchall()]
