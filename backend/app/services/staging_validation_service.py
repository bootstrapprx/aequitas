import logging
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.errors import AequitasError
from app.db.models.staging_qbo_account import StagingQBOAccount
from app.services.normalization_service import QBOAccountNormalizationService
from app.services.mapping_engine_v1 import MappingEngineV1, MappingDecision
from app.services.company_account_service import CompanyAccountService
from app.db.models.account_mapping import AccountMapping

logger = logging.getLogger(__name__)


class ValidationResult:
    def __init__(self, status: str, errors: Optional[List[dict]] = None):
        self.status = status
        self.errors = errors or []


class StagingValidationService:
    """Performs structural validation on staging_qbo_accounts rows."""

    REQUIRED_FIELDS = ["source_account_id", "name", "raw_payload"]

    def __init__(self, db: Session):
        self.db = db

    def _validate_row(self, row: StagingQBOAccount) -> ValidationResult:
        errors: List[dict] = []

        for field in self.REQUIRED_FIELDS:
            value = getattr(row, field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append({"field": field, "code": "AEQ_QBO_STAGING_MISSING_FIELD", "message": f"{field} is required"})

        if row.raw_payload is None:
            errors.append({"field": "raw_payload", "code": "AEQ_QBO_STAGING_MISSING_PAYLOAD", "message": "raw_payload missing"})

        status = "INVALID" if errors else "VALID"
        return ValidationResult(status=status, errors=errors)

    def validate(self, company_id: Optional[UUID] = None, limit: int = 100) -> List[StagingQBOAccount]:
        query = self.db.query(StagingQBOAccount).filter(StagingQBOAccount.validation_status.is_(None))
        if company_id:
            query = query.filter(StagingQBOAccount.company_id == company_id)
        rows = query.order_by(StagingQBOAccount.imported_at).limit(limit).all()

        for row in rows:
            result = self._validate_row(row)
            row.validation_status = result.status
            row.validation_errors = result.errors if result.errors else None
            row.validated_at = datetime.utcnow()
            self.db.add(row)
        self.db.commit()
        return rows


class StagingPipelineService:
    """
    Orchestrates validation, normalization, mapping, and company account generation.
    """

    def __init__(self, db: Session):
        self.db = db
        self.validator = StagingValidationService(db)
        self.normalizer = QBOAccountNormalizationService()
        self.mapping_engine = MappingEngineV1(db)
        self.company_account_service = CompanyAccountService(db)

    def process_company(self, company_id: UUID, limit: int = 100) -> Tuple[str, int]:
        run_id = str(uuid4())
        logger.info(
            "staging_pipeline_start",
            extra={"company_id": str(company_id), "run_id": run_id},
        )

        validated_rows = self.validator.validate(company_id=company_id, limit=limit)

        processed_count = 0
        for row in validated_rows:
            try:
                self._process_row(row, run_id)
                processed_count += 1
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception(
                    "staging_pipeline_row_failed",
                    extra={
                        "company_id": str(company_id),
                        "row_id": str(row.id),
                        "run_id": run_id,
                        "error": str(exc),
                    },
                )
                row.processed = True
                row.processing_result = "FAILED"
                row.processed_at = datetime.utcnow()
                self.db.add(row)
                self.db.commit()

        logger.info(
            "staging_pipeline_complete",
            extra={"company_id": str(company_id), "run_id": run_id, "processed": processed_count},
        )
        return run_id, processed_count

    def _process_row(self, row: StagingQBOAccount, run_id: str) -> None:
        if row.validation_status != "VALID":
            row.processed = True
            row.processing_result = "FAILED"
            row.mapping_status = "UNMAPPED"
            row.processed_at = datetime.utcnow()
            self.db.add(row)
            self.db.commit()
            return

        normalized = self.normalizer.normalize_account(row)
        row.normalized_payload = normalized
        self.db.add(row)
        self.db.commit()

        decision: MappingDecision = self.mapping_engine.map_account(row.company_id, normalized)

        mapping_record: Optional[AccountMapping] = None
        company_account_id = None

        if decision.status == "AUTO_MAPPED":
            company_account = self.company_account_service.create_or_update_auto_mapped(
                company_id=row.company_id,
                staging_row=row,
                normalized_payload=normalized,
                master_account=decision.master_account,
            )
            company_account_id = company_account.id
            mapping_record = self.mapping_engine.persist_mapping(
                company_account_id=company_account.id,
                staging_id=row.id,
                decision=decision,
            )
        elif decision.status in ("NEEDS_REVIEW", "UNMAPPED"):
            company_account = self.company_account_service.create_draft_from_staging(
                company_id=row.company_id,
                staging_row=row,
                normalized_payload=normalized,
            )
            company_account_id = company_account.id
            if decision.master_account:
                mapping_record = self.mapping_engine.persist_mapping(
                    company_account_id=company_account.id,
                    staging_id=row.id,
                    decision=decision,
                )
        else:
            raise AequitasError(
                code="AEQ_QBO_MAPPING_STATE",
                message=f"Unknown mapping status {decision.status}",
                http_status=400,
            )

        row.mapping_status = decision.status
        row.company_account_id = company_account_id
        row.mapping_id = mapping_record.id if mapping_record else None
        row.processed = True
        row.processing_result = "SUCCESS" if decision.status == "AUTO_MAPPED" else "PARTIAL"
        row.processed_at = datetime.utcnow()
        self.db.add(row)
        self.db.commit()
