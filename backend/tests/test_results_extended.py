"""
Extended tests for results.py — covers the paths not reached by test_results.py:
update_result, penalties, audit-log, run-results view, standings, statistics,
_fmt helper, and the full CSV export.
"""
from __future__ import annotations
import pytest


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_result(client, headers, event_id, class_id, participant_id,
                 run_number=1, raw_time=45.123, status="valid"):
    r = client.post(f"/api/events/{event_id}/results", json={
        "participant_id": participant_id,
        "class_id": class_id,
        "run_number": run_number,
        "raw_time": raw_time,
        "status": status,
    }, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _make_penalty_def(client, admin_headers, reglement_id):
    r = client.post(f"/api/reglements/{reglement_id}/penalties",
                    json={"label": "Kegel", "seconds": 2.0},
                    headers=admin_headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.fixture()
def running_class(client, admin_headers, event_id):
    """Class with run_status='running' so results can be booked."""
    r = client.post(f"/api/events/{event_id}/classes", json={
        "name": "Laufende Klasse", "short_name": "LK", "run_status": "running",
    }, headers=admin_headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.fixture()
def runner(client, nennung_headers, event_id, running_class):
    r = client.post(f"/api/events/{event_id}/participants", json={
        "first_name": "Karl", "last_name": "Fahrer",
        "birth_year": 2008, "class_id": running_class, "start_number": 7,
    }, headers=nennung_headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.fixture()
def result_id(client, zeitnahme_headers, event_id, running_class, runner):
    return _make_result(client, zeitnahme_headers, event_id, running_class, runner)


@pytest.fixture()
def reglement_id(client, admin_headers):
    r = client.post("/api/reglements/", json={
        "name": "Testreg", "scoring_type": "sum_all",
    }, headers=admin_headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


# ── list_results (with filters) ───────────────────────────────────────────────

class TestListResults:
    def test_list_by_class(self, client, event_id, running_class, result_id):
        r = client.get(f"/api/events/{event_id}/results?class_id={running_class}")
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["id"] == result_id

    def test_list_by_run_number(self, client, event_id, running_class, result_id):
        r = client.get(f"/api/events/{event_id}/results?run_number=1")
        assert r.status_code == 200
        assert any(res["id"] == result_id for res in r.json())

    def test_list_by_class_and_run(self, client, event_id, running_class, result_id):
        r = client.get(f"/api/events/{event_id}/results?class_id={running_class}&run_number=1")
        assert r.status_code == 200
        assert len(r.json()) == 1


# ── create_result error paths ─────────────────────────────────────────────────

class TestCreateResult:
    def test_class_not_running_409(self, client, admin_headers, zeitnahme_headers,
                                    event_id, participant_id):
        cid = client.post(f"/api/events/{event_id}/classes", json={
            "name": "Geplant", "short_name": "GP", "run_status": "planned",
        }, headers=admin_headers).json()["id"]
        r = client.post(f"/api/events/{event_id}/results", json={
            "participant_id": participant_id, "class_id": cid, "run_number": 1,
        }, headers=zeitnahme_headers)
        assert r.status_code == 409

    def test_exhibition_class_bypasses_running_check(self, client, admin_headers,
                                                      zeitnahme_headers, nennung_headers,
                                                      event_id):
        cid = client.post(f"/api/events/{event_id}/classes", json={
            "name": "Vorstarter", "short_name": "VS", "run_status": "planned",
            "is_exhibition": True,
        }, headers=admin_headers).json()["id"]
        pid = client.post(f"/api/events/{event_id}/participants", json={
            "first_name": "E", "last_name": "X", "birth_year": 2012,
            "class_id": cid, "start_number": 99,
        }, headers=nennung_headers).json()["id"]
        r = client.post(f"/api/events/{event_id}/results", json={
            "participant_id": pid, "class_id": cid, "run_number": 1, "raw_time": 30.0,
        }, headers=zeitnahme_headers)
        assert r.status_code == 201

    def test_duplicate_result_409(self, client, zeitnahme_headers, event_id,
                                   running_class, runner, result_id):
        r = client.post(f"/api/events/{event_id}/results", json={
            "participant_id": runner, "class_id": running_class, "run_number": 1,
        }, headers=zeitnahme_headers)
        assert r.status_code == 409


# ── update_result ─────────────────────────────────────────────────────────────

class TestUpdateResult:
    def test_update_time(self, client, schiri_headers, event_id, result_id):
        r = client.patch(f"/api/events/{event_id}/results/{result_id}",
                         json={"raw_time": 42.5, "reason": "Korrektur Lichtschranke"},
                         headers=schiri_headers)
        assert r.status_code == 200
        assert r.json()["raw_time"] == 42.5

    def test_update_status(self, client, schiri_headers, event_id, result_id):
        r = client.patch(f"/api/events/{event_id}/results/{result_id}",
                         json={"status": "dnf", "reason": "Abbruch"},
                         headers=schiri_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "dnf"

    def test_update_is_official(self, client, schiri_headers, event_id, result_id):
        r = client.patch(f"/api/events/{event_id}/results/{result_id}",
                         json={"is_official": True, "reason": "Freigabe"},
                         headers=schiri_headers)
        assert r.status_code == 200
        assert r.json()["is_official"] is True

    def test_update_404(self, client, schiri_headers, event_id):
        r = client.patch(f"/api/events/{event_id}/results/99999",
                         json={"status": "dnf", "reason": "Test"},
                         headers=schiri_headers)
        assert r.status_code == 404

    def test_update_blocked_when_official(self, client, admin_headers, schiri_headers,
                                           event_id, running_class, runner):
        rid = _make_result(client, schiri_headers, event_id, running_class, runner, run_number=2)
        # set class to official
        client.patch(f"/api/events/{event_id}/classes/{running_class}",
                     json={"run_status": "official"}, headers=admin_headers)
        r = client.patch(f"/api/events/{event_id}/results/{rid}",
                         json={"status": "dnf", "reason": "Versuch"}, headers=schiri_headers)
        assert r.status_code == 409

    def test_update_requires_schiri(self, client, zeitnahme_headers, event_id, result_id):
        r = client.patch(f"/api/events/{event_id}/results/{result_id}",
                         json={"status": "dnf", "reason": "Test"},
                         headers=zeitnahme_headers)
        assert r.status_code == 403


# ── penalties ─────────────────────────────────────────────────────────────────

class TestPenalties:
    def test_list_empty(self, client, event_id, result_id):
        r = client.get(f"/api/events/{event_id}/results/{result_id}/penalties")
        assert r.status_code == 200
        assert r.json() == []

    def test_add_and_list(self, client, admin_headers, zeitnahme_headers,
                          event_id, result_id, reglement_id):
        pen_def_id = _make_penalty_def(client, admin_headers, reglement_id)
        r = client.post(f"/api/events/{event_id}/results/{result_id}/penalties",
                        json={"penalty_definition_id": pen_def_id, "count": 2},
                        headers=zeitnahme_headers)
        assert r.status_code == 201
        data = r.json()
        assert data["count"] == 2
        assert data["penalty_definition_id"] == pen_def_id

    def test_delete_penalty(self, client, admin_headers, schiri_headers,
                             zeitnahme_headers, event_id, result_id, reglement_id):
        pen_def_id = _make_penalty_def(client, admin_headers, reglement_id)
        pid = client.post(f"/api/events/{event_id}/results/{result_id}/penalties",
                          json={"penalty_definition_id": pen_def_id},
                          headers=zeitnahme_headers).json()["id"]
        r = client.delete(f"/api/events/{event_id}/results/{result_id}/penalties/{pid}",
                          headers=schiri_headers)
        assert r.status_code == 204

    def test_delete_penalty_blocked_when_official(self, client, admin_headers,
                                                   schiri_headers, zeitnahme_headers,
                                                   event_id, running_class, runner, reglement_id):
        rid = _make_result(client, zeitnahme_headers, event_id, running_class, runner, run_number=3)
        pen_def_id = _make_penalty_def(client, admin_headers, reglement_id)
        pen_id = client.post(f"/api/events/{event_id}/results/{rid}/penalties",
                             json={"penalty_definition_id": pen_def_id},
                             headers=zeitnahme_headers).json()["id"]
        client.patch(f"/api/events/{event_id}/classes/{running_class}",
                     json={"run_status": "official"}, headers=admin_headers)
        r = client.delete(f"/api/events/{event_id}/results/{rid}/penalties/{pen_id}",
                          headers=schiri_headers)
        assert r.status_code == 409


# ── audit-log ─────────────────────────────────────────────────────────────────

class TestAuditLog:
    def test_empty(self, client, event_id):
        r = client.get(f"/api/events/{event_id}/audit-log")
        assert r.status_code == 200
        assert r.json() == []

    def test_entry_after_update(self, client, schiri_headers, event_id, result_id, running_class):
        client.patch(f"/api/events/{event_id}/results/{result_id}",
                     json={"raw_time": 50.0, "reason": "Audit-Test"},
                     headers=schiri_headers)
        r = client.get(f"/api/events/{event_id}/audit-log")
        assert r.status_code == 200
        assert len(r.json()) >= 1
        assert r.json()[0]["reason"] == "Audit-Test"

    def test_filter_by_class(self, client, schiri_headers, event_id, result_id, running_class):
        client.patch(f"/api/events/{event_id}/results/{result_id}",
                     json={"status": "dnf", "reason": "Klassenfilter"},
                     headers=schiri_headers)
        r = client.get(f"/api/events/{event_id}/audit-log?class_id={running_class}")
        assert r.status_code == 200
        assert len(r.json()) >= 1


# ── run-results view ──────────────────────────────────────────────────────────

class TestRunResults:
    def test_empty(self, client, event_id):
        r = client.get(f"/api/events/{event_id}/run-results")
        assert r.status_code == 200
        assert r.json() == []

    def test_with_result(self, client, event_id, running_class, result_id):
        r = client.get(f"/api/events/{event_id}/run-results?class_id={running_class}")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_filter_by_run_number(self, client, event_id, running_class, result_id):
        r = client.get(f"/api/events/{event_id}/run-results?run_number=1")
        assert r.status_code == 200
        r2 = client.get(f"/api/events/{event_id}/run-results?run_number=9")
        assert r2.json() == []


# ── standings view ────────────────────────────────────────────────────────────

class TestStandings:
    def test_empty(self, client, event_id):
        r = client.get(f"/api/events/{event_id}/standings")
        assert r.status_code == 200
        assert r.json() == []

    def test_with_result(self, client, event_id, running_class, result_id):
        r = client.get(f"/api/events/{event_id}/standings?class_id={running_class}")
        assert r.status_code == 200
        assert len(r.json()) == 1
        row = r.json()[0]
        assert row["class_id"] == running_class
        assert row["rank"] == 1
        assert row["valid_runs"] == 1


# ── statistics ────────────────────────────────────────────────────────────────

class TestStatistics:
    def test_empty(self, client, event_id):
        r = client.get(f"/api/events/{event_id}/statistics")
        assert r.status_code == 200
        data = r.json()
        assert data["fastest_per_class"] == []
        assert data["fastest_dame"] is None
        assert data["fastest_herr"] is None

    def test_with_gendered_results(self, client, admin_headers, zeitnahme_headers,
                                   nennung_headers, event_id, running_class):
        # male driver
        pid_m = client.post(f"/api/events/{event_id}/participants", json={
            "first_name": "Hans", "last_name": "M", "birth_year": 2005,
            "class_id": running_class, "start_number": 21, "gender": "m",
        }, headers=nennung_headers).json()["id"]
        # female driver
        pid_w = client.post(f"/api/events/{event_id}/participants", json={
            "first_name": "Lena", "last_name": "W", "birth_year": 2006,
            "class_id": running_class, "start_number": 22, "gender": "w",
        }, headers=nennung_headers).json()["id"]
        _make_result(client, zeitnahme_headers, event_id, running_class, pid_m,
                     run_number=1, raw_time=40.0)
        _make_result(client, zeitnahme_headers, event_id, running_class, pid_w,
                     run_number=1, raw_time=42.0)
        r = client.get(f"/api/events/{event_id}/statistics")
        assert r.status_code == 200
        data = r.json()
        assert data["fastest_herr"] is not None
        assert data["fastest_dame"] is not None


# ── CSV export ────────────────────────────────────────────────────────────────

class TestExportCSV:
    def test_export_no_event_404(self, client):
        r = client.get("/api/events/99999/results/export")
        assert r.status_code == 404

    def test_export_empty_event(self, client, event_id):
        r = client.get(f"/api/events/{event_id}/results/export")
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]
        # no classes → empty body (just BOM)
        assert len(r.content) <= 4

    def test_export_with_results(self, client, zeitnahme_headers, nennung_headers,
                                  event_id, running_class, runner, result_id):
        r = client.get(f"/api/events/{event_id}/results/export")
        assert r.status_code == 200
        text = r.content.decode("utf-8-sig")
        assert "Karl" in text
        assert "Fahrer" in text

    def test_export_filter_by_class(self, client, event_id, running_class, result_id):
        r = client.get(f"/api/events/{event_id}/results/export?class_id={running_class}")
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]

    def test_export_multi_run_with_penalties(self, client, admin_headers, schiri_headers,
                                              zeitnahme_headers, nennung_headers,
                                              event_id, running_class, runner, reglement_id):
        # 2nd run
        rid2 = _make_result(client, zeitnahme_headers, event_id, running_class, runner,
                             run_number=2, raw_time=43.5)
        # add a penalty to run 1
        pen_def_id = _make_penalty_def(client, admin_headers, reglement_id)
        rid1 = _make_result(client, zeitnahme_headers, event_id, running_class,
                            client.post(f"/api/events/{event_id}/participants", json={
                                "first_name": "B", "last_name": "C", "birth_year": 2009,
                                "class_id": running_class, "start_number": 88,
                            }, headers=nennung_headers).json()["id"],
                            run_number=1, raw_time=60.0)
        client.post(f"/api/events/{event_id}/results/{rid1}/penalties",
                    json={"penalty_definition_id": pen_def_id, "count": 1},
                    headers=zeitnahme_headers)
        r = client.get(f"/api/events/{event_id}/results/export?class_id={running_class}")
        assert r.status_code == 200
        text = r.content.decode("utf-8-sig")
        assert "Lauf" in text

    def test_fmt_helper_directly(self):
        from routers.results import _fmt
        assert _fmt(None) == ""
        assert _fmt(0.0, zero_as_dash=True) == "0.000"
        assert _fmt(0.0) == "0.000"
        assert _fmt(30.5) == "30.500"
        assert _fmt(65.25) == "1:05.250"
        assert _fmt(125.0) == "2:05.000"
