"""
Database enums aligned with PostgreSQL enum types.

CANONICAL REFERENCE:
- docs/canonical/DATA_DICTIONARY.md
- PostgreSQL enum definitions (accounttype, normalbalance, etc.)

These enums MUST match PostgreSQL exactly (case-sensitive).
"""
import enum


class AccountType(str, enum.Enum):
    """
    Account type classification.

    PostgreSQL enum: accounttype
    Values: Asset, Liability, Equity, Revenue, Expense

    Corresponds to the five fundamental account categories in
    double-entry bookkeeping.
    """
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"


class NormalBalance(str, enum.Enum):
    """
    Normal balance side for an account.

    PostgreSQL enum: normalbalance
    Values: Debit, Credit

    Defines which side (debit or credit) increases the account balance.
    - Asset, Expense: Debit
    - Liability, Equity, Revenue: Credit
    """
    DEBIT = "Debit"
    CREDIT = "Credit"


class LockedReason(str, enum.Enum):
    """
    Reason why an account is locked.

    PostgreSQL enum: lockedreason
    Values: FirstTransaction, PeriodClose, Manual

    Locked accounts cannot have their type, code, or hierarchy changed.
    """
    FIRST_TRANSACTION = "FirstTransaction"
    PERIOD_CLOSE = "PeriodClose"
    MANUAL = "Manual"


class EntryStatus(str, enum.Enum):
    """
    Journal entry status.

    PostgreSQL enum: entrystatus
    Values: DRAFT, POSTED, VOID

    State machine: DRAFT → POSTED → VOID
    """
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    VOID = "VOID"


class EntryType(str, enum.Enum):
    """
    Journal entry type classification.

    PostgreSQL enum: entrytype
    Values: STANDARD, ADJUSTING, CLOSING, REVERSING, OPENING
    """
    STANDARD = "STANDARD"
    ADJUSTING = "ADJUSTING"
    CLOSING = "CLOSING"
    REVERSING = "REVERSING"
    OPENING = "OPENING"


class PeriodStatus(str, enum.Enum):
    """
    Fiscal period status.

    PostgreSQL enum: periodstatus
    Values: OPEN, CLOSED, LOCKED

    Lifecycle: OPEN → CLOSED → LOCKED → ARCHIVED
    """
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    LOCKED = "LOCKED"


class PeriodType(str, enum.Enum):
    """
    Fiscal period type.

    PostgreSQL enum: periodtype
    Values: MONTH, QUARTER, YEAR
    """
    MONTH = "MONTH"
    QUARTER = "QUARTER"
    YEAR = "YEAR"


class MasterAccountType(str, enum.Enum):
    """
    Master account type: Header or Detail.

    Headers organize structure, Details record transactions.
    """
    HEADER = "H"
    DETAIL = "D"



class OnboardingStatus(str, enum.Enum):
    """
    Company onboarding wizard status.

    PostgreSQL enum: onboardingstatus
    Values: DRAFT, TEMPLATE_SELECTED, CHART_READY, CHART_FINALIZED, ACTIVE

    CANONICAL STATE MACHINE:
    DRAFT → TEMPLATE_SELECTED → CHART_READY → CHART_FINALIZED → ACTIVE

    - DRAFT: Company exists, onboarding in progress (steps 0-1)
    - TEMPLATE_SELECTED: Template chosen, chart not materialized (step 2)
    - CHART_READY: Chart materialized, ready for review (step 3)
    - CHART_FINALIZED: Chart reviewed, fiscal periods setup (step 4-5)
    - ACTIVE: Onboarding complete, accounting active (step 6)

    Rules:
    - Dashboard access allowed only if status = ACTIVE
    - Any other state → redirect to /onboarding/:companyId
    - State transitions only via onboarding endpoints
    """
    DRAFT = "DRAFT"
    TEMPLATE_SELECTED = "TEMPLATE_SELECTED"
    CHART_READY = "CHART_READY"
    CHART_FINALIZED = "CHART_FINALIZED"
    ACTIVE = "ACTIVE"


class ModuleType(str, enum.Enum):
    """
    Optional functional modules for companies.
    Values: ACCOUNTING, FISCAL, INVOICING, CONTRACTS, INVENTORY, PAYROLL
    """
    ACCOUNTING = "ACCOUNTING"
    FISCAL = "FISCAL"
    INVOICING = "INVOICING"
    CONTRACTS = "CONTRACTS"
    INVENTORY = "INVENTORY"
    PAYROLL = "PAYROLL"


# Export all enums
__all__ = [
    "AccountType",
    "NormalBalance",
    "LockedReason",
    "EntryStatus",
    "EntryType",
    "PeriodStatus",
    "PeriodType",
    "MasterAccountType",
    "OnboardingStatus",
    "ModuleType",
]
