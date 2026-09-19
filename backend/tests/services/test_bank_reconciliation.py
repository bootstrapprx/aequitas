import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.company import Company
from app.db.models.user import User
from app.db.models.fiscal_period import FiscalPeriod, PeriodType, PeriodStatus
from app.db.models.company_account import CompanyAccount
from app.db.models.master_account import MasterAccount
from app.db.models.enums import AccountType, NormalBalance, EntryStatus, EntryType
from app.db.models.journal_entry import JournalEntry
from app.db.models.journal_entry_line import JournalEntryLine
from app.db.models.bank_statement import BankStatement, BankStatementLine, StatementLineStatus
from app.services.bank_statement_service import BankStatementService
from app.services.bank_reconciliation_service import BankReconciliationService


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def bank_reconciliation_setup(db_session):
    u = User(id=uuid4(), email="banker@example.com", is_active=True)
    c = Company(id=uuid4(), name="Banked Corp", ucid=str(uuid4()), is_active=True)
    p = FiscalPeriod(
        id=uuid4(),
        company_id=c.id,
        period_type=PeriodType.MONTH,
        period_number=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        status=PeriodStatus.OPEN,
    )

    m_cash = MasterAccount(id=uuid4(), code="10000", description="Cash Checking", category="ASSET", normal_balance="Debit", type="D", level=1, version=1, start_date=date(2025, 1, 1))
    m_rev = MasterAccount(id=uuid4(), code="40000", description="Sales", category="REVENUE", normal_balance="Credit", type="D", level=1, version=1, start_date=date(2025, 1, 1))
    db_session.add_all([u, c, p, m_cash, m_rev])

    c_cash = CompanyAccount(id=uuid4(), company_id=c.id, code="10000", description="Checking 1234", account_type=AccountType.ASSET, type="D", normal_balance=NormalBalance.DEBIT, mapped_master_account_id=m_cash.id, is_active=True)
    c_rev = CompanyAccount(id=uuid4(), company_id=c.id, code="40000", description="Sales Rev", account_type=AccountType.REVENUE, type="D", normal_balance=NormalBalance.CREDIT, mapped_master_account_id=m_rev.id, is_active=True)
    db_session.add_all([c_cash, c_rev])
    db_session.commit()

    # Create GL entries
    # 1. Deposit $1,500 on Jan 10
    je1 = JournalEntry(id=uuid4(), company_id=c.id, fiscal_period_id=p.id, entry_number="JE-DEP-01", entry_date=date(2026, 1, 10), description="Deposit from Customer A", status=EntryStatus.POSTED, created_by=u.id, posted_by=u.id)
    db_session.add(je1)
    db_session.flush()
    l1 = JournalEntryLine(id=uuid4(), journal_entry_id=je1.id, company_account_id=c_cash.id, line_number=1, debit_amount=Decimal("1500.00"), credit_amount=Decimal("0.00"))
    l2 = JournalEntryLine(id=uuid4(), journal_entry_id=je1.id, company_account_id=c_rev.id, line_number=2, debit_amount=Decimal("0.00"), credit_amount=Decimal("1500.00"))
    db_session.add_all([l1, l2])

    # 2. Deposit $500 on Jan 12
    je2 = JournalEntry(id=uuid4(), company_id=c.id, fiscal_period_id=p.id, entry_number="JE-DEP-02", entry_date=date(2026, 1, 12), description="Deposit from Customer B", status=EntryStatus.POSTED, created_by=u.id, posted_by=u.id)
    db_session.add(je2)
    db_session.flush()
    l3 = JournalEntryLine(id=uuid4(), journal_entry_id=je2.id, company_account_id=c_cash.id, line_number=1, debit_amount=Decimal("500.00"), credit_amount=Decimal("0.00"))
    l4 = JournalEntryLine(id=uuid4(), journal_entry_id=je2.id, company_account_id=c_rev.id, line_number=2, debit_amount=Decimal("0.00"), credit_amount=Decimal("500.00"))
    db_session.add_all([l3, l4])
    db_session.commit()

    return {
        "company": c,
        "cash_account": c_cash,
        "je_line_1": l1,
        "je_line_2": l3,
    }


def test_bank_statement_import_and_auto_reconciliation(db_session, bank_reconciliation_setup):
    setup = bank_reconciliation_setup
    stmt_service = BankStatementService(db_session)
    reconcile_service = BankReconciliationService(db_session)

    # 1. Ingest Bank Statement
    raw_csv_content = """Date,Description,Amount,Reference
2026-01-10,Customer A Wire,1500.00,TXN-9081
2026-01-12,Customer B ACH,500.00,TXN-9082
2026-01-14,Unknown Bank Fee,-25.00,TXN-9083
"""
    statement = stmt_service.import_csv_statement(
        company_id=setup["company"].id,
        cash_account_id=setup["cash_account"].id,
        statement_date=date(2026, 1, 31),
        csv_text=raw_csv_content,
    )

    assert statement is not None
    assert len(statement.lines) == 3
    assert statement.lines[0].amount == Decimal("1500.00")

    # 2. Run Auto-Reconciliation Matching
    match_result = reconcile_service.auto_match(
        statement_id=statement.id,
        cash_account_id=setup["cash_account"].id,
    )

    assert match_result["matched_count"] == 2
    assert match_result["unmatched_count"] == 1

    stmt_line_1 = statement.lines[0]
    assert stmt_line_1.status == StatementLineStatus.MATCHED
    assert stmt_line_1.matched_journal_entry_line_id == setup["je_line_1"].id
