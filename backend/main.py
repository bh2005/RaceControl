import os
import pathlib
import secrets
import sqlite3
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_db, DB_PATH
from broadcast import manager
from system_logger import log_event
from routers import auth, users, reglements, events, participants, results, teams, clubs, public, sponsors, settings, notifications, assets as assets_router, marshal as marshal_router, admin_logs as admin_logs_router
from routers import import_router
from routers import trainees as trainees_router
from routers import training as training_router
from routers import downhill as downhill_router
from routers import disciplines as disciplines_router

app = FastAPI(
    title="RaceControl Pro",
    description="Kart-Slalom Veranstaltungssoftware – MSC Braach 1980 e.V.",
    version="0.6.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lokales WLAN – kein öffentlicher Zugang
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    log_event("server_start", detail=f"RaceControl Pro v{app.version}")


_API = "/api"
app.include_router(auth.router,         prefix=_API)
app.include_router(users.router,        prefix=_API)
app.include_router(reglements.router,   prefix=_API)
app.include_router(events.router,       prefix=_API)
app.include_router(participants.router, prefix=_API)
app.include_router(results.router,      prefix=_API)
app.include_router(teams.router,        prefix=_API)
app.include_router(clubs.router,        prefix=_API)
app.include_router(sponsors.router,     prefix=_API)
app.include_router(public.router,       prefix=_API)
app.include_router(settings.router,     prefix=_API)
app.include_router(import_router.router,      prefix=_API)
app.include_router(notifications.router,     prefix=_API)
app.include_router(assets_router.router,     prefix=_API)
app.include_router(marshal_router.router,    prefix=_API)
app.include_router(admin_logs_router.router, prefix=_API)
app.include_router(trainees_router.router,  prefix=_API)
app.include_router(training_router.router,  prefix=_API)
app.include_router(downhill_router.router,    prefix=_API)
app.include_router(disciplines_router.router, prefix=_API)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


# Tracks how many timing devices (Raspi) are connected right now
_timing_devices: set[WebSocket] = set()


_TIMING_MIN_TIME =  5.0   # Sekunden – kürzere Läufe werden verworfen
_TIMING_MAX_TIME = 999.0  # Sekunden – längere Läufe werden verworfen


def _get_timing_api_key() -> str:
    """Liest den aktuellen Timing-API-Key. Env-Variable hat Vorrang (SaaS-Betrieb)."""
    env_key = os.environ.get("TIMING_API_KEY", "")
    if env_key:
        return env_key
    try:
        conn = sqlite3.connect(str(DB_PATH))
        row = conn.execute("SELECT value FROM Settings WHERE key='timing_api_key'").fetchone()
        conn.close()
        return row[0] if row else ""
    except Exception:
        return ""


def _clock_to_seconds(clock: str) -> float:
    """Parse 'HH:MM:SS.mmm' or 'HH:MM:SS' → total seconds since midnight."""
    parts = clock.split(":")
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])


