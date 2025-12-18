"""
TaxRuleset SQLAlchemy model.

Stores versioned tax calculation rulesets.
"""
import uuid
from sqlalchemy import Column, String, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class TaxRuleset(Base):
    """
    Versioned tax calculation rulesets.
    Each ruleset contains a set of rules for calculating tax adjustments.
    """
    __tablename__ = "tax_rulesets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Versioning
    version = Column(String, nullable=False, index=True)  # "2025.1", "2025.2"
    scope = Column(String, nullable=False, index=True)  # "PASS_THROUGH_BASE", "C_CORP_BASE"
    jurisdiction = Column(String, nullable=True)  # "US", "CA", null for federal

    # Status
    status = Column(String, nullable=False, default="ACTIVE")  # ACTIVE, INACTIVE

    # Rules (JSON array of rule definitions)
    rules = Column(JSONB, nullable=False, default=list)  # [{"rule_id": "meal_entertainment", "adjustment_rate": 0.50, ...}]

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tax_runs = relationship("TaxRun", back_populates="ruleset")

    __table_args__ = (
        Index('ix_tax_rulesets_version_scope_jurisdiction', 'version', 'scope', 'jurisdiction', unique=True),
    )

    def __repr__(self):
        return f"<TaxRuleset(version='{self.version}', scope='{self.scope}', status='{self.status}')>"
