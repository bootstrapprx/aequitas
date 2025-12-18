"""
TaxFact SQLAlchemy model.

Normalized facts derived from trial balance / ledger.
"""
import uuid
from sqlalchemy import Column, String, Date, Numeric, ForeignKey, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class TaxFact(Base):
    """
    Normalized financial facts for tax calculation.
    Derived from trial balance or ledger, tagged for tax treatment.
    """
    __tablename__ = "tax_facts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Run reference
    tax_run_id = Column(UUID(as_uuid=True), ForeignKey("tax_runs.id", ondelete="CASCADE"), nullable=False, index=True)

    # Company and period
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Account reference
    account_id = Column(UUID(as_uuid=True), ForeignKey("company_accounts.id"), nullable=True)  # May be null for consolidated
    account_code = Column(String, nullable=False)
    account_name = Column(String, nullable=False)

    # Amount
    amount = Column(Numeric(15, 2), nullable=False)

    # Tax treatment
    tax_tags = Column(JSONB, nullable=False, default=list)  # ["taxable_income", "meals_entertainment", "depreciation"]

    # Source
    source = Column(String, nullable=False)  # "TRIAL_BALANCE", "LEDGER"
    source_trace = Column(JSONB, nullable=False, default=dict)  # {"trial_balance_account_id": "...", "original_balance": 12345.67}

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tax_run = relationship("TaxRun", back_populates="tax_facts")
    company = relationship("Company")
    account = relationship("CompanyAccount", foreign_keys=[account_id])

    def __repr__(self):
        return f"<TaxFact(account_code='{self.account_code}', amount={self.amount}, tags={self.tax_tags})>"
