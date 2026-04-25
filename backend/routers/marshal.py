from __future__ import annotations
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, field_validator

from broadcast import manager
from deps import CurrentUser, require_roles

router = APIRouter(prefix="/marshal", tags=["marshal"])

_MarshalUser = Annotated[
    object,
    Depends(require_roles("marshal", "admin")),
]


class MarshalReportIn(BaseModel):
    penalty_seconds: float
    station:         str
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


@router.post("/report", status_code=204)
async def report_penalty(
    body: MarshalReportIn,
    background_tasks: BackgroundTasks,
    user: CurrentUser,
    _: _MarshalUser,
):
    background_tasks.add_task(
        manager.broadcast,
        {
            "type":            "marshal_penalty",
            "penalty_seconds": body.penalty_seconds,
            "penalty_label":   body.penalty_label or f"{body.penalty_seconds:.0f}s",
            "penalty_id":      body.penalty_id,
            "station":         body.station,
            "class_id":        body.class_id,
            "class_name":      body.class_name,
            "marshal":         user["username"],
            "ts":              datetime.now(timezone.utc).isoformat(),
        },
    )
