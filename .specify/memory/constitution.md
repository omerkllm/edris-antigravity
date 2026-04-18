<!--
SYNC IMPACT REPORT
==================
Version change: (blank template) → 1.0.0
Constitution established from scratch — all principles are new additions.

Added sections:
  I.   Algorithmic Efficiency
  II.  Code Structure & Modularity
  III. Phase-Gated Delivery (NON-NEGOTIABLE)
  IV.  Context Continuity
  V.   Code Correctness & No Faulty Code (NON-NEGOTIABLE)
  VI.  Security, Validation & Rate Limiting
  VII. Simplicity First
  VIII.Minimal UI Priority

Templates updated:
  ✅ .specify/templates/plan-template.md  — Constitution Check gates now map to I–VIII
  ✅ .specify/templates/tasks-template.md — Phase-gate rule enforced (one phase, await proceed)
  ✅ .specify/memory/constitution.md      — This file (established)
  ⚠  .specify/templates/spec-template.md — No structural changes needed; principles apply at task/impl level

Deferred items:
  None — all principles provided by user; no TODOs remain.

Suggested commit message:
  docs: establish constitution v1.0.0 (8 principles — efficiency, structure, phase-gating, context, correctness, security, simplicity, minimal UI)
-->

# AI Opportunity Inbox Copilot — Constitution

## Core Principles

### I. Algorithmic Efficiency

Every algorithm, data structure, and transformation in this codebase MUST use
the best feasible time complexity for the problem. Choosing a worse complexity
class MUST be explicitly justified in a code comment citing why the optimal
approach is impractical (e.g., memory constraint, library limitation).

Rules:
- Prefer O(1) lookups (sets, dicts) over O(n) linear scans where the data size
  is unbounded or user-controlled.
- Sorting MUST use O(n log n) algorithms (Python's built-in `sorted()`/`sort()`
  use Timsort — always prefer these over hand-rolled sorting).
- Deduplication MUST use a hash set, never nested loops.
- No nested loops over the same collection unless the algorithm is provably O(n²)
  and alternatives have been evaluated.
- String matching for URL hallucination guard MUST use substring search, not
  character-by-character comparison.

### II. Code Structure & Modularity (NON-NEGOTIABLE)

Code MUST be organized into functions and classes with clear, single
responsibilities. Spaghetti code (inline logic spread across route handlers,
unstructured top-level scripts, deeply nested conditionals) is prohibited.

Rules:
- Every logical operation (parsing, scoring, AI call, validation) MUST live in
  its own named function or method — not inlined in a route handler.
- Classes MUST be used when a unit of code owns state and has multiple behaviors
  (e.g., `AIClient`, `ScoringEngine`). Pure functions MUST be used for stateless
  transformations (e.g., `parse_cgpa`, `assign_badge`).
- Functions MUST do one thing. A function that parses AND scores is two functions.
- Maximum function length: 40 lines. Exceed this only when a longer function is a
  mandatory sequence that cannot be meaningfully split (justify in a comment).
- No magic numbers in logic — all constants MUST be named (e.g., `MAX_EMAILS = 15`,
  `MIN_CHAR_COUNT = 30`).
- File responsibilities: one module per concern (ingestion, classifier, extractor,
  scoring, checklist, ai_client). No catch-all `utils.py` dumping grounds.

### III. Phase-Gated Delivery (NON-NEGOTIABLE)

Implementation MUST proceed exactly one phase at a time. The next phase MUST NOT
begin until the user explicitly issues a "proceed" command.

Rules:
- Each phase ends with a visible CHECKPOINT summary listing what was built and
  what the user should verify before saying "proceed."
- The agent MUST NOT autonomously start the next phase, even if it believes the
  previous phase is complete.
- Phases are defined in `tasks.md`. No phase boundaries may be skipped or merged.
- If an error is discovered mid-phase, it MUST be fixed within that phase before
  the phase is declared complete. The user is notified.

### IV. Context Continuity

Every conversation turn that produces code, decisions, or discoveries MUST be
recorded in `context/session_log.md` at the project root so it can be used as
context for future turns.

Rules:
- The file is append-only. Existing entries MUST NOT be modified.
- Each entry MUST have: timestamp (ISO 8601), turn type (USER / AGENT), and a
  concise summary (2–5 sentences max) of what was asked or decided.
- Decisions that affect architecture, file paths, or scoring logic MUST be tagged
  `[DECISION]` in the log.
- The log is consulted at the start of any implementation turn before any code is
  written.
- Format per entry:
  ```
  ### [TIMESTAMP] [USER|AGENT]
  [Summary]
  [DECISION] (if applicable)
  ```

### V. Code Correctness & No Faulty Code (NON-NEGOTIABLE)

