from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Any

from app.api import deps
from app.services.dexter.engine import dexter_engine
from app.services.dexter.models import OnboardingPreprocessRequest, OnboardingPreprocessResponse
from app.core.access_control import require_company_access

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
    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=False,
        allow_superuser=True,
    )
    
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
