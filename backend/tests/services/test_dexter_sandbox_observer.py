"""
Unit Tests: Dexter Sandbox Observer (Zone C Intelligence)

CANONICAL REFERENCE:
- Canon IV: Intelligence Boundaries
- Dexter is advisory only, never authoritative

CRITICAL VERIFICATION:
- Dexter only performs SELECT queries
- NO INSERT, UPDATE, DELETE operations
- NO writes to sandbox or truth tables
"""
import pytest
from uuid import uuid4
from unittest.mock import Mock, MagicMock
from decimal import Decimal

from app.services.dexter_sandbox_observer import DexterSandboxObserver
from app.schemas.sandbox import ProjectionType, TaxType


class TestDexterReadOnlyNature:
    """Verify Dexter cannot mutate data"""

    def test_observer_has_no_write_methods(self):
        """Dexter observer should have no write/mutate methods"""
        db = Mock()
        observer = DexterSandboxObserver(db)

        # Get all public methods
        methods = [m for m in dir(observer) if not m.startswith('_') and callable(getattr(observer, m))]

        # Forbidden method names (should not exist)
        forbidden_keywords = [
            'create', 'update', 'delete', 'insert', 'mutate',
            'write', 'save', 'modify', 'change', 'set', 'execute'
        ]

        for method in methods:
            for keyword in forbidden_keywords:
                assert keyword not in method.lower(), \
                    f"Dexter observer should not have method '{method}' containing '{keyword}'"

    def test_all_queries_are_select_only(self):
        """Verify all database queries are SELECT (not INSERT/UPDATE/DELETE)"""
        db = Mock()
        db.execute = MagicMock(return_value=MagicMock(fetchall=lambda: [], fetchone=lambda: None))

        observer = DexterSandboxObserver(db)

        # Try all read methods
        scenario_id = uuid4()

        try:
            observer.observe_scenario_structure(scenario_id)
        except:
            pass  # Expected if no data, but query should have been SELECT

        try:
            observer.detect_patterns(scenario_id)
        except:
            pass

        try:
            observer.analyze_tax_liability(scenario_id)
        except:
            pass

        try:
            observer.explain_value_destinations(scenario_id)
        except:
            pass

        # Verify all executed queries are SELECT only
        for call in db.execute.call_args_list:
            query = str(call[0][0]).upper()
            assert 'SELECT' in query, "All Dexter queries must be SELECT"
            assert 'INSERT' not in query, "Dexter must not INSERT"
            assert 'UPDATE' not in query, "Dexter must not UPDATE"
            assert 'DELETE' not in query, "Dexter must not DELETE"
            assert 'TRUNCATE' not in query, "Dexter must not TRUNCATE"
            assert 'DROP' not in query, "Dexter must not DROP"


