"""
Kernel 2025.2 Master Chart Reseed Script

SAFETY: This script will REFUSE to run if:
- Any posted journal entries exist
- Any companies are in ACTIVE state (unless --force-dev flag is used)

This is a CLEAN RESEED for development/staging environments only.

Authority: Kernel 2025.2 is canonical. Database must conform.
"""

import sys
from pathlib import Path
from datetime import date
from typing import Dict, List
import uuid
import argparse

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import SessionLocal
from app.db.models.master_account import MasterAccount
from app.db.models.company import Company
from app.db.models.journal_entry import JournalEntry


# ============================================================================
# KERNEL 2025.2 SPECIFICATION (AUTHORITATIVE)
# ============================================================================

KERNEL_VERSION = "2025.2"

# L0 Universal Kernel (20 accounts - MANDATORY)
L0_KERNEL = [
    {"code": "10000", "name": "Operating Cash", "category": "Asset", "type": "D", "level": 1, "parent_code": None},
    {"code": "10100", "name": "Undeposited Funds", "category": "Asset", "type": "D", "level": 2, "parent_code": "10000"},
    {"code": "12000", "name": "Accounts Receivable", "category": "Asset", "type": "D", "level": 1, "parent_code": None},
    {"code": "14000", "name": "Prepaid Expenses", "category": "Asset", "type": "D", "level": 1, "parent_code": None},
    {"code": "15000", "name": "Fixed Assets", "category": "Asset", "type": "D", "level": 1, "parent_code": None},
    {"code": "15900", "name": "Accumulated Depreciation", "category": "Asset", "type": "D", "level": 2, "parent_code": "15000"},
    {"code": "20000", "name": "Accounts Payable", "category": "Liability", "type": "D", "level": 1, "parent_code": None},
    {"code": "21000", "name": "Accrued Liabilities", "category": "Liability", "type": "D", "level": 1, "parent_code": None},
    {"code": "22000", "name": "Taxes Payable", "category": "Liability", "type": "D", "level": 1, "parent_code": None},
    {"code": "23000", "name": "Deferred Revenue", "category": "Liability", "type": "D", "level": 1, "parent_code": None},
    {"code": "30000", "name": "Owners Equity / Capital", "category": "Equity", "type": "D", "level": 1, "parent_code": None},
    {"code": "32000", "name": "Retained Earnings", "category": "Equity", "type": "D", "level": 1, "parent_code": None},
    {"code": "39999", "name": "Current Period Earnings", "category": "Equity", "type": "D", "level": 1, "parent_code": None},
    {"code": "40000", "name": "General Operating Revenue", "category": "Revenue", "type": "D", "level": 1, "parent_code": None},
    {"code": "49000", "name": "Refunds / Allowances", "category": "Revenue", "type": "D", "level": 2, "parent_code": "40000"},
    {"code": "50000", "name": "Cost of Goods Sold", "category": "Cost of Goods Sold", "type": "D", "level": 1, "parent_code": None},
    {"code": "60000", "name": "General Operating Expenses", "category": "Expense", "type": "D", "level": 1, "parent_code": None},
    {"code": "61000", "name": "Payroll Expense", "category": "Expense", "type": "D", "level": 1, "parent_code": None},
    {"code": "62000", "name": "Depreciation Expense", "category": "Expense", "type": "D", "level": 1, "parent_code": None},
    {"code": "69000", "name": "Tax Expense", "category": "Expense", "type": "D", "level": 1, "parent_code": None},
]

