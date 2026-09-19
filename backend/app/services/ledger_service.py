from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict
from uuid import UUID
from datetime import date
from decimal import Decimal

from app.db.models.journal_entry import JournalEntry, EntryStatus
from app.db.models.journal_entry_line import JournalEntryLine
from app.db.models.account_balance import AccountBalance
from app.db.models.fiscal_period import FiscalPeriod
from app.db.models.company_account import CompanyAccount
from app.db.models.enums import AccountType, NormalBalance
from app.schemas.ledger import (
    AccountLedger,
    LedgerEntryResponse,
    TrialBalanceResponse,
    TrialBalanceAccount,
    AccountBalanceResponse
)


class LedgerService:
    """Service for ledger operations and balance calculations"""

    def __init__(self, db: Session):
        self.db = db

    def _resolve_normal_balance(self, account: CompanyAccount) -> str:
        if account.normal_balance:
            if isinstance(account.normal_balance, NormalBalance):
                return account.normal_balance.value
            return str(account.normal_balance)
        return NormalBalance.DEBIT.value

    def _resolve_category(self, account: CompanyAccount) -> str:
        if account.json_data and isinstance(account.json_data, dict):
            category = account.json_data.get("category")
            if category:
                return str(category)
        if account.account_type:
            if isinstance(account.account_type, AccountType):
                return account.account_type.value
            return str(account.account_type)
        return "Other"

    def post_journal_entry(self, journal_entry: JournalEntry) -> Dict[UUID, AccountBalance]:
        """
        Post a journal entry to the ledger (update account balances).

        Args:
            journal_entry: Posted journal entry

        Returns:
            Dictionary of account_id -> updated AccountBalance

        Raises:
            ValueError: If posting fails
        """
        if journal_entry.status != EntryStatus.POSTED:
            raise ValueError("Can only post journal entries with status POSTED")

        account_balances = {}

        for line in journal_entry.lines:
            # Get or create account balance for this period
            account_balance = self._get_or_create_account_balance(
                company_id=journal_entry.company_id,
                company_account_id=line.company_account_id,
                fiscal_period_id=journal_entry.fiscal_period_id
            )

            # Get account's normal balance from company account
            company_account = self.db.query(CompanyAccount).filter(
                CompanyAccount.id == line.company_account_id
            ).first()
            normal_balance = self._resolve_normal_balance(company_account) if company_account else NormalBalance.DEBIT.value

            # Update balance
            account_balance.update_balance(
                debit_amount=Decimal(str(line.debit_amount)),
                credit_amount=Decimal(str(line.credit_amount)),
                normal_balance=normal_balance
            )

            account_balances[line.company_account_id] = account_balance

        self.db.commit()

        return account_balances

    def get_account_ledger(
        self,
        company_id: UUID,
        company_account_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        fiscal_period_id: Optional[UUID] = None
    ) -> AccountLedger:
        """
        Get the ledger for a specific account.

        Args:
            company_id: Company ID
            company_account_id: Company account ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            fiscal_period_id: Optional fiscal period filter

        Returns:
            Account ledger with all entries
        """
        # Get account details
        company_account = self.db.query(CompanyAccount).filter(
            CompanyAccount.id == company_account_id
        ).first()

        if not company_account:
            raise ValueError("Company account not found")

        # Get normal balance from company account
        normal_balance = self._resolve_normal_balance(company_account)

        # Build query for journal entry lines
        query = self.db.query(
            JournalEntryLine,
            JournalEntry
        ).join(
            JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id
        ).filter(
            and_(
                JournalEntryLine.company_account_id == company_account_id,
                JournalEntry.company_id == company_id,
                JournalEntry.status == EntryStatus.POSTED
            )
        )

        if fiscal_period_id:
            query = query.filter(JournalEntry.fiscal_period_id == fiscal_period_id)

        if start_date:
            query = query.filter(JournalEntry.entry_date >= start_date)

        if end_date:
            query = query.filter(JournalEntry.entry_date <= end_date)

        query = query.order_by(JournalEntry.entry_date, JournalEntry.entry_number)

        results = query.all()

        # Calculate running balance
        entries = []
        running_balance = Decimal("0.00")
        total_debits = Decimal("0.00")
        total_credits = Decimal("0.00")

        for line, journal_entry in results:
            debit = Decimal(str(line.debit_amount))
            credit = Decimal(str(line.credit_amount))

            # Update running balance based on normal balance
            if normal_balance == "Debit":
                running_balance += debit - credit
            else:
                running_balance -= debit - credit

            total_debits += debit
            total_credits += credit

            ledger_entry = LedgerEntryResponse(
                journal_entry_id=journal_entry.id,
                journal_entry_line_id=line.id,
                entry_date=journal_entry.entry_date,
                entry_number=journal_entry.entry_number,
                description=line.description or journal_entry.description,
                reference=journal_entry.reference,
                debit_amount=debit,
                credit_amount=credit,
                running_balance=running_balance,
                account_code=company_account.code,
                account_description=company_account.description
            )
            entries.append(ledger_entry)

        # Get beginning balance (if filtering by period)
        beginning_balance = Decimal("0.00")
        if fiscal_period_id:
            account_balance = self.db.query(AccountBalance).filter(
                and_(
                    AccountBalance.company_account_id == company_account_id,
                    AccountBalance.fiscal_period_id == fiscal_period_id
                )
            ).first()
            if account_balance:
                beginning_balance = Decimal(str(account_balance.beginning_balance))

        return AccountLedger(
            company_id=company_id,
            company_account_id=company_account_id,
            account_code=company_account.code,
            account_description=company_account.description,
            normal_balance=normal_balance,
            beginning_balance=beginning_balance,
            ending_balance=running_balance,
            total_debits=total_debits,
            total_credits=total_credits,
            entries=entries
        )

    def get_trial_balance(
        self,
        company_id: UUID,
        fiscal_period_id: Optional[UUID] = None,
        as_of_date: Optional[date] = None,
        department_id: Optional[UUID] = None,
        cost_center_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
    ) -> TrialBalanceResponse:
        """
        Generate a trial balance report.

        Args:
            company_id: Company ID
            fiscal_period_id: Optional fiscal period filter
            as_of_date: Optional as-of date

        Returns:
            Trial balance report
        """
        # Get fiscal period for date range
        fiscal_period = None
        if fiscal_period_id:
            fiscal_period = self.db.query(FiscalPeriod).filter(
                FiscalPeriod.id == fiscal_period_id
            ).first()
            period_start = fiscal_period.start_date
            period_end = fiscal_period.end_date
        elif as_of_date:
            period_start = date(as_of_date.year, 1, 1)
            period_end = as_of_date
        else:
            raise ValueError("Must provide either fiscal_period_id or as_of_date")

        # Get all company accounts
        company_accounts = self.db.query(CompanyAccount).filter(
            and_(
                CompanyAccount.company_id == company_id,
                CompanyAccount.is_active == True
            )
        ).all()

        trial_balance_accounts = []
        total_debits = Decimal("0.00")
        total_credits = Decimal("0.00")

        for company_account in company_accounts:
            # Calculate account balance
            balance = self._calculate_account_balance(
                company_account_id=company_account.id,
                start_date=period_start,
                end_date=period_end,
                department_id=department_id,
                cost_center_id=cost_center_id,
                project_id=project_id,
                location_id=location_id,
            )

            normal_balance = self._resolve_normal_balance(company_account)
            category = self._resolve_category(company_account)
            account_type = "Header" if company_account.type == "H" else "Detail"

            # Determine debit or credit balance
            debit_balance = Decimal("0.00")
            credit_balance = Decimal("0.00")

            if normal_balance == "Debit":
                if balance >= 0:
                    debit_balance = balance
                else:
                    credit_balance = abs(balance)
            else:
                if balance >= 0:
                    credit_balance = balance
                else:
                    debit_balance = abs(balance)

            # Only include accounts with balance
            if debit_balance > 0 or credit_balance > 0:
                tb_account = TrialBalanceAccount(
                    account_code=company_account.code,
                    account_description=company_account.description,
                    account_type=account_type,
                    category=category,
                    normal_balance=normal_balance,
                    debit_balance=debit_balance,
                    credit_balance=credit_balance
                )
                trial_balance_accounts.append(tb_account)

                total_debits += debit_balance
                total_credits += credit_balance

        # Check if balanced
        variance = abs(total_debits - total_credits)
        is_balanced = variance < Decimal("0.01")  # Allow for rounding errors

        return TrialBalanceResponse(
            company_id=company_id,
            period_start=period_start,
            period_end=period_end,
            accounts=trial_balance_accounts,
            total_debits=total_debits,
            total_credits=total_credits,
            is_balanced=is_balanced,
            variance=variance
        )

    def _get_or_create_account_balance(
        self,
        company_id: UUID,
        company_account_id: UUID,
        fiscal_period_id: UUID
    ) -> AccountBalance:
        """
        Get or create an account balance record for a period.

        Args:
            company_id: Company ID
            company_account_id: Company account ID
            fiscal_period_id: Fiscal period ID

        Returns:
            Account balance record
        """
        account_balance = self.db.query(AccountBalance).filter(
            and_(
                AccountBalance.company_account_id == company_account_id,
                AccountBalance.fiscal_period_id == fiscal_period_id
            )
        ).first()

        if not account_balance:
            # Get beginning balance from previous period
            fiscal_period = self.db.query(FiscalPeriod).filter(
                FiscalPeriod.id == fiscal_period_id
            ).first()

            # Find previous period
            previous_period = self.db.query(FiscalPeriod).filter(
                and_(
                    FiscalPeriod.company_id == company_id,
                    FiscalPeriod.period_type == fiscal_period.period_type,
                    FiscalPeriod.end_date < fiscal_period.start_date
                )
            ).order_by(FiscalPeriod.end_date.desc()).first()

            beginning_balance = Decimal("0.00")
            if previous_period:
                previous_balance = self.db.query(AccountBalance).filter(
                    and_(
                        AccountBalance.company_account_id == company_account_id,
                        AccountBalance.fiscal_period_id == previous_period.id
                    )
                ).first()

                if previous_balance:
                    beginning_balance = Decimal(str(previous_balance.ending_balance))

            account_balance = AccountBalance(
                company_id=company_id,
                company_account_id=company_account_id,
                fiscal_period_id=fiscal_period_id,
                beginning_balance=beginning_balance,
                total_debits=Decimal("0.00"),
                total_credits=Decimal("0.00"),
                ending_balance=beginning_balance
            )
            self.db.add(account_balance)
            self.db.flush()

        return account_balance

    def _calculate_account_balance(
        self,
        company_account_id: UUID,
        start_date: date,
        end_date: date,
        department_id: Optional[UUID] = None,
        cost_center_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
    ) -> Decimal:
        """
        Calculate account balance for a specific period with optional dimensional filters.
        """
        filters = [
            JournalEntryLine.company_account_id == company_account_id,
            JournalEntry.status == EntryStatus.POSTED,
            JournalEntry.entry_date >= start_date,
            JournalEntry.entry_date <= end_date,
        ]

        if department_id:
            filters.append(JournalEntryLine.department_id == department_id)
        if cost_center_id:
            filters.append(JournalEntryLine.cost_center_id == cost_center_id)
        if project_id:
            filters.append(JournalEntryLine.project_id == project_id)
        if location_id:
            filters.append(JournalEntryLine.location_id == location_id)

        # Get posted journal entry lines in date range
        lines = self.db.query(JournalEntryLine).join(
            JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id
        ).filter(and_(*filters)).all()

        total_debits = sum(Decimal(str(line.debit_amount)) for line in lines)
        total_credits = sum(Decimal(str(line.credit_amount)) for line in lines)

        # Get account's normal balance to determine sign
        company_account = self.db.query(CompanyAccount).filter(
            CompanyAccount.id == company_account_id
        ).first()

        normal_balance = self._resolve_normal_balance(company_account) if company_account else NormalBalance.DEBIT.value

        # Calculate balance based on normal balance
        if normal_balance == "Debit":
            return total_debits - total_credits
        else:
            return total_credits - total_debits

    def get_account_balances(
        self,
        company_id: UUID,
        fiscal_period_id: UUID
    ) -> List[AccountBalanceResponse]:
        """
        Get all account balances for a fiscal period.

        Args:
            company_id: Company ID
            fiscal_period_id: Fiscal period ID

        Returns:
            List of account balances
        """
        balances = self.db.query(AccountBalance).filter(
            and_(
                AccountBalance.company_id == company_id,
                AccountBalance.fiscal_period_id == fiscal_period_id
            )
        ).all()

        result = []
        for balance in balances:
            company_account = self.db.query(CompanyAccount).filter(
                CompanyAccount.id == balance.company_account_id
            ).first()

            balance_response = AccountBalanceResponse(
                id=balance.id,
                company_id=balance.company_id,
                company_account_id=balance.company_account_id,
                fiscal_period_id=balance.fiscal_period_id,
                beginning_balance=balance.beginning_balance,
                total_debits=balance.total_debits,
                total_credits=balance.total_credits,
                ending_balance=balance.ending_balance,
                account_code=company_account.code if company_account else None,
                account_description=company_account.description if company_account else None
            )
            result.append(balance_response)

        return result
