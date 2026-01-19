"""
Service for managing company-specific charts of accounts.

PHASE 3B: Canonical schema compliance with strict immutability enforcement.
- Uses parent_id (UUID FK) for hierarchy, NOT parent_code
- Uses mapped_master_account_id (UUID FK) for master mapping, NOT master_account_code
- Enforces locked account immutability: name, type, account_type, normal_balance, parent_id
- Validates account_type only when present (nullable allowed)
- Separates validation logic from DB writes for unit testability

UPDATED: 2025-12-14 (Phase 3B - Strict Requirements)
"""

from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.models.company import Company
from app.db.models.company_account import CompanyAccount
from app.db.models.master_account import MasterAccount
from app.db.models.enums import AccountType, NormalBalance, LockedReason
from app.schemas.company_account import CompanyAccountCreate, CompanyAccountUpdate
from app.core.validators.master_chart_validator import MasterChartValidator
from app.core.normalizers.master_chart_normalizer import MasterChartNormalizer
from app.core.exceptions import ValidationError, ErrorCode
from app.core.kernel import L0_KERNEL_CODES, map_normal_balance
from app.services.validators.template_account_validator import TemplateAccountValidator
from app.services.audit_service import AuditService


class CompanyChartService:
    """
    Service for managing company-specific charts of accounts.

    CANONICAL COMPLIANCE:
    - All hierarchy operations use parent_id (UUID FK)
    - All master mappings use mapped_master_account_id (UUID FK)
    - Locked accounts enforce immutability on: name, type, account_type, normal_balance, parent_id
    - locked_by references users.id (UUID FK)
    - account_type is nullable and validated only when present
    - Validation logic is separated from DB writes for testability
    - Template-mandatory accounts enforced (Phase 3B)
    """

    # Immutable fields when account is locked
    LOCKED_IMMUTABLE_FIELDS = ['name', 'type', 'code', 'account_type', 'normal_balance', 'parent_id', 'mapped_master_account_id']

    def __init__(self, db: Session):
        self.db = db
        self.validator = MasterChartValidator()
        self.normalizer = MasterChartNormalizer()
        self.template_validator = TemplateAccountValidator(db)

    # ========================================================================
    # VALIDATION METHODS (Unit-testable, no DB writes)
    # ========================================================================

    def validate_locked_account_update(
        self,
        account: CompanyAccount,
        update_data: Dict[str, Any]
    ) -> None:
        """
        Validate that locked account updates don't modify immutable fields.

        CANONICAL RULE: When is_locked=True, the following fields are immutable:
        - name (display name)
        - type (H/D)
        - code
        - account_type (enum)
        - normal_balance (enum)
        - parent_id (hierarchy)
        - mapped_master_account_id (master mapping)

        Args:
            account: The account being updated
            update_data: Dictionary of fields to update

        Raises:
            ValidationError: If locked account immutability is violated
        """
        if not account.is_locked:
            return

        # Check each immutable field
        violations = []
        for field in self.LOCKED_IMMUTABLE_FIELDS:
            if field in update_data and update_data[field] is not None:
                current_value = getattr(account, field)
                new_value = update_data[field]

                # Handle enum comparison
                if isinstance(current_value, (AccountType, NormalBalance, LockedReason)):
                    current_value = current_value.value if current_value else None

                if new_value != current_value:
                    violations.append(f"  - {field}: cannot change from '{current_value}' to '{new_value}'")

        if violations:
            raise ValidationError(
                f"Cannot modify immutable fields on locked account.\n"
                f"Account locked: {account.locked_reason.value if account.locked_reason else 'Unknown'}\n"
                f"Locked at: {account.locked_at}\n"
                f"Locked by: {account.locked_by}\n"
                f"Attempted changes:\n" + "\n".join(violations) + "\n\n"
                f"To modify these fields, unlock the account first (requires superuser)."
            )

    def validate_parent_relationship(
        self,
        parent_id: Optional[UUID],
        company_id: UUID
    ) -> Optional[CompanyAccount]:
        """
        Validate parent account exists and belongs to same company.

        Args:
            parent_id: Parent account UUID (None for root accounts)
            company_id: Company UUID

        Returns:
            Parent CompanyAccount if valid, None if no parent

        Raises:
            ValidationError: If parent doesn't exist or belongs to different company
        """
        if not parent_id:
            return None

        parent = self.get_account_by_id(parent_id)
        if not parent:
            raise ValidationError(f"Parent account with ID {parent_id} not found.")

        if parent.company_id != company_id:
            raise ValidationError(
                f"Parent account belongs to different company.\n"
                f"Parent company: {parent.company_id}\n"
                f"Target company: {company_id}"
            )

        if parent.type == 'D':
            raise ValidationError(
                f"Cannot add child to Detail account.\n"
                f"Parent account: {parent.code} ({parent.description})\n"
                f"Detail accounts cannot have children."
            )

        return parent

    def validate_type_change_for_children(
        self,
        account: CompanyAccount,
        new_type: Optional[str]
    ) -> None:
        """
        Validate that changing to Detail type is allowed (no children).

        Args:
            account: Account being updated
            new_type: New type value ('H' or 'D')

        Raises:
            ValidationError: If changing to Detail but account has children
        """
        if new_type != 'D':
            return

        # Check for children using parent_id (UUID FK)
        has_children = self.db.query(CompanyAccount).filter(
            CompanyAccount.parent_id == account.id
        ).first()

        if has_children:
            raise ValidationError(
                f"Cannot change type to 'Detail' because account has children.\n"
                f"Account: {account.code} ({account.description})\n"
                f"Children must be removed or reparented first."
            )

    def validate_account_type_enum(
        self,
        account_type: Optional[str]
    ) -> None:
        """
        Validate account_type enum value (only when present, nullable allowed).

        CANONICAL RULE: account_type is nullable in the schema.
        When provided, must be a valid AccountType enum value.

        Args:
            account_type: Account type string or None

        Raises:
            ValidationError: If account_type is invalid
        """
        if account_type is None:
            return  # Nullable allowed

        valid_values = [e.value for e in AccountType]
        if account_type not in valid_values:
            raise ValidationError(
                f"Invalid account_type: '{account_type}'.\n"
                f"Valid values: {', '.join(valid_values)}"
            )

    def validate_deletion_constraints(
        self,
        account: CompanyAccount
    ) -> None:
        """
        Validate account can be deleted.

        CANONICAL RULES:
        - Cannot delete locked accounts
        - Cannot delete accounts with children
        - Cannot delete accounts with transactions (TODO: requires JournalEntryLine check)

        Args:
            account: Account to delete

        Raises:
            ValidationError: If deletion is not allowed
        """
        if account.code in L0_KERNEL_CODES:
            raise ValidationError(
                message=(
                    f"Cannot delete kernel account.\n"
                    f"Account: {account.code} ({account.description})\n"
                    f"L0 kernel accounts are protected and cannot be removed."
                ),
                code=ErrorCode.KERNEL_PROTECTED_ACCOUNT,
                details={"account_code": account.code}
            )

        # Check if locked
        if account.is_locked:
            raise ValidationError(
                f"Cannot delete locked account.\n"
                f"Account: {account.code} ({account.description})\n"
                f"Locked reason: {account.locked_reason.value if account.locked_reason else 'Unknown'}\n"
                f"Locked at: {account.locked_at}\n"
                f"Unlock the account first (requires superuser)."
            )

        # Check for children using parent_id (UUID FK)
        children = self.db.query(CompanyAccount).filter(
            CompanyAccount.parent_id == account.id
        ).all()

        if children:
            child_codes = [c.code for c in children[:5]]  # Show first 5
            more = f" and {len(children) - 5} more" if len(children) > 5 else ""
            raise ValidationError(
                f"Cannot delete account with children.\n"
                f"Account: {account.code} ({account.description})\n"
                f"Children: {', '.join(child_codes)}{more}\n"
                f"Remove or reparent children first."
            )

        # TODO: Check for journal entry lines
        # This requires JournalEntryLine model import
        # For now, we rely on database FK constraints

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
            List of CompanyAccount objects ordered by code
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
        Get account by code for a specific company.

        Args:
            company_id: Company UUID
            code: Account code

        Returns:
            CompanyAccount or None if not found
        """
        return self.db.query(CompanyAccount).filter(
            CompanyAccount.company_id == company_id,
            CompanyAccount.code == code
        ).first()

    def get_account_by_id(self, account_id: UUID) -> Optional[CompanyAccount]:
        """
        Get account by UUID.

        Args:
            account_id: Account UUID

        Returns:
            CompanyAccount or None if not found
        """
        return self.db.query(CompanyAccount).filter(
            CompanyAccount.id == account_id
        ).first()

    # ========================================================================
    # ACCOUNT CREATION (Phase 3B: UUID FKs, validation separation)
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

        CANONICAL COMPLIANCE:
        - Uses parent_id (UUID FK) for hierarchy
        - Uses mapped_master_account_id (UUID FK) for master mapping
        - Validates account_type only when present (nullable)
        - Separates validation from DB write

        Args:
            company_id: Company UUID
            account_data: Account creation schema
            validate: If True, run validation (default: True)
            normalize: If True, normalize names/descriptions (default: True)

        Returns:
            Created CompanyAccount

        Raises:
            ValidationError: If validation fails
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
                raise ValidationError(f"Validation failed:\n" + "\n".join(f"  - {err}" for err in validation_result.errors))

        # Check if code already exists
        existing = self.get_account_by_code(company_id, account_data.code)
        if existing:
            raise ValidationError(f"Account with code '{account_data.code}' already exists for this company.")

        # Validate parent relationship (uses parent_id UUID FK)
        if account_data.parent_id:
            self.validate_parent_relationship(account_data.parent_id, company_id)

        # Validate account_type enum (only when present, nullable allowed)
        if account_data.account_type:
            self.validate_account_type_enum(account_data.account_type)

        # Create account (DB write separated from validation)
        create_data = account_data.model_dump()
        create_data['company_id'] = company_id

        db_account = CompanyAccount(**create_data)
        self.db.add(db_account)
        self.db.commit()
        self.db.refresh(db_account)

        return db_account

    def add_account_from_master(
        self,
        company_id: UUID,
        master_account_id: UUID
    ) -> CompanyAccount:
        """
        Add a single company account from the master chart catalog.

        This is an explicit, one-account action and never bulk-imports.
        """
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValidationError("Company not found.")

        master_account = self.db.query(MasterAccount).filter(
            MasterAccount.id == master_account_id
        ).first()
        if not master_account:
            raise ValidationError("Master account not found.")

        existing = self.db.query(CompanyAccount).filter(
            CompanyAccount.company_id == company_id,
            CompanyAccount.code == master_account.code
        ).first()
        if existing:
            raise ValidationError(
                f"Account with code '{master_account.code}' already exists for this company."
            )

        parent_id = None
        if master_account.parent_id:
            parent_company = self.db.query(CompanyAccount).filter(
                CompanyAccount.company_id == company_id,
                CompanyAccount.mapped_master_account_id == master_account.parent_id
            ).first()
            if parent_company:
                parent_id = parent_company.id

        account_type = self._category_to_account_type(master_account.category)
        normal_balance = map_normal_balance(master_account.normal_balance)

        name = master_account.long_description or master_account.description or master_account.code
        description = master_account.description or name

        company_account = CompanyAccount(
            company_id=company_id,
            code=master_account.code,
            name=name,
            description=description,
            type=master_account.type or "D",
            account_type=account_type,
            normal_balance=normal_balance,
            parent_id=parent_id,
            mapped_master_account_id=master_account.id,
            template_account_id=None,
            currency=company.currency or "USD",
            is_active=True,
            is_locked=False,
            json_data={
                "category": master_account.category,
                "fs_mapping": master_account.fs_mapping,
                "cash_flow_classification": master_account.cash_flow_classification,
                "source": "master_catalog",
            }
        )

        self.db.add(company_account)
        self.db.commit()
        self.db.refresh(company_account)

        return company_account

    # ========================================================================
    # ACCOUNT UPDATES (Phase 3B: Strict locked account enforcement)
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

        CANONICAL COMPLIANCE:
        - Enforces locked account immutability (name, type, account_type, normal_balance, parent_id)
        - Uses parent_id (UUID FK) for hierarchy validation
        - Validates account_type only when present
        - Clear validation errors before DB write

        Args:
            company_id: Company UUID
            code: Account code to update
            account_data: Update schema
            normalize: If True, normalize names/descriptions (default: True)

        Returns:
            Updated CompanyAccount or None if not found

        Raises:
            ValidationError: If update violates business rules or locked account constraints
        """
        db_account = self.get_account_by_code(company_id, code)
        if not db_account:
            return None

        # Prepare update data
        update_data = account_data.model_dump(exclude_unset=True)

        # Normalize if requested
        if normalize and update_data:
            update_data = self.normalizer.normalize_account_data(update_data)

        # VALIDATION (no DB writes in this section)
        # ============================================

        # 1. Check locked account immutability
        self.validate_locked_account_update(db_account, update_data)

        # 2. Validate template restrictions (Phase 3B)
        self.template_validator.validate_account_update(db_account.id, update_data)

        # 3. Validate type change for accounts with children
        if 'type' in update_data:
            self.validate_type_change_for_children(db_account, update_data['type'])

        # 4. Validate account_type enum (only when present)
        if 'account_type' in update_data:
            self.validate_account_type_enum(update_data.get('account_type'))

        # 5. Validate parent relationship (if changing parent)
        if 'parent_id' in update_data:
            self.validate_parent_relationship(update_data['parent_id'], company_id)

        # APPLY UPDATES (DB write after all validation passes)
        # =====================================================

        for key, value in update_data.items():
            setattr(db_account, key, value)

        self.db.commit()
        self.db.refresh(db_account)

        return db_account

    # ========================================================================
    # ACCOUNT DELETION (Phase 3B: Clear validation errors)
    # ========================================================================

    def delete_account(self, company_id: UUID, code: str) -> bool:
        """
        Delete an account (soft delete).

        CANONICAL COMPLIANCE:
        - Validates deletion constraints before DB write
        - Checks for children using parent_id (UUID FK)
        - Validates template restrictions (Phase 3B)
        - Clear error messages for constraint violations

        Args:
            company_id: Company UUID
            code: Account code to delete

        Returns:
            True if deleted successfully

        Raises:
            ValidationError: If deletion violates constraints
        """
        db_account = self.get_account_by_code(company_id, code)
        if not db_account:
            raise ValidationError(f"Account with code '{code}' not found for this company.")

        # Validate deletion constraints (no DB writes)
        self.validate_deletion_constraints(db_account)

        # Validate template restrictions (Phase 3B)
        self.template_validator.validate_account_deletion(db_account.id)

        # Soft delete (DB write after validation passes)
        db_account.is_active = False
        self.db.commit()

        return True

    # ========================================================================
    # TREE BUILDING (Phase 3B: UUID-based hierarchy)
    # ========================================================================

    def build_tree(self, accounts: List[CompanyAccount]) -> List[Dict[str, Any]]:
        """
        Build hierarchical tree structure from flat account list.

        CANONICAL COMPLIANCE:
        - Uses parent_id (UUID FK) for hierarchy traversal
        - Returns parent_id and mapped_master_account_id as UUIDs (not codes)
        - Includes account_type and normal_balance enums
        - Includes locking status

        Args:
            accounts: Flat list of CompanyAccount objects

        Returns:
            List of tree root dictionaries with nested children
        """
        # Build lookup by UUID
        account_map = {acc.id: acc for acc in accounts}
        tree_roots = []

        # Build root accounts
        for acc in accounts:
            acc_dict = self._account_to_tree_dict(acc)

            # Root accounts have no parent_id
            if not acc.parent_id:
                tree_roots.append(acc_dict)

        # Build children recursively using UUID relationships
        def add_children(parent_dict: Dict, parent_id: UUID):
            for acc in accounts:
                if acc.parent_id == parent_id:
                    child_dict = self._account_to_tree_dict(acc)
                    parent_dict["children"].append(child_dict)
                    add_children(child_dict, acc.id)

        # Populate children for each root
        for root in tree_roots:
            root_id = UUID(root["id"])
            add_children(root, root_id)

        return tree_roots

    def _account_to_tree_dict(self, acc: CompanyAccount) -> Dict[str, Any]:
        """
        Convert CompanyAccount to tree dictionary representation.

        CANONICAL COMPLIANCE:
        - Returns UUIDs as strings
        - Returns enum values (not enum objects)
        - Includes locking information

        Args:
            acc: CompanyAccount object

        Returns:
            Dictionary representation for tree structure
        """
        return {
            "id": str(acc.id),
            "code": acc.code,
            "name": acc.name,
            "description": acc.description,
            "type": acc.type,
            "account_type": acc.account_type.value if acc.account_type else None,
            "normal_balance": acc.normal_balance.value if acc.normal_balance else None,
            "parent_id": str(acc.parent_id) if acc.parent_id else None,
            "mapped_master_account_id": str(acc.mapped_master_account_id) if acc.mapped_master_account_id else None,
            "is_active": acc.is_active,
            "is_locked": acc.is_locked,
            "locked_reason": acc.locked_reason.value if acc.locked_reason else None,
            "currency": acc.currency,
            "children": []
        }

    # ========================================================================
    # STATISTICS (Phase 3B: Uses UUID FK for mapping count)
    # ========================================================================

    def get_chart_stats(self, company_id: UUID) -> Dict[str, Any]:
        """
        Get statistics about company's chart of accounts.

        CANONICAL COMPLIANCE:
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
    # INITIALIZATION FROM MASTER CHART (Phase 3B: UUID-based)
    # ========================================================================

    def initialize_from_master_chart(self, company_id: UUID) -> Dict[str, Any]:
        """
        Initialize company chart from required kernel accounts.

        CANONICAL COMPLIANCE:
        - Sets mapped_master_account_id (UUID FK), NOT master_account_code
        - Sets parent_id (UUID FK), NOT parent_code
        - Builds UUID-based hierarchy relationships
        - Sets account_type and normal_balance from master chart

        Args:
            company_id: Company UUID

        Returns:
            Dictionary with initialization statistics

        Raises:
            ValidationError: If company already has accounts or master chart is empty
        """
        # Check if company already has accounts
        existing = self.get_company_chart(company_id, active_only=False)
        if existing:
            raise ValidationError(
                f"Company already has {len(existing)} accounts.\n"
                f"Cannot initialize from master chart.\n"
                f"Use reset_to_master_chart() to replace existing accounts."
            )

        # Get required kernel accounts ordered by level (parents before children)
        master_accounts = self.db.query(MasterAccount).filter(
            MasterAccount.code.in_(L0_KERNEL_CODES)
        ).order_by(
            MasterAccount.level,
            MasterAccount.code
        ).all()

        if not master_accounts:
            raise ValidationError("No master chart accounts found. Please seed the master chart first.")

        # Build mapping: master_id -> company_account for hierarchy resolution
        master_to_company_map: Dict[UUID, CompanyAccount] = {}

        # Create company accounts from master chart
        created_count = 0
        for master_acc in master_accounts:
            # Resolve parent_id using UUID FK
            parent_id = None
            if master_acc.parent_id:
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
                account_type=account_type,  # Nullable allowed
                normal_balance=normal_balance,  # Required
                parent_id=parent_id,  # UUID FK
                mapped_master_account_id=master_acc.id,  # UUID FK
                template_account_id=None,
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

            # Store mapping for parent resolution
            master_to_company_map[master_acc.id] = company_acc
            created_count += 1

        self.db.commit()

        return {
            "message": "Company chart initialized from kernel accounts",
            "accounts_created": created_count,
            "source": "kernel",
            "method": "uuid_hierarchy"
        }

    def _category_to_account_type(self, category: str) -> Optional[AccountType]:
        """
        Convert master account category to AccountType enum.

        CANONICAL COMPLIANCE:
        - Returns None for categories that don't map (nullable allowed)
        - Maps COGS to Expense

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
            "COST OF GOODS SOLD": AccountType.EXPENSE,
            "OTHER": None,  # Nullable allowed
        }
        return category_mapping.get(category.upper())

    # ========================================================================
    # ACCOUNT LOCKING (Phase 3B: New functionality)
    # ========================================================================

    def lock_account(
        self,
        account_id: UUID,
        reason: LockedReason,
        user_id: Optional[UUID] = None
    ) -> CompanyAccount:
        """
        Lock an account to prevent immutable field changes.

        CANONICAL COMPLIANCE:
        - Locked accounts cannot change: name, type, code, account_type, normal_balance, parent_id
        - locked_by must reference users.id (UUID FK)
        - locked_by required for Manual locks

        Args:
            account_id: Account UUID to lock
            reason: Locking reason (FirstTransaction, PeriodClose, Manual)
            user_id: User UUID (required for Manual locks)

        Returns:
            Locked CompanyAccount

        Raises:
            ValidationError: If account not found or invalid parameters
        """
        account = self.get_account_by_id(account_id)
        if not account:
            raise ValidationError(f"Account with ID {account_id} not found.")

        if account.is_locked:
            raise ValidationError(
                f"Account is already locked.\n"
                f"Locked reason: {account.locked_reason.value if account.locked_reason else 'Unknown'}\n"
                f"Locked at: {account.locked_at}\n"
                f"Locked by: {account.locked_by}"
            )

        if reason == LockedReason.MANUAL and not user_id:
            raise ValidationError(
                f"user_id is required for Manual locks.\n"
                f"locked_by must reference users.id (UUID FK)."
            )

        # Lock the account (calls model method)
        account.lock(reason=reason, user_id=user_id)
        self.db.commit()
        self.db.refresh(account)

        # AUDIT LOGGING: Record account lock event
        if user_id:
            audit_service = AuditService(self.db)
            audit_service.log_account_lock(
                user_id=user_id,
                account_id=account.id,
                account_code=account.code,
                account_name=account.name,
                company_id=account.company_id,
                locked_reason=reason.value
            )

        return account

    def unlock_account(
        self,
        account_id: UUID,
        user_id: UUID
    ) -> CompanyAccount:
        """
        Unlock an account (requires superuser - enforced at API layer).

        CANONICAL COMPLIANCE:
        - Only allowed if no posted transactions in current period (TODO: implement check)
        - Requires superuser privilege (enforced at API layer)

        Args:
            account_id: Account UUID to unlock
            user_id: User UUID performing unlock (for audit trail)

        Returns:
            Unlocked CompanyAccount

        Raises:
            ValidationError: If account not found or not locked
        """
        account = self.get_account_by_id(account_id)
        if not account:
            raise ValidationError(f"Account with ID {account_id} not found.")

        if not account.is_locked:
            raise ValidationError("Account is not locked.")

        # TODO: Check for posted transactions in current period
        # This requires fiscal period service integration
        # For now, allow unlock (API layer must enforce superuser privilege)

        # Unlock the account (calls model method)
        account.unlock()
        self.db.commit()
        self.db.refresh(account)

        # AUDIT LOGGING: Record account unlock event (CRITICAL SECURITY OPERATION)
        audit_service = AuditService(self.db)
        audit_service.log_account_unlock(
            user_id=user_id,
            account_id=account.id,
            account_code=account.code,
            account_name=account.name,
            company_id=account.company_id,
            unlock_reason=None  # Could be passed from API request if needed
        )

        return account

    def can_delete_account(
        self,
        account_id: UUID
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if account can be deleted (validation only, no DB write).

        CANONICAL COMPLIANCE:
        - Pure validation method (unit-testable)
        - Returns (can_delete, reason) tuple

        Args:
            account_id: Account UUID

        Returns:
            Tuple of (can_delete: bool, reason: Optional[str])
        """
        account = self.get_account_by_id(account_id)
        if not account:
            return (False, "Account not found")

        try:
            self.validate_deletion_constraints(account)
            return (True, None)
        except ValidationError as e:
            return (False, str(e))
