from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel

from app.schemas.company import CompanyResponse


class GroupCompanyBase(BaseModel):
    name: str
    description: Optional[str] = None


class GroupCompanyCreate(GroupCompanyBase):
    pass


class GroupCompanyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class GroupCompanyResponse(GroupCompanyBase):
    id: UUID
    owner_user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GroupCompanyWithMembers(GroupCompanyResponse):
    companies: List[CompanyResponse] = []

    class Config:
        from_attributes = True


class AddCompanyToGroupRequest(BaseModel):
    company_id: UUID


class PropagateM appingsRequest(BaseModel):
    source_company_id: UUID
    target_company_id: Optional[UUID] = None
    force: bool = False


class PropagateMappingsResponse(BaseModel):
    source_company_id: str
    target_companies: int
    source_mappings: int
    created: int
    updated: int
    skipped: int


class SUCreateCompanyRequest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    tax_id: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    group_company_id: Optional[UUID] = None
