import os
import pathlib
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_db
from broadcast import manager
from system_logger import log_event
from routers import auth, users, reglements, events, participants, results, teams, clubs, public, sponsors, settings, notifications, assets as assets_router, marshal as marshal_router, admin_logs as admin_logs_router
from routers import import_router

app = FastAPI(
    title="RaceControl Pro",
    description="Kart-Slalom Veranstaltungssoftware – ADAC Hessen-Thüringen",
    version="0.1.0",
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


@app.websocket("/ws/timing")
async def timing_device_endpoint(ws: WebSocket):
    """WebSocket endpoint for Raspberry Pi / Lichtschranke devices.

    Accepted messages (JSON):
      {"type": "timing_result",       "raw_time": 45.32, "device": "..."}
      {"type": "timing_device_heartbeat"}

    All messages are forwarded to browser clients on /ws.
    Connect/disconnect events broadcast a timing_device_status message.
    """
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
            if msg_type in ("timing_result", "timing_device_heartbeat"):
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
