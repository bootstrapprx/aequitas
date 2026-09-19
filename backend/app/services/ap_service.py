import uuid
from decimal import Decimal
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.db.models.ap_bill import APBill, APBillLine, APBillStatus, APPayment
from app.db.models.company_account import CompanyAccount
from app.db.models.master_account import MasterAccount
from app.db.models.journal_entry import JournalEntry, EntryStatus, EntryType
from app.db.models.journal_entry_line import JournalEntryLine
from app.db.models.enums import AccountType


class APService:
    """Service for Accounts Payable operations."""

    def __init__(self, db: Session):
        self.db = db

    def _get_ap_control_account(self, company_id: UUID) -> CompanyAccount:
        """Find the Accounts Payable control account."""
        acc = self.db.query(CompanyAccount).join(
            MasterAccount, CompanyAccount.mapped_master_account_id == MasterAccount.id, isouter=True
        ).filter(
            CompanyAccount.company_id == company_id,
            CompanyAccount.is_active.is_(True),
            (MasterAccount.code == "20000") | (CompanyAccount.code == "20000") | (CompanyAccount.description.ilike("%payable%"))
        ).first()

        if not acc:
            acc = self.db.query(CompanyAccount).filter(
                CompanyAccount.company_id == company_id,
                CompanyAccount.account_type == AccountType.LIABILITY,
                CompanyAccount.is_active.is_(True),
            ).first()

        if not acc:
            raise ValueError("No Accounts Payable or Liability account found.")
        return acc

    def create_bill(
        self,
        company_id: UUID,
        vendor_id: UUID,
        fiscal_period_id: UUID,
        bill_date: date,
        due_date: date,
        user_id: UUID,
        lines: List[Dict[str, Any]],
        bill_number: Optional[str] = None,
    ) -> APBill:
        """Create and post a vendor bill and corresponding GL entry."""
        if not lines:
            raise ValueError("Bill must have at least one line.")

        total_amount = sum(Decimal(str(l["amount"])) for l in lines)
        if not bill_number:
            bill_number = f"BILL-{int(datetime.utcnow().timestamp())}"

        ap_account = self._get_ap_control_account(company_id)

        # 1. Create Journal Entry (Debit Expense/Asset, Credit AP)
        je = JournalEntry(
            id=uuid.uuid4(),
            company_id=company_id,
            fiscal_period_id=fiscal_period_id,
            entry_number=f"JE-{bill_number}",
            entry_date=bill_date,
            description=f"Vendor Bill {bill_number}",
            entry_type=EntryType.STANDARD,
            status=EntryStatus.POSTED,
            created_by=user_id,
            posted_by=user_id,
            posted_at=datetime.utcnow(),
        )
        self.db.add(je)
        self.db.flush()

        # Expense Debit lines
        line_num = 1
        for l in lines:
            exp_line = JournalEntryLine(
                id=uuid.uuid4(),
                journal_entry_id=je.id,
                company_account_id=l["expense_account_id"],
                line_number=line_num,
                description=l.get("description", f"Expense - {bill_number}"),
                debit_amount=Decimal(str(l["amount"])),
                credit_amount=Decimal("0.00"),
            )
            self.db.add(exp_line)
            line_num += 1

        # AP Credit line
        je_line_ap = JournalEntryLine(
            id=uuid.uuid4(),
            journal_entry_id=je.id,
            company_account_id=ap_account.id,
            line_number=line_num,
            description=f"AP - {bill_number}",
            debit_amount=Decimal("0.00"),
            credit_amount=total_amount,
        )
        self.db.add(je_line_ap)

        # 2. Create AP Bill
        bill = APBill(
            id=uuid.uuid4(),
            company_id=company_id,
            vendor_id=vendor_id,
            fiscal_period_id=fiscal_period_id,
            journal_entry_id=je.id,
            bill_number=bill_number,
            bill_date=bill_date,
            due_date=due_date,
            status=APBillStatus.POSTED,
            total_amount=total_amount,
            amount_paid=Decimal("0.00"),
            amount_due=total_amount,
        )
        self.db.add(bill)
        self.db.flush()

        # Bill lines
        for idx, l in enumerate(lines, 1):
            b_line = APBillLine(
                id=uuid.uuid4(),
                bill_id=bill.id,
                expense_account_id=l["expense_account_id"],
                line_number=idx,
                description=l.get("description"),
                amount=Decimal(str(l["amount"])),
            )
            self.db.add(b_line)

        self.db.commit()
        self.db.refresh(bill)
        return bill

    def pay_bill(
        self,
        bill_id: UUID,
        payment_date: date,
        amount: Decimal,
        cash_account_id: UUID,
        user_id: UUID,
    ) -> APPayment:
        """Pay a vendor bill."""
        bill = self.db.query(APBill).filter(APBill.id == bill_id).first()
        if not bill:
            raise ValueError("Bill not found.")

        if amount > bill.amount_due:
            raise ValueError(f"Payment amount {amount} exceeds remaining due amount {bill.amount_due}.")

        ap_account = self._get_ap_control_account(bill.company_id)

        # GL Entry (Debit AP, Credit Cash)
        je = JournalEntry(
            id=uuid.uuid4(),
            company_id=bill.company_id,
            fiscal_period_id=bill.fiscal_period_id,
            entry_number=f"JE-BILL-PMT-{bill.bill_number}-{int(datetime.utcnow().timestamp())}",
            entry_date=payment_date,
            description=f"Payment for Bill {bill.bill_number}",
            entry_type=EntryType.STANDARD,
            status=EntryStatus.POSTED,
            created_by=user_id,
            posted_by=user_id,
            posted_at=datetime.utcnow(),
        )
        self.db.add(je)
        self.db.flush()

        l_ap = JournalEntryLine(
            id=uuid.uuid4(),
            journal_entry_id=je.id,
            company_account_id=ap_account.id,
            line_number=1,
            description=f"AP settlement - {bill.bill_number}",
            debit_amount=amount,
            credit_amount=Decimal("0.00"),
        )
        l_cash = JournalEntryLine(
            id=uuid.uuid4(),
            journal_entry_id=je.id,
            company_account_id=cash_account_id,
            line_number=2,
            description=f"Cash payment - {bill.bill_number}",
            debit_amount=Decimal("0.00"),
            credit_amount=amount,
        )
        self.db.add_all([l_ap, l_cash])

        # Payment record
        payment = APPayment(
            id=uuid.uuid4(),
            bill_id=bill.id,
            cash_account_id=cash_account_id,
            journal_entry_id=je.id,
            payment_date=payment_date,
            amount=amount,
        )
        self.db.add(payment)

        # Update bill balance and status
        bill.amount_paid += amount
        bill.amount_due -= amount
        if bill.amount_due == Decimal("0.00"):
            bill.status = APBillStatus.PAID
        else:
            bill.status = APBillStatus.PARTIALLY_PAID

        self.db.commit()
        self.db.refresh(payment)
        self.db.refresh(bill)
        return payment
