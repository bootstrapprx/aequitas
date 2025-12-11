"""Service for managing company-specific charts of accounts."""

from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.models.company_account import CompanyAccount
from app.db.models.master_account import MasterAccount
from app.schemas.company_account import CompanyAccountCreate, CompanyAccountUpdate


class CompanyChartService:
    """Service for managing company-specific charts of accounts."""

    def __init__(self, db: Session):
        self.db = db

    def get_company_chart(self, company_id: UUID, active_only: bool = True) -> List[CompanyAccount]:
        """Get all accounts for a company."""
        query = self.db.query(CompanyAccount).filter(CompanyAccount.company_id == company_id)
        if active_only:
            query = query.filter(CompanyAccount.is_active == True)
        return query.order_by(CompanyAccount.code).all()

    def get_account_by_code(self, company_id: UUID, code: str) -> Optional[CompanyAccount]:
        """Get a specific account by code for a company."""
        return self.db.query(CompanyAccount).filter(
            CompanyAccount.company_id == company_id,
            CompanyAccount.code == code
        ).first()

    def get_account_by_id(self, account_id: UUID) -> Optional[CompanyAccount]:
        """Get account by ID."""
        return self.db.query(CompanyAccount).filter(CompanyAccount.id == account_id).first()

    def create_account(self, company_id: UUID, account_data: CompanyAccountCreate) -> CompanyAccount:
        """Create a new account for a company."""
        # Check if account code already exists for this company
        existing = self.get_account_by_code(company_id, account_data.code)
        if existing:
            raise ValueError(f"Account with code {account_data.code} already exists for this company.")

        # Verify parent exists if parent_code is provided
        if account_data.parent_code:
            parent = self.get_account_by_code(company_id, account_data.parent_code)
            if not parent:
                raise ValueError(f"Parent account with code {account_data.parent_code} not found.")
            if parent.type == 'D':
                raise ValueError(f"Cannot add a child to a Detail account (code: {parent.code}).")

        create_data = account_data.model_dump()
        create_data['company_id'] = company_id

        db_account = CompanyAccount(**create_data)
        self.db.add(db_account)
        self.db.commit()
        self.db.refresh(db_account)
        return db_account

    def update_account(self, company_id: UUID, code: str, account_data: CompanyAccountUpdate) -> Optional[CompanyAccount]:
        """Update an existing account."""
        db_account = self.get_account_by_code(company_id, code)
        if not db_account:
            return None

        # If changing to Detail type, check for children
        if account_data.type == 'D':
            has_children = self.db.query(CompanyAccount).filter(
                CompanyAccount.company_id == company_id,
                CompanyAccount.parent_code == code
            ).first()
            if has_children:
                raise ValueError("Cannot change type to 'Detail' because this account has children.")

        update_data = account_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_account, key, value)

        self.db.commit()
        self.db.refresh(db_account)
        return db_account

    def delete_account(self, company_id: UUID, code: str) -> bool:
        """Delete an account (soft delete)."""
        db_account = self.get_account_by_code(company_id, code)
        if not db_account:
            return False

        # Check for children
        has_children = self.db.query(CompanyAccount).filter(
            CompanyAccount.company_id == company_id,
            CompanyAccount.parent_code == code
        ).first()
        if has_children:
            raise ValueError("Cannot delete an account that has children.")

        # Soft delete
        db_account.is_active = False
        self.db.commit()
        return True

    def build_tree(self, accounts: List[CompanyAccount]) -> List[Dict[str, Any]]:
        """
        Build a hierarchical tree structure from a flat list of accounts.
        Returns a list of dictionaries for easy JSON serialization.
        """
        account_map = {acc.code: acc for acc in accounts}
        tree_roots = []

        for acc in accounts:
            acc_dict = {
                "id": str(acc.id),
                "code": acc.code,
                "description": acc.description,
                "type": acc.type,
                "parent_code": acc.parent_code,
                "name": acc.name,
                "currency": acc.currency,
                "is_active": acc.is_active,
                "master_account_code": acc.master_account_code,
                "children": []
            }

            if acc.parent_code and acc.parent_code in account_map:
                # This account has a parent, add to parent's children
                # Note: This requires building a separate dictionary structure
                continue
            else:
                tree_roots.append(acc_dict)

        # Build children recursively
        def add_children(parent_dict: Dict, parent_code: str):
            for acc in accounts:
                if acc.parent_code == parent_code:
                    child_dict = {
                        "id": str(acc.id),
                        "code": acc.code,
                        "description": acc.description,
                        "type": acc.type,
                        "parent_code": acc.parent_code,
                        "name": acc.name,
                        "currency": acc.currency,
                        "is_active": acc.is_active,
                        "master_account_code": acc.master_account_code,
                        "children": []
                    }
                    parent_dict["children"].append(child_dict)
                    add_children(child_dict, acc.code)

        for root in tree_roots:
            add_children(root, root["code"])

        return tree_roots

    def get_chart_stats(self, company_id: UUID) -> Dict[str, Any]:
        """Get statistics about a company's chart of accounts."""
        accounts = self.get_company_chart(company_id, active_only=False)
        active_accounts = [acc for acc in accounts if acc.is_active]

        total_accounts = len(accounts)
        active_count = len(active_accounts)
        inactive_count = total_accounts - active_count
        header_count = sum(1 for acc in active_accounts if acc.type == 'H')
        detail_count = active_count - header_count

        # Count mapped accounts
        mapped_count = sum(1 for acc in active_accounts if acc.master_account_code)
        unmapped_count = active_count - mapped_count

        return {
            "total_accounts": total_accounts,
            "active_accounts": active_count,
            "inactive_accounts": inactive_count,
            "header_count": header_count,
            "detail_count": detail_count,
            "mapped_accounts": mapped_count,
            "unmapped_accounts": unmapped_count,
        }

    def initialize_from_master_chart(self, company_id: UUID) -> Dict[str, Any]:
        """
        Initialize a company's chart of accounts by copying from the master chart.
        This is called automatically when a company is created.
        """
        # Check if company already has accounts
        existing = self.get_company_chart(company_id, active_only=False)
        if existing:
            raise ValueError(f"Company already has {len(existing)} accounts. Cannot initialize.")

        # Get all master accounts
        master_accounts = self.db.query(MasterAccount).order_by(MasterAccount.code).all()

        if not master_accounts:
            raise ValueError("No master chart accounts found. Please seed the master chart first.")

        # Copy each master account to company account
        created_count = 0
        for master_acc in master_accounts:
            company_acc = CompanyAccount(
                company_id=company_id,
                code=master_acc.code,
                description=master_acc.description,
                type=master_acc.type,
                parent_code=master_acc.parent_code,
                name=master_acc.long_description or master_acc.description,
                currency="USD",  # Default currency
                is_active=True,
                master_account_code=master_acc.code,  # Link to master chart
                json_data={
                    "category": master_acc.category,
                    "normal_balance": master_acc.normal_balance,
                    "fs_mapping": master_acc.fs_mapping,
                    "initialized_from_master": True,
                }
            )
            self.db.add(company_acc)
            created_count += 1

        self.db.commit()

        return {
            "message": "Company chart of accounts initialized from master chart",
            "accounts_created": created_count,
            "source": "master_chart",
        }

    def reset_to_master_chart(self, company_id: UUID) -> Dict[str, Any]:
        """
        Reset a company's chart of accounts to match the master chart.
        This will deactivate all existing accounts and create new ones from master.
        """
        # Deactivate all existing accounts
        existing = self.get_company_chart(company_id, active_only=False)
        for acc in existing:
            acc.is_active = False

        # Get all master accounts
        master_accounts = self.db.query(MasterAccount).order_by(MasterAccount.code).all()

        # Create new accounts from master chart
        created_count = 0
        for master_acc in master_accounts:
            company_acc = CompanyAccount(
                company_id=company_id,
                code=master_acc.code,
                description=master_acc.description,
                type=master_acc.type,
                parent_code=master_acc.parent_code,
                name=master_acc.long_description or master_acc.description,
                currency="USD",
                is_active=True,
                master_account_code=master_acc.code,
                json_data={
                    "category": master_acc.category,
                    "normal_balance": master_acc.normal_balance,
                    "fs_mapping": master_acc.fs_mapping,
                    "reset_from_master": True,
                }
            )
            self.db.add(company_acc)
            created_count += 1

        self.db.commit()

        return {
            "message": "Company chart reset to master chart",
            "accounts_deactivated": len(existing),
            "accounts_created": created_count,
        }
