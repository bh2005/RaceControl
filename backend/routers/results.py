from __future__ import annotations
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Annotated, Optional
import csv
import io
import sqlite3

from broadcast import manager
from database import get_db
from deps import require_roles, get_current_user, CurrentUser
from schemas import (
    RaceResultCreate, RaceResultUpdate, RaceResultResponse,
    RunPenaltyCreate, RunPenaltyResponse,
    RunResultView, StandingRow,
)

router = APIRouter(prefix="/events/{event_id}", tags=["results"])

ZeitnahmeOrAbove = Annotated[sqlite3.Row, Depends(require_roles("admin", "schiedsrichter", "zeitnahme"))]
SchiriOrAdmin = Annotated[sqlite3.Row, Depends(require_roles("admin", "schiedsrichter"))]


def _get_class_row(db: sqlite3.Connection, class_id: int) -> sqlite3.Row:
    row = db.execute("SELECT run_status, is_exhibition FROM Classes WHERE id = ?", (class_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Klasse nicht gefunden")
    return row


def _require_class_running(db: sqlite3.Connection, class_id: int) -> None:
    """Zeitnahme darf nur buchen wenn Klasse läuft (Ausnahme: Vorstarter/Exhibition)."""
    cls = _get_class_row(db, class_id)
    if cls["is_exhibition"]:
        return
    if cls["run_status"] not in ("running", "paused"):
        raise HTTPException(
            409,
            "Klasse läuft nicht – Zeiteingabe erst nach Klassenstart möglich",
        )


def _require_class_not_official(db: sqlite3.Connection, class_id: int) -> None:
    """Korrekturen gesperrt sobald die Klasse offiziell freigegeben wurde."""
    cls = _get_class_row(db, class_id)
    if cls["run_status"] == "official":
        raise HTTPException(
            409,
            "Klasse ist offiziell freigegeben – keine Korrekturen mehr möglich",
        )


# ── RaceResults ───────────────────────────────────────────────────────────────

@router.get("/results", response_model=list[RaceResultResponse])
def list_results(
    event_id: int,
    class_id: Optional[int] = None,
    run_number: Optional[int] = None,
    db: Annotated[sqlite3.Connection, Depends(get_db)] = ...,
):
    query = "SELECT * FROM RaceResults WHERE event_id = ?"
    params: list = [event_id]
    if class_id is not None:
        query += " AND class_id = ?"
        params.append(class_id)
    if run_number is not None:
        query += " AND run_number = ?"
        params.append(run_number)
    query += " ORDER BY class_id, run_number, participant_id"
    return [dict(r) for r in db.execute(query, params).fetchall()]


@router.post("/results", response_model=RaceResultResponse, status_code=201)
def create_result(
    event_id: int,
    body: RaceResultCreate,
    background_tasks: BackgroundTasks,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    user: ZeitnahmeOrAbove,
):
    body.event_id = event_id
    _require_class_running(db, body.class_id)
    try:
        cur = db.execute(
            """INSERT INTO RaceResults
               (event_id, participant_id, class_id, run_number, raw_time, status, entered_by)
               VALUES (?,?,?,?,?,?,?)""",
            (event_id, body.participant_id, body.class_id, body.run_number,
             body.raw_time, body.status, user["id"]),
        )
        db.commit()
        background_tasks.add_task(
            manager.broadcast,
            {"type": "results", "event_id": event_id, "class_id": body.class_id},
        )
        return dict(db.execute("SELECT * FROM RaceResults WHERE id = ?", (cur.lastrowid,)).fetchone())
    except Exception:
        raise HTTPException(409, "Ergebnis für diesen Fahrer/Lauf bereits vorhanden")


@router.patch("/results/{result_id}", response_model=RaceResultResponse)
def update_result(
    event_id: int,
    result_id: int,
    body: RaceResultUpdate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    user: SchiriOrAdmin,
):
    existing = db.execute("SELECT * FROM RaceResults WHERE id = ? AND event_id = ?", (result_id, event_id)).fetchone()
    if not existing:
        raise HTTPException(404, "Ergebnis nicht gefunden")
    _require_class_not_official(db, existing["class_id"])

    updates: dict = {}
    if body.raw_time is not None:
        updates["raw_time"] = body.raw_time
    if body.status is not None:
        updates["status"] = body.status
    if body.is_official is not None:
        updates["is_official"] = int(body.is_official)

    if updates:
        sets = ", ".join(f"{k} = ?" for k in updates)
        db.execute(f"UPDATE RaceResults SET {sets} WHERE id = ?", (*updates.values(), result_id))

    # Audit each changed field
    for field, new_val in updates.items():
        old_val = existing[field]
        if old_val != new_val:
            db.execute(
                """INSERT INTO AuditLog (result_id, user_id, field_changed, old_value, new_value, reason)
                   VALUES (?,?,?,?,?,?)""",
                (result_id, user["id"], field, str(old_val), str(new_val), body.reason),
            )

    db.commit()
    return dict(db.execute("SELECT * FROM RaceResults WHERE id = ?", (result_id,)).fetchone())


# ── Penalties ─────────────────────────────────────────────────────────────────

@router.get("/results/{result_id}/penalties", response_model=list[RunPenaltyResponse])
def list_penalties(
    event_id: int,
    result_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
):
    return [dict(r) for r in db.execute(
        "SELECT * FROM RunPenalties WHERE result_id = ?", (result_id,)
    ).fetchall()]


@router.post("/results/{result_id}/penalties", response_model=RunPenaltyResponse, status_code=201)
def add_penalty(
    event_id: int,
    result_id: int,
    body: RunPenaltyCreate,
    background_tasks: BackgroundTasks,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    user: ZeitnahmeOrAbove,
):
    body.result_id = result_id
    cur = db.execute(
        "INSERT INTO RunPenalties (result_id, penalty_definition_id, count, entered_by) VALUES (?,?,?,?)",
        (result_id, body.penalty_definition_id, body.count, user["id"]),
    )
    db.commit()
    row = db.execute("SELECT class_id FROM RaceResults WHERE id = ?", (result_id,)).fetchone()
    background_tasks.add_task(
        manager.broadcast,
        {"type": "results", "event_id": event_id, "class_id": row["class_id"] if row else None},
    )
    return dict(db.execute("SELECT * FROM RunPenalties WHERE id = ?", (cur.lastrowid,)).fetchone())


@router.delete("/results/{result_id}/penalties/{penalty_id}", status_code=204)
def delete_penalty(
    event_id: int,
    result_id: int,
    penalty_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: SchiriOrAdmin,
):
    row = db.execute("SELECT class_id FROM RaceResults WHERE id = ?", (result_id,)).fetchone()
    if row:
        _require_class_not_official(db, row["class_id"])
    db.execute("DELETE FROM RunPenalties WHERE id = ? AND result_id = ?", (penalty_id, result_id))
    db.commit()


# ── Audit-Log ─────────────────────────────────────────────────────────────────

@router.get("/audit-log")
def get_audit_log(
    event_id: int,
    class_id: Optional[int] = None,
    limit: int = 100,
    db: Annotated[sqlite3.Connection, Depends(get_db)] = ...,
):
    query = """
        SELECT
            al.id,
            al.result_id,
            al.field_changed,
            al.old_value,
            al.new_value,
            al.reason,
            al.timestamp,
            COALESCE(u.display_name, u.username) AS user_name,
            p.start_number,
            p.first_name || ' ' || p.last_name   AS driver_name,
            r.class_id,
            r.run_number
        FROM AuditLog al
        JOIN  RaceResults  r ON r.id  = al.result_id
        LEFT JOIN Users       u ON u.id  = al.user_id
        LEFT JOIN Participants p ON p.id = r.participant_id
        WHERE r.event_id = ?
    """
    params: list = [event_id]
    if class_id is not None:
        query += " AND r.class_id = ?"
        params.append(class_id)
    query += " ORDER BY al.timestamp DESC LIMIT ?"
    params.append(limit)
    return [dict(r) for r in db.execute(query, params).fetchall()]


# ── Views ─────────────────────────────────────────────────────────────────────

@router.get("/run-results", response_model=list[RunResultView])
def run_results(
    event_id: int,
    class_id: Optional[int] = None,
    run_number: Optional[int] = None,
    db: Annotated[sqlite3.Connection, Depends(get_db)] = ...,
):
    query = "SELECT * FROM v_run_results WHERE event_id = ?"
    params: list = [event_id]
    if class_id is not None:
        query += " AND class_id = ?"
        params.append(class_id)
    if run_number is not None:
        query += " AND run_number = ?"
        params.append(run_number)
    query += " ORDER BY class_id, run_number, total_time NULLS LAST"
    return [dict(r) for r in db.execute(query, params).fetchall()]


@router.get("/standings", response_model=list[StandingRow])
def standings(
    event_id: int,
    class_id: Optional[int] = None,
    db: Annotated[sqlite3.Connection, Depends(get_db)] = ...,
):
    query = "SELECT * FROM v_class_standings_sum_all WHERE event_id = ?"
    params: list = [event_id]
    if class_id is not None:
        query += " AND class_id = ?"
        params.append(class_id)
    query += " ORDER BY class_id, rank"
    return [dict(r) for r in db.execute(query, params).fetchall()]


@router.get("/statistics")
def statistics(
    event_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)] = ...,
):
    fastest_per_class = [dict(r) for r in db.execute("""
        SELECT v.class_id, v.class_name, v.participant_id, v.start_number,
               v.first_name, v.last_name, v.club, v.run_number, v.total_time
        FROM v_run_results v
        WHERE v.event_id = ?
          AND v.run_number > 0
          AND v.status = 'valid'
          AND v.total_time IS NOT NULL
          AND v.total_time = (
              SELECT MIN(v2.total_time) FROM v_run_results v2
              WHERE v2.class_id = v.class_id AND v2.event_id = v.event_id
                AND v2.run_number > 0 AND v2.status = 'valid' AND v2.total_time IS NOT NULL
          )
        ORDER BY v.class_id, v.total_time
    """, (event_id,)).fetchall()]

    fastest_dame = db.execute("""
        SELECT v.participant_id, v.start_number, v.first_name, v.last_name,
               v.club, v.class_name, v.run_number, v.total_time
        FROM v_run_results v
        JOIN Participants p ON p.id = v.participant_id
        WHERE v.event_id = ? AND v.run_number > 0 AND v.status = 'valid'
          AND v.total_time IS NOT NULL AND p.gender = 'w'
        ORDER BY v.total_time LIMIT 1
    """, (event_id,)).fetchone()

    fastest_herr = db.execute("""
        SELECT v.participant_id, v.start_number, v.first_name, v.last_name,
               v.club, v.class_name, v.run_number, v.total_time
        FROM v_run_results v
        JOIN Participants p ON p.id = v.participant_id
        WHERE v.event_id = ? AND v.run_number > 0 AND v.status = 'valid'
          AND v.total_time IS NOT NULL AND p.gender = 'm'
        ORDER BY v.total_time LIMIT 1
    """, (event_id,)).fetchone()

    return {
        "fastest_per_class": fastest_per_class,
        "fastest_dame": dict(fastest_dame) if fastest_dame else None,
        "fastest_herr": dict(fastest_herr) if fastest_herr else None,
    }


