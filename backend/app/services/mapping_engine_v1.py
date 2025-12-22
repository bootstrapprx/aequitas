import difflib
import logging
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.master_account import MasterAccount
from app.db.models.account_mapping import AccountMapping

logger = logging.getLogger(__name__)


@dataclass
class MappingDecision:
    status: str
    master_account: Optional[MasterAccount]
    confidence: float
    reason: str


class MappingEngineV1:
    """
    Lightweight, deterministic mapping engine.

    Constraints:
    - No ML/embeddings
    - Hard type compatibility on canonical_category when provided
    - Name similarity via SequenceMatcher
    """

    def __init__(self, db: Session):
        self.db = db

    def map_account(self, company_id: UUID, normalized_payload: dict) -> MappingDecision:
        candidates = self._candidate_master_accounts(normalized_payload)
        if not candidates:
            return MappingDecision(
                status="UNMAPPED",
                master_account=None,
                confidence=0.0,
                reason="No compatible master accounts for category",
            )

        best = None
        best_score = 0.0
        for candidate in candidates:
            score = difflib.SequenceMatcher(
                None,
                normalized_payload.get("name", "").lower(),
                candidate.description.lower(),
            ).ratio()
            if score > best_score:
                best = candidate
                best_score = score

        if best is None:
            return MappingDecision(
                status="UNMAPPED",
                master_account=None,
                confidence=0.0,
                reason="No candidate matched",
            )

        if best_score >= 0.9:
            status = "AUTO_MAPPED"
            reason = "High name similarity and compatible category"
        elif best_score >= 0.6:
            status = "NEEDS_REVIEW"
            reason = "Moderate similarity; requires human review"
        else:
            status = "UNMAPPED"
            reason = "Low similarity"

        return MappingDecision(
            status=status,
            master_account=best if status != "UNMAPPED" else None,
            confidence=best_score,
            reason=reason,
        )

    def _candidate_master_accounts(self, normalized_payload: dict):
        query = self.db.query(MasterAccount)
        category = normalized_payload.get("canonical_category")
        if category:
            query = query.filter(MasterAccount.category == category)
        return query.all()

    def persist_mapping(
        self,
        company_account_id: UUID,
        staging_id: UUID,
        decision: MappingDecision,
    ) -> AccountMapping:
        mapping = AccountMapping(
            company_account_id=company_account_id,
            staging_account_id=staging_id,
            master_code=decision.master_account.code if decision.master_account else None,
            master_account_id=decision.master_account.id if decision.master_account else None,
            confidence=decision.confidence,
            status=decision.status,
            mapping_status=decision.status,
            decision_reason=decision.reason,
            source="quickbooks",
            decision_status="PENDING",
        )
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        return mapping
