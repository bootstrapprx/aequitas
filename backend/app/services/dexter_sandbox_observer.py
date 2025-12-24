"""
Dexter Sandbox Observer (Zone C Intelligence)

CANONICAL REFERENCE:
- Canon IV: Intelligence Boundaries
- Sandbox Engine Design: Backend API Design

CRITICAL RULES:
- READ-ONLY ACCESS to sandbox.* tables
- NO WRITES to any tables (sandbox or truth)
- NO INFERENCE from truth tables (only sandbox data)
- ALL insights are advisory only
- Explanations must be clear and actionable

PURPOSE:
Dexter observes sandbox scenarios and provides:
1. Pattern detection (revenue/expense/cashflow cycles)
2. Tax liability intelligence (missing projections, impact analysis)
3. Risk highlighting (circular dependencies, unrealistic assumptions)
4. Trade-off surfacing (scenario comparisons)
5. Value destination explanations (where money goes)
"""
from typing import Dict, List, Optional, Any
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.schemas.sandbox import ProjectionType, TaxType, ConfidenceLevel


class DexterSandboxObserver:
    """
    Read-only observer for sandbox scenarios.

    CANONICAL COMPLIANCE:
    - Zone C: Advisory intelligence only
    - No mutations to any data
    - No access to truth table writes
    - All suggestions are recommendations, not commands
    """

    def __init__(self, db: Session):
        self.db = db

    # ========================================================================
    # SCENARIO OBSERVATION
    # ========================================================================

    def observe_scenario_structure(self, scenario_id: UUID) -> Dict[str, Any]:
        """
        Get complete scenario structure for analysis.

        Returns:
            {
                "scenario": {...},
                "projections": [...],
                "bindings": [...],
                "summary": {...}
            }
        """
        # Get scenario metadata
        scenario_query = text("""
            SELECT id, company_id, name, description, status,
                   created_at, created_by, activated_at, archived_at
            FROM sandbox.scenarios
            WHERE id = :scenario_id
        """)

        scenario_row = self.db.execute(scenario_query, {
            "scenario_id": str(scenario_id)
        }).fetchone()

        if not scenario_row:
            return {"error": "Scenario not found"}

        scenario = {
            "id": scenario_row[0],
            "company_id": scenario_row[1],
            "name": scenario_row[2],
            "description": scenario_row[3],
            "status": scenario_row[4],
            "created_at": scenario_row[5],
            "created_by": scenario_row[6],
            "activated_at": scenario_row[7],
            "archived_at": scenario_row[8]
        }

        # Get projections
        projections_query = text("""
            SELECT id, type, name, amount, frequency, start_date, end_date,
                   total_projected_value, occurrence_count, monthly_run_rate,
                   jurisdiction, tax_type, calculation_basis, assumed_rate,
                   assumptions, confidence_level
            FROM sandbox.projections
            WHERE scenario_id = :scenario_id
            ORDER BY type, created_at
        """)

        projection_rows = self.db.execute(projections_query, {
            "scenario_id": str(scenario_id)
        }).fetchall()

        projections = []
        for row in projection_rows:
            projections.append({
                "id": row[0],
                "type": row[1],
                "name": row[2],
                "amount": row[3],
                "frequency": row[4],
                "start_date": row[5],
                "end_date": row[6],
                "total_projected_value": row[7],
                "occurrence_count": row[8],
                "monthly_run_rate": row[9],
                "jurisdiction": row[10],
                "tax_type": row[11],
                "calculation_basis": row[12],
                "assumed_rate": row[13],
                "assumptions": row[14],
                "confidence_level": row[15]
            })

        # Get bindings
        bindings_query = text("""
            SELECT id, source_projection_id, target_projection_id,
                   rule_type, coefficient, rule_description
            FROM sandbox.bindings
            WHERE scenario_id = :scenario_id
            ORDER BY created_at
        """)

        binding_rows = self.db.execute(bindings_query, {
            "scenario_id": str(scenario_id)
        }).fetchall()

        bindings = []
        for row in binding_rows:
            bindings.append({
                "id": row[0],
                "source_projection_id": row[1],
                "target_projection_id": row[2],
                "rule_type": row[3],
                "coefficient": row[4],
                "rule_description": row[5]
            })

        # Calculate summary
        summary = self._calculate_summary(projections)

        return {
            "scenario": scenario,
            "projections": projections,
            "bindings": bindings,
            "summary": summary
        }

    def _calculate_summary(self, projections: List[Dict]) -> Dict[str, Decimal]:
        """
        Calculate scenario financial summary.

        Returns:
            {
                "total_revenue": Decimal,
                "total_expense": Decimal,
                "projected_profit": Decimal,
                "total_tax_liability": Decimal,
                "net_position": Decimal
            }
        """
        total_revenue = Decimal(0)
        total_expense = Decimal(0)
        total_tax = Decimal(0)

        for proj in projections:
            proj_type = proj.get("type")
            value = proj.get("total_projected_value") or Decimal(0)

            if proj_type == ProjectionType.REVENUE.value:
                total_revenue += value
            elif proj_type == ProjectionType.EXPENSE.value:
                total_expense += value
            elif proj_type == ProjectionType.TAX_LIABILITY.value:
                total_tax += value

        projected_profit = total_revenue - total_expense
        net_position = projected_profit - total_tax

        return {
            "total_revenue": total_revenue,
            "total_expense": total_expense,
            "projected_profit": projected_profit,
            "total_tax_liability": total_tax,
            "net_position": net_position
        }

    # ========================================================================
    # PATTERN DETECTION
    # ========================================================================

    def detect_patterns(self, scenario_id: UUID) -> List[Dict[str, Any]]:
        """
        Detect patterns in scenario structure.

        Returns list of detected patterns:
        [
            {
                "pattern_type": "SEASONAL_REVENUE",
                "confidence": "HIGH",
                "description": "Revenue projections show seasonal variation",
                "projections_involved": [uuid, uuid],
                "recommendation": "Consider smoothing cashflow with reserves"
            }
        ]
        """
        structure = self.observe_scenario_structure(scenario_id)
        projections = structure.get("projections", [])
        bindings = structure.get("bindings", [])

        patterns = []

        # Pattern 1: Revenue concentration risk
        revenue_pattern = self._detect_revenue_concentration(projections)
        if revenue_pattern:
            patterns.append(revenue_pattern)

        # Pattern 2: Expense timing mismatch
        expense_pattern = self._detect_expense_timing_mismatch(projections)
        if expense_pattern:
            patterns.append(expense_pattern)

        # Pattern 3: Cashflow gap
        cashflow_pattern = self._detect_cashflow_gap(projections)
        if cashflow_pattern:
            patterns.append(cashflow_pattern)

        # Pattern 4: Binding complexity
        binding_pattern = self._detect_binding_complexity(bindings)
        if binding_pattern:
            patterns.append(binding_pattern)

        return patterns

    def _detect_revenue_concentration(self, projections: List[Dict]) -> Optional[Dict]:
        """Detect if revenue is concentrated in few sources."""
        revenue_projections = [p for p in projections if p["type"] == ProjectionType.REVENUE.value]

        if len(revenue_projections) == 0:
            return None

        if len(revenue_projections) == 1:
            return {
                "pattern_type": "REVENUE_CONCENTRATION",
                "confidence": ConfidenceLevel.HIGH.value,
                "description": "Single revenue source detected. Business has concentration risk.",
                "projections_involved": [revenue_projections[0]["id"]],
                "recommendation": "Consider diversifying revenue streams to reduce risk.",
                "risk_level": "HIGH"
            }

        # Calculate concentration (largest revenue / total revenue)
        total_revenue = sum(p.get("total_projected_value", 0) or 0 for p in revenue_projections)
        if total_revenue == 0:
            return None

        largest_revenue = max(p.get("total_projected_value", 0) or 0 for p in revenue_projections)
        concentration_ratio = largest_revenue / total_revenue

        if concentration_ratio > Decimal("0.75"):
            largest_proj = max(revenue_projections, key=lambda p: p.get("total_projected_value", 0) or 0)
            return {
                "pattern_type": "REVENUE_CONCENTRATION",
                "confidence": ConfidenceLevel.HIGH.value,
                "description": f"One revenue source represents {concentration_ratio * 100:.0f}% of total revenue.",
                "projections_involved": [largest_proj["id"]],
                "recommendation": "High revenue concentration. Consider diversifying to reduce dependency risk.",
                "risk_level": "MEDIUM"
            }

        return None

    def _detect_expense_timing_mismatch(self, projections: List[Dict]) -> Optional[Dict]:
        """Detect if expenses occur before revenue."""
        revenue_projections = [p for p in projections if p["type"] == ProjectionType.REVENUE.value]
        expense_projections = [p for p in projections if p["type"] == ProjectionType.EXPENSE.value]

        if not revenue_projections or not expense_projections:
            return None

        earliest_revenue = min((p.get("start_date") for p in revenue_projections if p.get("start_date")), default=None)
        earliest_expense = min((p.get("start_date") for p in expense_projections if p.get("start_date")), default=None)

        if earliest_revenue and earliest_expense and earliest_expense < earliest_revenue:
            days_gap = (earliest_revenue - earliest_expense).days

            return {
                "pattern_type": "EXPENSE_BEFORE_REVENUE",
                "confidence": ConfidenceLevel.HIGH.value,
                "description": f"Expenses start {days_gap} days before revenue begins.",
                "projections_involved": [],
                "recommendation": "Ensure sufficient working capital to cover pre-revenue expenses.",
                "risk_level": "MEDIUM"
            }

        return None

    def _detect_cashflow_gap(self, projections: List[Dict]) -> Optional[Dict]:
        """Detect potential cashflow shortfalls."""
        summary = self._calculate_summary(projections)

        # Check if projected profit is negative
        if summary["projected_profit"] < 0:
            loss_amount = abs(summary["projected_profit"])

            return {
                "pattern_type": "NEGATIVE_CASHFLOW",
                "confidence": ConfidenceLevel.HIGH.value,
                "description": f"Scenario projects loss of ${loss_amount:,.2f}.",
                "projections_involved": [],
                "recommendation": "Consider reducing expenses or increasing revenue to achieve profitability.",
                "risk_level": "HIGH"
            }

        # Check if net position (after tax) is close to zero
        if 0 < summary["net_position"] < summary["total_revenue"] * Decimal("0.05"):
            return {
                "pattern_type": "THIN_MARGINS",
                "confidence": ConfidenceLevel.MEDIUM.value,
                "description": f"Net position (${summary['net_position']:,.2f}) is less than 5% of revenue.",
                "projections_involved": [],
                "recommendation": "Low profit margin. Small revenue decline could result in loss.",
                "risk_level": "MEDIUM"
            }

        return None

    def _detect_binding_complexity(self, bindings: List[Dict]) -> Optional[Dict]:
        """Detect overly complex binding graphs."""
        if len(bindings) == 0:
            return None

        # Count unique projections involved
        projection_ids = set()
        for binding in bindings:
            projection_ids.add(binding["source_projection_id"])
            projection_ids.add(binding["target_projection_id"])

        # If more than 3 bindings per projection on average, flag complexity
        avg_bindings_per_projection = len(bindings) / len(projection_ids)

        if avg_bindings_per_projection > 3:
            return {
                "pattern_type": "COMPLEX_BINDINGS",
                "confidence": ConfidenceLevel.MEDIUM.value,
                "description": f"Scenario has {len(bindings)} bindings across {len(projection_ids)} projections.",
                "projections_involved": list(projection_ids),
                "recommendation": "Complex binding graph. Verify all relationships are necessary and accurate.",
                "risk_level": "LOW"
            }

        return None

    # ========================================================================
    # TAX LIABILITY INTELLIGENCE
    # ========================================================================

    def analyze_tax_liability(self, scenario_id: UUID) -> Dict[str, Any]:
        """
        Analyze tax liability projections and identify gaps.

        Returns:
            {
                "has_tax_projections": bool,
                "tax_projections": [...],
                "missing_tax_types": [...],
                "effective_tax_rate": Decimal,
                "tax_impact_on_profit": Decimal,
                "recommendations": [...]
            }
        """
        structure = self.observe_scenario_structure(scenario_id)
        projections = structure.get("projections", [])
        summary = structure.get("summary", {})

        tax_projections = [p for p in projections if p["type"] == ProjectionType.TAX_LIABILITY.value]

        has_tax = len(tax_projections) > 0

        # Calculate effective tax rate
        projected_profit = summary.get("projected_profit", Decimal(0))
        total_tax = summary.get("total_tax_liability", Decimal(0))

        effective_rate = Decimal(0)
        if projected_profit > 0:
            effective_rate = total_tax / projected_profit

        # Calculate tax impact
        tax_impact_pct = Decimal(0)
        if projected_profit > 0:
            tax_impact_pct = (total_tax / projected_profit) * 100

        # Detect missing tax types
        missing_tax_types = self._detect_missing_tax_types(projections, summary)

        # Generate recommendations
        recommendations = []

        if not has_tax:
            recommendations.append({
                "recommendation_type": "MISSING_TAX_PROJECTION",
                "severity": "HIGH",
                "description": "No tax liability projections found. Scenario may underestimate costs.",
                "action": "Add federal income tax projection based on projected profit.",
                "action_taken": False
            })

        if projected_profit > 0 and effective_rate < Decimal("0.15"):
            recommendations.append({
                "recommendation_type": "LOW_TAX_RATE",
                "severity": "MEDIUM",
                "description": f"Effective tax rate ({effective_rate * 100:.1f}%) seems low for profitable business.",
                "action": "Verify tax rate assumptions. Typical US federal rate is 21% for C-corps.",
                "action_taken": False
            })

        if effective_rate > Decimal("0.40"):
            recommendations.append({
                "recommendation_type": "HIGH_TAX_RATE",
                "severity": "MEDIUM",
                "description": f"Effective tax rate ({effective_rate * 100:.1f}%) is high. Review for over-estimation.",
                "action": "Check if state, local, and federal taxes are being double-counted.",
                "action_taken": False
            })

        for missing in missing_tax_types:
            recommendations.append(missing)

        return {
            "has_tax_projections": has_tax,
            "tax_projections": tax_projections,
            "missing_tax_types": missing_tax_types,
            "effective_tax_rate": effective_rate,
            "tax_impact_on_profit_pct": tax_impact_pct,
            "recommendations": recommendations
        }

    def _detect_missing_tax_types(self, projections: List[Dict], summary: Dict) -> List[Dict]:
        """Detect potentially missing tax types."""
        missing = []

        tax_projections = [p for p in projections if p["type"] == ProjectionType.TAX_LIABILITY.value]
        tax_types_present = set(p.get("tax_type") for p in tax_projections if p.get("tax_type"))

        # Check for federal income tax
        if summary.get("projected_profit", 0) > 0:
            if TaxType.FEDERAL_INCOME.value not in tax_types_present:
                missing.append({
                    "recommendation_type": "MISSING_FEDERAL_INCOME_TAX",
                    "severity": "HIGH",
                    "description": "Scenario shows profit but no federal income tax projection.",
                    "action": "Add federal income tax projection (typically 21% for C-corps).",
                    "action_taken": False
                })

        # Check for payroll tax if there are expense projections
        expense_projections = [p for p in projections if p["type"] == ProjectionType.EXPENSE.value]
        payroll_expenses = [p for p in expense_projections if "payroll" in p.get("name", "").lower() or "salary" in p.get("name", "").lower()]

        if payroll_expenses and TaxType.PAYROLL.value not in tax_types_present:
            missing.append({
                "recommendation_type": "MISSING_PAYROLL_TAX",
                "severity": "MEDIUM",
                "description": "Payroll expenses detected but no payroll tax projection.",
                "action": "Add payroll tax projection (typically 7.65% employer portion of FICA).",
                "action_taken": False
            })

        return missing

    # ========================================================================
    # VALUE DESTINATION ANALYSIS
    # ========================================================================

    def explain_value_destinations(self, scenario_id: UUID) -> Dict[str, Any]:
        """
        Explain where revenue goes (value destination axis).

        Returns:
            {
                "total_revenue": Decimal,
                "destinations": {
                    "operating_expense": Decimal,
                    "tax_liability": Decimal,
                    "net_retained": Decimal
                },
                "percentages": {...},
                "explanation": "Formatted explanation for user"
            }
        """
        structure = self.observe_scenario_structure(scenario_id)
        summary = structure.get("summary", {})

        total_revenue = summary.get("total_revenue", Decimal(0))
        total_expense = summary.get("total_expense", Decimal(0))
        total_tax = summary.get("total_tax_liability", Decimal(0))
        net_position = summary.get("net_position", Decimal(0))

        if total_revenue == 0:
            return {
                "total_revenue": Decimal(0),
                "destinations": {},
                "percentages": {},
                "explanation": "No revenue projections in scenario. Cannot calculate value destinations."
            }

        # Calculate percentages
        expense_pct = (total_expense / total_revenue) * 100
        tax_pct = (total_tax / total_revenue) * 100
        retained_pct = (net_position / total_revenue) * 100

        # Generate explanation
        explanation_lines = [
            f"Revenue Distribution (${total_revenue:,.2f} total):",
            f"",
            f"  Operating Expenses: ${total_expense:,.2f} ({expense_pct:.1f}%)",
            f"  Tax Liability:      ${total_tax:,.2f} ({tax_pct:.1f}%)",
            f"  Net Retained:       ${net_position:,.2f} ({retained_pct:.1f}%)",
            f"",
        ]

        # Add interpretation
        if retained_pct < 10:
            explanation_lines.append("⚠️  Low retention rate. Most revenue consumed by expenses and taxes.")
        elif retained_pct > 40:
            explanation_lines.append("✓  High retention rate. Strong profit margin after expenses and taxes.")
        else:
            explanation_lines.append("✓  Moderate retention rate. Typical for established businesses.")

        return {
            "total_revenue": total_revenue,
            "destinations": {
                "operating_expense": total_expense,
                "tax_liability": total_tax,
                "net_retained": net_position
            },
            "percentages": {
                "operating_expense_pct": expense_pct,
                "tax_liability_pct": tax_pct,
                "net_retained_pct": retained_pct
            },
            "explanation": "\n".join(explanation_lines)
        }

    # ========================================================================
    # SCENARIO COMPARISON
    # ========================================================================

    def compare_scenarios(self, scenario_ids: List[UUID]) -> Dict[str, Any]:
        """
        Compare up to 3 scenarios side-by-side.

        Returns:
            {
                "scenarios": [...],
                "comparison_matrix": {...},
                "trade_offs": [...],
                "recommendation": "..."
            }
        """
        if len(scenario_ids) > 3:
            return {"error": "Maximum 3 scenarios can be compared"}

        if len(scenario_ids) < 2:
            return {"error": "At least 2 scenarios required for comparison"}

        scenarios = []
        for scenario_id in scenario_ids:
            structure = self.observe_scenario_structure(scenario_id)
            scenarios.append(structure)

        # Build comparison matrix
        comparison = {
            "scenario_names": [s["scenario"]["name"] for s in scenarios],
            "total_revenue": [s["summary"]["total_revenue"] for s in scenarios],
            "total_expense": [s["summary"]["total_expense"] for s in scenarios],
            "projected_profit": [s["summary"]["projected_profit"] for s in scenarios],
            "total_tax_liability": [s["summary"]["total_tax_liability"] for s in scenarios],
            "net_position": [s["summary"]["net_position"] for s in scenarios]
        }

        # Detect trade-offs
        trade_offs = self._detect_trade_offs(scenarios)

        # Generate recommendation
        recommendation = self._generate_comparison_recommendation(scenarios, comparison)

        return {
            "scenarios": scenarios,
            "comparison_matrix": comparison,
            "trade_offs": trade_offs,
            "recommendation": recommendation
        }

    def _detect_trade_offs(self, scenarios: List[Dict]) -> List[Dict]:
        """Detect trade-offs between scenarios."""
        trade_offs = []

        # Example: Higher revenue but also higher expenses
        revenues = [s["summary"]["total_revenue"] for s in scenarios]
        expenses = [s["summary"]["total_expense"] for s in scenarios]

        max_revenue_idx = revenues.index(max(revenues))
        max_expense_idx = expenses.index(max(expenses))

        if max_revenue_idx == max_expense_idx:
            trade_offs.append({
                "trade_off_type": "REVENUE_EXPENSE_CORRELATION",
                "description": f"Scenario '{scenarios[max_revenue_idx]['scenario']['name']}' has highest revenue but also highest expenses.",
                "implication": "Growth comes with cost. Evaluate if margin improvement is possible."
            })

        return trade_offs

    def _generate_comparison_recommendation(self, scenarios: List[Dict], comparison: Dict) -> str:
        """Generate recommendation based on scenario comparison."""
        net_positions = comparison["net_position"]
        scenario_names = comparison["scenario_names"]

        best_idx = net_positions.index(max(net_positions))
        best_scenario = scenario_names[best_idx]
        best_net = net_positions[best_idx]

        return f"Scenario '{best_scenario}' has the highest net position (${best_net:,.2f}). Consider activating this scenario if financial maximization is the priority. Verify assumptions before proceeding."
