from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.db.models.user import User
from app.api.v1.auth import get_current_user
from app.schemas.group import SUCreateCompanyRequest
from app.schemas.company import CompanyResponse
from app.db.models.company import Company, SubscriptionType
from app.core.ucid import generate_ucid
from app.services.group_service import GroupService

router = APIRouter()


def check_superuser(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to ensure the current user is a superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Only superusers can access this endpoint"
        )
    return current_user


@router.post("/su-create", response_model=CompanyResponse)
def su_create_company(
    company_in: SUCreateCompanyRequest,
    current_user: User = Depends(check_superuser),
    db: Session = Depends(get_db)
):
    """
    Superuser endpoint to manually create a company bypassing payment.

    Features:
    - Creates company with NATIVE subscription type (no Stripe payment required)
    - Optionally associates the company with a group
    - Only accessible to superusers

    Args:
        company_in: Company creation data with optional group_company_id
        current_user: Must be a superuser
        db: Database session

    Returns:
        CompanyResponse: The created company
    """
    # Generate UCID
    ucid = generate_ucid(company_in.name)

    # Check for existing company with same UCID
    existing_company = db.query(Company).filter(Company.ucid == ucid).first()

    if existing_company and existing_company.is_active:
        raise HTTPException(
            status_code=400,
            detail=f"Company with UCID '{ucid}' already exists"
        )

    # If inactive company exists with same UCID, reactivate it
    if existing_company and not existing_company.is_active:
        existing_company.is_active = True
        existing_company.name = company_in.name
        existing_company.email = company_in.email
        existing_company.phone = company_in.phone
        existing_company.website = company_in.website
        existing_company.address_line1 = company_in.address_line1
        existing_company.address_line2 = company_in.address_line2
        existing_company.city = company_in.city
        existing_company.state = company_in.state
        existing_company.postal_code = company_in.postal_code
        existing_company.country = company_in.country
        existing_company.tax_id = company_in.tax_id
        existing_company.industry = company_in.industry
        existing_company.description = company_in.description
        existing_company.subscription_type = SubscriptionType.NATIVE

        db.commit()
        db.refresh(existing_company)
        company = existing_company
    else:
        # Create new company with NATIVE subscription (bypasses payment)
        company = Company(
            name=company_in.name,
            ucid=ucid,
            email=company_in.email,
            phone=company_in.phone,
            website=company_in.website,
            address_line1=company_in.address_line1,
            address_line2=company_in.address_line2,
            city=company_in.city,
            state=company_in.state,
            postal_code=company_in.postal_code,
            country=company_in.country,
            tax_id=company_in.tax_id,
            industry=company_in.industry,
            description=company_in.description,
            subscription_type=SubscriptionType.NATIVE,  # Key: Bypasses payment
            is_active=True
        )

        db.add(company)
        db.commit()
        db.refresh(company)

    # If group_company_id provided, associate the company with the group
    if company_in.group_company_id:
        try:
            GroupService.add_company_to_group(
                db=db,
                group_id=company_in.group_company_id,
                company_id=company.id
            )
        except ValueError as e:
            # If group association fails, log but don't fail the company creation
            # The company is already created at this point
            print(f"Warning: Failed to add company to group: {e}")

    return CompanyResponse.model_validate(company)
