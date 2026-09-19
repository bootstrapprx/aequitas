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
from app.db.models.accounting_dimension import AccountingDimension, DimensionType
from app.db.models.fiscal_period import FiscalPeriod, PeriodType, PeriodStatus
from app.db.models.company_account import CompanyAccount
from app.db.models.enums import AccountType, NormalBalance
from app.schemas.journal_entry import JournalEntryCreate, JournalEntryLineCreate
from app.services.journal_entry_service import JournalEntryService


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
def setup_dimensional_data(db_session):
    u = User(id=uuid4(), email="tester@example.com", is_active=True)
    c = Company(id=uuid4(), name="Dimension Co", ucid=str(uuid4()), is_active=True)
    p = FiscalPeriod(
        id=uuid4(),
        company_id=c.id,
        period_type=PeriodType.MONTH,
        period_number=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        status=PeriodStatus.OPEN,
    )
    
    # Create Dimensions
    dep_eng = AccountingDimension(id=uuid4(), company_id=c.id, dimension_type=DimensionType.DEPARTMENT, name="Engineering")
    dep_sales = AccountingDimension(id=uuid4(), company_id=c.id, dimension_type=DimensionType.DEPARTMENT, name="Sales")
    cc_marketing = AccountingDimension(id=uuid4(), company_id=c.id, dimension_type=DimensionType.COST_CENTER, name="Marketing Ops")

    # Create Account
    acc_exp = CompanyAccount(
        id=uuid4(),
        company_id=c.id,
        code="61000",
        description="Payroll Expense",
        account_type=AccountType.EXPENSE,
        type="D",
        normal_balance=NormalBalance.DEBIT,
        is_active=True,
    )
    acc_cash = CompanyAccount(
        id=uuid4(),
        company_id=c.id,
        code="10000",
        description="Cash",
        account_type=AccountType.ASSET,
        type="D",
        normal_balance=NormalBalance.DEBIT,
        is_active=True,
    )

    db_session.add_all([u, c, p, dep_eng, dep_sales, cc_marketing, acc_exp, acc_cash])
    db_session.commit()

    return {
        "user": u,
        "company": c,
        "period": p,
        "dep_eng": dep_eng,
        "dep_sales": dep_sales,
        "cc_marketing": cc_marketing,
        "acc_exp": acc_exp,
        "acc_cash": acc_cash,
    }

def test_create_journal_entry_with_dimensions(db_session, setup_dimensional_data):
    setup = setup_dimensional_data
    
    je_schema = JournalEntryCreate(
        company_id=setup["company"].id,
        fiscal_period_id=setup["period"].id,
        entry_date=date(2026, 1, 15),
        description="Payroll split by dimension",
        reference="PR-2026-01",
        lines=[
            JournalEntryLineCreate(
                company_account_id=setup["acc_exp"].id,
                line_number=1,
                debit_amount=Decimal("5000.00"),
                credit_amount=Decimal("0.00"),
                department_id=setup["dep_eng"].id,
            ),
            JournalEntryLineCreate(
                company_account_id=setup["acc_exp"].id,
                line_number=2,
                debit_amount=Decimal("3000.00"),
                credit_amount=Decimal("0.00"),
                department_id=setup["dep_sales"].id,
                cost_center_id=setup["cc_marketing"].id,
            ),
            JournalEntryLineCreate(
                company_account_id=setup["acc_cash"].id,
                line_number=3,
                debit_amount=Decimal("0.00"),
                credit_amount=Decimal("8000.00"),
            ),
        ]
    )

    je_service = JournalEntryService(db_session)
    entry = je_service.create_journal_entry(je_schema, setup["user"].id)

    assert entry is not None
    assert len(entry.lines) == 3
    
    line1 = next(l for l in entry.lines if l.line_number == 1)
    assert line1.department_id == setup["dep_eng"].id
    assert line1.cost_center_id is None

    line2 = next(l for l in entry.lines if l.line_number == 2)
    assert line2.department_id == setup["dep_sales"].id
    assert line2.cost_center_id == setup["cc_marketing"].id

    line3 = next(l for l in entry.lines if l.line_number == 3)
    assert line3.department_id is None
