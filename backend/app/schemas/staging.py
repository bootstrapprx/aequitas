from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel


class StagingAccount(BaseModel):
    id: UUID
    company_id: UUID
    source_account_id: str
    name: Optional[str] = None
    validation_status: Optional[str] = None
    validation_errors: Optional[List[Any]] = None
    normalized_payload: Optional[dict] = None
    mapping_status: Optional[str] = None
    processed: bool
    processing_result: Optional[str] = None
    processed_at: Optional[datetime] = None
    imported_at: datetime

    class Config:
        orm_mode = True


class StagingProcessRequest(BaseModel):
    company_id: UUID
    limit: Optional[int] = 100


class StagingProcessResponse(BaseModel):
    run_id: str
    processed: int
