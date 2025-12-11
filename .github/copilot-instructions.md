<!-- .github/copilot-instructions.md - Guidance for AI coding agents working on Aequitas -->
# Aequitas — Copilot Instructions (concise)

These concise instructions help an AI coding agent be productive quickly in this repository.

1) Big picture (what to touch first)
- Backend: `backend/app/` (FastAPI + SQLAlchemy). Core layers: `api/` (routes), `services/` (business logic), `db/` (models & session), `core/` (config, security, UCID).
- Frontend: `frontend/src/` (React + Vite). API client in `frontend/src/lib/api.ts`, `AuthProvider` in `frontend/src/contexts`.
- Dev orchestration: `Makefile` + `docker-compose.dev.yml` (recommended dev flow).

2) Quick dev workflows (exact commands)
- Start full dev stack (Docker): `make dev` (uses `docker-compose.dev.yml`).
- Stop: `make stop`; Logs: `make logs`; Full reset: `make reset`; Reset DB: `make reset-db`.
- Run backend tests: `cd backend && python -m pytest` (pytest lives under `backend/tests`).
- Run backend locally (no Docker): `cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000`.
- Install CLI for admin tasks: `cd backend && pip install -e .` then use `aequitas` commands (see `README.md` examples).

3) Project-specific conventions to follow
- UCID: Companies use a 4-character UCID generated in `backend/app/core/ucid.py`. Prefer using `generate_ucid()` for new-company code paths.
- DB session: Use `get_db()` dependency from `backend/app/db/session.py` in route handlers; do not open ad-hoc sessions.
- Service layer: Business logic belongs in `backend/app/services/*` and should be called from `api/v1/*` routes — avoid mixing concerns in route handlers.
- Master chart seed: Master chart data and reseeding scripts live in `backend/app/data/` (e.g., `seed_enriched_master_chart.py`).
- AI integrations: Ollama runs at `http://localhost:11435` in dev; env vars `OLLAMA_HOST` / `OLLAMA_MODEL` and Cloudflare Workers AI keys are in `backend` envs.

4) API and routing patterns (examples)
- Base API prefix: `/api/v1` (routes under `backend/app/api/v1/`).
- Common endpoints: `/api/v1/companies`, `/api/v1/masterchart`, `/api/v1/organizer`, `/api/v1/journal-entries`.
- Auth: JWT expected in `Authorization: Bearer <token>`; tokens produced via `create_access_token()` in `backend/app/core/security.py`.

5) What to include in any patch / PR
- File list: provide an explicit list of changed files.
- Motivation: 1–2 sentences explaining why (bugfix, feature, refactor).
- Tests: point to added/updated tests and how to run them locally (`python -m pytest backend/tests/...`).
- Validation: steps to manually exercise the change (eg. endpoints to call, UI flows to click, CLI commands to run).

6) Quick examples (copy/paste patterns)
- Add route skeleton: create `backend/app/api/v1/<module>.py`, add router and include in `app/main.py`.
- Add service call in route:
  - from `backend.app.services.<module>_service import <function>`
  - call service using `db = next(get_db())` only in tests; in routes use dependency injection `db: Session = Depends(get_db)`.
- Reseed master chart: `cd backend && python app/data/seed_enriched_master_chart.py`.

7) Tests & CI expectations
- Run backend unit tests with `python -m pytest` from `backend/`.
- Keep backend changes covered by tests where possible (unit-level for services, integration for API routes).

8) Integration & external dependencies
- Docker compose includes Postgres and Ollama; prefer the Docker dev stack for consistent envs.
- QuickBooks integration keys: `QBO_*` env vars. Cloudflare Workers AI via `CLOUDFLARE_*` env vars.

9) Files to inspect when reasoning about a change
- `backend/app/main.py` — app startup, DB table creation, router includes
- `backend/app/core/config.py` — settings and env-var defaults
- `backend/app/services/` — business logic implementations
- `backend/app/db/models/` and `backend/app/schemas/` — canonical data shapes
- `frontend/src/lib/api.ts` & `frontend/src/contexts/AuthContext.tsx` — frontend integration points

10) Tone and patch discipline (project rule derived from CLAUDE.md)
- Produce deterministic, well-scoped patches. Avoid speculative or TODO-only code. Include a short risk analysis and validation steps.

If anything here is unclear or you'd like more examples (e.g., a template PR body, test snippet, or example route), tell me what to expand.  
