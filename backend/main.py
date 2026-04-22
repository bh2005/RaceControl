from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import auth, users, reglements, events, participants, results

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


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(reglements.router)
app.include_router(events.router)
app.include_router(participants.router)
app.include_router(results.router)


@app.get("/health")
def health():
    return {"status": "ok"}
