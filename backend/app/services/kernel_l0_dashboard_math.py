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


def compute_tier1_metrics(
    bs_balances: Dict[str, Decimal],
    pl_activity: Dict[str, Decimal]
) -> CoreMetricValues:
    """
    Computes Tier 1 metrics strictly separating Balance Sheet (Stock)
    and Income Statement (Flow) inputs.

    :param bs_balances: Snapshot balances for 1xxxx, 2xxxx, 3xxxx (As of Period End)
    :param pl_activity: Total activity for 4xxxx, 5xxxx, 6xxxx (For the Period)
    """
    
    # 1. Total Cash (Stock) -> Uses BS
    # \Balance(10000, p) + \Balance(10100, p)
    total_cash = bs_balances.get("10000", Decimal("0")) + bs_balances.get("10100", Decimal("0"))

    # 2. Net Revenue (Flow) -> Uses PL
    # \Total(40000, p) - \Total(49000, p)
    net_revenue = pl_activity.get("40000", Decimal("0")) - pl_activity.get("49000", Decimal("0"))

    # 3. Operating Income (Flow) -> Uses PL
    # NetRevenue - COGS - OpEx - Payroll - Dep
    operating_income = (
        net_revenue
        - pl_activity.get("50000", Decimal("0"))
        - pl_activity.get("60000", Decimal("0"))
        - pl_activity.get("61000", Decimal("0"))
        - pl_activity.get("62000", Decimal("0"))
    )

    # 4. Net Working Capital (Stock) -> Uses BS
    # Current Assets - Current Liabilities
    current_assets = sum(bs_balances.get(code, Decimal("0")) for code in CURRENT_ASSET_CODES)
    current_liabilities = sum(bs_balances.get(code, Decimal("0")) for code in CURRENT_LIABILITY_CODES)
    net_working_capital = current_assets - current_liabilities

    # 5. Current Ratio (Stock) -> Uses BS
    # Current Assets / Current Liabilities
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
