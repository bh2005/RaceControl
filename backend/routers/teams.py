"""
Mannschaftswertung & Tagesschnellste

Mannschaft: 4 Fahrer, beste 3 Klassenpunkte zählen.
Punkte kommen aus der points_formula des Reglements (JSON: {"1": 40, "2": 37, ...}).
"""
from __future__ import annotations
import json
from typing import Annotated, Optional
import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from deps import require_roles
from schemas import (
    TeamCreate, TeamResponse,
    TeamMemberCreate, TeamMemberResponse,
    TeamStandingRow, FastestOfDayRow,
)

router = APIRouter(prefix="/events/{event_id}", tags=["teams"])

AdminOrNennung = Annotated[sqlite3.Row, Depends(require_roles("admin", "nennung"))]


# ── CRUD Teams ────────────────────────────────────────────────────────────────

@router.get("/teams", response_model=list[TeamResponse])
def list_teams(event_id: int, db: Annotated[sqlite3.Connection, Depends(get_db)]):
    return [dict(r) for r in db.execute(
        "SELECT * FROM Teams WHERE event_id = ? ORDER BY name", (event_id,)
    ).fetchall()]


@router.post("/teams", response_model=TeamResponse, status_code=201)
def create_team(
    event_id: int,
    body: TeamCreate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOrNennung,
):
    body.event_id = event_id
    try:
        cur = db.execute(
            "INSERT INTO Teams (event_id, name, club) VALUES (?,?,?)",
            (event_id, body.name, body.club),
        )
        db.commit()
        return dict(db.execute("SELECT * FROM Teams WHERE id = ?", (cur.lastrowid,)).fetchone())
    except Exception:
        raise HTTPException(409, "Mannschaftsname bereits vergeben")


@router.delete("/teams/{team_id}", status_code=204)
def delete_team(
    event_id: int,
    team_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOrNennung,
):
    db.execute("DELETE FROM Teams WHERE id = ? AND event_id = ?", (team_id, event_id))
    db.commit()


# ── Mitglieder ────────────────────────────────────────────────────────────────

@router.get("/teams/{team_id}/members", response_model=list[TeamMemberResponse])
def list_members(team_id: int, event_id: int, db: Annotated[sqlite3.Connection, Depends(get_db)]):
    return [dict(r) for r in db.execute(
        "SELECT * FROM TeamMembers WHERE team_id = ?", (team_id,)
    ).fetchall()]


@router.post("/teams/{team_id}/members", response_model=TeamMemberResponse, status_code=201)
def add_member(
    event_id: int,
    team_id: int,
    body: TeamMemberCreate,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOrNennung,
):
    # Max. 4 Mitglieder
    count = db.execute("SELECT COUNT(*) FROM TeamMembers WHERE team_id = ?", (team_id,)).fetchone()[0]
    if count >= 4:
        raise HTTPException(422, "Mannschaft hat bereits 4 Mitglieder (Maximum)")
    try:
        cur = db.execute(
            "INSERT INTO TeamMembers (team_id, participant_id) VALUES (?,?)",
            (team_id, body.participant_id),
        )
        db.commit()
        return dict(db.execute("SELECT * FROM TeamMembers WHERE id = ?", (cur.lastrowid,)).fetchone())
    except Exception:
        raise HTTPException(409, "Teilnehmer bereits Mitglied dieser Mannschaft")


@router.delete("/teams/{team_id}/members/{member_id}", status_code=204)
def remove_member(
    event_id: int,
    team_id: int,
    member_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    _: AdminOrNennung,
):
    db.execute("DELETE FROM TeamMembers WHERE id = ? AND team_id = ?", (member_id, team_id))
    db.commit()


# ── Mannschaftswertung ────────────────────────────────────────────────────────

