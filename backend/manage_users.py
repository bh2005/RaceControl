#!/usr/bin/env python3
"""Manage RaceControl user accounts directly in the SQLite database.

Subcommands:
    list                     Print all users (id, username, role, active, created_at)
    set-role  USER ROLE      Change a user's role
    activate  USER           Set is_active = 1
    deactivate USER          Set is_active = 0
    create    USER ROLE      Create a new user (prompts for password)
    delete    USER           Delete a user (cannot delete 'admin')

Roles: admin, schiedsrichter, nennung, zeitnahme, marshal, viewer

Usage:
    python backend/manage_users.py list
    python backend/manage_users.py set-role timing zeitnahme
    python backend/manage_users.py deactivate gast
    python backend/manage_users.py create stenzel schiedsrichter
    python backend/manage_users.py create stenzel schiedsrichter --password geheim42

Exit codes:
    0  Success
    1  User / argument error
    2  sqlite3 error

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

ROOT     = pathlib.Path(__file__).resolve().parent
DATA_DIR = pathlib.Path(os.environ.get("DATA_DIR", str(ROOT.parent)))
DB_PATH  = DATA_DIR / "racecontrol.db"

VALID_ROLES = {"admin", "schiedsrichter", "nennung", "zeitnahme", "marshal", "viewer"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage RaceControl user accounts."
    )
    parser.add_argument("--db", help="Path to racecontrol.db.")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all users.")

    p_role = sub.add_parser("set-role", help="Change a user's role.")
    p_role.add_argument("user", help="Username")
    p_role.add_argument("role", choices=sorted(VALID_ROLES), help="New role")

    p_act = sub.add_parser("activate", help="Enable a user account.")
    p_act.add_argument("user", help="Username")

    p_deact = sub.add_parser("deactivate", help="Disable a user account.")
    p_deact.add_argument("user", help="Username")

    p_create = sub.add_parser("create", help="Create a new user.")
    p_create.add_argument("user", help="Username")
    p_create.add_argument("role", choices=sorted(VALID_ROLES), help="Role")
    p_create.add_argument("--password", help="Password (prompted if omitted).")
    p_create.add_argument("--display-name", help="Optional display name.")

    p_del = sub.add_parser("delete", help="Delete a user (cannot delete admin).")
    p_del.add_argument("user", help="Username")

    return parser.parse_args()


def log(msg: str, *, error: bool = False) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr if error else sys.stdout)


def get_db(db_path: pathlib.Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def require_user(conn: sqlite3.Connection, username: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT id, username, role, is_active FROM Users WHERE username = ?", (username,)
    ).fetchone()
    if not row:
        log(f"Fehler: Benutzer '{username}' nicht gefunden.", error=True)
        sys.exit(1)
    return row


def prompt_password() -> str:
    pw = getpass.getpass("Passwort: ")
    confirm = getpass.getpass("Passwort wiederholen: ")
    if pw != confirm:
        print("Fehler: Passwörter stimmen nicht überein.", file=sys.stderr)
        sys.exit(1)
    if not pw:
        print("Fehler: Passwort darf nicht leer sein.", file=sys.stderr)
        sys.exit(1)
    return pw


def cmd_list(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        "SELECT id, username, role, is_active, created_at FROM Users ORDER BY id"
    ).fetchall()
    if not rows:
        log("Keine Benutzer vorhanden.")
        return 0
    header = f"{'ID':<4}  {'Benutzername':<20}  {'Rolle':<16}  {'Aktiv':<5}  Erstellt"
    print(header)
    print("-" * len(header))
    for r in rows:
        aktiv = "ja" if r["is_active"] else "nein"
        print(f"{r['id']:<4}  {r['username']:<20}  {r['role']:<16}  {aktiv:<5}  {r['created_at']}")
    return 0


def cmd_set_role(conn: sqlite3.Connection, username: str, role: str) -> int:
    row = require_user(conn, username)
    old_role = row["role"]
    conn.execute("UPDATE Users SET role = ? WHERE username = ?", (role, username))
    conn.commit()
    log(f"Rolle von '{username}' geändert: {old_role} → {role}")
    return 0


def cmd_activate(conn: sqlite3.Connection, username: str, active: int) -> int:
    require_user(conn, username)
    conn.execute("UPDATE Users SET is_active = ? WHERE username = ?", (active, username))
    conn.commit()
    status = "aktiviert" if active else "deaktiviert"
    log(f"Benutzer '{username}' {status}.")
    return 0


def cmd_create(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    existing = conn.execute(
        "SELECT id FROM Users WHERE username = ?", (args.user,)
    ).fetchone()
    if existing:
        log(f"Fehler: Benutzername '{args.user}' bereits vergeben.", error=True)
        return 1

    password = args.password if args.password else prompt_password()
    from auth import hash_password
    pw_hash = hash_password(password)

    conn.execute(
        "INSERT INTO Users (username, password_hash, role, display_name) VALUES (?, ?, ?, ?)",
        (args.user, pw_hash, args.role, args.display_name),
    )
    conn.commit()
    log(f"Benutzer '{args.user}' (Rolle: {args.role}) erstellt.")
    return 0


def cmd_delete(conn: sqlite3.Connection, username: str) -> int:
    if username == "admin":
        log("Fehler: Der 'admin'-Benutzer kann nicht gelöscht werden.", error=True)
        return 1
    row = require_user(conn, username)
    conn.execute("DELETE FROM Users WHERE id = ?", (row["id"],))
    conn.commit()
    log(f"Benutzer '{username}' (ID {row['id']}) gelöscht.")
    return 0


def main() -> int:
    args    = parse_args()
    db_path = pathlib.Path(args.db).expanduser().resolve() if args.db else DB_PATH

    if not db_path.exists():
        log(f"Fehler: Datenbankdatei nicht gefunden: {db_path}", error=True)
        return 1

    try:
        conn = get_db(db_path)

        if args.command == "list":
            rc = cmd_list(conn)
        elif args.command == "set-role":
            rc = cmd_set_role(conn, args.user, args.role)
        elif args.command == "activate":
            rc = cmd_activate(conn, args.user, 1)
        elif args.command == "deactivate":
            rc = cmd_activate(conn, args.user, 0)
        elif args.command == "create":
            rc = cmd_create(conn, args)
        elif args.command == "delete":
            rc = cmd_delete(conn, args.user)
        else:
            rc = 1

        conn.close()
        return rc

    except sqlite3.Error as exc:
        log(f"SQLite-Fehler: {exc}", error=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
