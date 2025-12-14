"""
MasterAccount Pydantic schemas.

CANONICAL REFERENCE:
- docs/canonical/DATA_DICTIONARY.md (Section 2.1: master_accounts)
- backend/app/db/models/master_account.py
- Phase 3A: Backend Model Alignment

These schemas MUST match the SQLAlchemy model exactly.
"""
import uuid
from datetime import date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_validator


# ==============================================================================
# BASE SCHEMAS
# ==============================================================================

class MasterAccountBase(BaseModel):
    """Base Pydantic model for MasterAccount attributes."""

    # Core identification fields
    code: str
    """Canonical account code (e.g., '1.10.10.10' for Cash)"""

    description: str
    """Short label for the account"""

    long_description: Optional[str] = None
    """Detailed accounting meaning (IFRS/GAAP explanation)"""

    # Classification fields
    type: str
    """Account type: 'H' (Header) or 'D' (Detail)"""

    category: str
    """Account category: ASSET, LIABILITY, EQUITY, REVENUE, COGS, EXPENSE, OTHER"""

    normal_balance: Optional[str] = None
    """Normal balance side: 'Debit' or 'Credit'"""

    # Hierarchy fields
    level: int
    """Hierarchy depth (1 = top level)"""

    parent_id: Optional[uuid.UUID] = None
    """UUID foreign key to parent account"""

    parent_code: Optional[str] = None
    """Legacy string reference to parent code"""

    # Financial statement mapping
    fs_mapping: Optional[str] = None
    """Financial statement placement"""

    cash_flow_classification: Optional[str] = None
    """Cash flow category: Operating, Investing, Financing"""

    # AI & classification fields
    tags: Optional[List[str]] = None
    """AI-friendly keywords for classification"""

    default_vendors: Optional[List[str]] = None
    """Common vendor associations"""

    regulatory_mapping: Optional[dict] = None
    """IFRS/IAS/ASC regulatory references"""

    cost_center: Optional[str] = None
    """Default cost center assignment"""

    # Versioning fields
    version: str
    """Canonical release version (e.g., '2024.1')"""

    start_date: date
    """Validity start date"""

    end_date: Optional[date] = None
    """Validity end date (NULL = currently active)"""

    # Metadata
    notes: Optional[str] = None
    """Additional notes or implementation guidance"""

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate account type is H or D"""
        if v.upper() not in ['H', 'D']:
            raise ValueError('Type must be "H" (Header) or "D" (Detail)')
        return v.upper()

    @field_validator('category')
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate category is one of the allowed values"""
        allowed = ['ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'COGS', 'EXPENSE', 'OTHER']
        if v.upper() not in allowed:
            raise ValueError(f'Category must be one of: {", ".join(allowed)}')
        return v.upper()


# ==============================================================================
# CREATE/UPDATE SCHEMAS
# ==============================================================================

class MasterAccountCreate(MasterAccountBase):
    """
    Schema for creating a new master account.

    All fields from base are required unless marked Optional.
    """
    pass


class MasterAccountUpdate(BaseModel):
    """
    Schema for updating an existing master account.

    All fields are optional (partial update).

    NOTE: Master accounts are generally immutable once published.
    Updates should only be for corrections or new versions.
    """
    description: Optional[str] = None
    long_description: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    normal_balance: Optional[str] = None
    fs_mapping: Optional[str] = None
    cash_flow_classification: Optional[str] = None
    tags: Optional[List[str]] = None
    default_vendors: Optional[List[str]] = None
    regulatory_mapping: Optional[dict] = None
    cost_center: Optional[str] = None
    notes: Optional[str] = None
    end_date: Optional[date] = None

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate account type is H or D"""
        if v is not None and v.upper() not in ['H', 'D']:
            raise ValueError('Type must be "H" (Header) or "D" (Detail)')
        return v.upper() if v else v

    @field_validator('category')
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        """Validate category is one of the allowed values"""
        if v is not None:
            allowed = ['ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'COGS', 'EXPENSE', 'OTHER']
            if v.upper() not in allowed:
                raise ValueError(f'Category must be one of: {", ".join(allowed)}')
            return v.upper()
        return v


# ==============================================================================
# RESPONSE SCHEMAS
# ==============================================================================

class MasterAccountSchema(MasterAccountBase):
    """
    Schema for representing a master account in API responses.

    Includes all fields plus computed/relationship fields.
    """
    id: uuid.UUID
    """Primary key"""

    model_config = ConfigDict(from_attributes=True)


class MasterAccountTree(MasterAccountSchema):
    """
    Recursive schema for representing an account and its children in a tree structure.

    Used for hierarchical chart of accounts views.
    """
    children: List['MasterAccountTree'] = []
    """Child accounts in hierarchy"""


class MasterAccountListResponse(BaseModel):
    """
    Schema for paginated list of master accounts.
    """
    accounts: List[MasterAccountSchema]
    total: int
    page: int
    page_size: int


# ==============================================================================
# SPECIALIZED SCHEMAS
# ==============================================================================

class MasterAccountSummary(BaseModel):
    """
    Lightweight summary schema for master account.

    Used in dropdowns, selects, and references.
    """
    id: uuid.UUID
    code: str
    description: str
    category: str
    type: str
    normal_balance: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MasterAccountAIContext(BaseModel):
    """
    Schema optimized for AI (Dexter) interaction.

    Includes only fields relevant for intelligent account classification.
    """
    code: str
    description: str
    long_description: Optional[str] = None
    category: str
    type: str
    tags: List[str] = []
    default_vendors: List[str] = []
    fs_mapping: Optional[str] = None
    normal_balance: Optional[str] = None
    regulatory_mapping: dict = {}
    parent_code: Optional[str] = None
    level: int


# ==============================================================================
# EXPORT LIST
# ==============================================================================

__all__ = [
    "MasterAccountBase",
    "MasterAccountCreate",
    "MasterAccountUpdate",
    "MasterAccountSchema",
    "MasterAccountTree",
    "MasterAccountListResponse",
    "MasterAccountSummary",
    "MasterAccountAIContext",
]
