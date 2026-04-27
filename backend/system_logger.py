"""Thin helper for writing to SystemLog — never raises, so it can be called anywhere."""
from __future__ import annotations
import sqlite3
from database import DB_PATH


def log_event(
    event_type: str,
    *,
    level: str = "info",
    username: str | None = None,
    detail: str | None = None,
    ip: str | None = None,
) -> None:
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute(
            """INSERT INTO SystemLog (level, event_type, username, detail, ip)
               VALUES (?, ?, ?, ?, ?)""",
            (level, event_type, username, detail, ip),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # Logging darf niemals die Anwendung abstürzen lassen
