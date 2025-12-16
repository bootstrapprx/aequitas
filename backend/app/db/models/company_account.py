"""
CompanyAccount SQLAlchemy model.

CANONICAL REFERENCE:
- docs/canonical/DATA_DICTIONARY.md (Section 4.1: company_accounts)
- Phase 3A: Backend Model Alignment

CRITICAL:
- parent_code and master_account_code were DROPPED in migration 022
- Use parent_id and mapped_master_account_id (UUID FKs) instead
- This model MUST match the PostgreSQL schema exactly
"""
import uuid
from sqlalchemy import Column, String, DateTime, func, ForeignKey, Boolean, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.models.enums import AccountType, NormalBalance, LockedReason

# pgvector support
try:
    from pgvector.sqlalchemy import Vector
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False
    Vector = None


class CompanyAccount(Base):
    """
    SQLAlchemy model for a company-specific Chart of Accounts.

    CANONICAL SCHEMA (from DATA_DICTIONARY.md):
    - Company-specific instantiation of the chart
    - Derived from chart templates or custom created
    - Can be locked after first transaction or period close
    - Supports hierarchy, mapping to master chart, and immutability rules

    LIFECYCLE:
    1. Instantiation: Created from template or manually
    2. Customization: Can be renamed, reorganized (before locking)
    3. First Transaction: Account locks (type/code immutable)
    4. Deactivation: Soft delete if unused, hidden if has history

    INVARIANTS:
    - Locked accounts cannot change type, code, hierarchy
    - Accounts with posted entries cannot be deleted
    - Mandatory template accounts cannot be removed
    """
    __tablename__ = "company_accounts"

    # ========================================================================
    # PRIMARY KEY
    # ========================================================================
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # ========================================================================
    # FOREIGN KEYS
    # ========================================================================
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    """Owning company"""

    parent_id = Column(UUID(as_uuid=True), ForeignKey("company_accounts.id", ondelete="CASCADE"), nullable=True, index=True)
    """Parent account in company hierarchy (NULL for top-level accounts)"""

    mapped_master_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("master_accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    """Mapping to canonical master chart account"""

    template_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chart_template_accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    """Source template account (if derived from template)"""

    locked_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    """User who locked the account (if manually locked)"""

    # ========================================================================
    # CORE IDENTIFICATION FIELDS
    # ========================================================================
    code = Column(String, nullable=False, index=True)
    """Company-specific account code (unique within company)"""

    name = Column(String, nullable=True)
    """Display name for the account"""

    description = Column(String, nullable=False)
    """Short description of the account"""

    # ========================================================================
    # CLASSIFICATION FIELDS
    # ========================================================================
    type = Column(String(1), nullable=False)
    """DEPRECATED: Use account_type instead. 'H' (Header) or 'D' (Detail)"""

    account_type = Column(SQLEnum(AccountType, name="accounttype"), nullable=True)
    """Account type enum: Asset, Liability, Equity, Revenue, Expense"""

    normal_balance = Column(SQLEnum(NormalBalance, name="normalbalance"), nullable=False)
    """Normal balance side: Debit or Credit"""

    # ========================================================================
    # STATUS & LOCKING FIELDS
    # ========================================================================
    is_active = Column(Boolean, default=True, nullable=False)
    """Soft delete flag (false = deactivated)"""

    is_locked = Column(Boolean, default=False, nullable=False)
    """Lock flag (true = type/code/hierarchy immutable)"""

    locked_at = Column(DateTime, nullable=True)
    """Timestamp when account was locked"""

    locked_reason = Column(SQLEnum(LockedReason, name="lockedreason"), nullable=True)
    """Reason for locking: FirstTransaction, PeriodClose, Manual"""

    # ========================================================================
    # METADATA FIELDS
    # ========================================================================
    currency = Column(String(3), default="USD", nullable=False)
    """ISO currency code (default: USD)"""

    json_data = Column(JSONB, nullable=True)
    """Additional metadata or custom fields"""

    # ========================================================================
    # SEMANTIC SEARCH SUPPORT (pgvector)
    # ========================================================================
    embedding = Column(Vector(384), nullable=True) if VECTOR_AVAILABLE else Column(ARRAY(float), nullable=True)
    """384-dimensional vector for semantic similarity search"""

    # ========================================================================
    # AUDIT TIMESTAMPS
    # ========================================================================
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    """Creation timestamp"""

    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    """Last update timestamp"""

    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    company = relationship("Company", back_populates="accounts")
    """Owning company"""

    master_account = relationship(
        "MasterAccount",
        back_populates="company_accounts",
        foreign_keys=[mapped_master_account_id]
    )
    """Mapped master chart account"""

    # Self-referential hierarchy relationship
    parent = relationship(
        "CompanyAccount",
        remote_side=[id],
        back_populates="children",
        foreign_keys=[parent_id]
    )
    """Parent account in company hierarchy"""

    children = relationship(
        "CompanyAccount",
        back_populates="parent",
        cascade="all, delete-orphan",
        foreign_keys=[parent_id]
    )
    """Child accounts in company hierarchy"""

    locker = relationship("User", foreign_keys=[locked_by])
    """User who locked the account"""

    # Journal entry lines using this account
    journal_entry_lines = relationship("JournalEntryLine", back_populates="company_account")
    """Journal entry lines referencing this account"""

    # Account balances by fiscal period
    balances = relationship("AccountBalance", back_populates="company_account")
    """Account balances by fiscal period"""

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def __repr__(self):
        return f"<CompanyAccount(company_id='{self.company_id}', code='{self.code}', name='{self.name}')>"

    def can_be_edited(self) -> bool:
        """
        Check if account can be edited.

        Locked accounts cannot change type, code, or hierarchy.
        Name and description can always be edited.

        Returns:
            False if locked, True otherwise
        """
        return not self.is_locked

    def can_be_deleted(self) -> bool:
        """
        Check if account can be deleted.

        Accounts with journal entries cannot be deleted (soft delete only).
        Mandatory template accounts cannot be deleted.

        Returns:
            False if has transactions or is mandatory, True otherwise
        """
        # This would require checking journal_entry_lines
        # For now, return based on lock status
        return not self.is_locked and self.is_active

    def lock(self, reason: LockedReason, user_id: uuid.UUID = None):
        """
        Lock the account.

        Locked accounts cannot change type, code, or hierarchy.

        Args:
            reason: Reason for locking
            user_id: User ID who is locking (for Manual locks)
        """
        self.is_locked = True
        self.locked_at = func.now()
        self.locked_reason = reason
        if reason == LockedReason.MANUAL and user_id:
            self.locked_by = user_id

    def unlock(self):
        """
        Unlock the account (requires superuser privilege in service layer).

        WARNING: Only allowed if no posted transactions in current period.
        """
        self.is_locked = False
        self.locked_at = None
        self.locked_reason = None
        self.locked_by = None

    def deactivate(self):
        """
        Soft delete the account.

        Only allowed if account has no balance and no transactions.
        """
        self.is_active = False

    def reactivate(self):
        """Reactivate a deactivated account."""
        self.is_active = True
