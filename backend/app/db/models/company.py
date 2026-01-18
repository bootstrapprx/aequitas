import enum
import uuid
from sqlalchemy import Column, String, Text, Boolean, Index, DateTime, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.db.models.enums import OnboardingStatus, KernelLayer

class SubscriptionType(str, enum.Enum):
    NATIVE = "native"
    STRIPE = "stripe"

class Company(Base):
    __tablename__ = "companies"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True, nullable=False)
    ucid = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    inactivated_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    inactivated_at = Column(DateTime, nullable=True)
    inactivated_by = Column(String, nullable=True) # User ID or Name
    subscription_type = Column(Enum(SubscriptionType), default=SubscriptionType.STRIPE, nullable=False)

    # Contact Information
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)

    # Address Information
    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    country = Column(String, nullable=True)

    # Additional Information
    tax_id = Column(String, nullable=True)  # Tax ID / EIN
    industry = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    # Phase 5 Onboarding Fields
    trade_name = Column(String, nullable=True)  # Trade name (DBA)
    timezone = Column(String, nullable=True)  # Timezone (e.g., 'America/New_York')
    currency = Column(String(3), nullable=True)  # ISO 4217 currency code (e.g., 'USD')
    legal_nature = Column(String, nullable=True) # LLC, Corp, etc.
    economic_activity = Column(String, nullable=True) # Commerce, Services, etc.
    is_standalone = Column(Boolean, default=True, nullable=False) # True if not part of a group

    # Onboarding State Machine
    onboarding_status = Column(
        Enum(OnboardingStatus),
        default=OnboardingStatus.DRAFT,
        nullable=False,
        index=True
    )
    onboarding_current_step = Column(Integer, default=0, nullable=False)  # 0-8
    onboarding_started_at = Column(DateTime(timezone=True), nullable=True)
    onboarding_completed_at = Column(DateTime(timezone=True), nullable=True)
    onboarding_session_lock = Column(UUID(as_uuid=True), nullable=True)  # Session lock UUID
    onboarding_session_locked_at = Column(DateTime(timezone=True), nullable=True)

    # Kernel binding
    kernel_version = Column(String(10), nullable=True)
    kernel_layer = Column(Enum(KernelLayer), nullable=True)
    
    modules = relationship("CompanyModule", back_populates="company", cascade="all, delete-orphan")
    accounts = relationship("CompanyAccount", back_populates="company", cascade="all, delete-orphan")

    # Relationship to users (many-to-many through UserCompany)
    user_companies = relationship("UserCompany", back_populates="company", cascade="all, delete-orphan")

    # Accounting relationships
    fiscal_periods = relationship("FiscalPeriod", back_populates="company", cascade="all, delete-orphan")
    journal_entries = relationship("JournalEntry", back_populates="company", cascade="all, delete-orphan")

    # Fiscal Engine relationship
    tax_profile = relationship("EntityTaxProfile", back_populates="company", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_companies_ucid_active', 'ucid', unique=True, postgresql_where=(is_active == True)),
        Index('ix_companies_name_active', 'name', unique=True, postgresql_where=(is_active == True)),
    )