def _lookup_points(points_formula: Optional[str], rank: int) -> int:
    """Punkte aus JSON-Tabelle für gegebenen Rang. Fallback: 0."""
    if not points_formula:
        return 0
    try:
        table: dict = json.loads(points_formula)
        # Exakter Rang, sonst letzter Eintrag wiederholen
        if str(rank) in table:
            return int(table[str(rank)])
        # Alle Ränge ab letztem Eintrag bekommen den kleinsten Wert
        max_rank = max(int(k) for k in table)
        if rank > max_rank:
            return int(table[str(max_rank)])
        return 0
    except Exception:
        return 0


@router.get("/teams/standings", response_model=list[TeamStandingRow])
def team_standings(
    event_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
):
    teams = db.execute(
        "SELECT * FROM Teams WHERE event_id = ? ORDER BY name", (event_id,)
    ).fetchall()

    results = []
    for team in teams:
        members = db.execute(
            "SELECT tm.id, tm.participant_id FROM TeamMembers tm WHERE tm.team_id = ?",
            (team["id"],),
        ).fetchall()

        member_details = []
        for m in members:
            # Rang des Teilnehmers in seiner Klasse (aus v_class_standings_sum_all)
            standing = db.execute(
                """SELECT s.rank, s.class_id, s.class_name
                   FROM v_class_standings_sum_all s
                   WHERE s.event_id = ? AND s.participant_id = ?""",
                (event_id, m["participant_id"]),
            ).fetchone()

            if not standing:
                member_details.append({
                    "participant_id": m["participant_id"],
                    "rank": None,
                    "points": 0,
                    "class_name": "–",
                })
                continue

            # Punkteformel des Reglements dieser Klasse holen
            reg = db.execute(
                """SELECT r.points_formula
                   FROM Reglements r
                   JOIN Classes c ON c.reglement_id = r.id
                   WHERE c.id = ?""",
                (standing["class_id"],),
            ).fetchone()

            points = _lookup_points(
                reg["points_formula"] if reg else None,
                standing["rank"],
            )
            p = db.execute(
                "SELECT first_name, last_name, start_number FROM Participants WHERE id = ?",
                (m["participant_id"],),
            ).fetchone()
            member_details.append({
                "participant_id": m["participant_id"],
                "start_number": p["start_number"] if p else None,
                "name": f"{p['first_name']} {p['last_name']}" if p else "?",
                "class_name": standing["class_name"],
                "rank": standing["rank"],
                "points": points,
            })

        # Beste 3 Punkte summieren
        sorted_by_points = sorted(member_details, key=lambda x: x["points"], reverse=True)
        top3 = sorted_by_points[:3]
        total_points = sum(m["points"] for m in top3)

        results.append(TeamStandingRow(
            team_id=team["id"],
            team_name=team["name"],
            club=team["club"],
            member_count=len(members),
            scoring_members=len(top3),
            total_points=total_points,
            members=member_details,
        ))

    results.sort(key=lambda x: x.total_points, reverse=True)
    return results


# ── Tagesschnellste ──────────────────────────────────────────────────────────

@router.get("/fastest-of-day", response_model=list[FastestOfDayRow])
def fastest_of_day(
    event_id: int,
    reglement_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
):
    """
    Schnellste Einzellaufzeit je Teilnehmer für das angegebene Reglement.
    KT und KS2000 jeweils separat aufrufen (verschiedene reglement_id).
    Gibt pro Fahrer nur seine schnellste Einzelzeit zurück, sortiert aufsteigend.
    """
    rows = db.execute(
        """SELECT participant_id, start_number, first_name, last_name, club,
                  class_name, run_number, MIN(run_time) AS run_time
           FROM v_fastest_of_day
           WHERE event_id = ? AND reglement_id = ?
           GROUP BY participant_id
           ORDER BY run_time ASC""",
        (event_id, reglement_id),
    ).fetchall()

    return [
        FastestOfDayRow(
            rank=i + 1,
            participant_id=r["participant_id"],
            start_number=r["start_number"],
            first_name=r["first_name"],
            last_name=r["last_name"],
            club=r["club"],
            class_name=r["class_name"],
            run_number=r["run_number"],
            run_time=r["run_time"],
        )
        for i, r in enumerate(rows)
    ]
