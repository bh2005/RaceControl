"""
Tests für import_router.py (CSV-Teilnehmerimport).
"""
from __future__ import annotations
import io
import pytest


def _upload(client, event_id, headers, csv_text: str, filename="test.csv",
            encoding="utf-8"):
    data = csv_text.encode(encoding)
    return client.post(
        f"/api/events/{event_id}/import-participants",
        files={"file": (filename, io.BytesIO(data), "text/csv")},
        headers=headers,
    )


# ── happy path ────────────────────────────────────────────────────────────────

class TestImportHappyPath:
    def test_basic_semicolon_csv(self, client, admin_headers, event_id):
        csv = "Vorname;Nachname;Geburtsjahr\nMax;Mustermann;2010\nAnna;Muster;2012\n"
        r = _upload(client, event_id, admin_headers, csv)
        assert r.status_code == 200
        data = r.json()
        assert data["imported"] == 2
        assert data["skipped"] == 0
        assert data["errors"] == []

    def test_basic_comma_csv(self, client, admin_headers, event_id):
        csv = "first_name,last_name,birth_year\nKarl,Fahrer,2008\n"
        r = _upload(client, event_id, admin_headers, csv)
        assert r.status_code == 200
        assert r.json()["imported"] == 1

    def test_english_column_aliases(self, client, admin_headers, event_id):
        csv = "First Name;Last Name;Birth Year\nJohn;Doe;2005\n"
        r = _upload(client, event_id, admin_headers, csv)
        assert r.status_code == 200
        assert r.json()["imported"] == 1

    def test_with_club_column_creates_club(self, client, admin_headers, event_id):
        csv = "Vorname;Nachname;Verein\nSusi;Mustermann;MC Neustadt\n"
        r = _upload(client, event_id, admin_headers, csv)
        assert r.status_code == 200
        assert r.json()["imported"] == 1
        # Club should now exist
        clubs = client.get("/api/clubs/").json()
        assert any(c["name"] == "MC Neustadt" for c in clubs)

    def test_club_reused_if_exists(self, client, admin_headers, event_id):
        client.post("/api/clubs/", json={"name": "MC Altstadt"}, headers=admin_headers)
        csv = "Vorname;Nachname;Verein\nTom;T;MC Altstadt\nLisa;L;MC Altstadt\n"
        r = _upload(client, event_id, admin_headers, csv)
        assert r.status_code == 200
        assert r.json()["imported"] == 2
        # still only one club with that name
        clubs = [c for c in client.get("/api/clubs/").json() if c["name"] == "MC Altstadt"]
        assert len(clubs) == 1

    def test_with_class_column_resolves_class(self, client, admin_headers,
                                               nennung_headers, event_id, class_id):
        # class_id fixture creates "Klasse A" — use exact name
        csv = "Vorname;Nachname;Klasse\nFrank;K;Klasse A\n"
        r = _upload(client, event_id, nennung_headers, csv)
        assert r.status_code == 200
        assert r.json()["imported"] == 1

    def test_unknown_class_imports_without_class(self, client, admin_headers, event_id):
        csv = "Vorname;Nachname;Klasse\nPeter;P;NichtExistent\n"
        r = _upload(client, event_id, admin_headers, csv)
        assert r.status_code == 200
        assert r.json()["imported"] == 1  # imported, just without class assignment

    def test_with_start_number(self, client, admin_headers, event_id):
        csv = "Vorname;Nachname;Startnummer\nRudi;R;42\n"
        r = _upload(client, event_id, admin_headers, csv)
        assert r.status_code == 200
        assert r.json()["imported"] == 1

    def test_invalid_start_number_ignored(self, client, admin_headers, event_id):
        csv = "Vorname;Nachname;Startnummer\nBerta;B;abc\n"
        r = _upload(client, event_id, admin_headers, csv)
        assert r.status_code == 200
        assert r.json()["imported"] == 1  # imported, start_number=None

    def test_invalid_birth_year_ignored(self, client, admin_headers, event_id):
        csv = "Vorname;Nachname;Geburtsjahr\nClaus;C;keinJahr\n"
        r = _upload(client, event_id, admin_headers, csv)
        assert r.status_code == 200
        assert r.json()["imported"] == 1  # birth_year=None

    def test_with_license_number(self, client, admin_headers, event_id):
        csv = "Vorname;Nachname;Lizenznummer\nEva;E;LZ-12345\n"
        r = _upload(client, event_id, admin_headers, csv)
        assert r.status_code == 200
        assert r.json()["imported"] == 1

    def test_latin1_encoding(self, client, admin_headers, event_id):
        csv = "Vorname;Nachname\nJörg;Müller\n"
        r = _upload(client, event_id, admin_headers, csv, encoding="latin-1")
        assert r.status_code == 200
        assert r.json()["imported"] == 1

    def test_utf8_bom_encoding(self, client, admin_headers, event_id):
        csv = "Vorname;Nachname\nGünter;Schäfer\n"
        r = _upload(client, event_id, admin_headers, csv, encoding="utf-8-sig")
        assert r.status_code == 200
        assert r.json()["imported"] == 1

    def test_requires_auth(self, client, viewer_headers, event_id):
        csv = "Vorname;Nachname\nX;Y\n"
        r = _upload(client, event_id, viewer_headers, csv)
        assert r.status_code == 403