class TestPatternDetection:
    """Test pattern detection heuristics"""

    def test_detect_revenue_concentration_single_source(self):
        """Single revenue source should trigger concentration warning"""
        db = Mock()

        scenario_id = uuid4()
        revenue_id = uuid4()

        # Mock: scenario exists
        def execute_side_effect(query, params):
            query_str = str(query).lower()

            # Scenario query
            if 'from sandbox.scenarios' in query_str:
                return MagicMock(fetchone=lambda: (
                    scenario_id, uuid4(), "Test Scenario", None, "DRAFT",
                    None, None, None, None
                ))

            # Projections query
            elif 'from sandbox.projections' in query_str:
                return MagicMock(fetchall=lambda: [
                    (revenue_id, ProjectionType.REVENUE.value, "Sales", Decimal('100000'),
                     "MONTHLY", None, None, Decimal('1200000'), 12, Decimal('100000'),
                     None, None, None, None, None, None)
                ])

            # Bindings query
            elif 'from sandbox.bindings' in query_str:
                return MagicMock(fetchall=lambda: [])

            return MagicMock(fetchall=lambda: [], fetchone=lambda: None)

        db.execute = MagicMock(side_effect=execute_side_effect)

        observer = DexterSandboxObserver(db)
        patterns = observer.detect_patterns(scenario_id)

        # Should detect revenue concentration
        assert any(p["pattern_type"] == "REVENUE_CONCENTRATION" for p in patterns)

        concentration_pattern = next(p for p in patterns if p["pattern_type"] == "REVENUE_CONCENTRATION")
        assert concentration_pattern["risk_level"] == "HIGH"
        assert revenue_id in concentration_pattern["projections_involved"]

    def test_detect_expense_before_revenue(self):
        """Expenses starting before revenue should be flagged"""
        from datetime import date

        db = Mock()

        scenario_id = uuid4()

        # Mock: expenses start Jan 1, revenue starts Feb 1
        def execute_side_effect(query, params):
            query_str = str(query).lower()

            if 'from sandbox.scenarios' in query_str:
                return MagicMock(fetchone=lambda: (
                    scenario_id, uuid4(), "Test", None, "DRAFT", None, None, None, None
                ))

            elif 'from sandbox.projections' in query_str:
                return MagicMock(fetchall=lambda: [
                    (uuid4(), ProjectionType.EXPENSE.value, "Rent", Decimal('5000'),
                     "MONTHLY", date(2024, 1, 1), None, Decimal('60000'), 12, Decimal('5000'),
                     None, None, None, None, None, None),
                    (uuid4(), ProjectionType.REVENUE.value, "Sales", Decimal('10000'),
                     "MONTHLY", date(2024, 2, 1), None, Decimal('110000'), 11, Decimal('10000'),
                     None, None, None, None, None, None)
                ])

            elif 'from sandbox.bindings' in query_str:
                return MagicMock(fetchall=lambda: [])

            return MagicMock(fetchall=lambda: [], fetchone=lambda: None)

        db.execute = MagicMock(side_effect=execute_side_effect)

        observer = DexterSandboxObserver(db)
        patterns = observer.detect_patterns(scenario_id)

        # Should detect expense timing mismatch
        assert any(p["pattern_type"] == "EXPENSE_BEFORE_REVENUE" for p in patterns)

    def test_detect_negative_cashflow(self):
        """Negative profit should be flagged"""
        db = Mock()

        scenario_id = uuid4()

        # Mock: expenses > revenue
        def execute_side_effect(query, params):
            query_str = str(query).lower()

            if 'from sandbox.scenarios' in query_str:
                return MagicMock(fetchone=lambda: (
                    scenario_id, uuid4(), "Test", None, "DRAFT", None, None, None, None
                ))

            elif 'from sandbox.projections' in query_str:
                return MagicMock(fetchall=lambda: [
                    (uuid4(), ProjectionType.REVENUE.value, "Sales", Decimal('50000'),
                     "MONTHLY", None, None, Decimal('600000'), 12, Decimal('50000'),
                     None, None, None, None, None, None),
                    (uuid4(), ProjectionType.EXPENSE.value, "Costs", Decimal('60000'),
                     "MONTHLY", None, None, Decimal('720000'), 12, Decimal('60000'),
                     None, None, None, None, None, None)
                ])

            elif 'from sandbox.bindings' in query_str:
                return MagicMock(fetchall=lambda: [])

            return MagicMock(fetchall=lambda: [], fetchone=lambda: None)

        db.execute = MagicMock(side_effect=execute_side_effect)

        observer = DexterSandboxObserver(db)
        patterns = observer.detect_patterns(scenario_id)

        # Should detect negative cashflow
        assert any(p["pattern_type"] == "NEGATIVE_CASHFLOW" for p in patterns)

        negative_pattern = next(p for p in patterns if p["pattern_type"] == "NEGATIVE_CASHFLOW")
        assert negative_pattern["risk_level"] == "HIGH"


