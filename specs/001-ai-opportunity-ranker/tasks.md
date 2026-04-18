# Tasks: AI Opportunity Inbox Copilot

**Input**: Design documents from `specs/001-ai-opportunity-ranker/`
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/api.md ✅

**Constitution**: One phase at a time. Await explicit "proceed" before next phase. No faulty code.
**Session log**: Consult `context/session_log.md` before each phase.

---

## Phase 1: Setup (Project Structure & Environment)

**Purpose**: Scaffold both projects, install dependencies, wire environment config.
**Await "proceed" before Phase 2.**

- [x] T001 Create directory tree: `backend/app/{api,models,services,data,scripts}/`, `backend/tests/{unit,integration}/`, `frontend/src/{components,pages,services,types}/` per `quickstart.md`
- [x] T002 Create `backend/requirements.txt` with exact pinned versions: fastapi==0.115.0, uvicorn[standard]==0.29.0, python-multipart==0.0.9, pydantic==2.13.0, google-genai==1.0.0, python-dotenv==1.0.0, httpx==0.27.0, python-dateutil==2.9.0, beautifulsoup4==4.12.3
- [x] T003 Create `backend/.env.example` with all env vars: GEMINI_API_KEY, LLM_PROVIDER=gemini, OLLAMA_BASE_URL, OLLAMA_MODEL, ALLOWED_ORIGINS, MAX_EMAILS=15, MAX_BODY_CHARS=3000
- [x] T004 Create `backend/app/main.py` — FastAPI app factory with CORSMiddleware (origins from ALLOWED_ORIGINS env), mount router, lifespan context loading .env via python-dotenv
- [x] T005 [P] Scaffold `frontend/` with `npm create vite@latest frontend -- --template react-ts`, configure `vite.config.ts` proxy `/api → http://localhost:8000`
- [x] T006 [P] Create `frontend/src/index.css` — CSS variables only: color palette, font (system-ui), spacing scale. No non-functional animations or glassmorphism per constitution Principle VIII (a functional loading spinner is allowed later)
- [x] T007 Create root `README.md` with exact commands to run both servers and load demo mode

**CHECKPOINT — Phase 1 complete when:**
- `cd backend && uvicorn app.main:app --reload` starts without import errors
- `cd frontend && npm run dev` opens a blank page at localhost:5173
- `powershell -NoProfile -Command "(Invoke-WebRequest -UseBasicParsing http://localhost:8000/docs).StatusCode"` returns `200`

---

## Phase 2: Foundational (Shared Schemas + AI Client + Rate Limiter)

**Purpose**: Core Pydantic models, AI client wrapper, and rate limiter that every service depends on.
**Await "proceed" before Phase 3.**

- [x] T008 Create `backend/app/models/schemas.py` — all 8 Pydantic models: `RawEmail`, `StudentProfile` (with Field validators for cgpa 0–4, semester 1–8), `ClassificationResult`, `OpportunityObject`, `ScoredOpportunity`, `RankedOutput`, `FilteredOut`, `FinalResponse`. Use `model_config = ConfigDict(strict=True)` where applicable
- [x] T009 Create `backend/app/services/ai_client.py` — `AIClient` class with single `async call(system_prompt, user_prompt) -> str` method. Routes to Gemini (`google-genai` SDK, temperature=0.1, response_mime_type="application/json") or Ollama (`httpx` POST to `/api/chat`, format="json") based on `LLM_PROVIDER` env. Retries once on JSON parse failure with appended instruction. Raises `RuntimeError` after one retry
- [x] T010 Create `backend/app/api/middleware.py` — in-memory sliding-window rate limiter: max 10 requests/minute per client IP. Uses `collections.deque` (O(1) append/popleft). Returns HTTP 429 with `{"detail":"Rate limit exceeded. Try again shortly."}` when exceeded. No third-party rate-limit library
- [x] T011 [P] Create `backend/app/api/routes.py` — register `GET /api/health` (returns version + status), mount rate limiter middleware, import (but do not implement) analyze and demo handlers as stubs that return HTTP 501
- [x] T012 [P] Create `frontend/src/types/models.ts` — TypeScript interfaces mirroring all 8 Pydantic schemas exactly. Use `readonly` on array fields

