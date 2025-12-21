import uuid
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, func, ForeignKey, Text, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class JournalEntryLine(Base):
    """
    SQLAlchemy model for journal entry lines.
    Represents individual debit or credit lines within a journal entry.
    Each line posts to a specific account in the company's chart of accounts.
    """
    __tablename__ = "journal_entry_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=False, index=True)
    company_account_id = Column(UUID(as_uuid=True), ForeignKey("company_accounts.id"), nullable=False, index=True)

    line_number = Column(Integer, nullable=False)  # Order within the entry (1, 2, 3...)
    description = Column(Text, nullable=True)  # Line-level description (optional)

    # Amounts (precision 15, scale 2 supports up to 999 trillion with 2 decimal places)
    debit_amount = Column(Numeric(15, 2), nullable=False, default=0)
    credit_amount = Column(Numeric(15, 2), nullable=False, default=0)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    journal_entry = relationship("JournalEntry", back_populates="lines")
    company_account = relationship("CompanyAccount", back_populates="journal_entry_lines")

    def __repr__(self):
        return f"<JournalEntryLine(entry_id='{self.journal_entry_id}', account='{self.company_account_id}', debit={self.debit_amount}, credit={self.credit_amount})>"

    def get_amount(self) -> Decimal:
        """Get the non-zero amount (either debit or credit)"""
        return Decimal(str(self.debit_amount)) if self.debit_amount > 0 else Decimal(str(self.credit_amount))

    def is_debit(self) -> bool:
        """Check if this is a debit line"""
        return self.debit_amount > 0

    def is_credit(self) -> bool:
        """Check if this is a credit line"""
        return self.credit_amount > 0

    def validate(self) -> tuple[bool, str]:
        """
        Validate the line:
        - Must have either debit OR credit (not both, not neither)
        - Amount must be positive
        """
        if self.debit_amount > 0 and self.credit_amount > 0:
            return False, "Line cannot have both debit and credit amounts"

        if self.debit_amount <= 0 and self.credit_amount <= 0:
            return False, "Line must have either a debit or credit amount"

        if self.debit_amount < 0 or self.credit_amount < 0:
            return False, "Amounts cannot be negative"

        return True, "Valid"
