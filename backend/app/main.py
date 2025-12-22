import logging
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1 import (
    accounting,
    admin,
    auth,
    client_logs,
    companies,
    companies_su,
    companychart,
    elevation,
    fiscal,
    groups,
    integration_jobs,
    invitations,
    journal_entries,
    mappings,
    masterchart,
    merge,
    oauth,
    onboarding,
    payments,
    permissions,
    qbo,
    settings,
    snapshots,
    templates,
    upload,
    users,
    users_management,
    dexter_onboarding,
)
from app.api.v1.integrations import staging as integrations_staging
from app.api.v1.integrations import mappings as integrations_mappings
from app.core.startup import startup_checks
from app.db.base import Base
from app.db.init_db import init_db
from app.db.session import SessionLocal, engine
from app.services.code_generator import router as code_generator_router
from app.services.dexter.router import router as dexter_router
from app.services.organizer_ai.router import router as organizer_router
from app.core.errors import (
    AequitasError,
    http_exception_to_aequitas_error,
    make_error_envelope,
)
from app.core.logging_config import configure_logging
from app.core.middleware.request_ids import RequestIdMiddleware
from app.core.request_context import ensure_request_ids

# 1. Application Initialization Order: FastAPI app is created at the very top.
app = FastAPI(
    title="Aequitas API",
    description="Backend for Aequitas - Integrated Accounting System.",
    version="1.0.0",
)
configure_logging()

# 2. Harden CORS Configuration: CORSMiddleware is attached immediately after.
# Dev-safe origins
allow_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

# Add production origins from environment variable
if os.getenv("BACKEND_CORS_ORIGINS"):
    origins_prod = [origin.strip() for origin in os.getenv("BACKEND_CORS_ORIGINS").split(",")]
    allow_origins.extend(origins_prod)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestIdMiddleware)
logger = logging.getLogger(__name__)


def _trace_headers():
    request_id, correlation_id = ensure_request_ids()
    return {
        "X-Aequitas-Request-Id": request_id,
        "X-Aequitas-Correlation-Id": correlation_id,
    }


# 3. DB initialization, startup checks, and side effects are moved into a startup handler.
@app.on_event("startup")
def startup_event():
    """
    Application startup logic.
    - Creates database extensions and tables.
    - Initializes the database with essential data (e.g., superuser).
    - Runs startup checks to ensure system integrity.
    """
    print("="*60)
    print("RUNNING STARTUP EVENT")
    print("="*60)
    
    # Create PostgreSQL extensions and tables
    with engine.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        connection.commit()
    Base.metadata.create_all(bind=engine)

    # Initialize database with superuser and default settings
    db = SessionLocal()
    try:
        init_db(db)

        # Run startup checks
        print("\n" + "="*60)
        print("RUNNING STARTUP CHECKS")
        print("="*60)
        startup_results = startup_checks(db)

        if startup_results["errors"]:
            print("\n⚠ WARNINGS:")
            for error in startup_results["errors"]:
                print(f"  - {error}")
        else:
            print("✓ All startup checks passed")
        print("="*60 + "\n")
    finally:
        db.close()
    
    print("="*60)
    print("STARTUP EVENT COMPLETE")
    print("="*60)


# API Routers
# 4. Eliminate Router Shadowing: companies_su router is moved to a dedicated admin prefix.
app.include_router(companies.router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(companies_su.router, prefix="/api/v1/admin/companies", tags=["Companies - Superuser"])

app.include_router(dexter_router, prefix="/api/v1/ai", tags=["ai"])
app.include_router(masterchart.router, prefix="/api/v1/masterchart", tags=["Master Chart"])
app.include_router(companychart.router, prefix="/api/v1", tags=["Chart of Accounts"])
app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])
app.include_router(snapshots.router, prefix="/api/v1", tags=["Snapshots"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["Templates"])
app.include_router(merge.router, prefix="/api/v1/merge", tags=["MergeEngine"])
app.include_router(qbo.router, prefix="/api/v1/qbo", tags=["QuickBooks"])
app.include_router(organizer_router, prefix="/api/v1/organizer", tags=["OrganizerAI"])
app.include_router(code_generator_router, prefix="/api/v1/code", tags=["CodeGenerator"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["Settings"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(oauth.router, prefix="/api/v1/auth/oauth", tags=["OAuth Authentication"])
app.include_router(invitations.router, prefix="/api/v1/invitations", tags=["Invitations"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(users_management.router, prefix="/api/v1", tags=["Users Management"])
app.include_router(permissions.router, prefix="/api/v1/permissions", tags=["Permissions"])
app.include_router(elevation.router, prefix="/api/v1/elevation", tags=["Elevation"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])

# Accounting routers
app.include_router(journal_entries.router, prefix="/api/v1/journal-entries", tags=["Accounting - Journal Entries"])
app.include_router(accounting.router, prefix="/api/v1/accounting", tags=["Accounting - Reports & Periods"])
app.include_router(client_logs.router, prefix="/api/v1", tags=["Client Logs"])

# Groups router
app.include_router(groups.router, prefix="/api/v1/groups", tags=["Groups"])

# Mappings router
app.include_router(mappings.router, prefix="/api/v1/mappings", tags=["Mappings"])

# Phase 5 - Onboarding router
app.include_router(onboarding.router, prefix="/api/v1", tags=["Onboarding"])
app.include_router(dexter_onboarding.router, prefix="/api/v1", tags=["Dexter Onboarding"])
app.include_router(integrations_staging.router, prefix="/api/v1/integrations")
app.include_router(integrations_mappings.router, prefix="/api/v1/integrations")

# Fiscal Engine router
app.include_router(fiscal.router, prefix="/api/v1/fiscal", tags=["Fiscal Engine"])

# Integration Jobs router (Phase 1.5: Operational Extraction)
app.include_router(integration_jobs.router, prefix="/api/v1/integrations", tags=["Integration Jobs"])

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


@app.exception_handler(AequitasError)
async def handle_aequitas_error(request: Request, exc: AequitasError):
    envelope = make_error_envelope(exc.code, exc.message, details=exc.details)
    return JSONResponse(status_code=exc.http_status, content=envelope, headers=_trace_headers())


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException):
    canonical_exc = http_exception_to_aequitas_error(exc)
    envelope = make_error_envelope(
        canonical_exc.code, canonical_exc.message, details=canonical_exc.details
    )
    return JSONResponse(status_code=canonical_exc.http_status, content=envelope, headers=_trace_headers())


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception):
    logger.exception("Unhandled exception", exc_info=exc)
    envelope = make_error_envelope(
        "AEQ_INTERNAL_SERVER_ERROR",
        "An unexpected error occurred.",
        details={"error": str(exc)},
    )
    return JSONResponse(status_code=500, content=envelope, headers=_trace_headers())