class TestTaxLiabilityIntelligence:
    """Test tax liability analysis"""

    def test_missing_tax_projection_detection(self):
        """Profitable scenario with no tax should be flagged"""
        db = Mock()

        scenario_id = uuid4()

        # Mock: profit > 0, no tax projections
        def execute_side_effect(query, params):
            query_str = str(query).lower()

            if 'from sandbox.scenarios' in query_str:
                return MagicMock(fetchone=lambda: (
                    scenario_id, uuid4(), "Test", None, "DRAFT", None, None, None, None
                ))

            elif 'from sandbox.projections' in query_str:
                return MagicMock(fetchall=lambda: [
                    (uuid4(), ProjectionType.REVENUE.value, "Sales", Decimal('100000'),
                     "MONTHLY", None, None, Decimal('1200000'), 12, Decimal('100000'),
                     None, None, None, None, None, None),
                    (uuid4(), ProjectionType.EXPENSE.value, "Costs", Decimal('60000'),
                     "MONTHLY", None, None, Decimal('720000'), 12, Decimal('60000'),
                     None, None, None, None, None, None)
                ])

            elif 'from sandbox.bindings' in query_str:
                return MagicMock(fetchall=lambda: [])

            return MagicMock(fetchall=lambda: [], fetchone=lambda: None)

        db.execute = MagicMock(side_effect=execute_side_effect)

        observer = DexterSandboxObserver(db)
        tax_analysis = observer.analyze_tax_liability(scenario_id)

        # Should detect missing tax
        assert not tax_analysis["has_tax_projections"]
        assert len(tax_analysis["recommendations"]) > 0

        # Should recommend adding tax
        assert any(
            "MISSING_FEDERAL_INCOME_TAX" in r.get("recommendation_type", "")
            for r in tax_analysis["recommendations"]
        )

    def test_missing_payroll_tax_detection(self):
        """Payroll expenses without payroll tax should be flagged"""
        db = Mock()

        scenario_id = uuid4()

        # Mock: payroll expense but no payroll tax
        def execute_side_effect(query, params):
            query_str = str(query).lower()

            if 'from sandbox.scenarios' in query_str:
                return MagicMock(fetchone=lambda: (
                    scenario_id, uuid4(), "Test", None, "DRAFT", None, None, None, None
                ))

            elif 'from sandbox.projections' in query_str:
                return MagicMock(fetchall=lambda: [
                    (uuid4(), ProjectionType.REVENUE.value, "Sales", Decimal('100000'),
                     "MONTHLY", None, None, Decimal('1200000'), 12, Decimal('100000'),
                     None, None, None, None, None, None),
                    (uuid4(), ProjectionType.EXPENSE.value, "Payroll Costs", Decimal('50000'),
                     "MONTHLY", None, None, Decimal('600000'), 12, Decimal('50000'),
                     None, None, None, None, None, None)
                ])

            elif 'from sandbox.bindings' in query_str:
                return MagicMock(fetchall=lambda: [])

            return MagicMock(fetchall=lambda: [], fetchone=lambda: None)

        db.execute = MagicMock(side_effect=execute_side_effect)

        observer = DexterSandboxObserver(db)
        tax_analysis = observer.analyze_tax_liability(scenario_id)

        # Should detect missing payroll tax
        missing_types = tax_analysis["missing_tax_types"]
        assert any(
            "MISSING_PAYROLL_TAX" in m.get("recommendation_type", "")
            for m in missing_types
        )

    def test_effective_tax_rate_calculation(self):
        """Verify effective tax rate is calculated correctly"""
        db = Mock()

        scenario_id = uuid4()

        # Mock: $100k profit, $21k tax = 21% effective rate
        def execute_side_effect(query, params):
            query_str = str(query).lower()

            if 'from sandbox.scenarios' in query_str:
                return MagicMock(fetchone=lambda: (
                    scenario_id, uuid4(), "Test", None, "ACTIVE", None, None, None, None
                ))

            elif 'from sandbox.projections' in query_str:
                return MagicMock(fetchall=lambda: [
                    (uuid4(), ProjectionType.REVENUE.value, "Sales", Decimal('150000'),
                     "ANNUAL", None, None, Decimal('150000'), 1, Decimal('12500'),
                     None, None, None, None, None, None),
                    (uuid4(), ProjectionType.EXPENSE.value, "Costs", Decimal('50000'),
                     "ANNUAL", None, None, Decimal('50000'), 1, Decimal('4167'),
                     None, None, None, None, None, None),
                    (uuid4(), ProjectionType.TAX_LIABILITY.value, "Federal Income Tax", Decimal('21000'),
                     None, None, None, Decimal('21000'), None, None,
                     "US", TaxType.FEDERAL_INCOME.value, "PROJECTED_PROFIT", Decimal('0.21'),
                     "21% federal corporate tax", "MEDIUM")
                ])

            elif 'from sandbox.bindings' in query_str:
                return MagicMock(fetchall=lambda: [])

            return MagicMock(fetchall=lambda: [], fetchone=lambda: None)

        db.execute = MagicMock(side_effect=execute_side_effect)

        observer = DexterSandboxObserver(db)
        tax_analysis = observer.analyze_tax_liability(scenario_id)

        # Effective rate should be 21% (21k / 100k profit)
        assert tax_analysis["has_tax_projections"]
        assert tax_analysis["effective_tax_rate"] == Decimal('0.21')


