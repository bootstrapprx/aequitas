"""
System settings model for global application configuration.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, DateTime
from app.db.base import Base


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    maintenance_mode = Column(Boolean, default=False, nullable=False)
    allow_public_signup = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SystemSettings(maintenance_mode={self.maintenance_mode}, allow_public_signup={self.allow_public_signup})>"
