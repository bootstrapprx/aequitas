import uuid
import enum
from decimal import Decimal
from sqlalchemy import Column, String, Date, Numeric, Enum as SQLEnum, ForeignKey, Text, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ARInvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    VOIDED = "VOIDED"


class ARInvoice(Base):
    """
    SQLAlchemy model for Accounts Receivable Customer Invoices.
    """
    __tablename__ = "ar_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("parties.id"), nullable=False, index=True)
    fiscal_period_id = Column(UUID(as_uuid=True), ForeignKey("fiscal_periods.id"), nullable=False, index=True)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=True, index=True)

    invoice_number = Column(String, nullable=False, index=True)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)

    status = Column(SQLEnum(ARInvoiceStatus, name="arinvoicestatus"), default=ARInvoiceStatus.DRAFT, nullable=False)
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    amount_paid = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    amount_due = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    customer = relationship("Party")
    fiscal_period = relationship("FiscalPeriod")
    journal_entry = relationship("JournalEntry")
    lines = relationship("ARInvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("ARPayment", back_populates="invoice")


class ARInvoiceLine(Base):
    """
    SQLAlchemy model for invoice line items.
    """
    __tablename__ = "ar_invoice_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("ar_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    revenue_account_id = Column(UUID(as_uuid=True), ForeignKey("company_accounts.id"), nullable=False)

    line_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)

    invoice = relationship("ARInvoice", back_populates="lines")
    revenue_account = relationship("CompanyAccount")


class ARPayment(Base):
    """
    SQLAlchemy model for customer payments applied against an invoice.
    """
    __tablename__ = "ar_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("ar_invoices.id"), nullable=False, index=True)
    cash_account_id = Column(UUID(as_uuid=True), ForeignKey("company_accounts.id"), nullable=False)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=True)

    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    invoice = relationship("ARInvoice", back_populates="payments")
    cash_account = relationship("CompanyAccount")
    journal_entry = relationship("JournalEntry")
