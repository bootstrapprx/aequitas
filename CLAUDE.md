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

### Working with the Standardized Master Chart

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

## Athenaeum Theme & Recent Transformations

### Overview

Aequitas features a "Digital Athenaeum of Finance" theme throughout its frontend, combining classical architecture metaphors with modern accounting functionality. The interface uses marble textures, gold accents, ancient manuscript aesthetics, and micro-interactions to create an immersive experience.

### Five-Phase Transformation (Completed)

The project underwent a comprehensive 5-phase transformation to consolidate architecture and apply the Athenaeum theme:

#### Phase 1: Foundation Fixes
- Removed duplicate and conflicting service implementations
- Consolidated mapping services into single source of truth
- Fixed broken imports and circular dependencies
- Cleaned up unused code and legacy references

#### Phase 2: Master Chart Normalization and Validation
- Standardized master chart data structure across all sources
- Implemented comprehensive validation for chart of accounts data
- Enhanced US-GAAP master chart with proper hierarchical codes
- Added data integrity checks and seeding scripts

#### Phase 3: Mapping Engine Consolidation
- Unified account mapping logic into `backend/app/services/mapping_service.py`
- Integrated AI-powered mapping suggestions (Ollama/Cloudflare)
- Added semantic search support with pgvector
- Implemented blended AI + vector similarity recommendations
- Removed duplicate chart/mapping services from frontend

#### Phase 4: Accounting Engine Integration
- Connected all accounting APIs to frontend pages
- Created fiscal period management UI (`/accountancy/fiscal-periods`)
- Completed accounting cycle: journal entries → ledger → trial balance → financial statements
- Added fiscal period CRUD operations with open/closed/locked states
- Ensured GAAP-compliant double-entry validation throughout

#### Phase 5: Athenaeum Theme Application
- Created reusable Athenaeum component library
- Applied classical theme to all core accounting pages
- Implemented micro-interactions and animations
- Transformed page headers with themed titles

### Athenaeum Component Library

Located in `frontend/src/components/athenaeum/`:

**1. PageHeader** (`PageHeader.tsx`)
```typescript
<PageHeader
  title="Scribe's Chamber"
  subtitle="Record transactions in the ledger with ancient precision"
  icon={Feather}
  actions={<Button>New Entry</Button>}
/>
```
- Classical page headers with embossed gold text
- Animated icon rotation on mount
- Decorative manuscript line separator
- Support for action buttons

**2. AtheneumCard** (`AtheneumCard.tsx`)
```typescript
<AtheneumCard hover glow>
  <AtheneumCardHeader icon={<Icon />} embossed>Title</AtheneumCardHeader>
  <AtheneumCardContent>Content here</AtheneumCardContent>
</AtheneumCard>
```
- Marble-textured cards with classical styling
- Props: `hover`, `glow`, `ornate`, `parchment`, `animate`
- Replaces standard shadcn Card component
- Column pattern overlays for architectural aesthetic

**3. WaxSealBadge** (`WaxSealBadge.tsx`)
```typescript
<WaxSealBadge type="approved" size="sm" />
```
- Animated wax seal status indicators
- Types: `approved`, `rejected`, `pending`, `locked`, `unlocked`
- Stamp animation on mount
- Sizes: `sm`, `md`, `lg`

**4. ScrollUnfurl** (`ScrollUnfurl.tsx`)
```typescript
<ScrollUnfurl title="Balance Sheet" subtitle="As of Dec 31, 2024">
  <FinancialStatement data={data} />
</ScrollUnfurl>
```
- Ancient scroll unfurling animation
- Perfect for financial reports and documents
- Parchment styling with scroll rods
- Staggered delays for multiple scrolls

**5. QuillIcon** (`QuillIcon.tsx`)
```typescript
<QuillIcon isWriting={isPending} size="md" />
<QuillWritingEffect text="Record saved" delay={0.2} />
```
- Animated quill icon for writing operations
- Moves when `isWriting={true}`
- Includes text writing effect component

### Themed Page Names

Core accounting pages now have classical, theme-appropriate names:

| Route | Theme Name | Icon | Description |
|-------|------------|------|-------------|
| `/accountancy/journal` | Scribe's Chamber | Feather | Journal entry creation and management |
| `/accountancy/ledger` | Ledger of Days | Scroll | Daily journal entry ledger |
| `/accountancy/trial-balance` | Hall of Balance | Scale | Trial balance report generation |
| `/accountancy/fiscal-periods` | Chronicle of Time | Hourglass | Fiscal period lifecycle management |
| `/reports/statements` | Auditor's Tower | Scroll | Financial statements (BS, IS, CF) |

### CSS Animations & Utilities

Located in `frontend/src/index.css`:

**Custom Animations:**
- `quill-write` - Quill pen writing motion
- `scroll-unfurl` - Ancient scroll unfurling
- `wax-seal` - Wax seal stamping
- `parchment-reveal` - Parchment paper reveal
- `ink-fade` - Ink fading in
- `shimmer` - Gold shimmer effect
- `pulse-glow` - Pulsing glow for important elements
- `float` - Gentle floating animation

