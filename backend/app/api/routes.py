from __future__ import annotations

import os
import time
from datetime import date

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.schemas import FinalResponse, StudentProfile
from app.services.ai_client import AIClient
from app.services.checklist import generate_checklists, to_ranked_output
from app.services.classifier import classify
from app.services.extractor import extract
from app.services.ingestion import parse_emails
from app.services.scoring import score_all


router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@router.post("/analyze")
async def analyze(
    profile: str = Form(...),
    pasted_text: str | None = Form(None),
    files: list[UploadFile] | None = File(None),
):
    if (not pasted_text or not pasted_text.strip()) and not files:
        raise HTTPException(
            status_code=400,
            detail="Either pasted_text or files must be provided",
        )

    try:
        student = StudentProfile.model_validate_json(profile)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid profile JSON")

    max_emails = int(os.getenv("MAX_EMAILS") or "15")
    max_body_chars = int(os.getenv("MAX_BODY_CHARS") or "3000")

    file_blobs: list[tuple[str, str, bytes]] = []
    if files:
        for f in files:
            content = await f.read()
            if len(content) > 500 * 1024:
                raise HTTPException(status_code=413, detail="File too large (max 500KB)")
            filename = f.filename or "upload"
            lower = filename.lower()
            if not (lower.endswith(".txt") or lower.endswith(".eml")):
                raise HTTPException(status_code=400, detail="Only .txt and .eml files are supported")
            ctype = (f.content_type or "").lower()
            if lower.endswith(".txt") and ctype and ctype != "text/plain":
                raise HTTPException(status_code=400, detail="Invalid MIME type for .txt file")
            if lower.endswith(".eml") and ctype and ctype != "message/rfc822":
                raise HTTPException(status_code=400, detail="Invalid MIME type for .eml file")
            file_blobs.append((filename, f.content_type or "", content))

    started = time.perf_counter()
    raw_emails, pre_filtered, warnings = parse_emails(
        pasted_text,
        file_blobs,
        max_emails=max_emails,
        max_body_chars=max_body_chars,
    )
    raw_map = {e.id: e for e in raw_emails}

    client = AIClient.from_env()
    opp_pairs, filtered = await classify(raw_emails, client)
    uncertain_ids = {email.id for email, result in opp_pairs if result.confidence < 0.6}
    # Extract only opportunities
    opp_for_extract = [(e, r.category) for (e, r) in opp_pairs]
    opp_objs = await extract(
        opp_for_extract,
        raw_map,
        client,
        today=date.today(),
    )

    scored = score_all(opp_objs, student, date.today())
    for item in scored:
        item.classification_uncertain = item.opportunity.email_id in uncertain_ids

    checklists = await generate_checklists(scored, client)
    ranked = to_ranked_output(scored, checklists)

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return FinalResponse(
        ranked_opportunities=ranked,
        filtered_out=pre_filtered + filtered,
        total_emails_input=len(raw_emails),
        opportunities_found=len(opp_objs),
        processing_time_ms=elapsed_ms,
        warnings=warnings,
    )


@router.get("/demo")
def demo_stub():
    raise HTTPException(status_code=501, detail="Not implemented yet")

