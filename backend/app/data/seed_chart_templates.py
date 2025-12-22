"""
Seed Chart Templates - Approach 1: Script-based seeding

This script seeds the chart_templates, chart_template_accounts, and linking tables
with predefined templates that can be selected during onboarding.

PERMISSION MODEL:
- Regular users: Can ADD accounts to their company chart (not subtract/delete mandatory accounts)
- Superusers: Can ADD and SUBTRACT (full CRUD on templates and all accounts)

CANONICAL TEMPLATE STRUCTURE:
- Templates define jurisdiction-specific chart of accounts
- Each template has mandatory accounts (is_mandatory=True) that users CANNOT delete
- Templates allow custom children (allow_custom_children=True) where users CAN add accounts
- Templates reference master_accounts for standardization

Usage:
    cd backend
    python app/data/seed_chart_templates.py
"""

import sys
import os
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.chart_template import ChartTemplate, ChartTemplateAccount
from app.db.models.master_account import MasterAccount
from typing import Dict, List
import uuid


def get_master_account_by_code(db: Session, code: str) -> MasterAccount | None:
    """Fetch master account by code."""
    return db.query(MasterAccount).filter(MasterAccount.code == code).first()


def seed_us_gaap_standard_template(db: Session) -> ChartTemplate:
    """
    Seed the US GAAP Standard Template.

    This is a comprehensive template for US-based businesses following GAAP.

    PERMISSION RULES:
    - Mandatory accounts (is_mandatory=True): Users cannot delete or modify core properties
    - Custom children allowed (allow_custom_children=True): Users can add sub-accounts
    - Non-mandatory accounts: Users can delete if unused
    """

    # Check if template already exists
    existing = db.query(ChartTemplate).filter(
        ChartTemplate.jurisdiction == "US",
        ChartTemplate.name == "US GAAP Standard"
    ).first()

    if existing:
        print(f"✓ Template 'US GAAP Standard' already exists (ID: {existing.id})")
        return existing

    # Create template
    template = ChartTemplate(
        id=uuid.uuid4(),
        name="US GAAP Standard",
        jurisdiction="US",
        version="2025.1",
        description="Standard Chart of Accounts for US businesses following Generally Accepted Accounting Principles (GAAP). "
                    "Includes comprehensive account structure for balance sheet and income statement reporting. "
                    "Suitable for small to medium-sized businesses across various industries.",
        is_active=True
    )

    db.add(template)
    db.flush()  # Get the template ID

    print(f"✓ Created template: {template.name} (ID: {template.id})")

    # Define template accounts structure
    # Structure: (code, name, is_mandatory, allow_custom_children, sort_order, required_module)

    account_definitions = [
        # ASSETS (1.x.x.x) - All mandatory with custom children allowed
        ("1.10.10.10", "Cash", True, True, 1, None),
        ("1.10.20.10", "Accounts Receivable", True, True, 2, None),
        ("1.10.30.10", "Inventory", False, True, 3, None),  # Optional (not all businesses have inventory)
        ("1.10.40.10", "Prepaid Expenses", True, True, 4, None),

        ("1.20.10.10", "Property, Plant & Equipment", True, True, 10, None),
        ("1.20.20.10", "Accumulated Depreciation", True, False, 11, None),  # No custom children for contra accounts
        ("1.20.30.10", "Intangible Assets", False, True, 12, None),

        # LIABILITIES (2.x.x.x)
        ("2.10.10.10", "Accounts Payable", True, True, 20, None),
        ("2.10.20.10", "Accrued Expenses", True, True, 21, None),
        ("2.10.30.10", "Short-term Debt", False, True, 22, None),
        ("2.10.40.10", "Deferred Revenue", False, True, 23, None),

        ("2.20.10.10", "Long-term Debt", False, True, 30, None),
        ("2.20.20.10", "Deferred Tax Liability", False, True, 31, None),

        # EQUITY (3.x.x.x)
        ("3.10.10.10", "Common Stock", True, False, 40, None),  # Mandatory, no custom children
        ("3.10.20.10", "Retained Earnings", True, False, 41, None),  # Mandatory, system-managed
        ("3.10.30.10", "Additional Paid-in Capital", False, True, 42, None),

        # REVENUE (4.x.x.x)
        ("4.10.10.10", "Sales Revenue", True, True, 50, None),
        ("4.10.20.10", "Service Revenue", False, True, 51, None),
        ("4.20.10.10", "Sales Returns and Allowances", True, False, 52, None),  # Contra-revenue

        # EXPENSES (5.x.x.x)
        ("5.10.10.10", "Cost of Goods Sold", False, True, 60, None),  # Optional if service-based
        ("5.20.10.10", "Salaries and Wages", True, True, 70, None),
        ("5.20.20.10", "Rent Expense", True, True, 71, None),
        ("5.20.30.10", "Utilities Expense", True, True, 72, None),
        ("5.20.40.10", "Insurance Expense", True, True, 73, None),
        ("5.20.50.10", "Depreciation Expense", True, True, 74, None),
        ("5.30.10.10", "Marketing and Advertising", False, True, 80, None),
        ("5.30.20.10", "Office Supplies", True, True, 81, None),
        ("5.30.30.10", "Professional Fees", True, True, 82, None),
    ]

    created_count = 0
    for code, name, is_mandatory, allow_custom, sort_order, req_module in account_definitions:
        # Find corresponding master account
        master_account = get_master_account_by_code(db, code)

        if not master_account:
            print(f"  ⚠ Warning: Master account {code} not found, skipping...")
            continue

        template_account = ChartTemplateAccount(
            id=uuid.uuid4(),
            template_id=template.id,
            master_account_id=master_account.id,
            parent_id=None,  # Flat structure for now (can be enhanced with hierarchy)
            code=code,
            name=name,
            is_mandatory=is_mandatory,
            allow_custom_children=allow_custom,
            sort_order=sort_order,
            required_module=req_module
        )

        db.add(template_account)
        created_count += 1

    print(f"  ✓ Added {created_count} accounts to template")

    return template


