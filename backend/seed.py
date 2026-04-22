"""
Seed: ADAC Hessen-Thüringen Jugendkart-Reglement 2026
Quellen: ADAC-HTH-Jugendkart-Reglement-2026.pdf

Ausführen:  python seed.py
"""
import json
import sqlite3
import pathlib
import sys

from auth import hash_password

DB_PATH = pathlib.Path(__file__).parent.parent / "racecontrol.db"


# ─────────────────────────────────────────────────────────────────────────────
# Punktetabelle Kartslalom (Kl.0–6) – ADAC HTH 2026
# Platz 1–35: feste Werte; ab Platz 36: je 1 Punkt (mind. 1)
# ─────────────────────────────────────────────────────────────────────────────
KS_POINTS = [40, 37, 35, 33, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21,
             20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]


def ks_points_formula(max_starters: int = 80) -> str:
    table = {}
    for rank, pts in enumerate(KS_POINTS, start=1):
        table[str(rank)] = pts
    for rank in range(len(KS_POINTS) + 1, max_starters + 1):
        table[str(rank)] = 1
    return json.dumps(table)


# ─────────────────────────────────────────────────────────────────────────────
# Reglements
# ─────────────────────────────────────────────────────────────────────────────
REGLEMENTS = [
    {
        "name": "Kartslalom (KS) HTH 2026",
        "scoring_type": "sum_all",        # Summe aller Wertungsläufe
        "points_formula": ks_points_formula(),
        "runs_per_class": 2,
        "has_training": 1,
        "penalties": [
            # Achter / Halbachter
            {"label": "Achter – Begrenzungspunkt",       "seconds": 3.0,  "shortcut_key": "1", "sort_order": 10},
            {"label": "Achter – Pylone",                  "seconds": 3.0,  "shortcut_key": None, "sort_order": 11},
            # Knoten
            {"label": "Knoten – Pylone",                  "seconds": 3.0,  "shortcut_key": "2", "sort_order": 20},
            # Slalom
            {"label": "Slalom – Pylone",                  "seconds": 3.0,  "shortcut_key": "3", "sort_order": 30},
            {"label": "Slalom – Pylonentor",              "seconds": 10.0, "shortcut_key": "4", "sort_order": 31},
            # Käfer
            {"label": "Käfer – Pylone",                   "seconds": 3.0,  "shortcut_key": "5", "sort_order": 40},
            {"label": "Käfer – Käferaufgabe verfehlt",    "seconds": 20.0, "shortcut_key": None, "sort_order": 41},
            # Schlange
            {"label": "Schlange – Pylone",                "seconds": 3.0,  "shortcut_key": "6", "sort_order": 50},
            {"label": "Schlange – Teilaufgabe nicht erf.","seconds": 10.0, "shortcut_key": None, "sort_order": 51},
            # Spurgasse
            {"label": "Spurgasse – Pylone",               "seconds": 3.0,  "shortcut_key": "7", "sort_order": 60},
            # Halteraum
            {"label": "Halteraum – Pylone",               "seconds": 3.0,  "shortcut_key": "8", "sort_order": 70},
            {"label": "Halteraum – nicht angehalten",     "seconds": 10.0, "shortcut_key": None, "sort_order": 71},
            # Pflichttor / Fahrtrichtung
            {"label": "Pflichttor – Pylone",              "seconds": 3.0,  "shortcut_key": "9", "sort_order": 80},
            {"label": "Pflichttor – nicht durchfahren",   "seconds": 10.0, "shortcut_key": None, "sort_order": 81},
            {"label": "Falsches Anfahren",                "seconds": 10.0, "shortcut_key": "0", "sort_order": 90},
            {"label": "Unkorrektes Verhalten",            "seconds": 20.0, "shortcut_key": "U", "sort_order": 99},
        ],
        "classes": [
            {"name": "Klasse 0",  "short_name": "K0",  "min_birth_year": 2020, "max_birth_year": 2020, "start_order": 0},
            {"name": "Klasse 1",  "short_name": "K1",  "min_birth_year": 2017, "max_birth_year": 2019, "start_order": 1},
            {"name": "Klasse 2",  "short_name": "K2",  "min_birth_year": 2015, "max_birth_year": 2016, "start_order": 2},
            {"name": "Klasse 3",  "short_name": "K3",  "min_birth_year": 2013, "max_birth_year": 2014, "start_order": 3},
            {"name": "Klasse 4",  "short_name": "K4",  "min_birth_year": 2011, "max_birth_year": 2012, "start_order": 4},
            {"name": "Klasse 5",  "short_name": "K5",  "min_birth_year": 2008, "max_birth_year": 2010, "start_order": 5},
            {"name": "Klasse 6",  "short_name": "K6",  "min_birth_year": 2001, "max_birth_year": 2007, "start_order": 6},
        ],
    },
    {
        "name": "Kartslalom Tretcar (KT) HTH 2026",
        "scoring_type": "sum_all",
        "points_formula": ks_points_formula(),
        "runs_per_class": 2,
        "has_training": 1,
        "penalties": [
            {"label": "Achter/Halbachter – halbe Aufgabe", "seconds": 20.0, "shortcut_key": "1", "sort_order": 10},
            {"label": "Achter – Begrenzungspunkt",          "seconds": 3.0,  "shortcut_key": "2", "sort_order": 11},
            {"label": "Knoten – halbe Aufgabe",             "seconds": 20.0, "shortcut_key": "3", "sort_order": 20},
            {"label": "Knoten – Pylone",                    "seconds": 3.0,  "shortcut_key": "4", "sort_order": 21},
            {"label": "Slalom – Pylone",                    "seconds": 3.0,  "shortcut_key": "5", "sort_order": 30},
            {"label": "Slalom – Pylonentor",                "seconds": 10.0, "shortcut_key": "6", "sort_order": 31},
            {"label": "Käfer – Pylone",                     "seconds": 3.0,  "shortcut_key": "7", "sort_order": 40},
            {"label": "Käfer – Aufgabe verfehlt",           "seconds": 20.0, "shortcut_key": None, "sort_order": 41},
            {"label": "Schlange – Teilaufgabe nicht erf.",  "seconds": 10.0, "shortcut_key": "8", "sort_order": 50},
            {"label": "Schlange – Pylone",                  "seconds": 3.0,  "shortcut_key": "9", "sort_order": 51},
            {"label": "Spurgasse – Pylone",                 "seconds": 3.0,  "shortcut_key": "0", "sort_order": 60},
            {"label": "Halteraum – nicht angehalten",       "seconds": 10.0, "shortcut_key": None, "sort_order": 70},
            {"label": "Halteraum – Pylone",                 "seconds": 3.0,  "shortcut_key": None, "sort_order": 71},
            {"label": "Pflichttor – nicht durchfahren",     "seconds": 10.0, "shortcut_key": None, "sort_order": 80},
            {"label": "Pflichttor – Pylone",                "seconds": 3.0,  "shortcut_key": None, "sort_order": 81},
            {"label": "Falsches Anfahren",                  "seconds": 10.0, "shortcut_key": "F", "sort_order": 90},
            {"label": "Unkorrektes Verhalten",              "seconds": 20.0, "shortcut_key": "U", "sort_order": 99},
        ],
        "classes": [
            {"name": "KT Klasse 1",  "short_name": "KT1",  "min_birth_year": 2016, "max_birth_year": 2019, "start_order": 0},
            {"name": "KT Klasse 2a", "short_name": "KT2a", "min_birth_year": 2011, "max_birth_year": 2015, "start_order": 1},
            {"name": "KT Klasse 3",  "short_name": "KT3",  "min_birth_year": 2008, "max_birth_year": 2010, "start_order": 2},
            {"name": "KT Klasse 4",  "short_name": "KT4",  "min_birth_year": 2001, "max_birth_year": 2007, "start_order": 3},
        ],
    },
    {
        "name": "KS2000 HTH 2026",
        "scoring_type": "sum_all",
        "points_formula": ks_points_formula(),
        "runs_per_class": 2,
        "has_training": 1,
        "penalties": [
            {"label": "Pylone",                            "seconds": 3.0,  "shortcut_key": "P", "sort_order": 10},
            {"label": "Pylonentor",                        "seconds": 10.0, "shortcut_key": "T", "sort_order": 20},
            {"label": "Schweizer Kreuz – verfehlt",        "seconds": 10.0, "shortcut_key": "S", "sort_order": 30},
            {"label": "Gasse – Pylone",                    "seconds": 3.0,  "shortcut_key": "G", "sort_order": 40},
            {"label": "Gasse – nicht korrekt durchf.",     "seconds": 15.0, "shortcut_key": None, "sort_order": 41},
            {"label": "Haltelinie – nicht angehalten",     "seconds": 3.0,  "shortcut_key": "H", "sort_order": 50},
            {"label": "Falsches Anfahren / Fahrtrichtung", "seconds": 10.0, "shortcut_key": "F", "sort_order": 60},
            {"label": "Unkorrektes Verhalten",             "seconds": 20.0, "shortcut_key": "U", "sort_order": 99},
        ],
        "classes": [
            {"name": "KS2000 Kl. 1",  "short_name": "KS1",  "min_birth_year": 2016, "max_birth_year": 2019, "start_order": 0},
            {"name": "KS2000 Kl. 2b", "short_name": "KS2b", "min_birth_year": 2011, "max_birth_year": 2014, "start_order": 1},
            {"name": "KS2000 Kl. 3",  "short_name": "KS3",  "min_birth_year": 2008, "max_birth_year": 2010, "start_order": 2},
            {"name": "KS2000 Kl. 4",  "short_name": "KS4",  "min_birth_year": 2001, "max_birth_year": 2007, "start_order": 3},
        ],
    },
]


