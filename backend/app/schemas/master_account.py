import uuid
from datetime import date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_validator
from .company_account import CompanyAccountSchema


# --- Base and Common Schemas ---

class MasterAccountBase(BaseModel):
    """Base Pydantic model for MasterAccount attributes."""
    code: Optional[str] = None # Code can be optional on creation for auto-generation
    description: str
    start_date: date
    end_date: Optional[date] = None
    type: str
    category: str
    notes: Optional[str] = None
    parent_code: Optional[str] = None

    @field_validator('type')
    def validate_type(cls, v: str) -> str:
        if v.upper() not in ['H', 'D']:
            raise ValueError('Type must be "H" (Header) or "D" (Detail)')
        return v.upper()

class MasterAccountCreate(MasterAccountBase):
    """Schema for creating a new account. Code is optional."""
    pass

class MasterAccountUpdate(BaseModel):
    """Schema for updating an existing account. All fields are optional."""
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    type: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('type')
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.upper() not in ['H', 'D']:
            raise ValueError('Type must be "H" (Header) or "D" (Detail)')
        return v.upper() if v else v

from .company_account import CompanyAccountSchema

# --- API Response Schemas ---

class MasterAccountSchema(MasterAccountBase):
    """
    Schema for representing a single account in API responses (flat structure).
    """
    id: uuid.UUID
    level: int
    code: str # Code is not optional in responses
    parent_id: Optional[uuid.UUID] = None
    company_accounts: List[CompanyAccountSchema] = []

    model_config = ConfigDict(from_attributes=True)

class MasterAccountTree(MasterAccountSchema):
    """
    Recursive schema for representing an account and its children in a tree structure.
    """
    children: List['MasterAccountTree'] = []

# --- Export List ---

__all__ = [
    "MasterAccountBase",
    "MasterAccountCreate",
    "MasterAccountUpdate",
    "MasterAccountSchema",
    "MasterAccountTree",
]