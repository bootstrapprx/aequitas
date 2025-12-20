
import enum
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid

class ModuleType(str, enum.Enum):
    ACCOUNTING = "ACCOUNTING"
    FISCAL = "FISCAL"
    INVOICING = "INVOICING"
    CONTRACTS = "CONTRACTS"
    INVENTORY = "INVENTORY"
    PAYROLL = "PAYROLL"

class CompanyModule(Base):
    __tablename__ = "company_modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(Enum(ModuleType), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    config = Column(JSON, nullable=True)

    company = relationship("Company", back_populates="modules")
