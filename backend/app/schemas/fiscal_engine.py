"""
Pydantic schemas for the Fiscal Engine.
"""
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field
from decimal import Decimal


# ===== EntityTaxProfile Schemas =====

class EntityTaxProfileBase(BaseModel):
    """Base schema for entity tax profile"""
    entity_type: str = "LLC"
    tax_regime: str = "PASS_THROUGH"
    accounting_method: Optional[str] = None
    fiscal_year_start: Optional[date] = None
    jurisdictions: List[str] = Field(default_factory=list)
    elections: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class EntityTaxProfileCreate(EntityTaxProfileBase):
    """Schema for creating entity tax profile"""
    company_id: UUID


class EntityTaxProfileUpdate(BaseModel):
    """Schema for updating entity tax profile"""
    entity_type: Optional[str] = None
    tax_regime: Optional[str] = None
    accounting_method: Optional[str] = None
    fiscal_year_start: Optional[date] = None
    jurisdictions: Optional[List[str]] = None
    elections: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class EntityTaxProfileResponse(EntityTaxProfileBase):
    """Schema for entity tax profile response"""
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== TaxRuleset Schemas =====

class TaxRulesetBase(BaseModel):
    """Base schema for tax ruleset"""
    version: str
    scope: str
    jurisdiction: Optional[str] = None
    status: str = "ACTIVE"
    rules: List[Dict[str, Any]] = Field(default_factory=list)


class TaxRulesetCreate(TaxRulesetBase):
    """Schema for creating tax ruleset"""
    pass


class TaxRulesetResponse(TaxRulesetBase):
    """Schema for tax ruleset response"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== TaxRun Schemas =====

class TaxRunRequest(BaseModel):
    """Schema for requesting a tax run"""
    company_id: Optional[UUID] = None  # null for consolidated
    period_start: date
    period_end: date
    as_of_date: Optional[date] = None
    ruleset_version: str = "2025.1"


class TaxRunConsolidatedRequest(BaseModel):
    """Schema for requesting a consolidated tax run"""
    company_ids: List[UUID]
    period_start: date
    period_end: date
    as_of_date: Optional[date] = None
    ruleset_version: str = "2025.1"


class TaxRunResponse(BaseModel):
    """Schema for tax run response"""
    id: UUID
    company_id: Optional[UUID]
    period_start: date
    period_end: date
    as_of_date: Optional[date]
    ruleset_id: UUID
    ruleset_version: str
    engine_version: str
    inputs_hash: str
    status: str
    confidence_score: int
    missing_inputs: List[str]
    label: str
    created_at: datetime

    class Config:
        from_attributes = True


# ===== TaxFact Schemas =====

class TaxFactResponse(BaseModel):
    """Schema for tax fact response"""
    id: UUID
    tax_run_id: UUID
    company_id: UUID
    period_start: date
    period_end: date
    account_id: Optional[UUID]
    account_code: str
    account_name: str
    amount: Decimal
    tax_tags: List[str]
    source: str
    source_trace: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ===== TaxAdjustment Schemas =====

class TaxAdjustmentResponse(BaseModel):
    """Schema for tax adjustment response"""
    id: UUID
    tax_run_id: UUID
    company_id: UUID
    tax_type: str
    adjustment_type: str
    amount: Decimal
    rule_id: str
    reason: str
    source_fact_ids: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ===== TaxPosition Schemas =====

class TaxPositionResponse(BaseModel):
    """Schema for tax position response"""
    id: UUID
    tax_run_id: UUID
    company_id: Optional[UUID]
    tax_type: str
    taxable_income_estimated: Decimal
    exposure_estimated: Optional[Decimal]
    currency: str
    confidence_score: int
    missing_inputs: List[str]
    top_drivers: List[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Tax Run Detail Response (includes facts, adjustments, position) =====

class TaxRunDetailResponse(TaxRunResponse):
    """Schema for detailed tax run response with facts, adjustments, and positions"""
    facts_summary: Dict[str, Any] = Field(default_factory=dict)  # {total_facts: 10, total_amount: 100000}
    adjustments_summary: Dict[str, Any] = Field(default_factory=dict)  # {total_adjustments: 3, total_amount: 5000}
    position: Optional[TaxPositionResponse] = None


# ===== Latest Position Query Response =====

class LatestPositionResponse(BaseModel):
    """Schema for latest position query response"""
    position: Optional[TaxPositionResponse]
    run: Optional[TaxRunResponse]
