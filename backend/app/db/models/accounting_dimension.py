import uuid
import enum
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base

class DimensionType(str, enum.Enum):
    DEPARTMENT = "DEPARTMENT"
    COST_CENTER = "COST_CENTER"
    PROJECT = "PROJECT"
    LOCATION = "LOCATION"

class AccountingDimension(Base):
    """
    SQLAlchemy model for accounting dimensions.
    Allows for line-level tagging across Journal Entries (e.g. by Department, Cost Center).
    """
    __tablename__ = "accounting_dimensions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)

    dimension_type = Column(SQLEnum(DimensionType, name="dimensiontype"), nullable=False)
    name = Column(String, nullable=False)
    code = Column(String, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    company = relationship("Company")

    def __repr__(self):
        return f"<AccountingDimension(id='{self.id}', type='{self.dimension_type.value}', name='{self.name}')>"
