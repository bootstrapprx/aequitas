from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

from app.db.models.journal_entry import JournalEntry, EntryStatus, EntryType
from app.db.models.journal_entry_line import JournalEntryLine
from app.db.models.fiscal_period import FiscalPeriod, PeriodStatus
from app.db.models.company_account import CompanyAccount
from app.db.models.master_account import MasterAccount
from app.schemas.journal_entry import (
    JournalEntryCreate,
    JournalEntryUpdate,
    JournalEntryResponse,
    JournalEntryLineResponse
)


class JournalEntryService:
    """Service for managing journal entries"""

    def __init__(self, db: Session):
        self.db = db

    def create_journal_entry(
        self,
        entry_data: JournalEntryCreate,
        created_by: UUID
    ) -> JournalEntry:
        """
        Create a new journal entry with double-entry validation.

        Args:
            entry_data: Journal entry creation data
            created_by: User ID creating the entry

        Returns:
            Created journal entry

        Raises:
            ValueError: If validation fails
        """
        # Validate fiscal period exists and is open
        fiscal_period = self.db.query(FiscalPeriod).filter(
            FiscalPeriod.id == entry_data.fiscal_period_id
        ).first()

        if not fiscal_period:
            raise ValueError("Fiscal period not found")

        if not fiscal_period.is_open():
            raise ValueError(f"Fiscal period is {fiscal_period.status}, cannot post entries")

        # Validate entry date is within fiscal period
        if not (fiscal_period.start_date <= entry_data.entry_date <= fiscal_period.end_date):
            raise ValueError(
                f"Entry date {entry_data.entry_date} is outside fiscal period "
                f"{fiscal_period.start_date} to {fiscal_period.end_date}"
            )

        # Validate all accounts exist and belong to the company
        account_ids = [line.company_account_id for line in entry_data.lines]
        accounts = self.db.query(CompanyAccount).filter(
            and_(
                CompanyAccount.id.in_(account_ids),
                CompanyAccount.company_id == entry_data.company_id
            )
        ).all()

        if len(accounts) != len(account_ids):
            raise ValueError("One or more accounts not found or do not belong to company")

        # Validate double-entry (already validated in schema, but double-check)
        total_debits = sum(line.debit_amount for line in entry_data.lines)
        total_credits = sum(line.credit_amount for line in entry_data.lines)

        if total_debits != total_credits:
            raise ValueError(f"Debits ({total_debits}) must equal credits ({total_credits})")

        # Generate entry number
        entry_number = self._generate_entry_number(entry_data.company_id, entry_data.entry_date)

        # Create journal entry
        journal_entry = JournalEntry(
            company_id=entry_data.company_id,
            fiscal_period_id=entry_data.fiscal_period_id,
            entry_number=entry_number,
            entry_date=entry_data.entry_date,
            description=entry_data.description,
            reference=entry_data.reference,
            entry_type=EntryType(entry_data.entry_type),
            status=EntryStatus.DRAFT,
            created_by=created_by
        )

        self.db.add(journal_entry)
        self.db.flush()  # Get the entry ID

        # Create journal entry lines
        for line_data in entry_data.lines:
            line = JournalEntryLine(
                journal_entry_id=journal_entry.id,
                company_account_id=line_data.company_account_id,
                line_number=line_data.line_number,
                description=line_data.description,
                debit_amount=line_data.debit_amount,
                credit_amount=line_data.credit_amount
            )
            self.db.add(line)

        self.db.commit()
        self.db.refresh(journal_entry)

        return journal_entry

    def get_journal_entry(self, entry_id: UUID) -> Optional[JournalEntry]:
        """Get a journal entry by ID"""
        return self.db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()

    def get_journal_entries(
        self,
        company_id: UUID,
        fiscal_period_id: Optional[UUID] = None,
        status: Optional[EntryStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[JournalEntry]:
        """
        Get journal entries with filters.

        Args:
            company_id: Company ID
            fiscal_period_id: Optional fiscal period filter
            status: Optional status filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum entries to return
            offset: Pagination offset

        Returns:
            List of journal entries
        """
        query = self.db.query(JournalEntry).filter(JournalEntry.company_id == company_id)

        if fiscal_period_id:
            query = query.filter(JournalEntry.fiscal_period_id == fiscal_period_id)

        if status:
            query = query.filter(JournalEntry.status == status)

        if start_date:
            query = query.filter(JournalEntry.entry_date >= start_date)

        if end_date:
            query = query.filter(JournalEntry.entry_date <= end_date)

        query = query.order_by(desc(JournalEntry.entry_date), desc(JournalEntry.entry_number))

        return query.limit(limit).offset(offset).all()

    def update_journal_entry(
        self,
        entry_id: UUID,
        update_data: JournalEntryUpdate
    ) -> JournalEntry:
        """
        Update a journal entry (only drafts can be updated).

        Args:
            entry_id: Journal entry ID
            update_data: Update data

        Returns:
            Updated journal entry

        Raises:
            ValueError: If entry cannot be updated
        """
        entry = self.get_journal_entry(entry_id)
        if not entry:
            raise ValueError("Journal entry not found")

        if not entry.can_be_edited():
            raise ValueError(f"Cannot update entry with status {entry.status}")

        # Update fields
        if update_data.entry_date:
            entry.entry_date = update_data.entry_date

        if update_data.description:
            entry.description = update_data.description

        if update_data.reference is not None:
            entry.reference = update_data.reference

        # Update lines if provided
        if update_data.lines:
            # Validate new lines
            total_debits = sum(line.debit_amount for line in update_data.lines)
            total_credits = sum(line.credit_amount for line in update_data.lines)

            if total_debits != total_credits:
                raise ValueError(f"Debits ({total_debits}) must equal credits ({total_credits})")

            # Delete existing lines
            self.db.query(JournalEntryLine).filter(
                JournalEntryLine.journal_entry_id == entry_id
            ).delete()

            # Create new lines
            for line_data in update_data.lines:
                line = JournalEntryLine(
                    journal_entry_id=entry.id,
                    company_account_id=line_data.company_account_id,
                    line_number=line_data.line_number,
                    description=line_data.description,
                    debit_amount=line_data.debit_amount,
                    credit_amount=line_data.credit_amount
                )
                self.db.add(line)

        self.db.commit()
        self.db.refresh(entry)

        return entry

    def post_journal_entry(self, entry_id: UUID, posted_by: UUID) -> JournalEntry:
        """
        Post a journal entry (make it permanent and update balances).

        Args:
            entry_id: Journal entry ID
            posted_by: User ID posting the entry

        Returns:
            Posted journal entry

        Raises:
            ValueError: If entry cannot be posted
        """
        entry = self.get_journal_entry(entry_id)
        if not entry:
            raise ValueError("Journal entry not found")

        if not entry.can_be_posted():
            raise ValueError(f"Cannot post entry with status {entry.status}")

        # Validate the entry is balanced
        if not self._validate_entry_balanced(entry):
            raise ValueError("Entry is not balanced")

        # Check fiscal period is still open
        fiscal_period = self.db.query(FiscalPeriod).filter(
            FiscalPeriod.id == entry.fiscal_period_id
        ).first()

        if not fiscal_period or not fiscal_period.is_open():
            raise ValueError("Fiscal period is not open")

        # Update entry status
        entry.status = EntryStatus.POSTED
        entry.posted_at = datetime.utcnow()
        entry.posted_by = posted_by

        self.db.commit()
        self.db.refresh(entry)

        # Note: Balance updates will be handled by ledger_service
        return entry

    def void_journal_entry(
        self,
        entry_id: UUID,
        voided_by: UUID,
        void_reason: str
    ) -> JournalEntry:
        """
        Void a journal entry (creates reversing entry).

        Args:
            entry_id: Journal entry ID
            voided_by: User ID voiding the entry
            void_reason: Reason for voiding

        Returns:
            Voided journal entry

        Raises:
            ValueError: If entry cannot be voided
        """
        entry = self.get_journal_entry(entry_id)
        if not entry:
            raise ValueError("Journal entry not found")

        if not entry.can_be_voided():
            raise ValueError(f"Cannot void entry with status {entry.status}")

        # Update entry status
        entry.status = EntryStatus.VOID
        entry.voided_at = datetime.utcnow()
        entry.voided_by = voided_by
        entry.void_reason = void_reason

        self.db.commit()
        self.db.refresh(entry)

        return entry

    def delete_journal_entry(self, entry_id: UUID) -> bool:
        """
        Delete a journal entry (only drafts can be deleted).

        Args:
            entry_id: Journal entry ID

        Returns:
            True if deleted

        Raises:
            ValueError: If entry cannot be deleted
        """
        entry = self.get_journal_entry(entry_id)
        if not entry:
            raise ValueError("Journal entry not found")

        if not entry.is_draft():
            raise ValueError("Only draft entries can be deleted")

        self.db.delete(entry)
        self.db.commit()

        return True

    def _generate_entry_number(self, company_id: UUID, entry_date: date) -> str:
        """
        Generate a unique entry number for the company.

        Format: JE-YYYY-NNNN (e.g., JE-2024-0001)

        Args:
            company_id: Company ID
            entry_date: Entry date

        Returns:
            Generated entry number
        """
        year = entry_date.year

        # Get the last entry number for this year
        last_entry = self.db.query(JournalEntry).filter(
            and_(
                JournalEntry.company_id == company_id,
                JournalEntry.entry_number.like(f"JE-{year}-%")
            )
        ).order_by(desc(JournalEntry.entry_number)).first()

        if last_entry:
            # Extract the sequence number and increment
            last_num = int(last_entry.entry_number.split("-")[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"JE-{year}-{next_num:04d}"

    def _validate_entry_balanced(self, entry: JournalEntry) -> bool:
        """
        Validate that a journal entry is balanced (debits = credits).

        Args:
            entry: Journal entry

        Returns:
            True if balanced
        """
        total_debits = sum(line.debit_amount for line in entry.lines)
        total_credits = sum(line.credit_amount for line in entry.lines)

        return total_debits == total_credits

    def get_entry_totals(self, entry: JournalEntry) -> tuple[Decimal, Decimal]:
        """
        Get total debits and credits for an entry.

        Args:
            entry: Journal entry

        Returns:
            Tuple of (total_debits, total_credits)
        """
        total_debits = sum(Decimal(str(line.debit_amount)) for line in entry.lines)
        total_credits = sum(Decimal(str(line.credit_amount)) for line in entry.lines)

        return total_debits, total_credits
