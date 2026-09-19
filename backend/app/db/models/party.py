import uuid
import enum
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class PartyType(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    VENDOR = "VENDOR"
    EMPLOYEE = "EMPLOYEE"


class Party(Base):
    """
    SQLAlchemy model for counterparties (Customers, Vendors, Employees).
    """
    __tablename__ = "parties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)

    party_type = Column(SQLEnum(PartyType, name="partytype"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    tax_id = Column(String, nullable=True)

    is_1099_eligible = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    company = relationship("Company")

    def __repr__(self):
        return f"<Party(name='{self.name}', type='{self.party_type.value}')>"
