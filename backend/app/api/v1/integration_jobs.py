"""
Integration Jobs API Endpoints.

PHASE 1.5: Operational Extraction - API Layer

Endpoints:
1. POST /jobs - Trigger job in Go worker (Python → Go)
2. POST /jobs/callback - Receive callback from Go worker (Go → Python)

CANONICAL REFERENCE:
- docs/canonical/API_CONTRACTS.md (Section 5)
- Pattern A: Python triggers job
- Pattern B: Go calls back with results

BOUNDARIES:
- NO accounting validation in this layer
- NO mapping or classification
- ONLY transport and staging coordination
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import logging

from app.db.session import get_db
from app.core.config import Settings, get_settings
from app.core.errors import AequitasError, make_error_envelope
from app.core.request_context import ensure_request_ids, get_request_id, get_correlation_id
from app.db.models.user import User
from app.api.v1.auth import get_current_user
from app.services.integration_job_service import IntegrationJobService
from app.services.permission_service import PermissionService
from app.schemas.integrations import (
    JobTriggerRequest,
    JobTriggerResponse,
    JobCallbackPayload,
    JobCallbackResponse,
)


router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Pattern A: Python → Go (Job Trigger)
# ============================================================================


@router.post("/jobs", response_model=JobTriggerResponse, status_code=202)
async def trigger_integration_job(
    job_request: JobTriggerRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    x_aequitas_idempotency_key: Optional[str] = Header(None, alias="X-Aequitas-Idempotency-Key"),
):
    """
    Trigger an integration job in the Go worker service.

    Flow:
    1. Authenticate user
    2. Verify company permissions
    3. Generate/extract request IDs
    4. Forward request to Go worker with canonical headers
    5. Return job_id immediately (async processing)

    Args:
        job_request: Job trigger request
        current_user: Authenticated user
        db: Database session
        settings: Application settings
        x_aequitas_idempotency_key: Optional idempotency key

    Returns:
        JobTriggerResponse with job_id from Go worker

    Raises:
        HTTPException: On permission denial or worker failure
    """
    # Ensure request IDs exist
    request_id, correlation_id = ensure_request_ids()

    logger.info(
        f"Triggering integration job: {job_request.job_type}",
        extra={
            "request_id": request_id,
            "correlation_id": correlation_id,
            "user_id": str(current_user.id),
            "company_id": str(job_request.company_id),
            "job_type": job_request.job_type,
        },
    )

    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_manage_company(current_user.id, job_request.company_id):
        logger.warning(
            f"Permission denied for user {current_user.id} on company {job_request.company_id}",
            extra={"request_id": request_id, "correlation_id": correlation_id},
        )
        raise HTTPException(
            status_code=403,
            detail="No permission to trigger jobs for this company",
        )

    # Trigger job via service
    service = IntegrationJobService(db, settings)
    try:
        response = await service.trigger_job(
            job_trigger=job_request,
            request_id=request_id,
            correlation_id=correlation_id,
            idempotency_key=x_aequitas_idempotency_key,
        )

        logger.info(
            f"Job triggered successfully: {response.job_id}",
            extra={
                "request_id": request_id,
                "correlation_id": correlation_id,
                "job_id": str(response.job_id),
            },
        )

        return response

    except AequitasError as e:
        logger.error(
            f"Failed to trigger job: {e.code}",
            extra={
                "request_id": request_id,
                "correlation_id": correlation_id,
                "error_code": e.code,
                "error_message": e.message,
            },
        )
        raise HTTPException(status_code=502, detail=make_error_envelope(e))


# ============================================================================
# Pattern B: Go → Python (Callback Receiver)
# ============================================================================


@router.post("/jobs/callback", response_model=JobCallbackResponse, status_code=200)
def receive_job_callback(
    callback: JobCallbackPayload,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    x_aequitas_request_id: Optional[str] = Header(None, alias="X-Aequitas-Request-Id"),
    x_aequitas_correlation_id: Optional[str] = Header(None, alias="X-Aequitas-Correlation-Id"),
    x_aequitas_idempotency_key: Optional[str] = Header(None, alias="X-Aequitas-Idempotency-Key"),
):
    """
    Receive callback from Go worker with job results.

    CRITICAL:
    - This endpoint is called by Go worker (not authenticated via JWT)
    - Should be protected by internal network or API key in production
    - Validates canonical headers
    - Enforces idempotency
    - Stages raw data WITHOUT accounting validation

    Flow:
    1. Extract canonical headers
    2. Validate callback schema
    3. Check idempotency (if key provided)
    4. Route to appropriate handler by job_type
    5. Stage raw data
    6. Return success response

    Args:
        callback: Callback payload from Go
        request: FastAPI request
        db: Database session
        settings: Application settings
        x_aequitas_request_id: Request ID from canonical headers
        x_aequitas_correlation_id: Correlation ID from canonical headers
        x_aequitas_idempotency_key: Idempotency key (optional)

    Returns:
        JobCallbackResponse indicating staging success

    Raises:
        HTTPException: On validation or processing errors
    """
    # Extract or generate request IDs
    request_id, correlation_id = ensure_request_ids(
        request_id=x_aequitas_request_id,
        correlation_id=x_aequitas_correlation_id,
    )

    logger.info(
        f"Received callback: {callback.job_type} [{callback.status}]",
        extra={
            "request_id": request_id,
            "correlation_id": correlation_id,
            "job_id": str(callback.job_id),
            "job_type": callback.job_type,
            "status": callback.status,
            "company_id": str(callback.company_id),
        },
    )

    # Validate canonical headers present
    if not x_aequitas_request_id:
        logger.warning(
            "Callback received without X-Aequitas-Request-Id header",
            extra={"job_id": str(callback.job_id)},
        )
        # Don't fail - we generated one, but log for observability

    if not x_aequitas_correlation_id:
        logger.warning(
            "Callback received without X-Aequitas-Correlation-Id header",
            extra={"job_id": str(callback.job_id)},
        )

    # Process callback via service
    service = IntegrationJobService(db, settings)
    try:
        response = service.process_callback(
            callback=callback,
            request_id=request_id,
            correlation_id=correlation_id,
            idempotency_key=x_aequitas_idempotency_key,
        )

        logger.info(
            f"Callback processed successfully",
            extra={
                "request_id": request_id,
                "correlation_id": correlation_id,
                "job_id": str(callback.job_id),
                "records_staged": response.records_staged,
            },
        )

        return response

    except AequitasError as e:
        logger.error(
            f"Failed to process callback: {e.code}",
            extra={
                "request_id": request_id,
                "correlation_id": correlation_id,
                "job_id": str(callback.job_id),
                "error_code": e.code,
                "error_message": e.message,
            },
        )
        raise HTTPException(status_code=400, detail=make_error_envelope(e))


# ============================================================================
# Health / Status Endpoint (Optional)
# ============================================================================


@router.get("/jobs/health", status_code=200)
def integration_health(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    Health check for integration jobs subsystem.

    Returns:
        Simple status object
    """
    return {
        "status": "ok",
        "worker_url": settings.AEQUITAS_WORKER_URL,
        "phase": "1.5",
        "capabilities": ["qbo.sync_accounts"],
    }
