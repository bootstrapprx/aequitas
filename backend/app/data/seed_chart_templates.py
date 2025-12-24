"""
Seed Chart Templates - Canon kernels

This script rebuilds onboarding templates using the canonical MasterAccount chart.
It enforces a universal L0 kernel, a full L1 US GAAP standard kernel, and a
pruned-but-complete L2 US GAAP simplified kernel. IFRS templates are disabled
until proper mapping exists.
"""

import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, Sequence
import uuid

# Add backend directory to Python path for direct script execution
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models.chart_template import ChartTemplate, ChartTemplateAccount
from app.db.models.master_account import MasterAccount

# ============================================================================
# Canon constants
# ============================================================================

MANDATORY_L0_CODES: Sequence[str] = (
    "10000",  # Operating Cash
    "10100",  # Undeposited Funds
    "12000",  # Accounts Receivable
    "14000",  # Prepaid Expenses
    "15000",  # Fixed Assets
    "15900",  # Accumulated Depreciation
    "20000",  # Accounts Payable
    "21000",  # Accrued Liabilities
    "22000",  # Taxes Payable
    "23000",  # Deferred Revenue
    "30000",  # Owners Equity / Capital
    "32000",  # Retained Earnings (system)
    "39999",  # Current Period Earnings (system)
    "40000",  # General Operating Revenue
    "49000",  # Refunds / Allowances
    "50000",  # Cost of Goods Sold
    "60000",  # General Operating Expenses
    "61000",  # Payroll Expense
    "62000",  # Depreciation Expense
    "69000",  # Tax Expense
)

L1_CATEGORY_CAPS: Dict[str, int] = {
    "Asset": 40,
    "Liability": 25,
    "Equity": 20,
    "Revenue": 15,
    "Cost of Goods Sold": 20,
    "Expense": 35,
}

L2_CATEGORY_CAPS: Dict[str, int] = {
    "Asset": 15,
    "Liability": 10,
    "Equity": 20,  # full equity structure preserved
    "Revenue": 8,
    "Cost of Goods Sold": 8,
}

SIMPLIFIED_EXPENSE_CODES = {"60000", "61000", "62000", "69000"}

ALLOWED_CATEGORIES = set(L1_CATEGORY_CAPS.keys())

TEMPLATES = {
    "US_GAAP_STANDARD": {"kernel_level": "L1", "enabled": True},
    "US_GAAP_SIMPLIFIED": {"kernel_level": "L2", "enabled": True},
    "IFRS_STANDARD": {
        "enabled": False,
        "reason": "IFRS mapping not implemented in Master Chart",
    },
}

TEMPLATE_METADATA = {
    "US_GAAP_STANDARD": {
        "name": "US GAAP Standard",
        "jurisdiction": "US",
        "description": "US GAAP L1 kernel seeded from canonical MasterAccount.",
    },
    "US_GAAP_SIMPLIFIED": {
        "name": "US GAAP Simplified",
        "jurisdiction": "US",
        "description": "US GAAP L2 kernel (collapsed expenses) seeded from canonical MasterAccount.",
    },
    "IFRS_STANDARD": {
        "name": "IFRS Standard",
        "jurisdiction": "INTL",
        "description": "Disabled until IFRS mapping is present in MasterAccount.",
    },
}

LEGACY_TEMPLATE_NAMES = ["US GAAP Standard", "US GAAP Simplified", "IFRS Standard"]
TEMPLATE_VERSION = "2025.2-kernel"
ONBOARDING_TEMPLATE_INCOMPLETE = "ONBOARDING_TEMPLATE_INCOMPLETE"


# ============================================================================
# Master account helpers
# ============================================================================

def load_master_account_map(db: Session) -> Dict[str, MasterAccount]:
    """Load all master accounts keyed by code."""
    accounts = db.query(MasterAccount).all()
    return {account.code: account for account in accounts if account.code}


