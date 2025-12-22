from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.v1.auth import get_current_user
from app.core.errors import AequitasError
from app.core.request_context import ensure_request_ids
from app.db.models.account_mapping import AccountMapping
from app.db.models.company_account import CompanyAccount
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.mapping import Mapping
from app.services.permission_service import PermissionService

router = APIRouter()


@router.get(
    "/mappings",
    response_model=List[Mapping],
    summary="List account mappings",
    tags=["Integrations - Mappings"],
)
def list_mappings(
    company_id: UUID = Query(...),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_request_ids()
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, company_id):
        raise AequitasError(
            code="AEQ_AUTH_FORBIDDEN",
            message="User cannot access mappings for this company",
            http_status=status.HTTP_403_FORBIDDEN,
        )

    query = (
        db.query(AccountMapping)
        .join(CompanyAccount, AccountMapping.company_account_id == CompanyAccount.id)
        .filter(CompanyAccount.company_id == company_id)
    )

    if status_filter:
        query = query.filter(AccountMapping.mapping_status == status_filter)

    return query.order_by(AccountMapping.created_at.desc()).all()
