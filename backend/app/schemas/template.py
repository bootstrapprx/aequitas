from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Any, Optional
from uuid import UUID

class TemplateBase(BaseModel):
    """Base Pydantic model for a CoA Template."""
    name: str
    version: Optional[str] = None
    data: Any

class TemplateCreate(TemplateBase):
    """Schema for creating a new template in the database."""
    pass

class Template(TemplateBase):
    """Schema for representing a template in API responses."""
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TemplateValidationResult(BaseModel):
    """Schema for the result of a template validation."""
    is_valid: bool
    errors: list[str] = []
    warnings: list[str] = []


class ChartTemplateSummary(BaseModel):
    """Lightweight schema for chart templates exposed to the onboarding UI."""
    id: UUID
    name: str
    jurisdiction: str
    version: str
    description: Optional[str] = None
    is_active: bool
    account_count: int = 0

    model_config = ConfigDict(from_attributes=True)
