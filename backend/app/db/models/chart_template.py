"""
Chart Template models for Phase 3B template enforcement.

TABLES:
- chart_templates: Template definitions (jurisdictions, versions)
- chart_template_accounts: Accounts within templates (with is_mandatory flag)
- company_template_usage: Links companies to their active template
"""

import uuid
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey, func, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.models.enums import ModuleType


class ChartTemplate(Base):
    """
    SQLAlchemy model for chart templates.

    CANONICAL SCHEMA:
    - Templates define jurisdiction-specific chart structures
    - Each template has a unique jurisdiction + version combination
    - Templates can be marked active/inactive
    """
    __tablename__ = "chart_templates"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # Core fields
    name = Column(String(255), nullable=False)
    """Template name (e.g., 'US GAAP Standard')"""

    jurisdiction = Column(String(100), nullable=False, index=True)
    """Jurisdiction code (e.g., 'US', 'CA', 'UK')"""

    version = Column(String(50), nullable=False)
    """Template version (e.g., '1.0', '2023-Q4')"""

    description = Column(Text, nullable=True)
    """Detailed description of the template"""

    is_active = Column(Boolean, default=True, nullable=False, index=True)
    """Active flag (only active templates can be assigned)"""

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    accounts = relationship("ChartTemplateAccount", back_populates="template", cascade="all, delete-orphan")
    company_usages = relationship("CompanyTemplateUsage", back_populates="template")

    def __repr__(self):
        return f"<ChartTemplate(name='{self.name}', jurisdiction='{self.jurisdiction}', version='{self.version}')>"


class ChartTemplateAccount(Base):
    """
    SQLAlchemy model for accounts within a chart template.

    CANONICAL SCHEMA:
    - Each template account references a master_account
    - Accounts can be marked as mandatory (must exist in company charts)
    - Accounts have hierarchical structure within the template
    - is_mandatory flag controls deletion and mutation rules
    """
    __tablename__ = "chart_template_accounts"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # Foreign keys
    template_id = Column(UUID(as_uuid=True), ForeignKey("chart_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    """Template this account belongs to"""

    master_account_id = Column(UUID(as_uuid=True), ForeignKey("master_accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    """Master account this template account references"""

    parent_id = Column(UUID(as_uuid=True), ForeignKey("chart_template_accounts.id", ondelete="CASCADE"), nullable=True, index=True)
    """Parent account in template hierarchy (NULL for top-level)"""

    # Core fields
    code = Column(String(50), nullable=False)
    """Template-specific account code"""

    name = Column(String(255), nullable=False)
    """Account name"""

    # Template enforcement fields
    is_mandatory = Column(Boolean, default=False, nullable=False)
    """
    If True, this account MUST exist in all companies using this template.

    CANONICAL RULES for mandatory accounts:
    - Cannot be deleted from company charts
    - Cannot change normal_balance
    - Cannot change mapped_master_account_id
    """

    allow_custom_children = Column(Boolean, default=False, nullable=False)
    """If True, companies can add custom child accounts under this account"""

    sort_order = Column(Integer, nullable=False)
    """Display sort order within parent"""

    required_module = Column(Enum(ModuleType), nullable=True)
    """If set, account is only created if company has this module enabled"""

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    template = relationship("ChartTemplate", back_populates="accounts")
    master_account = relationship("MasterAccount")
    parent = relationship("ChartTemplateAccount", remote_side=[id])
    company_accounts = relationship("CompanyAccount", foreign_keys="CompanyAccount.template_account_id")

    def __repr__(self):
        return f"<ChartTemplateAccount(code='{self.code}', name='{self.name}', mandatory={self.is_mandatory})>"


class CompanyTemplateUsage(Base):
    """
    SQLAlchemy model for tracking which template a company uses.

    CANONICAL SCHEMA:
    - Each company references exactly one active template
    - Unique constraint ensures one template per company
    - Tracks who assigned the template and when
    """
    __tablename__ = "company_template_usage"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # Foreign keys
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    """Company using this template (unique - one template per company)"""

    template_id = Column(UUID(as_uuid=True), ForeignKey("chart_templates.id", ondelete="RESTRICT"), nullable=False, index=True)
    """Active template for this company"""

    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    """User who assigned this template"""

    # Timestamps
    assigned_at = Column(DateTime, server_default=func.now(), nullable=False)
    """When template was assigned"""

    # Relationships
    company = relationship("Company")
    template = relationship("ChartTemplate", back_populates="company_usages")
    assigned_by_user = relationship("User")

    def __repr__(self):
        return f"<CompanyTemplateUsage(company_id='{self.company_id}', template_id='{self.template_id}')>"


# Export
__all__ = [
    "ChartTemplate",
    "ChartTemplateAccount",
    "CompanyTemplateUsage"
]
