from __future__ import annotations

import hashlib
import re
from email import policy
from email.parser import BytesParser

from bs4 import BeautifulSoup

from app.models.schemas import FilteredOut, RawEmail


MIN_CHAR_COUNT = 30
MAX_HASH_PREFIX = 200


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _sha256_prefix(text: str) -> str:
    prefix = text[:MAX_HASH_PREFIX].encode("utf-8", errors="ignore")
    return hashlib.sha256(prefix).hexdigest()


def _read_txt(content: bytes) -> str:
    return content.decode("utf-8", errors="ignore")


def _extract_eml_text(content: bytes) -> tuple[str, str | None, str | None]:
    msg = BytesParser(policy=policy.default).parsebytes(content)
    subject = msg.get("subject")
    sender = msg.get("from")

    text_part = msg.get_body(preferencelist=("plain",))
    html_part = msg.get_body(preferencelist=("html",))

    if text_part is not None:
        body = text_part.get_content()
        return body, subject, sender

    if html_part is not None:
        html = html_part.get_content()
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(" "), subject, sender

    # No usable body
    return "", subject, sender


def parse_emails(
    pasted_text: str | None,
    files: list[tuple[str, str, bytes]] | None,
    *,
    max_emails: int,
    max_body_chars: int,
) -> tuple[list[RawEmail], list[FilteredOut], list[str]]:
    """
    files: list of (filename, content_type, bytes)
    """
    warnings: list[str] = []
    candidates: list[tuple[str, str, str, str, str]] = []
    # tuple: (source, subject, sender, body, raw_text)

    if pasted_text:
        parts = [p.strip() for p in pasted_text.split("---EMAIL---")]
        if len(parts) == 1:
            body = parts[0]
            candidates.append(("paste", "No Subject", "Unknown Sender", body, pasted_text))
        else:
            for part in parts:
                if not part:
                    continue
                candidates.append(("paste", "No Subject", "Unknown Sender", part, part))

    if files:
        for filename, _content_type, blob in files:
            if not blob:
                continue
            lower = filename.lower()
            if lower.endswith(".eml"):
                body, subject, sender = _extract_eml_text(blob)
                candidates.append(
                    (
                        "file",
                        subject or "No Subject",
                        sender or "Unknown Sender",
                        body,
                        blob.decode("utf-8", errors="ignore"),
                    )
                )
            else:
                body = _read_txt(blob)
                candidates.append(
                    (
                        "file",
                        "No Subject",
                        "Unknown Sender",
                        body,
                        body,
                    )
                )

    filtered_out: list[FilteredOut] = []
    emails: list[RawEmail] = []
    seen_hashes: set[str] = set()

    if len(candidates) > max_emails:
        warnings.append(
            f"Input truncated to {max_emails} emails — {len(candidates) - max_emails} emails were not processed."
        )
        candidates = candidates[:max_emails]

    for idx, (source, subject, sender, body, raw_text) in enumerate(candidates, start=1):
        normalized_body = _normalize_whitespace(body)[:max_body_chars]
        char_count = len(normalized_body)
        email_id = f"email_{idx:03d}"

        if char_count < MIN_CHAR_COUNT:
            filtered_out.append(
                FilteredOut(
                    email_id=email_id,
                    subject=subject,
                    sender=sender,
                    reject_reason="Skipped: too short",
                )
            )
            continue

        digest = _sha256_prefix(normalized_body)
        if digest in seen_hashes:
            # Deduplicate silently (per spec)
            continue
        seen_hashes.add(digest)

        emails.append(
            RawEmail(
                id=email_id,
                subject=subject,
                sender=sender,
                body=normalized_body,
                raw_text=raw_text,
                source=source,  # type: ignore[arg-type]
                char_count=char_count,
            )
        )

    return emails, filtered_out, warnings