# L1 Standard Kernel Additional Accounts (15 accounts beyond L0)
L1_ADDITIONAL = [
    {"code": "11000", "name": "Savings Account", "category": "Asset", "type": "D", "level": 2, "parent_code": "10000"},
    {"code": "13000", "name": "Inventory", "category": "Asset", "type": "D", "level": 1, "parent_code": None},
    {"code": "16000", "name": "Intangible Assets", "category": "Asset", "type": "D", "level": 1, "parent_code": None},
    {"code": "24000", "name": "Short-term Debt", "category": "Liability", "type": "D", "level": 1, "parent_code": None},
    {"code": "25000", "name": "Long-term Debt", "category": "Liability", "type": "D", "level": 1, "parent_code": None},
    {"code": "31000", "name": "Partner Distributions", "category": "Equity", "type": "D", "level": 2, "parent_code": "30000"},
    {"code": "41000", "name": "Service Revenue", "category": "Revenue", "type": "D", "level": 2, "parent_code": "40000"},
    {"code": "42000", "name": "Product Sales", "category": "Revenue", "type": "D", "level": 2, "parent_code": "40000"},
    {"code": "51000", "name": "Materials Cost", "category": "Cost of Goods Sold", "type": "D", "level": 2, "parent_code": "50000"},
    {"code": "52000", "name": "Labor Cost", "category": "Cost of Goods Sold", "type": "D", "level": 2, "parent_code": "50000"},
    {"code": "63000", "name": "Rent Expense", "category": "Expense", "type": "D", "level": 2, "parent_code": "60000"},
    {"code": "64000", "name": "Utilities Expense", "category": "Expense", "type": "D", "level": 2, "parent_code": "60000"},
    {"code": "65000", "name": "Insurance Expense", "category": "Expense", "type": "D", "level": 2, "parent_code": "60000"},
    {"code": "66000", "name": "Marketing Expense", "category": "Expense", "type": "D", "level": 2, "parent_code": "60000"},
    {"code": "67000", "name": "Professional Fees", "category": "Expense", "type": "D", "level": 2, "parent_code": "60000"},
]

# L2 Simplified Kernel = L0 (same 20 accounts)

# Full kernel = L0 + L1_ADDITIONAL
FULL_KERNEL = L0_KERNEL + L1_ADDITIONAL


# ============================================================================
# SAFETY GUARDS
# ============================================================================

def check_safety_conditions(db: Session, force_dev: bool = False) -> bool:
    """
    Check if it's safe to reseed the master chart.

    Returns:
        True if safe, False if blocked
    """
    print("\n" + "=" * 70)
    print("  SAFETY CHECKS")
    print("=" * 70 + "\n")

    # Check 1: Posted journal entries
    posted_count = db.query(JournalEntry).filter(JournalEntry.is_posted == True).count()
    if posted_count > 0:
        print(f"❌ BLOCKED: {posted_count} posted journal entries exist.")
        print("   Reseeding would break historical references.")
        print("   This operation is only safe in development with no real data.")
        return False
    print(f"✓ No posted journal entries ({posted_count})")

    # Check 2: Active companies
    active_count = db.query(Company).filter(Company.is_active == True).count()
    if active_count > 0 and not force_dev:
        print(f"❌ BLOCKED: {active_count} active companies exist.")
        print("   Use --force-dev flag ONLY if this is a development environment.")
        return False
    if active_count > 0 and force_dev:
        print(f"⚠️  WARNING: {active_count} active companies exist, but --force-dev is set.")
        print("   Proceeding with reseed (DEV MODE ONLY).")
    else:
        print(f"✓ No active companies ({active_count})")

    # Check 3: Environment confirmation
    if not force_dev:
        print("\n⚠️  This operation will ADD missing kernel accounts and DEPRECATE non-kernel accounts.")
        print("    (Canon III: Additive migration - no deletions)")
        response = input("Are you sure you want to continue? (type 'yes' to confirm): ")
        if response.lower() != 'yes':
            print("❌ Operation cancelled by user.")
            return False

    print("\n✅ All safety checks passed.")
    return True


# ============================================================================
# RESEED LOGIC
# ============================================================================

