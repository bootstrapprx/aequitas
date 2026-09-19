import uuid
import enum
from decimal import Decimal
from sqlalchemy import Column, String, Date, Numeric, Enum as SQLEnum, ForeignKey, Text, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class StatementLineStatus(str, enum.Enum):
    UNMATCHED = "UNMATCHED"
    MATCHED = "MATCHED"
    RECONCILED = "RECONCILED"


class BankStatement(Base):
    """
    SQLAlchemy model for imported bank statements.
    """
    __tablename__ = "bank_statements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    cash_account_id = Column(UUID(as_uuid=True), ForeignKey("company_accounts.id"), nullable=False, index=True)

    statement_date = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    lines = relationship("BankStatementLine", back_populates="statement", cascade="all, delete-orphan")
    cash_account = relationship("CompanyAccount")


class BankStatementLine(Base):
    """
    SQLAlchemy model for individual bank statement line items.
    """
    __tablename__ = "bank_statement_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    statement_id = Column(UUID(as_uuid=True), ForeignKey("bank_statements.id", ondelete="CASCADE"), nullable=False, index=True)
    matched_journal_entry_line_id = Column(UUID(as_uuid=True), ForeignKey("journal_entry_lines.id"), nullable=True, index=True)

    line_number = Column(Integer, nullable=False)
    transaction_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    reference = Column(String, nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    status = Column(SQLEnum(StatementLineStatus, name="statementlinestatus"), default=StatementLineStatus.UNMATCHED, nullable=False)

    statement = relationship("BankStatement", back_populates="lines")
    matched_journal_entry_line = relationship("JournalEntryLine")
