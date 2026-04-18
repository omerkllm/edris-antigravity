from __future__ import annotations

from datetime import date, timedelta

from app.models.schemas import OpportunityObject, StudentProfile
from app.services.scoring import score_all


def _profile(*, cgpa: float = 3.3, preferred: list[str] | None = None) -> StudentProfile:
    return StudentProfile(
        name=None,
        degree="BS Computer Science",
        degree_level="undergraduate",
        semester=6,
        cgpa=cgpa,
        skills=["Python", "React"],
        preferred_types=preferred or ["scholarship", "internship"],
        financial_need=True,
        location_preference="any",
        past_experience=None,
    )


def _opp(**kwargs) -> OpportunityObject:
    base = dict(
        email_id="email_001",
        title="Opp",
        organization="Org",
        category="scholarship",
        deadline_raw="",
        deadline_iso=None,
        deadline_type="missing",
        degree_levels=["undergraduate"],
        min_cgpa=None,
        skills_required=[],
        location_type="remote",
        financial_need_required=False,
        year_of_study=[],
        required_documents=[],
        compensation=None,
        duration=None,
        application_link=None,
        contact_email=None,
        eligibility_raw="",
        deadline_raw_context="",
        extraction_incomplete=False,
    )
    base.update(kwargs)
    return OpportunityObject(**base)


def test_borderline_cgpa_marks_ineligible_and_partial():
    p = _profile(cgpa=2.8)
    opp = _opp(min_cgpa=3.0)
    scored = score_all([opp], p, date.today())
    assert scored[0].is_ineligible is True
    assert scored[0].profile_fit >= 25  # 5 (cgpa) + 10 + 8 + 10/5


def test_expired_deadline_badge_and_urgency_zero():
    today = date.today()
    opp = _opp(deadline_iso=(today - timedelta(days=1)).isoformat(), deadline_type="explicit")
    scored = score_all([opp], _profile(), today)
    assert scored[0].urgency_badge == "EXPIRED"
    assert scored[0].urgency_score == 0


def test_rolling_deadline_bucket():
    scored = score_all([_opp(deadline_type="rolling")], _profile(), date.today())
    assert scored[0].urgency_badge == "ROLLING"
    assert scored[0].urgency_score == 8


def test_tie_breaker_days_left_then_title():
    today = date.today()
    a = _opp(email_id="email_001", title="B", deadline_iso=(today + timedelta(days=5)).isoformat(), deadline_type="explicit")
    b = _opp(email_id="email_002", title="A", deadline_iso=(today + timedelta(days=10)).isoformat(), deadline_type="explicit")
    scored = score_all([b, a], _profile(), today)
    assert scored[0].opportunity.email_id == "email_001"