**CHECKPOINT — Phase 2 complete when:**
- `from app.models.schemas import FinalResponse` imports without error
- `from app.services.ai_client import AIClient` imports without error
- `powershell -NoProfile -Command "Invoke-RestMethod http://localhost:8000/api/health | ConvertTo-Json -Compress"` returns `{\"status\":\"ok\",\"version\":\"1.0.0\"}`
- Rate limiter correctly returns 429 after 10 rapid requests in unit test

---

## Phase 3: User Story 1 — Full Pipeline (Email Batch → Ranked Priority List)

**Goal**: Complete end-to-end flow: ingest emails → classify → extract → score → checklist → ranked JSON.
**Independent Test**: POST `/api/analyze` with 3-email paste (HEC Scholarship + pizza spam + ICPC) and a student profile. Verify pizza is filtered, HEC and ICPC are ranked with scores and evidence.
**Await "proceed" before Phase 4.**

### Implementation — Flow 1: Ingestion

- [x] T013 [US1] Create `backend/app/services/ingestion.py` — `parse_emails(pasted_text, files) -> tuple[list[RawEmail], list[FilteredOut]]`. Split paste on `---EMAIL---`. Read `.eml` files via stdlib `email.parser.BytesParser` with UTF-8 → latin-1 fallback; strip HTML via BeautifulSoup if no `text/plain` part. Read `.txt` files as plain body. Assign sequential IDs `email_001…`. Filter `char_count < MIN_CHAR_COUNT(30)`. Deduplicate via `set` of SHA-256 hashes of first 200 body chars (O(n) single pass). Truncate to `MAX_EMAILS`. Truncate each body to `MAX_BODY_CHARS`

### Implementation — Flow 2: Classification

- [x] T014 [US1] Create `backend/app/services/classifier.py` — `async classify(emails: list[RawEmail], client: AIClient) -> tuple[list[tuple[RawEmail, ClassificationResult]], list[FilteredOut]]`. Builds single batch prompt with all emails. Parses JSON array response; on parse failure all emails pass as `is_opportunity=True` (conservative fallback). Splits into opportunities vs filtered_out

### Implementation — Flow 3: Extraction

- [x] T015 [US1] Create `backend/app/services/extractor.py` — `async extract(opportunities, raw_emails_map: dict[str, RawEmail], client: AIClient) -> list[OpportunityObject]`. Builds single batch prompt with today's date injected. Validates every `application_link` is verbatim substring of `RawEmail.raw_text` (O(n) `in` check); discards if not. Converts percentage CGPA via `(pct/100)*4.0`. On per-email parse failure sets all fields to null/empty with `extraction_incomplete=True`

### Implementation — Flow 4: Scoring Engine

- [x] T016 [US1] Create `backend/app/services/scoring.py` — `score_all(opportunities: list[OpportunityObject], profile: StudentProfile, today: date) -> list[ScoredOpportunity]`. Four pure functions (one per dimension): `score_profile_fit`, `score_urgency`, `score_completeness`, `score_value`. Constants: `VALUE_MAP` dict, `URGENCY_BRACKETS` list of `(days_threshold, points)` tuples. Sort with `sorted(key=lambda x: (x.is_ineligible, -x.total_score, x.days_left or 9999, x.opportunity.title))` — single O(n log n) pass. Deterministic evidence strings built from actual field values — no AI

### Implementation — Flow 5: Checklist Generator

- [x] T017 [US1] Create `backend/app/services/checklist.py` — `async generate_checklists(scored: list[ScoredOpportunity], client: AIClient) -> list[RankedOutput]`. Batch prompt with all ranked opportunities. On any failure returns `fallback_checklist(opp)` which builds steps from `application_link`, `required_documents[:3]`, `deadline_raw`. Attaches rank (1-indexed) and final `classification_uncertain` flag

### Implementation — API Route + Validation

- [x] T018 [US1] Implement `POST /api/analyze` in `backend/app/api/routes.py` — validate `multipart/form-data`: reject if neither `pasted_text` nor `files`; validate file MIME types (text/plain, message/rfc822) and size (max 500 KB each, return 413 if exceeded); parse `profile` JSON field via `StudentProfile.model_validate_json()`; orchestrate flows 1–5 sequentially; measure wall-clock ms; return `FinalResponse`

