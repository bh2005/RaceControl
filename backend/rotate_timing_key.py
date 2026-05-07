#!/usr/bin/env python3
"""Generate a new timing API key and persist it in the database.

The key protects the /ws/timing WebSocket endpoint from unauthorized
timing injections.  Rotate it whenever a Raspberry Pi or timing client
is decommissioned or lost.

After rotating, the new key must be copied into any client scripts that
embed it (racecontrol_client.py, alge_timy_client.py, etc.).  Pass
--patch-clients to update those files automatically.

Usage:
    python backend/rotate_timing_key.py
    python backend/rotate_timing_key.py --patch-clients
    python backend/rotate_timing_key.py --show        # only print current key
    python backend/rotate_timing_key.py --db /custom/path/racecontrol.db

Exit codes:
    0  Success
    1  DB not found or key not found
    2  sqlite3 error

Environment:
    DATA_DIR  Optional path to the RaceControl data directory.
"""
from __future__ import annotations

import argparse
import datetime
import os
import pathlib
import re
import secrets
import sqlite3
import sys

ROOT     = pathlib.Path(__file__).resolve().parent
DATA_DIR = pathlib.Path(os.environ.get("DATA_DIR", str(ROOT.parent)))
DB_PATH  = DATA_DIR / "racecontrol.db"

# Client scripts that embed TIMING_API_KEY as a Python string literal
_CLIENT_SCRIPTS: list[pathlib.Path] = [
    ROOT.parent / "RaPi_lichtschranke" / "racecontrol_client.py",
    ROOT.parent / "RaPi_lichtschranke" / "racecontrol_client_max7219.py",
    ROOT.parent / "RaPi_lichtschranke" / "racecontrol_downhill_finish.py",
    ROOT.parent / "tools"              / "lsu200_client.py",
    ROOT.parent / "tools"              / "lsu200_linux_client.py",
    ROOT.parent / "tools"              / "alge_timy_client.py",
    ROOT.parent / "tools"              / "alge_multi_timy_client.py",
]

# Matches lines like:  TIMING_API_KEY = ""   or  TIMING_API_KEY = "abc123..."
_KEY_RE = re.compile(r'^(TIMING_API_KEY\s*=\s*)"[^"]*"', re.MULTILINE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rotate the RaceControl timing API key."
    )
    parser.add_argument("--db",           help="Path to racecontrol.db.")
    parser.add_argument("--show",         action="store_true",
                        help="Print current key and exit without rotating.")
    parser.add_argument("--patch-clients", action="store_true",
                        help="Also update TIMING_API_KEY in client scripts.")
    return parser.parse_args()


def log(msg: str, *, error: bool = False) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr if error else sys.stdout)


def get_current_key(conn: sqlite3.Connection) -> str | None:
    row = conn.execute(
        "SELECT value FROM Settings WHERE key = 'timing_api_key'"
    ).fetchone()
    return row[0] if row else None


def patch_client_scripts(new_key: str) -> None:
    patched = 0
    for script in _CLIENT_SCRIPTS:
        if not script.exists():
            log(f"  Übersprungen (nicht gefunden): {script.name}")
            continue
        original = script.read_text(encoding="utf-8")
        updated, count = _KEY_RE.subn(rf'\1"{new_key}"', original)
        if count:
            script.write_text(updated, encoding="utf-8")
            log(f"  Aktualisiert: {script.relative_to(ROOT.parent)}")
            patched += 1
        else:
            log(f"  Kein TIMING_API_KEY gefunden: {script.name}")
    if patched:
        log(f"{patched} Client-Script(s) aktualisiert. Bitte auf die Geräte übertragen.")


def main() -> int:
    args    = parse_args()
    db_path = pathlib.Path(args.db).expanduser().resolve() if args.db else DB_PATH

    if not db_path.exists():
        log(f"Fehler: Datenbankdatei nicht gefunden: {db_path}", error=True)
        return 1

    try:
        conn = sqlite3.connect(str(db_path))

        current_key = get_current_key(conn)

        if args.show:
            if current_key:
                log(f"Aktueller Timing-API-Key: {current_key}")
            else:
                log("Kein Timing-API-Key in der Datenbank gefunden.", error=True)
                conn.close()
                return 1
            conn.close()
            return 0

        if current_key:
            log(f"Aktueller Key: {current_key[:8]}… (wird ersetzt)")
        else:
            log("Kein Key vorhanden — wird neu angelegt.")

        new_key = secrets.token_hex(24)  # 48-Zeichen Hex-String, 192 bit Entropie
        conn.execute(
            "INSERT OR REPLACE INTO Settings (key, value) VALUES ('timing_api_key', ?)",
            (new_key,),
        )
        conn.commit()
        conn.close()

        log(f"Neuer Timing-API-Key: {new_key}")
        log("Starte den RaceControl-Server neu, damit der neue Key aktiv wird.")

        if args.patch_clients:
            log("Patche Client-Skripte …")
            patch_client_scripts(new_key)
        else:
            log("Hinweis: Client-Skripte wurden nicht aktualisiert. "
                "Führe --patch-clients aus oder trage den Key manuell ein.")

        return 0

    except sqlite3.Error as exc:
        log(f"SQLite-Fehler: {exc}", error=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
