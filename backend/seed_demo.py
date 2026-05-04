"""
Demo-Daten für RaceControl – alle Timing-Modi

Ausführen:  python seed_demo.py          (Demo-Daten anlegen)
            python seed_demo.py --clean  (Demo-Daten löschen)

Erzeugt:
  1. Club   "[DEMO] MSC Demo e.V."
  2. Slalom  "[DEMO] KS-Slalom 2026-05-10"
             K3 + K4, je 5 Teilnehmer, Training + Lauf 1 (K3 läuft, K4 geplant)
  3. Downhill "[DEMO] Downhill 2026-05-10"
              8 Starter, Startplan 10:00–10:07 (60s-Abstand), 3 Finishes
  4. Training "[DEMO] KS/JKS Training"
              6 Fahrer, Disziplin JKS, je 3–4 Läufe

Alle Demo-Objekte tragen den Prefix [DEMO] und werden mit --clean sauber entfernt.
"""
from __future__ import annotations
import pathlib
import sqlite3
import sys

DB_PATH     = pathlib.Path(__file__).parent.parent / "racecontrol.db"
EVENT_DATE  = "2026-05-10"
DEMO_PREFIX = "[DEMO]"


# ── Slalom-Fahrerlisten ───────────────────────────────────────────────────────
# (Vorname, Nachname, Jahrgang, Geschlecht, Startnr, fee_paid&helmet_ok)
K3_FAHRER = [
    ("Max",    "Müller",    2014, "m", 1, True),
    ("Lena",   "Schmidt",   2013, "w", 2, True),
    ("Tom",    "Weber",     2014, "m", 3, True),
    ("Jana",   "Fischer",   2013, "w", 4, False),   # Abnahme noch offen
    ("Felix",  "Braun",     2014, "m", 5, True),
]
K4_FAHRER = [
    ("Jonas",  "Becker",    2012, "m", 1, True),
    ("Lisa",   "Schneider", 2011, "w", 2, True),
    ("Ben",    "Hoffmann",  2012, "m", 3, False),   # Abnahme noch offen
    ("Sophie", "Koch",      2011, "w", 4, True),
    ("Paul",   "Richter",   2012, "m", 5, True),
]

# Ergebnisse K3: Index 0–4 = Fahrer 1–5 (None = noch nicht gefahren)
K3_TRAINING = [42.50, 44.10, None,  43.80, 41.90]
K3_LAUF1    = [45.20, 46.80, None,  44.90, 43.10]

# ── Downhill-Fahrerliste ──────────────────────────────────────────────────────
# (Vorname, Nachname, Jahrgang, Geschlecht, Startnr)
DOWNHILL_FAHRER = [
    ("Finn",   "Steiner",    2010, "m", 1),
    ("Mia",    "Wolf",       2009, "w", 2),
    ("Luis",   "Neumann",    2010, "m", 3),
    ("Emma",   "Schwarz",    2009, "w", 4),
    ("Noah",   "Zimmermann", 2010, "m", 5),
    ("Laura",  "Krüger",     2009, "w", 6),
    ("Elias",  "Schröder",   2010, "m", 7),
    ("Marie",  "Lange",      2009, "w", 8),
]
DH_FIRST_START_H = 10   # 10:00:00
DH_INTERVAL_S    = 60   # 1 Minute
# (Startposition 1-basiert, Laufzeit in Sekunden)
DH_FINISHES = [
    (1, 125.33),   # Finn  → 2:05,33
    (2, 131.88),   # Mia   → 2:11,88
    (3, 118.50),   # Luis  → 1:58,50
]

# ── Trainings-Fahrerliste ─────────────────────────────────────────────────────
# (Vorname, Nachname, Jahrgang, Geschlecht)
TRAINEES = [
    ("Anton",   "Berger",  2014, "m"),
    ("Clara",   "Sommer",  2013, "w"),
    ("David",   "Winter",  2014, "m"),
    ("Eva",     "Herbst",  2013, "w"),
    ("Florian", "Berg",    2012, "m"),
    ("Greta",   "Wald",    2012, "w"),
]
# Läufe pro Fahrer (None = Lauf noch nicht stattgefunden)
TRAINING_ZEITEN = [
    [48.23, 46.11, 45.87, 44.92],   # Anton   – 4 Läufe
    [52.01, 50.44, 49.78, 50.22],   # Clara   – 4 Läufe
    [55.30, 53.10, 51.44, None],    # David   – 3 Läufe
    [49.88, 48.65, 47.10, 46.55],   # Eva     – 4 Läufe
    [61.20, 58.40, 56.90, 55.10],   # Florian – 4 Läufe
    [57.33, 54.88, None,  None],    # Greta   – 2 Läufe
]


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _exists(conn: sqlite3.Connection, table: str, col: str, val) -> int | None:
    row = conn.execute(f"SELECT id FROM {table} WHERE {col}=?", (val,)).fetchone()
    return row["id"] if row else None


