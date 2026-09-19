"""
JournalEntryService - Service layer for managing journal entries.

CANONICAL COMPLIANCE - Phase 3B:
- Enforces accounting invariants (debits = credits)
- Validates against inactive accounts
- Validates against locked accounts
- Ensures all accounts belong to same company
- Enforces fiscal period constraints (OPEN only)
- Separates validation from persistence
- Returns structured validation errors (not generic exceptions)
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Tuple
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
from app.core.exceptions import ValidationError, ErrorCode, MultipleValidationErrors
from app.services.validators.fiscal_period_guard import FiscalPeriodGuard


class JournalEntryService:
    """
    Service for managing journal entries with GAAP-compliant invariant enforcement.

    CANONICAL COMPLIANCE:
    - Mandatory invariants enforced before persistence
    - Transactional integrity (reject partial writes)
    - Structured validation errors with error codes
    - Fiscal period guard integration
    """

    def __init__(self, db: Session):
        self.db = db
        self.period_guard = FiscalPeriodGuard(db)

    # ========================================================================
    # VALIDATION METHODS (Unit-testable, no DB writes)
    # ========================================================================

    def validate_journal_entry_balance(
        self,
        lines: List
    ) -> None:
        """
        Validate that journal entry is balanced (debits = credits).

        MANDATORY INVARIANT: Sum(debits) == Sum(credits)

        Args:
            lines: List of journal entry line data

        Raises:
            ValidationError: If debits do not equal credits
        """
        if not lines or len(lines) < 2:
            raise ValidationError(
                message="Journal entry must have at least 2 lines",
                code=ErrorCode.JOURNAL_EMPTY_LINES,
                details={"line_count": len(lines) if lines else 0}
            )

        total_debits = sum(Decimal(str(line.debit_amount)) for line in lines)
        total_credits = sum(Decimal(str(line.credit_amount)) for line in lines)

        if total_debits != total_credits:
            raise ValidationError(
                message=(
                    f"Journal entry is not balanced.\n"
                    f"Total debits: {total_debits}\n"
                    f"Total credits: {total_credits}\n"
                    f"Difference: {abs(total_debits - total_credits)}\n\n"
                    f"Debits must equal credits in double-entry bookkeeping."
                ),
                code=ErrorCode.JOURNAL_IMBALANCE,
                details={
                    "total_debits": str(total_debits),
                    "total_credits": str(total_credits),
                    "difference": str(abs(total_debits - total_credits))
                }
            )

    def validate_journal_entry_accounts(
        self,
        company_id: UUID,
        lines: List
    ) -> List[CompanyAccount]:
        """
        Validate all accounts in journal entry lines.

        MANDATORY INVARIANTS:
        - All accounts must exist
        - All accounts must belong to the same company
        - No account may be inactive
        - No account may be locked

        Args:
            company_id: Company UUID
            lines: List of journal entry line data

        Returns:
            List of validated CompanyAccount objects

        Raises:
            ValidationError: If any account validation fails
        """
        account_ids = [line.company_account_id for line in lines]

        # Get unique account IDs
        unique_account_ids = list(set(account_ids))
        
        # Get all accounts
        accounts = self.db.query(CompanyAccount).filter(
            CompanyAccount.id.in_(unique_account_ids)
        ).all()

        # Check all accounts exist
        if len(accounts) != len(unique_account_ids):
            found_ids = {acc.id for acc in accounts}
            missing_ids = [aid for aid in unique_account_ids if aid not in found_ids]
            raise ValidationError(
                message=(
                    f"One or more accounts not found.\n"
                    f"Missing account IDs: {', '.join(str(mid) for mid in missing_ids)}"
                ),
                code=ErrorCode.JOURNAL_INACTIVE_ACCOUNT,
                details={"missing_account_ids": [str(mid) for mid in missing_ids]}
            )

        # Validate all accounts belong to same company
        errors = []
        for acc in accounts:
            if acc.company_id != company_id:
                errors.append(ValidationError(
                    message=f"Account {acc.code} belongs to different company",
                    code=ErrorCode.JOURNAL_CROSS_COMPANY,
                    details={
                        "account_id": str(acc.id),
                        "account_code": acc.code,
                        "account_company_id": str(acc.company_id),
                        "journal_company_id": str(company_id)
                    },
                    field="company_account_id"
                ))

            # Check account is active
            if not acc.is_active:
                errors.append(ValidationError(
                    message=f"Account {acc.code} ({acc.description}) is inactive and cannot be used in journal entries",
                    code=ErrorCode.JOURNAL_INACTIVE_ACCOUNT,
                    details={
                        "account_id": str(acc.id),
                        "account_code": acc.code
                    },
                    field="company_account_id"
                ))

            # Check account is not locked
            if acc.is_locked:
                errors.append(ValidationError(
                    message=(
                        f"Account {acc.code} ({acc.description}) is locked and cannot be used in new journal entries.\n"
                        f"Locked reason: {acc.locked_reason.value if acc.locked_reason else 'Unknown'}\n"
                        f"Locked at: {acc.locked_at}"
                    ),
                    code=ErrorCode.JOURNAL_LOCKED_ACCOUNT,
                    details={
                        "account_id": str(acc.id),
                        "account_code": acc.code,
                        "locked_reason": acc.locked_reason.value if acc.locked_reason else None,
                        "locked_at": str(acc.locked_at) if acc.locked_at else None
                    },
                    field="company_account_id"
                ))

        if errors:
            raise MultipleValidationErrors(errors)

        return accounts

    def validate_journal_entry_amounts(
        self,
        lines: List
    ) -> None:
        """
        Validate that all journal entry line amounts are positive.

        Args:
            lines: List of journal entry line data

        Raises:
            ValidationError: If any amount is negative or zero
        """
        for idx, line in enumerate(lines):
            if line.debit_amount < 0 or line.credit_amount < 0:
                raise ValidationError(
                    message=f"Line {idx + 1}: Amounts cannot be negative",
                    code=ErrorCode.JOURNAL_INVALID_AMOUNT,
                    details={
                        "line_number": idx + 1,
                        "debit_amount": str(line.debit_amount),
                        "credit_amount": str(line.credit_amount)
                    },
                    field="amount"
                )

            # At least one amount must be non-zero
            if line.debit_amount == 0 and line.credit_amount == 0:
                raise ValidationError(
                    message=f"Line {idx + 1}: At least one amount (debit or credit) must be non-zero",
                    code=ErrorCode.JOURNAL_INVALID_AMOUNT,
                    details={
                        "line_number": idx + 1
                    },
                    field="amount"
                )

    # ========================================================================
    # CRUD OPERATIONS (with validation separation)
    # ========================================================================

    def create_journal_entry(
        self,
        entry_data: JournalEntryCreate,
        created_by: UUID
    ) -> JournalEntry:
        """
        Create a new journal entry with GAAP-compliant validation.

        CANONICAL COMPLIANCE - Phase 3B:
        - Validates before persistence (no partial writes)
        - Enforces all mandatory invariants
        - Returns structured validation errors
        - Fiscal period must be OPEN

        Args:
            entry_data: Journal entry creation data
            created_by: User ID creating the entry

        Returns:
            Created journal entry

        Raises:
            ValidationError: If any validation fails
        """
        # ========================================================================
        # VALIDATION SECTION (no DB writes)
        # ========================================================================

        # 1. Validate fiscal period is OPEN
        self.period_guard.validate_journal_entry_creation(
            entry_data.company_id,
            entry_data.entry_date
        )

        # 2. Validate journal entry balance (debits = credits)
        self.validate_journal_entry_balance(entry_data.lines)

        # 3. Validate amounts are positive
        self.validate_journal_entry_amounts(entry_data.lines)

        # 4. Validate all accounts (exist, active, not locked, same company)
        self.validate_journal_entry_accounts(entry_data.company_id, entry_data.lines)

        # ========================================================================
        # PERSISTENCE SECTION (after all validation passes)
        # ========================================================================

        # Get fiscal period for assignment
        fiscal_period = self.period_guard.get_period_for_date(
            entry_data.company_id,
            entry_data.entry_date
        )

        # Generate entry number
        entry_number = self._generate_entry_number(entry_data.company_id, entry_data.entry_date)

        # Create journal entry
        journal_entry = JournalEntry(
            company_id=entry_data.company_id,
            fiscal_period_id=fiscal_period.id,
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
                credit_amount=line_data.credit_amount,
                department_id=getattr(line_data, "department_id", None),
                cost_center_id=getattr(line_data, "cost_center_id", None),
                project_id=getattr(line_data, "project_id", None),
                location_id=getattr(line_data, "location_id", None),
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

        # Handle auto-reversal if configured
        if getattr(entry, "auto_reverse", False) and getattr(entry, "reversal_date", None) and entry.reversed_by_entry_id is None:
            reversal_period = self.db.query(FiscalPeriod).filter(
                FiscalPeriod.company_id == entry.company_id,
                FiscalPeriod.start_date <= entry.reversal_date,
                FiscalPeriod.end_date >= entry.reversal_date,
                FiscalPeriod.status == PeriodStatus.OPEN,
            ).first()

            if reversal_period:
                import uuid as _uuid
                reversal_entry = JournalEntry(
                    id=_uuid.uuid4(),
                    company_id=entry.company_id,
                    fiscal_period_id=reversal_period.id,
                    entry_number=f"{entry.entry_number}-REV",
                    entry_date=entry.reversal_date,
                    description=f"Auto-reversal of {entry.entry_number}: {entry.description}",
                    reference=entry.reference,
                    entry_type=EntryType.REVERSING,
                    status=EntryStatus.POSTED,
                    created_by=posted_by,
                    posted_by=posted_by,
                    posted_at=datetime.utcnow(),
                    reverses_entry_id=entry.id,
                )
                self.db.add(reversal_entry)
                self.db.flush()

                for line in entry.lines:
                    rev_line = JournalEntryLine(
                        id=_uuid.uuid4(),
                        journal_entry_id=reversal_entry.id,
                        company_account_id=line.company_account_id,
                        line_number=line.line_number,
                        description=line.description,
                        debit_amount=line.credit_amount,
                        credit_amount=line.debit_amount,
                    )
                    self.db.add(rev_line)

                entry.reversed_by_entry_id = reversal_entry.id

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
