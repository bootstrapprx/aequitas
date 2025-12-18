

## 🔴 PROMPT FOR GEMINI — PROD-GRADE BOOTSTRAP (DO NOT DEVIATE)

**Role:**
You are a senior DevOps / Backend engineer working on a FastAPI + SQLAlchemy + Alembic + Docker SaaS application called **Aequitas**.

You must implement a **production-grade bootstrap mechanism** that guarantees the application **never starts without migrations and required seeds applied**.

Do NOT propose alternatives.
Do NOT ask questions.
Implement the solution described below exactly.

---

## CONTEXT

* The backend runs inside Docker via `make dev` and `docker-compose`.
* Currently, the application starts **without guaranteeing**:

  * Alembic migrations are applied
  * Master Chart of Accounts is seeded
  * Default Fiscal RuleSets are seeded

This causes logical failures even though the app appears “up”.

This is unacceptable for a SaaS system.

---

## OBJECTIVE (MANDATORY)

Implement a **single bootstrap pipeline** that runs **inside the backend container** and guarantees, on every startup:

1. Database is reachable
2. Alembic migrations are applied (`upgrade head`)
3. Idempotent seeds are executed:

   * Master Chart of Accounts
   * Default Fiscal RuleSet (`2025.1`)
4. Only after all the above succeed, the FastAPI app starts

If any step fails, the container must fail fast.

---

## REQUIRED ARCHITECTURE (NON-NEGOTIABLE)

### 1️⃣ Create a bootstrap script

Create a new file:

```
backend/scripts/bootstrap.py
```

This script must:

* Wait for PostgreSQL to be available
* Run Alembic migrations programmatically
* Run idempotent seed functions
* Exit with non-zero code on failure

### Required responsibilities (exact):

```text
- wait_for_db()
- run_alembic_migrations()
- seed_master_chart()
- seed_default_fiscal_ruleset()
```

Seeds MUST be idempotent (safe to run multiple times).

---

### 2️⃣ Alembic integration

* Use `alembic.config.Config`
* Use `alembic.command.upgrade(cfg, "head")`
* Assume `alembic.ini` already exists

No shell calls (`subprocess`) allowed.

---

### 3️⃣ Seed logic

* Master chart seed:

  * Must NOT reinsert if data already exists
  * Must log what it did (inserted / skipped)

* Fiscal ruleset seed:

  * Ensure a ruleset with:

    * version = `"2025.1"`
    * scope = `"PASS_THROUGH_BASE"`
  * Create only if missing

---

### 4️⃣ Dockerfile modification (MANDATORY)

Modify the backend Dockerfile so that:

```dockerfile
CMD python backend/scripts/bootstrap.py && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The application **must not start** if bootstrap fails.

---

### 5️⃣ docker-compose compatibility

* Do NOT change docker-compose semantics
* Backend container must depend on DB
* Assume DB has a healthcheck or basic readiness

---

## CONSTRAINTS

You MUST NOT:

* Require manual commands after `make dev`
* Require developers to remember to run migrations
* Put migration logic inside FastAPI startup events
* Use shell scripts for migrations
* Break existing environments

This must be **CI-safe**, **prod-safe**, and **idempotent**.

---

## OUTPUT FORMAT

Return:

1. `backend/scripts/bootstrap.py` (full code)
2. Dockerfile diff (only the relevant lines)
3. Any small helper function needed (if applicable)
4. Short explanation (≤ 10 lines)

Do NOT include opinions.
Do NOT include alternatives.
Do NOT mention “other approaches”.

---

## DEFINITION OF DONE

After this change:

```bash
make dev
```

Is sufficient to guarantee:

* DB schema is correct
* Master Chart exists
* Fiscal Engine ruleset exists
* Backend starts in a valid logical state

This is a **production-grade requirement**, not a dev convenience.

---

If you want, after Gemini finishes, paste the output here and I’ll **audit it line-by-line** before you apply it.
