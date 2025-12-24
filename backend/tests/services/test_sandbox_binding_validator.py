"""
Unit Tests: Sandbox Binding Validator (Zone D)

CANONICAL REFERENCE:
- Sandbox Engine Design: Binding Model
- Tests cycle detection and forbidden binding enforcement
"""
import pytest
from uuid import uuid4
from unittest.mock import Mock, MagicMock
from decimal import Decimal

from app.services.sandbox_binding_validator import SandboxBindingValidator
from app.schemas.sandbox import ProjectionType, BindingRuleType, SandboxErrorCode
from app.core.exceptions import ValidationError


class TestBindingCycleDetection:
    """Test circular dependency detection"""

    def test_no_cycle_single_binding(self):
        """Single binding has no cycle"""
        db = Mock()
        db.execute = MagicMock(return_value=MagicMock(fetchall=lambda: []))

        validator = SandboxBindingValidator(db)

        # No existing bindings, add one
        scenario_id = uuid4()
        source_id = uuid4()
        target_id = uuid4()

        # Should not raise
        try:
            validator._validate_no_cycle(scenario_id, source_id, target_id)
        except ValidationError:
            pytest.fail("No cycle should be detected for single binding")

    def test_cycle_detected_simple(self):
        """Detect simple A → B → A cycle"""
        db = Mock()

        scenario_id = uuid4()
        proj_a = uuid4()
        proj_b = uuid4()

        # Existing: A → B
        # Proposed: B → A (creates cycle)
        db.execute = MagicMock(return_value=MagicMock(
            fetchall=lambda: [(proj_a, proj_b)]
        ))

        validator = SandboxBindingValidator(db)

        # Should raise CIRCULAR_BINDING
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_no_cycle(scenario_id, proj_b, proj_a)

        assert exc_info.value.code == SandboxErrorCode.CIRCULAR_BINDING

    def test_cycle_detected_complex(self):
        """Detect complex A → B → C → A cycle"""
        db = Mock()

        scenario_id = uuid4()
        proj_a = uuid4()
        proj_b = uuid4()
        proj_c = uuid4()

        # Existing: A → B, B → C
        # Proposed: C → A (creates cycle)
        db.execute = MagicMock(return_value=MagicMock(
            fetchall=lambda: [(proj_a, proj_b), (proj_b, proj_c)]
        ))

        validator = SandboxBindingValidator(db)

        with pytest.raises(ValidationError) as exc_info:
            validator._validate_no_cycle(scenario_id, proj_c, proj_a)

        assert exc_info.value.code == SandboxErrorCode.CIRCULAR_BINDING

    def test_no_cycle_dag(self):
        """Allow valid DAG: A → B, A → C, B → D, C → D"""
        db = Mock()

        scenario_id = uuid4()
        proj_a = uuid4()
        proj_b = uuid4()
        proj_c = uuid4()
        proj_d = uuid4()

        # Existing: A → B, A → C, B → D
        # Proposed: C → D (valid, no cycle)
        db.execute = MagicMock(return_value=MagicMock(
            fetchall=lambda: [(proj_a, proj_b), (proj_a, proj_c), (proj_b, proj_d)]
        ))

        validator = SandboxBindingValidator(db)

        # Should not raise
        try:
            validator._validate_no_cycle(scenario_id, proj_c, proj_d)
        except ValidationError:
            pytest.fail("Valid DAG should not raise cycle error")


