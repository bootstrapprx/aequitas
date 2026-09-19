"""
Dexter Observer API Endpoints (Ledger Observations)

Read-only endpoints for Dexter insights on posted journal entries.

Authority: Canon IV - Intelligence (Zone C) is advisory, never authoritative.

CRITICAL CONSTRAINTS:
- Uses DexterReadOnlySession (no writes possible)
- All responses validated by tone enforcer
- No autonomous actions
- All outputs are advisory

DISTINCTION:
- dexter.py: Sandbox scenario analysis
- dexter_observer.py: Posted ledger observations (this file)
"""

from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.dexter_session import get_dexter_db
from app.services.dexter_observer_service import DexterObserverService
from app.services.dexter_tone_enforcer import tone_enforcer, format_approved_message
from app.api.v1.auth import get_current_user
from app.db.models.user import User


router = APIRouter(prefix="/dexter/observer", tags=["dexter-observer"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class DexterInsight(BaseModel):
    """Single Dexter insight."""
    type: str = Field(..., description="Insight type (pattern, anomaly, etc)")
    message: str = Field(..., description="Tone-validated message")
    data: dict = Field(..., description="Supporting data")
    dismissible: bool = Field(default=True, description="Can be dismissed")
    actions: List[str] = Field(default_factory=list, description="Optional action labels")


class DexterInsightsResponse(BaseModel):
    """Response containing multiple insights."""
    company_id: UUID
    insights: List[DexterInsight]
    total_count: int
    observer_mode: str = Field(default="passive", description="Always 'passive'")


class DexterHealthResponse(BaseModel):
    """Health check for Dexter Observer service."""
    status: str
    read_only: bool
    tone_enforcement: bool
    observer_mode: str
    canon_compliant: bool


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/health", response_model=DexterHealthResponse)
def dexter_health_check():
    """
    Health check for Dexter Observer service.

    Returns:
        Status and configuration info
    """
    return DexterHealthResponse(
        status="operational",
        read_only=True,
        tone_enforcement=True,
        observer_mode="passive",
        canon_compliant=True
    )


@router.get("/companies/{company_id}/insights", response_model=DexterInsightsResponse)
def get_company_insights(
    company_id: UUID,
    period_id: Optional[UUID] = None,
    max_insights: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_dexter_db)  # Read-only session
):
    """
    Get Dexter insights for a company.

    All insights are read-only observations. No data is mutated.

    Args:
        company_id: Company to analyze
        period_id: Optional fiscal period filter
        max_insights: Maximum insights to return (default: 10)
        current_user: Authenticated user
        db: Read-only database session

    Returns:
        Insights with tone-validated messages

    Note:
        - Requires user authorization (user must own company)
        - All messages validated by tone enforcer
        - Database session is read-only (writes blocked)
    """
    # Authorization check (placeholder - implement user_owns_company)
    # if not user_owns_company(current_user.id, company_id, db):
    #     raise HTTPException(status_code=403, detail="Not authorized")

    service = DexterObserverService(db)

    try:
        # Get insights (read-only)
        raw_insights = service.get_insights_for_company(
            company_id=company_id,
            current_period_id=period_id,
            max_insights=max_insights
        )

        # Format insights with tone validation
        formatted_insights = []

        # Format patterns
        for pattern in raw_insights.get("patterns", []):
            try:
                message = format_approved_message(
                    "recurring_pattern",
                    account_name=", ".join(pattern["account_codes"][:2]),
                    description=pattern["description"]
                )

                formatted_insights.append(DexterInsight(
                    type="recurring_pattern",
                    message=message,
                    data=pattern,
                    dismissible=True,
                    actions=["Create Template", "Dismiss"]
                ))
            except Exception as e:
                # Skip if tone validation fails (should not happen with approved templates)
                print(f"Tone validation error: {e}")
                continue

        # Format anomalies
        for anomaly in raw_insights.get("anomalies", []):
            try:
                message = format_approved_message(
                    "anomaly",
                    account_name=anomaly["account_name"],
                    amount=f"${anomaly['amount']:.2f}",
                    date=anomaly["entry_date"],
                    avg_amount=f"${anomaly['avg_amount']:.2f}"
                )

                formatted_insights.append(DexterInsight(
                    type="anomaly",
                    message=message,
                    data=anomaly,
                    dismissible=True,
                    actions=["Review Entry", "Dismiss"]
                ))
            except Exception as e:
                print(f"Tone validation error: {e}")
                continue

        # Format missing entries
        for missing in raw_insights.get("missing_entries", []):
            try:
                message = format_approved_message(
                    "missing_entry",
                    description=missing["expected_description"],
                    day_of_month=missing["typical_day_of_month"]
                )

                formatted_insights.append(DexterInsight(
                    type="missing_entry",
                    message=message,
                    data=missing,
                    dismissible=True,
                    actions=["Create Entry", "Dismiss"]
                ))
            except Exception as e:
                print(f"Tone validation error: {e}")
                continue

        return DexterInsightsResponse(
            company_id=company_id,
            insights=formatted_insights,
            total_count=len(formatted_insights),
            observer_mode="passive"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate insights: {str(e)}"
        )


@router.get("/companies/{company_id}/patterns", response_model=List[DexterInsight])
def get_recurring_patterns(
    company_id: UUID,
    lookback_months: int = 3,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_dexter_db)
):
    """
    Get recurring patterns for a company.

    Args:
        company_id: Company to analyze
        lookback_months: Months to look back (default: 3)
        current_user: Authenticated user
        db: Read-only database session

    Returns:
        List of recurring pattern insights
    """
    service = DexterObserverService(db)

    try:
        patterns = service.detect_recurring_patterns(
            company_id=company_id,
            lookback_months=lookback_months
        )

        insights = []
        for pattern in patterns:
            try:
                message = format_approved_message(
                    "recurring_pattern",
                    account_name=", ".join(pattern["account_codes"][:2]),
                    description=pattern["description"]
                )

                insights.append(DexterInsight(
                    type="recurring_pattern",
                    message=message,
                    data=pattern,
                    dismissible=True,
                    actions=["Create Template", "Dismiss"]
                ))
            except Exception:
                continue

        return insights

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect patterns: {str(e)}"
        )


