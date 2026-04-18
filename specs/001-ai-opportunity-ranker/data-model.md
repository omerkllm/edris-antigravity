# Data Model: AI Opportunity Inbox Copilot

**Date**: 2026-04-18 | **Branch**: `001-ai-opportunity-ranker`

---

## Overview

All data in this system is **in-memory per request**. There is no database. Each POST to `/api/analyze` creates these objects, processes them through the 5-flow pipeline, and returns a `FinalResponse`. Nothing is persisted between requests.

---

## Entity 1: `RawEmail`

The normalized representation of one email, created at ingestion regardless of input method.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | `str` | Sequential: `"email_001"`, `"email_002"` | Assigned at parse time |
| `subject` | `str` | Default: `"No Subject"` if absent | Extracted from `Subject:` header |
| `sender` | `str` | Default: `"Unknown Sender"` if absent | Extracted from `From:` header |
| `body` | `str` | Stripped of excess whitespace | Plain text body |
| `raw_text` | `str` | Original unmodified input | Kept for URL hallucination guard |
| `source` | `Literal["paste", "file"]` | Required | Tracks input method |
| `char_count` | `int` | Computed from `len(body)` | Used for < 30 char filter |

**Validation rules**:
- `char_count < 30` → email is skipped before classification, not included in output
- Deduplication: SHA-256 hash of first 200 chars of `body`; duplicate is dropped silently

---

## Entity 2: `StudentProfile`

Collected via the React form. Validated by Pydantic on the backend.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `name` | `str` | Max 100 chars | Display only — not used in scoring |
| `degree` | `str` | Max 100 chars | e.g., "BS Computer Science" |
| `degree_level` | `Literal["undergraduate", "graduate", "phd"]` | Required | Dropdown selection |
| `semester` | `int` | 1–8 inclusive | Validated: reject outside range |
| `cgpa` | `float` | 0.0–4.0 inclusive | Validated: reject outside range |
| `skills` | `List[str]` | 0–20 items | Tags from multi-select input |
| `preferred_types` | `List[str]` | Subset of category enum | Multi-select checkboxes |
| `financial_need` | `bool` | Required | Toggle input |
| `location_preference` | `Literal["remote", "pakistan", "any"]` | Required | Dropdown |
| `past_experience` | `str` | Max 500 chars, optional | Display context only |

**Preferred types enum values**: `scholarship`, `internship`, `competition`, `fellowship`, `admission`, `conference`, `grant`, `job`

---

## Entity 3: `ClassificationResult`

Output of AI Call #1. One object per input email.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `email_id` | `str` | Matches `RawEmail.id` | Foreign key |
| `is_opportunity` | `bool` | Required | Core classification verdict |
| `category` | `str` | See enum below | Set to `"not_opportunity"` if false |
| `confidence` | `float` | 0.0–1.0 | Used for "(uncertain)" label if < 0.6 |
| `reject_reason` | `Optional[str]` | `null` if `is_opportunity=true` | Shown in filtered-out list |

**Category enum**: `scholarship`, `internship`, `competition`, `fellowship`, `admission`, `conference`, `grant`, `job`, `other`, `not_opportunity`

---

## Entity 4: `OpportunityObject`

Output of AI Call #2. One object per opportunity email that passed classification.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `email_id` | `str` | Matches `RawEmail.id` | Foreign key |
| `title` | `str` | Default: subject line | Human-readable opportunity name |
| `organization` | `str` | Default: sender domain | e.g., "Higher Education Commission" |
| `category` | `str` | Carried from classification | Category enum |
| `deadline_raw` | `str` | Verbatim from email | e.g., "May 20, 2026" or "" |
| `deadline_iso` | `Optional[str]` | `YYYY-MM-DD` or `null` | Parsed date for scoring |
| `deadline_type` | `Literal["explicit", "inferred", "rolling", "missing"]` | Required | Controls urgency scoring |
| `degree_levels` | `List[str]` | Subset of: `["undergraduate", "graduate", "phd", "any"]` | Empty = any |
| `min_cgpa` | `Optional[float]` | 0.0–4.0 or `null` | Null = no requirement |
| `skills_required` | `List[str]` | Hard skills only | Soft skills excluded |
| `location_type` | `Literal["remote", "pakistan_only", "international", "unknown"]` | Required | |
| `financial_need_required` | `bool` | Default: `false` | |
| `year_of_study` | `List[int]` | Semester numbers, or `[]` for any | e.g., `[1,2,3,4,5,6]` |
| `required_documents` | `List[str]` | Default: `[]` | e.g., ["CV", "Transcript"] |
| `compensation` | `Optional[str]` | Verbatim if present | e.g., "Stipend: $3,000 USD" |
| `duration` | `Optional[str]` | Verbatim if present | e.g., "12 weeks" |
| `application_link` | `Optional[str]` | Hallucination-validated | Must exist verbatim in `raw_text` |
| `contact_email` | `Optional[str]` | Email format | |
| `eligibility_raw` | `str` | Verbatim excerpt from email | Used in evidence strings |
| `deadline_raw_context` | `str` | Verbatim sentence with deadline | Used in evidence strings |

