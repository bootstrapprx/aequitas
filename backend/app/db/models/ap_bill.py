import uuid
import enum
from decimal import Decimal
from sqlalchemy import Column, String, Date, Numeric, Enum as SQLEnum, ForeignKey, Text, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class APBillStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    VOIDED = "VOIDED"


class APBill(Base):
    """
    SQLAlchemy model for Accounts Payable Vendor Bills.
    """
    __tablename__ = "ap_bills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("parties.id"), nullable=False, index=True)
    fiscal_period_id = Column(UUID(as_uuid=True), ForeignKey("fiscal_periods.id"), nullable=False, index=True)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=True, index=True)

    bill_number = Column(String, nullable=False, index=True)
    bill_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)

    status = Column(SQLEnum(APBillStatus, name="apbillstatus"), default=APBillStatus.DRAFT, nullable=False)
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    amount_paid = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    amount_due = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    vendor = relationship("Party")
    fiscal_period = relationship("FiscalPeriod")
    journal_entry = relationship("JournalEntry")
    lines = relationship("APBillLine", back_populates="bill", cascade="all, delete-orphan")
    payments = relationship("APPayment", back_populates="bill")


class APBillLine(Base):
    """
    SQLAlchemy model for vendor bill line items.
    """
    __tablename__ = "ap_bill_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("ap_bills.id", ondelete="CASCADE"), nullable=False, index=True)
    expense_account_id = Column(UUID(as_uuid=True), ForeignKey("company_accounts.id"), nullable=False)

    line_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)

    bill = relationship("APBill", back_populates="lines")
    expense_account = relationship("CompanyAccount")


class APPayment(Base):
    """
    SQLAlchemy model for payments made against vendor bills.
    """
    __tablename__ = "ap_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("ap_bills.id"), nullable=False, index=True)
    cash_account_id = Column(UUID(as_uuid=True), ForeignKey("company_accounts.id"), nullable=False)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=True)

    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    bill = relationship("APBill", back_populates="payments")
    cash_account = relationship("CompanyAccount")
    journal_entry = relationship("JournalEntry")
