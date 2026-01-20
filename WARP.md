# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**Aequitas** is a constitutional accounting system featuring a React frontend, FastAPI backend, and PostgreSQL database. The system is governed by canonical documents (Constitution) that define immutable accounting principles. Code must conform to these principles—if they conflict, the code is wrong.

## Development Commands

### Docker Environment (Recommended)
```bash
# Start full stack (Postgres, Ollama, Backend, Frontend)
make dev

# Start without rebuilding images
make dev-cached

# Stop all services
make stop

# View logs
make logs

# Complete reset (dangerous - removes all data)
make reset

# Reset only database
make reset-db

# Rebuild containers without cache
make rebuild
```

**Service URLs when running:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Ollama (AI): http://localhost:11435
- Postgres: localhost:5432

### Backend Development

**Testing:**
```bash
cd backend
python -m pytest                    # Run all tests
python -m pytest tests/test_*.py    # Run specific test file
python -m pytest -v                 # Verbose output
python -m pytest -k "test_name"     # Run tests matching pattern
```

**CLI Installation & Usage:**
```bash
cd backend
pip install -e .                    # Install CLI locally

# CLI examples
aequitas companies list             # List all companies
aequitas groups create "My Group"   # Create company group
aequitas db upgrade                 # Run migrations
aequitas diag health                # System health check
aequitas mappings propagate -s SRC -g GRP  # Propagate mappings

# Docker shortcut (when using containers)
./aq companies list                 # Equivalent to docker compose exec backend python -m cli.main
```

**Local Development (without Docker):**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start dev server
npm run build        # Production build
npm run lint         # Run linter
```

**Local development (without Docker):**
```bash
cd frontend
npm install
npm run dev          # Runs on http://localhost:5173
```

### Dependency Management

**Docker workflow (recommended):**
```bash
make rebuild         # Handles all dependency updates in containers
```

**Local IDE support (for TypeScript/Python autocomplete):**
```bash
make install-deps              # Install all local dependencies
make install-frontend          # Frontend only
make install-backend           # Backend only
make reinstall-deps            # Clean and reinstall all
```

## High-Level Architecture

### Constitutional Foundation

Aequitas is governed by canonical documents in `governance/canon/`:
- **CANON_I**: Accounting Truth & Structure (double-entry, GAAP, immutability)
- **CANON_II**: Authority & Power (permissions, ownership, multi-tenancy)
- **CANON_III**: Evolution & State (state machines, audit trails, versioning)
- **CANON_IV**: Intelligence & Guidance (AI roles, disclaimers, observer mode)
- **Kernel 2025.2**: Current frozen accounting kernel (20 L0 accounts, 35 L1 accounts)

**Core Principle:** Code is the executive branch that enforces canonical law. When code conflicts with Canon, the code is wrong.

### Backend Architecture (`backend/app/`)

**Layered Architecture:**
- `api/v1/`: API routes and endpoints (thin handlers)
- `services/`: Business logic layer (called by API routes)
- `db/`: Database models and session management
- `core/`: Configuration, security, UCID generation, error handling
- `cli/`: Administrative CLI tool (Typer-based)

**Key Backend Concepts:**

1. **UCID (Unique Company ID)**: 4-character hash generated from normalized company name (`backend/app/core/ucid.py`)
2. **Database Session**: Always use `get_db()` dependency injection in routes
3. **Master Chart**: 345-account US-GAAP chart in `backend/app/data/`
4. **Service Layer Pattern**: Business logic lives in `services/`, not in route handlers
5. **Canonical Error Envelope**: All errors follow AEQ error format with `code`, `message`, `details`, `request_id`, `correlation_id`

**Authentication:**
- JWT-based with Bearer tokens
- Default superuser: `admin@aequitas.local` / `admin123` (change immediately)
- Roles: Superuser, Admin, User

**API Structure:**
- Base prefix: `/api/v1`
- Major endpoints: `/companies`, `/masterchart`, `/organizer`, `/journal-entries`, `/fiscal`, `/groups`, `/mappings`

### Frontend Architecture (`frontend/src/`)

**Structure:**
- `pages/`: Page components organized by module (dashboard, registration, accountancy, reports, admin, groups)
- `components/`: Reusable components including Athenaeum theme components
- `lib/api.ts`: Centralized API client with error handling
- `contexts/AuthContext.tsx`: Authentication provider

**Key Frontend Concepts:**

1. **API Client** (`lib/api.ts`): Handles requests, auto-injects JWT tokens, parses canonical error envelopes
2. **Athenaeum Theme**: Classical "Digital Athenaeum of Finance" UI with marble textures, gold accents, animated components (`components/athenaeum/`)
3. **Themed Pages**: "Scribe's Chamber" (Journal), "Hall of Balance" (Trial Balance), "Auditor's Tower" (Statements)

**Tech Stack:**
- React 18 + TypeScript
- Vite for dev/build
- Tailwind CSS + shadcn/ui components
- TanStack Query for data fetching
- Framer Motion for animations
- React Router for navigation

### Database Layer

**Models** (`backend/app/db/models/`):
- Core: `Company`, `CompanyAccount`, `MasterAccount`, `User`, `UserCompany`
- Accounting: `FiscalPeriod`, `JournalEntry`, `JournalEntryLine`, `AccountBalance`
- Groups: `GroupCompany`, `GroupCompanyMember`
- Mappings: `AccountMapping`
- Fiscal Engine: `EntityTaxProfile`, `TaxRuleset`, `TaxRun`, `TaxFact`
- Staging: `StagingQBOAccount`

**Enums** (`backend/app/db/models/enums.py`):
- `AccountType`, `NormalBalance`, `EntryStatus`, `PeriodStatus`, `LockedReason`

**Migrations:**
```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Accounting Engine

