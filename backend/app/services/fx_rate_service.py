from decimal import Decimal
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.db.models.currency import Currency, ExchangeRate, RateType


class FxRateService:
    """Service for managing foreign exchange rates and conversions."""

    def __init__(self, db: Session):
        self.db = db

    def set_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate: Decimal,
        rate_date: date,
        rate_type: RateType = RateType.SPOT,
    ) -> ExchangeRate:
        """Create or update an exchange rate."""
        from_curr = from_currency.upper()
        to_curr = to_currency.upper()

        existing = self.db.query(ExchangeRate).filter(
            ExchangeRate.from_currency == from_curr,
            ExchangeRate.to_currency == to_curr,
            ExchangeRate.rate_date == rate_date,
            ExchangeRate.rate_type == rate_type,
        ).first()

        if existing:
            existing.rate = rate
            self.db.commit()
            self.db.refresh(existing)
            return existing

        new_rate = ExchangeRate(
            from_currency=from_curr,
            to_currency=to_curr,
            rate=rate,
            rate_date=rate_date,
            rate_type=rate_type,
        )
        self.db.add(new_rate)
        self.db.commit()
        self.db.refresh(new_rate)
        return new_rate

    def get_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate_date: date,
        rate_type: RateType = RateType.SPOT,
    ) -> Decimal:
        """Get the exchange rate between two currencies for a specific date."""
        from_curr = from_currency.upper()
        to_curr = to_currency.upper()

        if from_curr == to_curr:
            return Decimal("1.0000")

        # Direct rate
        rate_obj = self.db.query(ExchangeRate).filter(
            ExchangeRate.from_currency == from_curr,
            ExchangeRate.to_currency == to_curr,
            ExchangeRate.rate_date <= rate_date,
            ExchangeRate.rate_type == rate_type,
        ).order_by(desc(ExchangeRate.rate_date)).first()

        if rate_obj:
            return Decimal(str(rate_obj.rate))

        # Inverse rate
        inv_rate_obj = self.db.query(ExchangeRate).filter(
            ExchangeRate.from_currency == to_curr,
            ExchangeRate.to_currency == from_curr,
            ExchangeRate.rate_date <= rate_date,
            ExchangeRate.rate_type == rate_type,
        ).order_by(desc(ExchangeRate.rate_date)).first()

        if inv_rate_obj and inv_rate_obj.rate > 0:
            return Decimal("1.0000") / Decimal(str(inv_rate_obj.rate))

        raise ValueError(f"No exchange rate found for {from_curr}/{to_curr} on or before {rate_date}")

    def convert_amount(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        rate_date: date,
        rate_type: RateType = RateType.SPOT,
    ) -> Decimal:
        """Convert an amount from one currency to another."""
        rate = self.get_rate(from_currency, to_currency, rate_date, rate_type)
        return round(amount * rate, 2)
