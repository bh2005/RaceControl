from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal, Optional


# ── Sponsors ─────────────────────────────────────────────────────────────────

class SponsorCreate(BaseModel):
    name: str
    logo_url: Optional[str] = None
    website_url: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class SponsorUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    website_url: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class SponsorResponse(SponsorCreate):
    id: int
    created_at: str
    model_config = {"from_attributes": True}


# ── Clubs ─────────────────────────────────────────────────────────────────────

class ClubCreate(BaseModel):
    name: str
    short_name: Optional[str] = None
    city: Optional[str] = None


class ClubUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    city: Optional[str] = None


class ClubResponse(ClubCreate):
    id: int
    created_at: str

    model_config = {"from_attributes": True}


# ── Reglements ──────────────────────────────────────────────────────────────

class ReglementCreate(BaseModel):
    name: str
    scoring_type: Literal["sum_all", "best_of", "sum_minus_worst"]
    points_formula: Optional[str] = None
    runs_per_class: int = 2
    has_training: bool = True


class ReglementResponse(ReglementCreate):
    id: int
    created_at: str

    model_config = {"from_attributes": True}


# ── PenaltyDefinitions ───────────────────────────────────────────────────────

class PenaltyDefinitionCreate(BaseModel):
    reglement_id: Optional[int] = None   # filled by path param in router
    label: str
    seconds: float = Field(ge=0)
    shortcut_key: Optional[str] = None
    sort_order: int = 0


class PenaltyDefinitionResponse(PenaltyDefinitionCreate):
    id: int

    model_config = {"from_attributes": True}


# ── Events ───────────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    name: str
    date: str  # ISO-8601 "YYYY-MM-DD"
    location: Optional[str] = None
    reglement_id: Optional[int] = None
    status: Literal["planned", "active", "finished", "official"] = "planned"
    timing_mode: Literal["slalom", "downhill"] = "slalom"
    description: Optional[str] = None


class EventUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[str] = None
    location: Optional[str] = None
    reglement_id: Optional[int] = None
    status: Optional[Literal["planned", "active", "finished", "official"]] = None
    timing_mode: Optional[Literal["slalom", "downhill"]] = None
    description: Optional[str] = None


class EventResponse(EventCreate):
    id: int
    created_at: str

    model_config = {"from_attributes": True}


# ── StartSchedule (Downhill / Seifenkiste) ────────────────────────────────────

class StartScheduleCreate(BaseModel):
    participant_id: int
    scheduled_start: str                        # "HH:MM:SS"
    lane: Optional[Literal["A", "B"]] = None   # None = Single-Lane (kein Spurfilter)


class StartScheduleUpdate(BaseModel):
    scheduled_start: Optional[str] = None
    lane: Optional[Literal["A", "B"]] = None


class StartScheduleResponse(BaseModel):
    id: int
    event_id: int
    participant_id: int
    lane: Optional[str] = None
    scheduled_start: str
    first_name: str
    last_name: str
    start_number: Optional[int] = None
    finished: bool = False        # True sobald ein RaceResult für run_number>=1 existiert

    model_config = {"from_attributes": True}


# ── Classes ───────────────────────────────────────────────────────────────────

class ClassCreate(BaseModel):
    event_id: Optional[int] = None       # filled by path param in router
    reglement_id: Optional[int] = None
    name: str
    short_name: Optional[str] = None
    min_birth_year: Optional[int] = None
    max_birth_year: Optional[int] = None
    run_status: Literal["planned", "running", "paused", "preliminary", "official"] = "planned"
    start_order: int = 0
    registration_closed_at: Optional[str] = None
    start_time: Optional[str] = None   # "HH:MM"
    end_time: Optional[str] = None     # ISO timestamp, triggers protest period
    is_exhibition: bool = False         # Vorstarter/Showklasse — kein run_status-Check bei Zeiteingabe


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    min_birth_year: Optional[int] = None
    max_birth_year: Optional[int] = None
    run_status: Optional[Literal["planned", "running", "paused", "preliminary", "official"]] = None
    start_order: Optional[int] = None
    reglement_id: Optional[int] = None
    registration_closed_at: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_exhibition: Optional[bool] = None


