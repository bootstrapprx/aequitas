"""
TaxPosition SQLAlchemy model.

Final tax position outputs (per company and consolidated).
"""
import uuid
from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class TaxPosition(Base):
    """
    Final calculated tax position.
    Represents the output of a tax run: taxable income, estimated exposure, drivers.
    """
    __tablename__ = "tax_positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Run reference
    tax_run_id = Column(UUID(as_uuid=True), ForeignKey("tax_runs.id", ondelete="CASCADE"), nullable=False, index=True)

    # Company (null for consolidated)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True)

    # Tax type
    tax_type = Column(String, nullable=False)  # "PASS_THROUGH_INCOME"

    # Outputs
    taxable_income_estimated = Column(Numeric(15, 2), nullable=False)
    exposure_estimated = Column(Numeric(15, 2), nullable=True)  # Placeholder for when we add rate tables
    currency = Column(String(3), nullable=False, default="USD")

    # Confidence
    confidence_score = Column(Integer, nullable=False, default=0)  # 0-100
    missing_inputs = Column(JSONB, nullable=False, default=list)  # ["accounting_method", "state_apportionment"]

    # Top drivers (for reporting)
    top_drivers = Column(JSONB, nullable=False, default=list)  # [{"account_code": "4000", "amount": 50000, "tag": "taxable_income"}]

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tax_run = relationship("TaxRun", back_populates="tax_positions")
    company = relationship("Company", foreign_keys=[company_id])

    __table_args__ = (
        Index('ix_tax_positions_company_tax_type', 'company_id', 'tax_type'),
    )

    def __repr__(self):
        return f"<TaxPosition(company_id='{self.company_id}', tax_type='{self.tax_type}', taxable_income={self.taxable_income_estimated})>"
