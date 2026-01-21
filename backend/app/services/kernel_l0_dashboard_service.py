from datetime import date
from decimal import Decimal
from typing import Dict, Iterable, Optional
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.db.models.company_account import CompanyAccount
from app.db.models.enums import NormalBalance
from app.db.models.fiscal_period import FiscalPeriod, PeriodStatus
from app.db.models.journal_entry import JournalEntry, EntryStatus
from app.db.models.journal_entry_line import JournalEntryLine
from app.services.kernel_l0_dashboard_math import (
    BALANCE_SHEET_CODES,
    INCOME_STATEMENT_CODES,
    KERNEL_L0_CORE_CODES,
    REDUCTION_CODES,
    compute_core_metric_deltas,
    compute_core_metrics_from_balances,
)


class KernelL0DashboardService:
    """Compute Kernel L0 Dashboard Tier 1 Core Metrics."""

    def __init__(self, db: Session):
        self.db = db

    def _resolve_normal_balance(self, account: CompanyAccount) -> str:
        if account.normal_balance:
            if isinstance(account.normal_balance, NormalBalance):
                return account.normal_balance.value
            return str(account.normal_balance)
        return NormalBalance.DEBIT.value

    def _get_fiscal_period(
        self,
        company_id: UUID,
        fiscal_period_id: Optional[UUID]
    ) -> FiscalPeriod:
        if fiscal_period_id:
            period = self.db.query(FiscalPeriod).filter(
                and_(
                    FiscalPeriod.id == fiscal_period_id,
                    FiscalPeriod.company_id == company_id,
                )
            ).first()
            if not period:
                raise ValueError("Fiscal period not found for company")
            return period

        open_periods = self.db.query(FiscalPeriod).filter(
            and_(
                FiscalPeriod.company_id == company_id,
                FiscalPeriod.status == PeriodStatus.OPEN,
            )
        ).order_by(FiscalPeriod.start_date.asc()).all()

        if len(open_periods) == 1:
            return open_periods[0]

        if len(open_periods) == 0:
            raise ValueError("No open fiscal period found; specify fiscal_period_id")

        raise ValueError("Multiple open fiscal periods found; specify fiscal_period_id")

    def _get_prior_period(self, period: FiscalPeriod) -> Optional[FiscalPeriod]:
        return self.db.query(FiscalPeriod).filter(
            and_(
                FiscalPeriod.company_id == period.company_id,
                FiscalPeriod.period_type == period.period_type,
                FiscalPeriod.end_date < period.start_date,
            )
        ).order_by(FiscalPeriod.end_date.desc()).first()

    def _get_company_accounts(
        self,
        company_id: UUID,
        codes: Iterable[str]
    ) -> Dict[str, CompanyAccount]:
        accounts = self.db.query(CompanyAccount).filter(
            and_(
                CompanyAccount.company_id == company_id,
                CompanyAccount.code.in_(list(codes)),
                CompanyAccount.is_active == True,
            )
        ).all()

        account_map = {account.code: account for account in accounts}
        missing = sorted(set(codes) - set(account_map.keys()))
        if missing:
            raise ValueError(
                "Missing required Kernel L0 accounts: " + ", ".join(missing)
            )

        return account_map

    def _calculate_balance_as_of(self, account: CompanyAccount, as_of_date: date) -> Decimal:
        lines = self.db.query(JournalEntryLine).join(
            JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id
        ).filter(
            and_(
                JournalEntryLine.company_account_id == account.id,
                JournalEntry.status == EntryStatus.POSTED,
                JournalEntry.entry_date <= as_of_date,
            )
        ).all()

        total_debits = sum(Decimal(str(line.debit_amount)) for line in lines)
        total_credits = sum(Decimal(str(line.credit_amount)) for line in lines)

        normal_balance = self._resolve_normal_balance(account)
        if normal_balance == "Debit":
            return total_debits - total_credits
        return total_credits - total_debits

    def _calculate_balance_for_period(
        self,
        account: CompanyAccount,
        start_date: date,
        end_date: date
    ) -> Decimal:
        lines = self.db.query(JournalEntryLine).join(
            JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id
        ).filter(
            and_(
                JournalEntryLine.company_account_id == account.id,
                JournalEntry.status == EntryStatus.POSTED,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date,
            )
        ).all()

        total_debits = sum(Decimal(str(line.debit_amount)) for line in lines)
        total_credits = sum(Decimal(str(line.credit_amount)) for line in lines)

        normal_balance = self._resolve_normal_balance(account)
        if normal_balance == "Debit":
            return total_debits - total_credits
        return total_credits - total_debits

    def _normalize_reporting_polarity(self, code: str, amount: Decimal) -> Decimal:
        if code in REDUCTION_CODES:
            return abs(amount)
        return amount

    def _get_normalized_balances(
        self,
        accounts: Dict[str, CompanyAccount],
        period: FiscalPeriod
    ) -> Dict[str, Decimal]:
        balances: Dict[str, Decimal] = {}

        for code in BALANCE_SHEET_CODES:
            raw_balance = self._calculate_balance_as_of(accounts[code], period.end_date)
            balances[code] = self._normalize_reporting_polarity(code, raw_balance)

        for code in INCOME_STATEMENT_CODES:
            raw_balance = self._calculate_balance_for_period(
                accounts[code],
                period.start_date,
                period.end_date,
            )
            balances[code] = self._normalize_reporting_polarity(code, raw_balance)

        return balances

    def get_core_metrics(
        self,
        company_id: UUID,
        fiscal_period_id: Optional[UUID] = None
    ) -> Dict[str, object]:
        period = self._get_fiscal_period(company_id, fiscal_period_id)
        accounts = self._get_company_accounts(company_id, KERNEL_L0_CORE_CODES)

        current_balances = self._get_normalized_balances(accounts, period)
        current_metrics = compute_core_metrics_from_balances(current_balances)

        prior_period = self._get_prior_period(period)
        prior_metrics = None
        if prior_period:
            prior_balances = self._get_normalized_balances(accounts, prior_period)
            prior_metrics = compute_core_metrics_from_balances(prior_balances)

        deltas = compute_core_metric_deltas(current_metrics, prior_metrics)

        return {
            "company_id": company_id,
            "fiscal_period_id": period.id,
            "period_start": period.start_date,
            "period_end": period.end_date,
            "total_cash": current_metrics.total_cash,
            "net_revenue": current_metrics.net_revenue,
            "operating_income": current_metrics.operating_income,
            "net_working_capital": current_metrics.net_working_capital,
            "current_ratio": current_metrics.current_ratio,
            "total_cash_delta": deltas.total_cash,
            "net_revenue_delta": deltas.net_revenue,
            "operating_income_delta": deltas.operating_income,
            "net_working_capital_delta": deltas.net_working_capital,
            "current_ratio_delta": deltas.current_ratio,
        }
