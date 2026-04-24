from __future__ import annotations
import pytest


def _make_penalty_def(db) -> int:
    """Insert a Reglement + PenaltyDefinition; return the penalty_definition_id."""
    cur = db.execute(
        "INSERT INTO Reglements (name, scoring_type) VALUES (?,?)",
        ("Test-Reglement", "sum_all"),
    )
    reg_id = cur.lastrowid
    cur = db.execute(
        "INSERT INTO PenaltyDefinitions (reglement_id, label, seconds) VALUES (?,?,?)",
        (reg_id, "Pylone", 5.0),
    )
    db.commit()
    return cur.lastrowid


def _post_result(client, event_id, participant_id, class_id, run, time,
                 headers, status="valid"):
    return client.post(f"/api/events/{event_id}/results", json={
        "participant_id": participant_id,
        "class_id": class_id,
        "run_number": run,
        "raw_time": time,
        "status": status,
    }, headers=headers)


# ── Create result ─────────────────────────────────────────────────────────────

def test_create_result(client, event_id, participant_id, class_id, zeitnahme_headers):
    r = _post_result(client, event_id, participant_id, class_id, 1, 45.3, zeitnahme_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["raw_time"] == pytest.approx(45.3)
    assert data["run_number"] == 1
    assert data["event_id"] == event_id


def test_create_result_by_admin(client, event_id, participant_id, class_id, admin_headers):
    r = _post_result(client, event_id, participant_id, class_id, 1, 40.0, admin_headers)
    assert r.status_code == 201


def test_create_result_forbidden_for_nennung(client, event_id, participant_id,
                                             class_id, nennung_headers):
    r = _post_result(client, event_id, participant_id, class_id, 1, 40.0, nennung_headers)
    assert r.status_code == 403


def test_create_result_forbidden_without_token(client, event_id, participant_id, class_id):
    r = client.post(f"/api/events/{event_id}/results", json={
        "participant_id": participant_id, "class_id": class_id,
        "run_number": 1, "raw_time": 40.0,
    })
    assert r.status_code in (401, 403)


def test_duplicate_result_raises_409(client, event_id, participant_id, class_id, zeitnahme_headers):
    body = dict(participant_id=participant_id, class_id=class_id, run_number=1, raw_time=40.0)
    client.post(f"/api/events/{event_id}/results", json=body, headers=zeitnahme_headers)
    r = client.post(f"/api/events/{event_id}/results", json=body, headers=zeitnahme_headers)
    assert r.status_code == 409


# ── Standings ─────────────────────────────────────────────────────────────────

def test_standings_empty(client, event_id):
    r = client.get(f"/api/events/{event_id}/standings")
    assert r.status_code == 200
    assert r.json() == []


def test_standings_single_participant(client, event_id, participant_id,
                                      class_id, zeitnahme_headers):
    _post_result(client, event_id, participant_id, class_id, 1, 42.0, zeitnahme_headers)
    _post_result(client, event_id, participant_id, class_id, 2, 44.0, zeitnahme_headers)

    r = client.get(f"/api/events/{event_id}/standings")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["rank"] == 1
    assert rows[0]["total_time"] == pytest.approx(86.0)
    assert rows[0]["valid_runs"] == 2


def test_standings_training_run_excluded(client, event_id, participant_id,
                                         class_id, zeitnahme_headers):
    _post_result(client, event_id, participant_id, class_id, 0, 30.0, zeitnahme_headers)

    r = client.get(f"/api/events/{event_id}/standings")
    assert r.json() == []  # training run (run_number=0) not counted


def test_standings_ranking_order(client, db, event_id, class_id, admin_headers,
                                 nennung_headers, zeitnahme_headers):
    def _add_p(name, nr):
        r = client.post(f"/api/events/{event_id}/participants", json={
            "first_name": name, "last_name": "Test",
            "class_id": class_id, "start_number": nr,
        }, headers=nennung_headers)
        return r.json()["id"]

    slow = _add_p("Slow", 11)
    fast = _add_p("Fast", 12)

    _post_result(client, event_id, slow, class_id, 1, 60.0, zeitnahme_headers)
    _post_result(client, event_id, fast, class_id, 1, 40.0, zeitnahme_headers)

    rows = client.get(f"/api/events/{event_id}/standings",
                      params={"class_id": class_id}).json()
    assert rows[0]["first_name"] == "Fast"
    assert rows[0]["rank"] == 1
    assert rows[1]["first_name"] == "Slow"
    assert rows[1]["rank"] == 2


# ── Penalties ─────────────────────────────────────────────────────────────────

def test_add_penalty_affects_standings(client, db, event_id, participant_id,
                                       class_id, zeitnahme_headers):
    pen_def_id = _make_penalty_def(db)

    r = _post_result(client, event_id, participant_id, class_id, 1, 40.0, zeitnahme_headers)
    result_id = r.json()["id"]

    r = client.post(f"/api/events/{event_id}/results/{result_id}/penalties",
                    json={"penalty_definition_id": pen_def_id, "count": 2},
                    headers=zeitnahme_headers)
    assert r.status_code == 201

    rows = client.get(f"/api/events/{event_id}/standings").json()
    assert rows[0]["total_time"] == pytest.approx(50.0)  # 40 + 2 * 5


def test_list_penalties(client, db, event_id, participant_id, class_id, zeitnahme_headers):
    pen_def_id = _make_penalty_def(db)

    r = _post_result(client, event_id, participant_id, class_id, 1, 40.0, zeitnahme_headers)
    result_id = r.json()["id"]
    client.post(f"/api/events/{event_id}/results/{result_id}/penalties",
                json={"penalty_definition_id": pen_def_id, "count": 1},
                headers=zeitnahme_headers)

    r = client.get(f"/api/events/{event_id}/results/{result_id}/penalties")
    assert r.status_code == 200
    assert len(r.json()) == 1


# ── Update result (Schiri) ────────────────────────────────────────────────────

def test_update_result_by_schiri(client, event_id, participant_id, class_id,
                                 zeitnahme_headers, schiri_headers):
    r = _post_result(client, event_id, participant_id, class_id, 1, 40.0, zeitnahme_headers)
    result_id = r.json()["id"]

    r = client.patch(f"/api/events/{event_id}/results/{result_id}",
                     json={"raw_time": 38.5, "reason": "Korrektur nach Protest"},
                     headers=schiri_headers)
    assert r.status_code == 200
    assert r.json()["raw_time"] == pytest.approx(38.5)


def test_update_result_forbidden_for_zeitnahme(client, event_id, participant_id,
                                               class_id, zeitnahme_headers):
    r = _post_result(client, event_id, participant_id, class_id, 1, 40.0, zeitnahme_headers)
    result_id = r.json()["id"]

    r = client.patch(f"/api/events/{event_id}/results/{result_id}",
                     json={"raw_time": 38.5, "reason": "Versuch"},
                     headers=zeitnahme_headers)
    assert r.status_code == 403


def test_update_result_not_found(client, event_id, schiri_headers):
    r = client.patch(f"/api/events/{event_id}/results/9999",
                     json={"raw_time": 38.5, "reason": "Test"},
                     headers=schiri_headers)
    assert r.status_code == 404


# ── Run-results view ──────────────────────────────────────────────────────────

def test_run_results_view(client, event_id, participant_id, class_id, zeitnahme_headers):
    _post_result(client, event_id, participant_id, class_id, 1, 42.0, zeitnahme_headers)

    r = client.get(f"/api/events/{event_id}/run-results")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["raw_time"] == pytest.approx(42.0)
    assert rows[0]["total_penalties"] == pytest.approx(0.0)
    assert rows[0]["total_time"] == pytest.approx(42.0)
