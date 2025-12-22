"""
Integration Job Service.

PHASE 1.5: Operational Extraction - Service Layer

Handles:
1. Triggering jobs in Go worker (Python → Go)
2. Processing callbacks from Go worker (Go → Python)
3. Staging raw external data
4. Idempotency enforcement

BOUNDARIES:
- NO accounting validation
- NO mapping or classification
- NO ledger manipulation
- ONLY transport and staging

CANONICAL REFERENCE:
- docs/canonical/API_CONTRACTS.md
- docs/canonical/LANGUAGE_MAP.md
"""
import logging
import httpx
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AequitasError
from app.db.models.staging_qbo_account import StagingQBOAccount
from app.db.models.idempotency_key import IdempotencyKey, IdempotencyStatus
from app.schemas.integrations import (
    JobTriggerRequest,
    JobTriggerResponse,
    JobCallbackPayload,
    JobCallbackResponse,
    QBOAccountRaw,
)


logger = logging.getLogger(__name__)


class IntegrationJobService:
    """
    Service for managing integration jobs with Go worker.

    RESPONSIBILITIES:
    - Trigger jobs in Go worker
    - Receive and process callbacks
    - Stage raw data
    - Enforce idempotency

    NOT RESPONSIBLE FOR:
    - Accounting validation
    - Mapping
    - Classification
    - Ledger operations
    """

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.worker_url = settings.AEQUITAS_WORKER_URL

    async def trigger_job(
        self,
        job_trigger: JobTriggerRequest,
        request_id: str,
        correlation_id: str,
        idempotency_key: Optional[str] = None,
    ) -> JobTriggerResponse:
        """
        Trigger a job in the Go worker service.

        Flow:
        1. Validate request
        2. Build canonical headers
        3. POST to Go worker /jobs
        4. Return job_id

        Args:
            job_trigger: Job trigger request
            request_id: X-Aequitas-Request-Id
            correlation_id: X-Aequitas-Correlation-Id
            idempotency_key: X-Aequitas-Idempotency-Key (optional)

        Returns:
            JobTriggerResponse with job_id from Go

        Raises:
            AequitasError: If Go worker is unreachable or rejects request
        """
        logger.info(
            f"Triggering job: {job_trigger.job_type} for company {job_trigger.company_id}",
            extra={
                "request_id": request_id,
                "correlation_id": correlation_id,
                "job_type": job_trigger.job_type,
                "company_id": str(job_trigger.company_id),
            },
        )

        # Build canonical headers
        headers = {
            "Content-Type": "application/json",
            "X-Aequitas-Request-Id": request_id,
            "X-Aequitas-Correlation-Id": correlation_id,
        }
        if idempotency_key:
            headers["X-Aequitas-Idempotency-Key"] = idempotency_key

        # Call Go worker
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.worker_url}/jobs",
                    json=job_trigger.model_dump(mode="json"),
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

            logger.info(
                f"Job triggered successfully: {data.get('job_id')}",
                extra={
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "job_id": data.get("job_id"),
                },
            )

            return JobTriggerResponse(**data)

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Go worker rejected job: {e.response.status_code}",
                extra={
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "status_code": e.response.status_code,
                    "response_body": e.response.text,
                },
            )
            raise AequitasError(
                code="AEQ_WORKER_REJECTED",
                message=f"Go worker rejected job: {e.response.text}",
            )
        except httpx.RequestError as e:
            logger.error(
                f"Failed to reach Go worker: {str(e)}",
                extra={"request_id": request_id, "correlation_id": correlation_id},
            )
            raise AequitasError(
                code="AEQ_WORKER_UNREACHABLE",
                message=f"Go worker unreachable: {str(e)}",
            )

    def process_callback(
        self,
        callback: JobCallbackPayload,
        request_id: str,
        correlation_id: str,
        idempotency_key: Optional[str] = None,
    ) -> JobCallbackResponse:
        """
        Process callback from Go worker.

        Flow:
        1. Check idempotency (if key provided)
        2. Route by job_type
        3. Stage raw data
        4. Return success response

        Args:
            callback: Callback payload from Go
            request_id: X-Aequitas-Request-Id
            correlation_id: X-Aequitas-Correlation-Id
            idempotency_key: X-Aequitas-Idempotency-Key (optional)

        Returns:
            JobCallbackResponse

        Raises:
            AequitasError: On validation or processing errors
        """
        logger.info(
            f"Processing callback: {callback.job_type} [{callback.status}]",
            extra={
                "request_id": request_id,
                "correlation_id": correlation_id,
                "job_id": str(callback.job_id),
                "job_type": callback.job_type,
                "status": callback.status,
            },
        )

        # Check idempotency
        if idempotency_key:
            existing = self._check_idempotency(
                endpoint="integrations.jobs.callback",
                key=idempotency_key,
                company_id=callback.company_id,
            )
            if existing:
                logger.info(
                    f"Idempotent callback replay detected",
                    extra={
                        "request_id": request_id,
                        "correlation_id": correlation_id,
                        "idempotency_key": idempotency_key,
                    },
                )
                return existing  # Return cached response

        # Route by job_type
        if callback.job_type == "qbo.sync_accounts":
            response = self._process_qbo_sync_accounts(
                callback, request_id, correlation_id
            )
        else:
            logger.warning(
                f"Unknown job_type: {callback.job_type}",
                extra={
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "job_type": callback.job_type,
                },
            )
            raise AequitasError(
                code="AEQ_UNKNOWN_JOB_TYPE",
                message=f"Unknown job_type: {callback.job_type}",
            )

        # Store idempotency key if provided
        if idempotency_key:
            self._store_idempotency(
                endpoint="integrations.jobs.callback",
                key=idempotency_key,
                company_id=callback.company_id,
                response_body=response.model_dump(),
            )

        return response

    def _process_qbo_sync_accounts(
        self,
        callback: JobCallbackPayload,
        request_id: str,
        correlation_id: str,
    ) -> JobCallbackResponse:
        """
        Process qbo.sync_accounts callback.

        Stages raw QuickBooks accounts without validation.

        CRITICAL:
        - NO accounting validation
        - NO mapping
        - NO classification
        - ONLY raw data staging

        Args:
            callback: Callback payload
            request_id: Request ID
            correlation_id: Correlation ID

        Returns:
            JobCallbackResponse
        """
        if callback.status == "failed":
            # Job failed in Go - log but don't crash
            logger.error(
                f"QBO sync job failed in Go worker",
                extra={
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "job_id": str(callback.job_id),
                    "errors": [e.model_dump() for e in callback.errors],
                },
            )
            return JobCallbackResponse(
                status="accepted",
                message=f"Job failed: {callback.errors[0].message if callback.errors else 'Unknown error'}",
                records_staged=0,
            )

        # Extract accounts from result
        if not callback.result or "accounts" not in callback.result:
            raise AequitasError(
                code="AEQ_INVALID_CALLBACK",
                message="Missing 'accounts' in callback result",
            )

        accounts = callback.result["accounts"]
        staged_count = 0

        # Stage each account
        for account_data in accounts:
            account = QBOAccountRaw(**account_data)

            staging_record = StagingQBOAccount(
                job_id=callback.job_id,
                request_id=UUID(request_id),
                correlation_id=UUID(correlation_id),
                company_id=callback.company_id,
                source="quickbooks",
                source_account_id=account.id,
                name=account.name,
                account_type=account.type,
                account_subtype=account.subtype,
                active=account.active,
                currency=account.currency,
                raw_payload=account_data,  # Store complete raw data
            )

            self.db.add(staging_record)
            staged_count += 1

        self.db.commit()

        logger.info(
            f"Staged {staged_count} QBO accounts",
            extra={
                "request_id": request_id,
                "correlation_id": correlation_id,
                "job_id": str(callback.job_id),
                "company_id": str(callback.company_id),
                "staged_count": staged_count,
            },
        )

        return JobCallbackResponse(
            status="accepted",
            message=f"Staged {staged_count} accounts",
            records_staged=staged_count,
        )

    def _check_idempotency(
        self, endpoint: str, key: str, company_id: UUID
    ) -> Optional[JobCallbackResponse]:
        """Check if idempotency key was already processed."""
        existing = (
            self.db.query(IdempotencyKey)
            .filter(
                IdempotencyKey.endpoint == endpoint,
                IdempotencyKey.key == key,
                IdempotencyKey.company_id == company_id,
            )
            .first()
        )

        if existing and existing.status == IdempotencyStatus.COMPLETED.value:
            return JobCallbackResponse(**existing.response_body)

        return None

    def _store_idempotency(
        self, endpoint: str, key: str, company_id: UUID, response_body: Dict[str, Any]
    ):
        """Store idempotency key for completed operation."""
        idem_record = IdempotencyKey(
            company_id=company_id,
            endpoint=endpoint,
            key=key,
            status=IdempotencyStatus.COMPLETED.value,
            response_body=response_body,
        )
        self.db.add(idem_record)
        self.db.commit()
