import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Path, status, Body
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.errors import AequitasError
from app.core.request_context import ensure_request_ids, get_request_id, get_correlation_id
from app.db.models.account_mapping import AccountMapping
from app.db.models.master_account import MasterAccount
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.mapping_review import (
    MappingDecisionRequest,
    MappingOverrideRequest,
    MappingDecisionResponse,
    MasterAccountSummary,
    CompanyAccountSummary,
)
from app.services.mapping_decision_service import MappingDecisionService

router = APIRouter()
logger = logging.getLogger(__name__)


def _to_response(mapping: AccountMapping, master_account: MasterAccount | None) -> MappingDecisionResponse:
    company_account = mapping.company_account
    return MappingDecisionResponse(
        id=mapping.id,
        company_account=CompanyAccountSummary(
            id=company_account.id,
            code=company_account.code,
            name=company_account.name,
            description=company_account.description,
        ),
        master_account=MasterAccountSummary(
            id=master_account.id if master_account else None,
            code=master_account.code if master_account else mapping.master_code,
            description=master_account.description if master_account else None,
        )
        if (master_account or mapping.master_code)
        else None,
        confidence=mapping.confidence,
        mapping_status=mapping.mapping_status,
        decision_status=mapping.decision_status,
        decision_reason=mapping.decision_reason,
        decided_at=mapping.decided_at,
        decided_by=mapping.decided_by,
        status=mapping.status,
        notes=mapping.notes,
    )


@router.get(
    "/mapping-review/pending",
    response_model=List[MappingDecisionResponse],
    summary="List pending mappings for review",
    tags=["Integrations - Mapping Review"],
)
def list_pending_mappings(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_request_ids()
    service = MappingDecisionService(db)
    mappings = service.list_pending_mappings(company_id=company_id, user_id=current_user.id)

    results: List[MappingDecisionResponse] = []
    for mapping in mappings:
        master_account = None
        if mapping.master_account_id:
            master_account = db.query(MasterAccount).filter(MasterAccount.id == mapping.master_account_id).first()
        results.append(_to_response(mapping, master_account))
    return results


@router.post(
    "/mapping-review/{mapping_id}/accept",
    response_model=MappingDecisionResponse,
    summary="Accept a mapping",
    tags=["Integrations - Mapping Review"],
)
def accept_mapping(
    mapping_id: UUID = Path(...),
    payload: MappingDecisionRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request_id, correlation_id = ensure_request_ids()
    service = MappingDecisionService(db)
    mapping = service.accept_mapping(mapping_id=mapping_id, user_id=current_user.id, reason=payload.reason)
    master_account = None
    if mapping.master_account_id:
        master_account = db.query(MasterAccount).filter(MasterAccount.id == mapping.master_account_id).first()
    logger.info(
        "mapping_accept",
        extra={"request_id": request_id, "correlation_id": correlation_id, "mapping_id": str(mapping_id)},
    )
    return _to_response(mapping, master_account)


@router.post(
    "/mapping-review/{mapping_id}/override",
    response_model=MappingDecisionResponse,
    summary="Override a mapping with a different master account",
    tags=["Integrations - Mapping Review"],
)
def override_mapping(
    mapping_id: UUID = Path(...),
    payload: MappingOverrideRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request_id, correlation_id = ensure_request_ids()
    service = MappingDecisionService(db)
    mapping = service.override_mapping(
        mapping_id=mapping_id,
        new_master_account_id=payload.master_account_id,
        user_id=current_user.id,
        reason=payload.reason,
    )
    master_account = None
    if mapping.master_account_id:
        master_account = db.query(MasterAccount).filter(MasterAccount.id == mapping.master_account_id).first()
    logger.info(
        "mapping_override",
        extra={
            "request_id": request_id,
            "correlation_id": correlation_id,
            "mapping_id": str(mapping_id),
            "master_account_id": str(payload.master_account_id),
        },
    )
    return _to_response(mapping, master_account)


@router.post(
    "/mapping-review/{mapping_id}/reject",
    response_model=MappingDecisionResponse,
    summary="Reject a mapping",
    tags=["Integrations - Mapping Review"],
)
def reject_mapping(
    mapping_id: UUID = Path(...),
    payload: MappingDecisionRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request_id, correlation_id = ensure_request_ids()
    service = MappingDecisionService(db)
    mapping = service.reject_mapping(mapping_id=mapping_id, user_id=current_user.id, reason=payload.reason)
    master_account = None
    logger.info(
        "mapping_reject",
        extra={"request_id": request_id, "correlation_id": correlation_id, "mapping_id": str(mapping_id)},
    )
    return _to_response(mapping, master_account)