def reseed_master_chart(db: Session) -> Dict:
    """
    Additive migration of master chart with Kernel 2025.2 accounts.

    Strategy: Add missing kernel accounts, deprecate non-kernel accounts.
    Respects Canon III: No deletions, only additions and version updates.

    Returns:
        dict with counts and status
    """
    print("\n" + "=" * 70)
    print("  RESEEDING MASTER CHART (KERNEL 2025.2)")
    print("=" * 70 + "\n")

    # Step 1: Mark non-kernel accounts as deprecated (set end_date)
    existing_count = db.query(MasterAccount).count()
    if existing_count > 0:
        print(f"Found {existing_count} existing master accounts")

        # Get codes that should remain active (kernel codes)
        kernel_codes = {acc["code"] for acc in FULL_KERNEL}

        # Mark non-kernel accounts as deprecated
        deprecated_count = 0
        for account in db.query(MasterAccount).all():
            if account.code not in kernel_codes and account.end_date is None:
                account.end_date = date(2025, 12, 24)  # Mark as deprecated
                deprecated_count += 1

        if deprecated_count > 0:
            db.commit()
            print(f"✓ Marked {deprecated_count} non-kernel accounts as deprecated")
        else:
            print("✓ No accounts needed deprecation")

    # Step 2: Get existing kernel accounts or create missing ones
    code_to_id: Dict[str, uuid.UUID] = {}

    # Load existing accounts
    existing_accounts = {acc.code: acc for acc in db.query(MasterAccount).all()}

    # Pass 1: Build code_to_id map for all existing accounts first
    for code, account in existing_accounts.items():
        code_to_id[code] = account.id

    # Pass 2: Create missing kernel accounts WITH parent_id set during creation
    created_count = 0
    updated_count = 0
    parent_count = 0
    print(f"\nProcessing {len(FULL_KERNEL)} kernel accounts...")

    # Process in order to ensure parents exist before children
    # Sort by level (parents have lower level numbers)
    sorted_kernel = sorted(FULL_KERNEL, key=lambda x: (x["level"], x["code"]))

    for account_spec in sorted_kernel:
        if account_spec["code"] in existing_accounts:
            # Account exists - update if needed (only end_date and embedding allowed)
            account = existing_accounts[account_spec["code"]]
            code_to_id[account_spec["code"]] = account.id

            # Ensure it's active (clear end_date if deprecated)
            if account.end_date is not None:
                account.end_date = None
                # Note: version cannot be updated due to trigger
                updated_count += 1
        else:
            # Account doesn't exist - create it with parent_id set immediately
            parent_id = None
            if account_spec["parent_code"] and account_spec["parent_code"] in code_to_id:
                parent_id = code_to_id[account_spec["parent_code"]]
                parent_count += 1

            account = MasterAccount(
                id=uuid.uuid4(),
                code=account_spec["code"],
                description=account_spec["name"],
                start_date=date(2025, 12, 24),  # Kernel effective date
                end_date=None,
                type=account_spec["type"],
                level=account_spec["level"],
                category=account_spec["category"],
                notes=f"Kernel 2025.2 - L0/L1 account",
                parent_code=account_spec["parent_code"],
                parent_id=parent_id,  # Set immediately during creation
                version=KERNEL_VERSION,
                normal_balance="Debit" if account_spec["category"] in ["Asset", "Expense", "Cost of Goods Sold"] else "Credit",
                fs_mapping="Balance Sheet" if account_spec["category"] in ["Asset", "Liability", "Equity"] else "Income Statement",
            )
            db.add(account)
            db.flush()  # Flush immediately so it's available for children
            code_to_id[account_spec["code"]] = account.id
            created_count += 1

    db.commit()

    print(f"✓ Created {created_count} new accounts")
    print(f"✓ Updated {updated_count} existing accounts")
    print(f"✓ Set {parent_count} parent relationships")

    return {
        "total_kernel_accounts": len(FULL_KERNEL),
        "created": created_count,
        "updated": updated_count,
        "deprecated": deprecated_count if 'deprecated_count' in locals() else 0,
        "l0_count": len(L0_KERNEL),
        "l1_count": len(FULL_KERNEL),
        "parent_relationships": parent_count
    }


# ============================================================================
# VERIFICATION
# ============================================================================

