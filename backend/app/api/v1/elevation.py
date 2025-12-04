from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.elevation_request import ElevationRequest, ElevationStatus
from app.api.v1.auth import get_current_user

router = APIRouter()

# --- Schemas ---

class ElevationRequestCreate(BaseModel):
    requested_role: str
    reason: Optional[str] = None

class ElevationRequestResponse(BaseModel):
    id: UUID
    user_id: UUID
    requested_role: str
    reason: Optional[str]
    status: str
    created_at: datetime
    rejection_reason: Optional[str]

    class Config:
        from_attributes = True

class ElevationReview(BaseModel):
    status: str # APPROVED or REJECTED
    rejection_reason: Optional[str] = None

# --- Endpoints ---

@router.post("/request", response_model=ElevationRequestResponse, status_code=status.HTTP_201_CREATED)
def request_elevation(
    request_in: ElevationRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a request to elevate privileges."""
    # Check if pending request exists
    existing = db.query(ElevationRequest).filter(
        ElevationRequest.user_id == current_user.id,
        ElevationRequest.status == ElevationStatus.PENDING
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="You already have a pending request.")

    new_request = ElevationRequest(
        user_id=current_user.id,
        requested_role=request_in.requested_role,
        reason=request_in.reason,
        status=ElevationStatus.PENDING
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request

@router.get("/my-requests", response_model=List[ElevationRequestResponse])
def get_my_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's elevation requests."""
    return db.query(ElevationRequest).filter(ElevationRequest.user_id == current_user.id).all()

@router.get("/pending", response_model=List[ElevationRequestResponse])
def get_pending_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all pending requests (Admin only)."""
    # In a real app, use a proper permission check dependency
    if current_user.role not in ["ADMIN", "SU"] and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return db.query(ElevationRequest).filter(ElevationRequest.status == ElevationStatus.PENDING).all()

@router.post("/{request_id}/review", response_model=ElevationRequestResponse)
def review_request(
    request_id: UUID,
    review: ElevationReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve or reject a request (Admin only)."""
    if current_user.role not in ["ADMIN", "SU"] and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    request = db.query(ElevationRequest).filter(ElevationRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if request.status != ElevationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request is not pending")

    request.status = review.status
    request.reviewed_by_id = current_user.id
    request.updated_at = datetime.utcnow()
    
    if review.status == "APPROVED":
        # Update user role
        user = db.query(User).filter(User.id == request.user_id).first()
        if user:
            user.role = request.requested_role
            if request.requested_role == "SU":
                user.is_superuser = True
    elif review.status == "REJECTED":
        request.rejection_reason = review.rejection_reason

    db.commit()
    db.refresh(request)
    return request
