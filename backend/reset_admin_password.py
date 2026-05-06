#!/usr/bin/env python3
"""Reset password for a RaceControl user directly on the server.

This script updates the SQLite user password hash without going through the API.
It uses the same bcrypt-based hashing as the backend.

Usage:
    python backend/reset_admin_password.py --user admin
    python backend/reset_admin_password.py --user admin --password secret123

Environment:
    DATA_DIR  Optional path to the RaceControl data directory.
"""

from __future__ import annotations

import argparse
import datetime
import getpass
import os
import pathlib
import sqlite3
import sys

from auth import hash_password

ROOT = pathlib.Path(__file__).resolve().parent
DATA_DIR = pathlib.Path(os.environ.get("DATA_DIR", str(ROOT.parent)))
DB_PATH = DATA_DIR / "racecontrol.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reset a RaceControl user password directly in the local database."
    )
    parser.add_argument(
        "-u",
        "--user",
        "--username",
        dest="user",
        default="admin",
        help="Username of the account to reset (default: admin)",
    )
    parser.add_argument(
        "--password",
        help="New password. If omitted, the script prompts securely.",
    )
    parser.add_argument(
        "--db",
        help="Path to racecontrol.db. Defaults to DATA_DIR/racecontrol.db or repo root.",
    )
    parser.add_argument(
        "--log-file",
        help="Optional path to a log file. Appends timestamped action logging.",
    )
    return parser.parse_args()


def log(message: str, *, error: bool = False, log_file: pathlib.Path | None = None) -> None:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    output = sys.stderr if error else sys.stdout
    print(line, file=output)
    if log_file:
        try:
            with open(log_file, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        except OSError:
            print(f"Warnung: Logdatei '{log_file}' konnte nicht geschrieben werden.", file=sys.stderr)


def get_password(args: argparse.Namespace) -> str:
    if args.password:
        return args.password

    password = getpass.getpass("Neues Passwort: ")
    confirm = getpass.getpass("Passwort wiederholen: ")
    if password != confirm:
        print("Fehler: Die Passwörter stimmen nicht überein.", file=sys.stderr)
        sys.exit(1)
    if not password:
        print("Fehler: Passwort darf nicht leer sein.", file=sys.stderr)
        sys.exit(1)
    return password


def resolve_db_path(args: argparse.Namespace) -> pathlib.Path:
    if args.db:
        return pathlib.Path(args.db).expanduser().resolve()
    return DB_PATH


def load_user(conn: sqlite3.Connection, username: str) -> sqlite3.Row | None:
    conn.row_factory = sqlite3.Row
    return conn.execute("SELECT id, username FROM Users WHERE username = ?", (username,)).fetchone()


def main() -> int:
    args = parse_args()
    db_path = resolve_db_path(args)
    log_file = pathlib.Path(args.log_file).expanduser().resolve() if args.log_file else None

    if not db_path.exists():
        log(
            f"Fehler: Datenbankdatei nicht gefunden: {db_path}. Setzen Sie DATA_DIR oder --db.",
            error=True,
            log_file=log_file,
        )
        return 1

    password = get_password(args)
    log(f"Starte Passwort-Reset für Benutzer '{args.user}' in Datenbank '{db_path}'.", log_file=log_file)

    conn = None
    try:
        conn = sqlite3.connect(str(db_path))
        row = load_user(conn, args.user)
        if not row:
            log(f"Fehler: Benutzer '{args.user}' wurde nicht gefunden.", error=True, log_file=log_file)
            return 1

        log(f"Benutzer gefunden: ID {row['id']} — '{row['username']}'. Passwort wird gesetzt …", log_file=log_file)

        conn.execute(
            "UPDATE Users SET password_hash = ? WHERE id = ?",
            (hash_password(password), row["id"]),
        )
        conn.commit()
        log(f"Passwort für Benutzer '{args.user}' wurde erfolgreich zurückgesetzt.", log_file=log_file)
        return 0
    except sqlite3.Error as exc:
        log(f"Datenbankfehler: {exc}", error=True, log_file=log_file)
        return 2
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
