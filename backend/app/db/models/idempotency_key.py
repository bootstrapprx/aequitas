import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base


class IdempotencyStatus(str, enum.Enum):
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    FAILED = "failed"


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True)
    endpoint = Column(String, nullable=False)
    key = Column(String, nullable=False)
    status = Column(String, nullable=False, default=IdempotencyStatus.ACCEPTED.value)
    response_body = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "endpoint", "key", name="uq_idempotency_company_endpoint_key"),
    )
