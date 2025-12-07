import uuid
from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class GroupCompanyMember(Base):
    __tablename__ = "group_company_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_company_id = Column(UUID(as_uuid=True), ForeignKey("group_companies.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)

    group = relationship("GroupCompany", back_populates="members")
    company = relationship("Company")

    __table_args__ = (
        UniqueConstraint('group_company_id', 'company_id', name='uq_group_company_member'),
    )

    def __repr__(self):
        return f"<GroupCompanyMember(group_id='{self.group_company_id}', company_id='{self.company_id}')>"