class TestForbiddenBindings:
    """Test forbidden binding enforcement"""

    def test_tax_liability_cannot_drive_expense(self):
        """TAX_LIABILITY → EXPENSE is forbidden"""
        db = Mock()

        source_id = uuid4()
        target_id = uuid4()
        scenario_id = uuid4()

        # Mock projection data
        db.execute = MagicMock(return_value=MagicMock(
            fetchall=lambda: [
                (source_id, scenario_id, ProjectionType.TAX_LIABILITY.value),
                (target_id, scenario_id, ProjectionType.EXPENSE.value)
            ]
        ))

        validator = SandboxBindingValidator(db)

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_binding(
                scenario_id=scenario_id,
                source_projection_id=source_id,
                target_projection_id=target_id,
                rule_type=BindingRuleType.DRIVES
            )

        assert exc_info.value.code == SandboxErrorCode.FORBIDDEN_BINDING
        assert "Tax liability cannot drive expenses" in exc_info.value.message

    def test_tax_liability_cannot_drive_cashflow(self):
        """TAX_LIABILITY → CASHFLOW is forbidden (no auto-payment)"""
        db = Mock()

        source_id = uuid4()
        target_id = uuid4()
        scenario_id = uuid4()

        db.execute = MagicMock(return_value=MagicMock(
            fetchall=lambda: [
                (source_id, scenario_id, ProjectionType.TAX_LIABILITY.value),
                (target_id, scenario_id, ProjectionType.CASHFLOW.value)
            ]
        ))

        validator = SandboxBindingValidator(db)

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_binding(
                scenario_id=scenario_id,
                source_projection_id=source_id,
                target_projection_id=target_id,
                rule_type=BindingRuleType.DRIVES
            )

        assert exc_info.value.code == SandboxErrorCode.FORBIDDEN_BINDING
        assert "when to pay taxes" in exc_info.value.message

    def test_revenue_can_drive_expense(self):
        """REVENUE → EXPENSE is allowed (e.g., commissions)"""
        db = Mock()

        source_id = uuid4()
        target_id = uuid4()
        scenario_id = uuid4()

        # Mock: No existing bindings (no cycle)
        def execute_side_effect(query, params):
            # First call: get projection data
            if "sandbox.projections" in str(query):
                return MagicMock(fetchall=lambda: [
                    (source_id, scenario_id, ProjectionType.REVENUE.value),
                    (target_id, scenario_id, ProjectionType.EXPENSE.value)
                ])
            # Second call: get existing bindings (for cycle check)
            elif "sandbox.bindings" in str(query):
                return MagicMock(fetchall=lambda: [])
            return MagicMock(fetchall=lambda: [])

        db.execute = MagicMock(side_effect=execute_side_effect)

        validator = SandboxBindingValidator(db)

        # Should not raise
        try:
            validator.validate_binding(
                scenario_id=scenario_id,
                source_projection_id=source_id,
                target_projection_id=target_id,
                rule_type=BindingRuleType.DRIVES
            )
        except ValidationError:
            pytest.fail("REVENUE → EXPENSE binding should be allowed")

    def test_revenue_can_drive_tax_liability(self):
        """REVENUE → TAX_LIABILITY is allowed (via profit)"""
        db = Mock()

        source_id = uuid4()
        target_id = uuid4()
        scenario_id = uuid4()

        def execute_side_effect(query, params):
            if "sandbox.projections" in str(query):
                return MagicMock(fetchall=lambda: [
                    (source_id, scenario_id, ProjectionType.REVENUE.value),
                    (target_id, scenario_id, ProjectionType.TAX_LIABILITY.value)
                ])
            elif "sandbox.bindings" in str(query):
                return MagicMock(fetchall=lambda: [])
            return MagicMock(fetchall=lambda: [])

        db.execute = MagicMock(side_effect=execute_side_effect)

        validator = SandboxBindingValidator(db)

        # Should not raise
        try:
            validator.validate_binding(
                scenario_id=scenario_id,
                source_projection_id=source_id,
                target_projection_id=target_id,
                rule_type=BindingRuleType.DRIVES
            )
        except ValidationError:
            pytest.fail("REVENUE → TAX_LIABILITY binding should be allowed")


class TestTaxDerivation:
    """Test tax liability derivation (simulation only)"""

    def test_projected_profit_basis(self):
        """Tax derived from projected profit"""
        from app.services.sandbox_service import SandboxService

        db = Mock()

        # Mock revenue = $100k, expense = $40k → profit = $60k
        # Tax rate = 21% → tax = $12,600
        def execute_side_effect(query, params):
            query_str = str(query)
            if "type = 'REVENUE'" in query_str:
                return MagicMock(scalar=lambda: Decimal('100000'))
            elif "type = 'EXPENSE'" in query_str:
                return MagicMock(scalar=lambda: Decimal('40000'))
            elif "type = 'TAX_LIABILITY'" in query_str:
                return MagicMock(scalar=lambda: Decimal('0'))
            return MagicMock(scalar=lambda: Decimal('0'))

        db.execute = MagicMock(side_effect=execute_side_effect)

        service = SandboxService(db)

        tax = service.derive_tax_liability(
            scenario_id=uuid4(),
            calculation_basis="PROJECTED_PROFIT",
            assumed_rate=Decimal('0.21')
        )

        assert tax == Decimal('12600.00')

    def test_no_tax_on_loss(self):
        """No tax liability if profit is negative"""
        from app.services.sandbox_service import SandboxService

        db = Mock()

        # Mock revenue = $50k, expense = $80k → loss = -$30k
        # Tax = $0 (no tax on loss)
        def execute_side_effect(query, params):
            query_str = str(query)
            if "type = 'REVENUE'" in query_str:
                return MagicMock(scalar=lambda: Decimal('50000'))
            elif "type = 'EXPENSE'" in query_str:
                return MagicMock(scalar=lambda: Decimal('80000'))
            elif "type = 'TAX_LIABILITY'" in query_str:
                return MagicMock(scalar=lambda: Decimal('0'))
            return MagicMock(scalar=lambda: Decimal('0'))

        db.execute = MagicMock(side_effect=execute_side_effect)

        service = SandboxService(db)

        tax = service.derive_tax_liability(
            scenario_id=uuid4(),
            calculation_basis="PROJECTED_PROFIT",
            assumed_rate=Decimal('0.21')
        )

        assert tax == Decimal('0')

    def test_gross_revenue_basis(self):
        """Tax derived from gross revenue (e.g., sales tax)"""
        from app.services.sandbox_service import SandboxService

        db = Mock()

        # Mock revenue = $100k, sales tax = 8.5%
        def execute_side_effect(query, params):
            query_str = str(query)
            if "type = 'REVENUE'" in query_str:
                return MagicMock(scalar=lambda: Decimal('100000'))
            elif "type = 'EXPENSE'" in query_str:
                return MagicMock(scalar=lambda: Decimal('0'))
            elif "type = 'TAX_LIABILITY'" in query_str:
                return MagicMock(scalar=lambda: Decimal('0'))
            return MagicMock(scalar=lambda: Decimal('0'))

        db.execute = MagicMock(side_effect=execute_side_effect)

        service = SandboxService(db)

        tax = service.derive_tax_liability(
            scenario_id=uuid4(),
            calculation_basis="GROSS_REVENUE",
            assumed_rate=Decimal('0.085')
        )

        assert tax == Decimal('8500.00')
