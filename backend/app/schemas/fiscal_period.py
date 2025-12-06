from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime
from uuid import UUID
from typing import Optional


class FiscalPeriodBase(BaseModel):
    """Base schema for fiscal period"""
    period_type: str = Field(..., description="Type of period: month, quarter, year")
    period_number: str = Field(..., description="Period identifier (e.g., '2024-01', '2024-Q1', '2024')")
    start_date: date = Field(..., description="Period start date")
    end_date: date = Field(..., description="Period end date")
    status: str = Field(default="open", description="Period status: open, closed, locked")


class FiscalPeriodCreate(FiscalPeriodBase):
    """Schema for creating a fiscal period"""
    company_id: UUID = Field(..., description="Company ID")


class FiscalPeriodUpdate(BaseModel):
    """Schema for updating a fiscal period"""
    status: Optional[str] = Field(None, description="Update period status")


class FiscalPeriodInDB(FiscalPeriodBase):
    """Schema for fiscal period in database"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    closed_at: Optional[datetime] = None
    closed_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class FiscalPeriodResponse(FiscalPeriodInDB):
    """Schema for fiscal period API response"""
    pass


class FiscalPeriodClose(BaseModel):
    """Schema for closing a fiscal period"""
    closed_by: UUID = Field(..., description="User ID who is closing the period")
