from __future__ import annotations

import json
import logging
from datetime import date

from app.models.schemas import OpportunityObject, RawEmail
from app.services.ai_client import AIClient


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You extract structured opportunity fields from emails.
Return ONLY JSON: an array of objects, one per email, matching OpportunityObject fields.
All fields must be present. Use null/empty lists as appropriate.
deadline_iso must be YYYY-MM-DD or null. deadline_type must be explicit|inferred|rolling|missing.
location_type must be remote|pakistan_only|international|unknown.
year_of_study must be an array of integers (semester numbers) or [].
"""


def _validate_application_link(link: str | None, raw_text: str) -> str | None:
    if not link:
        return None
    return link if link in raw_text else None


def _convert_pct_cgpa(min_cgpa: float | None) -> float | None:
    if min_cgpa is None:
        return None
    # Heuristic: if model extracted percent (e.g., 70) rather than 4.0-scale.
    if min_cgpa > 4.0 and min_cgpa <= 100.0:
        return (min_cgpa / 100.0) * 4.0
    return min_cgpa


def _fallback_object(email: RawEmail, category: str) -> OpportunityObject:
    return OpportunityObject(
        email_id=email.id,
        title=email.subject,
        organization=None,
        category=category,
        deadline_raw=None,
        deadline_iso=None,
        deadline_type="missing",
        degree_levels=[],
        min_cgpa=None,
        skills_required=[],
        location_type="unknown",
        financial_need_required=False,
        year_of_study=[],
        required_documents=[],
        compensation=None,
        duration=None,
        application_link=None,
        contact_email=None,
        eligibility_raw="",
        deadline_raw_context="",
        extraction_incomplete=True,
    )


async def extract(
    opportunities: list[tuple[RawEmail, str]],
    raw_emails_map: dict[str, RawEmail],
    client: AIClient,
    *,
    today: date,
) -> list[OpportunityObject]:
    if not opportunities:
        return []

    payload = []
    for email, category in opportunities:
        payload.append(
            {
                "email_id": email.id,
                "subject": email.subject,
                "sender": email.sender,
                "category": category,
                "body": email.body,
            }
        )

    user_prompt = (
        f"Today's date is {today.isoformat()}.\n"
        "Extract opportunities from these emails. Return JSON only.\n\n"
        + json.dumps(payload, ensure_ascii=False)
    )

    try:
        raw = await client.call(SYSTEM_PROMPT, user_prompt)
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Extractor returned malformed JSON; using fallback extraction")
        return [_fallback_object(email, category) for email, category in opportunities]
    except Exception:
        logger.warning("Extractor call failed; using fallback extraction", exc_info=True)
        return [_fallback_object(email, category) for email, category in opportunities]

    data_by_email_id: dict[str, dict] = {}
    if isinstance(parsed, list):
        for item in parsed:
            if not isinstance(item, dict):
                continue
            email_id = item.get("email_id")
            if isinstance(email_id, str) and email_id not in data_by_email_id:
                data_by_email_id[email_id] = item

    out: list[OpportunityObject] = []
    for email, category in opportunities:
        item = data_by_email_id.get(email.id)
        if not item:
            out.append(_fallback_object(email, category))
            continue

        try:
            obj = OpportunityObject.model_validate(item)
        except Exception:
            out.append(_fallback_object(email, category))
            continue

        raw_email = raw_emails_map.get(obj.email_id)
        if raw_email:
            obj.application_link = _validate_application_link(
                obj.application_link, raw_email.raw_text
            )
        if not obj.title:
            obj.title = email.subject
        if not obj.category:
            obj.category = category
        obj.min_cgpa = _convert_pct_cgpa(obj.min_cgpa)
        out.append(obj)

    return out

