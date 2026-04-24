from __future__ import annotations


# ── Create ────────────────────────────────────────────────────────────────────

def test_create_participant(client, event_id, class_id, nennung_headers):
    r = client.post(f"/api/events/{event_id}/participants", json={
        "first_name": "Anna", "last_name": "Schmidt",
        "birth_year": 2012, "class_id": class_id, "start_number": 10,
    }, headers=nennung_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["first_name"] == "Anna"
    assert data["event_id"] == event_id
    assert data["start_number"] == 10


def test_create_participant_by_admin(client, event_id, class_id, admin_headers):
    r = client.post(f"/api/events/{event_id}/participants", json={
        "first_name": "Ben", "last_name": "Müller",
        "class_id": class_id, "start_number": 20,
    }, headers=admin_headers)
    assert r.status_code == 201


def test_create_participant_forbidden_without_token(client, event_id, class_id):
    r = client.post(f"/api/events/{event_id}/participants", json={
        "first_name": "Ghost", "last_name": "User", "class_id": class_id,
    })
    assert r.status_code in (401, 403)


def test_create_participant_forbidden_for_zeitnahme(client, event_id, class_id, zeitnahme_headers):
    r = client.post(f"/api/events/{event_id}/participants", json={
        "first_name": "Ghost", "last_name": "User", "class_id": class_id,
    }, headers=zeitnahme_headers)
    assert r.status_code == 403


def test_create_participant_duplicate_start_number(client, event_id, class_id,
                                                   participant_id, nennung_headers):
    r = client.post(f"/api/events/{event_id}/participants", json={
        "first_name": "Doppelt", "last_name": "Startnummer",
        "class_id": class_id, "start_number": 1,  # already taken by fixture
    }, headers=nennung_headers)
    assert r.status_code == 409


# ── List ──────────────────────────────────────────────────────────────────────

def test_list_participants(client, event_id, participant_id):
    r = client.get(f"/api/events/{event_id}/participants")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 1
    assert any(p["id"] == participant_id for p in rows)


def test_list_participants_no_auth_required(client, event_id, participant_id):
    r = client.get(f"/api/events/{event_id}/participants")
    assert r.status_code == 200


# ── Update ────────────────────────────────────────────────────────────────────

def test_update_fee_paid(client, event_id, participant_id, nennung_headers):
    r = client.patch(f"/api/events/{event_id}/participants/{participant_id}",
                     json={"fee_paid": True}, headers=nennung_headers)
    assert r.status_code == 200
    assert r.json()["fee_paid"] is True


def test_update_helmet_ok(client, event_id, participant_id, nennung_headers):
    r = client.patch(f"/api/events/{event_id}/participants/{participant_id}",
                     json={"helmet_ok": True}, headers=nennung_headers)
    assert r.status_code == 200
    assert r.json()["helmet_ok"] is True


def test_update_status_checked_in(client, event_id, participant_id, nennung_headers):
    r = client.patch(f"/api/events/{event_id}/participants/{participant_id}",
                     json={"status": "checked_in"}, headers=nennung_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "checked_in"


def test_update_participant_forbidden_for_zeitnahme(client, event_id,
                                                    participant_id, zeitnahme_headers):
    r = client.patch(f"/api/events/{event_id}/participants/{participant_id}",
                     json={"fee_paid": True}, headers=zeitnahme_headers)
    assert r.status_code == 403


# ── Suggest class ─────────────────────────────────────────────────────────────

def test_suggest_class_by_birth_year(client, event_id, class_id, db):
    db.execute(
        "UPDATE Classes SET min_birth_year = 2008, max_birth_year = 2014 WHERE id = ?",
        (class_id,),
    )
    db.commit()
    r = client.get(f"/api/events/{event_id}/participants/suggest-class/2010")
    assert r.status_code == 200
    assert r.json()["class_id"] == class_id


def test_suggest_class_no_match(client, event_id):
    r = client.get(f"/api/events/{event_id}/participants/suggest-class/1950")
    assert r.status_code == 404
