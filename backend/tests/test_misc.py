"""
Tests for clubs, sponsors, disciplines, notifications, and users routers.
Covers the previously untested CRUD paths to push coverage above 70 %.
"""
from __future__ import annotations
import pytest


# ══════════════════════════════════════════════════════════════════════════════
# Clubs
# ══════════════════════════════════════════════════════════════════════════════

class TestClubs:
    def test_list_empty(self, client):
        r = client.get("/api/clubs/")
        assert r.status_code == 200
        assert r.json() == []

    def test_create(self, client, admin_headers):
        r = client.post("/api/clubs/", json={"name": "Testverein", "short_name": "TV", "city": "Kassel"},
                        headers=admin_headers)
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Testverein"
        assert data["short_name"] == "TV"
        assert data["city"] == "Kassel"
        assert "id" in data

    def test_create_duplicate_409(self, client, admin_headers):
        client.post("/api/clubs/", json={"name": "Duplikat"}, headers=admin_headers)
        r = client.post("/api/clubs/", json={"name": "Duplikat"}, headers=admin_headers)
        assert r.status_code == 409

    def test_create_requires_admin(self, client, viewer_headers):
        r = client.post("/api/clubs/", json={"name": "Nope"}, headers=viewer_headers)
        assert r.status_code == 403

    def test_patch(self, client, admin_headers):
        cid = client.post("/api/clubs/", json={"name": "Alt"}, headers=admin_headers).json()["id"]
        r = client.patch(f"/api/clubs/{cid}", json={"city": "Neu-Stadt"}, headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["city"] == "Neu-Stadt"

    def test_patch_no_fields_422(self, client, admin_headers):
        cid = client.post("/api/clubs/", json={"name": "Leer"}, headers=admin_headers).json()["id"]
        r = client.patch(f"/api/clubs/{cid}", json={}, headers=admin_headers)
        assert r.status_code == 422

    def test_delete(self, client, admin_headers):
        cid = client.post("/api/clubs/", json={"name": "Weg"}, headers=admin_headers).json()["id"]
        r = client.delete(f"/api/clubs/{cid}", headers=admin_headers)
        assert r.status_code == 204

    def test_list_after_create(self, client, admin_headers):
        client.post("/api/clubs/", json={"name": "Verein A"}, headers=admin_headers)
        client.post("/api/clubs/", json={"name": "Verein B"}, headers=admin_headers)
        r = client.get("/api/clubs/")
        assert r.status_code == 200
        assert len(r.json()) == 2


# ══════════════════════════════════════════════════════════════════════════════
# Sponsors
# ══════════════════════════════════════════════════════════════════════════════

class TestSponsors:
    def test_list_empty(self, client):
        r = client.get("/api/sponsors/")
        assert r.status_code == 200
        assert r.json() == []

    def test_create(self, client, admin_headers):
        r = client.post("/api/sponsors/", json={
            "name": "TestSponsor", "logo_url": "http://example.com/logo.png",
            "website_url": "http://example.com", "sort_order": 1, "is_active": True,
        }, headers=admin_headers)
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "TestSponsor"
        assert data["is_active"] is True

    def test_create_requires_admin(self, client, nennung_headers):
        r = client.post("/api/sponsors/", json={"name": "Nope"}, headers=nennung_headers)
        assert r.status_code == 403

    def test_patch(self, client, admin_headers):
        sid = client.post("/api/sponsors/", json={"name": "S1"}, headers=admin_headers).json()["id"]
        r = client.patch(f"/api/sponsors/{sid}", json={"sort_order": 5}, headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["sort_order"] == 5

    def test_patch_is_active_bool(self, client, admin_headers):
        sid = client.post("/api/sponsors/", json={"name": "S2", "is_active": True},
                          headers=admin_headers).json()["id"]
        r = client.patch(f"/api/sponsors/{sid}", json={"is_active": False}, headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["is_active"] is False

    def test_patch_nonexistent_404(self, client, admin_headers):
        r = client.patch("/api/sponsors/99999", json={"sort_order": 1}, headers=admin_headers)
        assert r.status_code == 404

    def test_patch_no_fields_422(self, client, admin_headers):
        sid = client.post("/api/sponsors/", json={"name": "S3"}, headers=admin_headers).json()["id"]
        r = client.patch(f"/api/sponsors/{sid}", json={}, headers=admin_headers)
        assert r.status_code == 422

    def test_delete(self, client, admin_headers):
        sid = client.post("/api/sponsors/", json={"name": "DelMe"}, headers=admin_headers).json()["id"]
        r = client.delete(f"/api/sponsors/{sid}", headers=admin_headers)
        assert r.status_code == 204


# ══════════════════════════════════════════════════════════════════════════════
# Disciplines
# ══════════════════════════════════════════════════════════════════════════════

class TestDisciplines:
    def test_list(self, client, admin_headers):
        r = client.get("/api/disciplines", headers=admin_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_requires_auth(self, client):
        r = client.get("/api/disciplines")
        assert r.status_code == 401

    def test_create(self, client, admin_headers):
        r = client.post("/api/disciplines", json={"name": "Slalom", "sort_order": 1},
                        headers=admin_headers)
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Slalom"
        assert data["is_active"] is True

    def test_create_duplicate_409(self, client, admin_headers):
        client.post("/api/disciplines", json={"name": "DupDisziplin"}, headers=admin_headers)
        r = client.post("/api/disciplines", json={"name": "DupDisziplin"}, headers=admin_headers)
        assert r.status_code == 409

    def test_create_requires_admin(self, client, zeitnahme_headers):
        r = client.post("/api/disciplines", json={"name": "Nope"}, headers=zeitnahme_headers)
        assert r.status_code == 403

    def test_patch(self, client, admin_headers):
        did = client.post("/api/disciplines", json={"name": "D1"}, headers=admin_headers).json()["id"]
        r = client.patch(f"/api/disciplines/{did}", json={"is_active": False}, headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["is_active"] is False

    def test_patch_404(self, client, admin_headers):
        r = client.patch("/api/disciplines/99999", json={"sort_order": 1}, headers=admin_headers)
        assert r.status_code == 404

    def test_patch_no_fields_422(self, client, admin_headers):
        did = client.post("/api/disciplines", json={"name": "D2"}, headers=admin_headers).json()["id"]
        r = client.patch(f"/api/disciplines/{did}", json={}, headers=admin_headers)
        assert r.status_code == 422

    def test_delete(self, client, admin_headers):
        did = client.post("/api/disciplines", json={"name": "DelDis"}, headers=admin_headers).json()["id"]
        r = client.delete(f"/api/disciplines/{did}", headers=admin_headers)
        assert r.status_code == 204

    def test_delete_404(self, client, admin_headers):
        r = client.delete("/api/disciplines/99999", headers=admin_headers)
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# Notifications
# ══════════════════════════════════════════════════════════════════════════════

class TestNotifications:
    def test_send_ok(self, client, admin_headers):
        r = client.post("/api/notifications", json={"message": "Testnachricht"},
                        headers=admin_headers)
        assert r.status_code == 204

    def test_send_as_viewer(self, client, viewer_headers):
        r = client.post("/api/notifications", json={"message": "Hallo"},
                        headers=viewer_headers)
        assert r.status_code == 204

    def test_send_empty_message_422(self, client, admin_headers):
        r = client.post("/api/notifications", json={"message": "   "},
                        headers=admin_headers)
        assert r.status_code == 422

    def test_send_too_long_422(self, client, admin_headers):
        r = client.post("/api/notifications", json={"message": "x" * 301},
                        headers=admin_headers)
        assert r.status_code == 422

    def test_send_requires_auth(self, client):
        r = client.post("/api/notifications", json={"message": "Hallo"})
        assert r.status_code == 401

    def test_send_forbidden_for_marshal(self, client, marshal_headers):
        r = client.post("/api/notifications", json={"message": "Hallo"},
                        headers=marshal_headers)
        assert r.status_code == 403


# ══════════════════════════════════════════════════════════════════════════════
# Users
# ══════════════════════════════════════════════════════════════════════════════

class TestUsers:
    def test_list(self, client, admin_headers):
        r = client.get("/api/users/", headers=admin_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_requires_admin(self, client, viewer_headers):
        r = client.get("/api/users/", headers=viewer_headers)
        assert r.status_code == 403

    def test_create(self, client, admin_headers):
        r = client.post("/api/users/", json={
            "username": "neuernutzer", "password": "geheim123", "role": "zeitnahme",
        }, headers=admin_headers)
        assert r.status_code == 201
        data = r.json()
        assert data["username"] == "neuernutzer"
        assert data["role"] == "zeitnahme"
        assert data["is_active"] is True

    def test_create_duplicate_409(self, client, admin_headers):
        payload = {"username": "dupuser", "password": "abc12345", "role": "viewer"}
        client.post("/api/users/", json=payload, headers=admin_headers)
        r = client.post("/api/users/", json=payload, headers=admin_headers)
        assert r.status_code == 409

    def test_create_requires_admin(self, client, schiri_headers):
        r = client.post("/api/users/", json={
            "username": "x", "password": "x", "role": "viewer",
        }, headers=schiri_headers)
        assert r.status_code == 403

    def test_deactivate(self, client, admin_headers):
        uid = client.post("/api/users/", json={
            "username": "zudeaktivieren", "password": "test1234", "role": "viewer",
        }, headers=admin_headers).json()["id"]
        r = client.delete(f"/api/users/{uid}", headers=admin_headers)
        assert r.status_code == 204
        users = client.get("/api/users/", headers=admin_headers).json()
        match = next((u for u in users if u["id"] == uid), None)
        assert match is not None
        assert match["is_active"] is False

    def test_change_own_password(self, client, viewer_headers):
        # viewer is created with password "test1234" by the fixture
        r = client.patch("/api/users/me/password", json={
            "current_password": "test1234", "new_password": "neupasswort",
        }, headers=viewer_headers)
        assert r.status_code == 204

    def test_change_own_password_wrong_current_401(self, client, viewer_headers):
        r = client.patch("/api/users/me/password", json={
            "current_password": "falsch!", "new_password": "neupasswort",
        }, headers=viewer_headers)
        assert r.status_code == 401

    def test_admin_change_user_password(self, client, admin_headers):
        uid = client.post("/api/users/", json={
            "username": "zupatch", "password": "alt1234", "role": "viewer",
        }, headers=admin_headers).json()["id"]
        r = client.patch(f"/api/users/{uid}/password", json={"new_password": "neu1234"},
                         headers=admin_headers)
        assert r.status_code == 204

    def test_admin_change_password_404(self, client, admin_headers):
        r = client.patch("/api/users/99999/password", json={"new_password": "neu1234"},
                         headers=admin_headers)
        assert r.status_code == 404
