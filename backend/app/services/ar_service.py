import uuid
from decimal import Decimal
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.db.models.ar_invoice import ARInvoice, ARInvoiceLine, ARInvoiceStatus, ARPayment
from app.db.models.company_account import CompanyAccount
from app.db.models.master_account import MasterAccount
from app.db.models.journal_entry import JournalEntry, EntryStatus, EntryType
from app.db.models.journal_entry_line import JournalEntryLine
from app.db.models.enums import AccountType


class ARService:
    """Service for Accounts Receivable operations."""

    def __init__(self, db: Session):
        self.db = db

    def _get_ar_control_account(self, company_id: UUID) -> CompanyAccount:
        """Find the Accounts Receivable control account."""
        acc = self.db.query(CompanyAccount).join(
            MasterAccount, CompanyAccount.mapped_master_account_id == MasterAccount.id, isouter=True
        ).filter(
            CompanyAccount.company_id == company_id,
            CompanyAccount.is_active.is_(True),
            (MasterAccount.code == "12000") | (CompanyAccount.code == "12000") | (CompanyAccount.description.ilike("%receivable%"))
        ).first()

        if not acc:
            acc = self.db.query(CompanyAccount).filter(
                CompanyAccount.company_id == company_id,
                CompanyAccount.account_type == AccountType.ASSET,
                CompanyAccount.is_active.is_(True),
            ).first()

        if not acc:
            raise ValueError("No Accounts Receivable or Asset account found.")
        return acc

    def create_invoice(
        self,
        company_id: UUID,
        customer_id: UUID,
        fiscal_period_id: UUID,
        invoice_date: date,
        due_date: date,
        user_id: UUID,
        lines: List[Dict[str, Any]],
        invoice_number: Optional[str] = None,
    ) -> ARInvoice:
        """Create and post a customer invoice and corresponding GL entry."""
        if not lines:
            raise ValueError("Invoice must have at least one line.")

        total_amount = sum(Decimal(str(l["amount"])) for l in lines)
        if not invoice_number:
            invoice_number = f"INV-{int(datetime.utcnow().timestamp())}"

        ar_account = self._get_ar_control_account(company_id)

        # 1. Create Journal Entry (Debit AR, Credit Revenue)
        je = JournalEntry(
            id=uuid.uuid4(),
            company_id=company_id,
            fiscal_period_id=fiscal_period_id,
            entry_number=f"JE-{invoice_number}",
            entry_date=invoice_date,
            description=f"Invoice {invoice_number} to Customer",
            entry_type=EntryType.STANDARD,
            status=EntryStatus.POSTED,
            created_by=user_id,
            posted_by=user_id,
            posted_at=datetime.utcnow(),
        )
        self.db.add(je)
        self.db.flush()

        # AR Debit line
        je_line_ar = JournalEntryLine(
            id=uuid.uuid4(),
            journal_entry_id=je.id,
            company_account_id=ar_account.id,
            line_number=1,
            description=f"AR - {invoice_number}",
            debit_amount=total_amount,
            credit_amount=Decimal("0.00"),
        )
        self.db.add(je_line_ar)

        # Revenue Credit lines
        line_num = 2
        for l in lines:
            rev_line = JournalEntryLine(
                id=uuid.uuid4(),
                journal_entry_id=je.id,
                company_account_id=l["revenue_account_id"],
                line_number=line_num,
                description=l.get("description", f"Revenue - {invoice_number}"),
                debit_amount=Decimal("0.00"),
                credit_amount=Decimal(str(l["amount"])),
            )
            self.db.add(rev_line)
            line_num += 1

        # 2. Create AR Invoice
        invoice = ARInvoice(
            id=uuid.uuid4(),
            company_id=company_id,
            customer_id=customer_id,
            fiscal_period_id=fiscal_period_id,
            journal_entry_id=je.id,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            due_date=due_date,
            status=ARInvoiceStatus.POSTED,
            total_amount=total_amount,
            amount_paid=Decimal("0.00"),
            amount_due=total_amount,
        )
        self.db.add(invoice)
        self.db.flush()

        # Invoice lines
        for idx, l in enumerate(lines, 1):
            inv_line = ARInvoiceLine(
                id=uuid.uuid4(),
                invoice_id=invoice.id,
                revenue_account_id=l["revenue_account_id"],
                line_number=idx,
                description=l.get("description"),
                amount=Decimal(str(l["amount"])),
            )
            self.db.add(inv_line)

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def apply_payment(
        self,
        invoice_id: UUID,
        payment_date: date,
        amount: Decimal,
        cash_account_id: UUID,
        user_id: UUID,
    ) -> ARPayment:
        """Apply payment against an open AR Invoice."""
        invoice = self.db.query(ARInvoice).filter(ARInvoice.id == invoice_id).first()
        if not invoice:
            raise ValueError("Invoice not found.")

        if amount > invoice.amount_due:
            raise ValueError(f"Payment amount {amount} exceeds remaining due amount {invoice.amount_due}.")

        ar_account = self._get_ar_control_account(invoice.company_id)

        # GL Entry (Debit Cash, Credit AR)
        je = JournalEntry(
            id=uuid.uuid4(),
            company_id=invoice.company_id,
            fiscal_period_id=invoice.fiscal_period_id,
            entry_number=f"JE-PMT-{invoice.invoice_number}-{int(datetime.utcnow().timestamp())}",
            entry_date=payment_date,
            description=f"Payment for Invoice {invoice.invoice_number}",
            entry_type=EntryType.STANDARD,
            status=EntryStatus.POSTED,
            created_by=user_id,
            posted_by=user_id,
            posted_at=datetime.utcnow(),
        )
        self.db.add(je)
        self.db.flush()

        l_cash = JournalEntryLine(
            id=uuid.uuid4(),
            journal_entry_id=je.id,
            company_account_id=cash_account_id,
            line_number=1,
            description=f"Cash receipt - {invoice.invoice_number}",
            debit_amount=amount,
            credit_amount=Decimal("0.00"),
        )
        l_ar = JournalEntryLine(
            id=uuid.uuid4(),
            journal_entry_id=je.id,
            company_account_id=ar_account.id,
            line_number=2,
            description=f"AR settlement - {invoice.invoice_number}",
            debit_amount=Decimal("0.00"),
            credit_amount=amount,
        )
        self.db.add_all([l_cash, l_ar])

        # Payment record
        payment = ARPayment(
            id=uuid.uuid4(),
            invoice_id=invoice.id,
            cash_account_id=cash_account_id,
            journal_entry_id=je.id,
            payment_date=payment_date,
            amount=amount,
        )
        self.db.add(payment)

        # Update invoice balance and status
        invoice.amount_paid += amount
        invoice.amount_due -= amount
        if invoice.amount_due == Decimal("0.00"):
            invoice.status = ARInvoiceStatus.PAID
        else:
            invoice.status = ARInvoiceStatus.PARTIALLY_PAID

        self.db.commit()
        self.db.refresh(payment)
        self.db.refresh(invoice)
        return payment
