import uuid
from sqlalchemy import Column, String, DateTime, func, ForeignKey, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class AccountMapping(Base):
    """
    SQLAlchemy model to store mapping suggestions and results between
    a CompanyAccount and a MasterAccount.
    """
    __tablename__ = "account_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    company_account_id = Column(UUID(as_uuid=True), ForeignKey("company_accounts.id"), nullable=False, index=True)
    company_account = relationship("CompanyAccount")

    staging_account_id = Column(UUID(as_uuid=True), ForeignKey("staging_qbo_accounts.id"), nullable=True, index=True)

    # Storing the master_code directly as requested, for simplicity.
    # For higher normalization, this could be a ForeignKey to master_accounts.id
    master_code = Column(String, index=True, nullable=True)
    master_account_id = Column(UUID(as_uuid=True), ForeignKey("master_accounts.id"), nullable=True, index=True)
    
    confidence = Column(Float, nullable=False)
    # Status can be 'suggested', 'confirmed', 'rejected', 'manual_review' or AUTO_MAPPED/NEEDS_REVIEW/UNMAPPED for staging pipeline
    status = Column(String, nullable=False, default="suggested", index=True)
    mapping_status = Column(String, nullable=True, index=True, comment="AUTO_MAPPED | NEEDS_REVIEW | UNMAPPED")

    notes = Column(String, nullable=True)
    decision_reason = Column(Text, nullable=True)
    source = Column(String, nullable=False, default="quickbooks")

    decision_status = Column(String, nullable=False, default="PENDING", index=True, comment="PENDING|ACCEPTED|OVERRIDDEN|REJECTED")
    decided_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    previous_master_account_id = Column(UUID(as_uuid=True), ForeignKey("master_accounts.id"), nullable=True)

    # For group propagation: tracks the source company if this mapping was propagated
    propagated_from = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<AccountMapping(company_id='{self.company_account_id}', master_code='{self.master_code}', status='{self.status}')>"