### Implementation — Unit Tests

- [x] T019 [P] [US1] Write `backend/tests/unit/test_ingestion.py` — test: delimiter split (3 emails), no-delimiter (1 email), < 30 chars skipped, dedup by hash, truncation to MAX_EMAILS, `.eml` UTF-8 and latin-1 fallback, empty file skipped
- [x] T020 [P] [US1] Write `backend/tests/unit/test_scoring.py` — test all 4 scoring dimensions with concrete inputs matching `data-model.md` tables. Test tie-breaker order. Test CGPA borderline (within 0.2 → score 5). Test expired → urgency 0 + EXPIRED badge. Test rolling → score 8

**CHECKPOINT — Phase 3 complete when:**
- `POST /api/analyze` with 3-email paste returns HTTP 200 with pizza filtered out and HEC + ICPC ranked
- `pytest backend/tests/unit/` passes all tests
- HEC Scholarship scores > ICPC in the response (matches data-model.md example: 83 vs 66)
- No `application_link` in response that doesn't appear in the original email text

---

## Phase 4: User Story 2 — Student Profile Form (Structured Input)

**Goal**: React form that collects all StudentProfile fields with client-side validation.
**Independent Test**: Fill form with CGPA=5.0 → see validation error. Fill with valid data → JSON serialized correctly in FormData to backend.
**Await "proceed" before Phase 5.**

- [x] T021 [US2] Create `frontend/src/components/ProfileForm.tsx` — controlled form for all `StudentProfile` fields. Degree level: `<select>`. Semester: `<input type="number" min=1 max=8>`. CGPA: `<input type="number" min=0 max=4 step=0.01>`. Skills: tag-style `<input>` + add button, stored as `string[]`. Preferred types: `<fieldset>` of checkboxes. Financial need: `<input type="checkbox">`. Location: `<select>`. Client-side validation: block submit if CGPA outside 0–4 or semester outside 1–8, show inline error message. No external form library
- [x] T022 [US2] Add `StudentProfile` serialization to `frontend/src/services/api.ts` — `buildFormData(emails: File[], pastedText: string, profile: StudentProfile): FormData`. Appends profile as JSON string to `profile` field

**CHECKPOINT — Phase 4 complete when:**
- CGPA field shows inline error for value 5.0 without submitting
- Submitting a valid profile serializes all fields correctly in DevTools Network tab

---

## Phase 5: User Story 3 — Email Input (Paste + File Upload)

**Goal**: React email input section with textarea + file upload, delimiter hint, and validation.
**Independent Test**: Paste 3 emails with `---EMAIL---` delimiters, submit, verify 3 emails processed.
**Await "proceed" before Phase 6.**

- [x] T023 [US3] Create `frontend/src/components/EmailInput.tsx` — `<textarea>` with placeholder showing `---EMAIL---` delimiter example. `<input type="file" multiple accept=".txt,.eml">`. Tab switcher (Paste / Upload) using plain CSS. Character count display. Disable submit if both are empty
- [x] T024 [US3] Create `frontend/src/pages/InputPage.tsx` — composes `EmailInput` + `ProfileForm` + submit button. Calls `api.ts` `analyze()`. On submit transitions app state to "loading". Handles validation error display (HTTP 400 detail string shown as banner)

**CHECKPOINT — Phase 5 complete when:**
- Paste + Upload tabs switch correctly
- Empty submit shows client-side error
- Valid submit transitions to loading state

---

## Phase 6: User Story 4 — Graceful Degradation (AI Failures)

**Goal**: All AI failure paths return safe output — no crashes, no silent data loss.
**Independent Test**: Inject malformed JSON in classifier response; verify all emails still appear as opportunities. Disable checklist API; verify fallback bullets appear.
**Await "proceed" before Phase 7.**

- [x] T025 [US4] Harden `backend/app/services/classifier.py` — wrap `json.loads()` in `try/except json.JSONDecodeError`; on failure log warning and return all emails as `is_opportunity=True` with `confidence=0.5`. Add `classification_uncertain=True` if confidence < 0.6
- [x] T026 [US4] Harden `backend/app/services/extractor.py` — wrap per-email extraction in `try/except`; on failure return `OpportunityObject` with all optional fields null and title defaulting to email subject. Never drop an email from output
- [x] T027 [US4] Harden `backend/app/services/checklist.py` — wrap entire AI call in `try/except`; on any failure call `fallback_checklist()` for every opportunity. Ensure `fallback_checklist` always returns at least 1 bullet even if all fields are null
- [x] T028 [P] [US4] Write `backend/tests/unit/test_fallbacks.py` — test classification JSON failure → all opportunities pass. Test extraction parse failure → null-field OpportunityObject preserved. Test checklist failure → fallback bullets generated

