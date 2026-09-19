# Aequitas Backend Remediation Plan

> For Hermes: implement task-by-task with two-stage review: security/spec compliance first, then code-quality review.

Goal: make the Aequitas FastAPI backend safe to expose, reproducible to deploy, and consistent with the accounting and governance invariants in `governance/canon/`.

Architecture: retain the existing FastAPI + SQLAlchemy + PostgreSQL architecture, but establish explicit security dependencies at the route boundary, one authoritative Alembic migration path, and a small set of service-layer contracts for accounting mutations. Do not perform a broad rewrite while the working tree is heavily modified; make narrow, independently verifiable changes.

Tech Stack: Python 3.11, FastAPI 0.111, Pydantic Settings, SQLAlchemy 2, Alembic, PostgreSQL/pgvector, pytest, Docker Compose.

---

## Verified context and constraints

- Backend root: `backend/`.
- Application entrypoint: `backend/app/main.py`.
- Current static inventory: approximately 363 Python files and 224 FastAPI route handlers.
- The worktree is already heavily modified (over 1,100 paths). Do not reset, clean, or overwrite unrelated changes.
- The local host does not have the backend dependencies installed: `pytest`, FastAPI, SQLAlchemy, and Pydantic Settings are unavailable outside the container. Validation must therefore begin with dependency installation in an isolated environment or Docker.
- `python3 -m compileall -q app cli tests` currently passes; this proves syntax only, not importability or runtime correctness.
- `scripts/validate_imports.py` currently reports 208 import errors because the environment is missing the declared dependencies.
- Canonical constraints to preserve:
  - Backend is the final authority: `governance/canon/CANON_II_AUTHORITY_AND_POWER.md`.
  - No role may exceed its scope, including superusers.
  - Accounting truth is versioned and corrected additively, not overwritten: `CANON_I` and `CANON_III`.
  - Every critical action must be attributable, timestamped, explainable, and idempotent where applicable.

Primary evidence to address:

- `backend/app/core/config.py:17-29` has insecure defaults for `SECRET_KEY` and first-superuser credentials.
- `backend/app/main.py:68-91` permits `allow_origin_regex=r".*"` with credentials in development.
- `backend/app/main.py:222-230` returns `str(exc)` in the 500 response.
- `backend/app/main.py:105-143` performs startup DDL, seeding, and migration-related side effects; it also uses deprecated `on_event` lifecycle registration.
- `backend/app/api/v1/settings.py:16-43`, `snapshots.py:12-37`, `merge.py:10-48`, `templates.py:48-104`, `upload.py:13-46`, and `qbo.py:17-122` contain mutation or sensitive integration routes without an explicit authenticated/company-scope dependency.
- `backend/app/api/v1/client_logs.py:11-18` is unauthenticated and writes arbitrary client-supplied content to logs.
- `backend/app/api/v1/integration_jobs.py:148-256` documents that its callback is not JWT-authenticated but does not enforce an internal API key or signature.
- `backend/app/api/v1/quickbooks.py:5` imports `app.services.quickbooks_service`, which is not present in the repository inventory.
- `backend/requirements.txt` omits `python-multipart` despite `UploadFile`/`Form` and `OAuth2PasswordRequestForm` usage, and omits `stripe` despite runtime imports.
- Alembic revisions `001` through `024` contain 48 empty `upgrade()`/`downgrade()` bodies; `backend/app/db/migrate_schema.py` provides a second, ad hoc DDL path.

---

## Phase 0: establish a reproducible baseline

### Task 0.1: Preserve the current dirty-tree boundary

Files: none.

- Record `git status --short --branch` and do not include unrelated modified files in remediation commits.
- Identify the backend files changed by the implementation branch before each task.
- Never read, print, or commit `backend/.env.dev` or other credential-bearing files.

Validation:

```bash
git status --short --branch
```

Expected: the existing dirty state is recorded; no unrelated file is reverted.

### Task 0.2: Create an isolated backend validation environment

Files:

- Modify: `backend/requirements-dev.txt`
- Create or modify: `backend/pyproject.toml` (only if selected as the package-management standard)
- Create: `backend/tests/conftest.py` if fixtures are needed

- Add a reproducible development/test dependency set, including pytest, pytest-asyncio if needed, httpx compatible with the pinned FastAPI, and a test database strategy.
- Decide whether tests run against a disposable PostgreSQL/pgvector container or a transaction-isolated test database. Prefer PostgreSQL because SQLite cannot validate PostgreSQL enums, JSONB, triggers, extensions, or UUID behavior.
- Do not make application startup connect to a developer's production database during tests.

