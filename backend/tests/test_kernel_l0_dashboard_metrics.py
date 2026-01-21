from decimal import Decimal

from app.services.kernel_l0_dashboard_math import (
    KERNEL_L0_CORE_CODES,
    compute_core_metrics_from_balances,
    compute_core_metric_deltas,
)


def _balances(overrides: dict[str, Decimal | int | str]) -> dict[str, Decimal]:
    balances = {code: Decimal("0") for code in KERNEL_L0_CORE_CODES}
    for code, value in overrides.items():
        balances[code] = Decimal(str(value))
    return balances


def test_vector_01_empty_company():
    metrics = compute_core_metrics_from_balances(_balances({}))

    assert metrics.total_cash == Decimal("0")
    assert metrics.net_revenue == Decimal("0")
    assert metrics.operating_income == Decimal("0")
    assert metrics.net_working_capital == Decimal("0")
    assert metrics.current_ratio is None


def test_vector_02_cash_only():
    metrics = compute_core_metrics_from_balances(_balances({"10000": 10000}))

    assert metrics.total_cash == Decimal("10000")
    assert metrics.net_revenue == Decimal("0")
    assert metrics.operating_income == Decimal("0")
    assert metrics.net_working_capital == Decimal("10000")
    assert metrics.current_ratio is None


def test_vector_03_simple_revenue_no_costs():
    metrics = compute_core_metrics_from_balances(_balances({"40000": 25000}))

    assert metrics.total_cash == Decimal("0")
    assert metrics.net_revenue == Decimal("25000")
    assert metrics.operating_income == Decimal("25000")
    assert metrics.net_working_capital == Decimal("0")
    assert metrics.current_ratio is None


def test_vector_04_revenue_with_refunds():
    metrics = compute_core_metrics_from_balances(
        _balances({"40000": 50000, "49000": 8000})
    )

    assert metrics.net_revenue == Decimal("42000")
    assert metrics.operating_income == Decimal("42000")


def test_vector_05_full_operating_stack_profit():
    metrics = compute_core_metrics_from_balances(
        _balances({
            "40000": 100000,
            "49000": 5000,
            "50000": 40000,
            "60000": 20000,
            "61000": 25000,
            "62000": 3000,
        })
    )

    assert metrics.net_revenue == Decimal("95000")
    assert metrics.operating_income == Decimal("7000")


def test_vector_06_full_operating_stack_loss():
    metrics = compute_core_metrics_from_balances(
        _balances({
            "40000": 30000,
            "49000": 0,
            "50000": 15000,
            "60000": 12000,
            "61000": 10000,
            "62000": 1000,
        })
    )

    assert metrics.net_revenue == Decimal("30000")
    assert metrics.operating_income == Decimal("-8000")


def test_vector_07_working_capital_positive():
    metrics = compute_core_metrics_from_balances(
        _balances({
            "10000": 20000,
            "10100": 500,
            "12000": 12000,
            "14000": 1500,
            "20000": 8000,
            "21000": 2000,
            "22000": 3000,
            "23000": 6000,
        })
    )

    assert metrics.net_working_capital == Decimal("15000")
    assert metrics.current_ratio == Decimal("1.79")


def test_vector_08_working_capital_negative():
    metrics = compute_core_metrics_from_balances(
        _balances({"10000": 10000, "20000": 25000})
    )

    assert metrics.net_working_capital == Decimal("-15000")
    assert metrics.current_ratio == Decimal("0.40")


def test_vector_09_deferred_revenue_dominance():
    metrics = compute_core_metrics_from_balances(
        _balances({"10000": 50000, "23000": 70000})
    )

    assert metrics.net_working_capital == Decimal("-20000")
    assert metrics.current_ratio == Decimal("0.71")


def test_vector_10_division_by_zero_ratio():
    metrics = compute_core_metrics_from_balances(_balances({"10000": 5000}))

    assert metrics.net_working_capital == Decimal("5000")
    assert metrics.current_ratio is None


def test_vector_11_negative_cash():
    metrics = compute_core_metrics_from_balances(
        _balances({"10000": -2000, "10100": 300})
    )

    assert metrics.total_cash == Decimal("-1700")


def test_vector_12_period_delta_cash_increase():
    prior_metrics = compute_core_metrics_from_balances(_balances({"10000": 9000}))
    current_metrics = compute_core_metrics_from_balances(_balances({"10000": 13700}))

    deltas = compute_core_metric_deltas(current_metrics, prior_metrics)

    assert deltas.total_cash == Decimal("4700")
    assert deltas.current_ratio is None
