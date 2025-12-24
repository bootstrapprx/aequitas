"""
Sandbox Schema Definitions (Zone D)

CANONICAL REFERENCE:
- Sandbox Engine Design (Authoritative)
- Canon IV: Intelligence Boundaries, Zone D

CRITICAL RULES:
- All schemas are for simulation only
- No writes to truth tables (Zone A)
- Tax liability = estimate, not accounting liability
- All projections are assumptions, not facts
"""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ============================================================================
# ENUMS
# ============================================================================

class ScenarioStatus(str, Enum):
    """Scenario lifecycle states"""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class ProjectionType(str, Enum):
    """Projection categories"""
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"
    CASHFLOW = "CASHFLOW"
    TAX_LIABILITY = "TAX_LIABILITY"


class ProjectionFrequency(str, Enum):
    """Recurrence patterns"""
    ONE_TIME = "ONE_TIME"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ANNUALLY = "ANNUALLY"


class TaxType(str, Enum):
    """Tax classification"""
    INCOME = "INCOME"
    PAYROLL = "PAYROLL"
    SALES = "SALES"
    VAT = "VAT"
    PROPERTY = "PROPERTY"
    OTHER = "OTHER"


class ConfidenceLevel(str, Enum):
    """Estimation confidence"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CashflowType(str, Enum):
    """Cashflow classification"""
    FINANCING = "FINANCING"
    INVESTMENT = "INVESTMENT"
    OPERATING = "OPERATING"


class BindingRuleType(str, Enum):
    """Binding relationship types"""
    DRIVES = "DRIVES"
    OFFSETS = "OFFSETS"
    CONSTRAINS = "CONSTRAINS"


# ============================================================================
# SCENARIO SCHEMAS
# ============================================================================

class ScenarioCreate(BaseModel):
    """Create new scenario"""
    company_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ScenarioUpdate(BaseModel):
    """Update scenario (DRAFT only)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class ScenarioClone(BaseModel):
    """Clone scenario request"""
    new_name: str = Field(..., min_length=1, max_length=255)


class ScenarioResponse(BaseModel):
    """Scenario response"""
    id: UUID
    company_id: UUID
    name: str
    description: Optional[str]
    status: ScenarioStatus
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    archived_by: Optional[UUID] = None

    # Counts (optional, for list views)
    projection_count: Optional[int] = None
    binding_count: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================================
# PROJECTION SCHEMAS
# ============================================================================

class ProjectionBase(BaseModel):
    """Base projection fields"""
    scenario_id: UUID
    type: ProjectionType
    name: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    frequency: ProjectionFrequency
    start_date: date
    end_date: Optional[date] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and v < values['start_date']:
            raise ValueError("end_date must be >= start_date")
        return v


class RevenueProjectionCreate(ProjectionBase):
    """Create revenue projection"""
    type: ProjectionType = Field(default=ProjectionType.REVENUE, const=True)

    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Revenue amount must be positive")
        return v


class ExpenseProjectionCreate(ProjectionBase):
    """Create expense projection"""
    type: ProjectionType = Field(default=ProjectionType.EXPENSE, const=True)
    expense_category: Optional[str] = Field(None, max_length=100)

    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Expense amount must be positive")
        return v


class CashflowProjectionCreate(ProjectionBase):
    """Create cashflow projection"""
    type: ProjectionType = Field(default=ProjectionType.CASHFLOW, const=True)
    cashflow_type: CashflowType
    event_date: Optional[date] = None  # For ONE_TIME events

    # Cashflow can be positive (inflow) or negative (outflow)
    amount: Decimal  # Override base constraint


class TaxLiabilityProjectionCreate(BaseModel):
    """Create tax liability projection (SIMULATION ONLY)"""
    scenario_id: UUID
    type: ProjectionType = Field(default=ProjectionType.TAX_LIABILITY, const=True)
    name: str = Field(..., min_length=1, max_length=255)

    # MANDATORY tax fields
    jurisdiction: str = Field(..., min_length=1, max_length=100)
    tax_type: TaxType
    calculation_basis: str = Field(..., min_length=1, max_length=200)
    assumed_rate: Decimal = Field(..., ge=0, le=1)

    # Amount (can be manually entered or auto-calculated)
    amount: Decimal = Field(..., ge=0)

    # Time period
    start_date: date
    end_date: date

    # MANDATORY assumptions
    assumptions: str = Field(..., min_length=1)
    confidence_level: ConfidenceLevel

    # Metadata
    currency: str = Field(default="USD", min_length=3, max_length=3)
    metadata: Optional[Dict[str, Any]] = None

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError("end_date must be >= start_date")
        return v


