from __future__ import annotations


# ── active-event ──────────────────────────────────────────────────────────────

def test_active_event_not_found_when_empty(client):
    r = client.get("/api/public/active-event")
    assert r.status_code == 404


def test_active_event_returns_most_recent(client, event_id):
    r = client.get("/api/public/active-event")
    assert r.status_code == 200
    data = r.json()
    assert "event" in data
    assert "classes" in data
    assert "clubs" in data
    assert "sponsors" in data
    assert data["event"]["id"] == event_id


def test_active_event_includes_class(client, class_id, event_id):
    r = client.get("/api/public/active-event")
    classes = r.json()["classes"]
    assert any(c["id"] == class_id for c in classes)


def test_active_event_no_auth_required(client, event_id):
    r = client.get("/api/public/active-event")
    assert r.status_code == 200


# ── self-register ─────────────────────────────────────────────────────────────

def test_self_register_creates_participant(client, event_id):
    r = client.post(f"/api/public/events/{event_id}/register", json={
        "first_name": "Lisa",
        "last_name": "Muster",
        "birth_year": 2011,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "created"
    assert data["participant"]["first_name"] == "Lisa"


def test_self_register_duplicate_by_name_and_birth_year(client, event_id):
    body = {"first_name": "Doppel", "last_name": "Name", "birth_year": 2011}
    client.post(f"/api/public/events/{event_id}/register", json=body)
    r = client.post(f"/api/public/events/{event_id}/register", json=body)
    assert r.status_code == 201
    assert r.json()["status"] == "duplicate"


def test_self_register_duplicate_by_license(client, event_id):
    body = {"first_name": "A", "last_name": "B", "license_number": "LIC-123"}
    client.post(f"/api/public/events/{event_id}/register", json=body)
    r = client.post(f"/api/public/events/{event_id}/register", json={
        "first_name": "Different", "last_name": "Name", "license_number": "LIC-123",
    })
    assert r.status_code == 201
    assert r.json()["status"] == "duplicate"


def test_self_register_unknown_event(client):
    r = client.post("/api/public/events/9999/register", json={
        "first_name": "Max", "last_name": "Test",
    })
    assert r.status_code == 404
