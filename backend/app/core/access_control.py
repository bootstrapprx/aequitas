"""
Centralized company access guards.
"""
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.company import Company
from app.db.models.user import User
from app.db.models.user_company import UserCompany


def require_company_access(
    db: Session,
    current_user: User,
    company_id: UUID,
    *,
    require_admin: bool = False,
    allow_superuser: bool = False,
) -> Company:
    """
    Enforce company access for the current user.

    Args:
        db: Database session
        current_user: Authenticated user
        company_id: Company UUID
        require_admin: If True, user must be company admin
        allow_superuser: If True, superusers bypass membership checks
    """
    if allow_superuser and current_user.is_superuser:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        return company

    user_company = db.query(UserCompany).filter(
        UserCompany.user_id == current_user.id,
        UserCompany.company_id == company_id,
    ).first()

    if not user_company:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this company")

    if require_admin and not user_company.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required for this company")

    if not user_company.can_view:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="View access required for this company")

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    return company
