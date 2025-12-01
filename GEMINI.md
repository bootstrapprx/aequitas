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