class ClassResponse(ClassCreate):
    id: int

    model_config = {"from_attributes": True}


# ── Participants ──────────────────────────────────────────────────────────────

class ParticipantCreate(BaseModel):
    event_id: Optional[int] = None       # filled by path param in router
    class_id: Optional[int] = None
    club_id: Optional[int] = None   # NULL = "n.N."
    start_number: Optional[int] = None  # NULL bis zur Auslosung
    first_name: str
    last_name: str
    birth_year: Optional[int] = None
    license_number: Optional[str] = None
    gender: Optional[Literal["m", "w"]] = None
    status: Literal["registered", "checked_in", "technical_ok", "disqualified"] = "registered"
    fee_paid: bool = False
    helmet_ok: bool = False


class ParticipantUpdate(BaseModel):
    class_id: Optional[int] = None
    club_id: Optional[int] = None
    start_number: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_year: Optional[int] = None
    license_number: Optional[str] = None
    gender: Optional[Literal["m", "w"]] = None
    status: Optional[Literal["registered", "checked_in", "technical_ok", "disqualified"]] = None
    fee_paid: Optional[bool] = None
    helmet_ok: Optional[bool] = None


class ParticipantResponse(BaseModel):
    id: int
    event_id: int
    class_id: Optional[int]
    club_id: Optional[int]
    start_number: Optional[int]
    first_name: str
    last_name: str
    birth_year: Optional[int]
    license_number: Optional[str]
    gender: Optional[str] = None
    status: str
    fee_paid: bool = False
    helmet_ok: bool = False
    club_name: Optional[str] = None   # aus JOIN, nicht in DB-Spalte

    model_config = {"from_attributes": True}


# ── RaceResults ───────────────────────────────────────────────────────────────

class RaceResultCreate(BaseModel):
    event_id: Optional[int] = None       # filled by path param in router
    participant_id: int
    class_id: int
    run_number: int = Field(ge=0)
    raw_time: Optional[float] = None
    status: Literal["valid", "dns", "dnf", "dsq"] = "valid"


class RaceResultUpdate(BaseModel):
    raw_time: Optional[float] = None
    status: Optional[Literal["valid", "dns", "dnf", "dsq"]] = None
    is_official: Optional[bool] = None
    reason: str  # Audit-Pflicht


class RaceResultResponse(BaseModel):
    id: int
    event_id: int
    participant_id: int
    class_id: int
    run_number: int
    raw_time: Optional[float]
    status: str
    is_official: bool
    entered_by: Optional[int]
    created_at: str

    model_config = {"from_attributes": True}


# ── RunPenalties ──────────────────────────────────────────────────────────────

class RunPenaltyCreate(BaseModel):
    result_id: Optional[int] = None
    penalty_definition_id: int
    count: int = Field(ge=1, default=1)


class RunPenaltyResponse(RunPenaltyCreate):
    id: int
    entered_by: Optional[int]
    created_at: str

    model_config = {"from_attributes": True}


# ── Users ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    password: str
    role: Literal["admin", "schiedsrichter", "nennung", "zeitnahme", "marshal", "viewer"]
    display_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    display_name: Optional[str]
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


# ── Teams / Mannschaftswertung ───────────────────────────────────────────────

class TeamCreate(BaseModel):
    event_id: Optional[int] = None       # filled by path param in router
    name: str
    club: Optional[str] = None


class TeamResponse(TeamCreate):
    id: int
    model_config = {"from_attributes": True}


class TeamMemberCreate(BaseModel):
    participant_id: int


class TeamMemberResponse(BaseModel):
    id: int
    team_id: int
    participant_id: int
    model_config = {"from_attributes": True}


class TeamStandingRow(BaseModel):
    team_id: int
    team_name: str
    club: Optional[str]
    member_count: int          # Anzahl Mitglieder gesamt (max. 4)
    scoring_members: int       # Mitglieder die in die Wertung kommen (max. 3)
    total_points: int          # Summe der Punkte der besten 3
    members: list[dict]        # Einzelne Mitglieder mit Rang + Punkten


# ── Tagesschnellste ──────────────────────────────────────────────────────────