def _is_gaap_account(account: MasterAccount) -> bool:
    """Allow only 5-digit GAAP accounts without IFRS dot notation."""
    return (
        account.code.isdigit()
        and len(account.code) == 5
        and account.category in ALLOWED_CATEGORIES
    )


def validate_l0(master_accounts: Dict[str, MasterAccount]) -> None:
    """Validate that all mandatory L0 accounts exist."""
    missing = [code for code in MANDATORY_L0_CODES if code not in master_accounts]
    if missing:
        raise ValueError(
            f"{ONBOARDING_TEMPLATE_INCOMPLETE}: Missing mandatory L0 master accounts {missing}"
        )


def ensure_equity_presence(selected_accounts: Dict[str, MasterAccount]) -> None:
    """Ensure equity and system equity accounts are present."""
    codes = set(selected_accounts.keys())
    missing_codes = [
        code
        for code in ( "32000", "39999" )
        if code not in codes
    ]
    has_equity = any(acc.category == "Equity" for acc in selected_accounts.values())
    if missing_codes or not has_equity:
        detail = []
        if missing_codes:
            detail.append(f"missing equity system accounts {missing_codes}")
        if not has_equity:
            detail.append("no equity accounts present")
        reason = "; ".join(detail)
        raise ValueError(f"{ONBOARDING_TEMPLATE_INCOMPLETE}: {reason}")


def _select_accounts_by_category(
    master_accounts: Dict[str, MasterAccount],
    category_caps: Dict[str, int],
    base_codes: Iterable[str],
) -> Dict[str, MasterAccount]:
    """
    Select accounts per category using deterministic caps to form kernels.
    """
    selected: Dict[str, MasterAccount] = {}
    category_counts: Counter = Counter()

    # Pre-load base codes (L0 + headers)
    for code in base_codes:
        account = master_accounts.get(code)
        if account and _is_gaap_account(account):
            selected[code] = account
            category_counts[account.category] += 1

    headers = [
        acc
        for acc in master_accounts.values()
        if acc.type in {"H", "Header"} and acc.category in category_caps and _is_gaap_account(acc)
    ]
    for header in sorted(headers, key=lambda acc: int(acc.code)):
        if header.code in selected:
            continue
        if category_counts[header.category] >= category_caps[header.category]:
            continue
        selected[header.code] = header
        category_counts[header.category] += 1

    gaap_accounts = [
        acc
        for acc in master_accounts.values()
        if _is_gaap_account(acc)
    ]
    gaap_accounts.sort(key=lambda acc: int(acc.code))

    for account in gaap_accounts:
        if account.code in selected:
            continue
        cap = category_caps.get(account.category)
        if cap is None:
            continue
        if category_counts[account.category] >= cap:
            continue
        selected[account.code] = account
        category_counts[account.category] += 1

    return selected


# ============================================================================
# Kernel builders
# ============================================================================

def build_standard_kernel(master_accounts: Dict[str, MasterAccount]) -> Dict[str, MasterAccount]:
    """Build the L1 US GAAP standard kernel."""
    validate_l0(master_accounts)
    base_codes = set(MANDATORY_L0_CODES)
    selected = _select_accounts_by_category(master_accounts, L1_CATEGORY_CAPS, base_codes)
    ensure_equity_presence(selected)
    return selected


def build_simplified_kernel(
    master_accounts: Dict[str, MasterAccount],
    standard_kernel: Dict[str, MasterAccount],
) -> Dict[str, MasterAccount]:
    """Build the L2 simplified kernel derived from L1."""
    validate_l0(master_accounts)

    base_codes = set(MANDATORY_L0_CODES)
    # Preserve all equity accounts from L1 to keep the closing stack intact.
    for code, account in standard_kernel.items():
        if account.category == "Equity":
            base_codes.add(code)

    # Simplify expenses to the collapsed buckets.
    expense_codes = {
        code for code in standard_kernel if code in SIMPLIFIED_EXPENSE_CODES
    }
    base_codes.update(expense_codes)

    simplified = _select_accounts_by_category(master_accounts, L2_CATEGORY_CAPS, base_codes)
    ensure_equity_presence(simplified)
    return simplified