**Complete Accounting Cycle:**
1. Journal Entries → Daily Ledger
2. Trial Balance by period
3. Fiscal Period management (open/closed/locked states)
4. Financial Statements (Balance Sheet, Income Statement, Cash Flow)

**Key Services:**
- `journal_entry_service.py`: Create, post, void, delete entries
- `ledger_service.py`: Daily journal management
- `fiscal_period_service.py`: Period CRUD and state transitions
- `financial_statement_service.py`: Report generation

**Immutability Rules:**
- Posted journal entries cannot be edited (only voided)
- Closed fiscal periods enforce "Points of No Return"
- All critical actions are audit-logged

### AI Integration

**Dexter - AI Accounting Assistant:**
- Runs in **Observer Mode** (read-only)
- Provides advisory intelligence, not commands
- Located in: `backend/app/services/dexter/`

**AI Providers:**
- **Ollama** (local, private): http://localhost:11435 in dev
- **Cloudflare Workers AI** (edge-based): Configured via env vars

**Organizer AI:**
- Automatic account classification and mapping
- Located in: `backend/app/services/organizer_ai/`

## Key Development Patterns

### Adding a New API Route

1. Create route file in `backend/app/api/v1/my_module.py`
2. Define router: `router = APIRouter()`
3. Implement business logic in `backend/app/services/my_module_service.py`
4. Use dependency injection: `db: Session = Depends(get_db)`
5. Include router in `backend/app/main.py`

### Error Handling

All errors should use the canonical AEQ error envelope:
```python
from app.core.errors import AequitasError

raise AequitasError(
    code="AEQ_CUSTOM_ERROR",
    message="User-friendly message",
    details={"additional": "context"}
)
```

### UCID Generation

Always use `generate_ucid()` for new companies:
```python
from app.core.ucid import generate_ucid

ucid = generate_ucid("Acme Corp Inc")  # Returns 4-char hash
```

### Database Sessions

**In routes:**
```python
from app.db.session import get_db

@router.get("/")
def my_route(db: Session = Depends(get_db)):
    # db is auto-managed
    pass
```

**In tests:**
```python
from app.db.session import SessionLocal

db = SessionLocal()
try:
    # test code
finally:
    db.close()
```

### Frontend API Calls

```typescript
import { api } from '@/lib/api';

// GET request
const data = await api.get<MyType>('/endpoint');

// POST with body
const result = await api.post<ResultType>('/endpoint', { key: 'value' });

// Error handling
try {
  await api.post('/endpoint', data);
} catch (error) {
  if (error instanceof ApiError) {
    console.error(error.code, error.getUserMessage());
  }
}
```

## Important Constraints

### Canonical Compliance

1. **Never mutate Canon documents** without explicit user authorization
2. **Master Chart is versioned**, not mutable
3. **Kernel 2025.2 is frozen** - any changes require new kernel version
4. **Double-entry bookkeeping is inviolable** - debits must equal credits
5. **Posted entries are immutable** - use void/remediation, not deletion

### Security & Permissions

1. **Multi-tenancy**: All queries must filter by `company_id` or use permission checks
2. **Permission Service**: Use `backend/app/services/permission_service.py` for authorization
3. **No "God Mode"**: Audit trails cannot be bypassed
4. **JWT required**: All protected endpoints check `Authorization: Bearer <token>`

### Service Layer Separation

