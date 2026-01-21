from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional

# Kernel L0 account codes used by Tier 1 core metrics (authoritative)
KERNEL_L0_CORE_CODES = {
    "10000",
    "10100",
    "12000",
    "14000",
    "20000",
    "21000",
    "22000",
    "23000",
    "40000",
    "49000",
    "50000",
    "60000",
    "61000",
    "62000",
}

BALANCE_SHEET_CODES = {
    "10000",
    "10100",
    "12000",
    "14000",
    "20000",
    "21000",
    "22000",
    "23000",
}

INCOME_STATEMENT_CODES = {
    "40000",
    "49000",
    "50000",
    "60000",
    "61000",
    "62000",
}

REDUCTION_CODES = {
    "49000",  # Refunds / Allowances
    "50000",  # COGS
    "60000",  # General Operating Expenses
    "61000",  # Payroll Expense
    "62000",  # Depreciation Expense
}

CURRENT_ASSET_CODES = {"10000", "10100", "12000", "14000"}
CURRENT_LIABILITY_CODES = {"20000", "21000", "22000", "23000"}


@dataclass(frozen=True)
class CoreMetricValues:
    total_cash: Decimal
    net_revenue: Decimal
    operating_income: Decimal
    net_working_capital: Decimal
    current_ratio: Optional[Decimal]


@dataclass(frozen=True)
class CoreMetricDeltas:
    total_cash: Optional[Decimal]
    net_revenue: Optional[Decimal]
    operating_income: Optional[Decimal]
    net_working_capital: Optional[Decimal]
    current_ratio: Optional[Decimal]


def _round_ratio(value: Optional[Decimal]) -> Optional[Decimal]:
    if value is None:
        return None
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_core_metrics_from_balances(balances: Dict[str, Decimal]) -> CoreMetricValues:
    # Core metric formulas (Tier 1, Kernel L0)
    total_cash = balances["10000"] + balances["10100"]
    net_revenue = balances["40000"] - balances["49000"]
    operating_income = (
        net_revenue
        - balances["50000"]
        - balances["60000"]
        - balances["61000"]
        - balances["62000"]
    )

    current_assets = sum(balances[code] for code in CURRENT_ASSET_CODES)
    current_liabilities = sum(balances[code] for code in CURRENT_LIABILITY_CODES)
    net_working_capital = current_assets - current_liabilities

    current_ratio = None
    if current_liabilities != Decimal("0"):
        current_ratio = _round_ratio(current_assets / current_liabilities)

    return CoreMetricValues(
        total_cash=total_cash,
        net_revenue=net_revenue,
        operating_income=operating_income,
        net_working_capital=net_working_capital,
        current_ratio=current_ratio,
    )


def compute_core_metric_deltas(
    current: CoreMetricValues,
    prior: Optional[CoreMetricValues]
) -> CoreMetricDeltas:
    if prior is None:
        return CoreMetricDeltas(
            total_cash=None,
            net_revenue=None,
            operating_income=None,
            net_working_capital=None,
            current_ratio=None,
        )

    current_ratio_delta = None
    if current.current_ratio is not None and prior.current_ratio is not None:
        current_ratio_delta = current.current_ratio - prior.current_ratio

    return CoreMetricDeltas(
        total_cash=current.total_cash - prior.total_cash,
        net_revenue=current.net_revenue - prior.net_revenue,
        operating_income=current.operating_income - prior.operating_income,
        net_working_capital=current.net_working_capital - prior.net_working_capital,
        current_ratio=current_ratio_delta,
    )
