#!/usr/bin/env python3
"""Delete old entries from the SystemLog table.

Rows older than --days N are removed.  AuditLog is intentionally excluded
(legal requirement: audit trail must never be deleted by automated scripts).

Usage:
    python backend/trim_logs.py                  # delete SystemLog rows > 90 days
    python backend/trim_logs.py --days 30
    python backend/trim_logs.py --dry-run        # show count, don't delete
    python backend/trim_logs.py --vacuum         # run VACUUM after deletion

Exit codes:
    0  Success (or nothing to do)
    1  DB not found
    2  sqlite3 error

Environment:
    DATA_DIR  Optional path to the RaceControl data directory.
"""
from __future__ import annotations

import argparse
import datetime
import os
import pathlib
import sqlite3
import sys

ROOT     = pathlib.Path(__file__).resolve().parent
DATA_DIR = pathlib.Path(os.environ.get("DATA_DIR", str(ROOT.parent)))
DB_PATH  = DATA_DIR / "racecontrol.db"

DEFAULT_DAYS = 90


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete old SystemLog entries from racecontrol.db."
    )
    parser.add_argument("--db",      help="Path to racecontrol.db.")
    parser.add_argument(
        "--days", type=int, default=DEFAULT_DAYS,
        help=f"Delete rows older than N days (default: {DEFAULT_DAYS}).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print how many rows would be deleted without actually deleting.",
    )
    parser.add_argument(
        "--vacuum", action="store_true",
        help="Run VACUUM after deletion to reclaim space.",
    )
    return parser.parse_args()


def log(msg: str, *, error: bool = False) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr if error else sys.stdout)


def main() -> int:
    args    = parse_args()
    db_path = pathlib.Path(args.db).expanduser().resolve() if args.db else DB_PATH

    if not db_path.exists():
        log(f"Fehler: Datenbankdatei nicht gefunden: {db_path}", error=True)
        return 1

    if args.days <= 0:
        log("Fehler: --days muss eine positive Zahl sein.", error=True)
        return 1

    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=args.days)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    log(f"Trennzeitpunkt: {cutoff} (Einträge älter als {args.days} Tage)")

    try:
        conn = sqlite3.connect(str(db_path))

        count_row = conn.execute(
            "SELECT COUNT(*) FROM SystemLog WHERE ts < ?", (cutoff,)
        ).fetchone()
        count = count_row[0] if count_row else 0

        if args.dry_run:
            log(f"Dry-run: {count} SystemLog-Einträge würden gelöscht.")
            conn.close()
            return 0

        if count == 0:
            log("Keine Einträge zum Löschen gefunden.")
            conn.close()
            return 0

        conn.execute("DELETE FROM SystemLog WHERE ts < ?", (cutoff,))
        conn.commit()
        log(f"{count} SystemLog-Einträge gelöscht.")

        if args.vacuum:
            log("Führe VACUUM aus …")
            conn.execute("VACUUM")
            log("VACUUM abgeschlossen.")

        conn.close()

    except sqlite3.Error as exc:
        log(f"SQLite-Fehler: {exc}", error=True)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