async def _handle_timing_finish(ws: WebSocket, data: dict) -> None:
    """Handle timing_finish message from a downhill finish-only RPi.

    Finds the next unfinished participant in the active downhill event on the
    given lane, calculates raw_time = finish_clock − scheduled_start, writes a
    RaceResult, and sends timing_result_display back to the device.
    """
    clock = data.get("clock", "")
    lane  = data.get("lane", "A")

    try:
        finish_s = _clock_to_seconds(clock)
    except Exception:
        await ws.send_json({"type": "timing_rejected", "reason": "invalid_clock", "clock": clock})
        return

    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        # Active downhill event
        event = conn.execute(
            "SELECT id FROM Events WHERE status = 'active' AND timing_mode = 'downhill' LIMIT 1"
        ).fetchone()
        if not event:
            await ws.send_json({"type": "timing_rejected", "reason": "no_active_downhill_event"})
            return
        event_id = event["id"]

        # Next unfinished participant — lane=NULL in schedule means single-lane (always matches)
        row = conn.execute(
            """SELECT ss.id AS schedule_id, ss.participant_id, ss.scheduled_start,
                      p.class_id, p.first_name, p.last_name, p.start_number
               FROM   StartSchedule ss
               JOIN   Participants p ON p.id = ss.participant_id
               LEFT JOIN RaceResults rr
                      ON rr.participant_id = ss.participant_id
                     AND rr.event_id = ss.event_id
                     AND rr.run_number >= 1
               WHERE  ss.event_id = ?
                 AND  (ss.lane IS NULL OR ss.lane = ?)
                 AND  rr.id IS NULL
               ORDER  BY ss.scheduled_start
               LIMIT  1""",
            (event_id, lane),
        ).fetchone()
        if not row:
            await ws.send_json({"type": "timing_rejected", "reason": "no_starter_found", "lane": lane})
            return

        start_s  = _clock_to_seconds(row["scheduled_start"])
        raw_time = round(finish_s - start_s, 3)
        if raw_time < 0:
            await ws.send_json({"type": "timing_rejected", "reason": "negative_time",
                                "raw_time": raw_time, "clock": clock,
                                "scheduled_start": row["scheduled_start"]})
            return

        # Nächste run_number für diesen Teilnehmer in diesem Event
        nr = conn.execute(
            "SELECT COALESCE(MAX(run_number), 0) + 1 AS next FROM RaceResults WHERE participant_id = ? AND event_id = ?",
            (row["participant_id"], event_id),
        ).fetchone()["next"]

        conn.execute(
            """INSERT INTO RaceResults
               (event_id, participant_id, class_id, run_number, raw_time, status, is_official)
               VALUES (?,?,?,?,?,'valid',0)""",
            (event_id, row["participant_id"], row["class_id"], nr, raw_time),
        )
        conn.commit()

        await ws.send_json({
            "type": "timing_result_display",
            "raw_time": raw_time,
            "participant_id": row["participant_id"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "start_number": row["start_number"],
            "lane": lane,
        })
        await manager.broadcast({
            "type":           "timing_finish_result",
            "event_id":       event_id,
            "participant_id": row["participant_id"],
            "first_name":     row["first_name"],
            "last_name":      row["last_name"],
            "start_number":   row["start_number"],
            "raw_time":       raw_time,
            "lane":           lane,
            "clock":          clock,
            "scheduled_start": row["scheduled_start"],
        })
    except Exception as exc:
        await ws.send_json({"type": "timing_rejected", "reason": "internal_error", "detail": str(exc)})
    finally:
        conn.close()


@app.websocket("/ws/timing")
async def timing_device_endpoint(ws: WebSocket):
    """WebSocket endpoint for Raspberry Pi / Lichtschranke devices.

    Verbindungsaufbau: wss://<host>/ws/timing?key=<TIMING_API_KEY>

    Accepted messages (JSON):
      {"type": "timing_result",       "raw_time": 45.32, "device": "..."}
      {"type": "timing_device_heartbeat"}

    All messages are forwarded to browser clients on /ws.
    Connect/disconnect events broadcast a timing_device_status message.
    """
    # ── Schicht 1: API-Key prüfen ─────────────────────────────────────────────
    expected_key = _get_timing_api_key()
    provided_key = ws.query_params.get("key", "")
    if expected_key and not secrets.compare_digest(provided_key, expected_key):
        await ws.accept()
        await ws.close(code=4401, reason="Ungültiger API-Key")
        log_event("timing_auth_failed", detail=f"Verbindungsversuch mit ungültigem Key von {ws.client.host}")
        return

    await ws.accept()
    _timing_devices.add(ws)
    await manager.broadcast({
        "type": "timing_device_status",
        "connected": True,
        "count": len(_timing_devices),
    })
    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")

            if msg_type == "timing_result":
                # ── Schicht 2: Plausibilitätsprüfung ─────────────────────────
                raw = data.get("raw_time")
                if not isinstance(raw, (int, float)) or not (_TIMING_MIN_TIME <= raw <= _TIMING_MAX_TIME):
                    await ws.send_json({"type": "timing_rejected", "reason": "implausible_time", "raw_time": raw})
                    continue
                await manager.broadcast(data)

            elif msg_type == "timing_finish":
                await _handle_timing_finish(ws, data)

            elif msg_type == "timing_device_heartbeat":
                await manager.broadcast(data)

    except (WebSocketDisconnect, Exception):
        pass
    finally:
        _timing_devices.discard(ws)
        await manager.broadcast({
            "type": "timing_device_status",
            "connected": len(_timing_devices) > 0,
            "count": len(_timing_devices),
        })


# Serve assets folder (Reglements, Vorlagen, Logos) unter /media
# Nicht /assets — das ist Vites kompiliertes Frontend (dist/assets/)
_assets_dir = pathlib.Path(os.environ.get("ASSETS_DIR", str(pathlib.Path(__file__).parent.parent / "assets")))
if _assets_dir.exists():
    app.mount("/media", StaticFiles(directory=str(_assets_dir)), name="assets_files")

# Serve built frontend — must come AFTER all API/WS routes
_dist = pathlib.Path(__file__).parent.parent / "frontend" / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="static")
