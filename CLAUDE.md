# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Aequitas** is an integrated accounting system with intelligent chart of accounts management, journal entries, financial reporting, and AI-powered account classification. The system uses a modern React/Vite frontend with a FastAPI/PostgreSQL backend, containerized with Docker.

**Key Modules:**
- **Registration:** Companies, users, and basic chart of accounts setup
- **Chart of Accounts (ChartForge):** Master chart management with AI-powered classification (Dexter AI), QuickBooks integration, templates, and mapping engine
- **Accountancy:** Journal entries, ledger accounts, trial balance, fiscal periods
- **Reports:** Financial statements (Balance Sheet, Income Statement, Cash Flow)
- **Administration:** System settings, integrations, audit logs, superuser panel

## Development Environment

### Primary Development Commands

```bash
# Start all services (recommended)
make dev

# Stop all services
make stop

# View logs
make logs

# Complete reset (stops, removes volumes, rebuilds)
make reset

# Reset database only
make reset-db

# Force rebuild containers without cache
make rebuild
```

### Service URLs (when running)
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs (interactive Swagger UI)
- Ollama (AI): http://localhost:11435
- PostgreSQL: localhost:5432

### Dependency Management

**Docker development (recommended):** Changes to dependencies require `make rebuild` to rebuild containers with fresh dependencies.

**Local IDE support (for TypeScript/ESLint/autocomplete):**
```bash
make install-deps          # Install all dependencies locally
make install-frontend      # Install frontend dependencies only
make install-backend       # Install backend dependencies only
make reinstall-deps        # Clean and reinstall all dependencies
```

### Running Tests

Backend tests use pytest:
```bash
# From backend directory
cd backend
python -m pytest

# Run specific test file
python -m pytest tests/test_ucid.py

# Run with verbose output
python -m pytest -v
```

## Architecture

### Backend Structure

**Framework:** FastAPI with SQLAlchemy ORM, PostgreSQL database, JWT authentication

**Core directories:**
- `backend/app/api/v1/` - API route handlers for each module
- `backend/app/db/models/` - SQLAlchemy database models
- `backend/app/schemas/` - Pydantic schemas for request/response validation
- `backend/app/services/` - Business logic layer
- `backend/app/core/` - Core utilities (config, security, UCID generation)
- `backend/app/data/` - Master chart data (US-GAAP CSV/JSON files, seed scripts)

**Key backend patterns:**

1. **Database session management:** Use the `get_db()` dependency from `app/db/session.py` in route handlers
2. **Authentication:** JWT tokens created via `create_access_token()` in `app/core/security.py`
3. **UCID Generation:** Company IDs use `generate_ucid()` from `app/core/ucid.py` (normalizes name, hashes with SHA-256, truncates to 4 chars)
4. **Configuration:** All settings managed through `app/core/config.py` using Pydantic Settings with `.env` file support
5. **Service layer:** Business logic lives in `app/services/` separate from API routes

**Database initialization:** On startup, `app/main.py` creates all tables via `Base.metadata.create_all()` and calls `init_db()` to create the default superuser.

**Master Chart:** The US-GAAP master chart (345 accounts) is stored in `backend/app/data/` as CSV/JSON. Seed with `seed_enriched_master_chart.py` or `seed_us_gaap.py`.

**AI Services:**
- `backend/app/services/organizer_ai/` - AI-powered account classification using Ollama or Cloudflare Workers AI
- `backend/app/services/dexter/` - Dexter AI assistant for chart of accounts queries and mapping

### Frontend Structure

**Framework:** React 19 + TypeScript with Vite, Tailwind CSS, shadcn/ui components, Tanstack Query for data fetching

**Core directories:**
- `frontend/src/pages/` - Page components organized by module (dashboard, registration, chartforge, accountancy, reports, admin)
- `frontend/src/components/` - Reusable UI components
- `frontend/src/lib/` - Utilities (API client, query keys, helpers)
- `frontend/src/contexts/` - React contexts (AuthContext)

**Key frontend patterns:**

1. **API client:** Central `api` object in `frontend/src/lib/api.ts` with methods `get()`, `post()`, `put()`, `delete()`, `patch()`
2. **Authentication:** `AuthProvider` context in `frontend/src/contexts/AuthContext.tsx`, `ProtectedRoute` component wraps authenticated routes
3. **Routing:** React Router with `DashboardLayout` wrapper for authenticated pages
4. **Module organization:** Routes follow pattern `/module/submodule` (e.g., `/chartforge/masterchart`, `/accountancy/journal`)

**URL routing patterns:**
- Registration: `/companies`, `/registration/users`, `/registration/coa`
- ChartForge: `/chartforge/masterchart`, `/chartforge/mapping`, `/chartforge/organizer`
- Accountancy: `/accountancy/ledger`, `/accountancy/journal`, `/accountancy/trial-balance`
- Reports: `/reports/statements`, `/reports/custom`, `/reports/export`
- Admin: `/admin/superuser`, `/admin/system`, `/admin/integrations`, `/admin/audit`

