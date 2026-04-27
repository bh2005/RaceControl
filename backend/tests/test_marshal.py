from __future__ import annotations
import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _report(client, headers, **kwargs):
    body = {"penalty_seconds": 5.0, "station": "Posten 1", **kwargs}
    return client.post("/api/marshal/report", json=body, headers=headers)


# ── POST /marshal/report ──────────────────────────────────────────────────────

def test_report_by_marshal(client, marshal_headers):
    r = _report(client, marshal_headers)
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert "ts" in data


def test_report_by_admin(client, admin_headers):
    r = _report(client, admin_headers)
    assert r.status_code == 200


def test_report_forbidden_for_viewer(client, viewer_headers):
    r = _report(client, viewer_headers)
    assert r.status_code == 403


def test_report_forbidden_for_zeitnahme(client, zeitnahme_headers):
    r = _report(client, zeitnahme_headers)
    assert r.status_code == 403


def test_report_forbidden_without_token(client):
    r = client.post("/api/marshal/report",
                    json={"penalty_seconds": 5.0, "station": "Posten 1"})
    assert r.status_code in (401, 403)


def test_report_empty_station_rejected(client, marshal_headers):
    r = _report(client, marshal_headers, station="   ")
    assert r.status_code == 422


def test_report_zero_penalty_rejected(client, marshal_headers):
    r = _report(client, marshal_headers, penalty_seconds=0)
    assert r.status_code == 422


def test_report_negative_penalty_rejected(client, marshal_headers):
    r = _report(client, marshal_headers, penalty_seconds=-5.0)
    assert r.status_code == 422


def test_report_with_event_and_class(client, marshal_headers, event_id, class_id):
    r = _report(client, marshal_headers, event_id=event_id,
                class_id=class_id, class_name="Klasse A", penalty_label="Pylone")
    assert r.status_code == 200
    assert "id" in r.json()


def test_report_stored_in_db(client, db, marshal_headers, event_id):
    _report(client, marshal_headers, event_id=event_id)
    rows = db.execute("SELECT * FROM MarshalReports WHERE event_id=?", (event_id,)).fetchall()
    assert len(rows) == 1
    assert rows[0]["cancelled"] == 0


# ── POST /marshal/cancel ──────────────────────────────────────────────────────

def test_cancel_by_marshal(client, db, marshal_headers):
    r = _report(client, marshal_headers)
    report_id = r.json()["id"]
    ts = r.json()["ts"]

    r = client.post("/api/marshal/cancel",
                    json={"ts": ts, "report_id": report_id},
                    headers=marshal_headers)
    assert r.status_code == 204

    row = db.execute("SELECT cancelled FROM MarshalReports WHERE id=?", (report_id,)).fetchone()
    assert row["cancelled"] == 1


def test_cancel_by_admin(client, db, marshal_headers, admin_headers):
    r = _report(client, marshal_headers)
    report_id = r.json()["id"]
    ts = r.json()["ts"]

    r = client.post("/api/marshal/cancel",
                    json={"ts": ts, "report_id": report_id},
                    headers=admin_headers)
    assert r.status_code == 204


def test_cancel_forbidden_for_zeitnahme(client, marshal_headers, zeitnahme_headers):
    r = _report(client, marshal_headers)
    ts = r.json()["ts"]
    r = client.post("/api/marshal/cancel",
                    json={"ts": ts}, headers=zeitnahme_headers)
    assert r.status_code == 403


def test_cancel_without_report_id_is_ok(client, marshal_headers):
    r = _report(client, marshal_headers)
    ts = r.json()["ts"]
    r = client.post("/api/marshal/cancel", json={"ts": ts}, headers=marshal_headers)
    assert r.status_code == 204


# ── GET /marshal/reports ──────────────────────────────────────────────────────

def test_list_reports_by_admin(client, admin_headers):
    r = client.get("/api/marshal/reports", headers=admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_reports_by_zeitnahme(client, zeitnahme_headers):
    r = client.get("/api/marshal/reports", headers=zeitnahme_headers)
    assert r.status_code == 200


def test_list_reports_by_schiri(client, schiri_headers):
    r = client.get("/api/marshal/reports", headers=schiri_headers)
    assert r.status_code == 200


def test_list_reports_by_viewer(client, viewer_headers):
    r = client.get("/api/marshal/reports", headers=viewer_headers)
    assert r.status_code == 200


def test_list_reports_forbidden_for_nennung(client, nennung_headers):
    r = client.get("/api/marshal/reports", headers=nennung_headers)
    assert r.status_code == 403


def test_list_reports_forbidden_for_marshal(client, marshal_headers):
    r = client.get("/api/marshal/reports", headers=marshal_headers)
    assert r.status_code == 403


def test_list_reports_filter_by_event(client, db, marshal_headers, admin_headers, event_id):
    _report(client, marshal_headers, event_id=event_id)
    _report(client, marshal_headers, event_id=None)

    r = client.get("/api/marshal/reports",
                   params={"event_id": event_id}, headers=admin_headers)
    rows = r.json()
    assert all(row["event_id"] == event_id for row in rows)
    assert len(rows) == 1


def test_list_reports_filter_cancelled(client, db, marshal_headers, admin_headers):
    r1 = _report(client, marshal_headers)
    r2 = _report(client, marshal_headers)
    ts1, id1 = r1.json()["ts"], r1.json()["id"]

    client.post("/api/marshal/cancel",
                json={"ts": ts1, "report_id": id1}, headers=marshal_headers)

    r = client.get("/api/marshal/reports",
                   params={"cancelled": 0}, headers=admin_headers)
    ids = [row["id"] for row in r.json()]
    assert id1 not in ids
    assert r2.json()["id"] in ids


def test_list_reports_returns_most_recent_first(client, marshal_headers, admin_headers):
    for i in range(3):
        _report(client, marshal_headers, station=f"Posten {i}")
    rows = client.get("/api/marshal/reports", headers=admin_headers).json()
    assert len(rows) == 3
    # newest first (ts DESC)
    assert rows[0]["ts"] >= rows[1]["ts"] >= rows[2]["ts"]