def _fmt(seconds: Optional[float], zero_as_dash: bool = False) -> str:
    """Formatiert Sekunden als MM:SS.sss oder SS.sss für CSV-Export."""
    if seconds is None:
        return ""
    if zero_as_dash and seconds == 0.0:
        return "0.000"
    if seconds >= 60:
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m}:{s:06.3f}"
    return f"{seconds:.3f}"


@router.get("/results/export")
def export_results_csv(
    event_id: int,
    class_id: Optional[int] = None,
    db: Annotated[sqlite3.Connection, Depends(get_db)] = ...,
):
    """CSV-Export der Ergebnisse. Kein Login erforderlich (Ergebnisse sind öffentlich).
    Optional ?class_id=N für eine einzelne Klasse."""

    event = db.execute(
        "SELECT name, date, location FROM Events WHERE id = ?", (event_id,)
    ).fetchone()
    if not event:
        raise HTTPException(404, "Veranstaltung nicht gefunden")

    class_q = "SELECT id, name FROM Classes WHERE event_id = ? ORDER BY sort_order, id"
    class_p: list = [event_id]
    if class_id is not None:
        class_q += " AND id = ?"
        class_p.append(class_id)
    classes = db.execute(class_q, class_p).fetchall()

    output = io.StringIO()
    w = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")

    for cls in classes:
        cid = cls["id"]

        # Alle Teilnehmer der Klasse
        participants = db.execute("""
            SELECT p.id, p.start_number, p.first_name, p.last_name, p.birth_year, p.gender,
                   COALESCE(cl.short_name, cl.name, 'n.N.') AS club
            FROM   Participants p
            LEFT JOIN Clubs cl ON cl.id = p.club_id
            WHERE  p.event_id = ? AND p.class_id = ?
            ORDER  BY p.start_number
        """, (event_id, cid)).fetchall()

        if not participants:
            continue

        # Alle Laufergebnisse der Klasse
        run_rows = db.execute("""
            SELECT v.participant_id, v.run_number, v.raw_time,
                   v.total_penalties, v.total_time, v.status
            FROM   v_run_results v
            WHERE  v.event_id = ? AND v.class_id = ?
            ORDER  BY v.participant_id, v.run_number
        """, (event_id, cid)).fetchall()

        # Pivot: {participant_id: {run_number: row}}
        pivot: dict[int, dict[int, dict]] = {}
        for r in run_rows:
            pid = r["participant_id"]
            pivot.setdefault(pid, {})[r["run_number"]] = dict(r)

        run_numbers = sorted({r["run_number"] for r in run_rows})

        # Gesamtzeiten und Rang in Python berechnen
        def _total(pid: int) -> float | None:
            runs = pivot.get(pid, {})
            times = [
                runs[rn]["total_time"]
                for rn in runs
                if rn > 0
                and runs[rn].get("status") == "valid"
                and runs[rn].get("total_time") is not None
            ]
            return sum(times) if times else None

        totals = {p["id"]: _total(p["id"]) for p in participants}

        def _rank_key(pid: int):
            t = totals[pid]
            return (t is None, t or 0.0)

        sorted_pids = sorted([p["id"] for p in participants], key=_rank_key)
        ranks: dict[int, int | str] = {}
        counter = 1
        for i, pid in enumerate(sorted_pids):
            if totals[pid] is None:
                ranks[pid] = "–"
            else:
                # gleiche Zeit → gleicher Rang
                if i > 0 and totals[pid] == totals[sorted_pids[i - 1]]:
                    ranks[pid] = ranks[sorted_pids[i - 1]]
                else:
                    ranks[pid] = counter
            counter = i + 2

        p_by_id = {p["id"]: dict(p) for p in participants}
        best_time = next((totals[pid] for pid in sorted_pids if totals[pid] is not None), None)

        # Klassen-Header
        loc = event["location"] or ""
        w.writerow([f"Veranstaltung: {event['name']} · {event['date']}" + (f" · {loc}" if loc else "")])
        w.writerow([f"Klasse: {cls['name']}"])
        w.writerow([])

        # Spaltenköpfe
        header = ["Rang", "Startnr.", "Nachname", "Vorname", "Verein", "Jg."]
        for rn in run_numbers:
            lbl = "Training" if rn == 0 else f"Lauf {rn}"
            header += [f"{lbl} Rohzeit", f"{lbl} Strafen", f"{lbl} Gesamt", f"{lbl} Status"]
        header += ["Summe", "Differenz"]
        w.writerow(header)

        # Datenzeilen (nach Rang sortiert)
        for pid in sorted_pids:
            p = p_by_id[pid]
            row: list = [
                ranks[pid],
                p["start_number"] or "",
                p["last_name"],
                p["first_name"],
                p["club"],
                p["birth_year"] or "",
            ]
            for rn in run_numbers:
                run = pivot.get(pid, {}).get(rn)
                if run:
                    status = run.get("status") or ""
                    row += [
                        _fmt(run.get("raw_time")),
                        _fmt(run.get("total_penalties"), zero_as_dash=True),
                        _fmt(run.get("total_time")),
                        "" if status == "valid" else status.upper(),
                    ]
                else:
                    row += ["", "", "", ""]

            total = totals[pid]
            row.append(_fmt(total))
            if total is not None and best_time is not None:
                diff = total - best_time
                row.append("+0.000" if diff == 0 else f"+{diff:.3f}")
            else:
                row.append("")

            w.writerow(row)

        w.writerow([])  # Leerzeile zwischen Klassen

    event_name = event["name"].replace(" ", "_")
    filename = f"Ergebnisse_{event_name}_{event['date']}.csv"
    content = "﻿" + output.getvalue()  # UTF-8 BOM → Excel öffnet korrekt

    return StreamingResponse(
        iter([content.encode("utf-8")]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