### API Architecture

**Base URL:** `/api/v1`

**Key endpoint patterns:**
- `/api/v1/companies` - Company CRUD
- `/api/v1/masterchart` - Master chart management
- `/api/v1/organizer` - AI account classification
- `/api/v1/ai` - Dexter AI assistant
- `/api/v1/qbo` - QuickBooks integration
- `/api/v1/journal-entries` - Journal entry management
- `/api/v1/accounting` - Ledger, fiscal periods, financial statements
- `/api/v1/auth` - Authentication (login, register)
- `/api/v1/settings` - System settings
- `/api/v1/admin` - Admin operations

**Authentication:** Most endpoints require JWT token in `Authorization: Bearer <token>` header.

## Database Models

**Key relationships:**

1. **Company ↔ Users:** Many-to-many through `UserCompany` join table
2. **Company → CompanyAccount:** One-to-many (each company has its own chart of accounts)
3. **Company → JournalEntry:** One-to-many (journal entries belong to a company)
4. **Company → FiscalPeriod:** One-to-many (fiscal periods belong to a company)
5. **JournalEntry → JournalEntryLine:** One-to-many (journal entry has multiple lines)
6. **MasterAccount:** Standalone table for the US-GAAP master chart (not company-specific)
7. **AccountMapping:** Links company accounts to master chart accounts

**Important model details:**
- Companies have a unique `ucid` (4-char hash) and can be soft-deleted (`is_active` flag)
- Users have role-based permissions (superuser, admin, user)
- Journal entries have a `status` field (draft, posted, void) and double-entry validation

## Configuration & Environment

**Backend configuration:** Managed via `backend/app/core/config.py` using Pydantic Settings.

**Required environment variables:**
- `DATABASE_URL` - PostgreSQL connection string (default: `postgresql+psycopg2://user:password@localhost:5432/aequitas_dev`)
- `SECRET_KEY` - JWT secret key
- `DEFAULT_SUPERUSER_EMAIL` / `DEFAULT_SUPERUSER_PASSWORD` - Initial superuser credentials

**Optional integrations:**
- `QBO_CLIENT_ID`, `QBO_CLIENT_SECRET`, `QBO_REDIRECT_URI` - QuickBooks OAuth
- `OLLAMA_HOST`, `OLLAMA_MODEL` - Ollama AI configuration
- `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` - Cloudflare Workers AI
- `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET` - Stripe payments

**Frontend environment:**
- `VITE_API_URL` - Backend API URL (default: `http://localhost:8000/api/v1`)

## Development Workflow

### Adding a New API Endpoint

1. Create route handler in `backend/app/api/v1/<module>.py`
2. Define request/response schemas in `backend/app/schemas/<module>.py`
3. Add business logic in `backend/app/services/<module>_service.py`
4. Update `backend/app/main.py` to include the router if new module
5. Frontend: Add API call in component using `api.get()`/`api.post()` from `frontend/src/lib/api.ts`

### Adding a New Database Model

1. Create model in `backend/app/db/models/<model_name>.py` inheriting from `Base`
2. Import model in `backend/app/db/models/__init__.py`
3. Import model in `backend/app/main.py` (required for table creation)
4. Restart backend to create table (in dev mode, tables are auto-created on startup)
5. For production, generate Alembic migration: `alembic revision --autogenerate -m "description"`

### Working with the Master Chart

The master chart is seeded from `backend/app/data/enriched_master_chart.json` or `us_gaap_master_chart.json`.

**To reseed the master chart:**
```bash
cd backend
python app/data/seed_enriched_master_chart.py
# or
python app/data/seed_us_gaap.py
```

**Master chart structure:**
- 345 total accounts (7 headers + 338 details)
- Account codes use hierarchical structure (e.g., `1.10.10.10` for Cash)
- Includes AI tags, vendor mappings, regulatory references (IAS/IFRS/ASC)

## Authentication & Authorization

**Default superuser credentials (change immediately):**
- Email: admin@aequitas.local
- Password: admin123

**Role levels:**
- **Superuser:** Full system access, can manage all companies and users
- **Admin:** Company-level administration
- **User:** Standard user access

**Backend auth utilities:**
- `create_access_token()` - Generate JWT token
- `verify_password()` - Validate password hash
- `get_password_hash()` - Hash password
- `check_superuser()` - Dependency to require superuser privileges

## Common Tasks

### Reset Database
```bash
make reset-db  # Removes postgres volume and recreates
```

### View Logs
```bash
make logs  # Follow all container logs

# View specific service logs
docker compose -f docker-compose.dev.yml logs backend
docker compose -f docker-compose.dev.yml logs frontend
```

