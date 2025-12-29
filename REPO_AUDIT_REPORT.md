# Repository State Report

## 1. Implemented Features (Evidence for Goals)
| Feature / Component | Status | Location (File/Dir) | Notes |
| :--- | :--- | :--- | :--- |
| **Auth** | ✅ Done | `backend/app/api/v1/auth.py`, `backend/app/api/v1/oauth.py` | Uses OAuth (Google) + standard JWT flow. Models: `User`, `OAuthAccount`. |
| **Onboarding** | ✅ Done | `backend/app/api/v1/onboarding.py`, `frontend/src/pages/onboarding/` | Massive module. Includes `companies`, `settings`, `chart` setup. |
| **Accounting Core** | ✅ Done | `backend/app/api/v1/accounting.py`, `backend/app/db/models/journal_entry.py` | Full double-entry engine. Journals, Fiscal Periods, Master/Company Charts. |
| **Dexter (AI)** | ✅ Done | `backend/app/api/v1/dexter.py`, `backend/app/api/v1/dexter_observer.py` | "Observer" and "Onboarding" AI agents present. |
| **Companies** | ✅ Done | `backend/app/api/v1/companies.py`, `frontend/src/pages/Companies.tsx` | Multi-tenant structure initiated. Groups and Companies supported. |
| **Integrations** | 🚧 WIP | `backend/app/api/v1/integrations/`, `backend/app/api/v1/qbo.py` | QBO integration exists but flagged as one of few. Others missing. |
| **Admin** | ✅ Done | `backend/app/api/v1/admin.py`, `frontend/src/pages/admin/` | Superuser controls present. |
| **Invoicing** | ❌ Missing | - | No dedicated module found in backend or frontend. |
| **Contracts** | ❌ Missing | - | No dedicated module found. |
| **Inventory** | ❌ Missing | - | No dedicated module found. |
| **Payroll** | ❌ Missing | - | No dedicated module found. |

## 2. Technical Stack & Decisions (For 04_DECISIONS)
- **Language/Framework**: Python 3.11+ / FastAPI
- **Database**: Postgres 16 (via Docker)
- **ORM**: SQLAlchemy 2.0+ (No SQLModel found, standard SQLAlchemy models used)
- **Frontend**: React 18 + Vite + Tailwind CSS + Radix UI
- **State Management**: React Context (`AuthContext`, `CompanyContext`). No global store like Redux seen.
- **Auth Provider**: Custom implementation using identifiers + Google OAuth (`google-auth`, `authlib`). Not Clerk/Auth0. Codebase owns identity.

## 3. Infrastructure
- [x] Docker: Yes (`docker-compose.dev.yml`, `Dockerfile`)
- [ ] CI/CD: No (`.github/workflows` does not exist)
- [x] Makefiles: Yes (Extensive `Makefile` for dev, up, reset-db)

## 4. Key Files Manifest
1. `backend/app/main.py` (App Entry)
2. `backend/app/api/v1/accounting.py` (Core Logic)
3. `backend/app/api/v1/journal_entries.py` (Core Logic)
4. `backend/app/db/models/journal_entry.py` (Core Model)
5. `backend/app/api/v1/companies.py` (Tenancy)
6. `backend/app/api/v1/onboarding.py` (Critical Flow)
7. `backend/app/api/v1/auth.py` (Security)
8. `backend/app/api/v1/dexter.py` (AI Agent)
9. `backend/app/db/models/company.py` (Tenancy Model)
10. `backend/app/db/models/user.py` (Identity Model)
11. `frontend/src/App.tsx` (Router/Entry)
12. `frontend/src/pages/Dashboard.tsx` (Main View)
13. `frontend/src/pages/Companies.tsx` (Tenancy View)
14. `frontend/src/pages/accountancy/journal/JournalEntriesPage.tsx` (Core UI)
15. `frontend/src/contexts/AuthContext.tsx` (State)
16. `frontend/src/contexts/CompanyContext.tsx` (State)
17. `backend/app/db/base.py` (DB Config)
18. `backend/app/api/v1/integrations/qbo.py` (Integration)
19. `frontend/package.json` (FE Deps)
20. `backend/requirements.txt` (BE Deps)
