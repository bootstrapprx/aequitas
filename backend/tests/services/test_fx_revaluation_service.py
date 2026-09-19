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
from app.db.models.currency import Currency, ExchangeRate, RateType
from app.db.models.enums import AccountType, NormalBalance, EntryStatus, EntryType
from app.db.models.journal_entry import JournalEntry
from app.db.models.journal_entry_line import JournalEntryLine
from app.services.fx_rate_service import FxRateService
from app.services.fx_revaluation_service import FxRevaluationService


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
def fx_revaluation_setup(db_session):
    u = User(id=uuid4(), email="treasurer@example.com", is_active=True)
    c = Company(id=uuid4(), name="Global Corp", ucid=str(uuid4()), is_active=True)
    p = FiscalPeriod(
        id=uuid4(),
        company_id=c.id,
        period_type=PeriodType.MONTH,
        period_number=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        status=PeriodStatus.OPEN,
    )

    # Currencies
    c_usd = Currency(code="USD", name="US Dollar", symbol="$", decimals=2, is_active=True)
    c_eur = Currency(code="EUR", name="Euro", symbol="€", decimals=2, is_active=True)
    db_session.add_all([u, c, p, c_usd, c_eur])

    # Accounts
    m_eur_cash = MasterAccount(
        id=uuid4(), code="10200", description="Foreign Bank EUR", category="ASSET",
        normal_balance="Debit", type="D", level=1, version=1, start_date=date(2025, 1, 1)
    )
    m_fx_gain_loss = MasterAccount(
        id=uuid4(), code="70500", description="Unrealized FX Gain/Loss", category="EXPENSE",
        normal_balance="Debit", type="D", level=1, version=1, start_date=date(2025, 1, 1)
    )
    m_equity = MasterAccount(
        id=uuid4(), code="30000", description="Common Stock", category="EQUITY",
        normal_balance="Credit", type="D", level=1, version=1, start_date=date(2025, 1, 1)
    )
    db_session.add_all([m_eur_cash, m_fx_gain_loss, m_equity])

    c_eur_cash = CompanyAccount(
        id=uuid4(), company_id=c.id, code="10200", description="EUR Bank Account",
        account_type=AccountType.ASSET, type="D", normal_balance=NormalBalance.DEBIT,
        currency="EUR", mapped_master_account_id=m_eur_cash.id, is_active=True
    )
    c_fx_gain_loss = CompanyAccount(
        id=uuid4(), company_id=c.id, code="70500", description="Unrealized FX Gain/Loss",
        account_type=AccountType.EXPENSE, type="D", normal_balance=NormalBalance.DEBIT,
        mapped_master_account_id=m_fx_gain_loss.id, is_active=True
    )
    c_equity = CompanyAccount(
        id=uuid4(), company_id=c.id, code="30000", description="Common Stock",
        account_type=AccountType.EQUITY, type="D", normal_balance=NormalBalance.CREDIT,
        mapped_master_account_id=m_equity.id, is_active=True
    )
    db_session.add_all([c_eur_cash, c_fx_gain_loss, c_equity])
    db_session.commit()

    # Initial transaction: EUR 10,000 received on Jan 1st at rate 1.05 -> USD 10,500
    je_init = JournalEntry(
        id=uuid4(), company_id=c.id, fiscal_period_id=p.id, entry_number="JE-INIT-EUR",
        entry_date=date(2026, 1, 1), description="Initial EUR Capital", status=EntryStatus.POSTED,
        created_by=u.id, posted_by=u.id
    )
    db_session.add(je_init)
    db_session.flush()

    l1 = JournalEntryLine(
        id=uuid4(), journal_entry_id=je_init.id, company_account_id=c_eur_cash.id,
        line_number=1, debit_amount=Decimal("10500.00"), credit_amount=Decimal("0.00")
    )
    l2 = JournalEntryLine(
        id=uuid4(), journal_entry_id=je_init.id, company_account_id=c_equity.id,
        line_number=2, debit_amount=Decimal("0.00"), credit_amount=Decimal("10500.00")
    )
    db_session.add_all([l1, l2])
    db_session.commit()

    # Set Closing Exchange rate on Jan 31st: EUR/USD = 1.10 (Gain of $500 on EUR 10,000)
    fx_service = FxRateService(db_session)
    fx_service.set_rate(
        from_currency="EUR",
        to_currency="USD",
        rate=Decimal("1.1000"),
        rate_date=date(2026, 1, 31),
        rate_type=RateType.CLOSING
    )

    return {
        "user": u,
        "company": c,
        "period": p,
        "c_eur_cash": c_eur_cash,
        "c_fx_gain_loss": c_fx_gain_loss,
    }


def test_fx_period_revaluation_posts_balanced_entry(db_session, fx_revaluation_setup):
    setup = fx_revaluation_setup
    reval_service = FxRevaluationService(db_session)

    # Run revaluation for Jan 31, 2026
    # Current Book USD = 10,500. Target USD = EUR 10,000 * 1.10 = 11,000.
    # Unrealized Gain = $500.00 (Debit EUR Bank 500, Credit FX Gain/Loss 500)
    reval_entry = reval_service.run_period_revaluation(
        company_id=setup["company"].id,
        fiscal_period_id=setup["period"].id,
        user_id=setup["user"].id,
        foreign_account_balances={"EUR": {setup["c_eur_cash"].id: Decimal("10000.00")}}
    )

    assert reval_entry is not None
    assert reval_entry.status == EntryStatus.POSTED
    assert reval_entry.entry_type == EntryType.ADJUSTING

    lines = reval_entry.lines
    assert len(lines) == 2

    # Verify debit on cash (appreciation of EUR asset)
    cash_line = next(l for l in lines if l.company_account_id == setup["c_eur_cash"].id)
    assert cash_line.debit_amount == Decimal("500.00")
    assert cash_line.credit_amount == Decimal("0.00")

    # Verify credit on gain account
    gain_line = next(l for l in lines if l.company_account_id == setup["c_fx_gain_loss"].id)
    assert gain_line.credit_amount == Decimal("500.00")
    assert gain_line.debit_amount == Decimal("0.00")