**Utility Classes:**
- `.parchment` - Parchment paper texture
- `.wax-seal` - Wax seal styling
- `.embossed-gold` - Embossed gold text effect
- `.ornate-border` - Classical ornate borders
- `.scrollwork` - Decorative scrollwork patterns
- `.manuscript-line` - Decorative manuscript separator
- `.ink-splash` - Ink splash decoration
- `.marble-texture` - Marble background texture
- `.shadow-gold` - Gold-tinted shadow

**Color Palette:**
- Primary: Emerald (`hsl(142 76% 36%)`)
- Accent: Gold/Bronze (`hsl(38 72% 52%)`)
- Marble: Various beige/cream tones
- Text: Dark gray on light, white on dark

**Fonts:**
- Headings: Playfair Display (classical serif)
- Body: DM Sans (modern sans-serif)

### Using Athenaeum Components

**Best Practices:**

1. **Import from barrel export:**
```typescript
import {
  PageHeader,
  AtheneumCard,
  WaxSealBadge
} from '@/components/athenaeum';
```

2. **Replace standard cards:**
```typescript
// OLD
<Card>
  <CardHeader><CardTitle>Title</CardTitle></CardHeader>
  <CardContent>Content</CardContent>
</Card>

// NEW
<AtheneumCard hover>
  <AtheneumCardHeader icon={<Icon />}>Title</AtheneumCardHeader>
  <AtheneumCardContent>Content</AtheneumCardContent>
</AtheneumCard>
```

3. **Use themed status badges:**
```typescript
// Replace Badge with WaxSealBadge for status indicators
{status === 'posted' && <WaxSealBadge type="approved" size="sm" />}
{status === 'draft' && <WaxSealBadge type="pending" size="sm" />}
{status === 'void' && <WaxSealBadge type="rejected" size="sm" />}
```

4. **Wrap reports in ScrollUnfurl:**
```typescript
<ScrollUnfurl title="Financial Report" subtitle="Q4 2024">
  <ReportContent data={data} />
</ScrollUnfurl>
```

5. **Add QuillIcon to create/edit buttons:**
```typescript
<Button onClick={handleCreate} className="shadow-gold">
  <QuillIcon isWriting={isCreating} className="mr-2" />
  New Entry
</Button>
```

### Route Structure Updates

**Accountancy Module** (`/accountancy/*`):
- `/accountancy/ledger` - Daily ledger (Ledger of Days)
- `/accountancy/journal` - Journal entries (Scribe's Chamber)
- `/accountancy/trial-balance` - Trial balance (Hall of Balance)
- `/accountancy/fiscal-periods` - Fiscal period management (Chronicle of Time) **[NEW in Phase 4]**

**Reports Module** (`/reports/*`):
- `/reports/statements` - Financial statements (Auditor's Tower)
  - Balance Sheet (wrapped in ScrollUnfurl)
  - Income Statement (wrapped in ScrollUnfurl)
  - Cash Flow Statement (wrapped in ScrollUnfurl)

### Backend Services Structure

**Consolidated Services:**

1. **MappingService** (`backend/app/services/mapping_service.py`)
   - Single source of truth for account mapping logic
   - AI-powered suggestions via Ollama/Cloudflare
   - Semantic search with pgvector
   - Blended recommendations (AI + similarity)

2. **ChartService** (`backend/app/services/chart_service.py`)
   - Master chart operations
   - Template management
   - Account normalization

3. **AccountingService** (various in `backend/app/services/`)
   - Journal entry processing
   - Ledger balance calculations
   - Trial balance generation
   - Financial statement compilation

4. **PermissionService** (`backend/app/services/permission_service.py`)
   - User permission checks
   - Company access control
   - Role-based authorization

**Removed/Consolidated:**
- Duplicate mapping services from frontend
- Conflicting chart normalization logic
- Redundant AI classification services

### Development Guidelines for Themed Pages

When creating or updating pages in the Athenaeum theme:

1. **Use PageHeader instead of custom headers**
   - Choose an appropriate classical name (e.g., "Archive of Records", "Temple of Numbers")
   - Select a relevant Lucide icon
   - Include a subtitle that explains the page's purpose

2. **Replace all Card components with AtheneumCard**
   - Add `hover` prop for interactive cards
   - Add `glow` prop for important content
   - Use `embossed` prop on headers for emphasis

3. **Use WaxSealBadge for status indicators**
   - Map application states to seal types
   - Consistent sizing across the page

4. **Add QuillIcon to writing/saving operations**
   - Set `isWriting` based on mutation state
   - Creates visual feedback for user actions

5. **Wrap reports and documents in ScrollUnfurl**
   - Use staggered delays for multiple items
   - Include meaningful titles and subtitles

6. **Apply shadow-gold class to primary buttons**
   - Maintains consistency with gold accent theme

### Architectural Improvements

**Phase 1-3 Fixes:**
- Eliminated circular dependencies between services
- Single source of truth for mapping logic
- Consolidated AI integration points
- Removed duplicate API calls
- Standardized data validation

**Phase 4-5 Enhancements:**
- Complete accounting cycle implementation
- Fiscal period lifecycle management
- Consistent theme across all pages
- Reusable component library
- Performance-optimized animations

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

