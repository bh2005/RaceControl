import pathlib
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_db
from broadcast import manager
from routers import auth, users, reglements, events, participants, results, teams, clubs, public, sponsors, settings

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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            # Keep the connection alive; ignore any client messages
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


# Serve built frontend — must come AFTER all API/WS routes
_dist = pathlib.Path(__file__).parent.parent / "frontend" / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="static")
