import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models.master_account import MasterAccount
from app.db.models.chart_template import ChartTemplate, ChartTemplateAccount
from app.data.seed_chart_templates import (
    MANDATORY_L0_CODES,
    seed_templates,
)


def build_master_account(
    code: str,
    category: str,
    account_type: str = "D",
    level: int = 2,
    parent_code: str | None = None,
) -> MasterAccount:
    """Factory for test master accounts."""
    return MasterAccount(
        code=code,
        description=f"{category} {code}",
        start_date=date(2024, 1, 1),
        end_date=None,
        type=account_type,
        level=level,
        category=category,
        notes=None,
        parent_code=parent_code,
        version="test",
    )


def seed_master_chart(db):
    """Populate a synthetic but complete master chart for tests."""
    # Required L0 accounts (mapped to appropriate categories)
    category_map = {
        "10000": "Asset",
        "10100": "Asset",
        "12000": "Asset",
        "14000": "Asset",
        "15000": "Asset",
        "15900": "Asset",
        "20000": "Liability",
        "21000": "Liability",
        "22000": "Liability",
        "23000": "Liability",
        "30000": "Equity",
        "32000": "Equity",
        "39999": "Equity",
        "40000": "Revenue",
        "49000": "Revenue",
        "50000": "Cost of Goods Sold",
        "60000": "Expense",
        "61000": "Expense",
        "62000": "Expense",
        "69000": "Expense",
    }

    for code, category in category_map.items():
        db.add(build_master_account(code=code, category=category, level=1 if code.endswith("0000") else 2))

    # Additional accounts per category to satisfy kernel caps
    generation_plan = {
        "Asset": (11000, 55),
        "Liability": (21050, 30),
        "Equity": (31050, 22),
        "Revenue": (41000, 18),
        "Cost of Goods Sold": (51000, 24),
        "Expense": (61050, 45),
    }

    used_codes = set(MANDATORY_L0_CODES)
    for category, (start_code, total) in generation_plan.items():
        code = start_code
        created = 0
        while created < total:
            code_str = f"{code:05d}"
            code += 1
            if code_str in used_codes:
                continue
            used_codes.add(code_str)
            db.add(build_master_account(code=code_str, category=category))
            created += 1

    db.flush()


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(
        bind=engine,
        tables=[MasterAccount.__table__, ChartTemplate.__table__, ChartTemplateAccount.__table__],
    )
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(
            bind=engine,
            tables=[MasterAccount.__table__, ChartTemplate.__table__, ChartTemplateAccount.__table__],
        )


def test_us_gaap_standard_seeds_minimum_accounts(db_session):
    seed_master_chart(db_session)
    counts = seed_templates(db_session)
    db_session.commit()

    standard = db_session.query(ChartTemplate).filter(ChartTemplate.name == "US GAAP Standard").one()
    assert counts["US_GAAP_STANDARD"] >= 130
    assert len(standard.accounts) == counts["US_GAAP_STANDARD"]


def test_simplified_kernel_collapses_but_remains_complete(db_session):
    seed_master_chart(db_session)
    counts = seed_templates(db_session)
    db_session.commit()

    simplified = db_session.query(ChartTemplate).filter(ChartTemplate.name == "US GAAP Simplified").one()
    standard_count = counts["US_GAAP_STANDARD"]
    simplified_count = counts["US_GAAP_SIMPLIFIED"]

    assert simplified_count >= 40
    assert simplified_count < standard_count


def test_equity_and_system_accounts_present_in_templates(db_session):
    seed_master_chart(db_session)
    seed_templates(db_session)
    db_session.commit()

    templates = db_session.query(ChartTemplate).filter(ChartTemplate.name.in_(["US GAAP Standard", "US GAAP Simplified"])).all()
    for template in templates:
        codes = {acct.code for acct in template.accounts}
        assert "32000" in codes
        assert "39999" in codes
        assert any(acct.master_account.category == "Equity" for acct in template.accounts)


def test_ifrs_template_is_not_selectable(db_session):
    seed_master_chart(db_session)
    seed_templates(db_session)
    db_session.commit()

    active_ifrs = db_session.query(ChartTemplate).filter(
        ChartTemplate.jurisdiction == "INTL", ChartTemplate.is_active == True  # noqa: E712
    ).all()
    assert active_ifrs == []
