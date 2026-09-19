import pytest
from uuid import uuid4
from datetime import date
from decimal import Decimal
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
from app.services.journal_entry_service import JournalEntryService
from app.services.year_end_closing_service import YearEndClosingService


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
def test_setup(db_session):
    # Create user
    user = User(
        id=uuid4(),
        email="accountant@test.com",
        role="ACCOUNTANT",
        is_active=True,
    )
    db_session.add(user)

    # Create company
    company = Company(
        id=uuid4(),
        name="Test Corp",
        ucid=str(uuid4()),
        is_active=True,
    )
    db_session.add(company)

    # Create fiscal periods for year 2026
    p1 = FiscalPeriod(
        id=uuid4(),
        company_id=company.id,
        period_type=PeriodType.MONTH,
        period_number=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        status=PeriodStatus.OPEN,
    )
    p12 = FiscalPeriod(
        id=uuid4(),
        company_id=company.id,
        period_type=PeriodType.MONTH,
        period_number=12,
        start_date=date(2026, 12, 1),
        end_date=date(2026, 12, 31),
        status=PeriodStatus.OPEN,
    )
    p_next_year = FiscalPeriod(
        id=uuid4(),
        company_id=company.id,
        period_type=PeriodType.MONTH,
        period_number=1,
        start_date=date(2027, 1, 1),
        end_date=date(2027, 1, 31),
        status=PeriodStatus.OPEN,
    )
    db_session.add_all([p1, p12, p_next_year])

    # Create Master Accounts
    m_cash = MasterAccount(
        id=uuid4(),
        code="10000",
        description="Operating Cash",
        category="ASSET",
        normal_balance="Debit",
        type="D",
        level=1,
        version=1,
        start_date=date(2025, 1, 1),
    )
    m_re = MasterAccount(
        id=uuid4(),
        code="39000",
        description="Retained Earnings",
        category="EQUITY",
        normal_balance="Credit",
        type="D",
        level=1,
        version=1,
        start_date=date(2025, 1, 1),
    )
    m_rev = MasterAccount(
        id=uuid4(),
        code="40000",
        description="Operating Revenue",
        category="REVENUE",
        normal_balance="Credit",
        type="D",
        level=1,
        version=1,
        start_date=date(2025, 1, 1),
    )
    m_exp = MasterAccount(
        id=uuid4(),
        code="60000",
        description="Operating Expenses",
        category="EXPENSE",
        normal_balance="Debit",
        type="D",
        level=1,
        version=1,
        start_date=date(2025, 1, 1),
    )
    db_session.add_all([m_cash, m_re, m_rev, m_exp])

    # Create Company Accounts
    c_cash = CompanyAccount(
        id=uuid4(),
        company_id=company.id,
        code="10000",
        description="Operating Checking",
        account_type=AccountType.ASSET,
        type="D",
        normal_balance=NormalBalance.DEBIT,
        mapped_master_account_id=m_cash.id,
        is_active=True,
    )
    c_re = CompanyAccount(
        id=uuid4(),
        company_id=company.id,
        code="39000",
        description="Retained Earnings",
        account_type=AccountType.EQUITY,
        type="D",
        normal_balance=NormalBalance.CREDIT,
        mapped_master_account_id=m_re.id,
        is_active=True,
    )
    c_rev = CompanyAccount(
        id=uuid4(),
        company_id=company.id,
        code="40000",
        description="Client Fees",
        account_type=AccountType.REVENUE,
        type="D",
        normal_balance=NormalBalance.CREDIT,
        mapped_master_account_id=m_rev.id,
        is_active=True,
    )
    c_exp = CompanyAccount(
        id=uuid4(),
        company_id=company.id,
        code="60000",
        description="Rent Expense",
        account_type=AccountType.EXPENSE,
        type="D",
        normal_balance=NormalBalance.DEBIT,
        mapped_master_account_id=m_exp.id,
        is_active=True,
    )
    db_session.add_all([c_cash, c_re, c_rev, c_exp])
    db_session.commit()

    return {
        "user": user,
        "company": company,
        "p1": p1,
        "p12": p12,
        "p_next_year": p_next_year,
        "c_cash": c_cash,
        "c_re": c_re,
        "c_rev": c_rev,
        "c_exp": c_exp,
    }


