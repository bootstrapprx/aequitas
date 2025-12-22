import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.company_account import CompanyAccount
from app.db.models.master_account import MasterAccount
from app.db.models.enums import AccountType, NormalBalance

logger = logging.getLogger(__name__)


class CompanyAccountService:
    """Creates or updates company accounts from staging decisions."""

    def __init__(self, db: Session):
        self.db = db

    def create_or_update_auto_mapped(
        self,
        company_id: UUID,
        staging_row,
        normalized_payload: dict,
        master_account: MasterAccount,
    ) -> CompanyAccount:
        existing = (
            self.db.query(CompanyAccount)
            .filter(
                CompanyAccount.company_id == company_id,
                CompanyAccount.code == self._source_code(staging_row),
            )
            .first()
        )

        normal_balance = self._normal_balance_from_master(master_account)
        account_type = self._account_type_from_category(master_account.category)

        if existing:
            existing.name = normalized_payload.get("name") or existing.name
            existing.description = normalized_payload.get("name") or existing.description
            existing.mapped_master_account_id = master_account.id
            existing.account_type = account_type
            existing.normal_balance = normal_balance
            existing.json_data = self._merge_json(existing.json_data, staging_row)
            self.db.add(existing)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        account = CompanyAccount(
            company_id=company_id,
            code=self._source_code(staging_row),
            name=normalized_payload.get("name"),
            description=normalized_payload.get("name") or "Imported account",
            type=master_account.type or "D",
            account_type=account_type,
            normal_balance=normal_balance,
            is_active=bool(normalized_payload.get("active", True)),
            currency=normalized_payload.get("currency") or "USD",
            mapped_master_account_id=master_account.id,
            json_data=self._merge_json({}, staging_row),
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def create_draft_from_staging(
        self,
        company_id: UUID,
        staging_row,
        normalized_payload: dict,
    ) -> CompanyAccount:
        existing = (
            self.db.query(CompanyAccount)
            .filter(
                CompanyAccount.company_id == company_id,
                CompanyAccount.code == self._source_code(staging_row),
            )
            .first()
        )
        if existing:
            return existing

        account = CompanyAccount(
            company_id=company_id,
            code=self._source_code(staging_row),
            name=normalized_payload.get("name"),
            description=normalized_payload.get("name") or "Imported account",
            type="D",
            account_type=self._account_type_from_category(normalized_payload.get("canonical_category")),
            normal_balance=NormalBalance.DEBIT,
            is_active=False,
            currency=normalized_payload.get("currency") or "USD",
            json_data=self._merge_json({}, staging_row),
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def _source_code(self, staging_row) -> str:
        return f"QBO-{staging_row.source_account_id}"

    def _merge_json(self, existing_json: Optional[dict], staging_row) -> dict:
        data = existing_json.copy() if existing_json else {}
        data.update(
            {
                "source": staging_row.source,
                "source_account_id": staging_row.source_account_id,
                "staging_id": str(staging_row.id),
                "imported_at": staging_row.imported_at.isoformat() if staging_row.imported_at else datetime.utcnow().isoformat(),
            }
        )
        return data

    def _normal_balance_from_master(self, master_account: MasterAccount) -> NormalBalance:
        if master_account.normal_balance and master_account.normal_balance.lower().startswith("c"):
            return NormalBalance.CREDIT
        if master_account.normal_balance and master_account.normal_balance.lower().startswith("d"):
            return NormalBalance.DEBIT
        # Fallback based on category
        category = (master_account.category or "").upper()
        if category in ("LIABILITY", "EQUITY", "REVENUE"):
            return NormalBalance.CREDIT
        return NormalBalance.DEBIT

    def _account_type_from_category(self, category: Optional[str]) -> Optional[AccountType]:
        if category is None:
            return None
        upper = category.upper()
        mapping = {
            "ASSET": AccountType.ASSET,
            "LIABILITY": AccountType.LIABILITY,
            "EQUITY": AccountType.EQUITY,
            "REVENUE": AccountType.REVENUE,
            "EXPENSE": AccountType.EXPENSE,
            "COGS": AccountType.EXPENSE,
        }
        return mapping.get(upper)
