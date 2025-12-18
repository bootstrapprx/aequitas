"""
Dexter Fiscal Adapter - Enables Dexter to answer tax exposure questions.

This adapter provides Dexter with the ability to:
- Answer "What's my projected 2025 tax liability?"
- Explain tax drivers and missing inputs
- Show consolidated vs per-company exposure
- Provide actionable checklists when data is incomplete
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.db.models.tax_run import TaxRun
from app.db.models.tax_position import TaxPosition
from app.db.models.company import Company
from app.services.fiscal_engine import CalculationService


class FiscalAdapter:
    """
    Adapter for Dexter to access Fiscal Engine data.

    This provides a high-level interface for querying tax positions,
    explaining results, and providing guidance.
    """

    def __init__(self, db: Session):
        self.db = db
        self.calc_service = CalculationService(db)

    def get_latest_position(self, company_id: UUID, tax_type: str = "PASS_THROUGH_INCOME") -> Optional[Dict[str, Any]]:
        """
        Get the latest tax position for a company.

        Returns:
            Dictionary with position data and metadata, or None if not found
        """
        position = self.db.query(TaxPosition).join(TaxRun).filter(
            TaxPosition.company_id == company_id,
            TaxPosition.tax_type == tax_type
        ).order_by(TaxRun.created_at.desc()).first()

        if not position:
            return None

        run = self.db.query(TaxRun).filter(TaxRun.id == position.tax_run_id).first()
        company = self.db.query(Company).filter(Company.id == company_id).first()

        return {
            "company_name": company.name if company else "Unknown",
            "taxable_income": float(position.taxable_income_estimated),
            "exposure": float(position.exposure_estimated) if position.exposure_estimated else None,
            "currency": position.currency,
            "confidence_score": position.confidence_score,
            "missing_inputs": position.missing_inputs,
            "top_drivers": position.top_drivers,
            "period_start": str(run.period_start),
            "period_end": str(run.period_end),
            "label": run.label,
            "status": run.status
        }

    def get_all_company_positions(self, company_ids: List[UUID]) -> List[Dict[str, Any]]:
        """
        Get latest positions for multiple companies.

        Returns:
            List of position dictionaries
        """
        positions = []
        for company_id in company_ids:
            position = self.get_latest_position(company_id)
            if position:
                positions.append(position)
        return positions

    def explain_drivers(self, company_id: UUID) -> Dict[str, Any]:
        """
        Explain what's driving the tax exposure for a company.

        Returns:
            Dictionary with driver explanation and top accounts
        """
        position = self.get_latest_position(company_id)
        if not position:
            return {
                "explanation": "No tax calculation has been run yet for this company.",
                "action": "Run a tax calculation first using the Fiscal Engine."
            }

        drivers = position.get("top_drivers", [])
        taxable_income = position["taxable_income"]

        if not drivers:
            return {
                "explanation": "No detailed drivers available. This usually means accounts lack tax tags.",
                "action": "Add tax tags to your chart of accounts to get detailed driver analysis."
            }

        explanation = f"Your estimated taxable income of ${taxable_income:,.2f} is primarily driven by:\n\n"
        for i, driver in enumerate(drivers[:5], 1):
            explanation += f"{i}. {driver['account_name']} ({driver['account_code']}): ${driver['amount']:,.2f} [{driver.get('tag', 'untagged')}]\n"

        return {
            "explanation": explanation,
            "top_drivers": drivers[:5],
            "total_taxable_income": taxable_income
        }

    def get_missing_inputs_checklist(self, company_id: UUID) -> Dict[str, Any]:
        """
        Generate an actionable checklist of missing inputs.

        Returns:
            Dictionary with checklist and confidence impact
        """
        position = self.get_latest_position(company_id)
        if not position:
            return {
                "message": "Run a tax calculation to identify missing inputs.",
                "checklist": []
            }

        missing = position.get("missing_inputs", [])
        confidence = position["confidence_score"]

        if not missing:
            return {
                "message": "No missing inputs! Your calculation is complete.",
                "confidence_score": confidence,
                "checklist": []
            }

        # Build actionable checklist
        checklist = []
        for item in missing:
            if item == "accounting_method":
                checklist.append({
                    "item": "Set accounting method (Cash/Accrual)",
                    "action": "Update tax profile with accounting_method",
                    "impact": "High - affects revenue recognition"
                })
            elif item == "fiscal_year_start":
                checklist.append({
                    "item": "Set fiscal year start date",
                    "action": "Update tax profile with fiscal_year_start",
                    "impact": "Medium - affects period boundaries"
                })
            elif item.startswith("tax_tags_account_"):
                account_code = item.replace("tax_tags_account_", "")
                checklist.append({
                    "item": f"Add tax tags to account {account_code}",
                    "action": f"Tag account {account_code} as taxable_income, deductible_expense, etc.",
                    "impact": "Medium - affects classification"
                })

        return {
            "message": f"Your tax calculation is {confidence}% confident. Complete these items to improve accuracy:",
            "confidence_score": confidence,
            "checklist": checklist,
            "total_missing": len(missing)
        }

    def format_for_dexter_response(self, company_id: UUID, question_type: str) -> str:
        """
        Format fiscal data as a plain-text response for Dexter.

        Args:
            company_id: Company UUID
            question_type: "liability", "drivers", "missing_inputs", "all"

        Returns:
            Formatted plain-text response
        """
        position = self.get_latest_position(company_id)

        if not position:
            return (
                "I don't have any tax calculations on file for this company yet. "
                "Would you like me to run a calculation for you? "
                "I'll need a period range (start and end dates)."
            )

        response = f"**{position['label']}**\n\n"

        if question_type in ["liability", "all"]:
            response += f"**Estimated Taxable Income:** ${position['taxable_income']:,.2f}\n"
            response += f"**Confidence Score:** {position['confidence_score']}%\n"
            response += f"**Period:** {position['period_start']} to {position['period_end']}\n\n"

        if question_type in ["drivers", "all"]:
            drivers_info = self.explain_drivers(company_id)
            response += "**Top Drivers:**\n"
            response += drivers_info["explanation"] + "\n"

        if question_type in ["missing_inputs", "all"]:
            checklist = self.get_missing_inputs_checklist(company_id)
            if checklist["checklist"]:
                response += "**Action Items to Improve Accuracy:**\n"
                for item in checklist["checklist"]:
                    response += f"- {item['item']} (Impact: {item['impact']})\n"
            else:
                response += "✓ All required inputs are complete.\n"

        response += f"\n_{position['label']}_"
        return response
