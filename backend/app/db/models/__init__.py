"""
Database models package.

CANONICAL REFERENCE:
- docs/canonical/DATA_DICTIONARY.md
- Phase 3A: Backend Model Alignment

All models MUST match PostgreSQL schema exactly.
"""

from .company import Company
from .company_account import CompanyAccount
from .master_account import MasterAccount
from .snapshot import Snapshot
from .qbo_token import QboToken
from .organizer_memory import OrganizerMemory
from .organizer_rules import OrganizerRule
from .account_mapping import AccountMapping
from .template import Template
from .user import User
from .user_company import UserCompany
from .pending_registration import PendingRegistration
from .group_company import GroupCompany
from .group_company_member import GroupCompanyMember

# Chart template models (Phase 3B)
from .chart_template import ChartTemplate, ChartTemplateAccount, CompanyTemplateUsage

# Accounting models
from .fiscal_period import FiscalPeriod
from .journal_entry import JournalEntry
from .journal_entry_line import JournalEntryLine
from .account_balance import AccountBalance

# Centralized enums (aligned with PostgreSQL enum types)
from .enums import (
    AccountType,
    NormalBalance,
    LockedReason,
    EntryStatus,
    EntryType,
    PeriodStatus,
    PeriodType,
    MasterAccountType,
)

__all__ = [
    # Core models
    "Company",
    "CompanyAccount",
    "MasterAccount",
    "Snapshot",
    "QboToken",
    "OrganizerMemory",
    "OrganizerRule",
    "AccountMapping",
    "Template",
    "User",
    "UserCompany",
    "PendingRegistration",
    "GroupCompany",
    "GroupCompanyMember",
    # Chart template models (Phase 3B)
    "ChartTemplate",
    "ChartTemplateAccount",
    "CompanyTemplateUsage",
    # Accounting models
    "FiscalPeriod",
    "JournalEntry",
    "JournalEntryLine",
    "AccountBalance",
    # Enums
    "AccountType",
    "NormalBalance",
    "LockedReason",
    "EntryStatus",
    "EntryType",
    "PeriodStatus",
    "PeriodType",
    "MasterAccountType",
]

