"""
Shared test fixtures for RaceControl backend.

Each test function gets its own in-memory SQLite database so tests are
fully isolated — no shared state, no leftover rows between tests.
"""
from __future__ import annotations
import pathlib
import sqlite3
import sys

import pytest
from fastapi.testclient import TestClient

# Make sure backend package is importable from this directory
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from auth import create_access_token, hash_password
from database import get_db
from main import app

SCHEMA = (pathlib.Path(__file__).parent.parent.parent / "schema.sql").read_text(encoding="utf-8")


def _fresh_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    return conn


@pytest.fixture()
def db():
    conn = _fresh_db()
    yield conn
    conn.close()


@pytest.fixture()
def client(db):
    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Auth helpers ──────────────────────────────────────────────────────────────

def _make_user(db, username: str, role: str) -> str:
    """Insert a user and return a valid JWT for that user."""
    db.execute(
        "INSERT INTO Users (username, password_hash, role, is_active) VALUES (?,?,?,1)",
        (username, hash_password("test1234"), role),
    )
    db.commit()
    uid = db.execute("SELECT id FROM Users WHERE username=?", (username,)).fetchone()["id"]
    return create_access_token({"sub": str(uid), "role": role})


@pytest.fixture()
def admin_headers(db):
    return {"Authorization": f"Bearer {_make_user(db, 't_admin', 'admin')}"}


@pytest.fixture()
def schiri_headers(db):
    return {"Authorization": f"Bearer {_make_user(db, 't_schiri', 'schiedsrichter')}"}


@pytest.fixture()
def zeitnahme_headers(db):
    return {"Authorization": f"Bearer {_make_user(db, 't_zeit', 'zeitnahme')}"}


@pytest.fixture()
def nennung_headers(db):
    return {"Authorization": f"Bearer {_make_user(db, 't_nenn', 'nennung')}"}


# ── Domain object fixtures ────────────────────────────────────────────────────

@pytest.fixture()
def event_id(client, admin_headers):
    r = client.post("/api/events", json={
        "name": "Testlauf 2026", "date": "2026-06-01",
        "location": "Testort", "status": "active",
    }, headers=admin_headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.fixture()
def class_id(client, admin_headers, event_id):
    r = client.post(f"/api/events/{event_id}/classes", json={
        "name": "Klasse A", "short_name": "KA", "run_status": "planned",
    }, headers=admin_headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.fixture()
def participant_id(client, nennung_headers, event_id, class_id):
    r = client.post(f"/api/events/{event_id}/participants", json={
        "first_name": "Max", "last_name": "Mustermann",
        "birth_year": 2010, "class_id": class_id, "start_number": 1,
    }, headers=nennung_headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]