class ProjectionUpdate(BaseModel):
    """Update projection (DRAFT scenario only)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[Decimal] = Field(None, ge=0)
    frequency: Optional[ProjectionFrequency] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    metadata: Optional[Dict[str, Any]] = None

    # Tax-specific updates
    jurisdiction: Optional[str] = None
    tax_type: Optional[TaxType] = None
    calculation_basis: Optional[str] = None
    assumed_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    assumptions: Optional[str] = None
    confidence_level: Optional[ConfidenceLevel] = None


class ProjectionResponse(BaseModel):
    """Projection response with derived calculations"""
    id: UUID
    scenario_id: UUID
    type: ProjectionType
    name: str
    amount: Decimal
    currency: str
    frequency: ProjectionFrequency
    start_date: date
    end_date: Optional[date]

    # Derived fields (calculated on read)
    total_projected_value: Optional[Decimal] = None
    occurrence_count: Optional[int] = None
    monthly_run_rate: Optional[Decimal] = None

    # Type-specific fields
    expense_category: Optional[str] = None
    cashflow_type: Optional[CashflowType] = None
    event_date: Optional[date] = None

    # Tax-specific fields
    jurisdiction: Optional[str] = None
    tax_type: Optional[TaxType] = None
    calculation_basis: Optional[str] = None
    assumed_rate: Optional[Decimal] = None
    assumptions: Optional[str] = None
    confidence_level: Optional[ConfidenceLevel] = None

    # Metadata
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    # Tax disclaimer (always present for TAX_LIABILITY)
    _disclaimer: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# BINDING SCHEMAS
# ============================================================================

class BindingCreate(BaseModel):
    """Create binding between projections"""
    scenario_id: UUID
    source_projection_id: UUID
    target_projection_id: UUID
    rule_type: BindingRuleType
    coefficient: Optional[Decimal] = Field(None, ge=0, le=1)
    rule_description: str = Field(..., min_length=1)

    @validator('target_projection_id')
    def no_self_binding(cls, v, values):
        if 'source_projection_id' in values and v == values['source_projection_id']:
            raise ValueError("Cannot bind projection to itself")
        return v


class BindingResponse(BaseModel):
    """Binding response"""
    id: UUID
    scenario_id: UUID
    source_projection_id: UUID
    target_projection_id: UUID
    rule_type: BindingRuleType
    coefficient: Optional[Decimal]
    rule_description: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCENARIO SUMMARY SCHEMAS
# ============================================================================

class ValueDestination(BaseModel):
    """Where money flows (ethical transparency)"""
    government_taxes: Dict[str, Any]  # amount, percentage
    suppliers_expenses: Dict[str, Any]
    entity_retained: Dict[str, Any]


class ScenarioSummary(BaseModel):
    """Scenario financial summary"""
    scenario: ScenarioResponse
    summary: Dict[str, Any]  # total_revenue, total_expense, etc.
    value_destination: ValueDestination
    projections_by_type: Dict[ProjectionType, int]


class ScenarioComparison(BaseModel):
    """Compare multiple scenarios"""
    scenarios: List[Dict[str, Any]]
    deltas: Dict[str, Dict[str, Any]]


# ============================================================================
# ERROR CODES (Sandbox-Specific)
# ============================================================================

class SandboxErrorCode(str, Enum):
    """Sandbox domain errors"""
    SCENARIO_NOT_EDITABLE = "SCENARIO_NOT_EDITABLE"
    SCENARIO_NOT_FOUND = "SCENARIO_NOT_FOUND"
    FORBIDDEN_BINDING = "FORBIDDEN_BINDING"
    CIRCULAR_BINDING = "CIRCULAR_BINDING"
    TAX_ASSUMPTIONS_MISSING = "TAX_ASSUMPTIONS_MISSING"
    PROJECTION_NOT_FOUND = "PROJECTION_NOT_FOUND"
    BINDING_NOT_FOUND = "BINDING_NOT_FOUND"
    INVALID_SCENARIO_STATE = "INVALID_SCENARIO_STATE"
    CROSS_SCENARIO_BINDING = "CROSS_SCENARIO_BINDING"
    INVALID_PROJECTION_TYPE = "INVALID_PROJECTION_TYPE"
