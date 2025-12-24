"""
Sandbox Service (Zone D)

CANONICAL REFERENCE:
- Sandbox Engine Design (Authoritative)
- Canon IV: Intelligence Boundaries

CRITICAL RULES:
- Never write to truth tables (public schema)
- All writes go to sandbox schema only
- Tax liability = simulation, not accounting liability
- ACTIVE/ARCHIVED scenarios are immutable
- Bindings must be cycle-free
"""
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, text

from app.core.exceptions import ValidationError
from app.schemas.sandbox import (
    ScenarioStatus,
    ProjectionType,
    BindingRuleType,
    SandboxErrorCode,
)


class SandboxService:
    """
    Service for Sandbox Engine (Zone D - Simulation & Future)

    CANONICAL COMPLIANCE:
    - All operations isolated to sandbox schema
    - No writes to truth tables
    - ACTIVE scenarios are immutable
    - Tax projections are estimates only
    """

    def __init__(self, db: Session):
        self.db = db

    # ========================================================================
    # SCENARIO OPERATIONS
    # ========================================================================

    def create_scenario(
        self,
        company_id: UUID,
        name: str,
        description: Optional[str],
        created_by: UUID
    ) -> Dict[str, Any]:
        """
        Create new scenario in DRAFT state.

        Args:
            company_id: Company UUID
            name: Scenario name
            description: Optional description
            created_by: User UUID who created scenario

        Returns:
            Scenario record
        """
        query = text("""
            INSERT INTO sandbox.scenarios (
                company_id, name, description, status, created_by, created_at, updated_at
            ) VALUES (
                :company_id, :name, :description, 'DRAFT', :created_by, NOW(), NOW()
            )
            RETURNING id, company_id, name, description, status, created_by, created_at, updated_at
        """)

        result = self.db.execute(query, {
            "company_id": str(company_id),
            "name": name,
            "description": description,
            "created_by": str(created_by)
        }).fetchone()

        self.db.commit()

        return {
            "id": result[0],
            "company_id": result[1],
            "name": result[2],
            "description": result[3],
            "status": result[4],
            "created_by": result[5],
            "created_at": result[6],
            "updated_at": result[7]
        }

    def get_scenario(self, scenario_id: UUID, company_id: UUID) -> Dict[str, Any]:
        """
        Get scenario by ID (company-scoped).

        Args:
            scenario_id: Scenario UUID
            company_id: Company UUID (for authorization)

        Returns:
            Scenario record

        Raises:
            ValidationError: If scenario not found or wrong company
        """
        query = text("""
            SELECT id, company_id, name, description, status, created_by,
                   created_at, updated_at, archived_at, archived_by
            FROM sandbox.scenarios
            WHERE id = :scenario_id AND company_id = :company_id
        """)

        result = self.db.execute(query, {
            "scenario_id": str(scenario_id),
            "company_id": str(company_id)
        }).fetchone()

        if not result:
            raise ValidationError(
                message=f"Scenario {scenario_id} not found",
                code=SandboxErrorCode.SCENARIO_NOT_FOUND
            )

        return {
            "id": result[0],
            "company_id": result[1],
            "name": result[2],
            "description": result[3],
            "status": result[4],
            "created_by": result[5],
            "created_at": result[6],
            "updated_at": result[7],
            "archived_at": result[8],
            "archived_by": result[9]
        }

    def list_scenarios(
        self,
        company_id: UUID,
        status: Optional[ScenarioStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        List scenarios for company.

        Args:
            company_id: Company UUID
            status: Optional status filter

        Returns:
            List of scenario records with counts
        """
        if status:
            query = text("""
                SELECT s.id, s.name, s.status, s.created_at,
                       (SELECT COUNT(*) FROM sandbox.projections WHERE scenario_id = s.id) as projection_count,
                       (SELECT COUNT(*) FROM sandbox.bindings WHERE scenario_id = s.id) as binding_count
                FROM sandbox.scenarios s
                WHERE s.company_id = :company_id AND s.status = :status
                ORDER BY s.created_at DESC
            """)
            result = self.db.execute(query, {
                "company_id": str(company_id),
                "status": status.value
            }).fetchall()
        else:
            query = text("""
                SELECT s.id, s.name, s.status, s.created_at,
                       (SELECT COUNT(*) FROM sandbox.projections WHERE scenario_id = s.id) as projection_count,
                       (SELECT COUNT(*) FROM sandbox.bindings WHERE scenario_id = s.id) as binding_count
                FROM sandbox.scenarios s
                WHERE s.company_id = :company_id
                ORDER BY s.created_at DESC
            """)
            result = self.db.execute(query, {
                "company_id": str(company_id)
            }).fetchall()

        return [
            {
                "id": row[0],
                "name": row[1],
                "status": row[2],
                "created_at": row[3],
                "projection_count": row[4],
                "binding_count": row[5]
            }
            for row in result
        ]

    def activate_scenario(self, scenario_id: UUID, company_id: UUID) -> Dict[str, Any]:
        """
        Activate scenario (DRAFT → ACTIVE).

        Validates:
        - Scenario is DRAFT
        - Has at least 1 projection
        - No circular bindings

        Args:
            scenario_id: Scenario UUID
            company_id: Company UUID

        Returns:
            Updated scenario

        Raises:
            ValidationError: If validation fails
        """
        # Get scenario
        scenario = self.get_scenario(scenario_id, company_id)

        # Validate state
        if scenario["status"] != ScenarioStatus.DRAFT.value:
            raise ValidationError(
                message=f"Cannot activate scenario in {scenario['status']} state. Only DRAFT scenarios can be activated.",
                code=SandboxErrorCode.INVALID_SCENARIO_STATE
            )

        # Validate has projections
        projection_count_query = text("""
            SELECT COUNT(*) FROM sandbox.projections WHERE scenario_id = :scenario_id
        """)
        count = self.db.execute(projection_count_query, {
            "scenario_id": str(scenario_id)
        }).scalar()

        if count == 0:
            raise ValidationError(
                message="Cannot activate scenario with no projections. Add at least one projection.",
                code=SandboxErrorCode.INVALID_SCENARIO_STATE
            )

        # Validate no circular bindings
        if self._has_circular_bindings(scenario_id):
            raise ValidationError(
                message="Cannot activate scenario with circular binding dependencies.",
                code=SandboxErrorCode.CIRCULAR_BINDING
            )

        # Update status
        update_query = text("""
            UPDATE sandbox.scenarios
            SET status = 'ACTIVE', updated_at = NOW()
            WHERE id = :scenario_id AND company_id = :company_id
            RETURNING id, company_id, name, description, status, created_by, created_at, updated_at
        """)

        result = self.db.execute(update_query, {
            "scenario_id": str(scenario_id),
            "company_id": str(company_id)
        }).fetchone()

        self.db.commit()

        return {
            "id": result[0],
            "company_id": result[1],
            "name": result[2],
            "description": result[3],
            "status": result[4],
            "created_by": result[5],
            "created_at": result[6],
            "updated_at": result[7]
        }

    def archive_scenario(
        self,
        scenario_id: UUID,
        company_id: UUID,
        archived_by: UUID
    ) -> Dict[str, Any]:
        """
        Archive scenario (ACTIVE → ARCHIVED).

        Args:
            scenario_id: Scenario UUID
            company_id: Company UUID
            archived_by: User UUID

        Returns:
            Updated scenario
        """
        scenario = self.get_scenario(scenario_id, company_id)

        if scenario["status"] != ScenarioStatus.ACTIVE.value:
            raise ValidationError(
                message=f"Only ACTIVE scenarios can be archived. This scenario is {scenario['status']}.",
                code=SandboxErrorCode.INVALID_SCENARIO_STATE
            )

        update_query = text("""
            UPDATE sandbox.scenarios
            SET status = 'ARCHIVED', archived_at = NOW(), archived_by = :archived_by, updated_at = NOW()
            WHERE id = :scenario_id AND company_id = :company_id
            RETURNING id, status, archived_at, archived_by, updated_at
        """)

        result = self.db.execute(update_query, {
            "scenario_id": str(scenario_id),
            "company_id": str(company_id),
            "archived_by": str(archived_by)
        }).fetchone()

        self.db.commit()

        scenario["status"] = result[1]
        scenario["archived_at"] = result[2]
        scenario["archived_by"] = result[3]
        scenario["updated_at"] = result[4]

        return scenario

    def clone_scenario(
        self,
        scenario_id: UUID,
        company_id: UUID,
        new_name: str,
        cloned_by: UUID
    ) -> Dict[str, Any]:
        """
        Clone scenario (ACTIVE → DRAFT copy).

        Copies:
        - All projections (new UUIDs)
        - All bindings (updated references)

        Args:
            scenario_id: Source scenario UUID
            company_id: Company UUID
            new_name: Name for cloned scenario
            cloned_by: User UUID

        Returns:
            New scenario
        """
        # Get source scenario
        source = self.get_scenario(scenario_id, company_id)

        # Create new scenario
        new_scenario = self.create_scenario(
            company_id=company_id,
            name=new_name,
            description=f"Cloned from: {source['name']}",
            created_by=cloned_by
        )

        # Clone projections
        clone_projections_query = text("""
            INSERT INTO sandbox.projections (
                scenario_id, type, name, description, amount, currency, frequency,
                start_date, end_date, expense_category, cashflow_type, event_date,
                jurisdiction, tax_type, calculation_basis, assumed_rate, assumptions,
                confidence_level, metadata, created_at, updated_at
            )
            SELECT
                :new_scenario_id, type, name, description, amount, currency, frequency,
                start_date, end_date, expense_category, cashflow_type, event_date,
                jurisdiction, tax_type, calculation_basis, assumed_rate, assumptions,
                confidence_level, metadata, NOW(), NOW()
            FROM sandbox.projections
            WHERE scenario_id = :source_scenario_id
            RETURNING id
        """)

        new_projection_ids = self.db.execute(clone_projections_query, {
            "new_scenario_id": str(new_scenario["id"]),
            "source_scenario_id": str(scenario_id)
        }).fetchall()

        # Clone bindings (if projections were cloned)
        if new_projection_ids:
            # Build mapping of old IDs to new IDs
            old_projection_ids_query = text("""
                SELECT id FROM sandbox.projections
                WHERE scenario_id = :source_scenario_id
                ORDER BY created_at
            """)
            old_ids = [row[0] for row in self.db.execute(old_projection_ids_query, {
                "source_scenario_id": str(scenario_id)
            }).fetchall()]

            new_ids = [row[0] for row in new_projection_ids]
            id_mapping = dict(zip(old_ids, new_ids))

            # Clone bindings with updated references
            clone_bindings_query = text("""
                SELECT source_projection_id, target_projection_id, rule_type, coefficient, rule_description
                FROM sandbox.bindings
                WHERE scenario_id = :source_scenario_id
            """)

            source_bindings = self.db.execute(clone_bindings_query, {
                "source_scenario_id": str(scenario_id)
            }).fetchall()

            for binding in source_bindings:
                old_source = binding[0]
                old_target = binding[1]

                # Map to new projection IDs
                new_source = id_mapping.get(old_source)
                new_target = id_mapping.get(old_target)

                if new_source and new_target:
                    insert_binding_query = text("""
                        INSERT INTO sandbox.bindings (
                            scenario_id, source_projection_id, target_projection_id,
                            rule_type, coefficient, rule_description, created_at, updated_at
                        ) VALUES (
                            :scenario_id, :source_id, :target_id, :rule_type, :coefficient,
                            :description, NOW(), NOW()
                        )
                    """)

                    self.db.execute(insert_binding_query, {
                        "scenario_id": str(new_scenario["id"]),
                        "source_id": str(new_source),
                        "target_id": str(new_target),
                        "rule_type": binding[2],
                        "coefficient": binding[3],
                        "description": binding[4]
                    })

        self.db.commit()

        return new_scenario

    def _ensure_scenario_editable(self, scenario_id: UUID, company_id: UUID):
        """
        Ensure scenario is DRAFT (editable).

        Raises ValidationError if ACTIVE or ARCHIVED.
        """
        scenario = self.get_scenario(scenario_id, company_id)

        if scenario["status"] != ScenarioStatus.DRAFT.value:
            raise ValidationError(
                message=f"Cannot modify {scenario['status']} scenario. Only DRAFT scenarios are editable. Clone this scenario to make changes.",
                code=SandboxErrorCode.SCENARIO_NOT_EDITABLE
            )

    def _has_circular_bindings(self, scenario_id: UUID) -> bool:
        """
        Detect circular dependencies in binding graph using DFS.

        Args:
            scenario_id: Scenario to check

        Returns:
            True if cycle exists, False otherwise
        """
        # Get all bindings for scenario
        bindings_query = text("""
            SELECT source_projection_id, target_projection_id
            FROM sandbox.bindings
            WHERE scenario_id = :scenario_id
        """)

        bindings = self.db.execute(bindings_query, {
            "scenario_id": str(scenario_id)
        }).fetchall()

        if not bindings:
            return False

        # Build adjacency list
        graph = {}
        for source, target in bindings:
            if source not in graph:
                graph[source] = []
            graph[source].append(target)

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
                    return True

        return False

    # ========================================================================
    # PROJECTION CALCULATIONS
    # ========================================================================

    def calculate_projection_totals(
        self,
        amount: Decimal,
        frequency: str,
        start_date: date,
        end_date: Optional[date],
        scenario_end_date: Optional[date] = None
    ) -> Tuple[Decimal, int, Optional[Decimal]]:
        """
        Calculate derived projection values.

        Args:
            amount: Base amount
            frequency: Recurrence pattern
            start_date: Start date
            end_date: End date (None = ongoing)
            scenario_end_date: Scenario boundary (default: 12 months from start)

        Returns:
            (total_projected_value, occurrence_count, monthly_run_rate)
        """
        from dateutil.relativedelta import relativedelta

        # Determine scenario end
        if not scenario_end_date:
            scenario_end_date = start_date + relativedelta(months=12)

        # Determine effective end date
        effective_end = end_date if end_date else scenario_end_date
        if effective_end > scenario_end_date:
            effective_end = scenario_end_date

        # Calculate occurrences
        if frequency == "ONE_TIME":
            occurrence_count = 1
            total_value = amount
        elif frequency == "MONTHLY":
            months = (effective_end.year - start_date.year) * 12 + (effective_end.month - start_date.month) + 1
            occurrence_count = max(0, months)
            total_value = amount * occurrence_count
        elif frequency == "QUARTERLY":
            months = (effective_end.year - start_date.year) * 12 + (effective_end.month - start_date.month) + 1
            occurrence_count = max(0, months // 3)
            total_value = amount * occurrence_count
        elif frequency == "ANNUALLY":
            years = (effective_end.year - start_date.year) + 1
            occurrence_count = max(0, years)
            total_value = amount * occurrence_count
        else:
            occurrence_count = 0
            total_value = Decimal(0)

        # Calculate monthly run rate
        if frequency == "MONTHLY":
            monthly_run_rate = amount
        elif frequency == "QUARTERLY":
            monthly_run_rate = amount / Decimal(3)
        elif frequency == "ANNUALLY":
            monthly_run_rate = amount / Decimal(12)
        else:
            monthly_run_rate = None

        return (total_value, occurrence_count, monthly_run_rate)

    def derive_tax_liability(
        self,
        scenario_id: UUID,
        calculation_basis: str,
        assumed_rate: Decimal
    ) -> Decimal:
        """
        Derive tax liability from scenario data (SIMULATION ONLY).

        CRITICAL: This is an estimate, not accounting truth.

        Args:
            scenario_id: Scenario UUID
            calculation_basis: What to tax (PROJECTED_PROFIT, GROSS_REVENUE, etc.)
            assumed_rate: Tax rate (0.21 = 21%)

        Returns:
            Estimated tax liability
        """
        if calculation_basis == "PROJECTED_PROFIT":
            # Calculate profit = revenue - expense
            summary = self.calculate_scenario_summary(scenario_id)
            profit = summary["projected_profit"]

            if profit <= 0:
                return Decimal(0)  # No tax on loss

            return profit * assumed_rate

        elif calculation_basis == "GROSS_REVENUE":
            summary = self.calculate_scenario_summary(scenario_id)
            revenue = summary["total_revenue"]
            return revenue * assumed_rate

        elif calculation_basis.startswith("PAYROLL"):
            # Sum payroll expenses
            payroll_query = text("""
                SELECT COALESCE(SUM(amount), 0)
                FROM sandbox.projections
                WHERE scenario_id = :scenario_id
                  AND type = 'EXPENSE'
                  AND (expense_category = 'PAYROLL' OR expense_category ILIKE '%payroll%')
            """)

            payroll_total = self.db.execute(payroll_query, {
                "scenario_id": str(scenario_id)
            }).scalar() or Decimal(0)

            return payroll_total * assumed_rate

        else:
            # Unknown basis - return 0 (user must manually calculate)
            return Decimal(0)

    def calculate_scenario_summary(self, scenario_id: UUID) -> Dict[str, Any]:
        """
        Calculate scenario financial summary.

        Args:
            scenario_id: Scenario UUID

        Returns:
            Summary dict with totals
        """
        # Sum revenue
        revenue_query = text("""
            SELECT COALESCE(SUM(amount), 0)
            FROM sandbox.projections
            WHERE scenario_id = :scenario_id AND type = 'REVENUE'
        """)
        total_revenue = self.db.execute(revenue_query, {
            "scenario_id": str(scenario_id)
        }).scalar() or Decimal(0)

        # Sum expense
        expense_query = text("""
            SELECT COALESCE(SUM(amount), 0)
            FROM sandbox.projections
            WHERE scenario_id = :scenario_id AND type = 'EXPENSE'
        """)
        total_expense = self.db.execute(expense_query, {
            "scenario_id": str(scenario_id)
        }).scalar() or Decimal(0)

        # Calculate profit
        projected_profit = total_revenue - total_expense

        # Sum tax liabilities
        tax_query = text("""
            SELECT COALESCE(SUM(amount), 0)
            FROM sandbox.projections
            WHERE scenario_id = :scenario_id AND type = 'TAX_LIABILITY'
        """)
        total_tax_liability = self.db.execute(tax_query, {
            "scenario_id": str(scenario_id)
        }).scalar() or Decimal(0)

        # Calculate net position
        net_position = projected_profit - total_tax_liability

        return {
            "total_revenue": total_revenue,
            "total_expense": total_expense,
            "projected_profit": projected_profit,
            "total_tax_liability": total_tax_liability,
            "net_position": net_position
        }
