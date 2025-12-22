from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class Mapping(BaseModel):
    id: UUID
    company_account_id: UUID
    staging_account_id: Optional[UUID] = None
    master_code: Optional[str] = None
    confidence: float
    status: str
    mapping_status: Optional[str] = None
    decision_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
