import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.v1.auth import get_current_user
from app.core.errors import AequitasError
from app.core.request_context import ensure_request_ids
from app.db.models.user import User
from app.db.session import get_db
from app.services.permission_service import PermissionService
from app.services.staging_validation_service import StagingPipelineService
from app.db.models.staging_qbo_account import StagingQBOAccount
from app.schemas.staging import (
    StagingAccount,
    StagingProcessRequest,
    StagingProcessResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/staging/accounts",
    response_model=List[StagingAccount],
    summary="List staging QBO accounts",
    tags=["Integrations - Staging"],
)
def list_staging_accounts(
    company_id: UUID = Query(...),
    validation_status: Optional[str] = Query(None),
    mapping_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_request_ids()
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, company_id):
        raise AequitasError(
            code="AEQ_AUTH_FORBIDDEN",
            message="User cannot access this company's staging data",
            http_status=status.HTTP_403_FORBIDDEN,
        )

    query = db.query(StagingQBOAccount).filter(StagingQBOAccount.company_id == company_id)
    if validation_status:
        query = query.filter(StagingQBOAccount.validation_status == validation_status)
    if mapping_status:
        query = query.filter(StagingQBOAccount.mapping_status == mapping_status)

    return query.order_by(StagingQBOAccount.imported_at.desc()).all()


@router.post(
    "/staging/process",
    response_model=StagingProcessResponse,
    summary="Process staging accounts (validate + map)",
    tags=["Integrations - Staging"],
)
def process_staging_accounts(
    request_body: StagingProcessRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request_id, correlation_id = ensure_request_ids()
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, request_body.company_id):
        raise AequitasError(
            code="AEQ_AUTH_FORBIDDEN",
            message="User cannot process this company's staging data",
            http_status=status.HTTP_403_FORBIDDEN,
        )

    pipeline = StagingPipelineService(db)
    try:
        run_id, processed = pipeline.process_company(
            company_id=request_body.company_id,
            limit=request_body.limit or 100,
        )
        return StagingProcessResponse(run_id=run_id, processed=processed)
    except AequitasError as exc:
        logger.error(
            "staging_pipeline_failed",
            extra={
                "request_id": request_id,
                "correlation_id": correlation_id,
                "company_id": str(request_body.company_id),
                "error": exc.code,
            },
        )
        raise
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception(
            "staging_pipeline_unhandled",
            extra={
                "request_id": request_id,
                "correlation_id": correlation_id,
                "company_id": str(request_body.company_id),
            },
        )
        raise AequitasError(
            code="AEQ_QBO_PIPELINE_ERROR",
            message="Failed to process staging accounts",
            details={"error": str(exc)},
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
