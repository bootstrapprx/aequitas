from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class MasterAccountSummary(BaseModel):
    id: Optional[UUID]
    code: Optional[str]
    description: Optional[str] = None

    class Config:
        orm_mode = True


class CompanyAccountSummary(BaseModel):
    id: UUID
    code: str
    name: Optional[str] = None
    description: Optional[str] = None

    class Config:
        orm_mode = True


class MappingDecisionResponse(BaseModel):
    id: UUID
    company_account: CompanyAccountSummary
    master_account: Optional[MasterAccountSummary]
    confidence: float
    mapping_status: Optional[str]
    decision_status: str
    decision_reason: Optional[str] = None
    decided_at: Optional[datetime] = None
    decided_by: Optional[UUID] = None
    status: str
    notes: Optional[str] = None

    class Config:
        orm_mode = True


class MappingDecisionRequest(BaseModel):
    reason: str


class MappingOverrideRequest(BaseModel):
    reason: str
    master_account_id: UUID