class TestValueDestinationAnalysis:
    """Test value destination explanations"""

    def test_value_destination_breakdown(self):
        """Verify value destinations are calculated correctly"""
        db = Mock()

        scenario_id = uuid4()

        # Mock: $1M revenue, $600k expenses, $84k tax, $316k retained
        def execute_side_effect(query, params):
            query_str = str(query).lower()

            if 'from sandbox.scenarios' in query_str:
                return MagicMock(fetchone=lambda: (
                    scenario_id, uuid4(), "Test", None, "ACTIVE", None, None, None, None
                ))

            elif 'from sandbox.projections' in query_str:
                return MagicMock(fetchall=lambda: [
                    (uuid4(), ProjectionType.REVENUE.value, "Sales", Decimal('1000000'),
                     "ANNUAL", None, None, Decimal('1000000'), 1, Decimal('83333'),
                     None, None, None, None, None, None),
                    (uuid4(), ProjectionType.EXPENSE.value, "Costs", Decimal('600000'),
                     "ANNUAL", None, None, Decimal('600000'), 1, Decimal('50000'),
                     None, None, None, None, None, None),
                    (uuid4(), ProjectionType.TAX_LIABILITY.value, "Tax", Decimal('84000'),
                     None, None, None, Decimal('84000'), None, None,
                     "US", TaxType.FEDERAL_INCOME.value, "PROJECTED_PROFIT", Decimal('0.21'),
                     "21% tax", "HIGH")
                ])

            elif 'from sandbox.bindings' in query_str:
                return MagicMock(fetchall=lambda: [])

            return MagicMock(fetchall=lambda: [], fetchone=lambda: None)

        db.execute = MagicMock(side_effect=execute_side_effect)

        observer = DexterSandboxObserver(db)
        value_dest = observer.explain_value_destinations(scenario_id)

        # Verify calculations
        assert value_dest["total_revenue"] == Decimal('1000000')
        assert value_dest["destinations"]["operating_expense"] == Decimal('600000')
        assert value_dest["destinations"]["tax_liability"] == Decimal('84000')
        assert value_dest["destinations"]["net_retained"] == Decimal('316000')

        # Verify percentages
        assert value_dest["percentages"]["operating_expense_pct"] == Decimal('60.0')
        assert value_dest["percentages"]["tax_liability_pct"] == Decimal('8.4')
        assert value_dest["percentages"]["net_retained_pct"] == Decimal('31.6')

        # Explanation should exist
        assert len(value_dest["explanation"]) > 0
        assert "Revenue Distribution" in value_dest["explanation"]


class TestScenarioComparison:
    """Test scenario comparison"""

    def test_compare_two_scenarios(self):
        """Verify scenarios can be compared side-by-side"""
        db = Mock()

        scenario_1 = uuid4()
        scenario_2 = uuid4()

        # Mock: Conservative vs Aggressive
        def execute_side_effect(query, params):
            query_str = str(query).lower()
            scenario_id = params.get("scenario_id")

            if 'from sandbox.scenarios' in query_str:
                if scenario_id == str(scenario_1):
                    return MagicMock(fetchone=lambda: (
                        scenario_1, uuid4(), "Conservative", None, "ACTIVE", None, None, None, None
                    ))
                else:
                    return MagicMock(fetchone=lambda: (
                        scenario_2, uuid4(), "Aggressive", None, "ACTIVE", None, None, None, None
                    ))

            elif 'from sandbox.projections' in query_str:
                if scenario_id == str(scenario_1):
                    # Conservative: $500k revenue, $300k expense
                    return MagicMock(fetchall=lambda: [
                        (uuid4(), ProjectionType.REVENUE.value, "Sales", Decimal('500000'),
                         None, None, None, Decimal('500000'), None, None, None, None, None, None, None, None),
                        (uuid4(), ProjectionType.EXPENSE.value, "Costs", Decimal('300000'),
                         None, None, None, Decimal('300000'), None, None, None, None, None, None, None, None)
                    ])
                else:
                    # Aggressive: $1M revenue, $650k expense
                    return MagicMock(fetchall=lambda: [
                        (uuid4(), ProjectionType.REVENUE.value, "Sales", Decimal('1000000'),
                         None, None, None, Decimal('1000000'), None, None, None, None, None, None, None, None),
                        (uuid4(), ProjectionType.EXPENSE.value, "Costs", Decimal('650000'),
                         None, None, None, Decimal('650000'), None, None, None, None, None, None, None, None)
                    ])

            elif 'from sandbox.bindings' in query_str:
                return MagicMock(fetchall=lambda: [])

            return MagicMock(fetchall=lambda: [], fetchone=lambda: None)

        db.execute = MagicMock(side_effect=execute_side_effect)

        observer = DexterSandboxObserver(db)
        comparison = observer.compare_scenarios([scenario_1, scenario_2])

        # Verify comparison structure
        assert len(comparison["comparison_matrix"]["scenario_names"]) == 2
        assert "Conservative" in comparison["comparison_matrix"]["scenario_names"]
        assert "Aggressive" in comparison["comparison_matrix"]["scenario_names"]

        # Verify recommendation exists
        assert len(comparison["recommendation"]) > 0