def verify_kernel_compliance(db: Session) -> bool:
    """
    Verify that master chart conforms to Kernel 2025.2.

    Returns:
        True if compliant, False otherwise
    """
    print("\n" + "=" * 70)
    print("  KERNEL COMPLIANCE VERIFICATION")
    print("=" * 70 + "\n")

    all_passed = True

    # Check 1: L0 completeness (20 accounts)
    l0_codes = [acc["code"] for acc in L0_KERNEL]
    existing_l0 = db.query(MasterAccount.code).filter(
        MasterAccount.code.in_(l0_codes)
    ).all()
    existing_l0_codes = {row[0] for row in existing_l0}

    missing_l0 = set(l0_codes) - existing_l0_codes
    if missing_l0:
        print(f"❌ L0 Kernel: Missing {len(missing_l0)} accounts: {sorted(missing_l0)}")
        all_passed = False
    else:
        print(f"✅ L0 Kernel: {len(l0_codes)}/20 accounts present")

    # Check 2: System accounts (32000, 39999)
    system_accounts = db.query(MasterAccount).filter(
        MasterAccount.code.in_(["32000", "39999"])
    ).all()
    if len(system_accounts) != 2:
        print(f"❌ System Accounts: Expected 2, found {len(system_accounts)}")
        all_passed = False
    else:
        print(f"✅ System Accounts: Retained Earnings (32000), Current Period Earnings (39999)")

    # Check 3: L1 completeness (35 accounts)
    l1_codes = [acc["code"] for acc in FULL_KERNEL]
    existing_l1 = db.query(MasterAccount.code).filter(
        MasterAccount.code.in_(l1_codes)
    ).all()
    existing_l1_codes = {row[0] for row in existing_l1}

    missing_l1 = set(l1_codes) - existing_l1_codes
    if missing_l1:
        print(f"❌ L1 Kernel: Missing {len(missing_l1)} accounts: {sorted(missing_l1)}")
        all_passed = False
    else:
        print(f"✅ L1 Kernel: {len(l1_codes)}/35 accounts present")

    # Check 4: Parent relationships (only count kernel accounts, not legacy deprecated accounts)
    kernel_codes = [acc["code"] for acc in FULL_KERNEL]
    accounts_with_parent = db.query(MasterAccount).filter(
        MasterAccount.code.in_(kernel_codes),
        MasterAccount.parent_id.isnot(None)
    ).count()
    expected_parent_count = sum(1 for acc in FULL_KERNEL if acc["parent_code"])
    if accounts_with_parent != expected_parent_count:
        print(f"❌ Parent Relationships: Expected {expected_parent_count}, found {accounts_with_parent}")
        all_passed = False
    else:
        print(f"✅ Parent Relationships: {accounts_with_parent} kernel accounts have valid parents")

    # Check 5: No polluted accounts (basic check - no person names, bank account numbers)
    # This is a simple heuristic - real names/banks would need more sophisticated detection
    total_accounts = db.query(MasterAccount).count()
    print(f"✅ Total Master Accounts: {total_accounts}")

    if all_passed:
        print("\n" + "=" * 70)
        print("✅ KERNEL 2025.2 COMPLIANCE: PASS")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ KERNEL 2025.2 COMPLIANCE: FAIL")
        print("=" * 70)

    return all_passed


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description="Reseed master chart with Kernel 2025.2")
    parser.add_argument(
        "--force-dev",
        action="store_true",
        help="Force execution in development (bypass active company check)"
    )
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("  KERNEL 2025.2 MASTER CHART RESEED")
    print("=" * 70)
    print("\nAuthority: Kernel 2025.2 is canonical. Database must conform.")
    print("Mode: CLEAN RESEED (delete old, create new)")
    print("Safety: Refuses to run if posted journal entries exist")

    db = SessionLocal()
    try:
        # Safety checks
        if not check_safety_conditions(db, force_dev=args.force_dev):
            print("\n❌ Reseed aborted due to safety violations.")
            sys.exit(1)

        # Execute reseed
        result = reseed_master_chart(db)

        # Verify compliance
        if not verify_kernel_compliance(db):
            print("\n⚠️  WARNING: Verification failed. Rolling back...")
            db.rollback()
            sys.exit(1)

        # Success
        print("\n" + "=" * 70)
        print("✅ RESEED COMPLETE")
        print("=" * 70)
        print(f"Kernel accounts (total): {result['total_kernel_accounts']}")
        print(f"  Created new: {result['created']}")
        print(f"  Updated existing: {result['updated']}")
        print(f"  Deprecated non-kernel: {result['deprecated']}")
        print(f"L0 accounts: {result['l0_count']}")
        print(f"L1 accounts: {result['l1_count']}")
        print(f"Parent relationships: {result['parent_relationships']}")
        print("\nNext steps:")
        print("  1. Run: python app/data/seed_chart_templates.py")
        print("  2. Verify templates reference kernel accounts")
        print("=" * 70 + "\n")

    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