def _ensure_migrations(conn: sqlite3.Connection) -> None:
    """Wendet ausstehende Migrationen an (ruft database._migrate direkt auf)."""
    import sys as _sys
    import pathlib as _pl
    _sys.path.insert(0, str(_pl.Path(__file__).parent))
    from database import _migrate  # type: ignore
    _migrate(conn)
    conn.commit()


# ── Einzelne Seed-Funktionen ──────────────────────────────────────────────────

def seed_club(conn: sqlite3.Connection) -> int:
    name = f"{DEMO_PREFIX} MSC Demo e.V."
    cid = _exists(conn, "Clubs", "name", name)
    if cid:
        print(f"  Club bereits vorhanden (id={cid})")
        return cid
    cur = conn.execute(
        "INSERT INTO Clubs (name, short_name, city) VALUES (?,?,?)",
        (name, "MSC Demo", "Demo-Stadt"),
    )
    cid = cur.lastrowid
    print(f"  Club angelegt: {name} (id={cid})")
    return cid


def seed_slalom_event(conn: sqlite3.Connection, club_id: int) -> None:
    name = f"{DEMO_PREFIX} KS-Slalom {EVENT_DATE}"
    if _exists(conn, "Events", "name", name):
        print(f"  Slalom-Event bereits vorhanden, übersprungen")
        return

    ks_reg = conn.execute(
        "SELECT id FROM Reglements WHERE name LIKE 'Kartslalom (KS)%' LIMIT 1"
    ).fetchone()
    if not ks_reg:
        print("  WARNUNG: KS-Reglement nicht gefunden – bitte zuerst 'python seed.py' ausführen!")
        return
    reg_id = ks_reg["id"]

    ev_id = conn.execute(
        "INSERT INTO Events (name, date, location, status, timing_mode) VALUES (?,?,?,?,?)",
        (name, EVENT_DATE, "Testgelände Demo-Stadt", "active", "slalom"),
    ).lastrowid
    print(f"  Slalom-Event angelegt: {name} (id={ev_id})")

    k3_id = conn.execute(
        """INSERT INTO Classes (event_id, reglement_id, name, short_name,
           min_birth_year, max_birth_year, run_status, start_order)
           VALUES (?,?,?,?,?,?,?,?)""",
        (ev_id, reg_id, "Klasse 3", "K3", 2013, 2014, "running", 0),
    ).lastrowid

    k4_id = conn.execute(
        """INSERT INTO Classes (event_id, reglement_id, name, short_name,
           min_birth_year, max_birth_year, run_status, start_order)
           VALUES (?,?,?,?,?,?,?,?)""",
        (ev_id, reg_id, "Klasse 4", "K4", 2011, 2012, "planned", 1),
    ).lastrowid

    k3_ids = []
    for fn, ln, jg, gen, nr, ok in K3_FAHRER:
        pid = conn.execute(
            """INSERT INTO Participants
               (event_id, class_id, club_id, start_number, first_name, last_name,
                birth_year, gender, status, fee_paid, helmet_ok)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (ev_id, k3_id, club_id, nr, fn, ln, jg, gen,
             "technical_ok" if ok else "checked_in",
             int(ok), int(ok)),
        ).lastrowid
        k3_ids.append(pid)

    k4_ids = []
    for fn, ln, jg, gen, nr, ok in K4_FAHRER:
        pid = conn.execute(
            """INSERT INTO Participants
               (event_id, class_id, club_id, start_number, first_name, last_name,
                birth_year, gender, status, fee_paid, helmet_ok)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (ev_id, k4_id, club_id, nr, fn, ln, jg, gen,
             "technical_ok" if ok else "checked_in",
             int(ok), int(ok)),
        ).lastrowid
        k4_ids.append(pid)

    print(f"    K3: {len(k3_ids)} Teilnehmer (run_status=running), K4: {len(k4_ids)} (run_status=planned)")

    for pid, t in zip(k3_ids, K3_TRAINING):
        if t is None: continue
        conn.execute(
            """INSERT OR IGNORE INTO RaceResults
               (event_id, participant_id, class_id, run_number, raw_time)
               VALUES (?,?,?,?,?)""",
            (ev_id, pid, k3_id, 0, t),
        )
    for pid, t in zip(k3_ids, K3_LAUF1):
        if t is None: continue
        conn.execute(
            """INSERT OR IGNORE INTO RaceResults
               (event_id, participant_id, class_id, run_number, raw_time)
               VALUES (?,?,?,?,?)""",
            (ev_id, pid, k3_id, 1, t),
        )

    entered = sum(1 for t in K3_TRAINING + K3_LAUF1 if t is not None)
    print(f"    K3-Ergebnisse: Training + Lauf 1 ({entered} von {len(k3_ids)*2} eingetragen, 1 Fahrer noch offen)")
    conn.commit()


