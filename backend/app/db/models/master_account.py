import uuid
from sqlalchemy import Column, String, Date, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class MasterAccount(Base):
    """
    SQLAlchemy model for the Master Chart of Accounts.
    """
    __tablename__ = "master_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    type = Column(String(1), nullable=False)  # "H" for Header, "D" for Detail
    parent_code = Column(String, nullable=True)
    level = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    notes = Column(Text, nullable=True)

    parent_id = Column(UUID(as_uuid=True), ForeignKey("master_accounts.id"), nullable=True)
    
    # Self-referential relationship for parent-child hierarchy.
    # remote_side=[id] is necessary for SQLAlchemy to understand the self-join.
    parent = relationship("MasterAccount", remote_side=[id], back_populates="children")
    
    # cascade="all, delete-orphan" ensures that children are deleted when the parent is.
    children = relationship("MasterAccount", back_populates="parent", cascade="all, delete-orphan")

    company_accounts = relationship("CompanyAccount", back_populates="master_account")

    def __repr__(self):
        return f"<MasterAccount(code='{self.code}', description='{self.description}')>"

    def as_dict(self):
       """Return object data in easily serializable format"""
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}