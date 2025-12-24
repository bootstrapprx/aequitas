"""
Sandbox Binding Validator (Zone D)

CANONICAL REFERENCE:
- Sandbox Engine Design: Binding Model (Differentiator)
- Canon IV: Intelligence Boundaries

CRITICAL RULES:
- Enforce allowed binding matrix
- Prevent forbidden bindings (especially TAX_LIABILITY → *)
- Detect circular dependencies
- Validate cross-scenario binding attempts
"""
from uuid import UUID
from typing import Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.exceptions import ValidationError
from app.schemas.sandbox import (
    ProjectionType,
    BindingRuleType,
    SandboxErrorCode,
)


# ============================================================================
# BINDING MATRIX (CANONICAL)
# ============================================================================

ALLOWED_BINDINGS = {
    # (source_type, target_type, rule_type): allowed
    (ProjectionType.REVENUE, ProjectionType.EXPENSE, BindingRuleType.DRIVES): True,
    (ProjectionType.REVENUE, ProjectionType.EXPENSE, BindingRuleType.OFFSETS): True,
    (ProjectionType.REVENUE, ProjectionType.EXPENSE, BindingRuleType.CONSTRAINS): True,
    (ProjectionType.REVENUE, ProjectionType.TAX_LIABILITY, BindingRuleType.DRIVES): True,
    (ProjectionType.EXPENSE, ProjectionType.TAX_LIABILITY, BindingRuleType.DRIVES): True,  # Payroll → Payroll Tax
    (ProjectionType.CASHFLOW, ProjectionType.EXPENSE, BindingRuleType.CONSTRAINS): True,
}

FORBIDDEN_BINDINGS = {
    # Tax liability cannot drive anything (it's an outcome, not a driver)
    (ProjectionType.TAX_LIABILITY, ProjectionType.EXPENSE, BindingRuleType.DRIVES): "Tax liability cannot drive expenses. Tax is a value destination, not operational spending.",
    (ProjectionType.TAX_LIABILITY, ProjectionType.CASHFLOW, BindingRuleType.DRIVES): "Tax liability cannot auto-generate cashflow. User must explicitly decide when to pay taxes.",
    (ProjectionType.TAX_LIABILITY, ProjectionType.REVENUE, BindingRuleType.DRIVES): "Tax liability cannot generate revenue.",

    # Expense cannot drive revenue (no deterministic causation)
    (ProjectionType.EXPENSE, ProjectionType.REVENUE, BindingRuleType.DRIVES): "Expenses do not automatically create revenue. Model revenue response separately.",

    # Cashflow cannot drive revenue (receiving cash ≠ earning revenue)
    (ProjectionType.CASHFLOW, ProjectionType.REVENUE, BindingRuleType.DRIVES): "Cash inflow does not automatically create revenue. Revenue recognition is separate.",
}


