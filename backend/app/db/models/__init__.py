"""
Database models package.

CANONICAL REFERENCE:
- docs/canonical/DATA_DICTIONARY.md
- Phase 3A: Backend Model Alignment

All models MUST match PostgreSQL schema exactly.
"""

from .company import Company
from .company_account import CompanyAccount
from .company_module import CompanyModule
from .master_account import MasterAccount
from .snapshot import Snapshot
from .qbo_token import QboToken
from .organizer_memory import OrganizerMemory
from .organizer_rules import OrganizerRule
from .account_mapping import AccountMapping
from .template import Template
from .user import User
from .user_company import UserCompany
from .oauth_account import OAuthAccount
from .pending_registration import PendingRegistration
from .invitation import Invitation
from .group_company import GroupCompany
from .group_company_member import GroupCompanyMember

# Chart template models (Phase 3B)
from .chart_template import ChartTemplate, ChartTemplateAccount, CompanyTemplateUsage

# Accounting models
from .fiscal_period import FiscalPeriod
from .journal_entry import JournalEntry
from .journal_entry_line import JournalEntryLine
from .account_balance import AccountBalance

# Fiscal Engine models
from .entity_tax_profile import EntityTaxProfile
from .tax_ruleset import TaxRuleset
from .tax_run import TaxRun
from .tax_fact import TaxFact
from .tax_adjustment import TaxAdjustment
from .tax_position import TaxPosition

# Dexter Audit models
from .dexter_audit import NormalizationAudit, OnboardingCorrection

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
    "CompanyModule",
    "MasterAccount",
    "Snapshot",
    "QboToken",
    "OrganizerMemory",
    "OrganizerRule",
    "AccountMapping",
    "Template",
    "User",
    "UserCompany",
    "OAuthAccount",
    "PendingRegistration",
    "Invitation",
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
    # Fiscal Engine models
    "EntityTaxProfile",
    "TaxRuleset",
    "TaxRun",
    "TaxFact",
    "TaxAdjustment",
    "TaxPosition",
    # Dexter Audit models
    "NormalizationAudit",
    "OnboardingCorrection",
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

