from __future__ import annotations
import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _set_status(client, event_id, class_id, status, headers):
    return client.patch(f"/api/events/{event_id}/classes/{class_id}",
                        json={"run_status": status}, headers=headers)


def _auto_close(client, event_id, class_id, headers):
    return client.post(f"/api/events/{event_id}/classes/{class_id}/auto-close",
                       headers=headers)


def _get_class(client, event_id, class_id):
    r = client.get(f"/api/events/{event_id}/classes")
    return next(c for c in r.json() if c["id"] == class_id)


# ── auto-close: role guards ───────────────────────────────────────────────────

def test_auto_close_allowed_for_zeitnahme(client, event_id, class_id, zeitnahme_headers):
    r = _auto_close(client, event_id, class_id, zeitnahme_headers)
    assert r.status_code == 204


def test_auto_close_allowed_for_admin(client, event_id, class_id, admin_headers):
    r = _auto_close(client, event_id, class_id, admin_headers)
    assert r.status_code == 204


def test_auto_close_allowed_for_schiri(client, event_id, class_id, schiri_headers):
    r = _auto_close(client, event_id, class_id, schiri_headers)
    assert r.status_code == 204


def test_auto_close_forbidden_for_nennung(client, event_id, class_id, nennung_headers):
    r = _auto_close(client, event_id, class_id, nennung_headers)
    assert r.status_code == 403


def test_auto_close_forbidden_for_marshal(client, event_id, class_id, marshal_headers):
    r = _auto_close(client, event_id, class_id, marshal_headers)
    assert r.status_code == 403


# ── auto-close: status transitions ───────────────────────────────────────────

def test_auto_close_running_becomes_preliminary(client, event_id, class_id,
                                                admin_headers, zeitnahme_headers):
    _set_status(client, event_id, class_id, "running", admin_headers)
    _auto_close(client, event_id, class_id, zeitnahme_headers)
    cls = _get_class(client, event_id, class_id)
    assert cls["run_status"] == "preliminary"


def test_auto_close_paused_becomes_preliminary(client, event_id, class_id,
                                               admin_headers, zeitnahme_headers):
    _set_status(client, event_id, class_id, "paused", admin_headers)
    _auto_close(client, event_id, class_id, zeitnahme_headers)
    cls = _get_class(client, event_id, class_id)
    assert cls["run_status"] == "preliminary"


def test_auto_close_sets_end_time(client, db, event_id, class_id,
                                  admin_headers, zeitnahme_headers):
    _set_status(client, event_id, class_id, "running", admin_headers)
    _auto_close(client, event_id, class_id, zeitnahme_headers)
    row = db.execute("SELECT end_time FROM Classes WHERE id=?", (class_id,)).fetchone()
    assert row["end_time"] is not None


def test_auto_close_no_op_for_planned(client, event_id, class_id,
                                      admin_headers, zeitnahme_headers):
    _set_status(client, event_id, class_id, "planned", admin_headers)
    r = _auto_close(client, event_id, class_id, zeitnahme_headers)
    assert r.status_code == 204
    cls = _get_class(client, event_id, class_id)
    assert cls["run_status"] == "planned"  # unchanged


def test_auto_close_no_op_for_official(client, event_id, class_id,
                                       admin_headers, zeitnahme_headers):
    _set_status(client, event_id, class_id, "official", admin_headers)
    r = _auto_close(client, event_id, class_id, zeitnahme_headers)
    assert r.status_code == 204
    cls = _get_class(client, event_id, class_id)
    assert cls["run_status"] == "official"  # unchanged


def test_auto_close_no_op_for_already_preliminary(client, event_id, class_id,
                                                   admin_headers, zeitnahme_headers):
    _set_status(client, event_id, class_id, "preliminary", admin_headers)
    r = _auto_close(client, event_id, class_id, zeitnahme_headers)
    assert r.status_code == 204
    cls = _get_class(client, event_id, class_id)
    assert cls["run_status"] == "preliminary"  # unchanged


def test_auto_close_unknown_class_returns_204(client, event_id, zeitnahme_headers):
    r = client.post(f"/api/events/{event_id}/classes/9999/auto-close",
                    headers=zeitnahme_headers)
    assert r.status_code == 204  # silent no-op


# ── GET /admin/system-log ─────────────────────────────────────────────────────

def test_system_log_empty(client, admin_headers):
    r = client.get("/api/admin/system-log", headers=admin_headers)
    assert r.status_code == 200
    assert r.json() == []


def test_system_log_admin_only(client, zeitnahme_headers, viewer_headers,
                               schiri_headers, nennung_headers):
    for headers in (zeitnahme_headers, viewer_headers, schiri_headers, nennung_headers):
        r = client.get("/api/admin/system-log", headers=headers)
        assert r.status_code == 403


def test_system_log_forbidden_without_token(client):
    r = client.get("/api/admin/system-log")
    assert r.status_code in (401, 403)


def test_system_log_returns_entries(client, db, admin_headers):
    db.execute(
        "INSERT INTO SystemLog (level, event_type, username, detail) VALUES (?,?,?,?)",
        ("info", "server_start", None, "v0.5.0"),
    )
    db.execute(
        "INSERT INTO SystemLog (level, event_type, username) VALUES (?,?,?)",
        ("warn", "login_fail", "baduser"),
    )
    db.commit()

    r = client.get("/api/admin/system-log", headers=admin_headers)
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 2
    event_types = {row["event_type"] for row in rows}
    assert event_types == {"server_start", "login_fail"}


def test_system_log_filter_by_level(client, db, admin_headers):
    db.execute("INSERT INTO SystemLog (level, event_type) VALUES (?,?)", ("info", "server_start"))
    db.execute("INSERT INTO SystemLog (level, event_type) VALUES (?,?)", ("warn", "login_fail"))
    db.commit()

    r = client.get("/api/admin/system-log", params={"level": "warn"}, headers=admin_headers)
    rows = r.json()
    assert all(row["level"] == "warn" for row in rows)
    assert len(rows) == 1


def test_system_log_filter_by_event_type(client, db, admin_headers):
    db.execute("INSERT INTO SystemLog (level, event_type, username) VALUES (?,?,?)",
               ("info", "login_ok", "alice"))
    db.execute("INSERT INTO SystemLog (level, event_type, username) VALUES (?,?,?)",
               ("info", "login_ok", "bob"))
    db.execute("INSERT INTO SystemLog (level, event_type) VALUES (?,?)",
               ("info", "server_start"))
    db.commit()

    r = client.get("/api/admin/system-log",
                   params={"event_type": "login_ok"}, headers=admin_headers)
    rows = r.json()
    assert len(rows) == 2
    assert all(row["event_type"] == "login_ok" for row in rows)


def test_system_log_newest_first(client, db, admin_headers):
    for i in range(3):
        db.execute("INSERT INTO SystemLog (level, event_type, detail) VALUES (?,?,?)",
                   ("info", "login_ok", str(i)))
    db.commit()

    rows = client.get("/api/admin/system-log", headers=admin_headers).json()
    assert len(rows) == 3
    assert rows[0]["ts"] >= rows[1]["ts"] >= rows[2]["ts"]


def test_system_log_limit(client, db, admin_headers):
    for i in range(10):
        db.execute("INSERT INTO SystemLog (level, event_type) VALUES (?,?)",
                   ("info", "login_ok"))
    db.commit()

    r = client.get("/api/admin/system-log", params={"limit": 3}, headers=admin_headers)
    assert len(r.json()) == 3
