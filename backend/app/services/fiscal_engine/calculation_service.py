"""
Service for running tax calculations on company data.
"""
import uuid
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date
from decimal import Decimal

from app.db.models.tax_run import TaxRun
from app.db.models.tax_fact import TaxFact
from app.db.models.tax_adjustment import TaxAdjustment
from app.db.models.tax_position import TaxPosition
from app.db.models.company_account import CompanyAccount
from app.db.models.account_balance import AccountBalance
from app.services.fiscal_engine.hashing import compute_inputs_hash
from app.services.fiscal_engine.ruleset_service import RulesetService
from app.services.fiscal_engine.profile_service import ProfileService

ENGINE_VERSION = "1.0.0"


class CalculationService:
    """Service for calculating tax exposure for a company."""

    def __init__(self, db: Session):
        self.db = db
        self.ruleset_service = RulesetService(db)
        self.profile_service = ProfileService(db)

    def run_company_exposure(
        self,
        company_id: UUID,
        period_start: date,
        period_end: date,
        as_of_date: Optional[date] = None,
        ruleset_version: str = "2025.1"
    ) -> TaxRun:
        """
        Run tax exposure calculation for a single company.

        Steps:
        1. Get or create tax profile
        2. Get or create ruleset
        3. Read trial balance / account balances
        4. Compute inputs hash
        5. Create TaxRun
        6. Build TaxFacts from trial balance
        7. Calculate taxable income
        8. Compute confidence score and missing inputs
        9. Create TaxPosition
        10. Mark run as SUCCESS or PARTIAL

        Args:
            company_id: Company UUID
            period_start: Start of period
            period_end: End of period
            as_of_date: Optional as-of date for trial balance
            ruleset_version: Ruleset version to use

        Returns:
            TaxRun with associated facts and position
        """
        # 1. Get or create profile
        profile = self.profile_service.get_or_create_profile(company_id)

        # 2. Get or create ruleset
        ruleset = self.ruleset_service.get_active_ruleset(ruleset_version, "PASS_THROUGH_BASE")
        if not ruleset:
            ruleset = self.ruleset_service.seed_default_ruleset(ruleset_version)

        # 3. Read trial balance (account balances)
        trial_balance = self._get_trial_balance(company_id, period_start, period_end, as_of_date)

        # 4. Compute inputs hash
        trial_balance_snapshot = [
            {
                "account_id": str(item["account_id"]),
                "account_code": item["account_code"],
                "balance": float(item["balance"]),
            }
            for item in trial_balance
        ]
        profile_snapshot = {
            "entity_type": profile.entity_type,
            "tax_regime": profile.tax_regime,
            "accounting_method": profile.accounting_method,
        }
        inputs_hash = compute_inputs_hash(
            company_id, period_start, period_end, trial_balance_snapshot, profile_snapshot, ruleset_version
        )

        # 5. Create TaxRun
        tax_run = TaxRun(
            id=uuid.uuid4(),
            company_id=company_id,
            period_start=period_start,
            period_end=period_end,
            as_of_date=as_of_date or period_end,
            ruleset_id=ruleset.id,
            ruleset_version=ruleset.version,
            engine_version=ENGINE_VERSION,
            inputs_hash=inputs_hash,
            status="SUCCESS",  # Will update if needed
            confidence_score=100,  # Will recalculate
            missing_inputs=[],  # Will populate
            label="Estimated / Projected Tax Exposure — Not a Tax Filing"
        )
        self.db.add(tax_run)
        self.db.flush()  # Get ID for facts

        # 6. Build TaxFacts
        facts = self._build_tax_facts(tax_run, company_id, period_start, period_end, trial_balance)

        # 7 & 8. Calculate taxable income, confidence, and missing inputs
        position_result = self._calculate_position(tax_run, facts, profile)

        # 9. Create TaxPosition
        tax_position = TaxPosition(
            id=uuid.uuid4(),
            tax_run_id=tax_run.id,
            company_id=company_id,
            tax_type="PASS_THROUGH_INCOME",
            taxable_income_estimated=position_result["taxable_income"],
            exposure_estimated=None,  # Placeholder for future
            currency="USD",
            confidence_score=position_result["confidence_score"],
            missing_inputs=position_result["missing_inputs"],
            top_drivers=position_result["top_drivers"]
        )
        self.db.add(tax_position)

        # 10. Update run status
        tax_run.confidence_score = position_result["confidence_score"]
        tax_run.missing_inputs = position_result["missing_inputs"]
        if position_result["missing_inputs"]:
            tax_run.status = "PARTIAL"

        self.db.commit()
        self.db.refresh(tax_run)

        return tax_run

    def _get_trial_balance(
        self,
        company_id: UUID,
        period_start: date,
        period_end: date,
        as_of_date: Optional[date]
    ) -> List[Dict[str, Any]]:
        """
        Get trial balance (account balances) for the period.

        Uses account_balances table if available, otherwise calculates from journal entries.
        """
        # Query account balances
        # For v1, we'll use a simple approach: get all company accounts with their balances
        accounts = self.db.query(CompanyAccount).filter(
            CompanyAccount.company_id == company_id
        ).all()

        trial_balance = []
        for account in accounts:
            # Get balance from account_balances table if available
            balance_record = self.db.query(AccountBalance).filter(
                AccountBalance.company_account_id == account.id,
                AccountBalance.period_end <= (as_of_date or period_end)
            ).order_by(AccountBalance.period_end.desc()).first()

            balance = Decimal(0)
            if balance_record:
                balance = balance_record.debit_balance - balance_record.credit_balance

            trial_balance.append({
                "account_id": account.id,
                "account_code": account.code,
                "account_name": account.name,
                "account_type": account.account_type,
                "balance": balance,
                "tax_tags": account.tags or []  # Assuming tags field exists
            })

        return trial_balance

    def _build_tax_facts(
        self,
        tax_run: TaxRun,
        company_id: UUID,
        period_start: date,
        period_end: date,
        trial_balance: List[Dict[str, Any]]
    ) -> List[TaxFact]:
        """Build TaxFact records from trial balance."""
        facts = []

        for item in trial_balance:
            fact = TaxFact(
                id=uuid.uuid4(),
                tax_run_id=tax_run.id,
                company_id=company_id,
                period_start=period_start,
                period_end=period_end,
                account_id=item["account_id"],
                account_code=item["account_code"],
                account_name=item["account_name"],
                amount=item["balance"],
                tax_tags=item.get("tax_tags", []),
                source="TRIAL_BALANCE",
                source_trace={
                    "account_type": str(item.get("account_type", "UNKNOWN")),
                    "original_balance": float(item["balance"])
                }
            )
            facts.append(fact)
            self.db.add(fact)

        self.db.flush()
        return facts

    def _calculate_position(
        self,
        tax_run: TaxRun,
        facts: List[TaxFact],
        profile
    ) -> Dict[str, Any]:
        """
        Calculate tax position from facts.

        For v1 (pass-through), this is simplified:
        - Taxable income = sum of facts tagged "taxable_income" minus facts tagged "deductible_expense"
        - Confidence based on missing tags and profile completeness
        """
        taxable_income = Decimal(0)
        deductible_expenses = Decimal(0)
        missing_inputs = []
        top_drivers = []

        # Calculate confidence
        confidence_score = 100

        # Check profile completeness
        if not profile.accounting_method:
            missing_inputs.append("accounting_method")
            confidence_score -= 20

        if not profile.fiscal_year_start:
            missing_inputs.append("fiscal_year_start")
            confidence_score -= 10

        # Process facts
        untagged_facts = 0
        for fact in facts:
            if not fact.tax_tags or len(fact.tax_tags) == 0:
                untagged_facts += 1
                missing_inputs.append(f"tax_tags_account_{fact.account_code}")
            else:
                if "taxable_income" in fact.tax_tags:
                    taxable_income += fact.amount
                    top_drivers.append({
                        "account_code": fact.account_code,
                        "account_name": fact.account_name,
                        "amount": float(fact.amount),
                        "tag": "taxable_income"
                    })

                if "deductible_expense" in fact.tax_tags:
                    deductible_expenses += abs(fact.amount)  # Expenses are often negative

        # Reduce confidence for untagged accounts
        if untagged_facts > 0:
            tag_confidence_reduction = min(30, untagged_facts * 5)
            confidence_score -= tag_confidence_reduction

        # Calculate net taxable income
        net_taxable_income = taxable_income - deductible_expenses

        # Sort top drivers by absolute amount
        top_drivers = sorted(top_drivers, key=lambda x: abs(x["amount"]), reverse=True)[:5]

        return {
            "taxable_income": net_taxable_income,
            "confidence_score": max(0, confidence_score),  # Min 0
            "missing_inputs": list(set(missing_inputs)),  # Deduplicate
            "top_drivers": top_drivers
        }
