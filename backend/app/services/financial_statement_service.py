from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID
from datetime import date
from decimal import Decimal

from app.db.models.company import Company
from app.db.models.company_account import CompanyAccount
from app.db.models.master_account import MasterAccount
from app.db.models.journal_entry import JournalEntry, EntryStatus
from app.db.models.journal_entry_line import JournalEntryLine
from app.db.models.fiscal_period import FiscalPeriod
from app.schemas.financial_statements import (
    BalanceSheetResponse,
    BalanceSheetSection,
    BalanceSheetAccount,
    IncomeStatementResponse,
    IncomeStatementSection,
    IncomeStatementAccount,
    CashFlowStatementResponse,
    CashFlowSection,
    CashFlowAccount
)


class FinancialStatementService:
    """Service for generating financial statements"""

    def __init__(self, db: Session):
        self.db = db

    def generate_balance_sheet(
        self,
        company_id: UUID,
        as_of_date: date
    ) -> BalanceSheetResponse:
        """
        Generate a balance sheet as of a specific date.

        Args:
            company_id: Company ID
            as_of_date: Date to generate balance sheet for

        Returns:
            Balance sheet report
        """
        # Get company
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError("Company not found")

        # Get all company accounts mapped to master accounts
        company_accounts = self.db.query(CompanyAccount).filter(
            and_(
                CompanyAccount.company_id == company_id,
                CompanyAccount.is_active == True
            )
        ).all()

        # Calculate balances for each account
        assets = []
        liabilities = []
        equity_accounts = []

        for company_account in company_accounts:
            if not company_account.master_account_code:
                continue

            master_account = self.db.query(MasterAccount).filter(
                MasterAccount.code == company_account.master_account_code
            ).first()

            if not master_account or master_account.fs_mapping != "Balance Sheet":
                continue

            balance = self._calculate_balance(
                company_account_id=company_account.id,
                as_of_date=as_of_date
            )

            # Skip zero balances
            if abs(balance) < Decimal("0.01"):
                continue

            bs_account = BalanceSheetAccount(
                code=company_account.code,
                description=company_account.description,
                amount=abs(balance),
                level=master_account.level,
                is_header=(company_account.type == "H")
            )

            if master_account.category == "Asset":
                assets.append(bs_account)
            elif master_account.category == "Liability":
                liabilities.append(bs_account)
            elif master_account.category == "Equity":
                equity_accounts.append(bs_account)

        # Calculate totals
        total_assets = sum(acc.amount for acc in assets)
        total_liabilities = sum(acc.amount for acc in liabilities)
        total_equity = sum(acc.amount for acc in equity_accounts)

        # Create sections
        assets_section = BalanceSheetSection(
            name="Assets",
            accounts=sorted(assets, key=lambda x: x.code),
            total=total_assets
        )

        liabilities_section = BalanceSheetSection(
            name="Liabilities",
            accounts=sorted(liabilities, key=lambda x: x.code),
            total=total_liabilities
        )

        equity_section = BalanceSheetSection(
            name="Equity",
            accounts=sorted(equity_accounts, key=lambda x: x.code),
            total=total_equity
        )

        # Check if balanced (Assets = Liabilities + Equity)
        is_balanced = abs(total_assets - (total_liabilities + total_equity)) < Decimal("0.01")

        return BalanceSheetResponse(
            company_id=company_id,
            company_name=company.name,
            as_of_date=as_of_date,
            assets=assets_section,
            liabilities=liabilities_section,
            equity=equity_section,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            total_equity=total_equity,
            is_balanced=is_balanced
        )

    def generate_income_statement(
        self,
        company_id: UUID,
        start_date: date,
        end_date: date
    ) -> IncomeStatementResponse:
        """
        Generate an income statement (P&L) for a period.

        Args:
            company_id: Company ID
            start_date: Period start date
            end_date: Period end date

        Returns:
            Income statement report
        """
        # Get company
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError("Company not found")

        # Get all company accounts mapped to master accounts
        company_accounts = self.db.query(CompanyAccount).filter(
            and_(
                CompanyAccount.company_id == company_id,
                CompanyAccount.is_active == True
            )
        ).all()

        # Calculate balances for each account
        revenue_accounts = []
        cogs_accounts = []
        expense_accounts = []
        other_accounts = []

        for company_account in company_accounts:
            if not company_account.master_account_code:
                continue

            master_account = self.db.query(MasterAccount).filter(
                MasterAccount.code == company_account.master_account_code
            ).first()

            if not master_account or master_account.fs_mapping != "Income Statement":
                continue

            balance = self._calculate_balance_for_period(
                company_account_id=company_account.id,
                start_date=start_date,
                end_date=end_date
            )

            # Skip zero balances
            if abs(balance) < Decimal("0.01"):
                continue

            is_account = IncomeStatementAccount(
                code=company_account.code,
                description=company_account.description,
                amount=abs(balance),
                level=master_account.level,
                is_header=(company_account.type == "H")
            )

            if master_account.category == "Revenue":
                revenue_accounts.append(is_account)
            elif master_account.category == "Cost of Goods Sold":
                cogs_accounts.append(is_account)
            elif master_account.category == "Expense":
                expense_accounts.append(is_account)
            elif master_account.category == "Other":
                other_accounts.append(is_account)

        # Calculate totals
        total_revenue = sum(acc.amount for acc in revenue_accounts)
        total_cogs = sum(acc.amount for acc in cogs_accounts)
        total_expenses = sum(acc.amount for acc in expense_accounts)
        total_other = sum(acc.amount for acc in other_accounts)

        gross_profit = total_revenue - total_cogs
        net_income = gross_profit - total_expenses + total_other

        # Calculate margins
        gross_profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else None
        net_profit_margin = (net_income / total_revenue * 100) if total_revenue > 0 else None

        # Create sections
        revenue_section = IncomeStatementSection(
            name="Revenue",
            accounts=sorted(revenue_accounts, key=lambda x: x.code),
            total=total_revenue
        )

        cogs_section = IncomeStatementSection(
            name="Cost of Goods Sold",
            accounts=sorted(cogs_accounts, key=lambda x: x.code),
            total=total_cogs
        )

        expenses_section = IncomeStatementSection(
            name="Operating Expenses",
            accounts=sorted(expense_accounts, key=lambda x: x.code),
            total=total_expenses
        )

        other_section = IncomeStatementSection(
            name="Other Income/Expense",
            accounts=sorted(other_accounts, key=lambda x: x.code),
            total=total_other
        )

        return IncomeStatementResponse(
            company_id=company_id,
            company_name=company.name,
            period_start=start_date,
            period_end=end_date,
            revenue=revenue_section,
            cost_of_goods_sold=cogs_section,
            expenses=expenses_section,
            other_income=other_section,
            total_revenue=total_revenue,
            total_cogs=total_cogs,
            gross_profit=gross_profit,
            gross_profit_margin=gross_profit_margin,
            total_expenses=total_expenses,
            total_other_income=total_other,
            net_income=net_income,
            net_profit_margin=net_profit_margin
        )

    def generate_cash_flow_statement(
        self,
        company_id: UUID,
        start_date: date,
        end_date: date
    ) -> CashFlowStatementResponse:
        """
        Generate a cash flow statement (indirect method) for a period.

        Args:
            company_id: Company ID
            start_date: Period start date
            end_date: Period end date

        Returns:
            Cash flow statement report
        """
        # Get company
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError("Company not found")

        # Get all company accounts mapped to master accounts
        company_accounts = self.db.query(CompanyAccount).filter(
            and_(
                CompanyAccount.company_id == company_id,
                CompanyAccount.is_active == True
            )
        ).all()

        # Calculate balances by cash flow classification
        operating_accounts = []
        investing_accounts = []
        financing_accounts = []

        for company_account in company_accounts:
            if not company_account.master_account_code:
                continue

            master_account = self.db.query(MasterAccount).filter(
                MasterAccount.code == company_account.master_account_code
            ).first()

            if not master_account or not master_account.cash_flow_classification:
                continue

            balance = self._calculate_balance_for_period(
                company_account_id=company_account.id,
                start_date=start_date,
                end_date=end_date
            )

            # Skip zero balances
            if abs(balance) < Decimal("0.01"):
                continue

            cf_account = CashFlowAccount(
                code=company_account.code,
                description=company_account.description,
                amount=abs(balance),
                level=master_account.level,
                is_header=(company_account.type == "H")
            )

            if "Operating" in master_account.cash_flow_classification:
                operating_accounts.append(cf_account)
            elif "Investing" in master_account.cash_flow_classification:
                investing_accounts.append(cf_account)
            elif "Financing" in master_account.cash_flow_classification:
                financing_accounts.append(cf_account)

        # Calculate totals
        net_cash_operations = sum(acc.amount for acc in operating_accounts)
        net_cash_investing = sum(acc.amount for acc in investing_accounts)
        net_cash_financing = sum(acc.amount for acc in financing_accounts)
        net_change_in_cash = net_cash_operations + net_cash_investing + net_cash_financing

        # Get beginning and ending cash balances
        beginning_cash = self._get_cash_balance(company_id, start_date)
        ending_cash = beginning_cash + net_change_in_cash

        # Create sections
        operating_section = CashFlowSection(
            name="Operating Activities",
            accounts=sorted(operating_accounts, key=lambda x: x.code),
            total=net_cash_operations
        )

        investing_section = CashFlowSection(
            name="Investing Activities",
            accounts=sorted(investing_accounts, key=lambda x: x.code),
            total=net_cash_investing
        )

        financing_section = CashFlowSection(
            name="Financing Activities",
            accounts=sorted(financing_accounts, key=lambda x: x.code),
            total=net_cash_financing
        )

        return CashFlowStatementResponse(
            company_id=company_id,
            company_name=company.name,
            period_start=start_date,
            period_end=end_date,
            operating_activities=operating_section,
            investing_activities=investing_section,
            financing_activities=financing_section,
            net_cash_from_operations=net_cash_operations,
            net_cash_from_investing=net_cash_investing,
            net_cash_from_financing=net_cash_financing,
            net_change_in_cash=net_change_in_cash,
            beginning_cash_balance=beginning_cash,
            ending_cash_balance=ending_cash
        )

    def _calculate_balance(self, company_account_id: UUID, as_of_date: date) -> Decimal:
        """
        Calculate account balance as of a specific date.

        Args:
            company_account_id: Company account ID
            as_of_date: Date to calculate balance as of

        Returns:
            Account balance
        """
        # Get all posted journal entry lines up to date
        lines = self.db.query(JournalEntryLine).join(
            JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id
        ).filter(
            and_(
                JournalEntryLine.company_account_id == company_account_id,
                JournalEntry.status == EntryStatus.POSTED,
                JournalEntry.entry_date <= as_of_date
            )
        ).all()

        total_debits = sum(Decimal(str(line.debit_amount)) for line in lines)
        total_credits = sum(Decimal(str(line.credit_amount)) for line in lines)

        # Get normal balance from master account
        company_account = self.db.query(CompanyAccount).filter(
            CompanyAccount.id == company_account_id
        ).first()

        normal_balance = "Debit"
        if company_account and company_account.master_account_code:
            master_account = self.db.query(MasterAccount).filter(
                MasterAccount.code == company_account.master_account_code
            ).first()
            if master_account:
                normal_balance = master_account.normal_balance

        # Calculate balance based on normal balance
        if normal_balance == "Debit":
            return total_debits - total_credits
        else:
            return total_credits - total_debits

    def _calculate_balance_for_period(
        self,
        company_account_id: UUID,
        start_date: date,
        end_date: date
    ) -> Decimal:
        """
        Calculate account balance for a specific period.

        Args:
            company_account_id: Company account ID
            start_date: Period start date
            end_date: Period end date

        Returns:
            Account balance for period
        """
        # Get posted journal entry lines in date range
        lines = self.db.query(JournalEntryLine).join(
            JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id
        ).filter(
            and_(
                JournalEntryLine.company_account_id == company_account_id,
                JournalEntry.status == EntryStatus.POSTED,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            )
        ).all()

        total_debits = sum(Decimal(str(line.debit_amount)) for line in lines)
        total_credits = sum(Decimal(str(line.credit_amount)) for line in lines)

        # Get normal balance from master account
        company_account = self.db.query(CompanyAccount).filter(
            CompanyAccount.id == company_account_id
        ).first()

        normal_balance = "Debit"
        if company_account and company_account.master_account_code:
            master_account = self.db.query(MasterAccount).filter(
                MasterAccount.code == company_account.master_account_code
            ).first()
            if master_account:
                normal_balance = master_account.normal_balance

        # Calculate balance based on normal balance
        if normal_balance == "Debit":
            return total_debits - total_credits
        else:
            return total_credits - total_debits

    def _get_cash_balance(self, company_id: UUID, as_of_date: date) -> Decimal:
        """
        Get total cash balance as of a specific date.

        Args:
            company_id: Company ID
            as_of_date: Date to get cash balance for

        Returns:
            Total cash balance
        """
        # Find all cash accounts (category contains "Cash")
        company_accounts = self.db.query(CompanyAccount).filter(
            and_(
                CompanyAccount.company_id == company_id,
                CompanyAccount.is_active == True
            )
        ).all()

        total_cash = Decimal("0.00")

        for account in company_accounts:
            if not account.master_account_code:
                continue

            master_account = self.db.query(MasterAccount).filter(
                MasterAccount.code == account.master_account_code
            ).first()

            if master_account and "Cash" in (master_account.category or ""):
                balance = self._calculate_balance(account.id, as_of_date)
                total_cash += balance

        return total_cash