**CHECKPOINT — Phase 6 complete when:**
- All 3 test cases in `test_fallbacks.py` pass
- With `GEMINI_API_KEY=invalid`, `/api/analyze` still returns HTTP 200 with fallback data (not 500)

---

## Phase 7: User Story 5 — Offline Demo Mode

**Goal**: Pre-computed fixture loaded by `GET /api/demo`; "Load Demo" button in UI.
**Independent Test**: Disable internet. Click "Load Demo". Full ranked results appear in < 2s.
**Await "proceed" before Phase 8.**

- [ ] T029 [US5] Create `backend/app/scripts/generate_demo.py` — runs the full pipeline with 5 hardcoded curated emails (HEC Scholarship, ICPC, Google GSoC, pizza spam, webinar noise) and a hardcoded student profile. Saves result to `backend/app/data/demo_response.json`. Run once and commit the fixture
- [ ] T030 [US5] Implement `GET /api/demo` in `backend/app/api/routes.py` — reads and returns `demo_response.json` as `FinalResponse`. Returns HTTP 404 with regeneration instructions if file missing. No AI calls made
- [ ] T031 [US5] Add "Load Demo" button to `frontend/src/pages/InputPage.tsx` — calls `GET /api/demo`, populates results page. Show "(Demo Mode)" label in results header

**CHECKPOINT — Phase 7 complete when:**
- `GET /api/demo` returns pre-computed results in < 100ms
- "Load Demo" button renders results without any network call to Gemini

---

## Phase 8: Results UI (Cross-Story Frontend Assembly)

**Goal**: Results page displaying ranked opportunity cards + filtered-out section.
**Await "proceed" before Phase 9.**

- [ ] T032 Create `frontend/src/components/OpportunityCard.tsx` — displays: rank badge, title, organization, score (N/100), urgency badge (plain colored `<span>`), score breakdown table, evidence bullet list, action checklist, "Apply →" link (only if application_link present). "(uncertain)" label if `classification_uncertain`. "⚠ BELOW CGPA REQUIREMENT" warning if `is_ineligible`. Plain HTML, no animation
- [ ] T033 [P] Create `frontend/src/components/FilteredOut.tsx` — collapsible `<details><summary>` showing rejected emails with their reject_reason. No JS toggle needed — native HTML
- [ ] T034 [P] Create `frontend/src/components/LoadingOverlay.tsx` — simple `<div>` with text "Processing your emails…" and a CSS spinner (single rotating border, no library). Shows sequentially-updating step label via `setInterval` timed to estimated pipeline duration
- [ ] T035 Create `frontend/src/pages/ResultsPage.tsx` — renders warning banners (from `FinalResponse.warnings`), summary stats bar (X emails → Y opportunities found in Zms), sorted `OpportunityCard` list, `FilteredOut` section, "Analyze Again" button that resets state
- [ ] T036 Update `frontend/src/App.tsx` — state machine: `"input" | "loading" | "results" | "error"`. Routes between `InputPage` and `ResultsPage`. Handles HTTP 4xx showing error banner with retry. Handles HTTP 200 transitioning to results

**CHECKPOINT — Phase 8 complete when:**
- Full end-to-end flow works in browser: paste emails → fill profile → submit → loading → ranked cards
- Demo mode shows identical results
- Expired opportunities show EXPIRED badge at bottom of list
- Ineligible opportunity shows warning, not removed

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Hardening, cleanup, and README finalization. No new features.
**Await "proceed" before declaring complete.**

