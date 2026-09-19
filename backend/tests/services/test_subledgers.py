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
from app.db.models.party import Party, PartyType
from app.db.models.ar_invoice import ARInvoice, ARInvoiceLine, ARInvoiceStatus, ARPayment
from app.db.models.ap_bill import APBill, APBillLine, APBillStatus, APPayment
from app.db.models.fiscal_period import FiscalPeriod, PeriodType, PeriodStatus
from app.db.models.company_account import CompanyAccount
from app.db.models.master_account import MasterAccount
from app.db.models.enums import AccountType, NormalBalance
from app.services.ar_service import ARService
from app.services.ap_service import APService


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
def ar_ap_setup(db_session):
    u = User(id=uuid4(), email="clerk@example.com", is_active=True)
    c = Company(id=uuid4(), name="Operations Corp", ucid=str(uuid4()), is_active=True)
    p = FiscalPeriod(
        id=uuid4(),
        company_id=c.id,
        period_type=PeriodType.MONTH,
        period_number=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        status=PeriodStatus.OPEN,
    )

    # Master Accounts
    m_cash = MasterAccount(id=uuid4(), code="10000", description="Cash", category="ASSET", normal_balance="Debit", type="D", level=1, version=1, start_date=date(2025, 1, 1))
    m_ar = MasterAccount(id=uuid4(), code="12000", description="Accounts Receivable", category="ASSET", normal_balance="Debit", type="D", level=1, version=1, start_date=date(2025, 1, 1))
    m_ap = MasterAccount(id=uuid4(), code="20000", description="Accounts Payable", category="LIABILITY", normal_balance="Credit", type="D", level=1, version=1, start_date=date(2025, 1, 1))
    m_rev = MasterAccount(id=uuid4(), code="40000", description="Service Revenue", category="REVENUE", normal_balance="Credit", type="D", level=1, version=1, start_date=date(2025, 1, 1))
    m_exp = MasterAccount(id=uuid4(), code="60000", description="Software Subscriptions", category="EXPENSE", normal_balance="Debit", type="D", level=1, version=1, start_date=date(2025, 1, 1))
    db_session.add_all([u, c, p, m_cash, m_ar, m_ap, m_rev, m_exp])

    # Company Accounts
    c_cash = CompanyAccount(id=uuid4(), company_id=c.id, code="10000", description="Cash", account_type=AccountType.ASSET, type="D", normal_balance=NormalBalance.DEBIT, mapped_master_account_id=m_cash.id, is_active=True)
    c_ar = CompanyAccount(id=uuid4(), company_id=c.id, code="12000", description="A/R", account_type=AccountType.ASSET, type="D", normal_balance=NormalBalance.DEBIT, mapped_master_account_id=m_ar.id, is_active=True)
    c_ap = CompanyAccount(id=uuid4(), company_id=c.id, code="20000", description="A/P", account_type=AccountType.LIABILITY, type="D", normal_balance=NormalBalance.CREDIT, mapped_master_account_id=m_ap.id, is_active=True)
    c_rev = CompanyAccount(id=uuid4(), company_id=c.id, code="40000", description="Revenue", account_type=AccountType.REVENUE, type="D", normal_balance=NormalBalance.CREDIT, mapped_master_account_id=m_rev.id, is_active=True)
    c_exp = CompanyAccount(id=uuid4(), company_id=c.id, code="60000", description="Expense", account_type=AccountType.EXPENSE, type="D", normal_balance=NormalBalance.DEBIT, mapped_master_account_id=m_exp.id, is_active=True)
    db_session.add_all([c_cash, c_ar, c_ap, c_rev, c_exp])

    # Parties
    customer = Party(id=uuid4(), company_id=c.id, name="Acme Client", party_type=PartyType.CUSTOMER, email="billing@acme.com")
    vendor = Party(id=uuid4(), company_id=c.id, name="Cloud Hosting LLC", party_type=PartyType.VENDOR, is_1099_eligible=True)
    db_session.add_all([customer, vendor])
    db_session.commit()

    return {
        "user": u,
        "company": c,
        "period": p,
        "customer": customer,
        "vendor": vendor,
        "c_cash": c_cash,
        "c_ar": c_ar,
        "c_ap": c_ap,
        "c_rev": c_rev,
        "c_exp": c_exp,
    }


def test_ar_invoice_creation_and_settlement(db_session, ar_ap_setup):
    setup = ar_ap_setup
    ar_service = ARService(db_session)

    # 1. Create & Post Customer Invoice for $2,500
    invoice = ar_service.create_invoice(
        company_id=setup["company"].id,
        customer_id=setup["customer"].id,
        fiscal_period_id=setup["period"].id,
        invoice_date=date(2026, 1, 10),
        due_date=date(2026, 2, 10),
        user_id=setup["user"].id,
        lines=[{
            "description": "Monthly Consulting",
            "revenue_account_id": setup["c_rev"].id,
            "amount": Decimal("2500.00"),
        }]
    )

    assert invoice is not None
    assert invoice.status == ARInvoiceStatus.POSTED
    assert invoice.total_amount == Decimal("2500.00")
    assert invoice.amount_due == Decimal("2500.00")
    assert invoice.journal_entry_id is not None

    # Verify posted GL lines: Debit AR 2500, Credit Revenue 2500
    je_lines = invoice.journal_entry.lines
    ar_line = next(l for l in je_lines if l.company_account_id == setup["c_ar"].id)
    assert ar_line.debit_amount == Decimal("2500.00")

    # 2. Receive Partial Payment $1,000
    payment = ar_service.apply_payment(
        invoice_id=invoice.id,
        payment_date=date(2026, 1, 20),
        amount=Decimal("1000.00"),
        cash_account_id=setup["c_cash"].id,
        user_id=setup["user"].id,
    )

    assert invoice.amount_due == Decimal("1500.00")
    assert invoice.status == ARInvoiceStatus.PARTIALLY_PAID
    assert payment.journal_entry_id is not None


def test_ap_bill_creation_and_payment(db_session, ar_ap_setup):
    setup = ar_ap_setup
    ap_service = APService(db_session)

    # 1. Create & Post Vendor Bill for $800
    bill = ap_service.create_bill(
        company_id=setup["company"].id,
        vendor_id=setup["vendor"].id,
        fiscal_period_id=setup["period"].id,
        bill_date=date(2026, 1, 5),
        due_date=date(2026, 2, 5),
        user_id=setup["user"].id,
        lines=[{
            "description": "Cloud Servers",
            "expense_account_id": setup["c_exp"].id,
            "amount": Decimal("800.00"),
        }]
    )

    assert bill is not None
    assert bill.status == APBillStatus.POSTED
    assert bill.total_amount == Decimal("800.00")
    assert bill.amount_due == Decimal("800.00")

    # 2. Pay bill in full
    payment = ap_service.pay_bill(
        bill_id=bill.id,
        payment_date=date(2026, 1, 25),
        amount=Decimal("800.00"),
        cash_account_id=setup["c_cash"].id,
        user_id=setup["user"].id,
    )

    assert bill.amount_due == Decimal("0.00")
    assert bill.status == APBillStatus.PAID
    assert payment.journal_entry_id is not None
