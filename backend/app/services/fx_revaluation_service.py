"""
FX Period Revaluation Service
Calculates unrealized foreign exchange gains and losses on monetary balance sheet items
and posts adjusting journal entries at period-end.
"""

import uuid
from decimal import Decimal
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models.company_account import CompanyAccount
from app.db.models.master_account import MasterAccount
from app.db.models.fiscal_period import FiscalPeriod
from app.db.models.currency import RateType
from app.db.models.journal_entry import JournalEntry, EntryStatus, EntryType
from app.db.models.journal_entry_line import JournalEntryLine
from app.db.models.enums import AccountType
from app.services.fx_rate_service import FxRateService


class FxRevaluationService:
    """Service to execute period-end FX revaluations."""

    def __init__(self, db: Session):
        self.db = db
        self.fx_service = FxRateService(db)

    def _get_fx_gain_loss_account(self, company_id: UUID) -> CompanyAccount:
        """Find the Unrealized FX Gain/Loss account."""
        acc = self.db.query(CompanyAccount).join(
            MasterAccount, CompanyAccount.mapped_master_account_id == MasterAccount.id, isouter=True
        ).filter(
            CompanyAccount.company_id == company_id,
            CompanyAccount.is_active.is_(True),
            (MasterAccount.code == "70500") | (CompanyAccount.code == "70500") | (CompanyAccount.description.ilike("%unrealized fx%"))
        ).first()

        if not acc:
            # Fallback to any expense account
            acc = self.db.query(CompanyAccount).filter(
                CompanyAccount.company_id == company_id,
                CompanyAccount.account_type == AccountType.EXPENSE,
                CompanyAccount.is_active.is_(True),
            ).first()

        if not acc:
            raise ValueError("No FX Gain/Loss or Expense account configured for company.")

        return acc

    def run_period_revaluation(
        self,
        company_id: UUID,
        fiscal_period_id: UUID,
        user_id: UUID,
        foreign_account_balances: Dict[str, Dict[UUID, Decimal]],
    ) -> Optional[JournalEntry]:
        """
        Revalue foreign balances against period-end closing rates.
        foreign_account_balances structure: { "EUR": { account_uuid: foreign_balance } }
        """
        period = self.db.query(FiscalPeriod).filter(
            FiscalPeriod.id == fiscal_period_id,
            FiscalPeriod.company_id == company_id,
        ).first()

        if not period:
            raise ValueError(f"Fiscal period {fiscal_period_id} not found.")

        fx_gain_loss_account = self._get_fx_gain_loss_account(company_id)

        # Build adjusting lines
        lines_to_create = []
        line_num = 1
        total_adjustment = Decimal("0.00")

        for curr_code, acc_map in foreign_account_balances.items():
            rate = self.fx_service.get_rate(
                from_currency=curr_code,
                to_currency="USD",
                rate_date=period.end_date,
                rate_type=RateType.CLOSING,
            )

            for acc_id, foreign_amt in acc_map.items():
                target_book_usd = round(foreign_amt * rate, 2)

                # Get current book balance in USD
                totals = self.db.query(
                    func.coalesce(func.sum(JournalEntryLine.debit_amount), 0).label("debits"),
                    func.coalesce(func.sum(JournalEntryLine.credit_amount), 0).label("credits"),
                ).join(
                    JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id
                ).filter(
                    JournalEntry.company_id == company_id,
                    JournalEntry.status == EntryStatus.POSTED,
                    JournalEntry.entry_date <= period.end_date,
                    JournalEntryLine.company_account_id == acc_id,
                ).first()

                curr_book_usd = Decimal(str(totals.debits if totals else 0)) - Decimal(str(totals.credits if totals else 0))
                diff = target_book_usd - curr_book_usd

                if diff != Decimal("0.00"):
                    if diff > Decimal("0.00"):
                        # Asset increase (Gain): Debit Asset
                        acc_debit = diff
                        acc_credit = Decimal("0.00")
                    else:
                        # Asset decrease (Loss): Credit Asset
                        acc_debit = Decimal("0.00")
                        acc_credit = abs(diff)

                    lines_to_create.append({
                        "account_id": acc_id,
                        "debit": acc_debit,
                        "credit": acc_credit,
                        "desc": f"FX Revaluation for {curr_code} balance",
                    })
                    total_adjustment += diff

        if not lines_to_create:
            return None

        # Create Journal Entry
        reval_entry = JournalEntry(
            id=uuid.uuid4(),
            company_id=company_id,
            fiscal_period_id=fiscal_period_id,
            entry_number=f"JE-FX-REVAL-{period.period_number}",
            entry_date=period.end_date,
            description=f"Period-End FX Revaluation for Period {period.period_number}",
            entry_type=EntryType.ADJUSTING,
            status=EntryStatus.POSTED,
            created_by=user_id,
            posted_by=user_id,
            posted_at=datetime.utcnow(),
        )
        self.db.add(reval_entry)
        self.db.flush()

        for l_data in lines_to_create:
            line = JournalEntryLine(
                id=uuid.uuid4(),
                journal_entry_id=reval_entry.id,
                company_account_id=l_data["account_id"],
                line_number=line_num,
                description=l_data["desc"],
                debit_amount=l_data["debit"],
                credit_amount=l_data["credit"],
            )
            self.db.add(line)
            line_num += 1

        # Offset line to FX Gain/Loss
        if total_adjustment > Decimal("0.00"):
            # Net Gain: Credit Gain/Loss
            fx_debit = Decimal("0.00")
            fx_credit = total_adjustment
        else:
            # Net Loss: Debit Gain/Loss
            fx_debit = abs(total_adjustment)
            fx_credit = Decimal("0.00")

        offset_line = JournalEntryLine(
            id=uuid.uuid4(),
            journal_entry_id=reval_entry.id,
            company_account_id=fx_gain_loss_account.id,
            line_number=line_num,
            description="Net Unrealized FX Gain/Loss offset",
            debit_amount=fx_debit,
            credit_amount=fx_credit,
        )
        self.db.add(offset_line)

        self.db.commit()
        self.db.refresh(reval_entry)

        return reval_entry
