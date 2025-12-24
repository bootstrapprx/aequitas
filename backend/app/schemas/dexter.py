"""
Dexter Intelligence Schemas (Zone C)

CANONICAL REFERENCE:
- Canon IV: Intelligence Boundaries
- Dexter is advisory only, never authoritative

CRITICAL RULES:
- All insights are recommendations, not commands
- action_taken defaults to False (Dexter doesn't execute)
- Confidence levels are explicit
- Explanations are human-readable
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class PatternType(str, Enum):
    """Types of patterns Dexter can detect"""
    REVENUE_CONCENTRATION = "REVENUE_CONCENTRATION"
    EXPENSE_BEFORE_REVENUE = "EXPENSE_BEFORE_REVENUE"
    NEGATIVE_CASHFLOW = "NEGATIVE_CASHFLOW"
    THIN_MARGINS = "THIN_MARGINS"
    COMPLEX_BINDINGS = "COMPLEX_BINDINGS"
    SEASONAL_VARIATION = "SEASONAL_VARIATION"


class RecommendationType(str, Enum):
    """Types of recommendations Dexter can make"""
    MISSING_TAX_PROJECTION = "MISSING_TAX_PROJECTION"
    MISSING_FEDERAL_INCOME_TAX = "MISSING_FEDERAL_INCOME_TAX"
    MISSING_PAYROLL_TAX = "MISSING_PAYROLL_TAX"
    LOW_TAX_RATE = "LOW_TAX_RATE"
    HIGH_TAX_RATE = "HIGH_TAX_RATE"
    DIVERSIFY_REVENUE = "DIVERSIFY_REVENUE"
    REDUCE_EXPENSES = "REDUCE_EXPENSES"
    INCREASE_WORKING_CAPITAL = "INCREASE_WORKING_CAPITAL"


class RiskLevel(str, Enum):
    """Risk severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ConfidenceLevel(str, Enum):
    """Dexter's confidence in analysis"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TradeOffType(str, Enum):
    """Types of trade-offs between scenarios"""
    REVENUE_EXPENSE_CORRELATION = "REVENUE_EXPENSE_CORRELATION"
    RISK_RETURN = "RISK_RETURN"
    SHORT_TERM_VS_LONG_TERM = "SHORT_TERM_VS_LONG_TERM"


# ============================================================================
# PATTERN DETECTION RESPONSES
# ============================================================================

class PatternDetectionResponse(BaseModel):
    """Detected pattern in scenario structure"""
    pattern_type: PatternType = Field(..., description="Type of pattern detected")
    confidence: ConfidenceLevel = Field(..., description="Dexter's confidence in this detection")
    description: str = Field(..., description="Human-readable explanation of the pattern")
    projections_involved: List[UUID] = Field(default_factory=list, description="Projections related to this pattern")
    recommendation: str = Field(..., description="Advisory action user could take")
    risk_level: RiskLevel = Field(..., description="Severity of risk if not addressed")

    class Config:
        json_schema_extra = {
            "example": {
                "pattern_type": "REVENUE_CONCENTRATION",
                "confidence": "HIGH",
                "description": "Single revenue source detected. Business has concentration risk.",
                "projections_involved": ["550e8400-e29b-41d4-a716-446655440000"],
                "recommendation": "Consider diversifying revenue streams to reduce risk.",
                "risk_level": "HIGH"
            }
        }


# ============================================================================
# TAX INTELLIGENCE RESPONSES
# ============================================================================

class TaxRecommendation(BaseModel):
    """Tax-related recommendation"""
    recommendation_type: RecommendationType = Field(..., description="Type of tax recommendation")
    severity: RiskLevel = Field(..., description="Severity if not addressed")
    description: str = Field(..., description="Explanation of the issue")
    action: str = Field(..., description="Suggested action")
    action_taken: bool = Field(default=False, description="Whether action has been executed (always False - Dexter is advisory only)")

    class Config:
        json_schema_extra = {
            "example": {
                "recommendation_type": "MISSING_FEDERAL_INCOME_TAX",
                "severity": "HIGH",
                "description": "Scenario shows profit but no federal income tax projection.",
                "action": "Add federal income tax projection (typically 21% for C-corps).",
                "action_taken": False
            }
        }


class TaxLiabilityAnalysis(BaseModel):
    """Analysis of tax liability projections"""
    has_tax_projections: bool = Field(..., description="Whether scenario includes tax projections")
    tax_projection_count: int = Field(default=0, description="Number of tax liability projections")
    effective_tax_rate: Decimal = Field(..., description="Effective tax rate (tax / profit)")
    tax_impact_on_profit_pct: Decimal = Field(..., description="Tax as percentage of profit")
    recommendations: List[TaxRecommendation] = Field(default_factory=list, description="Tax-related recommendations")

    class Config:
        json_schema_extra = {
            "example": {
                "has_tax_projections": False,
                "tax_projection_count": 0,
                "effective_tax_rate": "0.00",
                "tax_impact_on_profit_pct": "0.00",
                "recommendations": [
                    {
                        "recommendation_type": "MISSING_TAX_PROJECTION",
                        "severity": "HIGH",
                        "description": "No tax liability projections found.",
                        "action": "Add federal income tax projection.",
                        "action_taken": False
                    }
                ]
            }
        }


# ============================================================================
# VALUE DESTINATION RESPONSES
# ============================================================================

class ValueDestinations(BaseModel):
    """Where revenue is allocated"""
    operating_expense: Decimal = Field(..., description="Total operating expenses")
    tax_liability: Decimal = Field(..., description="Total tax liability")
    net_retained: Decimal = Field(..., description="Net position after expenses and tax")


class ValueDestinationPercentages(BaseModel):
    """Percentage breakdown of revenue destinations"""
    operating_expense_pct: Decimal = Field(..., description="Operating expenses as % of revenue")
    tax_liability_pct: Decimal = Field(..., description="Tax liability as % of revenue")
    net_retained_pct: Decimal = Field(..., description="Net retained as % of revenue")


class ValueDestinationExplanation(BaseModel):
    """Value destination analysis"""
    total_revenue: Decimal = Field(..., description="Total projected revenue")
    destinations: ValueDestinations = Field(..., description="Where revenue goes")
    percentages: ValueDestinationPercentages = Field(..., description="Percentage breakdown")
    explanation: str = Field(..., description="Formatted human-readable explanation")

    class Config:
        json_schema_extra = {
            "example": {
                "total_revenue": "1000000.00",
                "destinations": {
                    "operating_expense": "600000.00",
                    "tax_liability": "84000.00",
                    "net_retained": "316000.00"
                },
                "percentages": {
                    "operating_expense_pct": "60.0",
                    "tax_liability_pct": "8.4",
                    "net_retained_pct": "31.6"
                },
                "explanation": "Revenue Distribution ($1,000,000 total):\\n\\n  Operating Expenses: $600,000 (60.0%)\\n  Tax Liability:      $84,000 (8.4%)\\n  Net Retained:       $316,000 (31.6%)\\n\\n✓  Moderate retention rate. Typical for established businesses."
            }
        }


# ============================================================================
# SCENARIO COMPARISON RESPONSES
# ============================================================================

class TradeOff(BaseModel):
    """Detected trade-off between scenarios"""
    trade_off_type: TradeOffType = Field(..., description="Type of trade-off")
    description: str = Field(..., description="Explanation of the trade-off")
    implication: str = Field(..., description="What this means for decision-making")

    class Config:
        json_schema_extra = {
            "example": {
                "trade_off_type": "REVENUE_EXPENSE_CORRELATION",
                "description": "Scenario 'Aggressive Growth' has highest revenue but also highest expenses.",
                "implication": "Growth comes with cost. Evaluate if margin improvement is possible."
            }
        }


class ComparisonMatrix(BaseModel):
    """Side-by-side scenario comparison"""
    scenario_names: List[str] = Field(..., description="Names of compared scenarios")
    total_revenue: List[Decimal] = Field(..., description="Total revenue per scenario")
    total_expense: List[Decimal] = Field(..., description="Total expenses per scenario")
    projected_profit: List[Decimal] = Field(..., description="Projected profit per scenario")
    total_tax_liability: List[Decimal] = Field(..., description="Total tax liability per scenario")
    net_position: List[Decimal] = Field(..., description="Net position per scenario")


class ScenarioComparison(BaseModel):
    """Comparison of multiple scenarios"""
    comparison_matrix: ComparisonMatrix = Field(..., description="Numeric comparison")
    trade_offs: List[TradeOff] = Field(default_factory=list, description="Detected trade-offs")
    recommendation: str = Field(..., description="Dexter's advisory recommendation")

    class Config:
        json_schema_extra = {
            "example": {
                "comparison_matrix": {
                    "scenario_names": ["Conservative", "Moderate", "Aggressive"],
                    "total_revenue": ["500000", "750000", "1000000"],
                    "total_expense": ["300000", "450000", "650000"],
                    "projected_profit": ["200000", "300000", "350000"],
                    "total_tax_liability": ["42000", "63000", "73500"],
                    "net_position": ["158000", "237000", "276500"]
                },
                "trade_offs": [
                    {
                        "trade_off_type": "REVENUE_EXPENSE_CORRELATION",
                        "description": "Aggressive scenario has highest revenue but also highest expenses.",
                        "implication": "Growth requires investment. Verify ROI justifies cost."
                    }
                ],
                "recommendation": "Scenario 'Aggressive' has highest net position ($276,500). Consider if growth assumptions are realistic."
            }
        }


# ============================================================================
# COMPREHENSIVE INSIGHT RESPONSE
# ============================================================================

class ScenarioInsights(BaseModel):
    """Complete Dexter analysis of a scenario"""
    scenario_id: UUID = Field(..., description="Scenario being analyzed")
    scenario_name: str = Field(..., description="Scenario name")
    patterns_detected: List[PatternDetectionResponse] = Field(default_factory=list, description="Detected patterns")
    tax_analysis: TaxLiabilityAnalysis = Field(..., description="Tax liability analysis")
    value_destination: ValueDestinationExplanation = Field(..., description="Value destination breakdown")

    _disclaimer: str = Field(
        default="This analysis is advisory only. Dexter does not execute changes or make decisions. "
                "All recommendations require human review and approval.",
        description="Canonical reminder that Dexter is non-authoritative"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "scenario_id": "550e8400-e29b-41d4-a716-446655440000",
                "scenario_name": "2024 Base Case",
                "patterns_detected": [
                    {
                        "pattern_type": "REVENUE_CONCENTRATION",
                        "confidence": "HIGH",
                        "description": "Single revenue source detected.",
                        "projections_involved": ["660e8400-e29b-41d4-a716-446655440001"],
                        "recommendation": "Consider diversifying revenue streams.",
                        "risk_level": "MEDIUM"
                    }
                ],
                "tax_analysis": {
                    "has_tax_projections": False,
                    "tax_projection_count": 0,
                    "effective_tax_rate": "0.00",
                    "tax_impact_on_profit_pct": "0.00",
                    "recommendations": [
                        {
                            "recommendation_type": "MISSING_TAX_PROJECTION",
                            "severity": "HIGH",
                            "description": "No tax liability projections found.",
                            "action": "Add federal income tax projection.",
                            "action_taken": False
                        }
                    ]
                },
                "value_destination": {
                    "total_revenue": "1000000.00",
                    "destinations": {
                        "operating_expense": "600000.00",
                        "tax_liability": "0.00",
                        "net_retained": "400000.00"
                    },
                    "percentages": {
                        "operating_expense_pct": "60.0",
                        "tax_liability_pct": "0.0",
                        "net_retained_pct": "40.0"
                    },
                    "explanation": "Revenue Distribution ($1,000,000 total)..."
                },
                "_disclaimer": "This analysis is advisory only..."
            }
        }
