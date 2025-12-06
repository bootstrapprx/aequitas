from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime
from uuid import UUID
from typing import Optional, List
from decimal import Decimal


class LedgerEntryBase(BaseModel):
    """Base schema for a ledger entry (from a journal entry line)"""
    entry_date: date
    entry_number: str
    description: str
    reference: Optional[str] = None
    debit_amount: Decimal
    credit_amount: Decimal
    running_balance: Decimal


class LedgerEntryResponse(LedgerEntryBase):
    """Schema for ledger entry API response"""
    model_config = ConfigDict(from_attributes=True)

    journal_entry_id: UUID
    journal_entry_line_id: UUID
    account_code: str
    account_description: str


class AccountLedger(BaseModel):
    """Schema for account ledger (all entries for an account)"""
    company_id: UUID
    company_account_id: UUID
    account_code: str
    account_description: str
    normal_balance: str
    beginning_balance: Decimal
    ending_balance: Decimal
    total_debits: Decimal
    total_credits: Decimal
    entries: List[LedgerEntryResponse]


class GeneralLedger(BaseModel):
    """Schema for general ledger (all accounts)"""
    company_id: UUID
    period_start: date
    period_end: date
    accounts: List[AccountLedger]


class TrialBalanceAccount(BaseModel):
    """Schema for a single account in trial balance"""
    account_code: str
    account_description: str
    account_type: str
    category: str
    normal_balance: str
    debit_balance: Decimal
    credit_balance: Decimal


class TrialBalanceResponse(BaseModel):
    """Schema for trial balance report"""
    company_id: UUID
    period_start: date
    period_end: date
    accounts: List[TrialBalanceAccount]
    total_debits: Decimal
    total_credits: Decimal
    is_balanced: bool
    variance: Decimal = Field(default=Decimal("0.00"))


class AccountBalanceResponse(BaseModel):
    """Schema for account balance"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    company_account_id: UUID
    fiscal_period_id: UUID
    beginning_balance: Decimal
    total_debits: Decimal
    total_credits: Decimal
    ending_balance: Decimal
    account_code: Optional[str] = None
    account_description: Optional[str] = None