def seed_downhill_event(conn: sqlite3.Connection, club_id: int) -> None:
    name = f"{DEMO_PREFIX} Downhill {EVENT_DATE}"
    if _exists(conn, "Events", "name", name):
        print(f"  Downhill-Event bereits vorhanden, übersprungen")
        return

    ev_id = conn.execute(
        "INSERT INTO Events (name, date, location, status, timing_mode) VALUES (?,?,?,?,?)",
        (name, EVENT_DATE, "Demo-Downhill-Strecke", "active", "downhill"),
    ).lastrowid
    print(f"  Downhill-Event angelegt: {name} (id={ev_id})")

    # Generische Klasse (RaceResults.class_id NOT NULL)
    cls_id = conn.execute(
        "INSERT INTO Classes (event_id, name, short_name, run_status, start_order) VALUES (?,?,?,?,?)",
        (ev_id, "Downhill Gesamt", "DH", "running", 0),
    ).lastrowid

    part_ids = []
    for fn, ln, jg, gen, nr in DOWNHILL_FAHRER:
        pid = conn.execute(
            """INSERT INTO Participants
               (event_id, class_id, club_id, start_number, first_name, last_name,
                birth_year, gender, status, fee_paid, helmet_ok)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (ev_id, cls_id, club_id, nr, fn, ln, jg, gen, "technical_ok", 1, 1),
        ).lastrowid
        part_ids.append(pid)

    print(f"    {len(part_ids)} Starter, alle startklar")

    # StartSchedule
    base_s = DH_FIRST_START_H * 3600
    for i, pid in enumerate(part_ids):
        total_s = base_s + i * DH_INTERVAL_S
        hh, mm, ss = total_s // 3600, (total_s % 3600) // 60, total_s % 60
        conn.execute(
            "INSERT OR IGNORE INTO StartSchedule (event_id, participant_id, lane, scheduled_start) VALUES (?,?,?,?)",
            (ev_id, pid, None, f"{EVENT_DATE}T{hh:02d}:{mm:02d}:{ss:02d}"),
        )
    last_s = base_s + (len(part_ids) - 1) * DH_INTERVAL_S
    print(f"    Startplan: 10:00:00–{last_s//3600:02d}:{(last_s%3600)//60:02d}:{last_s%60:02d} ({DH_INTERVAL_S}s-Abstand)")

    # Finishes für die ersten DH_FINISHES Starter
    for start_pos, elapsed in DH_FINISHES:
        pid = part_ids[start_pos - 1]
        conn.execute(
            """INSERT OR IGNORE INTO RaceResults
               (event_id, participant_id, class_id, run_number, raw_time)
               VALUES (?,?,?,?,?)""",
            (ev_id, pid, cls_id, 1, elapsed),
        )
    m1, s1 = divmod(DH_FINISHES[0][1], 60)
    m2, s2 = divmod(DH_FINISHES[2][1], 60)
    print(f"    {len(DH_FINISHES)} Finishes: {m1:.0f}:{s1:05.2f} – {m2:.0f}:{s2:05.2f} min")
    conn.commit()


def seed_training(conn: sqlite3.Connection, club_id: int) -> None:
    name = f"{DEMO_PREFIX} KS/JKS Training"
    if _exists(conn, "TrainingSessions", "name", name):
        print(f"  Trainings-Session bereits vorhanden, übersprungen")
        return

    disc = conn.execute("SELECT id FROM Disciplines WHERE name='JKS'").fetchone()
    disc_id = disc["id"] if disc else None

    sess_id = conn.execute(
        "INSERT INTO TrainingSessions (name, date, status, discipline_id) VALUES (?,?,?,?)",
        (name, EVENT_DATE, "active", disc_id),
    ).lastrowid
    print(f"  Training-Session angelegt: {name} (id={sess_id}, Disziplin={'JKS' if disc_id else 'keine'})")

    trainee_ids = []
    for fn, ln, jg, gen in TRAINEES:
        row = conn.execute(
            "SELECT id FROM Trainees WHERE first_name=? AND last_name=?", (fn, ln)
        ).fetchone()
        if row:
            trainee_ids.append(row["id"])
        else:
            tid = conn.execute(
                "INSERT INTO Trainees (first_name, last_name, birth_year, club_id, notes) VALUES (?,?,?,?,?)",
                (fn, ln, jg, club_id, DEMO_PREFIX),
            ).lastrowid
            trainee_ids.append(tid)

    total_runs = 0
    for tid, zeiten in zip(trainee_ids, TRAINING_ZEITEN):
        for run_nr, t in enumerate(zeiten, start=1):
            if t is None: continue
            conn.execute(
                """INSERT OR IGNORE INTO TrainingRuns
                   (session_id, trainee_id, run_number, raw_time, penalty_seconds, status, source)
                   VALUES (?,?,?,?,?,?,?)""",
                (sess_id, tid, run_nr, t, 0.0, "valid", "manual"),
            )
            total_runs += 1

    print(f"    {len(trainee_ids)} Fahrer, {total_runs} Läufe (beste: 44.92 s / schlechteste: 61.20 s)")
    conn.commit()


# ── Clean ─────────────────────────────────────────────────────────────────────

def clean_demo(conn: sqlite3.Connection) -> None:
    print(f"Lösche alle Objekte mit Prefix '{DEMO_PREFIX}' …")

    rows = conn.execute(
        "SELECT id, name FROM Events WHERE name LIKE ?", (f"{DEMO_PREFIX}%",)
    ).fetchall()
    for r in rows:
        conn.execute("DELETE FROM Events WHERE id=?", (r["id"],))
        print(f"  Event gelöscht: {r['name']}")

    rows = conn.execute(
        "SELECT id, name FROM TrainingSessions WHERE name LIKE ?", (f"{DEMO_PREFIX}%",)
    ).fetchall()
    for r in rows:
        conn.execute("DELETE FROM TrainingSessions WHERE id=?", (r["id"],))
        print(f"  TrainingSession gelöscht: {r['name']}")

    n = conn.execute(
        "DELETE FROM Trainees WHERE notes=?", (DEMO_PREFIX,)
    ).rowcount
    if n: print(f"  {n} Trainees gelöscht")

    n = conn.execute(
        "DELETE FROM Clubs WHERE name LIKE ?", (f"{DEMO_PREFIX}%",)
    ).rowcount
    if n: print(f"  {n} Club(s) gelöscht")

    conn.commit()
    print("Fertig.")


# ── Entry Point ───────────────────────────────────────────────────────────────

def run() -> None:
    if not DB_PATH.exists():
        print(f"Datenbank nicht gefunden: {DB_PATH}")
        print("Bitte zuerst 'python main.py' starten (initialisiert DB) und 'python seed.py' ausführen.")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    _ensure_migrations(conn)

    if "--clean" in sys.argv:
        clean_demo(conn)
    else:
        print("--- Demo-Daten anlegen ---")
        club_id = seed_club(conn)
        seed_slalom_event(conn, club_id)
        seed_downhill_event(conn, club_id)
        seed_training(conn, club_id)
        print()
        print("Fertig. Anmelden als admin/admin oder zeitnahme1/zeitnahme1.")
        print("Zum Löschen aller Demo-Daten:  python seed_demo.py --clean")

    conn.close()


if __name__ == "__main__":
    run()
