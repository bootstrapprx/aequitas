from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    companies,
    masterchart,
    companychart,
    mapping,
    upload,
    snapshots,
    templates,
    merge,
    merge,
    qbo,
    settings, # New
    auth, # New
    users, # New
    permissions, # New
    admin, # New
)
from app.services.organizer_ai.router import router as organizer_router
from app.services.code_generator import router as code_generator_router
from app.services.dexter.router import router as dexter_router

from app.db.base import Base
from app.db.session import engine
# Import all models to ensure they are registered with Base
from app.db.models import (
    master_account, 
    snapshot, 
    template, 
    company_account, 
    account_mapping,
    qbo_token, # New
    organizer_memory,
    organizer_rules,
    system_settings, # New
    user, # New
    user_company, # New
)

# Create all tables in the database on startup
# Create all tables in the database on startup
Base.metadata.create_all(bind=engine)

# Initialize database with superuser
from app.db.init_db import init_db
from app.db.session import SessionLocal
db = SessionLocal()
try:
    init_db(db)
finally:
    db.close()

app = FastAPI(
    title="Aequitas API",
    description="Backend for Aequitas - Integrated Accounting System.",
    version="1.0.0",
)

# CORS (Cross-Origin Resource Sharing)
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

# Add production origins from environment variable
import os
if os.getenv("BACKEND_CORS_ORIGINS"):
    origins.extend(os.getenv("BACKEND_CORS_ORIGINS").split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(companies.router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(dexter_router, prefix="/api/v1/ai", tags=["ai"])
app.include_router(masterchart.router, prefix="/api/v1/masterchart", tags=["Master Chart"])
app.include_router(companychart.router, prefix="/api/v1", tags=["Company Chart"])
app.include_router(mapping.router, prefix="/api/v1", tags=["Mapping"])
app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])
app.include_router(snapshots.router, prefix="/api/v1", tags=["Snapshots"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["Templates"])
app.include_router(merge.router, prefix="/api/v1/merge", tags=["MergeEngine"])
app.include_router(qbo.router, prefix="/api/v1/qbo", tags=["QuickBooks"]) # New
app.include_router(organizer_router, prefix="/api/v1/organizer", tags=["OrganizerAI"])
app.include_router(code_generator_router, prefix="/api/v1/code", tags=["CodeGenerator"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["Settings"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(permissions.router, prefix="/api/v1/permissions", tags=["Permissions"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}