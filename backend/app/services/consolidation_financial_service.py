from decimal import Decimal
from datetime import date
from typing import Dict, Any, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models.group_company import GroupCompany
from app.db.models.group_company_member import GroupCompanyMember
from app.db.models.company_account import CompanyAccount
from app.db.models.master_account import MasterAccount
from app.db.models.journal_entry import JournalEntry, EntryStatus
from app.db.models.journal_entry_line import JournalEntryLine
from app.db.models.enums import AccountType
from app.services.financial_statement_service import FinancialStatementService


class ConsolidationFinancialService:
    """Service to generate group consolidated statements with intercompany eliminations."""

    def __init__(self, db: Session):
        self.db = db
        self.fs_service = FinancialStatementService(db)

    def generate_consolidated_income_statement(
        self,
        group_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """
        Generate consolidated Income Statement rolling up all member companies
        and eliminating matched intercompany revenue and expense.
        """
        members = self.db.query(GroupCompanyMember).filter(
            GroupCompanyMember.group_company_id == group_id,
        ).all()

        if not members:
            raise ValueError(f"No active members found for group {group_id}")

        total_gross_revenue = Decimal("0.00")
        total_gross_expenses = Decimal("0.00")

        # Sum individual statements
        for m in members:
            pnl = self.fs_service.generate_income_statement(
                company_id=m.company_id,
                start_date=start_date,
                end_date=end_date,
            )
            total_gross_revenue += pnl.total_revenue
            total_gross_expenses += pnl.total_expenses

        # Identify intercompany lines for elimination
        # Accounts mapped to MasterAccount 13000 / 23000 or descriptions with Intercompany / Due From / Due To
        company_ids = [m.company_id for m in members]

        intercompany_lines = self.db.query(JournalEntryLine).join(
            JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id
        ).filter(
            JournalEntry.company_id.in_(company_ids),
            JournalEntry.status == EntryStatus.POSTED,
            JournalEntry.entry_date >= start_date,
            JournalEntry.entry_date <= end_date,
            JournalEntry.description.ilike("%intercompany%"),
        ).all()

        elim_rev = Decimal("0.00")
        elim_exp = Decimal("0.00")

        # Only count revenue accounts (credits on revenue) and expense accounts (debits on expense)
        for line in intercompany_lines:
            acc = line.company_account
            if acc:
                acc_type = acc.account_type
                if isinstance(acc_type, AccountType):
                    acc_type_val = acc_type.value
                else:
                    acc_type_val = str(acc_type or "")

                if acc_type_val.upper() in ("REVENUE", "OPERATING REVENUE"):
                    elim_rev += Decimal(str(line.credit_amount))
                elif acc_type_val.upper() in ("EXPENSE", "EXPENSES", "OPERATING EXPENSES"):
                    elim_exp += Decimal(str(line.debit_amount))

        net_rev = total_gross_revenue - elim_rev
        net_exp = total_gross_expenses - elim_exp
        net_income = net_rev - net_exp

        return {
            "gross_revenue": total_gross_revenue,
            "gross_expenses": total_gross_expenses,
            "eliminated_intercompany_revenue": elim_rev,
            "eliminated_intercompany_expenses": elim_exp,
            "net_consolidated_revenue": net_rev,
            "net_consolidated_expenses": net_exp,
            "net_consolidated_income": net_income,
        }