def test_year_end_closing_generates_balanced_entry(db_session, test_setup):
    setup = test_setup
    company = setup["company"]
    user = setup["user"]
    p1 = setup["p1"]
    p12 = setup["p12"]
    c_cash = setup["c_cash"]
    c_rev = setup["c_rev"]
    c_exp = setup["c_exp"]
    c_re = setup["c_re"]

    # Post revenue entry: Cash 10,000 / Revenue 10,000 in P1
    je_rev = JournalEntry(
        id=uuid4(),
        company_id=company.id,
        fiscal_period_id=p1.id,
        entry_number="JE-2026-001",
        entry_date=date(2026, 1, 15),
        description="Client revenue",
        status=EntryStatus.POSTED,
        created_by=user.id,
        posted_by=user.id,
    )
    db_session.add(je_rev)
    db_session.flush()
    l1 = JournalEntryLine(
        id=uuid4(),
        journal_entry_id=je_rev.id,
        company_account_id=c_cash.id,
        line_number=1,
        debit_amount=Decimal("10000.00"),
        credit_amount=Decimal("0.00"),
    )
    l2 = JournalEntryLine(
        id=uuid4(),
        journal_entry_id=je_rev.id,
        company_account_id=c_rev.id,
        line_number=2,
        debit_amount=Decimal("0.00"),
        credit_amount=Decimal("10000.00"),
    )
    db_session.add_all([l1, l2])

    # Post expense entry: Rent 3,000 / Cash 3,000 in P12
    je_exp = JournalEntry(
        id=uuid4(),
        company_id=company.id,
        fiscal_period_id=p12.id,
        entry_number="JE-2026-002",
        entry_date=date(2026, 12, 15),
        description="Office rent",
        status=EntryStatus.POSTED,
        created_by=user.id,
        posted_by=user.id,
    )
    db_session.add(je_exp)
    db_session.flush()
    l3 = JournalEntryLine(
        id=uuid4(),
        journal_entry_id=je_exp.id,
        company_account_id=c_exp.id,
        line_number=1,
        debit_amount=Decimal("3000.00"),
        credit_amount=Decimal("0.00"),
    )
    l4 = JournalEntryLine(
        id=uuid4(),
        journal_entry_id=je_exp.id,
        company_account_id=c_cash.id,
        line_number=2,
        debit_amount=Decimal("0.00"),
        credit_amount=Decimal("3000.00"),
    )
    db_session.add_all([l3, l4])
    db_session.commit()

    # Run Year-End Closing
    closing_service = YearEndClosingService(db_session)
    closing_entry = closing_service.generate_year_end_closing_entry(
        company_id=company.id,
        fiscal_year=2026,
        closing_period_id=p12.id,
        user_id=user.id,
    )

    assert closing_entry is not None
    assert closing_entry.entry_type == EntryType.CLOSING
    assert closing_entry.status == EntryStatus.POSTED

    # Verify lines
    # Revenue (10,000 credit balance) should be debited 10,000
    # Expense (3,000 debit balance) should be credited 3,000
    # Retained Earnings (Net Income 7,000) should be credited 7,000
    lines = closing_entry.lines
    assert len(lines) == 3

    total_debits = sum(line.debit_amount for line in lines)
    total_credits = sum(line.credit_amount for line in lines)
    assert total_debits == Decimal("10000.00")
    assert total_credits == Decimal("10000.00")

    re_line = next(l for l in lines if l.company_account_id == c_re.id)
    assert re_line.credit_amount == Decimal("7000.00")


def test_auto_reversing_journal_entry(db_session, test_setup):
    setup = test_setup
    company = setup["company"]
    user = setup["user"]
    p12 = setup["p12"]
    p_next_year = setup["p_next_year"]
    c_exp = setup["c_exp"]
    c_cash = setup["c_cash"]

    je_service = JournalEntryService(db_session)

    # Create an auto-reversing accrual entry in December 2026
    entry = JournalEntry(
        id=uuid4(),
        company_id=company.id,
        fiscal_period_id=p12.id,
        entry_number="JE-ACCRUAL-001",
        entry_date=date(2026, 12, 31),
        description="December utility accrual",
        status=EntryStatus.DRAFT,
        entry_type=EntryType.ADJUSTING,
        auto_reverse=True,
        reversal_date=date(2027, 1, 1),
        created_by=user.id,
    )
    db_session.add(entry)
    db_session.flush()

    line1 = JournalEntryLine(
        id=uuid4(),
        journal_entry_id=entry.id,
        company_account_id=c_exp.id,
        line_number=1,
        debit_amount=Decimal("500.00"),
        credit_amount=Decimal("0.00"),
    )
    line2 = JournalEntryLine(
        id=uuid4(),
        journal_entry_id=entry.id,
        company_account_id=c_cash.id,
        line_number=2,
        debit_amount=Decimal("0.00"),
        credit_amount=Decimal("500.00"),
    )
    db_session.add_all([line1, line2])
    db_session.commit()

    # Post the entry and verify auto-reversal is triggered
    posted_entry = je_service.post_journal_entry(entry.id, user.id)
    assert posted_entry.status == EntryStatus.POSTED
    assert posted_entry.reversed_by_entry_id is not None

    reversal_entry = db_session.query(JournalEntry).filter(
        JournalEntry.id == posted_entry.reversed_by_entry_id
    ).first()

    assert reversal_entry is not None
    assert reversal_entry.entry_type == EntryType.REVERSING
    assert reversal_entry.status == EntryStatus.POSTED
    assert reversal_entry.reverses_entry_id == posted_entry.id
    assert reversal_entry.entry_date == date(2027, 1, 1)

    # Inverted lines: Expense credited 500, Cash debited 500
    rev_lines = reversal_entry.lines
    exp_rev_line = next(l for l in rev_lines if l.company_account_id == c_exp.id)
    assert exp_rev_line.credit_amount == Decimal("500.00")
    assert exp_rev_line.debit_amount == Decimal("0.00")