Code that is shipped MUST work. Placeholder stubs, `TODO: implement this`,
`pass` bodies in critical paths, or code known to be broken are PROHIBITED.

Rules:
- Every function MUST be complete and executable before it is included in a phase
  deliverable.
- The agent MUST NOT produce code with unresolved `NameError`, `ImportError`, or
  obvious type mismatches. If a dependency is uncertain, research it first.
- Every Pydantic model MUST have valid field types and defaults that match the
  actual data shapes in the pipeline.
- JSON parse failures in AI responses MUST be handled with try/except on every
  call — never assume the AI output is valid.
- Before declaring a phase complete, the agent MUST mentally trace the primary
  happy-path through all functions written in that phase.
- Fallback paths (classification failure, extraction failure, checklist failure)
  MUST be implemented in the same phase as the primary path — not deferred.

### VI. Security, Validation & Rate Limiting

All external inputs MUST be validated before processing. The system MUST protect
against common attack vectors and API exhaustion.

Rules:
- Input validation MUST happen at the API boundary (FastAPI route) via Pydantic.
  No raw un-validated data MUST reach the service layer.
- File uploads MUST validate: MIME type (text/plain or message/rfc822 for .eml),
  and size (max 500 KB per file). Files exceeding limits are rejected with HTTP 413.
- CGPA MUST be validated as float in [0.0, 4.0]. Semester MUST be int in [1, 8].
  These are enforced by Pydantic `Field(ge=0.0, le=4.0)` and `Field(ge=1, le=8)`.
- The API endpoint MUST implement per-request rate limiting: max 10 requests per
  minute per IP address using a simple in-memory sliding window counter.
- AI prompt content MUST be text-only. No user-controlled prompt injection vectors
  (email bodies are inserted as quoted data blocks, not as instructions).
- Application links extracted by AI MUST be validated as verbatim substrings of the
  original email raw text before being returned to the client.
- Error responses MUST NOT leak internal stack traces or file paths to the client.
  All 500-class errors return a generic `{"detail": "Internal processing error"}`.
- The `GEMINI_API_KEY` MUST be loaded from environment only — never hardcoded or
  logged.

### VII. Simplicity First

The simplest correct solution MUST always be chosen over a clever or complex one.
Complexity MUST be justified by a concrete requirement, not by anticipation of
future needs (YAGNI).

Rules:
- No abstractions created for fewer than 2 concrete use cases.
- No third-party libraries added unless a stdlib solution is genuinely insufficient.
  Each new dependency MUST be justified in a comment or the plan.
- No database, ORM, cache, or message queue unless explicitly required by the spec.
  The system is stateless per-request.
- No dependency injection frameworks, plugin systems, or factory patterns unless
  the codebase has 3+ implementations of the same interface.
- Frontend state management MUST use React's built-in `useState`/`useEffect` —
  no Redux, Zustand, or Context API unless state genuinely spans more than 3
  unrelated components.
- When in doubt: write less code.

### VIII. Minimal UI Priority

The user interface (React frontend) is functional scaffolding for the demo.
UI polish MUST NOT be prioritized over pipeline correctness or AI accuracy.
The UI MUST be kept as basic as possible — no animations, no glassmorphism,
no elaborate design systems.

Rules:
- Plain HTML form elements (input, select, checkbox, textarea) are preferred.
- CSS MUST be plain CSS with no Tailwind, no CSS-in-JS, no UI component libraries
  (no MUI, no Chakra, no shadcn).
- The UI MUST be functional and readable. It need not be beautiful.
- No micro-animations, no transitions, no hover effects beyond the browser default
  unless they directly aid usability (e.g., a loading spinner is acceptable).
- Each React component MUST be under 100 lines. Longer components MUST be split.
- No placeholder images, no stock photos, no icon libraries beyond system emoji
  for urgency badges.

## Development Workflow

- All implementation MUST follow phase order defined in `tasks.md`.
- Each phase checkpoint MUST be verified by the user before the next phase starts
  (Principle III).
- The session log at `context/session_log.md` MUST be updated after each
  substantive agent turn (Principle IV).
- Constitution compliance MUST be verified in the `Constitution Check` section of
  every `plan.md` before implementation begins.
- Any deviation from these principles MUST be noted in `context/session_log.md`
  as a `[DEVIATION]` entry with justification.

## Governance

- This constitution supersedes all other project conventions.
- Amendments require: (a) user request, (b) version increment per semantic rules,
  (c) sync impact report, (d) update to `AGENTS.md` if applicable.
- MAJOR bump: removal or redefinition of a principle.
- MINOR bump: new principle added or materially expanded.
- PATCH bump: wording, clarification, typo fixes.
- All implementation PRs/reviews MUST verify constitution compliance.

**Version**: 1.0.0 | **Ratified**: 2026-04-18 | **Last Amended**: 2026-04-18
