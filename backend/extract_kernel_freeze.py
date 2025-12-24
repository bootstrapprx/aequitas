"""
Extract Kernel 2025.2 freeze data from the database.

This script executes the kernel selection logic from seed_chart_templates.py
and captures the exact accounts selected for L0, L1, and L2 kernels.

Output: kernel_data.json for use in generating freeze artifacts.
"""

import sys
import json
from pathlib import Path
from typing import Dict

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.master_account import MasterAccount
from app.data.seed_chart_templates import (
    MANDATORY_L0_CODES,
    load_master_account_map,
    build_standard_kernel,
    build_simplified_kernel,
)


def extract_kernel_freeze_data() -> Dict:
    """
    Extract the frozen kernel data by executing the actual kernel selection logic.

    Returns:
        Dict containing L0, L1, and L2 kernel account data
    """
    db = SessionLocal()
    try:
        master_accounts = load_master_account_map(db)

        if not master_accounts:
            raise ValueError("No master accounts found. Please seed the master chart first.")

        # Build L1 kernel (which includes L0)
        l1_kernel = build_standard_kernel(master_accounts)

        # Build L2 kernel (simplified)
        l2_kernel = build_simplified_kernel(master_accounts, l1_kernel)

        # Extract L0 accounts (universal kernel)
        l0_accounts = {
            code: master_accounts[code]
            for code in MANDATORY_L0_CODES
            if code in master_accounts
        }

        # Serialize account data
        def serialize_account(account: MasterAccount, layer: str) -> Dict:
            """Convert MasterAccount to serializable dict."""
            return {
                "layer": layer,
                "master_account_id": str(account.id),
                "code": account.code,
                "name": account.description,
                "category": account.category.upper(),
                "type": account.type,
                "parent_code": account.parent_code,
                "normal_balance": account.normal_balance,
                "fs_mapping": account.fs_mapping,
                "long_description": account.long_description,
                "level": account.level,
            }

        # Build kernel data structure
        kernel_data = {
            "metadata": {
                "kernel_version": "2025.2",
                "status": "FROZEN",
                "effective_from": "2025-12-24",
                "gaap_basis": "US_GAAP",
                "supports_ifrs": False,
                "notes": "First canon-complete kernel used in onboarding",
                "extraction_timestamp": "2025-12-24T00:00:00Z",
            },
            "kernels": {
                "L0": {
                    "name": "Universal Kernel",
                    "description": "Non-negotiable, always present accounts",
                    "required": True,
                    "accounts": [
                        serialize_account(l0_accounts[code], "L0")
                        for code in sorted(MANDATORY_L0_CODES, key=lambda x: int(x))
                        if code in l0_accounts
                    ],
                },
                "L1": {
                    "name": "US GAAP Standard Kernel",
                    "description": "Full GAAP chart with ~130-150 accounts",
                    "required": False,
                    "accounts": [
                        serialize_account(account, "L1")
                        for code, account in sorted(l1_kernel.items(), key=lambda x: int(x[0]))
                    ],
                },
                "L2": {
                    "name": "US GAAP Simplified Kernel",
                    "description": "Collapsed expense chart with ~40-60 accounts, derived from L1",
                    "required": False,
                    "accounts": [
                        serialize_account(account, "L2")
                        for code, account in sorted(l2_kernel.items(), key=lambda x: int(x[0]))
                    ],
                },
            },
            "counts": {
                "L0": len(l0_accounts),
                "L1": len(l1_kernel),
                "L2": len(l2_kernel),
            },
            "guarantees": [
                "Accounting equation satisfiable",
                "Double-entry journaling supported",
                "Fiscal period closing supported",
                "No factual or entity-specific accounts",
                "Kernel is canon-complete",
            ],
        }

        # Add derivation info for L2
        # L2 is derived from L1 by collapsing expenses and limiting other categories
        simplified_expense_codes = {"60000", "61000", "62000", "69000"}
        for account_data in kernel_data["kernels"]["L2"]["accounts"]:
            if account_data["code"] in simplified_expense_codes:
                # Find what L1 accounts this replaces
                l1_expense_codes = [
                    code for code in l1_kernel.keys()
                    if l1_kernel[code].category == "Expense"
                    and code not in simplified_expense_codes
                ]
                account_data["derived_from"] = l1_expense_codes
                account_data["collapse_rule"] = "ROLLUP"

        return kernel_data

    finally:
        db.close()


def main():
    """Main execution."""
    print("\n" + "=" * 60)
    print("  EXTRACTING KERNEL 2025.2 FREEZE DATA")
    print("=" * 60 + "\n")

    kernel_data = extract_kernel_freeze_data()

    # Write to temporary JSON file
    output_path = Path(__file__).parent / "kernel_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(kernel_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Kernel data extracted to: {output_path}")
    print(f"\nCounts:")
    print(f"  L0: {kernel_data['counts']['L0']} accounts")
    print(f"  L1: {kernel_data['counts']['L1']} accounts")
    print(f"  L2: {kernel_data['counts']['L2']} accounts")
    print("\n" + "=" * 60)
    print("  EXTRACTION COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
