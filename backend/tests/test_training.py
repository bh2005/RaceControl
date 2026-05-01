from __future__ import annotations
import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mk_session(client, headers, **kwargs):
    body = {"name": "Testsession", "date": "2026-06-01", "status": "planned", **kwargs}
    return client.post("/api/training/sessions", json=body, headers=headers)


def _mk_run(client, headers, session_id, trainee_id, **kwargs):
    body = {"trainee_id": trainee_id, "raw_time": 55.3,
            "penalty_seconds": 0.0, "status": "valid", "source": "manual", **kwargs}
    return client.post(f"/api/training/sessions/{session_id}/runs",
                       json=body, headers=headers)


# ═══════════════════════════════════════════════════════════════════════════════
# SESSIONS
# ═══════════════════════════════════════════════════════════════════════════════

def test_create_session(client, admin_headers):
    r = _mk_session(client, admin_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Testsession"
    assert data["status"] == "planned"
    assert "id" in data


def test_create_session_forbidden_for_zeitnahme(client, zeitnahme_headers):
    r = _mk_session(client, zeitnahme_headers)
    assert r.status_code == 403


def test_create_session_forbidden_without_token(client):
    r = client.post("/api/training/sessions",
                    json={"name": "X", "date": "2026-06-01", "status": "planned"})
    assert r.status_code in (401, 403)


def test_list_sessions_empty(client, admin_headers):
    r = client.get("/api/training/sessions", headers=admin_headers)
    assert r.status_code == 200
    assert r.json() == []


def test_list_sessions_by_zeitnahme(client, zeitnahme_headers):
    r = client.get("/api/training/sessions", headers=zeitnahme_headers)
    assert r.status_code == 200


def test_list_sessions_forbidden_for_nennung(client, nennung_headers):
    r = client.get("/api/training/sessions", headers=nennung_headers)
    assert r.status_code == 403


def test_list_sessions_returns_created(client, admin_headers, session_id):
    rows = client.get("/api/training/sessions", headers=admin_headers).json()
    assert any(r["id"] == session_id for r in rows)


def test_get_session_by_id(client, admin_headers, session_id):
    r = client.get(f"/api/training/sessions/{session_id}", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["id"] == session_id


def test_get_session_not_found(client, admin_headers):
    r = client.get("/api/training/sessions/99999", headers=admin_headers)
    assert r.status_code == 404


# ── Active session ────────────────────────────────────────────────────────────

def test_get_active_session_when_none(client, admin_headers):
    r = client.get("/api/training/sessions/active", headers=admin_headers)
    assert r.status_code == 404


def test_get_active_session(client, admin_headers, session_id):
    client.patch(f"/api/training/sessions/{session_id}",
                 json={"status": "active"}, headers=admin_headers)
    r = client.get("/api/training/sessions/active", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["id"] == session_id
    assert r.json()["status"] == "active"


def test_single_active_lock(client, admin_headers):
    r1 = _mk_session(client, admin_headers, name="Session 1")
    r2 = _mk_session(client, admin_headers, name="Session 2")
    sid1, sid2 = r1.json()["id"], r2.json()["id"]

    client.patch(f"/api/training/sessions/{sid1}",
                 json={"status": "active"}, headers=admin_headers)
    client.patch(f"/api/training/sessions/{sid2}",
                 json={"status": "active"}, headers=admin_headers)

    s1 = client.get(f"/api/training/sessions/{sid1}", headers=admin_headers).json()
    s2 = client.get(f"/api/training/sessions/{sid2}", headers=admin_headers).json()
    assert s1["status"] == "finished"
    assert s2["status"] == "active"


# ── Update session ────────────────────────────────────────────────────────────

def test_update_session_name(client, admin_headers, session_id):
    r = client.patch(f"/api/training/sessions/{session_id}",
                     json={"name": "Geänderter Name"}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Geänderter Name"


def test_update_session_forbidden_for_zeitnahme(client, zeitnahme_headers, session_id):
    r = client.patch(f"/api/training/sessions/{session_id}",
                     json={"name": "X"}, headers=zeitnahme_headers)
    assert r.status_code == 403


def test_update_session_not_found(client, admin_headers):
    r = client.patch("/api/training/sessions/99999",
                     json={"name": "X"}, headers=admin_headers)
    assert r.status_code == 404


def test_update_session_no_fields(client, admin_headers, session_id):
    r = client.patch(f"/api/training/sessions/{session_id}",
                     json={}, headers=admin_headers)
    assert r.status_code == 422


# ── Delete session ────────────────────────────────────────────────────────────

def test_delete_session(client, admin_headers, session_id):
    r = client.delete(f"/api/training/sessions/{session_id}", headers=admin_headers)
    assert r.status_code == 204

    r = client.get(f"/api/training/sessions/{session_id}", headers=admin_headers)
    assert r.status_code == 404


def test_delete_session_not_found(client, admin_headers):
    r = client.delete("/api/training/sessions/99999", headers=admin_headers)
    assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# RUNS
# ═══════════════════════════════════════════════════════════════════════════════

def test_create_run(client, admin_headers, session_id, trainee_id):
    r = _mk_run(client, admin_headers, session_id, trainee_id)
    assert r.status_code == 201
    data = r.json()
    assert data["raw_time"] == pytest.approx(55.3)
    assert data["run_number"] == 1
    assert data["trainee_id"] == trainee_id
    assert data["session_id"] == session_id


def test_create_run_by_zeitnahme(client, zeitnahme_headers, session_id, trainee_id):
    r = _mk_run(client, zeitnahme_headers, session_id, trainee_id)
    assert r.status_code == 201


def test_create_run_forbidden_for_nennung(client, nennung_headers, session_id, trainee_id):
    r = _mk_run(client, nennung_headers, session_id, trainee_id)
    assert r.status_code == 403


def test_create_run_session_not_found(client, admin_headers, trainee_id):
    r = _mk_run(client, admin_headers, 99999, trainee_id)
    assert r.status_code == 404


# ── Auto-increment run_number ─────────────────────────────────────────────────

def test_run_number_increments_per_trainee(client, admin_headers, session_id, trainee_id):
    r1 = _mk_run(client, admin_headers, session_id, trainee_id)
    r2 = _mk_run(client, admin_headers, session_id, trainee_id)
    r3 = _mk_run(client, admin_headers, session_id, trainee_id)
    assert r1.json()["run_number"] == 1
    assert r2.json()["run_number"] == 2
    assert r3.json()["run_number"] == 3


def test_run_number_independent_per_trainee(client, admin_headers, session_id, trainee_id):
    r2 = client.post("/api/trainees", json={
        "first_name": "Zweiter", "last_name": "Fahrer",
        "birth_year": 2011, "is_active": True,
    }, headers=admin_headers)
    trainee2 = r2.json()["id"]

    a1 = _mk_run(client, admin_headers, session_id, trainee_id)
    b1 = _mk_run(client, admin_headers, session_id, trainee2)
    a2 = _mk_run(client, admin_headers, session_id, trainee_id)
    b2 = _mk_run(client, admin_headers, session_id, trainee2)

    assert a1.json()["run_number"] == 1
    assert b1.json()["run_number"] == 1
    assert a2.json()["run_number"] == 2
    assert b2.json()["run_number"] == 2


# ── Kart-Nummer aus Stammdaten ────────────────────────────────────────────────

def test_kart_number_from_trainee_defaults(client, admin_headers, session_id, trainee_id):
    # trainee_id fixture sets kart_number="42"
    r = _mk_run(client, admin_headers, session_id, trainee_id)
    assert r.json()["kart_number"] == "42"


def test_kart_number_explicit_overrides_default(client, admin_headers, session_id, trainee_id):
    r = _mk_run(client, admin_headers, session_id, trainee_id, kart_number="99")
    assert r.json()["kart_number"] == "99"


# ── List runs ─────────────────────────────────────────────────────────────────

def test_list_runs_empty(client, admin_headers, session_id):
    r = client.get(f"/api/training/sessions/{session_id}/runs", headers=admin_headers)
    assert r.status_code == 200
    assert r.json() == []


def test_list_runs_returns_created(client, admin_headers, session_id, trainee_id):
    _mk_run(client, admin_headers, session_id, trainee_id, raw_time=40.0)
    _mk_run(client, admin_headers, session_id, trainee_id, raw_time=38.5)
    rows = client.get(f"/api/training/sessions/{session_id}/runs",
                      headers=admin_headers).json()
    assert len(rows) == 2


def test_list_runs_session_not_found(client, admin_headers):
    r = client.get("/api/training/sessions/99999/runs", headers=admin_headers)
    assert r.status_code == 404


# ── Update run ────────────────────────────────────────────────────────────────

def test_update_run_raw_time(client, admin_headers, session_id, trainee_id):
    run_id = _mk_run(client, admin_headers, session_id, trainee_id).json()["id"]
    r = client.patch(f"/api/training/sessions/{session_id}/runs/{run_id}",
                     json={"raw_time": 42.1}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["raw_time"] == pytest.approx(42.1)


def test_update_run_status_dns(client, admin_headers, session_id, trainee_id):
    run_id = _mk_run(client, admin_headers, session_id, trainee_id).json()["id"]
    r = client.patch(f"/api/training/sessions/{session_id}/runs/{run_id}",
                     json={"status": "dns"}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "dns"


def test_update_run_not_found(client, admin_headers, session_id):
    r = client.patch(f"/api/training/sessions/{session_id}/runs/99999",
                     json={"raw_time": 1.0}, headers=admin_headers)
    assert r.status_code == 404


def test_update_run_no_fields(client, admin_headers, session_id, trainee_id):
    run_id = _mk_run(client, admin_headers, session_id, trainee_id).json()["id"]
    r = client.patch(f"/api/training/sessions/{session_id}/runs/{run_id}",
                     json={}, headers=admin_headers)
    assert r.status_code == 422


# ── Delete run ────────────────────────────────────────────────────────────────

def test_delete_run(client, admin_headers, session_id, trainee_id):
    run_id = _mk_run(client, admin_headers, session_id, trainee_id).json()["id"]
    r = client.delete(f"/api/training/sessions/{session_id}/runs/{run_id}",
                      headers=admin_headers)
    assert r.status_code == 204

    rows = client.get(f"/api/training/sessions/{session_id}/runs",
                      headers=admin_headers).json()
    assert not any(row["id"] == run_id for row in rows)


def test_delete_run_not_found(client, admin_headers, session_id):
    r = client.delete(f"/api/training/sessions/{session_id}/runs/99999",
                      headers=admin_headers)
    assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# STANDINGS
# ═══════════════════════════════════════════════════════════════════════════════

def test_standings_empty_session(client, admin_headers, session_id):
    r = client.get(f"/api/training/sessions/{session_id}/standings",
                   headers=admin_headers)
    assert r.status_code == 200
    assert r.json() == []


def test_standings_ranked_by_best_time(client, admin_headers, session_id, trainee_id):
    t2 = client.post("/api/trainees", json={
        "first_name": "Zweiter", "last_name": "Fahrer",
        "birth_year": 2011, "is_active": True,
    }, headers=admin_headers).json()["id"]

    _mk_run(client, admin_headers, session_id, trainee_id, raw_time=50.0)
    _mk_run(client, admin_headers, session_id, trainee_id, raw_time=48.5)  # best
    _mk_run(client, admin_headers, session_id, t2, raw_time=46.0)          # faster overall

    rows = client.get(f"/api/training/sessions/{session_id}/standings",
                      headers=admin_headers).json()
    assert len(rows) == 2
    assert rows[0]["trainee_id"] == t2     # 46.0 wins rank 1
    assert rows[0]["rank"] == 1
    assert rows[1]["trainee_id"] == trainee_id
    assert rows[1]["rank"] == 2


def test_standings_dns_excluded_from_best_time(client, admin_headers, session_id, trainee_id):
    _mk_run(client, admin_headers, session_id, trainee_id, raw_time=None, status="dns")
    rows = client.get(f"/api/training/sessions/{session_id}/standings",
                      headers=admin_headers).json()
    # Trainee with only DNS has no best_time → appears last or no valid time
    assert all(row.get("best_time") is None for row in rows if row["trainee_id"] == trainee_id)


def test_standings_session_not_found(client, admin_headers):
    r = client.get("/api/training/sessions/99999/standings", headers=admin_headers)
    assert r.status_code == 404
