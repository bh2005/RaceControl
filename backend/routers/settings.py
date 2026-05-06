from __future__ import annotations
import datetime
import os
import pathlib
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Annotated, Optional
import secrets
import sqlite3

from database import DB_PATH, get_db
from deps import require_roles

SQLITE_MAGIC = b"SQLite format 3\x00"

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


@router.get("/db/download")
def download_db(
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    """WAL-safe snapshot of the current DB, streamed as a file download."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"racecontrol_{ts}.db"

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name
        dst = sqlite3.connect(tmp_path)
        db.backup(dst)
        dst.close()
        data = pathlib.Path(tmp_path).read_bytes()
    except sqlite3.Error as exc:
        raise HTTPException(500, f"Backup fehlgeschlagen: {exc}")
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/db/restore")
async def restore_db(
    _: AdminOnly,
    file: UploadFile = File(...),
):
    """Replace the running database with an uploaded .db file.

    Validates the SQLite magic bytes and runs integrity_check before
    applying.  The caller should reload the page after a successful restore.
    """
    data = await file.read()

    if len(data) < 16 or not data[:16].startswith(SQLITE_MAGIC):
        raise HTTPException(400, "Ungültige Datei – keine SQLite-Datenbank")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        # Validate integrity of the uploaded file
        try:
            src = sqlite3.connect(tmp_path)
            ok = src.execute("PRAGMA integrity_check").fetchone()
            if ok[0] != "ok":
                raise HTTPException(400, f"Datenbankfehler in der hochgeladenen Datei: {ok[0]}")
        except sqlite3.Error as exc:
            raise HTTPException(400, f"Ungültige Datenbankdatei: {exc}")

        # Restore: copy uploaded DB onto the running DB
        try:
            dst = sqlite3.connect(str(DB_PATH))
            src.backup(dst)
            dst.close()
        except sqlite3.Error as exc:
            raise HTTPException(500, f"Fehler beim Wiederherstellen: {exc}")
        finally:
            src.close()

    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    return {"detail": "Datenbank erfolgreich wiederhergestellt. Seite bitte neu laden."}


@router.post("/timing-key/regenerate")
def regenerate_timing_key(
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOnly,
):
    """Generates a new timing API key and replaces the old one. All connected
    timing devices must be reconfigured with the new key afterwards."""
    new_key = secrets.token_hex(24)
    db.execute("INSERT OR REPLACE INTO Settings (key, value) VALUES ('timing_api_key', ?)", (new_key,))
    db.commit()
    return {"timing_api_key": new_key}
