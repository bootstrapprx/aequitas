"""
StagingQBOAccount SQLAlchemy model.

PHASE 1.5: Operational Extraction - Staging Layer

PURPOSE:
- Stores RAW QuickBooks account data as received from Go worker
- Append-only, no deduplication (idempotency handled at endpoint level)
- NO accounting validation, mapping, or classification
- Acts as staging area before Python validates and processes

CRITICAL RULES:
- This is NOT authoritative accounting data
- This is NOT normalized or validated
- This table exists ONLY to isolate external integration data
- Mapping and validation happen in separate phase

LIFECYCLE:
1. Go worker fetches QBO data
2. Go calls back to Python with raw payload
3. Python persists to this staging table
4. (Future phase) Validation service reads from staging
5. (Future phase) Validated data flows to company_accounts
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base


class StagingQBOAccount(Base):
    """
    Staging table for raw QuickBooks Online account data.

    IMMUTABILITY:
    - Rows are never updated after insertion
    - Append-only design for audit trail
    - Duplicate callbacks prevented via idempotency

    BOUNDARIES:
    - Python writes here (from Go callback)
    - Python reads here (for validation phase)
    - This table NEVER joins to authoritative accounting tables
    """
    __tablename__ = "staging_qbo_accounts"

    # ========================================================================
    # PRIMARY KEY
    # ========================================================================
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # ========================================================================
    # TRACING & CORRELATION
    # ========================================================================
    job_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="Go worker job ID")
    request_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="X-Aequitas-Request-Id")
    correlation_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="X-Aequitas-Correlation-Id")

    # ========================================================================
    # COMPANY REFERENCE (Not FK - isolation boundary)
    # ========================================================================
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="Target company (not FK for isolation)")

    # ========================================================================
    # SOURCE DATA (Raw from QuickBooks)
    # ========================================================================
    source = Column(String, nullable=False, default="quickbooks", comment="Always 'quickbooks' for this table")
    source_account_id = Column(String, nullable=False, comment="QuickBooks account ID")

    # Basic account fields (neutral format from Go)
    name = Column(String, nullable=False)
    account_type = Column(String, nullable=True, comment="QuickBooks account type (raw)")
    account_subtype = Column(String, nullable=True, comment="QuickBooks account subtype (raw)")
    active = Column(Boolean, nullable=False, default=True)
    currency = Column(String, nullable=True, default="USD")

    # ========================================================================
    # RAW PAYLOAD (Complete data as received)
    # ========================================================================
    raw_payload = Column(JSONB, nullable=False, comment="Complete account object from Go worker")

    # ========================================================================
    # VALIDATION & NORMALIZATION METADATA (mutable)
    # ========================================================================
    validation_status = Column(String, nullable=True, index=True, comment="VALID or INVALID")
    validation_errors = Column(JSONB, nullable=True, comment="List of validation errors")
    validated_at = Column(DateTime, nullable=True)

    normalized_payload = Column(JSONB, nullable=True, comment="Deterministic normalized payload")

    mapping_status = Column(String, nullable=True, index=True, comment="AUTO_MAPPED | NEEDS_REVIEW | UNMAPPED")

    processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    processing_result = Column(String, nullable=True, comment="SUCCESS | PARTIAL | FAILED")

    company_account_id = Column(UUID(as_uuid=True), ForeignKey("company_accounts.id"), nullable=True)
    mapping_id = Column(UUID(as_uuid=True), ForeignKey("account_mappings.id"), nullable=True)

    # ========================================================================
    # METADATA
    # ========================================================================
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="When staged")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ========================================================================
    # INDEXES
    # ========================================================================
    __table_args__ = (
        Index("ix_staging_qbo_accounts_company_job", "company_id", "job_id"),
        Index("ix_staging_qbo_accounts_source_id", "source_account_id"),
        Index("ix_staging_qbo_accounts_imported_at", "imported_at"),
        {"comment": "STAGING ONLY - Not authoritative. Raw QBO data before validation."}
    )

    def __repr__(self):
        return f"<StagingQBOAccount(id={self.id}, company_id={self.company_id}, source_account_id={self.source_account_id}, name={self.name})>"
