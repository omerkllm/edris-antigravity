# API Contract: AI Opportunity Inbox Copilot

**Version**: 1.0 | **Date**: 2026-04-18 | **Base URL**: `http://localhost:8000`

---

## Endpoints

### `POST /api/analyze`

Processes a batch of emails against a student profile and returns ranked opportunities.

**Request**: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pasted_text` | `string` | ✗ (one of pasted_text/files required) | Emails separated by `---EMAIL---` |
| `files` | `File[]` | ✗ (one of pasted_text/files required) | `.txt` or `.eml` files, max 15 |
| `profile` | `string` (JSON-encoded) | ✓ | JSON-serialized `StudentProfile` object |

**Validation errors (HTTP 400)**:
- Neither `pasted_text` nor `files` provided
- `profile` JSON is malformed or fails Pydantic validation
- `profile.cgpa` outside 0.0–4.0
- `profile.semester` outside 1–8

**Success response (HTTP 200)**: `FinalResponse` JSON object

```json
{
  "ranked_opportunities": [
    {
      "rank": 1,
      "opportunity": {
        "email_id": "email_001",
        "title": "HEC Need-Based Scholarship 2026",
        "organization": "Higher Education Commission Pakistan",
        "category": "scholarship",
        "deadline_raw": "May 20, 2026",
        "deadline_iso": "2026-05-20",
        "deadline_type": "explicit",
        "degree_levels": ["undergraduate"],
        "min_cgpa": 2.8,
        "skills_required": [],
        "location_type": "pakistan_only",
        "financial_need_required": true,
        "year_of_study": [1, 2, 3, 4, 5, 6],
        "required_documents": ["CNIC copy", "Official Transcript", "Bank statement"],
        "compensation": null,
        "duration": null,
        "application_link": "https://eportal.hec.gov.pk/scholarship",
        "contact_email": "scholarships@hec.gov.pk",
        "eligibility_raw": "Minimum CGPA: 2.8. Must demonstrate financial need.",
        "deadline_raw_context": "Deadline: May 20, 2026"
      },
      "total_score": 83,
      "score_breakdown": {
        "profile_fit": 33,
        "urgency": 20,
        "completeness": 20,
        "value": 10
      },
      "evidence": [
        "CGPA eligible: your 3.3 meets the 2.8 minimum",
        "Financial need requirement matches your profile",
        "Deadline: May 20, 2026 (32 days from today)"
      ],
      "checklist": [
        "Collect income certificate and bank statement from family now",
        "Request official transcript from your university registrar",
        "Apply at eportal.hec.gov.pk/scholarship before May 20"
      ],
      "urgency_badge": "YELLOW",
      "is_ineligible": false,
      "days_left": 32,
      "classification_uncertain": false
    }
  ],
  "filtered_out": [
    {
      "email_id": "email_002",
      "subject": "50% off pizza tonight only!",
      "sender": "noreply@deals.com",
      "reject_reason": "Promotional discount email, not an academic opportunity"
    }
  ],
  "total_emails_input": 3,
  "opportunities_found": 2,
  "processing_time_ms": 4823,
  "warnings": []
}
```

---

### `GET /api/demo`

Returns pre-computed ranked results for 5 curated demo emails. No AI calls made.

**Response (HTTP 200)**: Same `FinalResponse` shape as `/api/analyze`

**Response (HTTP 404)**: If `backend/app/data/demo_response.json` is missing.

```json
{ "detail": "Demo data not found. Run: python -m app.scripts.generate_demo" }
```

---

### `GET /api/health`

Simple liveness check.

**Response (HTTP 200)**:
```json
{ "status": "ok", "version": "1.0.0" }
```

---

## `StudentProfile` JSON Schema

```json
{
  "name": "Ali Khan",
  "degree": "BS Computer Science",
  "degree_level": "undergraduate",
  "semester": 6,
  "cgpa": 3.3,
  "skills": ["Python", "Machine Learning", "React"],
  "preferred_types": ["internship", "competition"],
  "financial_need": true,
  "location_preference": "any",
  "past_experience": "ICPC 2025 participant, Web dev internship"
}
```

**Field constraints**:

| Field | Type | Allowed Values / Range |
|-------|------|------------------------|
| `degree_level` | enum string | `"undergraduate"`, `"graduate"`, `"phd"` |
| `semester` | integer | 1–8 (inclusive) |
| `cgpa` | float | 0.0–4.0 (inclusive) |
| `preferred_types` | array of enum | `["scholarship","internship","competition","fellowship","admission","conference","grant","job"]` |
| `location_preference` | enum string | `"remote"`, `"pakistan"`, `"any"` |

---

## Error Response Shape

All 4xx/5xx errors use:
```json
{
  "detail": "Human-readable error message"
}
```

---

## Frontend → Backend Communication

The React frontend communicates exclusively via:

1. **Analyze flow**: `fetch("http://localhost:8000/api/analyze", { method: "POST", body: formData })`
2. **Demo flow**: `fetch("http://localhost:8000/api/demo")`
3. **Health check**: `fetch("http://localhost:8000/api/health")`

The Vite config proxies `/api` → `http://localhost:8000` in development, so the React code can use `/api/analyze` (relative) without CORS issues.

---

## LLM Internal Prompt Contracts

These are the JSON schemas that the AI calls MUST conform to. The backend validates responses against these schemas with Pydantic.

### Classification Response Schema (per email)

```json
{
  "id": "email_001",
  "is_opportunity": true,
  "category": "scholarship",
  "confidence": 0.97,
  "reject_reason": null
}
```

### Extraction Response Schema (per opportunity)

See `OpportunityObject` in `data-model.md` — all fields must be present (null for optional missing fields).

### Checklist Response Schema (per opportunity)

```json
{
  "id": "email_001",
  "checklist": [
    "Action step 1 (max 12 words)",
    "Action step 2 (max 12 words)",
    "Action step 3 (optional, max 12 words)"
  ]
}
```
