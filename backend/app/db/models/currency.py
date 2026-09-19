import uuid
import enum
from sqlalchemy import Column, String, Integer, Boolean, Date, Numeric, Enum as SQLEnum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class RateType(str, enum.Enum):
    SPOT = "SPOT"
    AVERAGE = "AVERAGE"
    CLOSING = "CLOSING"
    HISTORICAL = "HISTORICAL"


class Currency(Base):
    """
    SQLAlchemy model for currencies.
    """
    __tablename__ = "currencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(3), unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    symbol = Column(String, nullable=True)
    decimals = Column(Integer, default=2, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Currency(code='{self.code}', name='{self.name}')>"


class ExchangeRate(Base):
    """
    SQLAlchemy model for exchange rates.
    """
    __tablename__ = "exchange_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_currency = Column(String(3), ForeignKey("currencies.code"), nullable=False, index=True)
    to_currency = Column(String(3), ForeignKey("currencies.code"), nullable=False, index=True)
    rate_date = Column(Date, nullable=False, index=True)
    rate_type = Column(SQLEnum(RateType, name="ratetype"), default=RateType.SPOT, nullable=False)
    rate = Column(Numeric(18, 6), nullable=False)

    __table_args__ = (
        UniqueConstraint("from_currency", "to_currency", "rate_date", "rate_type", name="uq_fx_rate_pair_date_type"),
    )

    def __repr__(self):
        return f"<ExchangeRate({self.from_currency}->{self.to_currency} on {self.rate_date}: {self.rate})>"
