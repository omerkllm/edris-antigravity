# AI Opportunity Inbox Copilot

Full-stack demo app that takes 5–15 emails + a student profile, identifies real opportunities, extracts structured fields, scores them deterministically (0–100), and returns a ranked list with evidence and action checklists.

## Quickstart

### Backend

```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

## Demo Mode

Once implemented (Phase 7), the UI will provide a **Load Demo** button backed by `GET /api/demo` returning a pre-computed fixture.