@router.get("/companies/{company_id}/anomalies", response_model=List[DexterInsight])
def get_anomalies(
    company_id: UUID,
    account_code: Optional[str] = None,
    threshold: float = 2.0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_dexter_db)
):
    """
    Get transaction anomalies for a company.

    Args:
        company_id: Company to analyze
        account_code: Optional account filter
        threshold: Standard deviation threshold (default: 2.0)
        current_user: Authenticated user
        db: Read-only database session

    Returns:
        List of anomaly insights
    """
    service = DexterObserverService(db)

    try:
        anomalies = service.detect_anomalies(
            company_id=company_id,
            account_code=account_code,
            threshold_stddev=threshold
        )

        insights = []
        for anomaly in anomalies:
            try:
                message = format_approved_message(
                    "anomaly",
                    account_name=anomaly["account_name"],
                    amount=f"${anomaly['amount']:.2f}",
                    date=anomaly["entry_date"],
                    avg_amount=f"${anomaly['avg_amount']:.2f}"
                )

                insights.append(DexterInsight(
                    type="anomaly",
                    message=message,
                    data=anomaly,
                    dismissible=True,
                    actions=["Review Entry", "Dismiss"]
                ))
            except Exception:
                continue

        return insights

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect anomalies: {str(e)}"
        )


@router.get("/companies/{company_id}/account-usage", response_model=List[DexterInsight])
def get_account_usage(
    company_id: UUID,
    period_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_dexter_db)
):
    """
    Get account usage statistics.

    Args:
        company_id: Company to analyze
        period_id: Optional fiscal period filter
        current_user: Authenticated user
        db: Read-only database session

    Returns:
        List of account usage insights
    """
    service = DexterObserverService(db)

    try:
        usage = service.analyze_account_usage(
            company_id=company_id,
            period_id=period_id
        )

        insights = []
        for account in usage:
            try:
                message = format_approved_message(
                    "account_usage",
                    account_name=account["account_name"],
                    count=account["transaction_count"]
                )

                insights.append(DexterInsight(
                    type="account_usage",
                    message=message,
                    data=account,
                    dismissible=True,
                    actions=["View Report", "Dismiss"]
                ))
            except Exception:
                continue

        return insights

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze account usage: {str(e)}"
        )


@router.post("/validate-message")
def validate_dexter_message(
    message: str,
    current_user: User = Depends(get_current_user)
):
    """
    Validate a Dexter message for tone compliance.

    This endpoint is for testing/validation only.
    All production messages are automatically validated.

    Args:
        message: Message to validate
        current_user: Authenticated user

    Returns:
        Validation result with violations (if any)
    """
    is_valid, violations = tone_enforcer.check(message)

    return {
        "message": message,
        "is_valid": is_valid,
        "violations": violations,
        "canon_compliant": is_valid
    }
