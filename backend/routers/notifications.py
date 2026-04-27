from __future__ import annotations
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, field_validator

from broadcast import manager
from deps import CurrentUser, require_roles

router = APIRouter(prefix="/notifications", tags=["notifications"])

_NotifUser = Annotated[
    object,
    Depends(require_roles("admin", "zeitnahme", "nennung", "schiedsrichter", "viewer")),
]


class NotificationIn(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nachricht darf nicht leer sein")
        if len(v) > 300:
            raise ValueError("Nachricht zu lang (max. 300 Zeichen)")
        return v


@router.post("", status_code=204)
async def send_notification(
    body: NotificationIn,
    background_tasks: BackgroundTasks,
    user: CurrentUser,
    _: _NotifUser,
):
    background_tasks.add_task(
        manager.broadcast,
        {
            "type": "notification",
            "message": body.message,
            "sender": user["username"],
            "level": "info",
        },
    )
