"""
EntityTaxProfile SQLAlchemy model.

Represents fiscal assumptions per company.
"""
import uuid
from sqlalchemy import Column, String, Text, Date, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class EntityTaxProfile(Base):
    """
    Fiscal assumptions and tax elections for each company.
    Stores entity-level tax configuration for the Fiscal Engine.
    """
    __tablename__ = "entity_tax_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), unique=True, nullable=False, index=True)

    # Entity structure
    entity_type = Column(String, nullable=False, default="LLC")  # LLC, S-Corp, C-Corp, Partnership, Sole Prop
    tax_regime = Column(String, nullable=False, default="PASS_THROUGH")  # PASS_THROUGH, C_CORP

    # Accounting method
    accounting_method = Column(String, nullable=True)  # CASH, ACCRUAL, HYBRID (unknown if null)

    # Fiscal year
    fiscal_year_start = Column(Date, nullable=True)  # Fiscal year start date (e.g., 2025-01-01)

    # Jurisdictions (state/local for future use)
    jurisdictions = Column(JSONB, nullable=False, default=list)  # ["CA", "NY"] for multi-state

    # Tax elections (QSub, Check-the-box, etc.)
    elections = Column(JSONB, nullable=False, default=dict)  # {"qtb_election": true, "elected_date": "2024-01-01"}

    # Notes
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    company = relationship("Company", back_populates="tax_profile")

    def __repr__(self):
        return f"<EntityTaxProfile(company_id='{self.company_id}', entity_type='{self.entity_type}', tax_regime='{self.tax_regime}')>"