Validation:

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest --collect-only -q
```

Expected: test collection succeeds without importing `.env.dev` secrets or requiring a live production database.

---

## Phase 1 (P0): close the security boundary before functional changes

### Task 1.1: Make security-critical settings mandatory

Files:

- Modify: `backend/app/core/config.py:9-152`
- Modify: `backend/app/main.py` startup validation
- Add tests: `backend/tests/test_security_config.py`

- Remove usable defaults for `SECRET_KEY`, `FIRST_SUPERUSER_PASSWORD`, and any fallback admin credentials.
- Fail fast in non-development environments when `SECRET_KEY`, database configuration, and required bootstrap credentials are absent or weak.
- Permit an explicit local-development mode only when it is bound to localhost/private development configuration and does not silently create a known admin account.
- Validate that `OAUTH_STATE_SECRET` is independent from the JWT secret in production.
- Keep secret values out of exception messages and logs.

Tests:

- Production settings reject a missing or known default secret.
- Production settings reject the known default password.
- Development settings do not create a superuser unless credentials are explicitly configured.
- Configuration validation never returns secret values.

### Task 1.2: Replace permissive CORS with an allowlist

Files:

- Modify: `backend/app/main.py:68-91`
- Modify: `backend/.env.example`
- Add tests: `backend/tests/test_cors.py`

- Delete the `.*` origin regex.
- Parse a comma-separated allowlist from configuration and reject wildcard origins when `allow_credentials=True`.
- Use a narrow localhost allowlist only in development.
- Define explicit allowed methods and headers instead of `*` unless a documented client contract requires otherwise.

Tests:

- Approved frontend origins receive CORS headers.
- An arbitrary origin does not receive credentialed CORS access.
- Preflight requests expose only the configured methods and headers.

### Task 1.3: Stop leaking internal exceptions

Files:

- Modify: `backend/app/main.py:207-230`
- Modify: `backend/app/core/errors.py` if envelope behavior requires it
- Add tests: `backend/tests/test_error_envelopes.py`

- Return a stable error code and generic message for unexpected exceptions.
- Keep the full exception and traceback only in structured server logs with request/correlation IDs.
- Preserve safe, explicit `AequitasError` details only when they are intentionally client-visible.
- Audit route-level `except Exception` handlers and remove `detail=str(e)` / `details={"error": str(e)}` from external responses.

Tests:

- A deliberately raised internal exception produces HTTP 500 without SQL, filesystem paths, credentials, or Python exception text.
- The server log contains the correlation/request ID and the traceback.

### Task 1.4: Define one reusable authentication and authorization dependency set

Files:

- Modify: `backend/app/api/v1/auth.py:44-82`
- Modify: `backend/app/core/security.py:34-52`
- Modify: `backend/app/api/deps.py`
- Add tests: `backend/tests/test_authorization_dependencies.py`

- Consolidate `check_superuser` into one implementation that composes `get_current_user` correctly when used through `Depends`.
- Add explicit dependencies for authenticated user, active user, superuser, company membership, and company-admin permission.
- Verify JWT claims: algorithm, expiration, subject format, issuer/audience if introduced, and user active status.
- Return 401 for invalid credentials and 403 for authenticated users lacking permission.
- Do not trust company IDs or role claims from the token as the sole authorization source; query current database permissions.

Tests:

- Missing, expired, malformed, and wrong-subject tokens are rejected.
- A regular user cannot access superuser endpoints.
- A user cannot read or mutate another company by changing a path parameter.
- An inactive user is rejected even with a previously valid token.

### Task 1.5: Protect every sensitive route and classify intentional public routes

Files:

- Modify: `backend/app/api/v1/settings.py`
- Modify: `backend/app/api/v1/snapshots.py`
- Modify: `backend/app/api/v1/merge.py`
- Modify: `backend/app/api/v1/templates.py`
- Modify: `backend/app/api/v1/upload.py`
- Modify: `backend/app/api/v1/qbo.py`
- Modify: `backend/app/api/v1/quickbooks.py` or remove the legacy router
- Modify: `backend/app/api/v1/dexter_onboarding.py`
- Modify: `backend/app/api/v1/masterchart.py`
- Modify: `backend/app/api/v1/admin/template_management.py`
- Modify: `backend/app/api/v1/client_logs.py`
- Add: `backend/tests/test_route_authorization.py`

Route policy:

- Public: health/read-only catalog endpoints only, with explicit rate limits and no tenant data.
- Authenticated + company-scoped: uploads, snapshots, mappings, journal/accounting operations, QBO import/export/reconciliation, onboarding, and merge operations.
- Company-admin: company configuration, user assignment, and company-level settings.
- Superuser: global master-chart/template administration and system settings.
- Internal service authentication: worker callbacks.

For each write endpoint:

1. Add the appropriate dependency.
2. Verify the requested company belongs to the current user or is an allowed superuser operation.
3. Add audit records with actor, entity, timestamp, request ID, and outcome.
4. Add idempotency where the operation has external side effects.
5. Add request size, filename, content-type, and row-count limits for uploads.

The route inventory must explicitly review at least:

- `POST /api/v1/settings/`
- `POST /api/v1/snapshots/snapshot`
- `POST /api/v1/merge/{company_id}/suggest`
- `POST /api/v1/merge/{company_id}/auto`
- `POST /api/v1/upload`
- `POST /api/v1/templates/apply/{template_name}`
- `POST /api/v1/templates/custom`
- `POST /api/v1/qbo/{company_id}/export`
- all QBO callbacks and legacy QuickBooks routes
- all admin template-management routes
- `POST /api/v1/client-logs`

Tests:

- Generate a route-level authorization matrix from the OpenAPI app and assert that every non-public mutation has an auth dependency.
- Test both unauthorized and cross-tenant access for every resource family.

### Task 1.6: Authenticate the worker callback

Files:

- Modify: `backend/app/api/v1/integration_jobs.py:148-256`
- Modify: `backend/app/services/integration_job_service.py`
- Modify: `services/aequitas-worker-go/internal/http/*`
- Add tests on both sides of the callback contract

- Add a dedicated internal service secret or request-signature scheme, stored only in environment configuration.
- Include timestamp/nonce protection to prevent replay.
- Reject missing, invalid, expired, or replayed signatures before parsing or mutating data.
- Bind callback authorization to the expected job ID and idempotency key.
- Keep the endpoint inaccessible from the public frontend network where deployment permits.

### Task 1.7: Secure OAuth and payment flows

Files:

- Modify: `backend/app/api/v1/oauth.py`
- Modify: `backend/app/api/v1/qbo.py`
- Modify or remove: `backend/app/api/v1/quickbooks.py`
- Modify: `backend/app/api/v1/payments.py`
- Modify: `backend/app/api/v1/auth.py`
- Modify: `backend/app/db/models/*` for persisted OAuth state if needed
- Add tests: `backend/tests/test_oauth_security.py`, `backend/tests/test_payment_webhook.py`

- Persist OAuth state bound to the initiating user/company, provider, redirect URI, expiry, and one-time use; validate it on callback.
- Never create a JWT from an untrusted QBO `realmId`; resolve the authenticated user/company from a validated state record.
- Do not return internal access tokens in callback JSON or URLs.
- Require a webhook secret whenever Stripe is enabled and verify signatures before processing.
- Make webhook processing idempotent by event ID and ensure concurrent delivery cannot finalize a registration twice.
- Disable mock payments outside explicit development/test mode.

---

## Phase 2 (P0/P1): make the application boot reproducibly

### Task 2.1: Declare all runtime dependencies

Files:

- Modify: `backend/requirements.txt`
- Modify: `backend/requirements-dev.txt`
- Modify: `backend/Dockerfile`
- Modify: `backend/setup.py` or replace it with a unified package configuration
- Add: dependency lock/constraints file if selected

- Add `python-multipart` for multipart/form routes.
- Add `stripe` for configured Stripe flows.
- Verify every top-level runtime import against declared dependencies.
- Resolve the Typer conflict between `requirements.txt` (`0.12.3`) and `setup.py` (`0.9.0`).
- Pin compatible versions and generate a reproducible lock/constraints artifact.

Validation:

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
python scripts/validate_imports.py
python -m pytest tests/test_imports.py -q
```

Expected: no missing dependency import failures.

### Task 2.2: Remove or repair the ghost QuickBooks router

Files:

- `backend/app/api/v1/quickbooks.py`
- `backend/app/services/quickbooks_service.py` (create only if the legacy route is still required)
- `backend/app/main.py`
- Tests covering the selected behavior

Choose one option explicitly:

- Implement the missing service and secure its OAuth flow, or
- Remove the obsolete router and keep only the maintained `qbo.py` integration.

Do not leave a route imported into the application that cannot resolve its service dependency.

### Task 2.3: Make health checks meaningful

Files:

- Modify: `backend/app/main.py`
- Add: `backend/app/api/health.py` if separation is useful
- Add tests: `backend/tests/test_health.py`

- Keep `/health` as a liveness endpoint with no database dependency.
- Add `/ready` that verifies database connectivity, required migration revision, and required dependencies such as pgvector.
- Return degraded/not-ready status rather than reporting `{"status":"ok"}` when the application cannot serve accounting operations.

---

## Phase 3 (P1): establish one authoritative database lifecycle

### Task 3.1: Inventory the real schema and migration graph

Files:

- Inspect: `backend/alembic/versions/*.py`
- Inspect: `backend/app/db/models/*.py`
- Inspect: `backend/app/db/migrate_schema.py`
- Inspect: SQL files under `backend/migrations/`, `backend/*.sql`, and `backend/sql/`
- Create: `backend/docs/database-migration-inventory.md`

- Produce a table mapping each schema object to its canonical creation/change revision.
- Compare a fresh database created from migrations with the current model metadata and the bootstrap scripts.
- Identify data migrations, triggers, extensions, indexes, seed data, and irreversible operations separately.
- Do not delete existing migrations until the inventory identifies whether deployed databases depend on their revision IDs.

### Task 3.2: Select Alembic as the single schema authority

Files:

- Modify: `backend/scripts/bootstrap.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/db/init_db.py`
- Modify or deprecate: `backend/app/db/migrate_schema.py`
- Implement missing revisions under `backend/alembic/versions/`

- Application startup must not run `Base.metadata.create_all()` in production.
- Application startup must not execute ad hoc schema alterations.
- Bootstrap may wait for PostgreSQL, run `alembic upgrade head`, and execute explicitly versioned seed jobs.
- Convert each required no-op migration into a real migration, or replace the historical no-op chain with a documented squashed baseline plus a forward-only migration for already-deployed databases.
- Every migration must have a tested downgrade strategy, or an explicit documented irreversible/data-migration policy.
- Make extension creation and trigger/index creation deterministic and safe under repeated execution.

Validation against disposable PostgreSQL/pgvector:

```bash
alembic upgrade head
alembic current
alembic downgrade base
alembic upgrade head
```

Expected: a fresh database can reach head; downgrade/upgrade behavior is known and tested; schema state does not depend on importing the FastAPI application.

### Task 3.3: Make bootstrap and seeding idempotent and concurrency-safe

Files:

- Modify: `backend/scripts/bootstrap.py`
- Modify: `backend/app/data/*seed*.py`
- Add tests: `backend/tests/test_bootstrap_idempotency.py`

- Use database advisory locking or a deployment-level migration lock so two replicas cannot seed concurrently.
- Use unique constraints and upserts for seeded data.
- Fail startup if a required migration or seed fails; do not continue with a partially valid database.
- Remove debug `print()` statements and log only non-sensitive identifiers.

---

## Phase 4 (P1): accounting correctness and tenant isolation

### Task 4.1: Add authorization tests for every company-scoped service

Files:

- Add/extend tests under `backend/tests/`
- Review: `app/services/permission_service.py`, `company_service.py`, `journal_entry_service.py`, `ledger_service.py`, `mapping_service.py`, `sandbox_service.py`

- Use two users and two companies in fixtures.
- Verify every service rejects cross-company reads and writes, not only the route layer.
- Verify superuser access is explicitly allowed only where Canon II permits it.
- Verify sandbox writes cannot affect real accounting tables.

### Task 4.2: Test accounting invariants at the database and service layers

Files:

- Extend: `backend/tests/test_journal_workflow.py`, `backend/tests/test_fiscal_engine.py`
- Review: journal-entry models, services, and relevant migrations/triggers

Cover:

- Debits equal credits.
- Posted journal entries are immutable.
- Locked fiscal periods reject mutations and backdating.
- Idempotent requests do not duplicate entries.
- Required kernel accounts cannot be removed or silently repurposed.
- Corrections are append-only and auditable.

### Task 4.3: Add upload and resource limits

Files:

- Modify: `backend/app/api/v1/upload.py`
- Modify: `backend/app/api/v1/templates.py`
- Modify: `backend/app/services/company_import_service.py`
- Add tests for oversized, malformed, and hostile files

- Enforce maximum request and file sizes at the reverse proxy and application layer.
- Validate MIME type and extension using file signatures where feasible.
- Limit spreadsheet row count, worksheet count, and parsing time.
- Ensure temporary files are isolated and deleted.
- Return generic errors without parser internals.

---

## Phase 5 (P2): reliability, maintainability, and observability

### Task 5.1: Replace deprecated lifecycle and naive datetimes

Files:

- Modify: `backend/app/main.py`
- Modify all uses of `datetime.utcnow()` in `backend/app/`
- Add tests for timezone-aware expiration and fiscal dates

- Replace `@app.on_event("startup")` with a lifespan context only for non-mutating initialization/readiness registration.
- Use timezone-aware UTC timestamps for tokens, rate limits, audit logs, and expiration fields.
- Preserve database compatibility during the transition.

### Task 5.2: Replace in-memory rate limiting

Files:

- Modify: `backend/app/core/rate_limiting.py`
- Modify: `backend/app/main.py` or middleware registration
- Add Redis-backed implementation or a database-backed fallback
- Add tests for multi-process consistency and bypass resistance

- Rate-limit by authenticated subject plus IP/device signal where appropriate.
- Apply limits to login, registration, password recovery, OAuth callbacks, uploads, and expensive accounting/AI operations.
- Keep a local limiter only as a defense-in-depth fallback, not as the authoritative distributed limit.

### Task 5.3: Consolidate services and remove route-level business logic

Files:

- Refactor incrementally: `backend/app/api/v1/auth.py`, `companies.py`, `accounting.py`, `journal_entries.py`
- Add focused service tests

- Move dashboard aggregation, registration finalization, and accounting mutation workflows into services.
- Keep route handlers responsible for parsing, dependency injection, and response mapping.
- Preserve existing API response contracts during the refactor.

### Task 5.4: Fix query and logging quality

Files:

- Modify: `backend/app/api/v1/companies.py` dashboard path
- Modify production modules currently using `print()`
- Add performance/logging tests or query-count assertions

- Replace the audit-log actor N+1 query with a joined/preloaded query.
- Replace production `print()` with structured logger calls.
- Ensure logs redact passwords, tokens, OAuth codes, webhook payloads, and financial secrets.
- Add request/correlation IDs to all external calls and mutation audit records.

### Task 5.5: Introduce static quality gates and CI

Files:

- Create or modify: `.github/workflows/backend.yml`
- Modify: `backend/requirements-dev.txt` or package configuration
- Add: `backend/ruff.toml`, `mypy.ini`, or equivalent configuration if selected

CI gates:

1. dependency installation from the lock/constraints file;
2. compile/import validation;
3. unit tests;
4. PostgreSQL integration tests;
5. migration upgrade/downgrade test;
6. route authorization matrix test;
7. lint/type checks;
8. container build and `/health`/`/ready` smoke test.

Do not treat a green syntax-only check as backend readiness.

---

## Release acceptance criteria

The backend is not ready for deployment until all of the following are true:

- No known default secret or admin password can authenticate.
- No credentialed wildcard CORS configuration exists.
- Unexpected exceptions do not expose internal details.
- Every sensitive mutation has a tested authentication, authorization, tenant-scope, audit, and idempotency policy.
- Worker callbacks and OAuth/payment callbacks are authenticated and replay-resistant.
- `python-multipart`, `stripe`, and all other runtime imports are reproducibly installed.
- The ghost QuickBooks route is removed or fully implemented.
- A fresh PostgreSQL/pgvector database reaches Alembic head without `create_all()` or ad hoc startup DDL.
- Re-running bootstrap is safe and does not duplicate seed data.
- Health/readiness checks distinguish process liveness from database readiness.
- Cross-tenant and accounting-invariant integration tests pass.
- CI runs the same validation path used for the release image.

## Risks and decisions to resolve before implementation

1. Migration history: whether deployed databases exist outside development determines whether no-op revisions can be rewritten or must be superseded by a repair/squash migration.
2. Public API policy: catalog and health routes may remain public, but this must be an explicit documented allowlist rather than an accidental absence of dependencies.
3. OAuth ownership: the maintained `qbo.py` flow and legacy `quickbooks.py` flow must not both remain active unless their contracts and security models are distinct.
4. Deployment topology: Redis-backed rate limiting and worker callback network isolation depend on whether production has multiple replicas and a private service network.
5. Secret rotation: changing JWT signing keys invalidates existing sessions; define a controlled rotation and revocation policy before enforcing mandatory secrets.

## Suggested implementation order

1. Phase 0 baseline and dependency environment.
2. Tasks 1.1-1.5: secrets, CORS, error handling, auth dependencies, route protection.
3. Tasks 1.6-1.7: internal callbacks and external OAuth/payment flows.
4. Tasks 2.1-2.3: bootability, ghost router, readiness checks.
5. Phase 3 migration consolidation.
6. Phase 4 tenant isolation and accounting invariants.
7. Phase 5 maintainability and CI hardening.

Do not expose the backend publicly while any Phase 1 task remains unresolved.
