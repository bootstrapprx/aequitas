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
from app.db.models.group_company import GroupCompany
from app.db.models.group_company_member import GroupCompanyMember
from app.db.models.fiscal_period import FiscalPeriod, PeriodType, PeriodStatus
from app.db.models.company_account import CompanyAccount
from app.db.models.master_account import MasterAccount
from app.db.models.enums import AccountType, NormalBalance, EntryStatus, EntryType
from app.db.models.journal_entry import JournalEntry
from app.db.models.journal_entry_line import JournalEntryLine
from app.services.intercompany_service import IntercompanyService
from app.services.consolidation_financial_service import ConsolidationFinancialService


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
def intercompany_setup(db_session):
    u = User(id=uuid4(), email="cfo@example.com", is_active=True)
    
    # Parent and Sub companies
    parent = Company(id=uuid4(), name="HoldCo", ucid=str(uuid4()), is_active=True)
    sub = Company(id=uuid4(), name="SubCo", ucid=str(uuid4()), is_active=True)
    db_session.add_all([u, parent, sub])
    db_session.flush()

    group = GroupCompany(id=uuid4(), name="Consolidated Group", owner_user_id=u.id)
    db_session.add(group)
    db_session.flush()

    m1 = GroupCompanyMember(id=uuid4(), group_company_id=group.id, company_id=parent.id)
    m2 = GroupCompanyMember(id=uuid4(), group_company_id=group.id, company_id=sub.id)
    db_session.add_all([m1, m2])

    # Periods
    p_parent = FiscalPeriod(id=uuid4(), company_id=parent.id, period_type=PeriodType.MONTH, period_number=1, start_date=date(2026, 1, 1), end_date=date(2026, 1, 31), status=PeriodStatus.OPEN)
    p_sub = FiscalPeriod(id=uuid4(), company_id=sub.id, period_type=PeriodType.MONTH, period_number=1, start_date=date(2026, 1, 1), end_date=date(2026, 1, 31), status=PeriodStatus.OPEN)
    db_session.add_all([p_parent, p_sub])

    # Master Accounts
    m_cash = MasterAccount(id=uuid4(), code="10000", description="Cash", category="ASSET", normal_balance="Debit", type="D", level=1, version=1, start_date=date(2025, 1, 1))
    m_due_from = MasterAccount(id=uuid4(), code="13000", description="Due From Affiliates", category="ASSET", normal_balance="Debit", type="D", level=1, version=1, start_date=date(2025, 1, 1))
    m_due_to = MasterAccount(id=uuid4(), code="23000", description="Due To Affiliates", category="LIABILITY", normal_balance="Credit", type="D", level=1, version=1, start_date=date(2025, 1, 1))
    m_rev = MasterAccount(id=uuid4(), code="40000", description="Revenue", category="REVENUE", normal_balance="Credit", type="D", level=1, version=1, start_date=date(2025, 1, 1), fs_mapping="Income Statement")
    m_exp = MasterAccount(id=uuid4(), code="60000", description="Expense", category="EXPENSE", normal_balance="Debit", type="D", level=1, version=1, start_date=date(2025, 1, 1), fs_mapping="Income Statement")
    db_session.add_all([m_cash, m_due_from, m_due_to, m_rev, m_exp])

    # Parent Accounts
    c_p_cash = CompanyAccount(id=uuid4(), company_id=parent.id, code="10000", description="Cash", account_type=AccountType.ASSET, type="D", normal_balance=NormalBalance.DEBIT, mapped_master_account_id=m_cash.id, is_active=True)
    c_p_due_from = CompanyAccount(id=uuid4(), company_id=parent.id, code="13000", description="Due From Sub", account_type=AccountType.ASSET, type="D", normal_balance=NormalBalance.DEBIT, mapped_master_account_id=m_due_from.id, is_active=True)
    c_p_rev = CompanyAccount(id=uuid4(), company_id=parent.id, code="40000", description="Management Fees", account_type=AccountType.REVENUE, type="D", normal_balance=NormalBalance.CREDIT, mapped_master_account_id=m_rev.id, is_active=True)

    # Sub Accounts
    c_s_cash = CompanyAccount(id=uuid4(), company_id=sub.id, code="10000", description="Cash", account_type=AccountType.ASSET, type="D", normal_balance=NormalBalance.DEBIT, mapped_master_account_id=m_cash.id, is_active=True)
    c_s_due_to = CompanyAccount(id=uuid4(), company_id=sub.id, code="23000", description="Due To Parent", account_type=AccountType.LIABILITY, type="D", normal_balance=NormalBalance.CREDIT, mapped_master_account_id=m_due_to.id, is_active=True)
    c_s_exp = CompanyAccount(id=uuid4(), company_id=sub.id, code="60000", description="Management Fee Expense", account_type=AccountType.EXPENSE, type="D", normal_balance=NormalBalance.DEBIT, mapped_master_account_id=m_exp.id, is_active=True)

    db_session.add_all([c_p_cash, c_p_due_from, c_p_rev, c_s_cash, c_s_due_to, c_s_exp])
    db_session.commit()

    return {
        "user": u,
        "group": group,
        "parent": parent,
        "sub": sub,
        "p_parent": p_parent,
        "p_sub": p_sub,
        "c_p_due_from": c_p_due_from,
        "c_p_rev": c_p_rev,
        "c_s_due_to": c_s_due_to,
        "c_s_exp": c_s_exp,
    }


def test_intercompany_paired_journal_entries_and_elimination(db_session, intercompany_setup):
    setup = intercompany_setup
    ic_service = IntercompanyService(db_session)
    consol_service = ConsolidationFinancialService(db_session)

    # 1. Post Paired Intercompany Charge: Parent bills Sub $5,000 management fee
    paired_result = ic_service.create_paired_intercompany_entry(
        from_company_id=setup["parent"].id,
        to_company_id=setup["sub"].id,
        from_fiscal_period_id=setup["p_parent"].id,
        to_fiscal_period_id=setup["p_sub"].id,
        entry_date=date(2026, 1, 15),
        amount=Decimal("5000.00"),
        from_revenue_account_id=setup["c_p_rev"].id,
        to_expense_account_id=setup["c_s_exp"].id,
        user_id=setup["user"].id,
        description="Shared IT & Management Services",
    )

    assert paired_result["source_entry"].status == EntryStatus.POSTED
    assert paired_result["mirror_entry"].status == EntryStatus.POSTED

    # 2. Consolidated Income Statement Elimination
    # Standalone Parent Rev = 5000, Sub Exp = 5000.
    # Group Consolidated Rev & Exp should both be eliminated to 0.00
    consol_pnl = consol_service.generate_consolidated_income_statement(
        group_id=setup["group"].id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )

    assert consol_pnl["eliminated_intercompany_revenue"] == Decimal("5000.00")
    assert consol_pnl["eliminated_intercompany_expenses"] == Decimal("5000.00")
    assert consol_pnl["net_consolidated_income"] == Decimal("0.00")