1. Business logic → `services/`
2. Route handlers → `api/v1/` (thin, delegate to services)
3. Database models → `db/models/`
4. No business logic in route handlers

### Testing Requirements

1. Add tests for new services: `backend/tests/`
2. Run pytest before committing
3. Test both success and error cases
4. Use canonical error codes in tests

## Integration & External Services

**QuickBooks Online:**
- OAuth2-based sync
- Env vars: `QBO_CLIENT_ID`, `QBO_CLIENT_SECRET`, `QBO_REDIRECT_URI`
- Environment: `QBO_ENVIRONMENT=sandbox` (or `production`)

**Cloudflare Workers AI:**
- Env vars: `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`
- Provider setting: `AI_PROVIDER=cloudflare`

**Ollama:**
- Runs in Docker container at `http://localhost:11435`
- Env vars: `OLLAMA_HOST`, `OLLAMA_MODEL`

## Files to Reference When Making Changes

**Configuration & Startup:**
- `backend/app/main.py` - FastAPI app, router includes, startup logic
- `backend/app/core/config.py` - Settings and environment variables
- `backend/app/db/session.py` - Database session management

**Canonical Documents:**
- `governance/canon/README.md` - Start here for constitutional overview
- `governance/canon/CANON_I_ACCOUNTING_TRUTH.md` - Accounting principles
- `governance/canon/kernels/kernel_2025.2.md` - Current frozen kernel

**Frontend Integration:**
- `frontend/src/lib/api.ts` - API client
- `frontend/src/contexts/AuthContext.tsx` - Authentication state

**Data Models:**
- `backend/app/db/models/` - All database models
- `backend/app/schemas/` - Pydantic schemas for validation

## Environment Setup

**Backend `.env` (in `backend/.env`):**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/aequitas_dev
SECRET_KEY=your-secret-key
OLLAMA_HOST=http://localhost:11435
OLLAMA_MODEL=llama2
DEFAULT_SUPERUSER_EMAIL=admin@aequitas.local
DEFAULT_SUPERUSER_PASSWORD=admin123
```

**Frontend `.env` (in `frontend/.env`):**
```env
VITE_API_URL=http://localhost:8000/api/v1
```

## Athenaeum Theme Components

The Athenaeum theme (`frontend/src/components/athenaeum/`) provides:
- `PageHeader`: Classical headers with embossed gold text
- `AtheneumCard`: Marble-textured cards with hover effects
- `WaxSealBadge`: Animated status indicators (approved, rejected, pending, locked)
- `ScrollUnfurl`: Ancient scroll animations for reports
- `QuillIcon`: Animated quill for writing operations

**Usage:** Import from `@/components/athenaeum/` and follow existing patterns in `pages/accountancy/`.

## CLI Command Reference

```bash
# Companies
aequitas companies list
aequitas companies create "Company Name"
aequitas companies delete <company_id>

# Groups
aequitas groups list
aequitas groups create "Group Name"
aequitas groups add-company <group_id> <company_id>

# Mappings
aequitas mappings list -c <company_id>
aequitas mappings propagate -s <source_company> -g <group_id>

# Database
aequitas db upgrade              # Run migrations
aequitas db downgrade            # Rollback migration
aequitas db current              # Show current revision

# Diagnostics
aequitas diag health             # System health check
aequitas diag check-chart        # Verify master chart integrity

# Logs
aequitas logs view               # View recent logs
aequitas logs export -o file.txt # Export logs
```

## Project-Specific Conventions

1. **UCID**: Companies use 4-character UCID (not UUID or sequential IDs)
2. **Master Chart**: 345 accounts, 7 headers + 338 details, IFRS/US-GAAP compliant
3. **Kernel Layers**: L0 (20 accounts, required), L1 (35 accounts, GAAP standard), L2 (20 accounts, simplified)
4. **No Inline Secrets**: Use environment variables, never commit secrets
5. **Deterministic Patches**: Code changes should be well-scoped and include validation steps
6. **Co-Author Commits**: Include `Co-Authored-By: Warp <agent@warp.dev>` in commit messages

## Port Usage

- **5173**: Frontend (Vite dev server)
- **8000**: Backend (FastAPI)
- **5432**: PostgreSQL
- **11435**: Ollama (AI inference)
- **1420**: Metatheos GUI (governance system)

## Additional Resources

- **Master Chart Guide**: `MASTER_CHART.md`
- **Technical Report**: `docs/technical_report.md`
- **Governance**: `governance/README.md`, `governance/aequitas_roadmap.md`
- **Constitution**: `governance/canon/README.md`
- **GitHub Copilot Instructions**: `.github/copilot-instructions.md`
