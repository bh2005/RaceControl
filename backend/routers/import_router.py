"""CSV-Importer für ADAC-Portal-Nennlisten."""
from __future__ import annotations
import csv
import io
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
import sqlite3

from database import get_db
from deps import require_roles

router = APIRouter(prefix="/events/{event_id}", tags=["import"])

AdminOrNennung = Annotated[sqlite3.Row, Depends(require_roles("admin", "nennung"))]

# Spaltennamen-Aliases (lowercase) → internes Feld
_ALIASES: dict[str, str] = {
    "vorname": "first_name",
    "first name": "first_name",
    "firstname": "first_name",
    "first_name": "first_name",
    "nachname": "last_name",
    "last name": "last_name",
    "lastname": "last_name",
    "last_name": "last_name",
    "geburtsjahr": "birth_year",
    "jahrgang": "birth_year",
    "jg": "birth_year",
    "jg.": "birth_year",
    "birth year": "birth_year",
    "birthyear": "birth_year",
    "birth_year": "birth_year",
    "verein": "club",
    "vereinsname": "club",
    "club": "club",
    "lizenznummer": "license_number",
    "lizenz": "license_number",
    "lizenznr": "license_number",
    "lizenznr.": "license_number",
    "license": "license_number",
    "license number": "license_number",
    "license_number": "license_number",
    "klasse": "class_name",
    "startklasse": "class_name",
    "class": "class_name",
    "startnummer": "start_number",
    "startnr": "start_number",
    "startnr.": "start_number",
    "nr": "start_number",
    "nr.": "start_number",
    "start number": "start_number",
    "start_number": "start_number",
}


@router.post("/import-participants")
async def import_participants(
    event_id: int,
    file: UploadFile = File(...),
    db: Annotated[sqlite3.Connection, Depends(get_db)] = ...,
    _: AdminOrNennung = None,
):
    """
    Importiert Teilnehmer aus einer CSV-Datei (ADAC-Portal-Format oder generisch).
    Unterstützte Spalten: Vorname, Nachname, Geburtsjahr/Jahrgang, Verein,
    Lizenznummer, Klasse/Startklasse, Startnummer.
    Trennzeichen: Semikolon oder Komma (auto-detect).
    Encoding: UTF-8 (mit/ohne BOM) oder Latin-1.
    Duplikate (gleiche Lizenznummer im selben Event) werden übersprungen.
    """
    raw = await file.read()
    text: Optional[str] = None
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise HTTPException(400, "Datei-Encoding nicht erkannt (UTF-8 oder Latin-1 erwartet)")

    # Trennzeichen auto-detect
    first_line = text.split("\n")[0]
    delimiter = ";" if first_line.count(";") >= first_line.count(",") else ","

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        raise HTTPException(400, "CSV leer oder keine Kopfzeile gefunden")

    # Spaltennamen mappen
    col_map: dict[str, str] = {}
    for h in reader.fieldnames:
        canonical = _ALIASES.get(h.strip().lower())
        if canonical and canonical not in col_map.values():
            col_map[h] = canonical

    canonical_set = set(col_map.values())
    if "first_name" not in canonical_set or "last_name" not in canonical_set:
        raise HTTPException(
            400,
            f"Pflicht-Spalten nicht gefunden. Erkannte Felder: {list(canonical_set) or 'keine'}. "
            "Mindestens Vorname + Nachname erforderlich."
        )

    # Klassen und Vereine für dieses Event vorladen
    classes: dict[str, int] = {
        r["name"].strip().lower(): r["id"]
        for r in db.execute("SELECT id, name FROM Classes WHERE event_id = ?", (event_id,)).fetchall()
    }
    clubs: dict[str, int] = {
        r["name"].strip().lower(): r["id"]
        for r in db.execute("SELECT id, name FROM Clubs").fetchall()
    }

    imported = skipped = 0
    errors: list[str] = []

    for line_no, row in enumerate(reader, start=2):
        mapped: dict[str, str] = {}
        for header, field in col_map.items():
            val = (row.get(header) or "").strip()
            if val:
                mapped[field] = val

        if not mapped.get("first_name") or not mapped.get("last_name"):
            skipped += 1
            continue

        # Duplikat-Check per Lizenznummer
        if mapped.get("license_number"):
            exists = db.execute(
                "SELECT 1 FROM Participants WHERE event_id = ? AND license_number = ?",
                (event_id, mapped["license_number"]),
            ).fetchone()
            if exists:
                skipped += 1
                continue

        # Klasse auflösen
        class_id: Optional[int] = None
        if "class_name" in mapped:
            class_id = classes.get(mapped["class_name"].lower())

        # Verein auflösen / anlegen
        club_id: Optional[int] = None
        if "club" in mapped:
            key = mapped["club"].lower()
            if key in clubs:
                club_id = clubs[key]
            else:
                cur = db.execute("INSERT OR IGNORE INTO Clubs (name) VALUES (?)", (mapped["club"],))
                db.commit()
                cid = cur.lastrowid or (
                    db.execute("SELECT id FROM Clubs WHERE name = ?", (mapped["club"],)).fetchone() or {}
                ).get("id")
                if cid:
                    club_id = cid
                    clubs[key] = cid

        birth_year: Optional[int] = None
        if "birth_year" in mapped:
            try:
                birth_year = int(mapped["birth_year"])
            except ValueError:
                pass

        start_number: Optional[int] = None
        if "start_number" in mapped:
            try:
                start_number = int(mapped["start_number"])
            except ValueError:
                pass

        try:
            db.execute(
                """INSERT INTO Participants
                   (event_id, class_id, club_id, start_number, first_name, last_name,
                    birth_year, license_number, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'registered')""",
                (
                    event_id, class_id, club_id, start_number,
                    mapped["first_name"], mapped["last_name"],
                    birth_year, mapped.get("license_number"),
                ),
            )
            db.commit()
            imported += 1
        except Exception as exc:
            errors.append(f"Zeile {line_no}: {exc}")

    return {"imported": imported, "skipped": skipped, "errors": errors}
