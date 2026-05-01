from __future__ import annotations
import pytest


_TRAINEE = {
    "first_name": "Max", "last_name": "Mustermann",
    "birth_year": 2010, "kart_number": "7", "is_active": True,
}


def _create(client, headers, **kwargs):
    return client.post("/api/trainees", json={**_TRAINEE, **kwargs}, headers=headers)


# ── List ──────────────────────────────────────────────────────────────────────

def test_list_empty(client, admin_headers):
    r = client.get("/api/trainees", headers=admin_headers)
    assert r.status_code == 200
    assert r.json() == []


def test_list_forbidden_for_zeitnahme(client, zeitnahme_headers):
    r = client.get("/api/trainees", headers=zeitnahme_headers)
    assert r.status_code == 403


def test_list_forbidden_without_token(client):
    r = client.get("/api/trainees")
    assert r.status_code in (401, 403)


# ── Create ────────────────────────────────────────────────────────────────────

def test_create(client, admin_headers):
    r = _create(client, admin_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["first_name"] == "Max"
    assert data["last_name"] == "Mustermann"
    assert data["kart_number"] == "7"
    assert data["is_active"] is True
    assert "id" in data


def test_create_forbidden_for_zeitnahme(client, zeitnahme_headers):
    r = _create(client, zeitnahme_headers)
    assert r.status_code == 403


def test_create_forbidden_without_token(client):
    r = client.post("/api/trainees", json=_TRAINEE)
    assert r.status_code in (401, 403)


def test_create_appears_in_list(client, admin_headers):
    _create(client, admin_headers, last_name="Eins")
    _create(client, admin_headers, last_name="Zwei")
    rows = client.get("/api/trainees", headers=admin_headers).json()
    names = [r["last_name"] for r in rows]
    assert "Eins" in names
    assert "Zwei" in names


# ── Filter: active_only ───────────────────────────────────────────────────────

def test_list_active_only(client, admin_headers):
    _create(client, admin_headers, last_name="Aktiv", is_active=True)
    _create(client, admin_headers, last_name="Inaktiv", is_active=False)

    all_rows  = client.get("/api/trainees", headers=admin_headers).json()
    active    = client.get("/api/trainees", params={"active_only": True},
                           headers=admin_headers).json()

    assert len(all_rows) == 2
    assert len(active) == 1
    assert active[0]["last_name"] == "Aktiv"


# ── Filter: search ────────────────────────────────────────────────────────────

def test_list_search_by_last_name(client, admin_headers):
    _create(client, admin_headers, last_name="Schmidt")
    _create(client, admin_headers, last_name="Müller")

    r = client.get("/api/trainees", params={"search": "Schm"}, headers=admin_headers)
    names = [row["last_name"] for row in r.json()]
    assert "Schmidt" in names
    assert "Müller" not in names


def test_list_search_case_insensitive(client, admin_headers):
    _create(client, admin_headers, last_name="Weber")
    r = client.get("/api/trainees", params={"search": "web"}, headers=admin_headers)
    assert any(row["last_name"] == "Weber" for row in r.json())


def test_list_search_by_license_number(client, admin_headers):
    _create(client, admin_headers, last_name="Lizenz", license_number="LIC-9999")
    _create(client, admin_headers, last_name="OhneLizenz")

    r = client.get("/api/trainees", params={"search": "LIC-9999"}, headers=admin_headers)
    names = [row["last_name"] for row in r.json()]
    assert "Lizenz" in names
    assert "OhneLizenz" not in names


# ── Update ────────────────────────────────────────────────────────────────────

def test_update_kart_number(client, admin_headers, trainee_id):
    r = client.patch(f"/api/trainees/{trainee_id}",
                     json={"kart_number": "99"}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["kart_number"] == "99"


def test_update_deactivate(client, admin_headers, trainee_id):
    r = client.patch(f"/api/trainees/{trainee_id}",
                     json={"is_active": False}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["is_active"] is False


def test_update_not_found(client, admin_headers):
    r = client.patch("/api/trainees/99999", json={"kart_number": "1"},
                     headers=admin_headers)
    assert r.status_code == 404


def test_update_no_fields_rejected(client, admin_headers, trainee_id):
    r = client.patch(f"/api/trainees/{trainee_id}", json={}, headers=admin_headers)
    assert r.status_code == 422


def test_update_forbidden_for_zeitnahme(client, zeitnahme_headers, trainee_id):
    r = client.patch(f"/api/trainees/{trainee_id}",
                     json={"kart_number": "1"}, headers=zeitnahme_headers)
    assert r.status_code == 403


# ── Delete ────────────────────────────────────────────────────────────────────

def test_delete(client, admin_headers, trainee_id):
    r = client.delete(f"/api/trainees/{trainee_id}", headers=admin_headers)
    assert r.status_code == 204

    r = client.get("/api/trainees", headers=admin_headers)
    ids = [row["id"] for row in r.json()]
    assert trainee_id not in ids


def test_delete_not_found(client, admin_headers):
    r = client.delete("/api/trainees/99999", headers=admin_headers)
    assert r.status_code == 404


def test_delete_forbidden_for_zeitnahme(client, zeitnahme_headers, trainee_id):
    r = client.delete(f"/api/trainees/{trainee_id}", headers=zeitnahme_headers)
    assert r.status_code == 403
