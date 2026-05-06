#!/usr/bin/env python3
"""Run health checks on the RaceControl SQLite database.

Checks performed:
  1. PRAGMA integrity_check      — structural page-level check
  2. PRAGMA foreign_key_check    — dangling FK references
  3. PRAGMA wal_checkpoint(TRUNCATE) — flush WAL to main file
  4. Optional VACUUM              — reclaim free pages (use sparingly; rewrites entire DB)
  5. File-size report before/after

Safe to run while the server is live.  The WAL checkpoint is a light operation;
VACUUM requires an exclusive lock and briefly blocks the server — omit it during
peak hours.

Usage:
    python backend/db_health.py
    python backend/db_health.py --vacuum
    python backend/db_health.py --db /custom/path/racecontrol.db

Exit codes:
    0  All checks passed
    1  DB not found or a check reported issues
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run health checks on racecontrol.db."
    )
    parser.add_argument("--db",     help="Path to racecontrol.db.")
    parser.add_argument("--vacuum", action="store_true",
                        help="Run VACUUM after checkpoint (exclusive lock; use off-peak).")
    return parser.parse_args()


def log(msg: str, *, error: bool = False) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr if error else sys.stdout)


def fmt_kb(path: pathlib.Path) -> str:
    return f"{path.stat().st_size // 1024} KB"


def main() -> int:
    args    = parse_args()
    db_path = pathlib.Path(args.db).expanduser().resolve() if args.db else DB_PATH

    if not db_path.exists():
        log(f"Fehler: Datenbankdatei nicht gefunden: {db_path}", error=True)
        return 1

    size_before = db_path.stat().st_size
    log(f"Datenbank: {db_path}  ({size_before // 1024} KB)")

    issues = 0
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON")

        # 1. Integrity check
        log("Führe PRAGMA integrity_check aus …")
        rows = conn.execute("PRAGMA integrity_check").fetchall()
        if len(rows) == 1 and rows[0][0] == "ok":
            log("  integrity_check: ok")
        else:
            for row in rows:
                log(f"  integrity_check: {row[0]}", error=True)
            issues += len(rows)

        # 2. Foreign-key check
        log("Führe PRAGMA foreign_key_check aus …")
        fk_rows = conn.execute("PRAGMA foreign_key_check").fetchall()
        if not fk_rows:
            log("  foreign_key_check: ok")
        else:
            for row in fk_rows:
                log(f"  FK-Fehler: Tabelle={row[0]}, rowid={row[1]}, referenziert={row[2]}", error=True)
            issues += len(fk_rows)

        # 3. WAL checkpoint
        log("Führe PRAGMA wal_checkpoint(TRUNCATE) aus …")
        wal_result = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        # wal_result = (busy, log_pages, checkpointed_pages)
        busy, log_pages, ckpt_pages = wal_result
        if busy:
            log(f"  checkpoint: busy (WAL pages={log_pages}, checkpointed={ckpt_pages})", error=True)
            issues += 1
        else:
            log(f"  checkpoint: ok (pages checkpointed={ckpt_pages})")

        # 4. Optional VACUUM
        if args.vacuum:
            log("Führe VACUUM aus (exklusiver Lock) …")
            conn.execute("VACUUM")
            log("  VACUUM: abgeschlossen")

        conn.close()

    except sqlite3.Error as exc:
        log(f"SQLite-Fehler: {exc}", error=True)
        return 2

    size_after = db_path.stat().st_size
    log(f"Größe: vorher={size_before // 1024} KB, nachher={size_after // 1024} KB")

    if issues:
        log(f"Health-Check abgeschlossen: {issues} Problem(e) gefunden.", error=True)
        return 1

    log("Health-Check abgeschlossen: alle Prüfungen bestanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
