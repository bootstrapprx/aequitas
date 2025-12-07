# Aequitas Code Project

## Project Overview

**Aequitas** is a complete accounting system featuring intelligent chart of accounts management (powered by ChartForge), financial reporting, and integrated bookkeeping. Built with a modern React frontend and powerful FastAPI backend, Aequitas provides a seamless experience for managing your company's financial operations.

**Frontend:**
- **Framework:** React 18 with TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS with shadcn/ui component library
- **Data Fetching:** Tanstack Query
- **Routing:** React Router

**Backend:**
- **Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Authentication:** JWT-based authentication
- **AI Features:**
    - Local AI with Ollama
    - Cloud AI with Cloudflare Workers AI

**DevOps:**
- **Containerization:** Docker & Docker Compose, Nginx, Cloudflare Tunnel
- **CI/CD:** GitHub Actions
- **Repository:** [https://github.com/bootstrapprx/Aequitas](https://github.com/bootstrapprx/Aequitas)

## Building and Running

### Docker (Recommended)

1.  **Start all services:**
    ```bash
    make dev
    ```

2.  **Access the application:**
    - Frontend: http://localhost:5173
    - Backend API: http://localhost:8000
    - API Documentation: http://localhost:8000/docs

3.  **Stop all services:**
    ```bash
    make stop
    ```

4.  **Reset the database:**
    ```bash
    make reset-db
    ```

5.  **View logs:**
    ```bash
    make logs
    ```

## Debugging & Session Stability

To ensure a stable development environment and create "stable points of return," follow this workflow before making significant changes:

1.  **Review Last Session:**
    Before starting new work, check the logs from the previous session to ensure it ended cleanly and identify any unaddressed errors.
    ```bash
    # Check for script errors
    cat dev_sessions/latest/errors.txt
    
    # Check for backend/db crashes or critical failures
    cat dev_sessions/latest/docker_stream.log
    
    # Review browser console logs (captured via backend)
    grep "[CLIENT-LOG]" dev_sessions/latest/docker_stream.log
    ```

2.  **Verify Clean State:**
    If the previous session was unstable (e.g., containers stuck, DB locked), perform a full reset to return to a known good state:
    ```bash
    make reset
    ```

3.  **Start Logged Session:**
    Always work inside a tracked session to capture your new changes and interactions:
    ```bash
    make session
    ```

4.  **Stop & Save:**
    Type `exit` or press `Ctrl+D` to cleanly stop the session. This triggers log rotation and ensures your session artifacts are saved as a reference integration point.

### Local Development

#### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

## Development Conventions

- **Linting:**
    - **Frontend:** `pnpm lint` in the `frontend` directory.
- **Testing:**
    - **Backend:**
        ```bash
        cd backend
        python3 -m venv venv
        source venv/bin/activate
        python3 -m pip install -r requirements.txt
        python3 -m pip install -r requirements-dev.txt
        pytest
        ```
    - **Frontend:**
        - TODO: No testing commands were found.

## Database Schema

The database schema is defined using SQLAlchemy in the `backend/app/db/models` directory. Here are some of the key models:

-   **User:** Represents a user of the system.
    -   Has a many-to-many relationship with the `Company` model through the `UserCompany` association table.
-   **Company:** Represents a company that is being managed by the system.
    -   Has a one-to-many relationship with the `CompanyAccount` model.
    -   Has a many-to-many relationship with the `User` model through the `UserCompany` association table.
-   **CompanyAccount:** Represents a single account in a company's chart of accounts.
    -   Belongs to a single `Company`.
-   **MasterAccount:** Represents a single account in the master chart of accounts.
-   **AccountMapping:** Represents the mapping between a company account and a master account.
-   **UserCompany:** A many-to-many table that links users and companies.
-   **QBOToken:** Stores OAuth2 tokens for QuickBooks Online integration.
-   **Snapshot:** Stores a snapshot of a company's chart of accounts at a particular point in time.
-   **Template:** Stores a reusable chart of accounts template.
-   **AuditLog:** Stores a log of all actions that are performed in the system.
-   **SystemSettings:** Stores system-wide settings.
-   **OrganizerMemory:** Stores the memory of the AI organizer.
-   **OrganizerRules:** Stores the rules that are used by the AI organizer.
-   **Embedding:** Stores embeddings for the AI organizer.
-   **UserDatabaseConfig:** Stores database configurations for users.

THE NEXT SECTIONS ARE THE USER NOTES - DO NOT DELETE

# Aequitas — Unified AI Development Team  
### Human + AI Architecture & Operational Protocol

Aequitas is built by a hybrid development team composed of one human architect and multiple specialized AI systems.  
This document defines the **roles, hierarchy, responsibilities, and collaboration rules** for every member of the team.

It ensures clarity, prevents role overlap, increases development velocity, and maintains architectural discipline across the entire project.

---

# 1. Team Hierarchy (Chain of Command)

**1. Thome — Chief Architect & Project Owner**  
**2. Claude Code — Lead AI Developer (Tech Lead)**  
**3. ChatGPT — Prompt Architect & Development Strategist**  
**4. Gemini CLI — Debugging & Diagnostics Specialist**  
**5. Antigravity — Micro-Editor for Safe Localized Edits**

This hierarchy must be respected during all development activity.  
No agent may operate outside its designated scope.

---

# 2. Role Definitions

## 2.1 Thome — Chief Architect & Project Owner
Thome provides:
- System vision and strategic direction  
- High-level requirements  
- Roadmap decisions  
- Final approval on architecture and design  
- Prioritization of tasks and features  

Thome is the **origin of all intent** within the project.

All agents operate in service of this vision.

---

## 2.2 Claude Code — Lead AI Developer (Tech Lead)
Claude holds **technical authority** over the entire AI team.

Responsible for:
- Major feature development  
- Architectural design  
- Multi-file changes  
- Backend & frontend structural decisions  
- GAAP-compliant accounting engine  
- Mapping engine and ChartForge integration  
- Code consolidation and refactoring  
- Ensuring roadmap order is respected  
- Reviewing and redirecting tasks for other agents  

Claude is the **chief engineer** of Aequitas.

No other AI may modify architecture without Claude's approval.

---

## 2.3 ChatGPT — Prompt Architect & Development Strategist
ChatGPT acts as Thome’s **interpreter, planner, and systems strategist**.

Responsibilities:
- Convert Thome’s ideas into clear, detailed prompts  
- Break down large tasks into technical specifications  
- Predict missing requirements  
- Assist Claude with architectural planning  
- Provide debugging reasoning and design clarification  
- Maintain continuity and project awareness  

ChatGPT is the **second-in-command** after Claude in matters of development structure.

---

## 2.4 Gemini CLI — Debugging & Diagnostics Specialist
Gemini is used **exclusively for problem solving**.

Responsibilities:
- Analyze errors, logs, crashes, and unexpected behavior  
- Provide surgical fixes for isolated issues  
- Investigate backend, frontend, Docker, and DB problems  
- Confirm integrity after critical failures  
- Assist Claude by unblocking technical roadblocks  

Gemini must **never**:
- Modify architecture  
- Implement features  
- Perform refactors  
- Create multi-file patches  

Gemini is the **forensic analyst** of Aequitas.

---

## 2.5 Antigravity — Micro-Editor for Safe, Localized Edits
Antigravity performs **tiny, risk-free file edits**.

Allowed:
- Typos, formatting, spacing  
- One-line adjustments  
- Text changes in UI  
- Comments, readability improvements  
- Micro CSS/Tailwind tweaks  

Prohibited:
- Any structural or logical change  
- Multi-file modifications  
- Feature implementations  
- Backend logic or data layer adjustments  

Antigravity is the **precision scalpel**, used only for finishing touches.

---

# 3. Operational Workflow

The Aequitas workflow is deterministic and structured:

Thome → ChatGPT → Claude Code → Gemini CLI → Antigravity


### Meaning:
- **Claude** decides if a task is structural (Claude) or auxiliary (Gemini / Antigravity).  
- **Gemini** resolves errors and system failures.  
- **Antigravity** performs cosmetic or minor code edits.  
- Neither Gemini nor Antigravity may initiate changes.  

---

# 4. When to Use Each Agent

### ✔ Use Gemini CLI when:
- Something is broken  
- Errors appear in logs or terminal  
- The backend crashes  
- Docker refuses to start  
- The frontend throws hydration/build/runtime errors  
- A dependency conflict appears  
- An environmental configuration is failing  

Gemini identifies root causes and may propose a safe patch.

---

### ✔ Use Antigravity when:
- There is a typo in code or UI  
- A spacing or formatting fix is needed  
- A small label or className must be corrected  
- A tiny front-end or back-end adjustment is needed  
- A comment or small block must be rewritten  

Antigravity never touches logic.

---

# 5. Interaction Rules

### Gemini CLI:
- Acts only when invoked  
- Provides detailed reasoning behind errors  
- Generates localized fixes (if safe)  
- Escalates architectural needs to Claude  

### Antigravity:
- Applies changes exactly as requested  
- Never modifies behavior or structure  
- Produces minimal diffs with no side effects  

---

# 6. Summary Table

| Agent | Purpose | Allowed | Forbidden |
|-------|----------|---------|-----------|
| **Gemini CLI** | Debugging, diagnostics | Isolated fixes, error resolution | Architecture, multi-file changes, features |
| **Antigravity** | Minor edits, formatting | One-file cosmetic tweaks | Logic, architecture, refactors |

---

# 7. Closing Note

Gemini CLI and Antigravity are **support tools**, not development leads.  
They exist to keep the project stable and maintain flow, while Claude Code remains the architect and primary developer.

This document governs both agents and replaces any separate GEMINI.md or Antigravity documents.
