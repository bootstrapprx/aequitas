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
from app.db.models.accounting_dimension import AccountingDimension, DimensionType
from app.db.models.enums import AccountType, NormalBalance, EntryStatus, EntryType
from app.db.models.journal_entry import JournalEntry
from app.db.models.journal_entry_line import JournalEntryLine
from app.services.financial_statement_service import FinancialStatementService
from app.services.ledger_service import LedgerService


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
def dimensional_reporting_setup(db_session):
    u = User(id=uuid4(), email="lead@example.com", is_active=True)
    c = Company(id=uuid4(), name="Segment Corp", ucid=str(uuid4()), is_active=True)
    p = FiscalPeriod(
        id=uuid4(),
        company_id=c.id,
        period_type=PeriodType.MONTH,
        period_number=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        status=PeriodStatus.OPEN,
    )

    dep_eng = AccountingDimension(id=uuid4(), company_id=c.id, dimension_type=DimensionType.DEPARTMENT, name="Engineering")
    dep_sales = AccountingDimension(id=uuid4(), company_id=c.id, dimension_type=DimensionType.DEPARTMENT, name="Sales")

    # Master Accounts
    m_cash = MasterAccount(
        id=uuid4(), code="10000", description="Cash", category="ASSET",
        normal_balance="Debit", type="D", level=1, version=1, start_date=date(2025, 1, 1)
    )
    m_rev = MasterAccount(
        id=uuid4(), code="40000", description="Revenue", category="REVENUE",
        normal_balance="Credit", type="D", level=1, version=1, start_date=date(2025, 1, 1),
        fs_mapping="Income Statement"
    )
    m_exp = MasterAccount(
        id=uuid4(), code="60000", description="Expenses", category="EXPENSE",
        normal_balance="Debit", type="D", level=1, version=1, start_date=date(2025, 1, 1),
        fs_mapping="Income Statement"
    )
    db_session.add_all([u, c, p, dep_eng, dep_sales, m_cash, m_rev, m_exp])

    # Company Accounts
    c_cash = CompanyAccount(
        id=uuid4(), company_id=c.id, code="10000", description="Cash",
        account_type=AccountType.ASSET, type="D", normal_balance=NormalBalance.DEBIT,
        mapped_master_account_id=m_cash.id, is_active=True
    )
    c_rev = CompanyAccount(
        id=uuid4(), company_id=c.id, code="40000", description="Consulting Revenue",
        account_type=AccountType.REVENUE, type="D", normal_balance=NormalBalance.CREDIT,
        mapped_master_account_id=m_rev.id, is_active=True
    )
    c_exp = CompanyAccount(
        id=uuid4(), company_id=c.id, code="60000", description="Software & Cloud Ops",
        account_type=AccountType.EXPENSE, type="D", normal_balance=NormalBalance.DEBIT,
        mapped_master_account_id=m_exp.id, is_active=True
    )
    db_session.add_all([c_cash, c_rev, c_exp])
    db_session.commit()

    # Create & Post Entry 1: Revenue 10,000 for Sales
    je1 = JournalEntry(
        id=uuid4(), company_id=c.id, fiscal_period_id=p.id, entry_number="JE-001",
        entry_date=date(2026, 1, 10), description="Sales Rev", status=EntryStatus.POSTED,
        created_by=u.id, posted_by=u.id
    )
    db_session.add(je1)
    db_session.flush()
    l1 = JournalEntryLine(
        id=uuid4(), journal_entry_id=je1.id, company_account_id=c_cash.id,
        line_number=1, debit_amount=Decimal("10000.00"), credit_amount=Decimal("0.00")
    )
    l2 = JournalEntryLine(
        id=uuid4(), journal_entry_id=je1.id, company_account_id=c_rev.id,
        line_number=2, debit_amount=Decimal("0.00"), credit_amount=Decimal("10000.00"),
        department_id=dep_sales.id
    )
    db_session.add_all([l1, l2])

    # Create & Post Entry 2: Expense 4,000 for Engineering
    je2 = JournalEntry(
        id=uuid4(), company_id=c.id, fiscal_period_id=p.id, entry_number="JE-002",
        entry_date=date(2026, 1, 15), description="Engineering Cloud", status=EntryStatus.POSTED,
        created_by=u.id, posted_by=u.id
    )
    db_session.add(je2)
    db_session.flush()
    l3 = JournalEntryLine(
        id=uuid4(), journal_entry_id=je2.id, company_account_id=c_exp.id,
        line_number=1, debit_amount=Decimal("4000.00"), credit_amount=Decimal("0.00"),
        department_id=dep_eng.id
    )
    l4 = JournalEntryLine(
        id=uuid4(), journal_entry_id=je2.id, company_account_id=c_cash.id,
        line_number=2, debit_amount=Decimal("0.00"), credit_amount=Decimal("4000.00")
    )
    db_session.add_all([l3, l4])
    db_session.commit()

    return {
        "company": c,
        "period": p,
        "dep_eng": dep_eng,
        "dep_sales": dep_sales,
    }


def test_financial_statement_and_ledger_department_filter(db_session, dimensional_reporting_setup):
    setup = dimensional_reporting_setup
    company = setup["company"]
    period = setup["period"]
    dep_eng = setup["dep_eng"]
    dep_sales = setup["dep_sales"]

    fs_service = FinancialStatementService(db_session)
    ledger_service = LedgerService(db_session)

    # 1. Total Unfiltered Income Statement: Net Income = 10,000 - 4,000 = 6,000
    is_total = fs_service.generate_income_statement(company.id, period.start_date, period.end_date)
    assert is_total.net_income == Decimal("6000.00")

    # 2. Filtered Income Statement for Sales Department: Net Income = 10,000
    is_sales = fs_service.generate_income_statement(
        company.id, period.start_date, period.end_date, department_id=dep_sales.id
    )
    assert is_sales.net_income == Decimal("10000.00")

    # 3. Filtered Income Statement for Engineering Department: Net Income = -4,000
    is_eng = fs_service.generate_income_statement(
        company.id, period.start_date, period.end_date, department_id=dep_eng.id
    )
    assert is_eng.net_income == Decimal("-4000.00")

    # 4. Trial balance filtered by Engineering Department
    tb_eng = ledger_service.get_trial_balance(
        company.id, fiscal_period_id=period.id, department_id=dep_eng.id
    )
    assert len(tb_eng.accounts) == 1
    assert tb_eng.accounts[0].account_code == "60000"
    assert tb_eng.accounts[0].debit_balance == Decimal("4000.00")
