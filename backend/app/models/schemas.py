from __future__ import annotations

from typing import Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field


OpportunityType = Literal[
    "scholarship",
    "internship",
    "competition",
    "fellowship",
    "admission",
    "conference",
    "grant",
    "job",
]


class RawEmail(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    subject: str
    sender: str
    body: str
    raw_text: str
    source: Literal["paste", "file"]
    char_count: int = Field(ge=0)


class StudentProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    name: str | None = None
    degree: str
    degree_level: Literal["undergraduate", "graduate", "phd"]
    semester: int = Field(ge=1, le=8)
    cgpa: float = Field(ge=0.0, le=4.0)
    skills: list[str] = Field(default_factory=list)
    preferred_types: list[OpportunityType] = Field(default_factory=list)
    financial_need: bool
    location_preference: Literal["remote", "pakistan", "any"]
    past_experience: str | None = None


class ClassificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    is_opportunity: bool
    category: Literal[
        "scholarship",
        "internship",
        "competition",
        "fellowship",
        "admission",
        "conference",
        "grant",
        "job",
        "other",
        "not_opportunity",
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    reject_reason: str | None = None


class OpportunityObject(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    email_id: str
    title: str | None = None
    organization: str | None = None
    category: str | None = None
    deadline_raw: str | None = None
    deadline_iso: str | None = None
    deadline_type: Literal["explicit", "inferred", "rolling", "missing"]
    degree_levels: list[Literal["undergraduate", "graduate", "phd", "any"]] = Field(
        default_factory=list
    )
    min_cgpa: float | None = None
    skills_required: list[str] = Field(default_factory=list)
    location_type: Literal["remote", "pakistan_only", "international", "unknown"]
    financial_need_required: bool = False
    year_of_study: list[int] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    compensation: str | None = None
    duration: str | None = None
    application_link: str | None = None
    contact_email: str | None = None
    eligibility_raw: str
    deadline_raw_context: str
    extraction_incomplete: bool = False


class ScoredOpportunity(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    opportunity: OpportunityObject
    total_score: int = Field(ge=0, le=100)
    profile_fit: int = Field(ge=0, le=40)
    urgency_score: int = Field(ge=0, le=30)
    completeness_score: int = Field(ge=0, le=20)
    value_score: int = Field(ge=0, le=10)
    evidence: list[str] = Field(default_factory=list)
    urgency_badge: Literal[
        "RED",
        "YELLOW",
        "GREEN",
        "ROLLING",
        "NO_DEADLINE",
        "EXPIRED",
    ]
    is_ineligible: bool
    days_left: int | None = None
    classification_uncertain: bool = False


class RankedOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    rank: int = Field(ge=1)
    opportunity: OpportunityObject
    total_score: int = Field(ge=0, le=100)
    score_breakdown: dict[str, int]
    evidence: list[str] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)
    urgency_badge: str
    is_ineligible: bool
    days_left: int | None = None
    classification_uncertain: bool


class FilteredOut(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    email_id: str
    subject: str
    sender: str
    reject_reason: str


class FinalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    ranked_opportunities: list[RankedOutput] = Field(default_factory=list)
    filtered_out: list[FilteredOut] = Field(default_factory=list)
    total_emails_input: int = Field(ge=0)
    opportunities_found: int = Field(ge=0)
    processing_time_ms: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)

