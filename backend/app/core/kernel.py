"""
Kernel constants and helpers.

Canon I: Accounting truth is kernel-derived, not user-derived.
"""
from typing import Dict, Set

from app.db.models.enums import AccountType, NormalBalance, KernelLayer


KERNEL_VERSION = "2025.2"

L0_KERNEL_CODES: Set[str] = {
    "10000", "10100", "12000", "14000", "15000", "15900",
    "20000", "21000", "22000", "23000",
    "30000", "32000", "39999",
    "40000", "49000", "50000",
    "60000", "61000", "62000", "69000",
}

L1_ADDITIONAL_KERNEL_CODES: Set[str] = {
    "11000", "13000", "16000", "24000", "25000",
    "31000", "41000", "42000", "51000", "52000",
    "63000", "64000", "65000", "66000", "67000",
}

L1_KERNEL_CODES: Set[str] = L0_KERNEL_CODES | L1_ADDITIONAL_KERNEL_CODES

CATEGORY_ACCOUNT_TYPE_MAP: Dict[str, AccountType] = {
    "Asset": AccountType.ASSET,
    "Liability": AccountType.LIABILITY,
    "Equity": AccountType.EQUITY,
    "Revenue": AccountType.REVENUE,
    "Expense": AccountType.EXPENSE,
    "Cost of Goods Sold": AccountType.EXPENSE,
    "Other": AccountType.EXPENSE,
}

NORMAL_BALANCE_MAP: Dict[str, NormalBalance] = {
    "Debit": NormalBalance.DEBIT,
    "Credit": NormalBalance.CREDIT,
}


def map_category_to_account_type(category: str | None) -> AccountType:
    if not category:
        return AccountType.EXPENSE
    return CATEGORY_ACCOUNT_TYPE_MAP.get(category, AccountType.EXPENSE)


def map_normal_balance(normal_balance: str | None) -> NormalBalance:
    if not normal_balance:
        return NormalBalance.DEBIT
    return NORMAL_BALANCE_MAP.get(normal_balance, NormalBalance.DEBIT)


def get_kernel_codes(layer: KernelLayer | None) -> Set[str]:
    if layer == KernelLayer.L1:
        return L1_KERNEL_CODES
    return L0_KERNEL_CODES