- [ ] T037 Verify all constants are named (`MAX_EMAILS`, `MIN_CHAR_COUNT`, `MAX_BODY_CHARS`, `VALUE_MAP`, `URGENCY_BRACKETS`) — no magic numbers anywhere in `backend/`
- [ ] T038 [P] Verify every function in `backend/app/services/` is ≤ 40 lines. Split any that exceed (per constitution Principle II)
- [ ] T039 [P] Verify every React component is ≤ 100 lines. Split any that exceed (per constitution Principle VIII)
- [ ] T040 Add server-side error response sanitization to `backend/app/main.py` — global exception handler returns `{"detail": "Internal processing error"}` for all unhandled 500s; no stack traces leak to client
- [ ] T041 [P] Write `backend/tests/integration/test_api.py` — integration test for `POST /api/analyze` with real fixture emails (mocked AI client returning fixture JSON). Assert response shape matches `FinalResponse` schema
- [ ] T044 [P] Add determinism regression test: call scoring twice with identical inputs and assert identical outputs (covers SC-007)
- [ ] T045 [P] Add AI call budget regression test: instrument/mock `AIClient.call` and assert `/api/analyze` performs exactly 3 calls per request (covers FR-038)
- [ ] T046 Add lightweight timing check script or test (generous thresholds): demo endpoint responds fast and analyze completes under normal conditions (covers SC-001, SC-005)
- [ ] T047 (Optional) Add a small labeled classification fixture set + evaluation script to compute precision/recall for SC-002, or explicitly downgrade SC-002 to a qualitative acceptance criterion if not implementing metrics
- [ ] T042 Update `context/session_log.md` with a final `[AGENT]` entry summarizing what was built and any deviations from constitution
- [ ] T043 Run `quickstart.md` validation: start both servers fresh, run `pytest backend/tests/`, confirm demo mode works, confirm analyze endpoint returns correct shape

**CHECKPOINT — Phase 9 (Final) complete when:**
- `pytest backend/tests/` — all tests pass
- No magic numbers in services code
- All functions ≤ 40 lines, all components ≤ 100 lines
- Error responses never leak stack traces
- README instructions produce a working demo from a clean checkout

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — **BLOCKS** Phases 3–9
- **Phase 3 (US1 — Full Pipeline)**: Depends on Phase 2 — core value; must complete first
- **Phase 4 (US2 — Profile Form)**: Depends on Phase 2; can integrate with Phase 3 output
- **Phase 5 (US3 — Email Input)**: Depends on Phase 2; can integrate with Phase 3 output
- **Phase 6 (US4 — Degradation)**: Depends on Phase 3 (hardens existing services)
- **Phase 7 (US5 — Demo Mode)**: Depends on Phase 3 (needs working pipeline to generate fixture)
- **Phase 8 (Results UI)**: Depends on Phases 3, 4, 5 (assembles all frontend pieces)
- **Phase 9 (Polish)**: Depends on all prior phases complete

### Within Each Phase

- Tasks marked `[P]` can be executed in parallel (different files, no shared state)
- Models before services; services before routes; routes before UI integration
- Tests written in same phase as the code they test (not deferred)
- Fallback paths implemented in same phase as primary path (Principle V)

---

## Implementation Strategy

### MVP (Phases 1–3 only)
Delivers: working `/api/analyze` endpoint that classifies, extracts, scores, and returns ranked JSON.
No UI — testable via `curl` or Postman. Validates the core AI pipeline.

### Demo-Ready (Phases 1–8)
Adds: profile form UI, email input UI, results cards, demo mode. Full browser-based demo.

### Production-Hardened (All 9 Phases)
Adds: graceful degradation, integration tests, hardening, constitution compliance verification.

---

## Task Summary

| Phase | Tasks | Parallelizable | Story |
|-------|-------|----------------|-------|
| 1 — Setup | T001–T007 | T005, T006 | — |
| 2 — Foundational | T008–T012 | T011, T012 | — |
| 3 — US1 Full Pipeline | T013–T020 | T019, T020 | US1 |
| 4 — US2 Profile Form | T021–T022 | — | US2 |
| 5 — US3 Email Input | T023–T024 | — | US3 |
| 6 — US4 Degradation | T025–T028 | T028 | US4 |
| 7 — US5 Demo Mode | T029–T031 | — | US5 |
| 8 — Results UI | T032–T036 | T033, T034 | — |
| 9 — Polish | T037–T047 | T038, T039, T041, T044, T045 | — |
| **Total** | **47 tasks** | **13 parallelizable** | |
