from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.models.schemas import OpportunityObject, ScoredOpportunity, StudentProfile


VALUE_MAP: dict[str, int] = {
    "scholarship": 10,
    "fellowship": 10,
    "internship": 8,
    "job": 8,
    "grant": 7,
    "competition": 6,
    "admission": 6,
    "conference": 4,
    "other": 4,
}


@dataclass(frozen=True)
class ScoreParts:
    profile_fit: int
    urgency: int
    completeness: int
    value: int

    @property
    def total(self) -> int:
        return self.profile_fit + self.urgency + self.completeness + self.value


def _parse_deadline_iso(deadline_iso: str | None) -> date | None:
    if not deadline_iso:
        return None
    try:
        return datetime.strptime(deadline_iso, "%Y-%m-%d").date()
    except ValueError:
        return None


def _days_left(today: date, deadline: date | None) -> int | None:
    if not deadline:
        return None
    return (deadline - today).days


def _urgency_badge(deadline_type: str, days_left: int | None) -> str:
    if deadline_type == "rolling":
        return "ROLLING"
    if deadline_type == "missing" or days_left is None:
        return "NO_DEADLINE"
    if days_left < 0:
        return "EXPIRED"
    if days_left <= 7:
        return "RED"
    if days_left <= 30:
        return "YELLOW"
    return "GREEN"


def score_profile_fit(opp: OpportunityObject, profile: StudentProfile) -> tuple[int, list[str], bool]:
    evidence: list[str] = []

    # CGPA (0..10)
    cgpa_score = 10
    is_ineligible = False
    if opp.min_cgpa is not None:
        if profile.cgpa >= opp.min_cgpa:
            cgpa_score = 10
            evidence.append(f"CGPA eligible: your {profile.cgpa:.1f} meets the {opp.min_cgpa:.1f} minimum")
        elif profile.cgpa >= opp.min_cgpa - 0.2:
            cgpa_score = 5
            is_ineligible = True
            evidence.append("CGPA borderline: you are within 0.2 of the requirement")
        else:
            cgpa_score = 0
            is_ineligible = True
            evidence.append(f"Below CGPA requirement: {profile.cgpa:.1f} < {opp.min_cgpa:.1f}")

    # Degree level (0..10)
    degree_score = 10
    if opp.degree_levels and "any" not in opp.degree_levels:
        degree_score = 10 if profile.degree_level in opp.degree_levels else 0

    # Skills (0..10)
    if not opp.skills_required:
        skills_score = 8
    else:
        required = {s.lower() for s in opp.skills_required}
        have = {s.lower() for s in profile.skills}
        matched = len(required & have)
        skills_score = round((matched / max(1, len(required))) * 10)

    # Type preference (0..10)
    if opp.category and opp.category in profile.preferred_types:
        type_score = 10
    else:
        type_score = 5

    score = cgpa_score + degree_score + skills_score + type_score
    return score, evidence, is_ineligible


def score_urgency(opp: OpportunityObject, today: date) -> tuple[int, str, int | None, list[str]]:
    deadline = _parse_deadline_iso(opp.deadline_iso)
    days = _days_left(today, deadline)
    badge = _urgency_badge(opp.deadline_type, days)
    evidence: list[str] = []

    if opp.deadline_type == "rolling":
        return 8, badge, days, ["Rolling admissions: urgency bucket applied"]
    if opp.deadline_type == "missing" or days is None:
        return 5, badge, days, ["No deadline found: default urgency applied"]
    if days < 0:
        return 0, badge, days, ["Deadline has passed"]
    if days <= 7:
        return 30, badge, days, [f"Deadline soon: {days} days left"]
    if days <= 14:
        return 25, badge, days, [f"Deadline: {days} days left"]
    if days <= 30:
        return 20, badge, days, [f"Deadline: {days} days left"]
    if days <= 60:
        return 12, badge, days, [f"Deadline: {days} days left"]
    return 6, badge, days, [f"Deadline: {days} days left"]


def score_completeness(opp: OpportunityObject) -> tuple[int, list[str]]:
    score = 0
    evidence: list[str] = []
    if opp.application_link:
        score += 5
    if opp.deadline_iso:
        score += 5
    if opp.required_documents:
        score += 5
    if opp.contact_email or opp.compensation:
        score += 5
    if score >= 15:
        evidence.append("High completeness: key fields present")
    return score, evidence


def score_value(opp: OpportunityObject) -> tuple[int, list[str]]:
    if not opp.category:
        return 4, []
    return VALUE_MAP.get(opp.category, 4), []


def score_all(
    opportunities: list[OpportunityObject], profile: StudentProfile, today: date
) -> list[ScoredOpportunity]:
    scored: list[ScoredOpportunity] = []
    for opp in opportunities:
        pf, pf_ev, ineligible = score_profile_fit(opp, profile)
        urg, badge, days, urg_ev = score_urgency(opp, today)
        comp, comp_ev = score_completeness(opp)
        val, val_ev = score_value(opp)

        evidence = []
        evidence.extend(pf_ev[:2])
        evidence.extend(urg_ev[:2])
        if comp_ev:
            evidence.extend(comp_ev[:1])
        evidence.extend(val_ev[:1])

        parts = ScoreParts(profile_fit=pf, urgency=urg, completeness=comp, value=val)
        scored.append(
            ScoredOpportunity(
                opportunity=opp,
                total_score=parts.total,
                profile_fit=pf,
                urgency_score=urg,
                completeness_score=comp,
                value_score=val,
                evidence=evidence,
                urgency_badge=badge,  # type: ignore[arg-type]
                is_ineligible=ineligible,
                days_left=days,
            )
        )

    return sorted(
        scored,
        key=lambda x: (
            x.is_ineligible,
            -(x.total_score),
            (x.days_left if x.days_left is not None else 9999),
            (x.opportunity.title or ""),
        ),
    )

