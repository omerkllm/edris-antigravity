from __future__ import annotations

import json
import logging

from app.models.schemas import RankedOutput, ScoredOpportunity
from app.services.ai_client import AIClient


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You generate concise application checklists for opportunities.
Return ONLY JSON: an array of objects, one per opportunity:
{ "id": string, "checklist": [string, string, string?] }
Each bullet must be <= 12 words and action-oriented.
"""


def fallback_checklist(scored: ScoredOpportunity) -> list[str]:
    opp = scored.opportunity
    bullets: list[str] = []

    if opp.required_documents:
        bullets.append(f"Prepare documents: {', '.join(opp.required_documents[:3])}")
    if opp.application_link:
        bullets.append("Open application link and review requirements")
    if opp.deadline_raw:
        bullets.append(f"Plan submission before: {opp.deadline_raw}")

    if not bullets:
        bullets.append("Review the email and note next steps")
    return bullets[:3]


async def generate_checklists(
    scored: list[ScoredOpportunity], client: AIClient
) -> dict[str, list[str]]:
    if not scored:
        return {}

    payload = [
        {
            "id": s.opportunity.email_id,
            "title": s.opportunity.title,
            "organization": s.opportunity.organization,
            "deadline_raw": s.opportunity.deadline_raw,
            "application_link": s.opportunity.application_link,
            "required_documents": s.opportunity.required_documents,
        }
        for s in scored
    ]

    user_prompt = "Generate checklists for these opportunities. Return JSON only.\n\n" + json.dumps(
        payload, ensure_ascii=False
    )

    try:
        raw = await client.call(SYSTEM_PROMPT, user_prompt)
        data = json.loads(raw)
        if not isinstance(data, list):
            raise ValueError("Checklist response must be a JSON array")

        out: dict[str, list[str]] = {}
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("Checklist item must be an object")
            oid = item.get("id")
            checklist = item.get("checklist")
            if not isinstance(oid, str) or not isinstance(checklist, list):
                raise ValueError("Checklist item missing id/checklist")
            out[oid] = [str(x) for x in checklist if str(x).strip()]

        expected_ids = {entry.opportunity.email_id for entry in scored}
        if set(out.keys()) != expected_ids:
            raise ValueError("Checklist response missing one or more opportunity IDs")
        if any(not bullets for bullets in out.values()):
            raise ValueError("Checklist response contained an empty checklist")

        return out
    except Exception:
        logger.warning("Checklist generation failed; using deterministic fallback", exc_info=True)
        return {s.opportunity.email_id: fallback_checklist(s) for s in scored}


def to_ranked_output(
    scored_sorted: list[ScoredOpportunity], checklists: dict[str, list[str]]
) -> list[RankedOutput]:
    ranked: list[RankedOutput] = []
    for i, s in enumerate(scored_sorted, start=1):
        ranked.append(
            RankedOutput(
                rank=i,
                opportunity=s.opportunity,
                total_score=s.total_score,
                score_breakdown={
                    "profile_fit": s.profile_fit,
                    "urgency": s.urgency_score,
                    "completeness": s.completeness_score,
                    "value": s.value_score,
                },
                evidence=s.evidence,
                checklist=checklists.get(s.opportunity.email_id, fallback_checklist(s)),
                urgency_badge=s.urgency_badge,
                is_ineligible=s.is_ineligible,
                days_left=s.days_left,
                classification_uncertain=s.classification_uncertain,
            )
        )
    return ranked

