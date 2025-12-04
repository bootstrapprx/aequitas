"""
Pydantic schemas for system settings.
"""
from pydantic import BaseModel
from datetime import datetime


class SystemSettingsBase(BaseModel):
    maintenance_mode: bool = False
    allow_public_signup: bool = False


class SystemSettingsCreate(SystemSettingsBase):
    pass


class SystemSettingsUpdate(BaseModel):
    maintenance_mode: bool | None = None
    allow_public_signup: bool | None = None


class SystemSettingsResponse(SystemSettingsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
