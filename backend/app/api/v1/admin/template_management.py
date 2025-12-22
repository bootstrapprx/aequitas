"""
Template Management API - Approach 2: API-based dynamic template CRUD

This module provides superuser-only endpoints for managing chart templates.

PERMISSION MODEL:
- ALL endpoints require superuser privileges
- Regular users: Cannot access these endpoints (403 Forbidden)
- Superusers: Full CRUD on templates and template accounts

API Routes:
- POST /api/v1/admin/templates - Create new template
- PUT /api/v1/admin/templates/{template_id} - Update template
- DELETE /api/v1/admin/templates/{template_id} - Delete template (soft delete via is_active)
- POST /api/v1/admin/templates/{template_id}/accounts - Add account to template
- DELETE /api/v1/admin/templates/{template_id}/accounts/{account_id} - Remove account from template
- PATCH /api/v1/admin/templates/{template_id}/accounts/{account_id} - Update template account settings

Usage:
    Include this router in main.py:
    from app.api.v1.admin import template_management
    app.include_router(template_management.router, prefix="/api/v1/admin", tags=["admin", "templates"])
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.db.models.chart_template import ChartTemplate, ChartTemplateAccount
from app.db.models.master_account import MasterAccount
from app.db.models.user import User
from app.core.security import check_superuser
from pydantic import BaseModel, Field


# ============================================================================
# SCHEMAS
# ============================================================================

class TemplateCreateRequest(BaseModel):
    """Request schema for creating a new chart template."""
    name: str = Field(..., min_length=1, max_length=255)
    jurisdiction: str = Field(..., min_length=2, max_length=100)
    version: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    is_active: bool = True


class TemplateUpdateRequest(BaseModel):
    """Request schema for updating a chart template."""
    name: str | None = Field(None, min_length=1, max_length=255)
    jurisdiction: str | None = Field(None, min_length=2, max_length=100)
    version: str | None = Field(None, min_length=1, max_length=50)
    description: str | None = None
    is_active: bool | None = None


class TemplateAccountCreateRequest(BaseModel):
    """Request schema for adding an account to a template."""
    master_account_id: UUID
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    is_mandatory: bool = False
    allow_custom_children: bool = False
    sort_order: int = 0
    parent_id: UUID | None = None


class TemplateAccountUpdateRequest(BaseModel):
    """Request schema for updating a template account."""
    is_mandatory: bool | None = None
    allow_custom_children: bool | None = None
    sort_order: int | None = None


class TemplateResponse(BaseModel):
    """Response schema for template operations."""
    id: UUID
    name: str
    jurisdiction: str
    version: str
    description: str | None
    is_active: bool
    account_count: int

    class Config:
        from_attributes = True


class TemplateAccountResponse(BaseModel):
    """Response schema for template account."""
    id: UUID
    template_id: UUID
    master_account_id: UUID
    code: str
    name: str
    is_mandatory: bool
    allow_custom_children: bool
    sort_order: int
    parent_id: UUID | None

    class Config:
        from_attributes = True


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter()


# ============================================================================
# TEMPLATE CRUD ENDPOINTS
# ============================================================================

@router.post("/templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    request: TemplateCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_superuser)
):
    """
    Create a new chart template.

    **Requires:** Superuser privileges

    Creates a new empty template. Use the add account endpoint to populate it.
    """

    # Check for duplicate name
    existing = db.query(ChartTemplate).filter(ChartTemplate.name == request.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Template with name '{request.name}' already exists"
        )

    template = ChartTemplate(
        name=request.name,
        jurisdiction=request.jurisdiction,
        version=request.version,
        description=request.description,
        is_active=request.is_active
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return TemplateResponse(
        id=template.id,
        name=template.name,
        jurisdiction=template.jurisdiction,
        version=template.version,
        description=template.description,
        is_active=template.is_active,
        account_count=0
    )


@router.put("/templates/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: UUID,
    request: TemplateUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_superuser)
):
    """
    Update an existing chart template.

    **Requires:** Superuser privileges

    Can update name, jurisdiction, version, description, and active status.
    """

    template = db.query(ChartTemplate).filter(ChartTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    # Update fields if provided
    if request.name is not None:
        # Check for duplicate name
        existing = db.query(ChartTemplate).filter(
            ChartTemplate.name == request.name,
            ChartTemplate.id != template_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Template with name '{request.name}' already exists"
            )
        template.name = request.name

    if request.jurisdiction is not None:
        template.jurisdiction = request.jurisdiction

    if request.version is not None:
        template.version = request.version

    if request.description is not None:
        template.description = request.description

    if request.is_active is not None:
        template.is_active = request.is_active

    db.commit()
    db.refresh(template)

    account_count = db.query(ChartTemplateAccount).filter(
        ChartTemplateAccount.template_id == template_id
    ).count()

    return TemplateResponse(
        id=template.id,
        name=template.name,
        jurisdiction=template.jurisdiction,
        version=template.version,
        description=template.description,
        is_active=template.is_active,
        account_count=account_count
    )


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_superuser)
):
    """
    Soft-delete a chart template by setting is_active=False.

    **Requires:** Superuser privileges

    Templates linked to companies cannot be hard-deleted.
    This endpoint sets is_active=False to hide the template from selection.
    """

    template = db.query(ChartTemplate).filter(ChartTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    # Soft delete
    template.is_active = False
    db.commit()

    return None


# ============================================================================
# TEMPLATE ACCOUNT ENDPOINTS
# ============================================================================

@router.post("/templates/{template_id}/accounts", response_model=TemplateAccountResponse, status_code=status.HTTP_201_CREATED)
def add_account_to_template(
    template_id: UUID,
    request: TemplateAccountCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_superuser)
):
    """
    Add an account to a chart template.

    **Requires:** Superuser privileges

    Links a master account to the template with configuration settings.
    """

    # Verify template exists
    template = db.query(ChartTemplate).filter(ChartTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    # Verify master account exists
    master_account = db.query(MasterAccount).filter(
        MasterAccount.id == request.master_account_id
    ).first()
    if not master_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Master account not found")

    # Check for duplicate code in this template
    existing = db.query(ChartTemplateAccount).filter(
        ChartTemplateAccount.template_id == template_id,
        ChartTemplateAccount.code == request.code
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Account with code '{request.code}' already exists in this template"
        )

    # Create template account
    template_account = ChartTemplateAccount(
        template_id=template_id,
        master_account_id=request.master_account_id,
        parent_id=request.parent_id,
        code=request.code,
        name=request.name,
        is_mandatory=request.is_mandatory,
        allow_custom_children=request.allow_custom_children,
        sort_order=request.sort_order
    )

    db.add(template_account)
    db.commit()
    db.refresh(template_account)

    return TemplateAccountResponse(
        id=template_account.id,
        template_id=template_account.template_id,
        master_account_id=template_account.master_account_id,
        code=template_account.code,
        name=template_account.name,
        is_mandatory=template_account.is_mandatory,
        allow_custom_children=template_account.allow_custom_children,
        sort_order=template_account.sort_order,
        parent_id=template_account.parent_id
    )


@router.patch("/templates/{template_id}/accounts/{account_id}", response_model=TemplateAccountResponse)
def update_template_account(
    template_id: UUID,
    account_id: UUID,
    request: TemplateAccountUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_superuser)
):
    """
    Update a template account's configuration.

    **Requires:** Superuser privileges

    Can modify is_mandatory, allow_custom_children, and sort_order.
    """

    template_account = db.query(ChartTemplateAccount).filter(
        ChartTemplateAccount.id == account_id,
        ChartTemplateAccount.template_id == template_id
    ).first()

    if not template_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template account not found")

    # Update fields
    if request.is_mandatory is not None:
        template_account.is_mandatory = request.is_mandatory

    if request.allow_custom_children is not None:
        template_account.allow_custom_children = request.allow_custom_children

    if request.sort_order is not None:
        template_account.sort_order = request.sort_order

    db.commit()
    db.refresh(template_account)

    return TemplateAccountResponse(
        id=template_account.id,
        template_id=template_account.template_id,
        master_account_id=template_account.master_account_id,
        code=template_account.code,
        name=template_account.name,
        is_mandatory=template_account.is_mandatory,
        allow_custom_children=template_account.allow_custom_children,
        sort_order=template_account.sort_order,
        parent_id=template_account.parent_id
    )


@router.delete("/templates/{template_id}/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_account_from_template(
    template_id: UUID,
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_superuser)
):
    """
    Remove an account from a chart template.

    **Requires:** Superuser privileges

    Hard deletes the template account. Use with caution.
    """

    template_account = db.query(ChartTemplateAccount).filter(
        ChartTemplateAccount.id == account_id,
        ChartTemplateAccount.template_id == template_id
    ).first()

    if not template_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template account not found")

    db.delete(template_account)
    db.commit()

    return None


@router.get("/templates/{template_id}/accounts", response_model=List[TemplateAccountResponse])
def list_template_accounts(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_superuser)
):
    """
    List all accounts in a template.

    **Requires:** Superuser privileges

    Returns all accounts sorted by sort_order.
    """

    # Verify template exists
    template = db.query(ChartTemplate).filter(ChartTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    accounts = db.query(ChartTemplateAccount).filter(
        ChartTemplateAccount.template_id == template_id
    ).order_by(ChartTemplateAccount.sort_order).all()

    return [
        TemplateAccountResponse(
            id=acc.id,
            template_id=acc.template_id,
            master_account_id=acc.master_account_id,
            code=acc.code,
            name=acc.name,
            is_mandatory=acc.is_mandatory,
            allow_custom_children=acc.allow_custom_children,
            sort_order=acc.sort_order,
            parent_id=acc.parent_id
        )
        for acc in accounts
    ]
