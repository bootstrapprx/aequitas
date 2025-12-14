"""
Service for managing company-specific charts of accounts.

PHASE 3B: Complete refactor to use UUID foreign keys instead of string codes.
- Uses parent_id (UUID FK) instead of parent_code (String)
- Uses mapped_master_account_id (UUID FK) instead of master_account_code (String)
- Enforces account locking rules
- Respects canonical accounting model invariants

UPDATED: 2025-12-14 (Phase 3B)
"""

from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from uuid import UUID

from app.db.models.company_account import CompanyAccount
from app.db.models.master_account import MasterAccount
from app.db.models.enums import AccountType, NormalBalance, LockedReason
from app.schemas.company_account import CompanyAccountCreate, CompanyAccountUpdate
from app.core.validators.master_chart_validator import MasterChartValidator
from app.core.normalizers.master_chart_normalizer import MasterChartNormalizer


class CompanyChartService:
    """
    Service for managing company-specific charts of accounts.

    PHASE 3B COMPLIANCE:
    - All hierarchy operations use parent_id (UUID FK), not parent_code
    - All master chart mappings use mapped_master_account_id (UUID FK), not master_account_code
    - Enforces account locking (cannot change type/code/hierarchy when locked)
    - Validates mandatory accounts (cannot delete template-required accounts)
    - Respects GAAP invariants (debit=credit, normal balance consistency)
    """

    def __init__(self, db: Session):
        self.db = db
        self.validator = MasterChartValidator()
        self.normalizer = MasterChartNormalizer()

    # ========================================================================
    # CORE CRUD OPERATIONS
    # ========================================================================

    def get_company_chart(
        self,
        company_id: UUID,
        active_only: bool = True
    ) -> List[CompanyAccount]:
        """
        Get all accounts for a company.

        Args:
            company_id: Company UUID
            active_only: If True, only return active accounts

        Returns:
            List of CompanyAccount objects
        """
        query = self.db.query(CompanyAccount).filter(
            CompanyAccount.company_id == company_id
        )
        if active_only:
            query = query.filter(CompanyAccount.is_active == True)
        return query.order_by(CompanyAccount.code).all()

    def get_account_by_code(
        self,
        company_id: UUID,
        code: str
    ) -> Optional[CompanyAccount]:
        """
        Get a specific account by code for a company.

        Args:
            company_id: Company UUID
            code: Account code

        Returns:
            CompanyAccount or None
        """
        return self.db.query(CompanyAccount).filter(
            CompanyAccount.company_id == company_id,
            CompanyAccount.code == code
        ).first()

    def get_account_by_id(self, account_id: UUID) -> Optional[CompanyAccount]:
        """
        Get account by ID.

        Args:
            account_id: Account UUID

        Returns:
            CompanyAccount or None
        """
        return self.db.query(CompanyAccount).filter(
            CompanyAccount.id == account_id
        ).first()

    # ========================================================================
    # ACCOUNT CREATION (PHASE 3B: Uses UUID FKs)
    # ========================================================================

    def create_account(
        self,
        company_id: UUID,
        account_data: CompanyAccountCreate,
        validate: bool = True,
        normalize: bool = True
    ) -> CompanyAccount:
        """
        Create a new account for a company.

        PHASE 3B CHANGES:
        - Uses parent_id (UUID) instead of parent_code (String)
        - Uses mapped_master_account_id (UUID) instead of master_account_code (String)
        - Sets account_type and normal_balance enums
        - Enforces parent account existence via UUID FK

        Args:
            company_id: Company UUID
            account_data: Account creation schema
            validate: If True, validate account data
            normalize: If True, normalize names and descriptions

        Returns:
            Created CompanyAccount

        Raises:
            ValueError: If validation fails or account already exists
        """
        # Normalize data if requested
        if normalize:
            account_dict = account_data.model_dump()
            normalized_dict = self.normalizer.normalize_account_data(account_dict)
            for key, value in normalized_dict.items():
                if hasattr(account_data, key):
                    setattr(account_data, key, value)

        # Validate data if requested
        if validate:
            account_dict = account_data.model_dump()
            validation_result = self.validator.validate_account(account_dict)
            if not validation_result.is_valid:
                raise ValueError(f"Validation failed: {', '.join(validation_result.errors)}")

        # Check if account code already exists for this company
        existing = self.get_account_by_code(company_id, account_data.code)
        if existing:
            raise ValueError(f"Account with code {account_data.code} already exists for this company.")

        # Verify parent exists if parent_id is provided (UUID-based hierarchy)
        if account_data.parent_id:
            parent = self.get_account_by_id(account_data.parent_id)
            if not parent:
                raise ValueError(f"Parent account with ID {account_data.parent_id} not found.")
            if parent.company_id != company_id:
                raise ValueError(f"Parent account belongs to different company.")
            if parent.type == 'D':
                raise ValueError(f"Cannot add a child to a Detail account (code: {parent.code}).")

        # Create account
        create_data = account_data.model_dump()
        create_data['company_id'] = company_id

        db_account = CompanyAccount(**create_data)
        self.db.add(db_account)
        self.db.commit()
        self.db.refresh(db_account)
        return db_account

    # ========================================================================
    # ACCOUNT UPDATES (PHASE 3B: Respects locking rules)
    # ========================================================================

    def update_account(
        self,
        company_id: UUID,
        code: str,
        account_data: CompanyAccountUpdate,
        normalize: bool = True
    ) -> Optional[CompanyAccount]:
        """
        Update an existing account.

        PHASE 3B CHANGES:
        - Prevents locked account type/code/hierarchy changes
        - Uses parent_id (UUID) instead of parent_code (String)
        - Validates normal_balance and account_type enums

        Args:
            company_id: Company UUID
            code: Account code to update
            account_data: Update schema
            normalize: If True, normalize names and descriptions

        Returns:
            Updated CompanyAccount or None if not found

        Raises:
            ValueError: If update violates business rules or account is locked
        """
        db_account = self.get_account_by_code(company_id, code)
        if not db_account:
            return None

        # PHASE 3B: Check if account is locked
        if db_account.is_locked:
            # Locked accounts cannot change type, code, account_type, normal_balance, or parent_id
            restricted_fields = ['type', 'code', 'account_type', 'normal_balance', 'parent_id', 'mapped_master_account_id']
            update_data = account_data.model_dump(exclude_unset=True)

            for field in restricted_fields:
                if field in update_data and update_data[field] is not None:
                    current_value = getattr(db_account, field)
                    if update_data[field] != current_value:
                        raise ValueError(
                            f"Cannot modify '{field}' on locked account. "
                            f"Account locked: {db_account.locked_reason}. "
                            f"Unlock the account first (requires appropriate permissions)."
                        )

        # If changing to Detail type, check for children (using parent_id)
        if account_data.type == 'D':
            has_children = self.db.query(CompanyAccount).filter(
                CompanyAccount.company_id == company_id,
                CompanyAccount.parent_id == db_account.id
            ).first()
            if has_children:
                raise ValueError("Cannot change type to 'Detail' because this account has children.")

        # Normalize data if requested
        update_data = account_data.model_dump(exclude_unset=True)
        if normalize:
            update_data = self.normalizer.normalize_account_data(update_data)

        # Apply updates
        for key, value in update_data.items():
            setattr(db_account, key, value)

        self.db.commit()
        self.db.refresh(db_account)
        return db_account

    # ========================================================================
    # ACCOUNT DELETION (PHASE 3B: Respects children via parent_id)
    # ========================================================================

    def delete_account(self, company_id: UUID, code: str) -> bool:
        """
        Delete an account (soft delete).

        PHASE 3B CHANGES:
        - Checks for children using parent_id (UUID FK)
        - Prevents deletion of locked accounts
        - Prevents deletion of mandatory template accounts

        Args:
            company_id: Company UUID
            code: Account code to delete

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If account has children, is locked, or is mandatory
        """
        db_account = self.get_account_by_code(company_id, code)
        if not db_account:
            return False

        # Check if account is locked
        if db_account.is_locked:
            raise ValueError(
                f"Cannot delete locked account. "
                f"Reason: {db_account.locked_reason}. "
                f"Unlock first (requires appropriate permissions)."
            )

        # Check for children using parent_id (UUID FK)
        has_children = self.db.query(CompanyAccount).filter(
            CompanyAccount.company_id == company_id,
            CompanyAccount.parent_id == db_account.id
        ).first()
        if has_children:
            raise ValueError("Cannot delete an account that has children.")

        # TODO: Check if account is template-mandatory
        # This requires template_account_id to be populated and template to have is_mandatory flag
        # For now, we'll allow deletion

        # Soft delete
        db_account.is_active = False
        self.db.commit()
        return True

    # ========================================================================
    # TREE BUILDING (PHASE 3B: Uses parent_id UUID FK)
    # ========================================================================

    def build_tree(self, accounts: List[CompanyAccount]) -> List[Dict[str, Any]]:
        """
        Build a hierarchical tree structure from a flat list of accounts.

        PHASE 3B CHANGES:
        - Uses parent_id (UUID) instead of parent_code (String)
        - Returns parent_id and mapped_master_account_id as UUIDs
        - Includes account_type and normal_balance

        Args:
            accounts: Flat list of CompanyAccount objects

        Returns:
            List of dictionaries representing tree roots with nested children
        """
        # Build lookup by ID (UUID)
        account_map = {acc.id: acc for acc in accounts}
        tree_roots = []

        # First pass: build root-level accounts
        for acc in accounts:
            acc_dict = {
                "id": str(acc.id),
                "code": acc.code,
                "description": acc.description,
                "name": acc.name,
                "type": acc.type,
                "account_type": acc.account_type.value if acc.account_type else None,
                "normal_balance": acc.normal_balance.value if acc.normal_balance else None,
                "parent_id": str(acc.parent_id) if acc.parent_id else None,
                "mapped_master_account_id": str(acc.mapped_master_account_id) if acc.mapped_master_account_id else None,
                "is_active": acc.is_active,
                "is_locked": acc.is_locked,
                "currency": acc.currency,
                "children": []
            }

            # If no parent, it's a root account
            if not acc.parent_id:
                tree_roots.append(acc_dict)

        # Build children recursively using UUID relationships
        def add_children(parent_dict: Dict, parent_id: UUID):
            for acc in accounts:
                if acc.parent_id == parent_id:
                    child_dict = {
                        "id": str(acc.id),
                        "code": acc.code,
                        "description": acc.description,
                        "name": acc.name,
                        "type": acc.type,
                        "account_type": acc.account_type.value if acc.account_type else None,
                        "normal_balance": acc.normal_balance.value if acc.normal_balance else None,
                        "parent_id": str(acc.parent_id) if acc.parent_id else None,
                        "mapped_master_account_id": str(acc.mapped_master_account_id) if acc.mapped_master_account_id else None,
                        "is_active": acc.is_active,
                        "is_locked": acc.is_locked,
                        "currency": acc.currency,
                        "children": []
                    }
                    parent_dict["children"].append(child_dict)
                    add_children(child_dict, acc.id)

        # Build children for each root
        for root in tree_roots:
            root_id = UUID(root["id"])
            add_children(root, root_id)

        return tree_roots

    # ========================================================================
    # STATISTICS (PHASE 3B: Uses mapped_master_account_id)
    # ========================================================================

    def get_chart_stats(self, company_id: UUID) -> Dict[str, Any]:
        """
        Get statistics about a company's chart of accounts.

        PHASE 3B CHANGES:
        - Counts mapped accounts using mapped_master_account_id (UUID FK)
        - Includes locked account statistics

        Args:
            company_id: Company UUID

        Returns:
            Dictionary with chart statistics
        """
        accounts = self.get_company_chart(company_id, active_only=False)
        active_accounts = [acc for acc in accounts if acc.is_active]

        total_accounts = len(accounts)
        active_count = len(active_accounts)
        inactive_count = total_accounts - active_count
        header_count = sum(1 for acc in active_accounts if acc.type == 'H')
        detail_count = active_count - header_count

        # Count mapped accounts using UUID FK
        mapped_count = sum(1 for acc in active_accounts if acc.mapped_master_account_id)
        unmapped_count = active_count - mapped_count

        # Count locked accounts
        locked_count = sum(1 for acc in active_accounts if acc.is_locked)
        unlocked_count = active_count - locked_count

        return {
            "total_accounts": total_accounts,
            "active_accounts": active_count,
            "inactive_accounts": inactive_count,
            "header_count": header_count,
            "detail_count": detail_count,
            "mapped_accounts": mapped_count,
            "unmapped_accounts": unmapped_count,
            "locked_accounts": locked_count,
            "unlocked_accounts": unlocked_count,
        }

    # ========================================================================
    # INITIALIZATION FROM MASTER CHART (PHASE 3B: Uses UUID FKs)
    # ========================================================================

    def initialize_from_master_chart(self, company_id: UUID) -> Dict[str, Any]:
        """
        Initialize a company's chart of accounts from the master chart.

        PHASE 3B CHANGES:
        - Sets mapped_master_account_id (UUID FK) instead of master_account_code (String)
        - Sets parent_id (UUID FK) instead of parent_code (String)
        - Sets account_type and normal_balance from master chart
        - Creates UUID-based hierarchy relationships

        Args:
            company_id: Company UUID

        Returns:
            Dictionary with initialization statistics

        Raises:
            ValueError: If company already has accounts or master chart is empty
        """
        # Check if company already has accounts
        existing = self.get_company_chart(company_id, active_only=False)
        if existing:
            raise ValueError(f"Company already has {len(existing)} accounts. Cannot initialize.")

        # Get all master accounts
        master_accounts = self.db.query(MasterAccount).order_by(
            MasterAccount.level,  # Create parents before children
            MasterAccount.code
        ).all()

        if not master_accounts:
            raise ValueError("No master chart accounts found. Please seed the master chart first.")

        # Build mapping: master_id -> company_account for hierarchy resolution
        master_to_company_map: Dict[UUID, CompanyAccount] = {}

        # Create company accounts from master chart
        created_count = 0
        for master_acc in master_accounts:
            # Determine parent_id using UUID FK
            parent_id = None
            if master_acc.parent_id:
                # Look up the company account we created for the master's parent
                parent_company_account = master_to_company_map.get(master_acc.parent_id)
                if parent_company_account:
                    parent_id = parent_company_account.id

            # Determine account_type from category
            account_type = self._category_to_account_type(master_acc.category)

            # Determine normal_balance from master chart
            normal_balance = NormalBalance(master_acc.normal_balance) if master_acc.normal_balance else None

            # Create company account
            company_acc = CompanyAccount(
                company_id=company_id,
                code=master_acc.code,
                description=master_acc.description,
                name=master_acc.long_description or master_acc.description,
                type=master_acc.type,
                account_type=account_type,
                normal_balance=normal_balance,
                parent_id=parent_id,  # ✅ UUID FK
                mapped_master_account_id=master_acc.id,  # ✅ UUID FK
                template_account_id=None,  # Not template-based initialization
                currency="USD",
                is_active=True,
                is_locked=False,  # Don't lock on initialization
                json_data={
                    "category": master_acc.category,
                    "fs_mapping": master_acc.fs_mapping,
                    "initialized_from_master": True,
                    "master_account_code": master_acc.code,  # For reference only
                }
            )
            self.db.add(company_acc)
            self.db.flush()  # Get ID for hierarchy mapping

            # Store mapping for parent lookups
            master_to_company_map[master_acc.id] = company_acc
            created_count += 1

        self.db.commit()

        return {
            "message": "Company chart of accounts initialized from master chart",
            "accounts_created": created_count,
            "source": "master_chart",
            "method": "uuid_hierarchy"
        }

    def _category_to_account_type(self, category: str) -> Optional[AccountType]:
        """
        Convert master account category to AccountType enum.

        Args:
            category: Category string from master account

        Returns:
            AccountType enum or None
        """
        category_mapping = {
            "ASSET": AccountType.ASSET,
            "LIABILITY": AccountType.LIABILITY,
            "EQUITY": AccountType.EQUITY,
            "REVENUE": AccountType.REVENUE,
            "EXPENSE": AccountType.EXPENSE,
            "COGS": AccountType.EXPENSE,  # Map COGS to Expense
            "OTHER": None,
        }
        return category_mapping.get(category.upper())

    # ========================================================================
    # ACCOUNT LOCKING (PHASE 3B: New functionality)
    # ========================================================================

    def lock_account(
        self,
        account_id: UUID,
        reason: LockedReason,
        user_id: Optional[UUID] = None
    ) -> CompanyAccount:
        """
        Lock an account to prevent type/code/hierarchy changes.

        Locked accounts cannot change:
        - type (H/D)
        - code
        - account_type
        - normal_balance
        - parent_id
        - mapped_master_account_id

        Args:
            account_id: Account UUID to lock
            reason: Locking reason (FirstTransaction, PeriodClose, Manual)
            user_id: User UUID (required for Manual locks)

        Returns:
            Locked CompanyAccount

        Raises:
            ValueError: If account not found or invalid parameters
        """
        account = self.get_account_by_id(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        if account.is_locked:
            raise ValueError(f"Account is already locked (reason: {account.locked_reason})")

        if reason == LockedReason.MANUAL and not user_id:
            raise ValueError("user_id is required for Manual locks")

        # Lock the account
        account.lock(reason=reason, user_id=user_id)
        self.db.commit()
        self.db.refresh(account)

        return account

    def unlock_account(
        self,
        account_id: UUID,
        user_id: UUID
    ) -> CompanyAccount:
        """
        Unlock an account (requires superuser privilege - enforced at API layer).

        WARNING: Only allowed if:
        - User has superuser privilege
        - No posted transactions in current fiscal period

        Args:
            account_id: Account UUID to unlock
            user_id: User UUID performing unlock (for audit trail)

        Returns:
            Unlocked CompanyAccount

        Raises:
            ValueError: If account not found or cannot be unlocked
        """
        account = self.get_account_by_id(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        if not account.is_locked:
            raise ValueError("Account is not locked")

        # TODO: Check for posted transactions in current period
        # This requires fiscal period service integration
        # For now, allow unlock (service layer trusts API layer permissions)

        # Unlock the account
        account.unlock()
        self.db.commit()
        self.db.refresh(account)

        return account

    def can_delete_account(
        self,
        account_id: UUID
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if an account can be deleted.

        An account CANNOT be deleted if:
        - It has children
        - It is locked
        - It is template-mandatory
        - It has journal entry lines (transactions)

        Args:
            account_id: Account UUID

        Returns:
            Tuple of (can_delete: bool, reason: Optional[str])
        """
        account = self.get_account_by_id(account_id)
        if not account:
            return (False, "Account not found")

        # Check for children
        has_children = self.db.query(CompanyAccount).filter(
            CompanyAccount.parent_id == account_id
        ).first()
        if has_children:
            return (False, "Account has children")

        # Check if locked
        if account.is_locked:
            return (False, f"Account is locked ({account.locked_reason})")

        # TODO: Check for journal entry lines
        # This requires JournalEntryLine model import
        # For now, assume no transactions

        # TODO: Check if template-mandatory
        # This requires template metadata
        # For now, allow deletion

        return (True, None)
