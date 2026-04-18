from __future__ import annotations

import json
import logging

from app.models.schemas import ClassificationResult, FilteredOut, RawEmail
from app.services.ai_client import AIClient


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a strict email classifier.
Return ONLY JSON: an array of objects, one per email, matching this schema:
{ "id": string, "is_opportunity": boolean, "category": string, "confidence": number, "reject_reason": string|null }

category must be one of: scholarship, internship, competition, fellowship, admission, conference, grant, job, other, not_opportunity.
If is_opportunity is false, category must be "not_opportunity" and reject_reason must be non-empty.
"""


async def classify(
    emails: list[RawEmail], client: AIClient
) -> tuple[list[tuple[RawEmail, ClassificationResult]], list[FilteredOut]]:
    if not emails:
        return [], []

    payload = [{"id": e.id, "subject": e.subject, "sender": e.sender, "body": e.body} for e in emails]
    user_prompt = (
        "Classify these emails. Treat forwarded opportunity emails as opportunities. "
        "Return JSON only.\n\nEmails:\n"
        + json.dumps(payload, ensure_ascii=False)
    )

    try:
        raw = await client.call(SYSTEM_PROMPT, user_prompt)
        data = json.loads(raw)
        results = [ClassificationResult.model_validate(item) for item in data]
    except json.JSONDecodeError:
        logger.warning("Classifier returned malformed JSON; applying conservative fallback")
        # Conservative fallback: treat all as opportunities.
        results = [
            ClassificationResult(
                id=e.id,
                is_opportunity=True,
                category="other",
                confidence=0.5,
                reject_reason=None,
            )
            for e in emails
        ]
    except Exception:
        logger.warning("Classifier call failed; applying conservative fallback", exc_info=True)
        # Conservative fallback: treat all as opportunities
        results = [
            ClassificationResult(
                id=e.id,
                is_opportunity=True,
                category="other",
                confidence=0.5,
                reject_reason=None,
            )
            for e in emails
        ]

    by_id = {r.id: r for r in results}
    opportunities: list[tuple[RawEmail, ClassificationResult]] = []
    filtered_out: list[FilteredOut] = []

    for e in emails:
        r = by_id.get(e.id)
        if not r:
            r = ClassificationResult(
                id=e.id,
                is_opportunity=True,
                category="other",
                confidence=0.5,
                reject_reason=None,
            )
        if r.is_opportunity:
            opportunities.append((e, r))
        else:
            filtered_out.append(
                FilteredOut(
                    email_id=e.id,
                    subject=e.subject,
                    sender=e.sender,
                    reject_reason=r.reject_reason or "Not an opportunity",
                )
            )

    return opportunities, filtered_out

