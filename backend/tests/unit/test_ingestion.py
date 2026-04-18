from __future__ import annotations

from app.services.ingestion import parse_emails


def test_split_delimiter_into_multiple_emails():
    pasted = "Hello one" + ("x" * 40) + "\n---EMAIL---\n" + "Hello two" + ("y" * 40)
    emails, filtered, warnings = parse_emails(
        pasted, None, max_emails=15, max_body_chars=3000
    )
    assert len(emails) == 2
    assert filtered == []
    assert warnings == []


def test_no_delimiter_treated_as_single_email():
    pasted = "Single email body" + ("x" * 40)
    emails, filtered, warnings = parse_emails(
        pasted, None, max_emails=15, max_body_chars=3000
    )
    assert len(emails) == 1
    assert filtered == []
    assert warnings == []


def test_too_short_is_filtered_out():
    pasted = "short\n---EMAIL---\n" + ("x" * 40)
    emails, filtered, _warnings = parse_emails(
        pasted, None, max_emails=15, max_body_chars=3000
    )
    assert len(emails) == 1
    assert len(filtered) == 1
    assert filtered[0].reject_reason == "Skipped: too short"


def test_dedup_by_first_200_chars():
    body = "A" * 250
    pasted = body + "\n---EMAIL---\n" + body + " trailing-diff"
    emails, filtered, warnings = parse_emails(
        pasted, None, max_emails=15, max_body_chars=3000
    )
    assert len(emails) == 1
    assert filtered == []
    assert warnings == []


def test_truncation_warning_when_too_many():
    pasted = "\n---EMAIL---\n".join([("x" * 40) + str(i) for i in range(20)])
    emails, _filtered, warnings = parse_emails(
        pasted, None, max_emails=15, max_body_chars=3000
    )
    assert len(emails) <= 15
    assert warnings
    assert "Input truncated to 15 emails" in warnings[0]


def test_eml_basic_text_plain_extraction():
    eml = (
        b"Subject: Test Subject\r\n"
        b"From: sender@example.com\r\n"
        b"MIME-Version: 1.0\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        + (b"Hello body " + (b"x" * 50))
    )
    emails, filtered, warnings = parse_emails(
        None,
        [("test.eml", "message/rfc822", eml)],
        max_emails=15,
        max_body_chars=3000,
    )
    assert len(emails) == 1
    assert filtered == []
    assert warnings == []
    assert emails[0].subject == "Test Subject"
    assert "sender@example.com" in emails[0].sender