class SandboxBindingValidator:
    """
    Validates binding creation rules (Zone D).

    CANONICAL COMPLIANCE:
    - Enforces allowed binding matrix
    - Rejects forbidden bindings
    - Prevents circular dependencies
    - Ensures same-scenario bindings only
    """

    def __init__(self, db: Session):
        self.db = db

    def validate_binding(
        self,
        scenario_id: UUID,
        source_projection_id: UUID,
        target_projection_id: UUID,
        rule_type: BindingRuleType
    ):
        """
        Validate binding creation.

        Raises ValidationError if:
        - Projections belong to different scenarios
        - Source and target are same projection
        - Binding type is forbidden
        - Would create circular dependency

        Args:
            scenario_id: Scenario UUID
            source_projection_id: Source projection UUID
            target_projection_id: Target projection UUID
            rule_type: Binding rule type
        """
        # Get projection types and scenario membership
        source_data, target_data = self._get_projection_data(
            source_projection_id,
            target_projection_id
        )

        # Validate same scenario
        if source_data["scenario_id"] != scenario_id or target_data["scenario_id"] != scenario_id:
            raise ValidationError(
                message="Bindings can only connect projections within the same scenario.",
                code=SandboxErrorCode.CROSS_SCENARIO_BINDING
            )

        # Validate not self-binding
        if source_projection_id == target_projection_id:
            raise ValidationError(
                message="Cannot bind a projection to itself.",
                code=SandboxErrorCode.FORBIDDEN_BINDING
            )

        # Validate binding type is allowed
        self._validate_binding_allowed(
            source_type=source_data["type"],
            target_type=target_data["type"],
            rule_type=rule_type
        )

        # Validate no circular dependency (if binding created)
        self._validate_no_cycle(
            scenario_id,
            source_projection_id,
            target_projection_id
        )

    def _get_projection_data(
        self,
        source_id: UUID,
        target_id: UUID
    ) -> Tuple[Dict, Dict]:
        """
        Get projection type and scenario for source and target.

        Returns:
            (source_data, target_data)
        """
        query = text("""
            SELECT id, scenario_id, type
            FROM sandbox.projections
            WHERE id IN (:source_id, :target_id)
        """)

        results = self.db.execute(query, {
            "source_id": str(source_id),
            "target_id": str(target_id)
        }).fetchall()

        if len(results) != 2:
            raise ValidationError(
                message="One or both projections not found.",
                code=SandboxErrorCode.PROJECTION_NOT_FOUND
            )

        projections = {row[0]: {"scenario_id": row[1], "type": row[2]} for row in results}

        if source_id not in projections:
            raise ValidationError(
                message=f"Source projection {source_id} not found.",
                code=SandboxErrorCode.PROJECTION_NOT_FOUND
            )

        if target_id not in projections:
            raise ValidationError(
                message=f"Target projection {target_id} not found.",
                code=SandboxErrorCode.PROJECTION_NOT_FOUND
            )

        return projections[source_id], projections[target_id]

    def _validate_binding_allowed(
        self,
        source_type: str,
        target_type: str,
        rule_type: BindingRuleType
    ):
        """
        Validate binding is in allowed matrix.

        Raises ValidationError if forbidden.
        """
        # Convert string types to enums
        source_enum = ProjectionType(source_type)
        target_enum = ProjectionType(target_type)

        binding_key = (source_enum, target_enum, rule_type)

        # Check if explicitly allowed
        if binding_key in ALLOWED_BINDINGS:
            return  # Allowed

        # Check if explicitly forbidden (with reason)
        if binding_key in FORBIDDEN_BINDINGS:
            reason = FORBIDDEN_BINDINGS[binding_key]
            raise ValidationError(
                message=f"Forbidden binding: {source_type} → {target_type} ({rule_type.value}). {reason}",
                code=SandboxErrorCode.FORBIDDEN_BINDING,
                details={
                    "source_type": source_type,
                    "target_type": target_type,
                    "rule_type": rule_type.value,
                    "reason": reason
                }
            )

        # Default: reject if not explicitly allowed
        raise ValidationError(
            message=f"Binding type not supported: {source_type} → {target_type} ({rule_type.value}). Consult allowed binding matrix.",
            code=SandboxErrorCode.FORBIDDEN_BINDING,
            details={
                "source_type": source_type,
                "target_type": target_type,
                "rule_type": rule_type.value
            }
        )

    def _validate_no_cycle(
        self,
        scenario_id: UUID,
        new_source: UUID,
        new_target: UUID
    ):
        """
        Validate that adding this binding would not create a cycle.

        Uses DFS to detect cycles in directed graph.

        Raises ValidationError if cycle detected.
        """
        # Get all existing bindings + proposed binding
        bindings_query = text("""
            SELECT source_projection_id, target_projection_id
            FROM sandbox.bindings
            WHERE scenario_id = :scenario_id
        """)

        existing_bindings = self.db.execute(bindings_query, {
            "scenario_id": str(scenario_id)
        }).fetchall()

        # Build adjacency list (include proposed binding)
        graph = {}
        for source, target in existing_bindings:
            if source not in graph:
                graph[source] = []
            graph[source].append(target)

        # Add proposed binding
        if new_source not in graph:
            graph[new_source] = []
        graph[new_source].append(new_target)

        # DFS cycle detection
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)

            if node in graph:
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        if has_cycle(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True

            rec_stack.remove(node)
            return False

        # Check all nodes
        for node in graph.keys():
            if node not in visited:
                if has_cycle(node):
                    raise ValidationError(
                        message="This binding would create a circular dependency. Bindings must form a directed acyclic graph (DAG).",
                        code=SandboxErrorCode.CIRCULAR_BINDING,
                        details={
                            "proposed_source": str(new_source),
                            "proposed_target": str(new_target)
                        }
                    )