def seed_us_gaap_simplified_template(db: Session) -> ChartTemplate:
    """
    Seed a simplified US GAAP Template for small businesses and startups.

    This template has fewer accounts and is easier to manage.
    """

    existing = db.query(ChartTemplate).filter(
        ChartTemplate.jurisdiction == "US",
        ChartTemplate.name == "US GAAP Simplified"
    ).first()

    if existing:
        print(f"✓ Template 'US GAAP Simplified' already exists (ID: {existing.id})")
        return existing

    template = ChartTemplate(
        id=uuid.uuid4(),
        name="US GAAP Simplified",
        jurisdiction="US",
        version="2025.1",
        description="Simplified Chart of Accounts for small businesses, startups, and sole proprietors. "
                    "Contains essential accounts for basic bookkeeping and financial reporting. "
                    "Ideal for businesses with straightforward transactions.",
        is_active=True
    )

    db.add(template)
    db.flush()

    print(f"✓ Created template: {template.name} (ID: {template.id})")

    # Simplified account list - fewer accounts, all with custom children allowed
    account_definitions = [
        ("1.10.10.10", "Cash", True, True, 1, None),
        ("1.10.20.10", "Accounts Receivable", True, True, 2, None),

        ("2.10.10.10", "Accounts Payable", True, True, 10, None),

        ("3.10.10.10", "Common Stock", True, False, 20, None),
        ("3.10.20.10", "Retained Earnings", True, False, 21, None),

        ("4.10.10.10", "Sales Revenue", True, True, 30, None),

        ("5.20.10.10", "Salaries and Wages", True, True, 40, None),
        ("5.20.20.10", "Rent Expense", True, True, 41, None),
        ("5.30.20.10", "Office Supplies", True, True, 42, None),
    ]

    created_count = 0
    for code, name, is_mandatory, allow_custom, sort_order, req_module in account_definitions:
        master_account = get_master_account_by_code(db, code)

        if not master_account:
            print(f"  ⚠ Warning: Master account {code} not found, skipping...")
            continue

        template_account = ChartTemplateAccount(
            id=uuid.uuid4(),
            template_id=template.id,
            master_account_id=master_account.id,
            parent_id=None,
            code=code,
            name=name,
            is_mandatory=is_mandatory,
            allow_custom_children=allow_custom,
            sort_order=sort_order,
            required_module=req_module
        )

        db.add(template_account)
        created_count += 1

    print(f"  ✓ Added {created_count} accounts to template")

    return template


