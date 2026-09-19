import uuid
from decimal import Decimal
from datetime import date, datetime
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.db.models.company_account import CompanyAccount
from app.db.models.master_account import MasterAccount
from app.db.models.journal_entry import JournalEntry, EntryStatus, EntryType
from app.db.models.journal_entry_line import JournalEntryLine
from app.db.models.enums import AccountType


class IntercompanyService:
    """Service to handle paired cross-company intercompany journal entries."""

    def __init__(self, db: Session):
        self.db = db

    def _get_due_from_account(self, company_id: UUID) -> CompanyAccount:
        acc = self.db.query(CompanyAccount).join(
            MasterAccount, CompanyAccount.mapped_master_account_id == MasterAccount.id, isouter=True
        ).filter(
            CompanyAccount.company_id == company_id,
            CompanyAccount.is_active.is_(True),
            (MasterAccount.code == "13000") | (CompanyAccount.code == "13000") | (CompanyAccount.description.ilike("%due from%"))
        ).first()

        if not acc:
            acc = self.db.query(CompanyAccount).filter(
                CompanyAccount.company_id == company_id,
                CompanyAccount.account_type == AccountType.ASSET,
                CompanyAccount.is_active.is_(True),
            ).first()

        if not acc:
            raise ValueError("No Due From intercompany asset account found.")
        return acc

    def _get_due_to_account(self, company_id: UUID) -> CompanyAccount:
        acc = self.db.query(CompanyAccount).join(
            MasterAccount, CompanyAccount.mapped_master_account_id == MasterAccount.id, isouter=True
        ).filter(
            CompanyAccount.company_id == company_id,
            CompanyAccount.is_active.is_(True),
            (MasterAccount.code == "23000") | (CompanyAccount.code == "23000") | (CompanyAccount.description.ilike("%due to%"))
        ).first()

        if not acc:
            acc = self.db.query(CompanyAccount).filter(
                CompanyAccount.company_id == company_id,
                CompanyAccount.account_type == AccountType.LIABILITY,
                CompanyAccount.is_active.is_(True),
            ).first()

        if not acc:
            raise ValueError("No Due To intercompany liability account found.")
        return acc

    def create_paired_intercompany_entry(
        self,
        from_company_id: UUID,
        to_company_id: UUID,
        from_fiscal_period_id: UUID,
        to_fiscal_period_id: UUID,
        entry_date: date,
        amount: Decimal,
        from_revenue_account_id: UUID,
        to_expense_account_id: UUID,
        user_id: UUID,
        description: str,
    ) -> Dict[str, Any]:
        """
        Atomically post paired GL entries:
        Source entity: Debit Due From Affiliates, Credit Revenue
        Target entity: Debit Expense, Credit Due To Affiliates
        """
        due_from_acc = self._get_due_from_account(from_company_id)
        due_to_acc = self._get_due_to_account(to_company_id)

        source_entry_id = uuid.uuid4()
        mirror_entry_id = uuid.uuid4()

        # 1. Source Journal Entry (Entity A)
        source_je = JournalEntry(
            id=source_entry_id,
            company_id=from_company_id,
            fiscal_period_id=from_fiscal_period_id,
            entry_number=f"JE-IC-SRC-{int(datetime.utcnow().timestamp())}",
            entry_date=entry_date,
            description=f"Intercompany Outgoing: {description}",
            entry_type=EntryType.STANDARD,
            status=EntryStatus.POSTED,
            created_by=user_id,
            posted_by=user_id,
            posted_at=datetime.utcnow(),
        )
        self.db.add(source_je)
        self.db.flush()

        s_l1 = JournalEntryLine(
            id=uuid.uuid4(),
            journal_entry_id=source_je.id,
            company_account_id=due_from_acc.id,
            line_number=1,
            description="Due From Affiliate",
            debit_amount=amount,
            credit_amount=Decimal("0.00"),
        )
        s_l2 = JournalEntryLine(
            id=uuid.uuid4(),
            journal_entry_id=source_je.id,
            company_account_id=from_revenue_account_id,
            line_number=2,
            description="Intercompany Revenue",
            debit_amount=Decimal("0.00"),
            credit_amount=amount,
        )
        self.db.add_all([s_l1, s_l2])

        # 2. Mirror Journal Entry (Entity B)
        mirror_je = JournalEntry(
            id=mirror_entry_id,
            company_id=to_company_id,
            fiscal_period_id=to_fiscal_period_id,
            entry_number=f"JE-IC-MIR-{int(datetime.utcnow().timestamp())}",
            entry_date=entry_date,
            description=f"Intercompany Incoming: {description}",
            entry_type=EntryType.STANDARD,
            status=EntryStatus.POSTED,
            created_by=user_id,
            posted_by=user_id,
            posted_at=datetime.utcnow(),
        )
        self.db.add(mirror_je)
        self.db.flush()

        m_l1 = JournalEntryLine(
            id=uuid.uuid4(),
            journal_entry_id=mirror_je.id,
            company_account_id=to_expense_account_id,
            line_number=1,
            description="Intercompany Expense",
            debit_amount=amount,
            credit_amount=Decimal("0.00"),
        )
        m_l2 = JournalEntryLine(
            id=uuid.uuid4(),
            journal_entry_id=mirror_je.id,
            company_account_id=due_to_acc.id,
            line_number=2,
            description="Due To Affiliate",
            debit_amount=Decimal("0.00"),
            credit_amount=amount,
        )
        self.db.add_all([m_l1, m_l2])

        self.db.commit()
        self.db.refresh(source_je)
        self.db.refresh(mirror_je)

        return {
            "source_entry": source_je,
            "mirror_entry": mirror_je,
        }
