from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from app.db.models.fiscal_period import FiscalPeriod, PeriodStatus, PeriodType
from app.db.models.journal_entry import JournalEntry, EntryStatus
from app.schemas.fiscal_period import FiscalPeriodCreate, FiscalPeriodUpdate


class FiscalPeriodService:
    """Service for managing fiscal periods"""

    def __init__(self, db: Session):
        self.db = db

    def create_fiscal_period(self, period_data: FiscalPeriodCreate) -> FiscalPeriod:
        """
        Create a new fiscal period.

        Args:
            period_data: Fiscal period creation data

        Returns:
            Created fiscal period

        Raises:
            ValueError: If validation fails
        """
        # Check for overlapping periods
        overlapping = self.db.query(FiscalPeriod).filter(
            and_(
                FiscalPeriod.company_id == period_data.company_id,
                FiscalPeriod.period_type == PeriodType(period_data.period_type),
                or_(
                    and_(
                        FiscalPeriod.start_date <= period_data.start_date,
                        FiscalPeriod.end_date >= period_data.start_date
                    ),
                    and_(
                        FiscalPeriod.start_date <= period_data.end_date,
                        FiscalPeriod.end_date >= period_data.end_date
                    )
                )
            )
        ).first()

        if overlapping:
            raise ValueError(
                f"Period overlaps with existing period {overlapping.period_number}"
            )

        # Create period
        fiscal_period = FiscalPeriod(
            company_id=period_data.company_id,
            period_type=PeriodType(period_data.period_type),
            period_number=period_data.period_number,
            start_date=period_data.start_date,
            end_date=period_data.end_date,
            status=PeriodStatus(period_data.status)
        )

        self.db.add(fiscal_period)
        self.db.commit()
        self.db.refresh(fiscal_period)

        return fiscal_period

    def get_fiscal_period(self, period_id: UUID) -> Optional[FiscalPeriod]:
        """Get a fiscal period by ID"""
        return self.db.query(FiscalPeriod).filter(FiscalPeriod.id == period_id).first()

    def get_fiscal_periods(
        self,
        company_id: UUID,
        period_type: Optional[PeriodType] = None,
        status: Optional[PeriodStatus] = None,
        year: Optional[int] = None
    ) -> List[FiscalPeriod]:
        """
        Get fiscal periods with filters.

        Args:
            company_id: Company ID
            period_type: Optional period type filter
            status: Optional status filter
            year: Optional year filter

        Returns:
            List of fiscal periods
        """
        query = self.db.query(FiscalPeriod).filter(FiscalPeriod.company_id == company_id)

        if period_type:
            query = query.filter(FiscalPeriod.period_type == period_type)

        if status:
            query = query.filter(FiscalPeriod.status == status)

        if year:
            query = query.filter(
                and_(
                    FiscalPeriod.start_date >= date(year, 1, 1),
                    FiscalPeriod.start_date <= date(year, 12, 31)
                )
            )

        return query.order_by(FiscalPeriod.start_date).all()

    def get_period_for_date(
        self,
        company_id: UUID,
        target_date: date,
        period_type: PeriodType = PeriodType.MONTH
    ) -> Optional[FiscalPeriod]:
        """
        Get the fiscal period for a specific date.

        Args:
            company_id: Company ID
            target_date: Date to find period for
            period_type: Type of period to find

        Returns:
            Fiscal period or None
        """
        return self.db.query(FiscalPeriod).filter(
            and_(
                FiscalPeriod.company_id == company_id,
                FiscalPeriod.period_type == period_type,
                FiscalPeriod.start_date <= target_date,
                FiscalPeriod.end_date >= target_date
            )
        ).first()

    def close_fiscal_period(self, period_id: UUID, closed_by: UUID) -> FiscalPeriod:
        """
        Close a fiscal period.

        Args:
            period_id: Fiscal period ID
            closed_by: User ID closing the period

        Returns:
            Closed fiscal period

        Raises:
            ValueError: If period cannot be closed
        """
        period = self.get_fiscal_period(period_id)
        if not period:
            raise ValueError("Fiscal period not found")

        if period.status != PeriodStatus.OPEN:
            raise ValueError(f"Period is already {period.status}")

        # Check if all journal entries are posted (no drafts)
        draft_entries = self.db.query(JournalEntry).filter(
            and_(
                JournalEntry.fiscal_period_id == period_id,
                JournalEntry.status == EntryStatus.DRAFT
            )
        ).count()

        if draft_entries > 0:
            raise ValueError(
                f"Cannot close period with {draft_entries} draft journal entries"
            )

        # Close the period
        period.status = PeriodStatus.CLOSED
        period.closed_at = datetime.utcnow()
        period.closed_by = closed_by

        self.db.commit()
        self.db.refresh(period)

        return period

    def reopen_fiscal_period(self, period_id: UUID) -> FiscalPeriod:
        """
        Reopen a closed fiscal period.

        Args:
            period_id: Fiscal period ID

        Returns:
            Reopened fiscal period

        Raises:
            ValueError: If period cannot be reopened
        """
        period = self.get_fiscal_period(period_id)
        if not period:
            raise ValueError("Fiscal period not found")

        if period.status == PeriodStatus.LOCKED:
            raise ValueError("Cannot reopen a locked period")

        if period.status == PeriodStatus.OPEN:
            raise ValueError("Period is already open")

        # Reopen the period
        period.status = PeriodStatus.OPEN
        period.closed_at = None
        period.closed_by = None

        self.db.commit()
        self.db.refresh(period)

        return period

    def lock_fiscal_period(self, period_id: UUID) -> FiscalPeriod:
        """
        Lock a fiscal period (prevents any changes, including reopening).

        Args:
            period_id: Fiscal period ID

        Returns:
            Locked fiscal period

        Raises:
            ValueError: If period cannot be locked
        """
        period = self.get_fiscal_period(period_id)
        if not period:
            raise ValueError("Fiscal period not found")

        if period.status != PeriodStatus.CLOSED:
            raise ValueError("Can only lock closed periods")

        period.status = PeriodStatus.LOCKED

        self.db.commit()
        self.db.refresh(period)

        return period

    def create_monthly_periods(self, company_id: UUID, year: int) -> List[FiscalPeriod]:
        """
        Create all 12 monthly periods for a year.

        Args:
            company_id: Company ID
            year: Year to create periods for

        Returns:
            List of created fiscal periods
        """
        periods = []

        for month in range(1, 13):
            start_date = date(year, month, 1)
            end_date = start_date + relativedelta(months=1, days=-1)

            period_number = f"{year}-{month:02d}"

            # Check if period already exists
            existing = self.db.query(FiscalPeriod).filter(
                and_(
                    FiscalPeriod.company_id == company_id,
                    FiscalPeriod.period_number == period_number
                )
            ).first()

            if not existing:
                period = FiscalPeriod(
                    company_id=company_id,
                    period_type=PeriodType.MONTH,
                    period_number=period_number,
                    start_date=start_date,
                    end_date=end_date,
                    status=PeriodStatus.OPEN
                )
                self.db.add(period)
                periods.append(period)

        if periods:
            self.db.commit()
            for period in periods:
                self.db.refresh(period)

        return periods

    def create_quarterly_periods(self, company_id: UUID, year: int) -> List[FiscalPeriod]:
        """
        Create all 4 quarterly periods for a year.

        Args:
            company_id: Company ID
            year: Year to create periods for

        Returns:
            List of created fiscal periods
        """
        periods = []
        quarters = [
            (1, 1, 3, 31),   # Q1: Jan 1 - Mar 31
            (2, 4, 6, 30),   # Q2: Apr 1 - Jun 30
            (3, 7, 9, 30),   # Q3: Jul 1 - Sep 30
            (4, 10, 12, 31)  # Q4: Oct 1 - Dec 31
        ]

        for quarter_num, start_month, end_month, end_day in quarters:
            start_date = date(year, start_month, 1)
            end_date = date(year, end_month, end_day)

            period_number = f"{year}-Q{quarter_num}"

            # Check if period already exists
            existing = self.db.query(FiscalPeriod).filter(
                and_(
                    FiscalPeriod.company_id == company_id,
                    FiscalPeriod.period_number == period_number
                )
            ).first()

            if not existing:
                period = FiscalPeriod(
                    company_id=company_id,
                    period_type=PeriodType.QUARTER,
                    period_number=period_number,
                    start_date=start_date,
                    end_date=end_date,
                    status=PeriodStatus.OPEN
                )
                self.db.add(period)
                periods.append(period)

        if periods:
            self.db.commit()
            for period in periods:
                self.db.refresh(period)

        return periods

    def create_yearly_period(self, company_id: UUID, year: int) -> FiscalPeriod:
        """
        Create a yearly period.

        Args:
            company_id: Company ID
            year: Year to create period for

        Returns:
            Created fiscal period
        """
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        period_number = str(year)

        # Check if period already exists
        existing = self.db.query(FiscalPeriod).filter(
            and_(
                FiscalPeriod.company_id == company_id,
                FiscalPeriod.period_number == period_number
            )
        ).first()

        if existing:
            return existing

        period = FiscalPeriod(
            company_id=company_id,
            period_type=PeriodType.YEAR,
            period_number=period_number,
            start_date=start_date,
            end_date=end_date,
            status=PeriodStatus.OPEN
        )

        self.db.add(period)
        self.db.commit()
        self.db.refresh(period)

        return period