### Run Backend Directly (without Docker)
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run Frontend Directly (without Docker)
```bash
cd frontend
npm install  # or pnpm install
npm run dev  # or pnpm dev
```

## Notes

- **Module naming:** The project recently renamed from "ChartForge" to "Aequitas". Some legacy references to "chartforge" remain in code and URLs.
- **Database migrations:** Currently using auto-table creation on startup. For production, implement proper Alembic migrations.
- **AI providers:** The system supports both Ollama (local, private) and Cloudflare Workers AI (edge-based) for account classification.
- **Session logging:** The system includes comprehensive development session logging via `make session` and the `SessionLogger` component in the frontend.

THE NEXT SECTIONS ARE THE USER NOTES - DO NOT DELETE

## Team Roles & Authority Structure

Aequitas is developed by a coordinated team consisting of Thome (project owner) and multiple AI agents.  
This section defines their roles, hierarchy, and interaction model.  
Claude Code must follow this structure in all development tasks.

### Hierarchy of Authority
1. **Thome — Chief Architect & Project Owner**  
   Provides strategic vision, requirements, and final decisions.

2. **Claude Code — Lead AI Developer (Tech Lead for all AI agents)**  
   Responsible for all major development tasks, system architecture, large-scale refactors,  
   page design, backend/ frontend coherence, accounting engine correctness, and roadmap execution.  
   Claude has technical authority over all remaining AI tools.

3. **ChatGPT — Prompt Architect & Development Strategist**  
   Converts Thome’s intentions into detailed technical prompts.  
   Assists with planning, debugging strategy, requirement analysis,  
   and serves as second-in-command to Claude in development matters.

4. **Gemini CLI — Dedicated Problem Solver**  
   Used exclusively for resolving specific technical issues, debugging,  
   isolated problems, error analysis, and targeted diagnostics.  
   Gemini must not modify architecture or refactor systems unless  
   explicitly instructed by Claude Code.

5. **Antigravity (Google Editor) — Minor Changes Executor**  
   Applies small edits, formatting adjustments, content polishing,  
   or micro-fixes in code or text.  
   Never performs major refactors, architecture changes, or multi-file updates.

---

## Claude Code — Mission & Operating Protocol

Claude Code is the **technical lead** and is responsible for ensuring that  
Aequitas remains coherent, maintainable, and aligned with the roadmap.

### Core Responsibilities
- Implement significant features and multi-file changes  
- Design and maintain backend and frontend architecture  
- Build the accounting engine (journal, ledger, periods, trial balance)  
- Create and refine system pages  
- Remove duplication and enforce structural conventions  
- Ensure GAAP compliance in all accounting logic  
- Guarantee end-to-end consistency between backend, frontend, seeders, and AI components  
- Review and enforce phase order in the roadmap  
- Produce clean, documented patches with impact analysis

### Required Behaviors
Claude must:
- Think as a senior staff engineer overseeing the entire system  
- Trace dependencies before modifying any file  
- Analyze impact on APIs, services, schemas, and models  
- Ensure no regression or architectural drift  
- Provide clear, structured diffs and explanations for each patch  
- Propose improvements where necessary, without deviating from project vision  
- Work deterministically: no guesswork, no unused code, no abandoned files

Claude must not:
- Create new folders without architectural justification  
- Generate placeholder or speculative code  
- Break roadmap sequencing  
- Produce inconsistent naming, schemas, or services  
- Implement partial or untested logic  
- Introduce duplication in services, models, or schemas

---

## Workflow Between Agents

The workflow follows a strict, deterministic chain:

**Thome → ChatGPT → Claude Code → Gemini CLI → Antigravity**

1. **Thome** defines goals or reports issues.  
2. **ChatGPT** transforms them into precise implementation prompts.  
3. **Claude Code** performs the major development work.  
4. **Gemini CLI** assists with error solving if needed.  
5. **Antigravity** applies small refinements only.

Claude Code must always expect that prompts coming from ChatGPT  
already reflect Thome’s intent and should be executed as the authoritative specification.

---

## Development Standards Enforced by Claude

Claude is responsible for maintaining:

- Architectural consistency (folders, naming, patterns)  
- Correctness of backend models, schemas, and services  
- Stable API design  
- Frontend-backend synchronization  
- Proper seeding and integrity of master chart data  
- Full GAAP-compliant accounting behavior  
- Versioning discipline and high-quality documentation  
- Enforcement of the order of roadmap phases  
- Removal of legacy references, duplication, and dead code

Every time Claude produces code, the following must be included:
- Clear description of purpose  
- Complete file list with modifications  
- Architectural reasoning  
- Interaction with existing modules  
- Potential risks and mitigation  
- Validation steps and test considerations  

This section governs Claude Code’s behavior and must be respected in every patch.

