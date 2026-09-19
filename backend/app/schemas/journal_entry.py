from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import date, datetime
from uuid import UUID
from typing import Optional, List
from decimal import Decimal


# ===== Journal Entry Line Schemas =====

class JournalEntryLineBase(BaseModel):
    """Base schema for journal entry line"""
    company_account_id: UUID = Field(..., description="Account ID to post to")
    line_number: int = Field(..., description="Line number within entry")
    description: Optional[str] = Field(None, description="Line-level description")
    debit_amount: Decimal = Field(default=Decimal("0.00"), description="Debit amount")
    credit_amount: Decimal = Field(default=Decimal("0.00"), description="Credit amount")

    department_id: Optional[UUID] = Field(None, description="Department dimension")
    cost_center_id: Optional[UUID] = Field(None, description="Cost center dimension")
    project_id: Optional[UUID] = Field(None, description="Project dimension")
    location_id: Optional[UUID] = Field(None, description="Location dimension")

    @field_validator('debit_amount', 'credit_amount')
    @classmethod
    def validate_amounts(cls, v):
        """Ensure amounts are non-negative and have max 2 decimal places"""
        if v < 0:
            raise ValueError("Amount cannot be negative")
        # Round to 2 decimal places
        return round(v, 2)


class JournalEntryLineCreate(JournalEntryLineBase):
    """Schema for creating a journal entry line"""
    pass


class JournalEntryLineInDB(JournalEntryLineBase):
    """Schema for journal entry line in database"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    journal_entry_id: UUID
    created_at: datetime
    updated_at: datetime


class JournalEntryLineResponse(JournalEntryLineInDB):
    """Schema for journal entry line API response"""
    pass


# ===== Journal Entry Schemas =====

class JournalEntryBase(BaseModel):
    """Base schema for journal entry"""
    entry_date: date = Field(..., description="Entry date")
    description: str = Field(..., description="Entry description")
    reference: Optional[str] = Field(None, description="External reference (invoice #, check #, etc.)")
    entry_type: str = Field(default="STANDARD", description="Entry type: STANDARD, ADJUSTING, CLOSING, REVERSING, OPENING")


class JournalEntryCreate(JournalEntryBase):
    """Schema for creating a journal entry"""
    company_id: UUID = Field(..., description="Company ID")
    fiscal_period_id: UUID = Field(..., description="Fiscal period ID")
    lines: List[JournalEntryLineCreate] = Field(..., min_length=2, description="Entry lines (minimum 2)")

    @field_validator('lines')
    @classmethod
    def validate_lines(cls, v):
        """Ensure at least 2 lines and debits equal credits"""
        if len(v) < 2:
            raise ValueError("Journal entry must have at least 2 lines")

        total_debits = sum(line.debit_amount for line in v)
        total_credits = sum(line.credit_amount for line in v)

        if total_debits != total_credits:
            raise ValueError(f"Debits ({total_debits}) must equal credits ({total_credits})")

        # Ensure each line has either debit OR credit (not both, not neither)
        for line in v:
            if line.debit_amount > 0 and line.credit_amount > 0:
                raise ValueError(f"Line {line.line_number} cannot have both debit and credit")
            if line.debit_amount == 0 and line.credit_amount == 0:
                raise ValueError(f"Line {line.line_number} must have either debit or credit")

        return v


class JournalEntryUpdate(BaseModel):
    """Schema for updating a journal entry (only drafts can be updated)"""
    entry_date: Optional[date] = None
    description: Optional[str] = None
    reference: Optional[str] = None
    lines: Optional[List[JournalEntryLineCreate]] = None

    @field_validator('lines')
    @classmethod
    def validate_lines(cls, v):
        """Validate lines if provided"""
        if v is not None:
            if len(v) < 2:
                raise ValueError("Journal entry must have at least 2 lines")

            total_debits = sum(line.debit_amount for line in v)
            total_credits = sum(line.credit_amount for line in v)

            if total_debits != total_credits:
                raise ValueError(f"Debits ({total_debits}) must equal credits ({total_credits})")

        return v


class JournalEntryInDB(JournalEntryBase):
    """Schema for journal entry in database"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    fiscal_period_id: UUID
    entry_number: str
    status: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    posted_at: Optional[datetime] = None
    posted_by: Optional[UUID] = None
    voided_at: Optional[datetime] = None
    voided_by: Optional[UUID] = None
    void_reason: Optional[str] = None
    reverses_entry_id: Optional[UUID] = None
    reversed_by_entry_id: Optional[UUID] = None


class JournalEntryResponse(JournalEntryInDB):
    """Schema for journal entry API response"""
    lines: List[JournalEntryLineResponse] = Field(default_factory=list)
    total_debit: Optional[Decimal] = Field(None, description="Total debit amount")
    total_credit: Optional[Decimal] = Field(None, description="Total credit amount")


class JournalEntryPost(BaseModel):
    """Schema for posting a journal entry"""
    posted_by: UUID = Field(..., description="User ID who is posting the entry")


class JournalEntryVoid(BaseModel):
    """Schema for voiding a journal entry"""
    voided_by: UUID = Field(..., description="User ID who is voiding the entry")
    void_reason: str = Field(..., description="Reason for voiding the entry")


class JournalEntryList(BaseModel):
    """Schema for journal entry list response"""
    entries: List[JournalEntryResponse]
    total: int
    page: int
    page_size: int