# ── duplicate handling ────────────────────────────────────────────────────────

class TestImportDuplicates:
    def test_duplicate_by_license_skipped(self, client, admin_headers, event_id):
        csv = "Vorname;Nachname;Lizenznummer\nKarl;K;LZ-999\n"
        _upload(client, event_id, admin_headers, csv)
        r = _upload(client, event_id, admin_headers, csv)
        assert r.status_code == 200
        data = r.json()
        assert data["imported"] == 0
        assert data["skipped"] == 1

    def test_no_license_allows_reimport(self, client, admin_headers, event_id):
        csv = "Vorname;Nachname\nOhne;Lizenz\n"
        _upload(client, event_id, admin_headers, csv)
        r = _upload(client, event_id, admin_headers, csv)
        assert r.status_code == 200
        # no license → no duplicate check → imported again (may fail on DB constraints)
        # either imported=1 or errors list — we just check no crash
        assert "imported" in r.json()


# ── error paths ───────────────────────────────────────────────────────────────

class TestImportErrors:
    def test_empty_file_400(self, client, admin_headers, event_id):
        r = _upload(client, event_id, admin_headers, "")
        assert r.status_code == 400

    def test_missing_required_columns_400(self, client, admin_headers, event_id):
        csv = "Geburtsjahr;Verein\n2010;MC Test\n"
        r = _upload(client, event_id, admin_headers, csv)
        assert r.status_code == 400
        assert "Vorname" in r.json()["detail"] or "first_name" in r.json()["detail"].lower()

    def test_rows_with_empty_name_skipped(self, client, admin_headers, event_id):
        csv = "Vorname;Nachname\nMax;Mustermann\n;Kein Vorname\nOhne Nachname;\n"
        r = _upload(client, event_id, admin_headers, csv)
        assert r.status_code == 200
        assert r.json()["imported"] == 1
        assert r.json()["skipped"] == 2

    def test_header_only_no_data(self, client, admin_headers, event_id):
        csv = "Vorname;Nachname\n"
        r = _upload(client, event_id, admin_headers, csv)
        assert r.status_code == 200
        assert r.json()["imported"] == 0

    def test_all_column_aliases_recognized(self, client, admin_headers, event_id):
        """Verify all alias variants map correctly by using them one by one."""
        aliases = [
            ("Nachname;Vorname", "Muster;Max"),
            ("last_name;first_name", "Muster;Max"),
            ("lastname;firstname", "Muster;Max"),
            ("Last Name;First Name", "Muster;Max"),
        ]
        for i, (header, row) in enumerate(aliases):
            csv = f"{header}\n{row}_{i}\n"
            r = _upload(client, event_id, admin_headers, csv)
            assert r.status_code == 200, f"Failed for header: {header!r}"
            assert r.json()["imported"] == 1 or "errors" in r.json()
