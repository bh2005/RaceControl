"""
Additional tests to push coverage from ~78% to ~85%.
Targets: reglements, settings, teams, downhill schedule, assets, broadcast.
"""
from __future__ import annotations
import asyncio
import io
import sqlite3
import tempfile
import pathlib
from unittest.mock import patch, MagicMock

import pytest


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _make_reglement(client, admin_headers, **kw):
    payload = {"name": "Testreglement", "scoring_type": "sum_all", **kw}
    r = client.post("/api/reglements/", json=payload, headers=admin_headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _make_downhill_event(client, admin_headers, db):
    r = client.post("/api/events", json={
        "name": "Downhill 2026", "date": "2026-07-01",
        "location": "Berg", "status": "active",
    }, headers=admin_headers)
    assert r.status_code == 201, r.text
    eid = r.json()["id"]
    # The events router doesn't expose timing_mode on create — patch the DB directly
    db.execute("UPDATE Events SET timing_mode='downhill' WHERE id=?", (eid,))
    db.commit()
    return eid


def _make_participant(client, headers, event_id, class_id, start_number=99):
    r = client.post(f"/api/events/{event_id}/participants", json={
        "first_name": "Test", "last_name": "Fahrer",
        "birth_year": 2010, "class_id": class_id, "start_number": start_number,
    }, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _make_class(client, admin_headers, event_id, name="Klasse DH"):
    r = client.post(f"/api/events/{event_id}/classes", json={
        "name": name, "short_name": "DH", "run_status": "running",
    }, headers=admin_headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


# ══════════════════════════════════════════════════════════════════════════════
# Reglements
# ══════════════════════════════════════════════════════════════════════════════

class TestReglements:
    def test_list_empty(self, client):
        r = client.get("/api/reglements/")
        assert r.status_code == 200
        assert r.json() == []

    def test_create(self, client, admin_headers):
        r = client.post("/api/reglements/", json={
            "name": "KT-Reglement", "scoring_type": "sum_all",
            "runs_per_class": 3, "has_training": True,
        }, headers=admin_headers)
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "KT-Reglement"
        assert data["scoring_type"] == "sum_all"

    def test_create_requires_admin(self, client, viewer_headers):
        r = client.post("/api/reglements/", json={
            "name": "Nope", "scoring_type": "sum_all",
        }, headers=viewer_headers)
        assert r.status_code == 403

    def test_get(self, client, admin_headers):
        rid = _make_reglement(client, admin_headers)
        r = client.get(f"/api/reglements/{rid}")
        assert r.status_code == 200
        assert r.json()["id"] == rid

    def test_get_404(self, client):
        r = client.get("/api/reglements/99999")
        assert r.status_code == 404

    def test_patch(self, client, admin_headers):
        rid = _make_reglement(client, admin_headers)
        r = client.patch(f"/api/reglements/{rid}", json={"name": "Geändert"},
                         headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["name"] == "Geändert"

    def test_patch_has_training(self, client, admin_headers):
        rid = _make_reglement(client, admin_headers, has_training=True)
        r = client.patch(f"/api/reglements/{rid}", json={"has_training": False},
                         headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["has_training"] is False

    def test_patch_empty_body_returns_unchanged(self, client, admin_headers):
        rid = _make_reglement(client, admin_headers, name="Unveränderlich")
        r = client.patch(f"/api/reglements/{rid}", json={}, headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["name"] == "Unveränderlich"

    def test_patch_404(self, client, admin_headers):
        r = client.patch("/api/reglements/99999", json={"name": "X"},
                         headers=admin_headers)
        assert r.status_code == 404

    def test_delete(self, client, admin_headers):
        rid = _make_reglement(client, admin_headers)
        r = client.delete(f"/api/reglements/{rid}", headers=admin_headers)
        assert r.status_code == 204

    def test_list_after_create(self, client, admin_headers):
        _make_reglement(client, admin_headers, name="R1")
        _make_reglement(client, admin_headers, name="R2")
        r = client.get("/api/reglements/")
        assert len(r.json()) == 2

    # ── Penalties ─────────────────────────────────────────────────────────────

    def test_list_penalties_empty(self, client, admin_headers):
        rid = _make_reglement(client, admin_headers)
        r = client.get(f"/api/reglements/{rid}/penalties")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_penalty(self, client, admin_headers):
        rid = _make_reglement(client, admin_headers)
        r = client.post(f"/api/reglements/{rid}/penalties", json={
            "label": "Leitkegel", "seconds": 2.0, "shortcut_key": "L",
        }, headers=admin_headers)
        assert r.status_code == 201
        data = r.json()
        assert data["label"] == "Leitkegel"
        assert data["seconds"] == 2.0

    def test_create_penalty_requires_admin(self, client, zeitnahme_headers):
        r = client.post("/api/reglements/1/penalties", json={
            "label": "Test", "seconds": 1.0,
        }, headers=zeitnahme_headers)
        assert r.status_code == 403

    def test_patch_penalty(self, client, admin_headers):
        rid = _make_reglement(client, admin_headers)
        pen_id = client.post(f"/api/reglements/{rid}/penalties", json={
            "label": "Alt", "seconds": 1.0,
        }, headers=admin_headers).json()["id"]
        r = client.patch(f"/api/reglements/{rid}/penalties/{pen_id}",
                         json={"label": "Neu", "seconds": 3.0}, headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["label"] == "Neu"
        assert r.json()["seconds"] == 3.0

    def test_patch_penalty_empty_returns_unchanged(self, client, admin_headers):
        rid = _make_reglement(client, admin_headers)
        pen_id = client.post(f"/api/reglements/{rid}/penalties", json={
            "label": "Stable", "seconds": 5.0,
        }, headers=admin_headers).json()["id"]
        r = client.patch(f"/api/reglements/{rid}/penalties/{pen_id}",
                         json={}, headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["label"] == "Stable"

    def test_patch_penalty_404(self, client, admin_headers):
        rid = _make_reglement(client, admin_headers)
        r = client.patch(f"/api/reglements/{rid}/penalties/99999",
                         json={"label": "X"}, headers=admin_headers)
        assert r.status_code == 404

    def test_delete_penalty(self, client, admin_headers):
        rid = _make_reglement(client, admin_headers)
        pen_id = client.post(f"/api/reglements/{rid}/penalties", json={
            "label": "WegPenalty", "seconds": 1.0,
        }, headers=admin_headers).json()["id"]
        r = client.delete(f"/api/reglements/{rid}/penalties/{pen_id}",
                          headers=admin_headers)
        assert r.status_code == 204


# ══════════════════════════════════════════════════════════════════════════════
# Settings
# ══════════════════════════════════════════════════════════════════════════════

class TestSettings:
    def test_get_settings(self, client):
        r = client.get("/api/settings/")
        assert r.status_code == 200
        assert "organizer_name" in r.json()

    def test_update_settings_requires_admin(self, client, viewer_headers):
        r = client.patch("/api/settings/", json={"organizer_name": "Test"},
                         headers=viewer_headers)
        assert r.status_code == 403

    def test_update_settings(self, client, admin_headers):
        r = client.patch("/api/settings/", json={
            "organizer_name": "Neuer Veranstalter",
            "organizer_address": "Teststraße 1",
        }, headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["organizer_name"] == "Neuer Veranstalter"
        assert data["organizer_address"] == "Teststraße 1"

    def test_download_db(self, client, admin_headers):
        r = client.get("/api/settings/db/download", headers=admin_headers)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/octet-stream"
        # SQLite magic bytes
        assert r.content[:15] == b"SQLite format 3"

    def test_download_db_requires_admin(self, client, viewer_headers):
        r = client.get("/api/settings/db/download", headers=viewer_headers)
        assert r.status_code == 403

    def test_regenerate_timing_key(self, client, admin_headers):
        r = client.post("/api/settings/timing-key/regenerate", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "timing_api_key" in data
        assert len(data["timing_api_key"]) == 48  # secrets.token_hex(24)

    def test_regenerate_timing_key_changes_key(self, client, admin_headers):
        r1 = client.post("/api/settings/timing-key/regenerate", headers=admin_headers).json()
        r2 = client.post("/api/settings/timing-key/regenerate", headers=admin_headers).json()
        assert r1["timing_api_key"] != r2["timing_api_key"]

    def test_regenerate_timing_key_requires_admin(self, client, schiri_headers):
        r = client.post("/api/settings/timing-key/regenerate", headers=schiri_headers)
        assert r.status_code == 403

    def test_restore_db_invalid_file(self, client, admin_headers):
        bad_data = b"this is not a sqlite file at all"
        r = client.post(
            "/api/settings/db/restore",
            files={"file": ("bad.db", io.BytesIO(bad_data), "application/octet-stream")},
            headers=admin_headers,
        )
        assert r.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
# Teams & Mannschaftswertung
# ══════════════════════════════════════════════════════════════════════════════

class TestTeams:
    def test_list_teams_empty(self, client, event_id):
        r = client.get(f"/api/events/{event_id}/teams")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_team(self, client, admin_headers, event_id):
        r = client.post(f"/api/events/{event_id}/teams", json={
            "name": "Team Alpha", "club": "MC Teststadt",
        }, headers=admin_headers)
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Team Alpha"
        assert data["event_id"] == event_id

    def test_create_team_duplicate_409(self, client, admin_headers, event_id):
        client.post(f"/api/events/{event_id}/teams", json={"name": "DupTeam"}, headers=admin_headers)
        r = client.post(f"/api/events/{event_id}/teams", json={"name": "DupTeam"}, headers=admin_headers)
        assert r.status_code == 409

    def test_create_team_requires_auth(self, client, viewer_headers, event_id):
        r = client.post(f"/api/events/{event_id}/teams", json={"name": "Nope"}, headers=viewer_headers)
        assert r.status_code == 403

    def test_delete_team(self, client, admin_headers, event_id):
        tid = client.post(f"/api/events/{event_id}/teams", json={"name": "WegTeam"},
                          headers=admin_headers).json()["id"]
        r = client.delete(f"/api/events/{event_id}/teams/{tid}", headers=admin_headers)
        assert r.status_code == 204

    def test_list_members_empty(self, client, admin_headers, event_id):
        tid = client.post(f"/api/events/{event_id}/teams", json={"name": "Leer"},
                          headers=admin_headers).json()["id"]
        r = client.get(f"/api/events/{event_id}/teams/{tid}/members")
        assert r.status_code == 200
        assert r.json() == []

    def test_add_member(self, client, admin_headers, nennung_headers, event_id, class_id, participant_id):
        tid = client.post(f"/api/events/{event_id}/teams", json={"name": "MitMitglied"},
                          headers=admin_headers).json()["id"]
        r = client.post(f"/api/events/{event_id}/teams/{tid}/members",
                        json={"participant_id": participant_id}, headers=admin_headers)
        assert r.status_code == 201
        data = r.json()
        assert data["participant_id"] == participant_id
        assert data["team_id"] == tid

    def test_add_member_duplicate_409(self, client, admin_headers, event_id, class_id, participant_id):
        tid = client.post(f"/api/events/{event_id}/teams", json={"name": "DupMember"},
                          headers=admin_headers).json()["id"]
        client.post(f"/api/events/{event_id}/teams/{tid}/members",
                    json={"participant_id": participant_id}, headers=admin_headers)
        r = client.post(f"/api/events/{event_id}/teams/{tid}/members",
                        json={"participant_id": participant_id}, headers=admin_headers)
        assert r.status_code == 409

    def test_add_member_max_4(self, client, admin_headers, nennung_headers, event_id, class_id):
        tid = client.post(f"/api/events/{event_id}/teams", json={"name": "MaxTeam"},
                          headers=admin_headers).json()["id"]
        for i in range(4):
            pid = client.post(f"/api/events/{event_id}/participants", json={
                "first_name": f"F{i}", "last_name": "L", "birth_year": 2010,
                "class_id": class_id, "start_number": 100 + i,
            }, headers=nennung_headers).json()["id"]
            client.post(f"/api/events/{event_id}/teams/{tid}/members",
                        json={"participant_id": pid}, headers=admin_headers)
        # 5th member should fail
        pid5 = client.post(f"/api/events/{event_id}/participants", json={
            "first_name": "F5", "last_name": "L", "birth_year": 2010,
            "class_id": class_id, "start_number": 200,
        }, headers=nennung_headers).json()["id"]
        r = client.post(f"/api/events/{event_id}/teams/{tid}/members",
                        json={"participant_id": pid5}, headers=admin_headers)
        assert r.status_code == 422

    def test_remove_member(self, client, admin_headers, event_id, class_id, participant_id):
        tid = client.post(f"/api/events/{event_id}/teams", json={"name": "RemoveTest"},
                          headers=admin_headers).json()["id"]
        mid = client.post(f"/api/events/{event_id}/teams/{tid}/members",
                          json={"participant_id": participant_id},
                          headers=admin_headers).json()["id"]
        r = client.delete(f"/api/events/{event_id}/teams/{tid}/members/{mid}",
                          headers=admin_headers)
        assert r.status_code == 204

    def test_team_standings_empty(self, client, admin_headers, event_id):
        r = client.get(f"/api/events/{event_id}/teams/standings")
        assert r.status_code == 200
        assert r.json() == []

    def test_fastest_of_day_empty(self, client, event_id):
        r = client.get(f"/api/events/{event_id}/fastest-of-day?reglement_id=1")
        assert r.status_code == 200
        assert r.json() == []


# ══════════════════════════════════════════════════════════════════════════════
# Downhill schedule
# ══════════════════════════════════════════════════════════════════════════════

class TestDownhill:
    @pytest.fixture()
    def dh_event(self, client, admin_headers, db):
        return _make_downhill_event(client, admin_headers, db)

    @pytest.fixture()
    def dh_class(self, client, admin_headers, dh_event):
        return _make_class(client, admin_headers, dh_event)

    @pytest.fixture()
    def dh_participant(self, client, nennung_headers, dh_event, dh_class):
        return _make_participant(client, nennung_headers, dh_event, dh_class)

    def test_list_schedule_empty(self, client, zeitnahme_headers, dh_event):
        r = client.get(f"/api/events/{dh_event}/schedule", headers=zeitnahme_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_list_schedule_requires_auth(self, client, viewer_headers, dh_event):
        r = client.get(f"/api/events/{dh_event}/schedule", headers=viewer_headers)
        assert r.status_code == 403

    def test_create_schedule_entry(self, client, admin_headers, zeitnahme_headers,
                                   dh_event, dh_class, dh_participant):
        r = client.post(f"/api/events/{dh_event}/schedule", json={
            "participant_id": dh_participant, "scheduled_start": "10:00:00",
        }, headers=admin_headers)
        assert r.status_code == 201
        data = r.json()
        assert data["participant_id"] == dh_participant
        assert data["finished"] is False

    def test_create_schedule_non_downhill_400(self, client, admin_headers,
                                               event_id, class_id, participant_id):
        r = client.post(f"/api/events/{event_id}/schedule", json={
            "participant_id": participant_id, "scheduled_start": "10:00:00",
        }, headers=admin_headers)
        assert r.status_code == 400

    def test_create_schedule_unknown_participant_404(self, client, admin_headers, dh_event):
        r = client.post(f"/api/events/{dh_event}/schedule", json={
            "participant_id": 99999, "scheduled_start": "10:00:00",
        }, headers=admin_headers)
        assert r.status_code == 404

    def test_create_schedule_duplicate_409(self, client, admin_headers,
                                           dh_event, dh_class, dh_participant):
        client.post(f"/api/events/{dh_event}/schedule", json={
            "participant_id": dh_participant, "scheduled_start": "10:00:00",
        }, headers=admin_headers)
        r = client.post(f"/api/events/{dh_event}/schedule", json={
            "participant_id": dh_participant, "scheduled_start": "10:05:00",
        }, headers=admin_headers)
        assert r.status_code == 409

    def test_next_starter(self, client, admin_headers, zeitnahme_headers,
                          dh_event, dh_class, dh_participant):
        client.post(f"/api/events/{dh_event}/schedule", json={
            "participant_id": dh_participant, "scheduled_start": "09:00:00",
        }, headers=admin_headers)
        r = client.get(f"/api/events/{dh_event}/schedule/next", headers=zeitnahme_headers)
        assert r.status_code == 200
        assert r.json()["participant_id"] == dh_participant

    def test_next_starter_empty(self, client, zeitnahme_headers, dh_event):
        r = client.get(f"/api/events/{dh_event}/schedule/next", headers=zeitnahme_headers)
        assert r.status_code == 200
        assert r.json() is None

    def test_update_schedule_entry(self, client, admin_headers,
                                   dh_event, dh_class, dh_participant):
        sid = client.post(f"/api/events/{dh_event}/schedule", json={
            "participant_id": dh_participant, "scheduled_start": "10:00:00",
        }, headers=admin_headers).json()["id"]
        r = client.patch(f"/api/events/{dh_event}/schedule/{sid}",
                         json={"scheduled_start": "11:30:00"}, headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["scheduled_start"] == "11:30:00"

    def test_update_schedule_no_fields_422(self, client, admin_headers,
                                           dh_event, dh_class, dh_participant):
        sid = client.post(f"/api/events/{dh_event}/schedule", json={
            "participant_id": dh_participant, "scheduled_start": "10:00:00",
        }, headers=admin_headers).json()["id"]
        r = client.patch(f"/api/events/{dh_event}/schedule/{sid}",
                         json={}, headers=admin_headers)
        assert r.status_code == 422

    def test_update_schedule_404(self, client, admin_headers, dh_event):
        r = client.patch(f"/api/events/{dh_event}/schedule/99999",
                         json={"scheduled_start": "12:00:00"}, headers=admin_headers)
        assert r.status_code == 404

    def test_delete_schedule_entry(self, client, admin_headers,
                                   dh_event, dh_class, dh_participant):
        sid = client.post(f"/api/events/{dh_event}/schedule", json={
            "participant_id": dh_participant, "scheduled_start": "10:00:00",
        }, headers=admin_headers).json()["id"]
        r = client.delete(f"/api/events/{dh_event}/schedule/{sid}", headers=admin_headers)
        assert r.status_code == 204

    def test_delete_schedule_404(self, client, admin_headers, dh_event):
        r = client.delete(f"/api/events/{dh_event}/schedule/99999", headers=admin_headers)
        assert r.status_code == 404

    def test_bulk_import_schedule(self, client, admin_headers, nennung_headers,
                                  dh_event, dh_class, dh_participant):
        pid2 = _make_participant(client, nennung_headers, dh_event, dh_class, start_number=77)
        r = client.post(f"/api/events/{dh_event}/schedule/bulk", json=[
            {"participant_id": dh_participant, "scheduled_start": "09:00:00"},
            {"participant_id": pid2, "scheduled_start": "09:05:00"},
        ], headers=admin_headers)
        assert r.status_code == 201
        assert len(r.json()) == 2

    def test_list_schedule_with_lane_filter(self, client, admin_headers, zeitnahme_headers,
                                            dh_event, dh_class, dh_participant):
        client.post(f"/api/events/{dh_event}/schedule", json={
            "participant_id": dh_participant, "scheduled_start": "10:00:00", "lane": "A",
        }, headers=admin_headers)
        r = client.get(f"/api/events/{dh_event}/schedule?lane=A", headers=zeitnahme_headers)
        assert r.status_code == 200
        assert len(r.json()) == 1
        r2 = client.get(f"/api/events/{dh_event}/schedule?lane=B", headers=zeitnahme_headers)
        assert r2.json() == []


# ══════════════════════════════════════════════════════════════════════════════
# Assets
# ══════════════════════════════════════════════════════════════════════════════

class TestAssets:
    def test_list_no_assets_dir(self, client):
        import routers.assets as assets_mod
        with patch.object(assets_mod, "_ASSETS", pathlib.Path("/nonexistent_dir_xyz_12345")):
            r = client.get("/api/assets/files")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_with_files(self, client):
        import routers.assets as assets_mod
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp)
            (p / "logos").mkdir()
            (p / "logos" / "test.png").write_bytes(b"\x89PNG\r\n")
            (p / "standalone.pdf").write_bytes(b"%PDF-1")
            with patch.object(assets_mod, "_ASSETS", p):
                r = client.get("/api/assets/files")
        assert r.status_code == 200
        files = r.json()
        names = [f["name"] for f in files]
        assert "test.png" in names
        assert "standalone.pdf" in names
        logo = next(f for f in files if f["name"] == "test.png")
        assert logo["category"] == "logos"
        assert logo["category_label"] == "Logos"


# ══════════════════════════════════════════════════════════════════════════════
# Broadcast manager (unit tests — no HTTP needed)
# ══════════════════════════════════════════════════════════════════════════════

class TestBroadcastManager:
    def test_broadcast_no_connections(self):
        from broadcast import BroadcastManager
        mgr = BroadcastManager()
        asyncio.run(mgr.broadcast({"type": "test"}))  # must not raise

    def test_connect_and_disconnect(self):
        from broadcast import BroadcastManager
        mgr = BroadcastManager()
        ws = MagicMock()

        async def _noop():
            return None

        async def _run():
            ws.accept = MagicMock(return_value=_noop())
            await mgr.connect(ws)
            assert ws in mgr._connections
            mgr.disconnect(ws)
            assert ws not in mgr._connections

        asyncio.run(_run())

    def test_broadcast_removes_dead_connections(self):
        from broadcast import BroadcastManager
        mgr = BroadcastManager()

        async def _bad_send(msg):
            raise RuntimeError("connection closed")

        ws = MagicMock()
        ws.send_json = _bad_send
        mgr._connections.add(ws)

        asyncio.run(mgr.broadcast({"type": "test"}))
        assert ws not in mgr._connections
