from __future__ import annotations

import asyncio
from datetime import date

from app.models.schemas import OpportunityObject, RawEmail, ScoredOpportunity
from app.services.checklist import generate_checklists
from app.services.classifier import classify
from app.services.extractor import extract


class FakeClient:
    def __init__(self, result: str | Exception):
        self._result = result

    async def call(self, _system_prompt: str, _user_prompt: str) -> str:
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


def _raw_email(email_id: str) -> RawEmail:
    return RawEmail(
        id=email_id,
        subject="Test Subject",
        sender="sender@example.com",
        body="This is a sufficiently long email body about an opportunity.",
        raw_text="Apply here: https://example.com/apply",
        source="paste",
        char_count=64,
    )


def _scored(email_id: str) -> ScoredOpportunity:
    opp = OpportunityObject(
        email_id=email_id,
        title="Opportunity",
        organization="Org",
        category="internship",
        deadline_raw=None,
        deadline_iso=None,
        deadline_type="missing",
        degree_levels=[],
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
    return ScoredOpportunity(
        opportunity=opp,
        total_score=50,
        profile_fit=20,
        urgency_score=5,
        completeness_score=15,
        value_score=10,
        evidence=["evidence"],
        urgency_badge="NO_DEADLINE",
        is_ineligible=False,
        days_left=None,
        classification_uncertain=False,
    )


def test_classification_json_failure_falls_back_to_all_opportunities():
    emails = [_raw_email("email_001"), _raw_email("email_002")]
    opportunities, filtered = asyncio.run(classify(emails, FakeClient("{")))

    assert len(opportunities) == 2
    assert filtered == []
    assert all(result.confidence == 0.5 for _, result in opportunities)
    assert all(result.is_opportunity for _, result in opportunities)


def test_extraction_parse_failure_preserves_email_with_incomplete_flag():
    email = _raw_email("email_001")
    opportunities = [(email, "scholarship")]
    extracted = asyncio.run(
        extract(
            opportunities,
            {email.id: email},
            FakeClient('[{"email_id":"email_001"}]'),
            today=date.today(),
        )
    )

    assert len(extracted) == 1
    assert extracted[0].email_id == "email_001"
    assert extracted[0].title == "Test Subject"
    assert extracted[0].extraction_incomplete is True


def test_checklist_failure_uses_deterministic_fallback():
    scored = [_scored("email_001")]
    out = asyncio.run(generate_checklists(scored, FakeClient(RuntimeError("boom"))))

    assert "email_001" in out
    assert out["email_001"]