class FastestOfDayRow(BaseModel):
    rank: int
    participant_id: int
    start_number: int
    first_name: str
    last_name: str
    club: Optional[str]
    class_name: str
    run_number: int
    run_time: float


# ── Trainees ─────────────────────────────────────────────────────────────────

class TraineeCreate(BaseModel):
    first_name: str
    last_name: str
    birth_year: Optional[int] = None
    license_number: Optional[str] = None
    club_id: Optional[int] = None
    kart_number: Optional[str] = None
    is_active: bool = True
    notes: Optional[str] = None
    discipline_ids: list[int] = []


class TraineeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_year: Optional[int] = None
    license_number: Optional[str] = None
    club_id: Optional[int] = None
    kart_number: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    discipline_ids: Optional[list[int]] = None


class TraineeResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    birth_year: Optional[int]
    license_number: Optional[str]
    club_id: Optional[int]
    club_name: Optional[str] = None   # aus JOIN
    kart_number: Optional[str]
    is_active: bool
    notes: Optional[str]
    created_at: str
    discipline_ids: list[int] = []

    model_config = {"from_attributes": True}


# ── Disciplines ───────────────────────────────────────────────────────────────

class DisciplineCreate(BaseModel):
    name: str
    sort_order: int = 0
    is_active: bool = True


class DisciplineUpdate(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class DisciplineResponse(BaseModel):
    id: int
    name: str
    sort_order: int
    is_active: bool

    model_config = {"from_attributes": True}


# ── TrainingSessions ─────────────────────────────────────────────────────────

class TrainingSessionCreate(BaseModel):
    name: str
    date: str  # ISO-8601 "YYYY-MM-DD"
    status: Literal["planned", "active", "finished"] = "planned"
    discipline_id: Optional[int] = None
    notes: Optional[str] = None


class TrainingSessionUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[str] = None
    status: Optional[Literal["planned", "active", "finished"]] = None
    discipline_id: Optional[int] = None
    notes: Optional[str] = None


class TrainingSessionResponse(TrainingSessionCreate):
    id: int
    created_by: Optional[int]
    created_at: str
    discipline_name: Optional[str] = None  # aus JOIN mit Disciplines

    model_config = {"from_attributes": True}


# ── TrainingRuns ──────────────────────────────────────────────────────────────

class TrainingRunCreate(BaseModel):
    trainee_id: int
    kart_number: Optional[str] = None
    raw_time: Optional[float] = None
    penalty_seconds: float = 0.0
    status: Literal["valid", "dns", "dnf", "dsq"] = "valid"
    source: Literal["manual", "lichtschranke"] = "manual"


class TrainingRunUpdate(BaseModel):
    kart_number: Optional[str] = None
    raw_time: Optional[float] = None
    penalty_seconds: Optional[float] = None
    status: Optional[Literal["valid", "dns", "dnf", "dsq"]] = None


class TrainingRunResponse(BaseModel):
    id: int
    session_id: int
    trainee_id: int
    first_name: str
    last_name: str
    club_name: Optional[str] = None
    kart_number: Optional[str]
    run_number: int
    raw_time: Optional[float]
    penalty_seconds: float
    total_time: Optional[float]
    status: str
    source: str
    created_at: str

    model_config = {"from_attributes": True}


class TrainingStandingRow(BaseModel):
    session_id: int
    trainee_id: int
    first_name: str
    last_name: str
    club_name: Optional[str]
    run_count: int
    best_time: Optional[float]
    avg_time: Optional[float]
    rank: int

    model_config = {"from_attributes": True}


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── View responses ────────────────────────────────────────────────────────────

class RunResultView(BaseModel):
    result_id: int
    event_id: int
    class_id: int
    class_name: str
    run_number: int
    participant_id: int
    start_number: int
    first_name: str
    last_name: str
    club: Optional[str]
    raw_time: Optional[float]
    status: str
    is_official: bool
    total_penalties: float
    total_time: Optional[float]

    model_config = {"from_attributes": True}


class StandingRow(BaseModel):
    event_id: int
    class_id: int
    class_name: str
    start_number: int
    first_name: str
    last_name: str
    club: Optional[str]
    valid_runs: int
    total_time: Optional[float]
    rank: int

    model_config = {"from_attributes": True}
