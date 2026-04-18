# Quickstart: AI Opportunity Inbox Copilot

**Branch**: `001-ai-opportunity-ranker` | **Runtime**: Python 3.11+ / Node 18+

---

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- A Gemini API key from [aistudio.google.com](https://aistudio.google.com/) (free tier)
- Git

---

## Project Layout

```text
d:/edris-antigravity/          ← repo root
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py          # FastAPI router: /api/analyze, /api/demo, /api/health
│   │   ├── models/
│   │   │   └── schemas.py         # Pydantic models: RawEmail, StudentProfile, OpportunityObject,
│   │   │                          #   ClassificationResult, ScoredOpportunity, RankedOutput, FinalResponse
│   │   ├── services/
│   │   │   ├── ingestion.py       # Flow 1: parse paste + .eml/.txt files → RawEmail[]
│   │   │   ├── classifier.py      # Flow 2: AI Call #1 — batch classification
│   │   │   ├── extractor.py       # Flow 3: AI Call #2 — batch extraction → OpportunityObject[]
│   │   │   ├── scoring.py         # Flow 4: deterministic scoring + ranking (zero AI)
│   │   │   ├── checklist.py       # Flow 5: AI Call #3 — batch checklist generation
│   │   │   └── ai_client.py       # Gemini / Ollama client wrapper + retry logic
│   │   ├── data/
│   │   │   └── demo_response.json # Pre-computed demo output (committed to repo)
│   │   ├── scripts/
│   │   │   └── generate_demo.py   # One-shot script to regenerate demo_response.json
│   │   └── main.py                # FastAPI app factory + CORS + router mount
│   ├── requirements.txt
│   └── .env                       # GEMINI_API_KEY=... (not committed)
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── EmailInput.tsx      # Paste textarea + file upload, delimiter hint
│   │   │   ├── ProfileForm.tsx     # Student profile structured form
│   │   │   ├── OpportunityCard.tsx # Single ranked opportunity card
│   │   │   ├── FilteredOut.tsx     # Collapsible filtered emails section
│   │   │   └── LoadingOverlay.tsx  # Full-screen loading with progress steps
│   │   ├── pages/
│   │   │   ├── InputPage.tsx       # Step 1: email input + profile form
│   │   │   └── ResultsPage.tsx     # Step 2: ranked opportunity list + filtered section
│   │   ├── services/
│   │   │   └── api.ts              # fetch wrappers for /api/analyze and /api/demo
│   │   ├── types/
│   │   │   └── models.ts           # TypeScript interfaces mirroring backend schemas
│   │   ├── App.tsx                 # Root: two-page routing (input → results)
│   │   ├── main.tsx                # React entry point
│   │   └── index.css               # Global CSS variables, dark mode, typography
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts              # API proxy: /api → http://localhost:8000
│   ├── tsconfig.json
│   └── package.json
├── specs/
│   └── 001-ai-opportunity-ranker/  # This spec directory
├── README.md                       # Root-level combined quickstart
└── AGENTS.md
```

---

## Setup & Run

### 1. Clone and navigate

```bash
git clone <repo-url>
cd edris-antigravity
```

### 2. Backend setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1         # Windows PowerShell
# source venv/bin/activate          # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and set: GEMINI_API_KEY=your_key_here
```

**`backend/requirements.txt`**:
```
fastapi==0.115.0
uvicorn[standard]==0.29.0
python-multipart==0.0.9
pydantic==2.13.0
google-genai==1.0.0
python-dotenv==1.0.0
httpx==0.27.0
python-dateutil==2.9.0
beautifulsoup4==4.12.3
pytest==8.4.2
```

### 3. Frontend setup

```bash
cd frontend
npm install
```

### 4. Run both servers (two terminals)

**Terminal 1 — Backend**:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
Backend available at: `http://localhost:8000`  
API docs at: `http://localhost:8000/docs`

**Terminal 2 — Frontend**:
```bash
cd frontend
npm run dev
```
Frontend available at: `http://localhost:5173`

---

## Demo Mode (no API key needed)

The pre-computed `demo_response.json` is committed in the repo. Click **"Load Demo"** in the UI to see results instantly without any API calls.

To regenerate the demo fixture with live data:
```bash
cd backend
python -m app.scripts.generate_demo
```

---

## Using Ollama (offline / local model)

If you prefer a fully local open-source model:

```bash
# Install Ollama from ollama.ai, then:
ollama pull llama3.2:3b
```

In `backend/.env`:
```
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

Restart the backend. All 3 AI calls will route to Ollama instead of Gemini.

> ⚠️ Ollama responses are slower (~5–15s per batch) and JSON schema compliance is lower — Pydantic retry logic will trigger on failures.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | (required if using Gemini) | Google AI Studio API key |
| `LLM_PROVIDER` | `gemini` | `gemini` or `ollama` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2:3b` | Ollama model name |
| `ALLOWED_ORIGINS` | `http://localhost:5173,http://localhost:4173` | Comma-separated CORS origins |
| `MAX_EMAILS` | `15` | Maximum emails per request |
| `MAX_BODY_CHARS` | `3000` | Truncation limit per email body |

---

## Key Commands

| Command | What it does |
|---------|-------------|
| `uvicorn app.main:app --reload` | Start backend dev server with hot reload |
| `npm run dev` | Start frontend dev server with HMR |
| `npm run build` | Build frontend for production |
| `python -m app.scripts.generate_demo` | Regenerate demo fixture JSON |
| `pytest backend/tests/` | Run backend unit tests |
