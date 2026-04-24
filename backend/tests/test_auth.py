from __future__ import annotations
from auth import hash_password


def _create(db, username, role, password="correct"):
    db.execute(
        "INSERT INTO Users (username, password_hash, role, is_active) VALUES (?,?,?,1)",
        (username, hash_password(password), role),
    )
    db.commit()


# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_returns_token(client, db):
    _create(db, "alice", "zeitnahme")
    r = client.post("/api/auth/login", data={"username": "alice", "password": "correct"})
    assert r.status_code == 200
    assert "access_token" in r.json()
    assert r.json()["token_type"] == "bearer"


def test_login_wrong_password(client, db):
    _create(db, "bob", "zeitnahme")
    r = client.post("/api/auth/login", data={"username": "bob", "password": "wrong"})
    assert r.status_code == 401


def test_login_unknown_user(client):
    r = client.post("/api/auth/login", data={"username": "nobody", "password": "pw"})
    assert r.status_code == 401


def test_login_inactive_user(client, db):
    db.execute(
        "INSERT INTO Users (username, password_hash, role, is_active) VALUES (?,?,?,0)",
        ("inactive", hash_password("pw"), "admin"),
    )
    db.commit()
    r = client.post("/api/auth/login", data={"username": "inactive", "password": "pw"})
    assert r.status_code == 401


# ── Role guards ───────────────────────────────────────────────────────────────

def test_admin_only_route_rejected_without_token(client):
    r = client.post("/api/events", json={"name": "x", "date": "2026-01-01", "status": "planned"})
    assert r.status_code in (401, 403)


def test_admin_only_route_rejected_for_zeitnahme(client, zeitnahme_headers):
    r = client.post("/api/events", json={"name": "x", "date": "2026-01-01", "status": "planned"},
                    headers=zeitnahme_headers)
    assert r.status_code == 403


def test_admin_only_route_accepted_for_admin(client, admin_headers):
    r = client.post("/api/events",
                    json={"name": "Event", "date": "2026-01-01", "status": "planned"},
                    headers=admin_headers)
    assert r.status_code == 201
