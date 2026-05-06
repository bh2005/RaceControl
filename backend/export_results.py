#!/usr/bin/env python3
"""Export race results to CSV.

Without --event: lists all events with their IDs so you can pick one.
With --event ID: exports all results of that event grouped by class.

Output format: UTF-8 with BOM (Excel-compatible), semicolon-separated.
Columns: Platz, Klasse, Startnr, Vorname, Nachname, Verein,
         Training, Lauf1, Lauf2, … (up to max run_number), Gesamt

Usage:
    python backend/export_results.py
    python backend/export_results.py --event 3
    python backend/export_results.py --event 3 --out /tmp/ergebnisse.csv
    python backend/export_results.py --event 3 --official-only

Exit codes:
    0  Success
    1  Not found / bad argument
    2  sqlite3 error

Environment:
    DATA_DIR  Optional path to the RaceControl data directory.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import io
import os
import pathlib
import sqlite3
import sys

ROOT     = pathlib.Path(__file__).resolve().parent
DATA_DIR = pathlib.Path(os.environ.get("DATA_DIR", str(ROOT.parent)))
DB_PATH  = DATA_DIR / "racecontrol.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export RaceControl event results to CSV."
    )
    parser.add_argument("--db",    help="Path to racecontrol.db.")
    parser.add_argument("--event", type=int, metavar="ID",
                        help="Event ID to export. Omit to list available events.")
    parser.add_argument("--out",   help="Output file path. Default: stdout.")
    parser.add_argument(
        "--official-only", action="store_true",
        help="Only include results marked is_official=1.",
    )
    return parser.parse_args()


def log(msg: str, *, error: bool = False) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr if error else sys.stdout)


def fmt_time(seconds: float | None) -> str:
    if seconds is None:
        return ""
    return f"{seconds:.3f}".replace(".", ",")  # German decimal comma


def list_events(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        "SELECT id, name, date, status FROM Events ORDER BY date DESC, id DESC"
    ).fetchall()
    if not rows:
        log("Keine Veranstaltungen in der Datenbank.")
        return 0
    print(f"{'ID':<5}  {'Datum':<12}  {'Status':<12}  Name")
    print("-" * 60)
    for r in rows:
        print(f"{r['id']:<5}  {r['date']:<12}  {r['status']:<12}  {r['name']}")
    return 0


def export_event(
    conn: sqlite3.Connection,
    event_id: int,
    official_only: bool,
    out_path: pathlib.Path | None,
) -> int:
    event = conn.execute(
        "SELECT id, name, date FROM Events WHERE id = ?", (event_id,)
    ).fetchone()
    if not event:
        log(f"Fehler: Veranstaltung mit ID {event_id} nicht gefunden.", error=True)
        return 1

    official_filter = "AND r.is_official = 1" if official_only else ""

    # Fetch all results via the view, grouped by class and participant
    rows = conn.execute(f"""
        SELECT
            vr.class_id,
            vr.class_name,
            vr.run_number,
            vr.participant_id,
            vr.start_number,
            vr.first_name,
            vr.last_name,
            vr.club,
            vr.raw_time,
            vr.status,
            vr.total_penalties,
            vr.total_time
        FROM v_run_results vr
        WHERE vr.event_id = ? {official_filter}
        ORDER BY vr.class_id, vr.participant_id, vr.run_number
    """, (event_id,)).fetchall()

    if not rows:
        log(f"Keine Ergebnisse für Veranstaltung {event_id} gefunden.")
        return 0

    # Determine max run number across all classes
    max_run = max(r["run_number"] for r in rows)

    # Pivot: build one dict per (class_id, participant_id)
    # key → {meta, runs: {run_number: (raw_time, penalties, total_time, status)}}
    classes_order: list[tuple[int, str]] = []
    seen_classes: set[int] = set()
    participants: dict[tuple[int, int], dict] = {}

    for r in rows:
        cid = r["class_id"]
        pid = r["participant_id"]
        if cid not in seen_classes:
            seen_classes.add(cid)
            classes_order.append((cid, r["class_name"]))
        key = (cid, pid)
        if key not in participants:
            participants[key] = {
                "class_id":    cid,
                "class_name":  r["class_name"],
                "start_number": r["start_number"],
                "first_name":  r["first_name"],
                "last_name":   r["last_name"],
                "club":        r["club"],
                "runs":        {},
            }
        participants[key]["runs"][r["run_number"]] = {
            "raw_time":    r["raw_time"],
            "penalties":   r["total_penalties"],
            "total_time":  r["total_time"],
            "status":      r["status"],
        }

    run_headers = []
    for rn in range(0, max_run + 1):
        label = "Training" if rn == 0 else f"Lauf {rn}"
        run_headers.extend([label, f"{label} (Strafe)", f"{label} (Gesamt)"])

    header = [
        "Platz", "Klasse", "Startnr",
        "Vorname", "Nachname", "Verein",
        *run_headers,
        "Beste Gesamtzeit",
    ]

    buf = io.StringIO()
    buf.write("﻿")  # BOM for Excel
    writer = csv.writer(buf, delimiter=";", lineterminator="\r\n")

    log(f"Exportiere: {event['name']} ({event['date']}) — "
        f"{len(participants)} Ergebnis-Einträge, max. Lauf {max_run}")

    writer.writerow([f"Veranstaltung: {event['name']}", event['date']])
    writer.writerow([])
    writer.writerow(header)

    for class_id, class_name in classes_order:
        class_participants = [
            (k, v) for k, v in participants.items() if v["class_id"] == class_id
        ]
        # Sort by best valid total_time (None/DNS last)
        def best_time(item: tuple) -> float:
            runs = item[1]["runs"]
            times = [
                v["total_time"] for v in runs.values()
                if v["total_time"] is not None and v["status"] == "valid"
            ]
            return min(times) if times else float("inf")

        class_participants.sort(key=best_time)

        for rank, (_, p) in enumerate(class_participants, start=1):
            run_cells: list[str] = []
            for rn in range(0, max_run + 1):
                run = p["runs"].get(rn)
                if run is None:
                    run_cells.extend(["", "", ""])
                elif run["status"] != "valid":
                    run_cells.extend([run["status"].upper(), "", ""])
                else:
                    run_cells.extend([
                        fmt_time(run["raw_time"]),
                        fmt_time(run["penalties"]),
                        fmt_time(run["total_time"]),
                    ])

            all_totals = [
                v["total_time"] for v in p["runs"].values()
                if v["total_time"] is not None and v["status"] == "valid"
            ]
            best = fmt_time(min(all_totals)) if all_totals else ""

            writer.writerow([
                rank, class_name, p["start_number"] or "",
                p["first_name"], p["last_name"], p["club"],
                *run_cells,
                best,
            ])

    csv_text = buf.getvalue()

    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(csv_text, encoding="utf-8-sig")
        log(f"CSV gespeichert: {out_path} ({out_path.stat().st_size} Bytes)")
    else:
        sys.stdout.write(csv_text)

    return 0


def main() -> int:
    args    = parse_args()
    db_path = pathlib.Path(args.db).expanduser().resolve() if args.db else DB_PATH
    out_path = pathlib.Path(args.out).expanduser().resolve() if args.out else None

    if not db_path.exists():
        log(f"Fehler: Datenbankdatei nicht gefunden: {db_path}", error=True)
        return 1

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        if args.event is None:
            rc = list_events(conn)
        else:
            rc = export_event(conn, args.event, args.official_only, out_path)

        conn.close()
        return rc

    except sqlite3.Error as exc:
        log(f"SQLite-Fehler: {exc}", error=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
