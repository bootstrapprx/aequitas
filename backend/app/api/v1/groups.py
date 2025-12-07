from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.db.session import get_db
from app.db.models.user import User
from app.api.v1.auth import get_current_user
from app.schemas.group import (
    GroupCompanyCreate,
    GroupCompanyUpdate,
    GroupCompanyResponse,
    GroupCompanyWithMembers,
    AddCompanyToGroupRequest,
    PropagateMappingsRequest,
    PropagateMappingsResponse
)
from app.schemas.company import CompanyResponse
from app.services.group_service import GroupService

router = APIRouter()


@router.get("/", response_model=List[GroupCompanyResponse])
def list_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all groups owned by the current user.
    Superusers can see all groups.
    """
    if current_user.is_superuser:
        # Superusers can see all groups
        groups = db.query(app.db.models.group_company.GroupCompany).all()
    else:
        # Regular users see only their owned groups
        groups = GroupService.get_groups_for_user(db, current_user.id)

    return groups


@router.post("/", response_model=GroupCompanyResponse)
def create_group(
    group_in: GroupCompanyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new group company.
    Only superusers and admins can create groups.
    """
    # Permission check: SU or group owner (anyone can create their own group)
    # For now, any authenticated user can create a group
    # Could be restricted to SU only if needed

    try:
        return GroupService.create_group(
            db=db,
            name=group_in.name,
            description=group_in.description,
            owner_user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{group_id}", response_model=GroupCompanyWithMembers)
def get_group(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific group with its member companies.
    """
    group = GroupService.get_group_by_id(db, group_id)

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Permission check: Only owner or superuser can view
    if not current_user.is_superuser and group.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this group")

    # Get member companies
    companies = GroupService.get_group_companies(db, group_id)

    # Convert to response model
    response = GroupCompanyWithMembers(
        id=group.id,
        name=group.name,
        description=group.description,
        owner_user_id=group.owner_user_id,
        created_at=group.created_at,
        updated_at=group.updated_at,
        companies=[CompanyResponse.model_validate(c) for c in companies]
    )

    return response


@router.post("/{group_id}/companies", response_model=dict)
def add_company_to_group(
    group_id: UUID,
    request: AddCompanyToGroupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a company to a group.
    Only group owner or superuser can add companies.
    """
    group = GroupService.get_group_by_id(db, group_id)

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Permission check
    if not current_user.is_superuser and group.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this group")

    try:
        member = GroupService.add_company_to_group(
            db=db,
            group_id=group_id,
            company_id=request.company_id
        )
        return {"message": "Company added to group successfully", "member_id": str(member.id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{group_id}/companies/{company_id}", response_model=dict)
def remove_company_from_group(
    group_id: UUID,
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a company from a group.
    Only group owner or superuser can remove companies.
    """
    group = GroupService.get_group_by_id(db, group_id)

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Permission check
    if not current_user.is_superuser and group.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this group")

    success = GroupService.remove_company_from_group(
        db=db,
        group_id=group_id,
        company_id=company_id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Company not found in group")

    return {"message": "Company removed from group successfully"}


@router.post("/{group_id}/propagate-mappings", response_model=PropagateMappingsResponse)
def propagate_mappings(
    group_id: UUID,
    request: PropagateMappingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Propagate account mappings from a source company to other companies in the group.
    Only group owner or superuser can propagate mappings.
    """
    group = GroupService.get_group_by_id(db, group_id)

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Permission check
    if not current_user.is_superuser and group.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this group")

    try:
        result = GroupService.propagate_mappings(
            db=db,
            group_id=group_id,
            source_company_id=request.source_company_id,
            target_company_id=request.target_company_id,
            force=request.force
        )
        return PropagateMappingsResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