# ============================================================================
# Template helpers
# ============================================================================

def archive_legacy_templates(db: Session) -> None:
    """Deactivate existing templates so new kernels are used for new onboardings."""
    existing = db.query(ChartTemplate).filter(ChartTemplate.name.in_(LEGACY_TEMPLATE_NAMES)).all()
    for template in existing:
        if template.is_active:
            template.is_active = False


def disable_ifrs_templates(db: Session) -> None:
    """Mark IFRS templates as inactive with reason attached."""
    ifrs_templates = db.query(ChartTemplate).filter(ChartTemplate.jurisdiction == "INTL").all()
    for template in ifrs_templates:
        template.is_active = False
        if template.description:
            if "IFRS mapping not implemented" not in template.description:
                template.description = f"{template.description} | IFRS mapping not implemented in Master Chart"
        else:
            template.description = "IFRS mapping not implemented in Master Chart"


def _create_template_accounts(
    db: Session, template: ChartTemplate, accounts: Iterable[MasterAccount]
) -> int:
    """Create ChartTemplateAccount rows for a template."""
    db.query(ChartTemplateAccount).filter(ChartTemplateAccount.template_id == template.id).delete()

    sorted_accounts = sorted(accounts, key=lambda acc: int(acc.code))
    count = 0
    for sort_order, account in enumerate(sorted_accounts, start=1):
        template_account = ChartTemplateAccount(
            id=uuid.uuid4(),
            template_id=template.id,
            master_account_id=account.id,
            parent_id=None,
            code=account.code,
            name=account.description,
            is_mandatory=True,
            allow_custom_children=True,
            sort_order=sort_order,
            required_module=None,
        )
        db.add(template_account)
        count += 1
    return count


def seed_templates(db: Session) -> Dict[str, int]:
    """
    Seed kernelized templates into the database.

    Returns:
        Dict mapping template key to account counts.
    """
    master_accounts = load_master_account_map(db)
    if not master_accounts:
        raise ValueError("No master accounts found. Seed the master chart before templates.")

    archive_legacy_templates(db)
    disable_ifrs_templates(db)

    kernels: Dict[str, Dict[str, MasterAccount]] = {}
    kernels["L1"] = build_standard_kernel(master_accounts)
    kernels["L2"] = build_simplified_kernel(master_accounts, kernels["L1"])

    seeded_counts: Dict[str, int] = {}

    for key, config in TEMPLATES.items():
        meta = TEMPLATE_METADATA[key]
        enabled = config.get("enabled", False)
        if not enabled:
            continue

        kernel_level = config["kernel_level"]
        accounts = kernels[kernel_level].values()

        template = ChartTemplate(
            id=uuid.uuid4(),
            name=meta["name"],
            jurisdiction=meta["jurisdiction"],
            version=TEMPLATE_VERSION,
            description=meta["description"],
            is_active=True,
        )
        db.add(template)
        db.flush()

        account_count = _create_template_accounts(db, template, accounts)
        seeded_counts[key] = account_count

    return seeded_counts


# ============================================================================
# Entry point
# ============================================================================

def main():
    """Main seeding function."""
    print("\n" + "=" * 60)
    print("  SEEDING CHART TEMPLATES (KERNEL MODE)")
    print("=" * 60 + "\n")

    db = SessionLocal()
    try:
        master_count = db.query(MasterAccount).count()
        print(f"✓ Found {master_count} master accounts\n")

        counts = seed_templates(db)
        db.commit()

        print("\n" + "=" * 60)
        print("  SEEDING COMPLETE")
        print("=" * 60)
        for key, count in counts.items():
            meta = TEMPLATE_METADATA[key]
            print(f"✓ {meta['name']} [{key}] seeded with {count} accounts (v{TEMPLATE_VERSION})")
        print("\nIFRS templates remain disabled until canonical mapping is available.\n")

    except Exception as exc:
        db.rollback()
        print(f"\n❌ ERROR: {exc}\n")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
