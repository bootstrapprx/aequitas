"""
Pending Registration model for storing registration data before payment confirmation.
"""
import uuid
import secrets
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class PendingRegistration(Base):
    """
    Stores pending registrations awaiting payment confirmation.
    
    For paid registration flows, user data is stored here temporarily
    until the payment is confirmed via Stripe webhook or manual confirmation.
    """
    __tablename__ = "pending_registrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User data (stored temporarily)
    email = Column(String, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    
    # Company data
    company_name = Column(String, nullable=False)
    
    # Plan selection
    plan = Column(String, default="starter", nullable=False)  # starter, pro
    
    # Confirmation token (secure random token for confirmation URL)
    token = Column(String, unique=True, nullable=False, index=True)
    
    # Stripe session ID (for webhook matching)
    stripe_session_id = Column(String, nullable=True, index=True)
    
    # Metadata stored as JSON string (for flexibility)
    metadata_json = Column(Text, nullable=True)
    
    # Expiry and timestamps
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    @classmethod
    def generate_token(cls) -> str:
        """Generate a secure random token for registration confirmation."""
        return secrets.token_urlsafe(32)
    
    @classmethod
    def default_expiry(cls) -> datetime:
        """Default expiry is 24 hours from now."""
        return datetime.utcnow() + timedelta(hours=24)
    
    @property
    def is_expired(self) -> bool:
        """Check if the pending registration has expired."""
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f"<PendingRegistration(email='{self.email}', plan='{self.plan}', expires_at='{self.expires_at}')>"
