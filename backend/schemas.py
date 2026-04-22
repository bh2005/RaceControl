from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal, Optional


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
    reglement_id: int
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


class EventUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[str] = None
    location: Optional[str] = None
    reglement_id: Optional[int] = None
    status: Optional[Literal["planned", "active", "finished", "official"]] = None


class EventResponse(EventCreate):
    id: int
    created_at: str

    model_config = {"from_attributes": True}


# ── Classes ───────────────────────────────────────────────────────────────────

class ClassCreate(BaseModel):
    event_id: int
    reglement_id: Optional[int] = None
    name: str
    short_name: Optional[str] = None
    min_birth_year: Optional[int] = None
    max_birth_year: Optional[int] = None
    run_status: Literal["planned", "running", "preliminary", "official"] = "planned"
    start_order: int = 0


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    min_birth_year: Optional[int] = None
    max_birth_year: Optional[int] = None
    run_status: Optional[Literal["planned", "running", "preliminary", "official"]] = None
    start_order: Optional[int] = None
    reglement_id: Optional[int] = None


class ClassResponse(ClassCreate):
    id: int

    model_config = {"from_attributes": True}


# ── Participants ──────────────────────────────────────────────────────────────

class ParticipantCreate(BaseModel):
    event_id: int
    class_id: Optional[int] = None
    start_number: int
    first_name: str
    last_name: str
    birth_year: Optional[int] = None
    club: Optional[str] = None
    license_number: Optional[str] = None
    status: Literal["registered", "checked_in", "technical_ok", "disqualified"] = "registered"


class ParticipantUpdate(BaseModel):
    class_id: Optional[int] = None
    start_number: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_year: Optional[int] = None
    club: Optional[str] = None
    license_number: Optional[str] = None
    status: Optional[Literal["registered", "checked_in", "technical_ok", "disqualified"]] = None


class ParticipantResponse(ParticipantCreate):
    id: int

    model_config = {"from_attributes": True}


# ── RaceResults ───────────────────────────────────────────────────────────────

class RaceResultCreate(BaseModel):
    event_id: int
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
    result_id: int
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
    role: Literal["admin", "schiedsrichter", "nennung", "zeitnahme", "viewer"]
    display_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    display_name: Optional[str]
    is_active: bool
    created_at: str

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
