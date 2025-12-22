import logging
from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import AequitasError
from app.core.request_context import get_request_id, get_correlation_id
from app.db.models.account_mapping import AccountMapping
from app.db.models.company_account import CompanyAccount
from app.db.models.master_account import MasterAccount
from app.services.permission_service import PermissionService

logger = logging.getLogger(__name__)


class MappingDecisionService:
    """Human-in-the-loop decision service for account mappings."""

    def __init__(self, db: Session):
        self.db = db
        self.permission_service = PermissionService(db)

    def _get_mapping_with_account(self, mapping_id: UUID) -> AccountMapping:
        mapping = (
            self.db.query(AccountMapping)
            .join(CompanyAccount, AccountMapping.company_account_id == CompanyAccount.id)
            .filter(AccountMapping.id == mapping_id)
            .first()
        )
        if not mapping:
            raise AequitasError(
                code="AEQ_QBO_MAPPING_NOT_FOUND",
                message="Mapping not found",
                http_status=404,
            )
        return mapping

    def _assert_company_permission(self, user_id: UUID, company_id: UUID) -> None:
        if not self.permission_service.can_manage_company(user_id, company_id):
            raise AequitasError(
                code="AEQ_AUTH_FORBIDDEN",
                message="User cannot modify mappings for this company",
                http_status=403,
            )

    def list_pending_mappings(self, company_id: UUID, user_id: UUID) -> List[AccountMapping]:
        self._assert_company_permission(user_id, company_id)
        return (
            self.db.query(AccountMapping)
            .join(CompanyAccount, AccountMapping.company_account_id == CompanyAccount.id)
            .filter(
                CompanyAccount.company_id == company_id,
                AccountMapping.decision_status == "PENDING",
            )
            .order_by(AccountMapping.created_at.desc())
            .all()
        )

    def accept_mapping(self, mapping_id: UUID, user_id: UUID, reason: str) -> AccountMapping:
        mapping = self._get_mapping_with_account(mapping_id)
        self._assert_company_permission(user_id, mapping.company_account.company_id)

        if mapping.decision_status == "ACCEPTED":
            return mapping

        master_account = self._resolve_master(mapping)
        company_account = mapping.company_account
        company_account.mapped_master_account_id = master_account.id if master_account else None
        company_account.is_active = True
        self.db.add(company_account)

        mapping.decision_status = "ACCEPTED"
        mapping.decision_reason = reason
        mapping.decided_by = user_id
        mapping.decided_at = datetime.utcnow()
        mapping.previous_master_account_id = mapping.master_account_id
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def override_mapping(
        self,
        mapping_id: UUID,
        new_master_account_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> AccountMapping:
        mapping = self._get_mapping_with_account(mapping_id)
        self._assert_company_permission(user_id, mapping.company_account.company_id)

        master_account = self.db.query(MasterAccount).filter(MasterAccount.id == new_master_account_id).first()
        if not master_account:
            raise AequitasError(
                code="AEQ_QBO_MASTER_ACCOUNT_NOT_FOUND",
                message="Master account not found",
                http_status=404,
            )

        if mapping.master_account_id == new_master_account_id and mapping.decision_status == "ACCEPTED":
            return mapping

        company_account = mapping.company_account
        mapping.previous_master_account_id = mapping.master_account_id
        mapping.master_account_id = master_account.id
        mapping.master_code = master_account.code
        mapping.decision_status = "OVERRIDDEN"
        mapping.decision_reason = reason
        mapping.decided_by = user_id
        mapping.decided_at = datetime.utcnow()

        company_account.mapped_master_account_id = master_account.id
        company_account.is_active = True
        self.db.add(company_account)
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def reject_mapping(self, mapping_id: UUID, user_id: UUID, reason: str) -> AccountMapping:
        mapping = self._get_mapping_with_account(mapping_id)
        self._assert_company_permission(user_id, mapping.company_account.company_id)

        company_account = mapping.company_account
        company_account.mapped_master_account_id = None
        company_account.is_active = False
        self.db.add(company_account)

        mapping.previous_master_account_id = mapping.master_account_id
        mapping.master_account_id = None
        mapping.master_code = None
        mapping.decision_status = "REJECTED"
        mapping.decision_reason = reason
        mapping.decided_by = user_id
        mapping.decided_at = datetime.utcnow()
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def _resolve_master(self, mapping: AccountMapping) -> MasterAccount:
        if mapping.master_account_id:
            master = self.db.query(MasterAccount).filter(MasterAccount.id == mapping.master_account_id).first()
            if master:
                return master
        if mapping.master_code:
            master = self.db.query(MasterAccount).filter(MasterAccount.code == mapping.master_code).first()
            if master:
                return master
        raise AequitasError(
            code="AEQ_QBO_MASTER_ACCOUNT_NOT_FOUND",
            message="Mapping missing master account reference",
            http_status=400,
        )
