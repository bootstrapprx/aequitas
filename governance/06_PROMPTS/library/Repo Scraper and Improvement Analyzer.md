---
type: prompt
id: PROMPT_REPO_SCRAPER
agent: Codex
purpose: repository reality extraction
origin: governance audit
status: active
---

# PROMPT: Repo Progress Extractor

## Target Agent
- An agent with direct access to the `aequitas` software repository/codebase.

## Context
We are managing a project via an Obsidian Vault ("The Governance Layer"). However, the Codebase may be ahead of the Vault. We need to "scrape" the reality of the code to update our Roadmap, Goals, and Decisions logs.

## Objective
Scan the entire codebase to determine **what has actually been built**. 
Your output will be used to update the `00_MASTER/Aequitas Roadmap Master.md` and backfill `03_GOALS_EPICS` and `04_DECISIONS`.

## Execution Steps

### 1. Feature Extraction (What exists?)
Scan `backend/` and `frontend/` for implemented features. Look for:
- **Modules**: defined folders in `backend/app/modules` or similar.
- **Endpoints**: functional API routes in `routers`.
- **UI Pages**: functional pages in `frontend/src/pages`.
- **Data Models**: defined SQLModel/Pydantic schemas.

Distinguish between:
- ✅ **Implemented**: Code exists, logic is written, tests might exist.
- 🚧 **Skeleton/WIP**: Files exist but contain `pass`, `TODO`, or just types without logic.
- ❌ **Missing**: Referenced in imports but not found.

### 2. Architectural Decision Extraction (How does it work?)
Identify the patterns used. We need to log these as "Decisions".
- **Auth**: What library/method? (e.g., Clerk, NextAuth, homegrown JWT).
- **Database**: ORM used? Migration tool? (e.g., SQLAlchemy, Alembic).
- **Frontend State**: Redux? Context? Zustand?
- **Structure**: Monolith? Microservices? Modular Monolith?

### 3. Verification Scrape
- List all `test` folders and what they cover.
- Do we have a `Dockerfile` or `docker-compose.yml`? What services satisfy the `make up` command?

## Output Format Required
Please provide a report in the following strict Markdown format:

```markdown
# Repository State Report

## 1. Implemented Features (Evidence for Goals)
| Feature / Component | Status | Location (File/Dir) | Notes |
| :--- | :--- | :--- | :--- |
| e.g., User Login | ✅ Done | `backend/auth/` | Uses OAuth2 |
| e.g., Invoicing | 🚧 WIP | `backend/modules/invoice/` | Models only, no logic |

## 2. Technical Stack & Decisions (For 04_DECISIONS)
- **Language/Framework**: [e.g. Python 3.11 / FastAPI]
- **Database**: [e.g. Postgres 16]
- **ORM**: [e.g. SQLModel]
- **Frontend**: [e.g. React + Vite + Tailwind]
- **Auth Provider**: [e.g. Google OAuth via libraries]

## 3. Infrastructure
- [ ] Docker: [Yes/No]
- [ ] CI/CD: [Github Actions?]
- [ ] Makefiles: [Yes/No]

## 4. Key Files Manifest
- List the top 20 most important/large files that define the system's logic. (Exclude lockfiles/configs).
```

## Definition of Done
The user can read your report and immediately check off items in their `03_GOALS_EPICS` folder and update the `00_MASTER/Aequitas Roadmap Master.md` with high confidence.
