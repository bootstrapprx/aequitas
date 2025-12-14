"""
FiscalPeriodGuard - Enforce fiscal period constraints for journal entries.

CANONICAL COMPLIANCE:
- Phase 3B: Fiscal period constraint enforcement
- Journal entries may only be created/modified in OPEN periods
- CLOSED and LOCKED periods are strictly read-only
- Period boundaries must be respected by posting_date

FISCAL PERIOD RULES:
- OPEN: Allows journal entry creation and modification
- CLOSED: Read-only, no modifications allowed
- LOCKED: Permanently read-only, even superuser cannot modify

ENFORCEMENT POINTS:
- Journal entry creation: Must have posting_date in OPEN period
- Journal entry modification: Period must still be OPEN
- Posting date changes: New date must be in OPEN period
"""

from typing import Optional
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.exceptions import ValidationError, ErrorCode
from app.db.models.enums import PeriodStatus


class FiscalPeriodGuard:
    """
    Guard service for fiscal period constraint enforcement.

    CANONICAL COMPLIANCE:
    - Ensures journal entries only created/modified in OPEN periods
    - Validates posting_date is within period boundaries
    - Prevents modifications to CLOSED or LOCKED periods
    - Provides clear, actionable error messages
    """

    def __init__(self, db: Session):
        """
        Initialize guard with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_period_for_date(
        self,
        company_id: UUID,
        posting_date: date
    ) -> Optional[object]:
        """
        Get the fiscal period for a given posting date.

        Args:
            company_id: Company UUID
            posting_date: Date to find period for

        Returns:
            FiscalPeriod object if found, None otherwise
        """
        from app.db.models.fiscal_period import FiscalPeriod

        period = self.db.query(FiscalPeriod).filter(
            and_(
                FiscalPeriod.company_id == company_id,
                FiscalPeriod.start_date <= posting_date,
                FiscalPeriod.end_date >= posting_date
            )
        ).first()

        return period

    def validate_period_is_open(
        self,
        company_id: UUID,
        posting_date: date,
        operation: str = "create journal entry"
    ) -> None:
        """
        Validate that posting_date falls within an OPEN fiscal period.

        Args:
            company_id: Company UUID
            posting_date: Posting date to validate
            operation: Operation description for error message (default: "create journal entry")

        Raises:
            ValidationError: If period not found, closed, or locked
        """
        # Get period for date
        period = self.get_period_for_date(company_id, posting_date)

        if not period:
            raise ValidationError(
                message=(
                    f"No fiscal period found for posting date.\n"
                    f"Posting date: {posting_date}\n"
                    f"Company: {company_id}\n\n"
                    f"Create a fiscal period covering this date before posting transactions."
                ),
                code=ErrorCode.PERIOD_NOT_FOUND,
                details={
                    "company_id": str(company_id),
                    "posting_date": str(posting_date),
                    "operation": operation
                },
                field="posting_date"
            )

        # Check period status
        if period.status == PeriodStatus.CLOSED:
            raise ValidationError(
                message=(
                    f"Cannot {operation} in CLOSED fiscal period.\n"
                    f"Period: {period.period_name} ({period.start_date} to {period.end_date})\n"
                    f"Status: CLOSED\n"
                    f"Closed at: {period.closed_at}\n\n"
                    f"CLOSED periods are read-only. To make changes, reopen the period (requires superuser)."
                ),
                code=ErrorCode.PERIOD_CLOSED,
                details={
                    "company_id": str(company_id),
                    "posting_date": str(posting_date),
                    "period_id": str(period.id),
                    "period_name": period.period_name,
                    "period_status": period.status.value,
                    "operation": operation
                },
                field="posting_date"
            )

        if period.status == PeriodStatus.LOCKED:
            raise ValidationError(
                message=(
                    f"Cannot {operation} in LOCKED fiscal period.\n"
                    f"Period: {period.period_name} ({period.start_date} to {period.end_date})\n"
                    f"Status: LOCKED\n"
                    f"Locked at: {period.locked_at}\n\n"
                    f"LOCKED periods are permanently read-only and cannot be reopened."
                ),
                code=ErrorCode.PERIOD_LOCKED,
                details={
                    "company_id": str(company_id),
                    "posting_date": str(posting_date),
                    "period_id": str(period.id),
                    "period_name": period.period_name,
                    "period_status": period.status.value,
                    "operation": operation
                },
                field="posting_date"
            )

        # Verify period is OPEN
        if period.status != PeriodStatus.OPEN:
            raise ValidationError(
                message=(
                    f"Cannot {operation}: fiscal period is not OPEN.\n"
                    f"Period: {period.period_name} ({period.start_date} to {period.end_date})\n"
                    f"Status: {period.status.value}\n\n"
                    f"Only OPEN periods allow journal entry modifications."
                ),
                code=ErrorCode.PERIOD_NOT_OPEN,
                details={
                    "company_id": str(company_id),
                    "posting_date": str(posting_date),
                    "period_id": str(period.id),
                    "period_name": period.period_name,
                    "period_status": period.status.value,
                    "operation": operation
                },
                field="posting_date"
            )

    def validate_journal_entry_creation(
        self,
        company_id: UUID,
        posting_date: date
    ) -> None:
        """
        Validate that journal entry can be created for given posting date.

        Args:
            company_id: Company UUID
            posting_date: Posting date for journal entry

        Raises:
            ValidationError: If period not OPEN
        """
        self.validate_period_is_open(
            company_id,
            posting_date,
            operation="create journal entry"
        )

    def validate_journal_entry_modification(
        self,
        journal_entry_id: UUID,
        new_posting_date: Optional[date] = None
    ) -> None:
        """
        Validate that journal entry can be modified.

        Args:
            journal_entry_id: Journal entry UUID
            new_posting_date: New posting date (if changing), None if not changing

        Raises:
            ValidationError: If period not OPEN (for current or new posting date)
        """
        from app.db.models.journal_entry import JournalEntry

        # Get journal entry
        entry = self.db.query(JournalEntry).filter(
            JournalEntry.id == journal_entry_id
        ).first()

        if not entry:
            raise ValidationError(
                message=f"Journal entry {journal_entry_id} not found",
                code=ErrorCode.PERMISSION_DENIED
            )

        # Validate current period is OPEN
        self.validate_period_is_open(
            entry.company_id,
            entry.posting_date,
            operation="modify journal entry"
        )

        # If changing posting date, validate new period is also OPEN
        if new_posting_date and new_posting_date != entry.posting_date:
            self.validate_period_is_open(
                entry.company_id,
                new_posting_date,
                operation="change posting date to"
            )

    def validate_posting_date_within_bounds(
        self,
        company_id: UUID,
        posting_date: date
    ) -> None:
        """
        Validate posting date falls within period boundaries.

        This is a softer check that only validates the date falls within
        a period, without checking if the period is OPEN.

        Args:
            company_id: Company UUID
            posting_date: Posting date to validate

        Raises:
            ValidationError: If no period found for posting date
        """
        period = self.get_period_for_date(company_id, posting_date)

        if not period:
            raise ValidationError(
                message=(
                    f"Posting date is outside all fiscal period boundaries.\n"
                    f"Posting date: {posting_date}\n"
                    f"Company: {company_id}\n\n"
                    f"Ensure posting date falls within a defined fiscal period."
                ),
                code=ErrorCode.PERIOD_DATE_OUTSIDE,
                details={
                    "company_id": str(company_id),
                    "posting_date": str(posting_date)
                },
                field="posting_date"
            )


# Export
__all__ = ["FiscalPeriodGuard"]
