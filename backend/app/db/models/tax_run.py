"""
TaxRun SQLAlchemy model.

One execution of the Fiscal Engine.
"""
import uuid
from sqlalchemy import Column, String, Date, Integer, ForeignKey, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class TaxRun(Base):
    """
    A single execution of the Fiscal Engine.
    Tracks inputs, version, status, and outputs for deterministic recalculation.
    """
    __tablename__ = "tax_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Company (null for consolidated runs)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True)

    # Period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    as_of_date = Column(Date, nullable=True)  # Trial balance as-of date

    # Ruleset
    ruleset_id = Column(UUID(as_uuid=True), ForeignKey("tax_rulesets.id"), nullable=False)
    ruleset_version = Column(String, nullable=False, index=True)  # Denormalized for quick filtering

    # Engine version
    engine_version = Column(String, nullable=False)  # "1.0.0"

    # Determinism
    inputs_hash = Column(String, nullable=False, index=True)  # SHA-256 hash of inputs

    # Status
    status = Column(String, nullable=False, default="SUCCESS")  # SUCCESS, PARTIAL, FAILED
    confidence_score = Column(Integer, nullable=False, default=0)  # 0-100
    missing_inputs = Column(JSONB, nullable=False, default=list)  # ["accounting_method", "tax_tags_account_1234"]

    # Label (mandatory disclaimer)
    label = Column(String, nullable=False, default="Estimated / Projected Tax Exposure — Not a Tax Filing")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    company = relationship("Company", foreign_keys=[company_id])
    ruleset = relationship("TaxRuleset", back_populates="tax_runs")
    tax_facts = relationship("TaxFact", back_populates="tax_run", cascade="all, delete-orphan")
    tax_adjustments = relationship("TaxAdjustment", back_populates="tax_run", cascade="all, delete-orphan")
    tax_positions = relationship("TaxPosition", back_populates="tax_run", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_tax_runs_company_period', 'company_id', 'period_start', 'period_end'),
    )

    def __repr__(self):
        return f"<TaxRun(company_id='{self.company_id}', period='{self.period_start} to {self.period_end}', status='{self.status}')>"
