import uuid
from sqlalchemy import Column, String, DateTime, Date, func, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum


class PeriodStatus(str, enum.Enum):
    """Status of a fiscal period"""
    OPEN = "open"
    CLOSED = "closed"
    LOCKED = "locked"


class PeriodType(str, enum.Enum):
    """Type of fiscal period"""
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class FiscalPeriod(Base):
    """
    SQLAlchemy model for fiscal periods.
    Manages accounting periods for companies, enabling period-based financial reporting
    and period locking to prevent unauthorized changes to historical data.
    """
    __tablename__ = "fiscal_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)

    period_type = Column(SQLEnum(PeriodType), nullable=False, default=PeriodType.MONTH)
    period_number = Column(String, nullable=False)  # "2024-01", "2024-Q1", "2024"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(SQLEnum(PeriodStatus), nullable=False, default=PeriodStatus.OPEN)

    closed_at = Column(DateTime, nullable=True)
    closed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    company = relationship("Company", back_populates="fiscal_periods")
    journal_entries = relationship("JournalEntry", back_populates="fiscal_period")
    account_balances = relationship("AccountBalance", back_populates="fiscal_period")

    def __repr__(self):
        return f"<FiscalPeriod(company_id='{self.company_id}', period='{self.period_number}', status='{self.status}')>"

    def is_open(self) -> bool:
        """Check if the period is open for posting"""
        return self.status == PeriodStatus.OPEN

    def is_locked(self) -> bool:
        """Check if the period is locked (prevents any changes)"""
        return self.status == PeriodStatus.LOCKED
