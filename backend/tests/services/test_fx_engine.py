import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.company import Company
from app.db.models.currency import Currency, ExchangeRate, RateType
from app.services.fx_rate_service import FxRateService


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


def test_currency_and_exchange_rates(db_session):
    c_usd = Currency(code="USD", name="US Dollar", symbol="$", decimals=2, is_active=True)
    c_eur = Currency(code="EUR", name="Euro", symbol="€", decimals=2, is_active=True)
    c_gbp = Currency(code="GBP", name="British Pound", symbol="£", decimals=2, is_active=True)

    db_session.add_all([c_usd, c_eur, c_gbp])
    db_session.commit()

    fx_service = FxRateService(db_session)

    # Add Rates for 2026-01-15
    fx_service.set_rate(
        from_currency="EUR",
        to_currency="USD",
        rate=Decimal("1.0850"),
        rate_date=date(2026, 1, 15),
        rate_type=RateType.SPOT
    )
    fx_service.set_rate(
        from_currency="GBP",
        to_currency="USD",
        rate=Decimal("1.2700"),
        rate_date=date(2026, 1, 15),
        rate_type=RateType.SPOT
    )

    # Direct Lookup
    rate_eur = fx_service.get_rate("EUR", "USD", date(2026, 1, 15))
    assert rate_eur == Decimal("1.0850")

    # Same Currency Identity
    rate_same = fx_service.get_rate("USD", "USD", date(2026, 1, 15))
    assert rate_same == Decimal("1.0000")

    # Inverse Rate Calculation
    rate_inv = fx_service.get_rate("USD", "EUR", date(2026, 1, 15))
    expected_inv = Decimal("1.0000") / Decimal("1.0850")
    assert round(rate_inv, 4) == round(expected_inv, 4)

    # Conversion helper
    converted = fx_service.convert_amount(
        amount=Decimal("1000.00"),
        from_currency="EUR",
        to_currency="USD",
        rate_date=date(2026, 1, 15)
    )
    assert converted == Decimal("1085.00")
