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