def seed_international_template(db: Session) -> ChartTemplate:
    """
    Seed an International (IFRS-based) Template.

    For businesses outside the US following International Financial Reporting Standards.
    """

    existing = db.query(ChartTemplate).filter(
        ChartTemplate.jurisdiction == "INTL",
        ChartTemplate.name == "IFRS Standard"
    ).first()

    if existing:
        print(f"✓ Template 'IFRS Standard' already exists (ID: {existing.id})")
        return existing

    template = ChartTemplate(
        id=uuid.uuid4(),
        name="IFRS Standard",
        jurisdiction="INTL",
        version="2025.1",
        description="International Financial Reporting Standards (IFRS) compliant Chart of Accounts. "
                    "Suitable for businesses operating in jurisdictions that follow IFRS, including "
                    "the UK, EU, Australia, Canada, and many other countries.",
        is_active=True
    )

    db.add(template)
    db.flush()

    print(f"✓ Created template: {template.name} (ID: {template.id})")

    # Similar structure to US GAAP but with IFRS terminology
    account_definitions = [
        ("1.10.10.10", "Cash", True, True, 1, None),
        ("1.10.20.10", "Accounts Receivable", True, True, 2, None),
        ("1.10.40.10", "Prepaid Expenses", True, True, 4, None),

        ("1.20.10.10", "Property, Plant & Equipment", True, True, 10, None),
        ("1.20.20.10", "Accumulated Depreciation", True, False, 11, None),

        ("2.10.10.10", "Accounts Payable", True, True, 20, None),
        ("2.10.20.10", "Accrued Expenses", True, True, 21, None),

        ("3.10.10.10", "Common Stock", True, False, 40, None),
        ("3.10.20.10", "Retained Earnings", True, False, 41, None),

        ("4.10.10.10", "Sales Revenue", True, True, 50, None),

        ("5.20.10.10", "Salaries and Wages", True, True, 70, None),
        ("5.20.20.10", "Rent Expense", True, True, 71, None),
        ("5.20.50.10", "Depreciation Expense", True, True, 74, None),
        ("5.30.20.10", "Office Supplies", True, True, 81, None),
    ]

    created_count = 0
    for code, name, is_mandatory, allow_custom, sort_order, req_module in account_definitions:
        master_account = get_master_account_by_code(db, code)

        if not master_account:
            print(f"  ⚠ Warning: Master account {code} not found, skipping...")
            continue

        template_account = ChartTemplateAccount(
            id=uuid.uuid4(),
            template_id=template.id,
            master_account_id=master_account.id,
            parent_id=None,
            code=code,
            name=name,
            is_mandatory=is_mandatory,
            allow_custom_children=allow_custom,
            sort_order=sort_order,
            required_module=req_module
        )

        db.add(template_account)
        created_count += 1

    print(f"  ✓ Added {created_count} accounts to template")

    return template


def main():
    """Main seeding function."""
    print("\n" + "="*60)
    print("  SEEDING CHART TEMPLATES")
    print("="*60 + "\n")

    db = SessionLocal()

    try:
        # Check if master accounts exist first
        master_count = db.query(MasterAccount).count()
        if master_count == 0:
            print("❌ ERROR: No master accounts found!")
            print("   Please run the master chart seeder first:")
            print("   python app/data/seed_enriched_master_chart.py\n")
            return

        print(f"✓ Found {master_count} master accounts\n")

        # Seed templates
        print("Seeding templates...\n")

        template1 = seed_us_gaap_standard_template(db)
        template2 = seed_us_gaap_simplified_template(db)
        template3 = seed_international_template(db)

        # Commit all changes
        db.commit()

        print("\n" + "="*60)
        print("  SEEDING COMPLETE")
        print("="*60)
        print(f"\n✓ Successfully seeded 3 chart templates")
        print(f"✓ Templates are ready for use in onboarding\n")

        # Print summary
        print("Templates created:")
        print(f"  1. {template1.name} ({template1.jurisdiction}) - v{template1.version}")
        print(f"  2. {template2.name} ({template2.jurisdiction}) - v{template2.version}")
        print(f"  3. {template3.name} ({template3.jurisdiction}) - v{template3.version}")
        print()

    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR: {str(e)}\n")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
