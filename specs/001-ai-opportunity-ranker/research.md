# Research: AI Opportunity Inbox Copilot

**Date**: 2026-04-18 | **Branch**: `001-ai-opportunity-ranker`

---

## Decision 1: AI Provider / Model

**Decision**: **Gemini 2.0 Flash** via the `google-genai` Python SDK (native), with a `.env` configurable `GEMINI_API_KEY`.

**Rationale**:
- Free tier at Google AI Studio (`aistudio.google.com`) — zero cost during hackathon demo.
- Supports native `response_mime_type="application/json"` + `response_json_schema` for strict structured output — critical for our 3-call batch architecture.
- Context window (1M tokens) is more than sufficient for a 15-email batch.
- Fast (Flash model ~1–2s per call) — meets the 30-second end-to-end SC-001.
- The spec says "open source models" — interpreted as: open API access with no per-seat licensing. Gemini Flash's free tier satisfies this. Alternatively, if a local Ollama model is required, `llama3.2:3b` is the fallback (see Decision 1b below).

**Alternative — Decision 1b: Ollama + llama3.2 (true local open-source)**:
- If internet is unavailable or judges require truly local models: `ollama pull llama3.2:3b` — supports JSON mode via Ollama's `/api/chat` with `format: "json"`.
- Configured via `LLM_PROVIDER=ollama` env var. Backend switches provider transparently.
- Tradeoff: slower (~5–15s per batch call), no guarantee of JSON schema compliance without Pydantic retry logic.

**Alternatives considered**:
- Claude 3 Haiku: paid-only after $5 free credit, risky for repeated judge demos.
- GPT-4o mini: OpenAI tier limits unpredictable; JSON mode reliable but cost uncertain.
- Local distilBERT classifier: Cannot do extraction + checklist — would need 3 separate model downloads.

---

## Decision 2: Backend Framework

**Decision**: **FastAPI** (Python 3.11+) with **Uvicorn** as the ASGI server.

**Rationale**:
- Single `POST /api/analyze` endpoint handles both `multipart/form-data` file upload and pasted text.
- `python-multipart` handles form-data parsing; `UploadFile` streams files without loading into memory.
- Auto-generated OpenAPI docs at `/docs` — useful for judge inspection.
- Native async support — the 3 sequential AI calls run `await` without blocking.
- `pydantic` v2 for all schema validation (StudentProfile, FinalResponse, etc.) — automatic validation errors with clear messages.

**Library stack**:
```
fastapi==0.115.x
uvicorn[standard]==0.29.x
python-multipart==0.0.9
pydantic==2.x
google-genai==1.x          # primary LLM client
httpx==0.27.x              # for optional Ollama HTTP calls
python-dateutil==2.9.x     # robust date parsing fallback
beautifulsoup4==4.12.x     # HTML stripping for .eml fallback
```

---

## Decision 3: Frontend Framework

**Decision**: **React 18 + Vite** (TypeScript), styled with plain CSS (no Tailwind, no UI library).

**Rationale**:
- User explicitly requested React.
- Vite gives instant HMR and < 300ms cold starts — fast iteration during 2-hour development.
- TypeScript catches API contract errors at compile time (FinalResponse shape mismatches).
- Plain CSS avoids build-time complexity; premium dark-mode design achievable with CSS variables.
- No state management library needed — a single `useState` + `fetch` covers the entire app flow.

**Key dependencies**:
```
react@18, react-dom@18
typescript@5
vite@5
```

---

## Decision 4: Project Structure

**Decision**: **Monorepo with two top-level directories** — `backend/` and `frontend/`.

**Rationale**:
- Clean separation; no confusion about which `package.json` or `requirements.txt` applies where.
- Backend served at `localhost:8000`, frontend dev server at `localhost:5173`.
- Vite proxy (`/api → http://localhost:8000`) eliminates CORS issues in development without modifying backend CORS config.
- Single `README.md` at root with instructions for both.

---

## Decision 5: Scoring Engine Location

**Decision**: Pure Python module at `backend/app/services/scoring.py` — deterministic, zero dependencies on AI SDK.

**Rationale**:
- All scoring logic lives in one file, independently unit-testable with no mocks needed.
- Scoring runs synchronously (pure math) — no async overhead.
- Separation of concerns: AI calls in `services/ai_client.py`, scoring in `services/scoring.py`.

---

## Decision 6: Demo Mode Implementation

**Decision**: Pre-computed JSON fixture file at `backend/app/data/demo_response.json`.

**Rationale**:
- GET `/api/demo` endpoint returns the fixture instantly (< 50ms, zero AI calls).
- Fixture is generated once by running the real pipeline with 5 curated emails, then saved.
- If fixture is missing, the endpoint returns a 404 with a clear message to regenerate it.

---

## Decision 7: Date / Deadline Handling

**Decision**: Today's date is retrieved via `datetime.date.today()` at request time (not hardcoded). Passed to the AI prompt as `TODAY = YYYY-MM-DD`.

**Rationale**:
- The spec's hardcoded `2026-04-18` was a documentation example, not a production choice.
- `python-dateutil` as fallback parser for any dates the LLM outputs that fail `fromisoformat()`.

---

## Decision 8: CORS Configuration

**Decision**: Backend allows `http://localhost:5173` (Vite dev) and `http://localhost:4173` (Vite preview) in development. Configured via `ALLOWED_ORIGINS` env var so production origins can be injected without code changes.

---

## Decision 9: Error Handling Strategy

**Decision**: All AI call failures are caught at the service layer and converted to safe fallback objects. The HTTP response is always HTTP 200 with the `FinalResponse` shape — never a 500 to the frontend. Internal errors are logged server-side.

**Rationale**: A 500 error during a judge demo is catastrophic. Silent degradation (with user-visible warning labels like "extraction incomplete") is always preferable.

---

## Decision 10: Text Truncation Limit

**Decision**: 3000 characters per email body before sending to AI (not 2000 as in the original PRDs.md, because Gemini Flash has a generous context window and 3000 chars captures most real-world opportunity emails fully).

---

## Resolved Clarifications

| NEEDS CLARIFICATION | Resolution |
|---------------------|------------|
| Which open source model? | Gemini Flash (free API, JSON mode, fast). Ollama llama3.2:3b as offline fallback. |
| React version? | React 18 with Vite 5 + TypeScript |
| Any database needed? | No — stateless per-request processing. No persistence layer. |
| Deployment target? | Local dev only for hackathon. `README.md` instructions for running both servers. |
| API key management? | `.env` file at `backend/` root, loaded via `python-dotenv`. |
