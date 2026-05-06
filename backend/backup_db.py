#!/usr/bin/env python3
"""Create a timestamped, WAL-safe backup of the RaceControl SQLite database.

Uses sqlite3's built-in .backup() API — safe to run while the server is live.

Usage:
    python backend/backup_db.py
    python backend/backup_db.py --dest /mnt/usb/backups --keep 20
    python backend/backup_db.py --db /custom/path/racecontrol.db

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

DEFAULT_BACKUP_DIR = DATA_DIR / "backups"
DEFAULT_KEEP       = 10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a timestamped, WAL-safe backup of racecontrol.db."
    )
    parser.add_argument("--db",   help="Path to racecontrol.db.")
    parser.add_argument("--dest", help=f"Backup directory (default: {DEFAULT_BACKUP_DIR}).")
    parser.add_argument(
        "--keep", type=int, default=DEFAULT_KEEP,
        help=f"Number of most-recent backups to keep (default: {DEFAULT_KEEP}, 0 = keep all).",
    )
    return parser.parse_args()


def log(msg: str, *, error: bool = False) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr if error else sys.stdout)


def rotate(backup_dir: pathlib.Path, keep: int) -> None:
    if keep <= 0:
        return
    backups = sorted(backup_dir.glob("racecontrol_*.db"))
    for old in backups[:-keep]:
        old.unlink()
        log(f"Altes Backup gelöscht: {old.name}")


def main() -> int:
    args     = parse_args()
    db_path  = pathlib.Path(args.db).expanduser().resolve() if args.db else DB_PATH
    bak_dir  = pathlib.Path(args.dest).expanduser().resolve() if args.dest else DEFAULT_BACKUP_DIR

    if not db_path.exists():
        log(f"Fehler: Datenbankdatei nicht gefunden: {db_path}", error=True)
        return 1

    bak_dir.mkdir(parents=True, exist_ok=True)
    ts   = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dest = bak_dir / f"racecontrol_{ts}.db"

    log(f"Starte Backup: {db_path} → {dest}")
    try:
        src = sqlite3.connect(str(db_path))
        dst = sqlite3.connect(str(dest))
        src.backup(dst)
        dst.close()
        src.close()
    except sqlite3.Error as exc:
        log(f"Fehler beim Backup: {exc}", error=True)
        return 2

    size_kb = dest.stat().st_size // 1024
    log(f"Backup erstellt: {dest.name} ({size_kb} KB)")

    rotate(bak_dir, args.keep)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
