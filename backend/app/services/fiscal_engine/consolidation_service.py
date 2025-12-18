"""
Service for running consolidated tax calculations across multiple companies.
"""
import uuid
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import date
from decimal import Decimal

from app.db.models.tax_run import TaxRun
from app.db.models.tax_position import TaxPosition
from app.services.fiscal_engine.calculation_service import CalculationService, ENGINE_VERSION
from app.services.fiscal_engine.ruleset_service import RulesetService


class ConsolidationService:
    """Service for calculating consolidated tax exposure across multiple companies."""

    def __init__(self, db: Session):
        self.db = db
        self.calculation_service = CalculationService(db)
        self.ruleset_service = RulesetService(db)

    def run_consolidated_exposure(
        self,
        company_ids: List[UUID],
        period_start: date,
        period_end: date,
        as_of_date: date = None,
        ruleset_version: str = "2025.1"
    ) -> TaxRun:
        """
        Run consolidated tax exposure calculation across multiple companies.

        Steps:
        1. Run individual calculations for each company
        2. Sum company-level taxable incomes
        3. Create consolidated TaxRun and TaxPosition (company_id=null)
        4. Aggregate confidence scores and missing inputs

        Args:
            company_ids: List of company UUIDs to consolidate
            period_start: Start of period
            period_end: End of period
            as_of_date: Optional as-of date
            ruleset_version: Ruleset version to use

        Returns:
            Consolidated TaxRun
        """
        if not company_ids:
            raise ValueError("At least one company_id required for consolidation")

        # 1. Run individual calculations
        company_runs = []
        for company_id in company_ids:
            run = self.calculation_service.run_company_exposure(
                company_id=company_id,
                period_start=period_start,
                period_end=period_end,
                as_of_date=as_of_date,
                ruleset_version=ruleset_version
            )
            company_runs.append(run)

        # 2. Get ruleset
        ruleset = self.ruleset_service.get_active_ruleset(ruleset_version, "PASS_THROUGH_BASE")
        if not ruleset:
            ruleset = self.ruleset_service.seed_default_ruleset(ruleset_version)

        # 3. Aggregate results
        total_taxable_income = Decimal(0)
        all_missing_inputs = set()
        confidence_scores = []

        for run in company_runs:
            # Get position for this run
            position = self.db.query(TaxPosition).filter(
                TaxPosition.tax_run_id == run.id
            ).first()

            if position:
                total_taxable_income += position.taxable_income_estimated
                all_missing_inputs.update(position.missing_inputs)
                confidence_scores.append(position.confidence_score)

        # Calculate average confidence
        avg_confidence = int(sum(confidence_scores) / len(confidence_scores)) if confidence_scores else 0

        # 4. Create consolidated TaxRun
        consolidated_run = TaxRun(
            id=uuid.uuid4(),
            company_id=None,  # Null for consolidated
            period_start=period_start,
            period_end=period_end,
            as_of_date=as_of_date or period_end,
            ruleset_id=ruleset.id,
            ruleset_version=ruleset.version,
            engine_version=ENGINE_VERSION,
            inputs_hash=f"consolidated_{'-'.join(str(cid) for cid in company_ids)}_{period_start}_{period_end}",
            status="SUCCESS",
            confidence_score=avg_confidence,
            missing_inputs=list(all_missing_inputs),
            label="Estimated / Projected Tax Exposure — Not a Tax Filing (Consolidated)"
        )
        self.db.add(consolidated_run)
        self.db.flush()

        # 5. Create consolidated TaxPosition
        consolidated_position = TaxPosition(
            id=uuid.uuid4(),
            tax_run_id=consolidated_run.id,
            company_id=None,  # Null for consolidated
            tax_type="PASS_THROUGH_INCOME",
            taxable_income_estimated=total_taxable_income,
            exposure_estimated=None,
            currency="USD",
            confidence_score=avg_confidence,
            missing_inputs=list(all_missing_inputs),
            top_drivers=[
                {
                    "company_id": str(cid),
                    "note": "See individual company run for details"
                }
                for cid in company_ids
            ]
        )
        self.db.add(consolidated_position)

        self.db.commit()
        self.db.refresh(consolidated_run)

        return consolidated_run
