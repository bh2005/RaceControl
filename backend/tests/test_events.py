from __future__ import annotations
import pytest


# ── Event CRUD ────────────────────────────────────────────────────────────────

def test_list_events_empty(client):
    r = client.get("/api/events")
    assert r.status_code == 200
    assert r.json() == []


def test_create_event(client, admin_headers):
    r = client.post("/api/events", json={
        "name": "Testlauf", "date": "2026-06-01", "status": "planned",
    }, headers=admin_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Testlauf"
    assert data["status"] == "planned"
    assert "id" in data


def test_create_event_forbidden_without_token(client):
    r = client.post("/api/events", json={"name": "x", "date": "2026-01-01", "status": "planned"})
    assert r.status_code in (401, 403)


def test_create_event_forbidden_for_zeitnahme(client, zeitnahme_headers):
    r = client.post("/api/events", json={
        "name": "x", "date": "2026-01-01", "status": "planned",
    }, headers=zeitnahme_headers)
    assert r.status_code == 403


def test_create_event_forbidden_for_nennung(client, nennung_headers):
    r = client.post("/api/events", json={
        "name": "x", "date": "2026-01-01", "status": "planned",
    }, headers=nennung_headers)
    assert r.status_code == 403


def test_get_event(client, event_id):
    r = client.get(f"/api/events/{event_id}")
    assert r.status_code == 200
    assert r.json()["id"] == event_id


def test_get_event_not_found(client):
    r = client.get("/api/events/9999")
    assert r.status_code == 404


def test_list_events_returns_created_event(client, event_id):
    r = client.get("/api/events")
    assert r.status_code == 200
    assert any(e["id"] == event_id for e in r.json())


def test_update_event_status(client, event_id, admin_headers):
    r = client.patch(f"/api/events/{event_id}", json={"status": "active"},
                     headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "active"


def test_update_event_forbidden_for_schiri(client, event_id, schiri_headers):
    r = client.patch(f"/api/events/{event_id}", json={"status": "active"},
                     headers=schiri_headers)
    assert r.status_code == 403


def test_delete_event(client, event_id, admin_headers):
    r = client.delete(f"/api/events/{event_id}", headers=admin_headers)
    assert r.status_code == 204
    r = client.get(f"/api/events/{event_id}")
    assert r.status_code == 404


def test_delete_event_forbidden_for_zeitnahme(client, event_id, zeitnahme_headers):
    r = client.delete(f"/api/events/{event_id}", headers=zeitnahme_headers)
    assert r.status_code == 403


# ── Class CRUD ────────────────────────────────────────────────────────────────

def test_list_classes_empty(client, event_id):
    r = client.get(f"/api/events/{event_id}/classes")
    assert r.status_code == 200
    assert r.json() == []


def test_create_class(client, event_id, admin_headers):
    r = client.post(f"/api/events/{event_id}/classes", json={
        "name": "Junioren", "short_name": "JUN", "run_status": "planned",
    }, headers=admin_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Junioren"
    assert data["event_id"] == event_id


def test_create_class_forbidden_for_zeitnahme(client, event_id, zeitnahme_headers):
    r = client.post(f"/api/events/{event_id}/classes", json={
        "name": "Junioren", "run_status": "planned",
    }, headers=zeitnahme_headers)
    assert r.status_code == 403


def test_list_classes_contains_created(client, class_id, event_id):
    r = client.get(f"/api/events/{event_id}/classes")
    assert r.status_code == 200
    assert any(c["id"] == class_id for c in r.json())


def test_update_class_status_by_admin(client, event_id, class_id, admin_headers):
    r = client.patch(f"/api/events/{event_id}/classes/{class_id}",
                     json={"run_status": "running"}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["run_status"] == "running"


def test_update_class_status_by_schiri(client, event_id, class_id, schiri_headers):
    r = client.patch(f"/api/events/{event_id}/classes/{class_id}",
                     json={"run_status": "running"}, headers=schiri_headers)
    assert r.status_code == 200
    assert r.json()["run_status"] == "running"


def test_update_class_forbidden_for_zeitnahme(client, event_id, class_id, zeitnahme_headers):
    r = client.patch(f"/api/events/{event_id}/classes/{class_id}",
                     json={"run_status": "running"}, headers=zeitnahme_headers)
    assert r.status_code == 403
