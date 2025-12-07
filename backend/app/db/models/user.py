import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_uid = Column(String, unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(String, default="USER") # USER, ACCOUNTANT, ADMIN, SU
    preferred_company_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to companies (many-to-many through UserCompany)
    user_companies = relationship("UserCompany", back_populates="user", cascade="all, delete-orphan")

    # Relationship to owned groups
    owned_groups = relationship("GroupCompany", back_populates="owner")

    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}')>"
    
    def has_access_to_company(self, company_id: uuid.UUID) -> bool:
        """Check if user has access to a specific company."""
        return any(uc.company_id == company_id for uc in self.user_companies)
    
    def get_company_ids(self) -> list[uuid.UUID]:
        """Get list of company IDs the user has access to."""
        return [uc.company_id for uc in self.user_companies]

