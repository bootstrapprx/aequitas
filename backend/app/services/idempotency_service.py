from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AequitasError
from app.db.models import IdempotencyKey, IdempotencyStatus


class IdempotencyService:
    """Helper for enforcing idempotent behavior on endpoints."""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create(
        self,
        *,
        company_id: Optional[UUID],
        endpoint: str,
        key: str,
    ) -> Tuple[IdempotencyKey, bool]:
        """
        Return an existing idempotency record or create one.

        Returns tuple of (record, created_bool).
        """
        existing = (
            self.db.query(IdempotencyKey)
            .filter(
                IdempotencyKey.company_id == company_id,
                IdempotencyKey.endpoint == endpoint,
                IdempotencyKey.key == key,
            )
            .first()
        )
        if existing:
            return existing, False

        record = IdempotencyKey(
            company_id=company_id,
            endpoint=endpoint,
            key=key,
            status=IdempotencyStatus.ACCEPTED.value,
        )
        self.db.add(record)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            existing = (
                self.db.query(IdempotencyKey)
                .filter(
                    IdempotencyKey.company_id == company_id,
                    IdempotencyKey.endpoint == endpoint,
                    IdempotencyKey.key == key,
                )
                .first()
            )
            if existing:
                return existing, False
            raise
        self.db.refresh(record)
        return record, True

    def mark_completed(self, record: IdempotencyKey, response_body: Dict[str, Any]) -> None:
        """Persist a completed response for reuse."""
        record.status = IdempotencyStatus.COMPLETED.value
        record.response_body = response_body
        self.db.add(record)
        self.db.commit()

    def mark_failed(self, record: IdempotencyKey, details: Optional[Dict[str, Any]] = None) -> None:
        """Mark an idempotent request as failed to block reuse."""
        record.status = IdempotencyStatus.FAILED.value
        record.response_body = details or {}
        self.db.add(record)
        self.db.commit()

    def resolve_existing(self, record: IdempotencyKey) -> Dict[str, Any]:
        """
        Decide what to return for an existing key.

        - completed: return stored response
        - accepted: signal in-progress conflict
        - failed: prevent reuse with conflict
        """
        if record.status == IdempotencyStatus.COMPLETED.value and record.response_body is not None:
            return record.response_body

        if record.status == IdempotencyStatus.ACCEPTED.value:
            raise AequitasError(
                code="AEQ_QBO_IDEMPOTENCY_IN_PROGRESS",
                message="An import is already in progress for this key.",
                details={
                    "status": record.status,
                    "key": record.key,
                    "endpoint": record.endpoint,
                },
                http_status=409,
            )

        if record.status == IdempotencyStatus.FAILED.value:
            raise AequitasError(
                code="AEQ_QBO_IDEMPOTENCY_FAILED",
                message="Previous request failed. Use a new idempotency key.",
                details={
                    "status": record.status,
                    "key": record.key,
                    "endpoint": record.endpoint,
                },
                http_status=409,
            )

        raise AequitasError(
            code="AEQ_QBO_IDEMPOTENCY_UNKNOWN_STATE",
            message="Unknown idempotency state.",
            details={"status": record.status},
            http_status=409,
        )
