import uuid
from decimal import Decimal
from sqlalchemy import Column, DateTime, func, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class AccountBalance(Base):
    """
    SQLAlchemy model for account balances by period.
    Stores running balances for each account in each fiscal period.
    This enables fast balance lookups without recalculating from journal entries.

    Balance calculation:
    ending_balance = beginning_balance + total_debits - total_credits (for debit accounts)
    ending_balance = beginning_balance - total_debits + total_credits (for credit accounts)
    """
    __tablename__ = "account_balances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    company_account_id = Column(UUID(as_uuid=True), ForeignKey("company_accounts.id"), nullable=False, index=True)
    fiscal_period_id = Column(UUID(as_uuid=True), ForeignKey("fiscal_periods.id"), nullable=False, index=True)

    # Balance amounts (precision 15, scale 2)
    beginning_balance = Column(Numeric(15, 2), nullable=False, default=0)
    total_debits = Column(Numeric(15, 2), nullable=False, default=0)
    total_credits = Column(Numeric(15, 2), nullable=False, default=0)
    ending_balance = Column(Numeric(15, 2), nullable=False, default=0)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    company = relationship("Company")
    company_account = relationship("CompanyAccount")
    fiscal_period = relationship("FiscalPeriod", back_populates="account_balances")

    # Unique constraint: one balance record per account per period
    __table_args__ = (
        UniqueConstraint('company_account_id', 'fiscal_period_id', name='uq_account_period'),
    )

    def __repr__(self):
        return f"<AccountBalance(account_id='{self.company_account_id}', period='{self.fiscal_period_id}', balance={self.ending_balance})>"

    def calculate_ending_balance(self, normal_balance: str) -> Decimal:
        """
        Calculate ending balance based on account's normal balance type.

        Args:
            normal_balance: "Debit" or "Credit"

        Returns:
            Calculated ending balance
        """
        beginning = Decimal(str(self.beginning_balance))
        debits = Decimal(str(self.total_debits))
        credits = Decimal(str(self.total_credits))

        if normal_balance == "Debit":
            # Asset, Expense, COGS: increase with debits, decrease with credits
            return beginning + debits - credits
        else:
            # Liability, Equity, Revenue: increase with credits, decrease with debits
            return beginning - debits + credits

    def update_balance(self, debit_amount: Decimal, credit_amount: Decimal, normal_balance: str):
        """
        Update the balance with new transaction amounts.

        Args:
            debit_amount: Amount to add to total debits
            credit_amount: Amount to add to total credits
            normal_balance: "Debit" or "Credit"
        """
        self.total_debits = Decimal(str(self.total_debits)) + debit_amount
        self.total_credits = Decimal(str(self.total_credits)) + credit_amount
        self.ending_balance = self.calculate_ending_balance(normal_balance)