def run_seed():
    if not DB_PATH.exists():
        print(f"Datenbank nicht gefunden: {DB_PATH}")
        print("Bitte zuerst 'python main.py' einmal starten um die DB zu initialisieren.")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys=ON")

    # Admin-Passwort setzen (nur wenn noch Placeholder)
    admin = conn.execute("SELECT * FROM Users WHERE username='admin'").fetchone()
    if admin and admin[2] == "__CHANGE_ON_FIRST_LOGIN__":
        conn.execute(
            "UPDATE Users SET password_hash = ? WHERE username = 'admin'",
            (hash_password("admin"),),
        )
        print("Admin-Passwort auf 'admin' gesetzt — bitte nach dem ersten Login ändern!")

    # Demo-Benutzer anlegen
    demo_users = [
        ("schiri1",     "schiedsrichter", "Schiedsrichter 1"),
        ("zeitnahme1",  "zeitnahme",      "Zeitnahme 1"),
        ("nennung1",    "nennung",        "Nennung 1"),
        ("viewer",      "viewer",         "Livetiming Gast"),
    ]
    for uname, role, display in demo_users:
        conn.execute(
            "INSERT OR IGNORE INTO Users (username, password_hash, role, display_name) VALUES (?,?,?,?)",
            (uname, hash_password(uname), role, display),
        )

    # Reglements + Strafen einfügen
    for reg in REGLEMENTS:
        existing = conn.execute(
            "SELECT id FROM Reglements WHERE name = ?", (reg["name"],)
        ).fetchone()
        if existing:
            reg_id = existing[0]
            print(f"  Reglement '{reg['name']}' bereits vorhanden (id={reg_id})")
        else:
            cur = conn.execute(
                """INSERT INTO Reglements (name, scoring_type, points_formula, runs_per_class, has_training)
                   VALUES (?,?,?,?,?)""",
                (reg["name"], reg["scoring_type"], reg["points_formula"],
                 reg["runs_per_class"], reg["has_training"]),
            )
            reg_id = cur.lastrowid
            print(f"  Reglement '{reg['name']}' angelegt (id={reg_id})")

            for i, pen in enumerate(reg["penalties"]):
                conn.execute(
                    """INSERT INTO PenaltyDefinitions
                       (reglement_id, label, seconds, shortcut_key, sort_order)
                       VALUES (?,?,?,?,?)""",
                    (reg_id, pen["label"], pen["seconds"], pen.get("shortcut_key"), pen["sort_order"]),
                )
            print(f"    → {len(reg['penalties'])} Strafarten eingetragen")

        # Klassen-Definitionen als Referenz auf dem Reglement-Objekt speichern
        # (werden erst bei Event-Erstellung genutzt – hier nur als Doku)
        reg["_id"] = reg_id

    conn.commit()
    conn.close()
    print("\nSeed abgeschlossen.")
    print_summary()


def print_summary():
    conn = sqlite3.connect(str(DB_PATH))
    regs = conn.execute("SELECT id, name FROM Reglements").fetchall()
    print("\n── Reglements in DB ──────────────────────────────────")
    for r in regs:
        pens = conn.execute(
            "SELECT COUNT(*) FROM PenaltyDefinitions WHERE reglement_id=?", (r[0],)
        ).fetchone()[0]
        print(f"  [{r[0]}] {r[1]}  ({pens} Strafarten)")
    users = conn.execute("SELECT username, role FROM Users ORDER BY id").fetchall()
    print("\n── Benutzer in DB ────────────────────────────────────")
    for u in users:
        print(f"  {u[0]:15s}  [{u[1]}]")
    conn.close()
    print("\nHinweis: Demo-Passwörter = Benutzername (bitte für Produktion ändern!)")


if __name__ == "__main__":
    run_seed()
