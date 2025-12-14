"""
MasterAccount SQLAlchemy model.

CANONICAL REFERENCE:
- docs/canonical/DATA_DICTIONARY.md (Section 2.1: master_accounts)
- Phase 3A: Backend Model Alignment

This model MUST match the PostgreSQL schema exactly.
Database is the source of truth.
"""
import uuid
from sqlalchemy import Column, String, Date, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base

# pgvector support
try:
    from pgvector.sqlalchemy import Vector
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False
    Vector = None


class MasterAccount(Base):
    """
    SQLAlchemy model for the Master Chart of Accounts (US-GAAP reference).

    CANONICAL SCHEMA (from DATA_DICTIONARY.md):
    - Immutable, versioned foundation
    - 345 standardized accounts (7 headers, 338 details)
    - Hierarchical structure using parent_id UUID FK
    - Never company-specific (global reference)

    LIFECYCLE:
    - Seeded via migration
    - Append-only across versions
    - Historical versions preserved via start_date/end_date
    """
    __tablename__ = "master_accounts"

    # ========================================================================
    # PRIMARY KEY
    # ========================================================================
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # ========================================================================
    # CORE IDENTIFICATION FIELDS
    # ========================================================================
    code = Column(String, unique=True, nullable=False, index=True)
    """Canonical account code (e.g., '1.10.10.10' for Cash)"""

    description = Column(String, nullable=False)
    """Short label for the account"""

    long_description = Column(Text, nullable=True)
    """Detailed accounting meaning (IFRS/GAAP explanation)"""

    # ========================================================================
    # CLASSIFICATION FIELDS
    # ========================================================================
    type = Column(String(1), nullable=False)
    """Account type: 'H' (Header) or 'D' (Detail)"""

    category = Column(String, nullable=False)
    """Account category: ASSET, LIABILITY, EQUITY, REVENUE, COGS, EXPENSE, OTHER"""

    normal_balance = Column(String, nullable=True)
    """Normal balance side: 'Debit' or 'Credit'"""

    # ========================================================================
    # HIERARCHY FIELDS
    # ========================================================================
    level = Column(Integer, nullable=False)
    """Hierarchy depth (1 = top level)"""

    parent_id = Column(UUID(as_uuid=True), ForeignKey("master_accounts.id"), nullable=True, index=True)
    """UUID foreign key to parent account (NULL for top-level accounts)"""

    parent_code = Column(String, nullable=True)
    """Legacy string reference to parent code (use parent_id for relationships)"""

    # ========================================================================
    # FINANCIAL STATEMENT MAPPING
    # ========================================================================
    fs_mapping = Column(String, nullable=True)
    """Financial statement placement: 'Balance Sheet', 'Income Statement', etc."""

    cash_flow_classification = Column(String, nullable=True)
    """Cash flow category: 'Operating', 'Investing', 'Financing'"""

    # ========================================================================
    # AI & CLASSIFICATION FIELDS
    # ========================================================================
    tags = Column(ARRAY(String), nullable=True)
    """AI-friendly keywords for classification and search"""

    default_vendors = Column(ARRAY(String), nullable=True)
    """Common vendor associations for auto-suggestion"""

    regulatory_mapping = Column(JSONB, nullable=True)
    """IFRS/IAS/ASC regulatory references (e.g., {"ASC": "310-10-45-2"})"""

    cost_center = Column(String, nullable=True)
    """Default cost center assignment (optional)"""

    # ========================================================================
    # VERSIONING FIELDS
    # ========================================================================
    version = Column(String(10), nullable=False)
    """Canonical release version (e.g., '2024.1')"""

    start_date = Column(Date, nullable=False)
    """Validity start date for this version"""

    end_date = Column(Date, nullable=True)
    """Validity end date (NULL = currently active)"""

    # ========================================================================
    # METADATA FIELDS
    # ========================================================================
    notes = Column(Text, nullable=True)
    """Additional notes or implementation guidance"""

    # ========================================================================
    # SEMANTIC SEARCH SUPPORT (pgvector)
    # ========================================================================
    embedding = Column(Vector(384), nullable=True) if VECTOR_AVAILABLE else Column(ARRAY(float), nullable=True)
    """384-dimensional vector for semantic similarity search (all-MiniLM-L6-v2)"""

    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================

    # Self-referential hierarchy relationship
    parent = relationship(
        "MasterAccount",
        remote_side=[id],
        back_populates="children",
        foreign_keys=[parent_id]
    )
    """Parent account in hierarchy (None for top-level accounts)"""

    children = relationship(
        "MasterAccount",
        back_populates="parent",
        cascade="all, delete-orphan",
        foreign_keys=[parent_id]
    )
    """Child accounts in hierarchy"""

    # Company account mappings
    company_accounts = relationship(
        "CompanyAccount",
        back_populates="master_account",
        foreign_keys="[CompanyAccount.mapped_master_account_id]"
    )
    """Company accounts mapped to this master account"""

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def __repr__(self):
        return f"<MasterAccount(code='{self.code}', description='{self.description}', category='{self.category}')>"

    def as_dict(self):
        """Return object data in easily serializable format"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def to_ai_context(self):
        """
        Return a simplified dict optimized for AI (DEXTER) interaction.
        Includes all relevant fields for intelligent account classification.
        """
        return {
            "code": self.code,
            "description": self.description,
            "long_description": self.long_description,
            "category": self.category,
            "type": self.type,
            "tags": self.tags or [],
            "default_vendors": self.default_vendors or [],
            "fs_mapping": self.fs_mapping,
            "normal_balance": self.normal_balance,
            "regulatory_mapping": self.regulatory_mapping or {},
            "parent_code": self.parent_code,
            "level": self.level,
        }

    def matches_keywords(self, keywords: list[str]) -> bool:
        """
        Check if this account matches any of the given keywords.
        Useful for AI-powered search and classification.

        Args:
            keywords: List of keywords to search for

        Returns:
            True if any keyword matches, False otherwise
        """
        if not keywords:
            return False

        searchable_text = " ".join([
            self.description.lower(),
            self.long_description.lower() if self.long_description else "",
            " ".join(self.tags).lower() if self.tags else "",
            " ".join(self.default_vendors).lower() if self.default_vendors else "",
        ])

        return any(keyword.lower() in searchable_text for keyword in keywords)

    def matches_vendor(self, vendor_name: str) -> bool:
        """
        Check if this account is associated with a given vendor.
        Useful for automatic account suggestion based on vendor.

        Args:
            vendor_name: Vendor name to match

        Returns:
            True if vendor is associated with this account, False otherwise
        """
        if not self.default_vendors or not vendor_name:
            return False

        vendor_lower = vendor_name.lower()
        return any(vendor_lower in v.lower() for v in self.default_vendors)
    
    def to_ai_context(self):
        """
        Return a simplified dict optimized for AI (DEXTER) interaction.
        Includes all relevant fields for intelligent account classification.
        """
        return {
            "code": self.code,
            "description": self.description,
            "long_description": self.long_description,
            "category": self.category,
            "type": self.type,
            "tags": self.tags or [],
            "default_vendors": self.default_vendors or [],
            "fs_mapping": self.fs_mapping,
            "normal_balance": self.normal_balance,
            "regulatory_mapping": self.regulatory_mapping or {},
            "parent_code": self.parent_code,
            "level": self.level,
        }
    
    def matches_keywords(self, keywords: list[str]) -> bool:
        """
        Check if this account matches any of the given keywords.
        Useful for AI-powered search and classification.
        """
        if not keywords:
            return False
        
        searchable_text = " ".join([
            self.description.lower(),
            self.long_description.lower() if self.long_description else "",
            " ".join(self.tags).lower() if self.tags else "",
            " ".join(self.default_vendors).lower() if self.default_vendors else "",
        ])
        
        return any(keyword.lower() in searchable_text for keyword in keywords)
    
    def matches_vendor(self, vendor_name: str) -> bool:
        """
        Check if this account is associated with a given vendor.
        Useful for automatic account suggestion based on vendor.
        """
        if not self.default_vendors or not vendor_name:
            return False
        
        vendor_lower = vendor_name.lower()
        return any(vendor_lower in v.lower() for v in self.default_vendors)