---

## Entity 5: `ScoredOpportunity`

Output of the deterministic scoring engine (Flow 4). Zero AI calls.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `opportunity` | `OpportunityObject` | Reference | Full opportunity data |
| `total_score` | `int` | 0–100 | Sum of 4 dimensions |
| `profile_fit` | `int` | 0–40 | Dimension 1 |
| `urgency_score` | `int` | 0–30 | Dimension 2 |
| `completeness_score` | `int` | 0–20 | Dimension 3 |
| `value_score` | `int` | 0–10 | Dimension 4 |
| `evidence` | `List[str]` | 2–6 strings | Deterministic, cites actual values |
| `urgency_badge` | `Literal["RED", "YELLOW", "GREEN", "ROLLING", "NO_DEADLINE", "EXPIRED"]` | Required | |
| `is_ineligible` | `bool` | True if CGPA hard fail | Ineligible sorted below eligible |
| `days_left` | `Optional[int]` | Negative if expired | Used for badge and urgency scoring |

---

## Entity 6: `RankedOutput`

Final unit returned per opportunity in the API response.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `rank` | `int` | 1-indexed, 1 = top priority | |
| `opportunity` | `OpportunityObject` | Reference | |
| `total_score` | `int` | 0–100 | |
| `score_breakdown` | `dict` | Keys: profile_fit, urgency, completeness, value | |
| `evidence` | `List[str]` | Deterministic evidence strings | |
| `checklist` | `List[str]` | 2–3 bullets from AI Call #3 (or fallback) | |
| `urgency_badge` | `str` | Badge label | |
| `is_ineligible` | `bool` | | |
| `days_left` | `Optional[int]` | | |
| `classification_uncertain` | `bool` | True if confidence < 0.6 | Triggers "(uncertain)" label in UI |

---

## Entity 7: `FilteredOut`

One object per email that was rejected by the classifier.

| Field | Type | Notes |
|-------|------|-------|
| `email_id` | `str` | |
| `subject` | `str` | |
| `sender` | `str` | |
| `reject_reason` | `str` | From classifier or "Skipped: too short" |

---

## Entity 8: `FinalResponse`

The single JSON object returned by `POST /api/analyze` and `GET /api/demo`.

| Field | Type | Notes |
|-------|------|-------|
| `ranked_opportunities` | `List[RankedOutput]` | Sorted: eligible by score desc, ineligible last, expired last |
| `filtered_out` | `List[FilteredOut]` | All non-opportunity emails |
| `total_emails_input` | `int` | After truncation to 15 |
| `opportunities_found` | `int` | Count of is_opportunity=true |
| `processing_time_ms` | `int` | Wall-clock time for full pipeline |
| `warnings` | `List[str]` | e.g., "Input truncated to 15 emails" |

---

## Scoring Dimension Breakdown

### Dimension 1: Profile Fit (max 40 pts)

| Sub-score | Max | Logic |
|-----------|-----|-------|
| CGPA Check | 10 | `opp.min_cgpa=None` → 10; `student ≥ min` → 10; `student ≥ min - 0.2` → 5 (borderline); else → 0 |
| Degree/Year Match | 10 | `degree_levels=[]` or `"any"` → 10; `student.degree_level in list` → 10; else → 0 |
| Skills Match | 10 | `skills_required=[]` → 8 (neutral); else `(matched/total) * 10` |
| Type Preference | 10 | `opp.category in student.preferred_types` → 10; else → 5 |

### Dimension 2: Urgency (max 30 pts)

| Days Left | Score |
|-----------|-------|
| `deadline_type="rolling"` | 8 |
| `deadline_type="missing"` | 5 |
| Past deadline (negative) | 0 |
| ≤ 7 days | 30 |
| ≤ 14 days | 25 |
| ≤ 30 days | 20 |
| ≤ 60 days | 12 |
| > 60 days | 6 |

### Dimension 3: Completeness (max 20 pts)

| Field Present | Points |
|---------------|--------|
| `application_link` not null | +5 |
| `deadline_iso` not null | +5 |
| `required_documents` non-empty | +5 |
| `contact_email` not null OR `compensation` not null | +5 |

### Dimension 4: Opportunity Value (max 10 pts)

| Category | Points |
|----------|--------|
| scholarship, fellowship | 10 |
| internship, job | 8 |
| grant | 7 |
| competition, admission | 6 |
| conference, other | 4 |

---

## State Transitions

```
RawEmail[] 
  → [Classification Filter] 
  → opportunities: OpportunityObject[]  +  filtered_out: FilteredOut[]
  → [Scoring Engine]
  → ScoredOpportunity[]
  → [Ranker: sorted by (not is_ineligible, total_score) desc]
  → [Checklist Generator: adds checklist[] to each]
  → RankedOutput[]
  → FinalResponse
```

Emails that fail ingestion pre-checks (< 30 chars, empty, duplicate) are represented in `filtered_out` with reason `"Skipped: {reason}"` and never reach the classifier.
