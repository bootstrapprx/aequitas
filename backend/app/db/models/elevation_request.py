import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum

class ElevationStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class ElevationRequest(Base):
    __tablename__ = "elevation_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    requested_role = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    status = Column(String, default=ElevationStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(String, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="elevation_requests")
    reviewer = relationship("User", foreign_keys=[reviewed_by_id])

    def __repr__(self):
        return f"<ElevationRequest(user='{self.user_id}', role='{self.requested_role}', status='{self.status}')>"
