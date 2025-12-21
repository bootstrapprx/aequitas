from sqlalchemy import Column, String, Boolean, Text, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class NormalizationAudit(Base):
    __tablename__ = "normalization_audit"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    entity_type = Column(String, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    field_name = Column(String, nullable=False)
    user_input = Column(Text, nullable=False)
    suggested_value = Column(Text, nullable=False)
    final_value = Column(Text, nullable=False)
    normalization_type = Column(String, nullable=False)
    confidence_score = Column(Numeric(3, 2), nullable=False)
    user_accepted_suggestion = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class OnboardingCorrection(Base):
    __tablename__ = "onboarding_corrections"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String, nullable=True)
    step = Column(String, nullable=False)
    field = Column(String, nullable=False)
    original_input = Column(Text, nullable=False)
    dexter_suggestion = Column(Text, nullable=False)
    correction_type = Column(String, nullable=False)
    user_action = Column(String, nullable=False)
    final_value = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    company = relationship("Company", backref="onboarding_corrections")
