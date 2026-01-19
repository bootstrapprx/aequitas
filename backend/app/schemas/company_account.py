"""
CompanyAccount Pydantic schemas.

CANONICAL REFERENCE:
- docs/canonical/DATA_DICTIONARY.md (Section 4.1: company_accounts)
- backend/app/db/models/company_account.py
- Phase 3A: Backend Model Alignment

CRITICAL CHANGES:
- REMOVED: parent_code (use parent_id instead)
- REMOVED: master_account_code (use mapped_master_account_id instead)
- ADDED: All locking fields (is_locked, locked_at, locked_reason, locked_by)
- ADDED: account_type, normal_balance (proper enums)
- ADDED: template_account_id

These schemas MUST match the SQLAlchemy model exactly.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, field_validator


# ==============================================================================
# BASE SCHEMAS
# ==============================================================================

class CompanyAccountBase(BaseModel):
    """
    Base Pydantic model for CompanyAccount attributes.

    NOTE: parent_code and master_account_code are DEPRECATED.
    Use parent_id and mapped_master_account_id instead.
    """

    # Core identification fields
    code: str
    """Company-specific account code (unique within company)"""

    name: Optional[str] = None
    """Display name for the account"""

    description: str
    """Short description of the account"""

    # Classification fields
    type: str
    """DEPRECATED: Use account_type. 'H' (Header) or 'D' (Detail)"""

    account_type: Optional[str] = None
    """Account type enum: Asset, Liability, Equity, Revenue, Expense"""

    normal_balance: str
    """Normal balance side: Debit or Credit"""

    # Hierarchy (UUID FK, NOT string codes)
    parent_id: Optional[uuid.UUID] = None
    """Parent account UUID (NULL for top-level accounts)"""

    # Master chart mapping (UUID FK, NOT string code)
    mapped_master_account_id: Optional[uuid.UUID] = None
    """Mapped master account UUID"""

    # Template reference
    template_account_id: Optional[uuid.UUID] = None
    """Source template account UUID (if derived from template)"""

    # Status fields
    is_active: bool = True
    """Soft delete flag"""

    is_locked: bool = False
    """Lock flag (true = type/code/hierarchy immutable)"""

    # Metadata
    currency: str = "USD"
    """ISO currency code"""

    json_data: Optional[Dict[str, Any]] = None
    """Additional metadata or custom fields"""

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate type is H or D"""
        if v.upper() not in ['H', 'D']:
            raise ValueError('Type must be "H" (Header) or "D" (Detail)')
        return v.upper()

    @field_validator('account_type')
    @classmethod
    def validate_account_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate account_type is one of the allowed enum values"""
        if v is not None:
            allowed = ['Asset', 'Liability', 'Equity', 'Revenue', 'Expense']
            if v not in allowed:
                raise ValueError(f'account_type must be one of: {", ".join(allowed)}')
        return v

    @field_validator('normal_balance')
    @classmethod
    def validate_normal_balance(cls, v: str) -> str:
        """Validate normal_balance is Debit or Credit"""
        if v not in ['Debit', 'Credit']:
            raise ValueError('normal_balance must be "Debit" or "Credit"')
        return v


# ==============================================================================
# CREATE/UPDATE SCHEMAS
# ==============================================================================

class CompanyAccountCreate(CompanyAccountBase):
    """
    Schema for creating a new company account.

    Requires company_id to associate the account with a company.
    """
    company_id: uuid.UUID
    """Owning company UUID"""


class CompanyAccountUpdate(BaseModel):
    """
    Schema for updating a company account.

    All fields are optional (partial update).

    LOCKED ACCOUNT RESTRICTIONS:
    - Cannot change: type, code, account_type, normal_balance, parent_id, mapped_master_account_id
    - Can change: name, description, currency, json_data
    """
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    account_type: Optional[str] = None
    normal_balance: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    mapped_master_account_id: Optional[uuid.UUID] = None
    template_account_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None
    currency: Optional[str] = None
    json_data: Optional[Dict[str, Any]] = None

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate type is H or D"""
        if v is not None and v.upper() not in ['H', 'D']:
            raise ValueError('Type must be "H" (Header) or "D" (Detail)')
        return v.upper() if v else v

    @field_validator('account_type')
    @classmethod
    def validate_account_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate account_type is one of the allowed enum values"""
        if v is not None:
            allowed = ['Asset', 'Liability', 'Equity', 'Revenue', 'Expense']
            if v not in allowed:
                raise ValueError(f'account_type must be one of: {", ".join(allowed)}')
        return v

    @field_validator('normal_balance')
    @classmethod
    def validate_normal_balance(cls, v: Optional[str]) -> Optional[str]:
        """Validate normal_balance is Debit or Credit"""
        if v is not None and v not in ['Debit', 'Credit']:
            raise ValueError('normal_balance must be "Debit" or "Credit"')
        return v


# ==============================================================================
# MASTER CHART ADDITIONS
# ==============================================================================

class CompanyAccountFromMasterRequest(BaseModel):
    """
    Request schema for adding a single account from the master chart catalog.
    """
    master_account_id: uuid.UUID


class CompanyAccountFromCatalogRequest(BaseModel):
    """
    Request schema for adding a single account from the template catalog.
    """
    catalog_account_id: str


# ==============================================================================
# LOCKING SCHEMAS
# ==============================================================================

class CompanyAccountLockRequest(BaseModel):
    """
    Schema for locking an account.

    Locked accounts cannot change type, code, or hierarchy.
    """
    reason: str
    """Locking reason: FirstTransaction, PeriodClose, Manual"""

    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v: str) -> str:
        """Validate reason is one of the allowed values"""
        allowed = ['FirstTransaction', 'PeriodClose', 'Manual']
        if v not in allowed:
            raise ValueError(f'reason must be one of: {", ".join(allowed)}')
        return v


class CompanyAccountUnlockRequest(BaseModel):
    """
    Schema for unlocking an account (requires superuser).

    WARNING: Only allowed if no posted transactions in current period.
    """
    reason: str
    """Reason for unlocking (for audit trail)"""


# ==============================================================================
# RESPONSE SCHEMAS
# ==============================================================================

class CompanyAccountSchema(CompanyAccountBase):
    """
    Schema for representing a company account in API responses.

    Includes all fields plus audit timestamps and locking information.
    """
    id: uuid.UUID
    """Primary key"""

    company_id: uuid.UUID
    """Owning company UUID"""

    # Locking information
    locked_at: Optional[datetime] = None
    """Timestamp when account was locked"""

    locked_reason: Optional[str] = None
    """Reason for locking: FirstTransaction, PeriodClose, Manual"""

    locked_by: Optional[uuid.UUID] = None
    """User UUID who locked the account (for Manual locks)"""

    # Audit timestamps
    created_at: datetime
    """Creation timestamp"""

    updated_at: datetime
    """Last update timestamp"""

    model_config = ConfigDict(from_attributes=True)


class CompanyAccountTree(CompanyAccountSchema):
    """
    Recursive schema for representing an account and its children in a tree structure.

    Used for hierarchical company chart of accounts views.
    """
    children: List['CompanyAccountTree'] = []
    """Child accounts in hierarchy"""


class CompanyAccountListResponse(BaseModel):
    """
    Schema for paginated list of company accounts.
    """
    accounts: List[CompanyAccountSchema]
    total: int
    page: int
    page_size: int


# ==============================================================================
# SPECIALIZED SCHEMAS
# ==============================================================================

class CompanyAccountSummary(BaseModel):
    """
    Lightweight summary schema for company account.

    Used in dropdowns, selects, and journal entry line selections.
    """
    id: uuid.UUID
    code: str
    name: Optional[str] = None
    description: str
    account_type: Optional[str] = None
    normal_balance: str
    is_active: bool
    is_locked: bool

    model_config = ConfigDict(from_attributes=True)


class CompanyAccountWithBalance(CompanyAccountSchema):
    """
    Schema for company account with computed balance.

    Used in trial balance, ledger, and financial statement reports.
    """
    balance: float
    """Computed account balance for the period"""

    debit_total: float = 0.0
    """Total debits for the period"""

    credit_total: float = 0.0
    """Total credits for the period"""


class CompanyAccountMappingInfo(BaseModel):
    """
    Schema for account with master chart mapping information.

    Used in mapping UI and AI suggestion workflows.
    """
    id: uuid.UUID
    code: str
    name: Optional[str] = None
    description: str
    account_type: Optional[str] = None
    mapped_master_account_id: Optional[uuid.UUID] = None
    master_account_code: Optional[str] = None
    master_account_description: Optional[str] = None
    mapping_confidence: Optional[float] = None
    mapping_source: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# EXPORT LIST
# ==============================================================================

__all__ = [
    "CompanyAccountBase",
    "CompanyAccountCreate",
    "CompanyAccountUpdate",
    "CompanyAccountFromMasterRequest",
    "CompanyAccountFromCatalogRequest",
    "CompanyAccountLockRequest",
    "CompanyAccountUnlockRequest",
    "CompanyAccountSchema",
    "CompanyAccountTree",
    "CompanyAccountListResponse",
    "CompanyAccountSummary",
    "CompanyAccountWithBalance",
    "CompanyAccountMappingInfo",
]
