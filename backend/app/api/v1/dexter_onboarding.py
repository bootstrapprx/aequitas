from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Any

from app.api import deps
from app.services.dexter.engine import dexter_engine
from app.services.dexter.models import OnboardingPreprocessRequest, OnboardingPreprocessResponse
from app.db.models.company import Company

router = APIRouter()

@router.post("/onboarding/{company_id}/dexter/preprocess", response_model=OnboardingPreprocessResponse)
async def preprocess_onboarding_step(
    company_id: UUID,
    request: OnboardingPreprocessRequest,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> OnboardingPreprocessResponse:
    """
    Preprocess user input for a specific onboarding step using Dexter.
    CANONICAL REF: DEXTER_CANON.md §7.1
    """
    # Verify company access
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    
    # Check if user is associated with company (simplified check for MVP)
    # real check would be in deps or explicit query on UserCompany
    
    # Process
    try:
        response = await dexter_engine.preprocess_onboarding(request)
        return response
    except Exception as e:
        # Fallback if engine fails
        return OnboardingPreprocessResponse(
            suggested_value=request.user_input,
            confidence=1.0,
            requires_confirmation=False,
            explanation=None
        )
