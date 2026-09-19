"""
Year-End Closing Service
Handles closing nominal accounts (Revenue and Expenses) at the end of a fiscal year
and rolling cumulative Net Income into Retained Earnings (Account 39000).
"""

import uuid
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models.company_account import CompanyAccount
from app.db.models.master_account import MasterAccount
from app.db.models.fiscal_period import FiscalPeriod
from app.db.models.journal_entry import JournalEntry, EntryStatus, EntryType
from app.db.models.journal_entry_line import JournalEntryLine
from app.db.models.enums import AccountType


class YearEndClosingService:
    """Service to execute annual nominal account closing entries."""

    def __init__(self, db: Session):
        self.db = db

    def _get_retained_earnings_account(self, company_id: UUID) -> CompanyAccount:
        """Find the company's Retained Earnings account (mapped to master account 39000 or code 39000)."""
        re_account = self.db.query(CompanyAccount).join(
            MasterAccount, CompanyAccount.mapped_master_account_id == MasterAccount.id, isouter=True
        ).filter(
            CompanyAccount.company_id == company_id,
            CompanyAccount.is_active.is_(True),
            (MasterAccount.code == "39000") | (CompanyAccount.code == "39000") | (CompanyAccount.name.ilike("%retained earnings%")) | (CompanyAccount.description.ilike("%retained earnings%"))
        ).first()

        if not re_account:
            # Fallback to any Equity account
            re_account = self.db.query(CompanyAccount).filter(
                CompanyAccount.company_id == company_id,
                CompanyAccount.account_type == AccountType.EQUITY,
                CompanyAccount.is_active.is_(True),
            ).first()

        if not re_account:
            raise ValueError("Company does not have an active Retained Earnings or Equity account to receive closed earnings.")

        return re_account

    def calculate_nominal_balances(self, company_id: UUID, fiscal_year: int) -> Dict[UUID, Dict[str, Any]]:
        """
        Calculate the cumulative net activity for all Revenue and Expense accounts in the fiscal year.
        Returns a map of account_id -> { account, net_balance, normal_balance, account_type }.
        """
        year_start = date(fiscal_year, 1, 1)
        year_end = date(fiscal_year, 12, 31)

        nominal_accounts = self.db.query(CompanyAccount).filter(
            CompanyAccount.company_id == company_id,
            CompanyAccount.account_type.in_([AccountType.REVENUE, AccountType.EXPENSE]),
            CompanyAccount.is_active.is_(True),
        ).all()

        results: Dict[UUID, Dict[str, Any]] = {}
        for acc in nominal_accounts:
            # Sum debits and credits across posted journal entries in the year
            totals = self.db.query(
                func.coalesce(func.sum(JournalEntryLine.debit_amount), 0).label("total_debits"),
                func.coalesce(func.sum(JournalEntryLine.credit_amount), 0).label("total_credits"),
            ).join(
                JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id
            ).filter(
                JournalEntry.company_id == company_id,
                JournalEntry.status == EntryStatus.POSTED,
                JournalEntry.entry_type != EntryType.CLOSING,
                JournalEntry.entry_date >= year_start,
                JournalEntry.entry_date <= year_end,
                JournalEntryLine.company_account_id == acc.id,
            ).first()

            debits = Decimal(str(totals.total_debits if totals else 0))
            credits = Decimal(str(totals.total_credits if totals else 0))

            acc_type = acc.account_type
            if isinstance(acc_type, AccountType):
                is_revenue = acc_type == AccountType.REVENUE
            else:
                is_revenue = str(acc_type) == AccountType.REVENUE.value

            if is_revenue:
                # Revenue normal balance is Credit. Net balance = credits - debits
                net = credits - debits
            else:
                # Expense normal balance is Debit. Net balance = debits - credits
                net = debits - credits

            if net != Decimal("0.00"):
                results[acc.id] = {
                    "account": acc,
                    "net_balance": net,
                    "account_type": acc.account_type,
                    "total_debits": debits,
                    "total_credits": credits,
                }

        return results

    def generate_year_end_closing_entry(
        self,
        company_id: UUID,
        fiscal_year: int,
        closing_period_id: UUID,
        user_id: UUID,
        closing_date: Optional[date] = None,
    ) -> JournalEntry:
        """
        Generate and post the year-end closing journal entry.
        Zeroes out all Revenue and Expense accounts and posts net income/loss to Retained Earnings.
        """
        if closing_date is None:
            closing_date = date(fiscal_year, 12, 31)

        period = self.db.query(FiscalPeriod).filter(
            FiscalPeriod.id == closing_period_id,
            FiscalPeriod.company_id == company_id,
        ).first()

        if not period or not period.is_open():
            raise ValueError(f"Closing period {closing_period_id} is not open for company {company_id}")

        nominal_map = self.calculate_nominal_balances(company_id, fiscal_year)
        if not nominal_map:
            raise ValueError(f"No active nominal account activity found for fiscal year {fiscal_year}")

        re_account = self._get_retained_earnings_account(company_id)

        closing_entry = JournalEntry(
            id=uuid.uuid4(),
            company_id=company_id,
            fiscal_period_id=closing_period_id,
            entry_number=f"JE-CLOSE-{fiscal_year}",
            entry_date=closing_date,
            description=f"Year-End Closing Entry for Fiscal Year {fiscal_year}",
            entry_type=EntryType.CLOSING,
            status=EntryStatus.POSTED,
            created_by=user_id,
            posted_by=user_id,
            posted_at=datetime.utcnow(),
        )
        self.db.add(closing_entry)
        self.db.flush()

        lines: List[JournalEntryLine] = []
        line_num = 1
        total_revenue_net = Decimal("0.00")
        total_expense_net = Decimal("0.00")

        for acc_id, data in nominal_map.items():
            acc = data["account"]
            net = data["net_balance"]
            acc_type = data["account_type"]

            is_revenue = (acc_type == AccountType.REVENUE) if isinstance(acc_type, AccountType) else (str(acc_type) == AccountType.REVENUE.value)

            if is_revenue:
                total_revenue_net += net
                # To zero a Revenue credit balance, debit it
                if net > Decimal("0.00"):
                    debit_amt = net
                    credit_amt = Decimal("0.00")
                else:
                    debit_amt = Decimal("0.00")
                    credit_amt = abs(net)
            else:
                total_expense_net += net
                # To zero an Expense debit balance, credit it
                if net > Decimal("0.00"):
                    debit_amt = Decimal("0.00")
                    credit_amt = net
                else:
                    debit_amt = abs(net)
                    credit_amt = Decimal("0.00")

            line = JournalEntryLine(
                id=uuid.uuid4(),
                journal_entry_id=closing_entry.id,
                company_account_id=acc.id,
                line_number=line_num,
                description=f"Close {acc.description or acc.name or acc.code} to Retained Earnings",
                debit_amount=debit_amt,
                credit_amount=credit_amt,
            )
            self.db.add(line)
            lines.append(line)
            line_num += 1

        # Net Income = Total Revenue - Total Expenses
        net_income = total_revenue_net - total_expense_net
        if net_income > Decimal("0.00"):
            # Profit: Credit Retained Earnings
            re_debit = Decimal("0.00")
            re_credit = net_income
        else:
            # Loss: Debit Retained Earnings
            re_debit = abs(net_income)
            re_credit = Decimal("0.00")

        re_line = JournalEntryLine(
            id=uuid.uuid4(),
            journal_entry_id=closing_entry.id,
            company_account_id=re_account.id,
            line_number=line_num,
            description=f"Net Income for Fiscal Year {fiscal_year} rolled into Retained Earnings",
            debit_amount=re_debit,
            credit_amount=re_credit,
        )
        self.db.add(re_line)
        lines.append(re_line)

        self.db.commit()
        self.db.refresh(closing_entry)

        return closing_entry
