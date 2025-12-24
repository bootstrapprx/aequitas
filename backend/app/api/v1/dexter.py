"""
Dexter Intelligence API Endpoints (Zone C)

CANONICAL REFERENCE:
- Canon IV: Intelligence Boundaries
- Dexter Sandbox Observer: Read-only intelligence layer

CRITICAL RULES:
- READ-ONLY endpoints only
- NO mutations to sandbox or truth tables
- All responses include advisory disclaimer
- Company-scoped authorization
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.auth import get_current_user
from app.services.dexter_sandbox_observer import DexterSandboxObserver
from app.schemas.dexter import (
    ScenarioInsights,
    PatternDetectionResponse,
    TaxLiabilityAnalysis,
    ValueDestinationExplanation,
    ScenarioComparison,
)

router = APIRouter(prefix="/dexter", tags=["dexter"])


# ============================================================================
# DEXTER INTELLIGENCE ENDPOINTS
# ============================================================================

@router.get("/scenarios/{scenario_id}/insights", response_model=ScenarioInsights)
def get_scenario_insights(
    scenario_id: UUID,
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get comprehensive Dexter analysis of a scenario.

    Returns:
    - Detected patterns (revenue concentration, cashflow gaps, etc.)
    - Tax liability analysis (missing projections, effective rate)
    - Value destination breakdown (where revenue goes)

    Zone C Operation: READ-ONLY analysis of sandbox data.
    """
    observer = DexterSandboxObserver(db)

    # Verify scenario exists and belongs to company
    structure = observer.observe_scenario_structure(scenario_id)
    if "error" in structure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )

    if str(structure["scenario"]["company_id"]) != str(company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Scenario does not belong to this company"
        )

    # Detect patterns
    patterns = observer.detect_patterns(scenario_id)

    # Analyze tax liability
    tax_analysis = observer.analyze_tax_liability(scenario_id)

    # Explain value destinations
    value_destination = observer.explain_value_destinations(scenario_id)

    return ScenarioInsights(
        scenario_id=scenario_id,
        scenario_name=structure["scenario"]["name"],
        patterns_detected=[PatternDetectionResponse(**p) for p in patterns],
        tax_analysis=TaxLiabilityAnalysis(
            has_tax_projections=tax_analysis["has_tax_projections"],
            tax_projection_count=len(tax_analysis["tax_projections"]),
            effective_tax_rate=tax_analysis["effective_tax_rate"],
            tax_impact_on_profit_pct=tax_analysis["tax_impact_on_profit_pct"],
            recommendations=tax_analysis["recommendations"]
        ),
        value_destination=ValueDestinationExplanation(
            total_revenue=value_destination["total_revenue"],
            destinations=value_destination["destinations"],
            percentages=value_destination["percentages"],
            explanation=value_destination["explanation"]
        )
    )


@router.get("/scenarios/{scenario_id}/patterns", response_model=List[PatternDetectionResponse])
def get_scenario_patterns(
    scenario_id: UUID,
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Detect patterns in scenario structure.

    Returns:
    - Revenue concentration risk
    - Expense timing mismatches
    - Cashflow gaps
    - Binding complexity

    Zone C Operation: READ-ONLY pattern detection.
    """
    observer = DexterSandboxObserver(db)

    # Verify scenario exists and belongs to company
    structure = observer.observe_scenario_structure(scenario_id)
    if "error" in structure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )

    if str(structure["scenario"]["company_id"]) != str(company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Scenario does not belong to this company"
        )

    patterns = observer.detect_patterns(scenario_id)
    return [PatternDetectionResponse(**p) for p in patterns]


@router.get("/scenarios/{scenario_id}/tax-analysis", response_model=TaxLiabilityAnalysis)
def get_tax_analysis(
    scenario_id: UUID,
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Analyze tax liability projections.

    Returns:
    - Whether tax projections exist
    - Effective tax rate
    - Missing tax types
    - Recommendations for improvement

    Zone C Operation: READ-ONLY tax intelligence.
    """
    observer = DexterSandboxObserver(db)

    # Verify scenario exists and belongs to company
    structure = observer.observe_scenario_structure(scenario_id)
    if "error" in structure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )

    if str(structure["scenario"]["company_id"]) != str(company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Scenario does not belong to this company"
        )

    tax_analysis = observer.analyze_tax_liability(scenario_id)

    return TaxLiabilityAnalysis(
        has_tax_projections=tax_analysis["has_tax_projections"],
        tax_projection_count=len(tax_analysis["tax_projections"]),
        effective_tax_rate=tax_analysis["effective_tax_rate"],
        tax_impact_on_profit_pct=tax_analysis["tax_impact_on_profit_pct"],
        recommendations=tax_analysis["recommendations"]
    )


@router.get("/scenarios/{scenario_id}/value-destinations", response_model=ValueDestinationExplanation)
def get_value_destinations(
    scenario_id: UUID,
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Explain where revenue goes (value destination axis).

    Returns:
    - Operating expense allocation
    - Tax liability allocation
    - Net retained position
    - Human-readable explanation

    Zone C Operation: READ-ONLY value destination analysis.
    """
    observer = DexterSandboxObserver(db)

    # Verify scenario exists and belongs to company
    structure = observer.observe_scenario_structure(scenario_id)
    if "error" in structure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )

    if str(structure["scenario"]["company_id"]) != str(company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Scenario does not belong to this company"
        )

    value_destination = observer.explain_value_destinations(scenario_id)

    return ValueDestinationExplanation(
        total_revenue=value_destination["total_revenue"],
        destinations=value_destination["destinations"],
        percentages=value_destination["percentages"],
        explanation=value_destination["explanation"]
    )


@router.post("/scenarios/compare", response_model=ScenarioComparison)
def compare_scenarios(
    scenario_ids: List[UUID],
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Compare up to 3 scenarios side-by-side.

    Returns:
    - Comparison matrix (revenue, expense, profit, tax, net position)
    - Detected trade-offs
    - Advisory recommendation

    Zone C Operation: READ-ONLY scenario comparison.
    """
    if len(scenario_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 scenarios required for comparison"
        )

    if len(scenario_ids) > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 3 scenarios can be compared"
        )

    observer = DexterSandboxObserver(db)

    # Verify all scenarios exist and belong to company
    for scenario_id in scenario_ids:
        structure = observer.observe_scenario_structure(scenario_id)
        if "error" in structure:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found"
            )

        if str(structure["scenario"]["company_id"]) != str(company_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Scenario {scenario_id} does not belong to this company"
            )

    # Compare scenarios
    comparison = observer.compare_scenarios(scenario_ids)

    if "error" in comparison:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=comparison["error"]
        )

    return ScenarioComparison(
        comparison_matrix=comparison["comparison_matrix"],
        trade_offs=comparison["trade_offs"],
        recommendation=comparison["recommendation"]
    )
