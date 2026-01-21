from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel
from app.db.models.enums import KernelLayer


class KernelL0CoreMetricsResponse(BaseModel):
    company_id: UUID
    fiscal_period_id: UUID
    period_start: date
    period_end: date

    total_cash: Decimal
    net_revenue: Decimal
    operating_income: Decimal
    net_working_capital: Decimal
    current_ratio: Optional[Decimal] = None

    total_cash_delta: Optional[Decimal] = None
    net_revenue_delta: Optional[Decimal] = None
    operating_income_delta: Optional[Decimal] = None
    net_working_capital_delta: Optional[Decimal] = None
    current_ratio_delta: Optional[Decimal] = None


class KernelLayerStatus(BaseModel):
    layer: KernelLayer
    state: str  # implemented | placeholder


class KernelLayerBindingsResponse(BaseModel):
    company_id: UUID
    kernel_version: Optional[str] = None
    kernel_layer: Optional[KernelLayer] = None
    layers: List[KernelLayerStatus]
