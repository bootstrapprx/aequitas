"""
Unified Master Chart Service
Handles CRUD operations, AI integration, tree building, and validation
for the Master Chart of Accounts

This service consolidates functionality from both the AI-focused and CRUD-focused
implementations, providing a complete interface for all master chart operations.
"""

import pandas as pd
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from uuid import UUID

from app.db.models.master_account import MasterAccount
from app.schemas.master_account import MasterAccountCreate, MasterAccountUpdate
from app.core.validators.master_chart_validator import MasterChartValidator, ValidationResult
from app.core.normalizers.master_chart_normalizer import MasterChartNormalizer


class MasterChartService:
    """
    Unified Master Chart Service

    Provides comprehensive master chart management including:
    - CRUD operations (create, read, update, delete)
    - Tree operations (hierarchy building, parent-child relationships)
    - AI/Dexter integration (account suggestions, keyword search)
    - Validation and normalization
    - Statistics and reporting
    """

    def __init__(self, db: Session):
        """
        Initialize service with database session

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.validator = MasterChartValidator()
        self.normalizer = MasterChartNormalizer()

        # Code generator pattern (lazy loaded to avoid circular imports)
        self._pattern = None

    @property
    def pattern(self):
        """Lazy load code generator pattern"""
        if self._pattern is None:
            from app.services.code_generator.patterns import get_active_pattern
            self._pattern = get_active_pattern()
        return self._pattern

    # ========================================
    # BASIC CRUD OPERATIONS
    # ========================================

    def get_all_accounts(self, include_headers: bool = True) -> List[MasterAccount]:
        """
        Get all master accounts

        Args:
            include_headers: If True, include header accounts. Default True.

        Returns:
            List of MasterAccount objects ordered by code
        """
        query = self.db.query(MasterAccount)
        if not include_headers:
            # Support both 'D' and 'Detail' formats
            query = query.filter(or_(
                MasterAccount.type == 'D',
                MasterAccount.type == 'Detail'
            ))
        return query.order_by(MasterAccount.code).all()

    def get_account_by_code(self, code: str) -> Optional[MasterAccount]:
        """
        Get a specific account by its code

        Args:
            code: Account code (e.g., "1.10.10")

        Returns:
            MasterAccount object or None if not found
        """
        return self.db.query(MasterAccount).filter(
            MasterAccount.code == code
        ).first()

    def get_account_by_id(self, account_id: UUID) -> Optional[MasterAccount]:
        """
        Get account by ID

        Args:
            account_id: Account UUID

        Returns:
            MasterAccount object or None if not found
        """
        return self.db.query(MasterAccount).filter(
            MasterAccount.id == account_id
        ).first()

    def get_categories(self) -> List[str]:
        """
        Get all unique categories

        Returns:
            List of category names
        """
        categories = self.db.query(MasterAccount.category).distinct().all()
        return [cat[0] for cat in categories if cat[0]]

    # ========================================
    # TREE OPERATIONS
    # ========================================

    def get_children(self, parent_code: str) -> List[MasterAccount]:
        """
        Get all direct children of a given parent code

        Args:
            parent_code: Parent account code

        Returns:
            List of child MasterAccount objects
        """
        return self.db.query(MasterAccount).filter(
            MasterAccount.parent_code == parent_code
        ).all()

    def build_tree(self, accounts: List[MasterAccount]) -> List[MasterAccount]:
        """
        Build a hierarchical tree structure from flat list of accounts

        This method modifies the account objects by setting their 'children' attribute
        to create a tree structure. The ORM objects are returned for Pydantic serialization.

        Args:
            accounts: Flat list of MasterAccount objects

        Returns:
            List of root MasterAccount objects with children populated
        """
        # Create ID-based lookup map
        account_map = {acc.id: acc for acc in accounts}

        # Clear existing children to avoid duplication
        for acc in accounts:
            acc.children = []

        # Build tree by linking children to parents
        tree_roots = []
        for acc in accounts:
            if acc.parent_id and acc.parent_id in account_map:
                parent = account_map[acc.parent_id]
                parent.children.append(acc)
            else:
                tree_roots.append(acc)

        # Sort children by code for consistent ordering
        for acc in accounts:
            if acc.children:
                acc.children.sort(key=lambda x: x.code)

        return tree_roots

    def get_account_tree(self) -> List[Dict[str, Any]]:
        """
        Get complete account tree as dictionary structure

        IMPORTANT: This method is required by QBO integration (accounts_export.py)
        Returns tree as serializable dictionaries rather than ORM objects

        Returns:
            List of root account dictionaries with nested children
        """
        accounts = self.get_all_accounts(include_headers=True)
        tree_roots = self.build_tree(accounts)

        # Convert ORM objects to dictionaries
        def account_to_dict(account: MasterAccount) -> Dict[str, Any]:
            """Convert account and its children to dictionary"""
            return {
                "id": str(account.id),
                "code": account.code,
                "account_name": account.account_name,
                "description": account.description,
                "type": account.type,
                "category": account.category,
                "normal_balance": account.normal_balance,
                "fs_mapping": account.fs_mapping,
                "parent_code": account.parent_code,
                "level": account.level,
                "children": [account_to_dict(child) for child in account.children] if account.children else []
            }

        return [account_to_dict(root) for root in tree_roots]

    def rebuild_hierarchy(self) -> Dict[str, Any]:
        """
        Rebuild parent-child hierarchy for all accounts

        Recalculates level and parent_id based on account codes
        Useful after bulk imports or code changes

        Returns:
            Dictionary with rebuild statistics
        """
        accounts = self.get_all_accounts()
        account_map_by_code: Dict[str, MasterAccount] = {acc.code: acc for acc in accounts}

        updated_count = 0
        for account in accounts:
            # Recalculate level from code
            account.level = self.pattern.get_level_from_code(account.code)

            # Recalculate parent_code from code pattern
            account.parent_code = self.pattern.get_parent_code(account.code)

            # Set parent_id if parent exists
            if account.parent_code and account.parent_code in account_map_by_code:
                account.parent_id = account_map_by_code[account.parent_code].id
            else:
                account.parent_id = None

            updated_count += 1

        self.db.commit()

        return {
            "status": "success",
            "accounts_updated": updated_count,
            "total_accounts": len(accounts)
        }

    # ========================================
    # CREATE, UPDATE, DELETE
    # ========================================

    def create_account(
        self,
        account_data: MasterAccountCreate,
        validate: bool = True,
        normalize: bool = True
    ) -> MasterAccount:
        """
        Create new master account with validation and normalization

        Args:
            account_data: Account creation schema
            validate: If True, validate before creating
            normalize: If True, normalize names and descriptions

        Returns:
            Created MasterAccount object

        Raises:
            ValueError: If validation fails or account already exists
        """
        # Normalize data if requested
        if normalize:
            account_dict = account_data.model_dump()
            normalized_dict = self.normalizer.normalize_account_data(account_dict)
            account_data = MasterAccountCreate(**normalized_dict)

        # Validate if requested
        if validate:
            validation_result = self.validator.validate_account(account_data.model_dump())
            if not validation_result.is_valid:
                raise ValueError(f"Validation failed: {', '.join(validation_result.errors)}")

        # Generate code if not provided
        code = account_data.code
        if not code:
            code_generator = self._get_code_generator_service()
            try:
                generated = code_generator.generate_new_code(
                    parent_code=account_data.parent_code
                )
                code = generated["code"]
                account_data.code = code
            except Exception as e:
                raise ValueError(f"Failed to auto-generate code: {e}")

        # Check for duplicates
        if self.get_account_by_code(code):
            raise ValueError(f"Account with code {code} already exists")

        # Determine parent and level
        final_parent_code = self.pattern.get_parent_code(code)
        level = self.pattern.get_level_from_code(code)

        parent = None
        parent_id = None
        if final_parent_code:
            parent = self.get_account_by_code(final_parent_code)
            if parent:
                # Validate parent is not a detail account
                if parent.type in ['D', 'Detail']:
                    raise ValueError(f"Cannot add child to Detail account (code: {parent.code})")
                parent_id = parent.id

        account_data.parent_code = final_parent_code

        # Create account
        create_data = account_data.model_dump()
        db_account = MasterAccount(
            **create_data,
            level=level,
            parent_id=parent_id
        )

        self.db.add(db_account)
        self.db.commit()
        self.db.refresh(db_account)

        return db_account

    def update_account(
        self,
        code: str,
        account_data: MasterAccountUpdate,
        normalize: bool = True
    ) -> Optional[MasterAccount]:
        """
        Update existing master account

        Args:
            code: Account code to update
            account_data: Update schema
            normalize: If True, normalize names and descriptions

        Returns:
            Updated MasterAccount object or None if not found

        Raises:
            ValueError: If update would violate business rules
        """
        db_account = self.get_account_by_code(code)
        if not db_account:
            return None

        # Validate type change (cannot change Header with children to Detail)
        if account_data.type in ['D', 'Detail']:
            has_children = self.db.query(MasterAccount).filter(
                MasterAccount.parent_id == db_account.id
            ).first()
            if has_children:
                raise ValueError("Cannot change type to 'Detail' because this account has children")

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

    def delete_account(self, code: str) -> bool:
        """
        Delete master account

        Args:
            code: Account code to delete

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If account has children
        """
        db_account = self.get_account_by_code(code)
        if not db_account:
            return False

        # Check for children
        has_children = self.db.query(MasterAccount).filter(
            MasterAccount.parent_id == db_account.id
        ).first()
        if has_children:
            raise ValueError("Cannot delete an account that has children")

        self.db.delete(db_account)
        self.db.commit()
        return True

    # ========================================
    # AI/DEXTER INTEGRATION
    # ========================================

    def get_accounts_for_ai(self, include_headers: bool = False) -> List[Dict[str, Any]]:
        """
        Get all master accounts in AI-friendly format for DEXTER

        Args:
            include_headers: If True, include header accounts

        Returns:
            List of simplified dicts optimized for AI processing
        """
        accounts = self.get_all_accounts(include_headers=include_headers)
        return [account.to_ai_context() for account in accounts if hasattr(account, 'to_ai_context')]

    def suggest_accounts(
        self,
        description: str,
        vendor: Optional[str] = None,
        amount: Optional[float] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Suggest accounts based on transaction description and optional vendor
        Main method DEXTER should use for account suggestions

        Args:
            description: Transaction description
            vendor: Optional vendor name
            amount: Optional transaction amount (for future heuristics)
            limit: Maximum number of suggestions to return

        Returns:
            List of suggested accounts with confidence scores
        """
        suggestions = []

        # 1. If vendor is provided, check vendor mappings first
        if vendor:
            vendor_matches = self.search_by_vendor(vendor)
            for acc in vendor_matches[:limit]:
                account_data = acc.to_ai_context() if hasattr(acc, 'to_ai_context') else {
                    "code": acc.code,
                    "name": acc.account_name,
                    "description": acc.description,
                    "category": acc.category
                }
                suggestions.append({
                    "account": account_data,
                    "confidence": 0.9,
                    "reason": f"Vendor '{vendor}' commonly uses this account",
                    "match_type": "vendor"
                })

        # 2. Search by keywords from description
        if len(suggestions) < limit:
            keywords = description.lower().split()
            keyword_matches = self.search_by_keywords(keywords, limit=limit*2)

            for acc in keyword_matches:
                # Skip if already in suggestions
                if any(s["account"]["code"] == acc.code for s in suggestions):
                    continue

                account_data = acc.to_ai_context() if hasattr(acc, 'to_ai_context') else {
                    "code": acc.code,
                    "name": acc.account_name,
                    "description": acc.description,
                    "category": acc.category
                }
                suggestions.append({
                    "account": account_data,
                    "confidence": 0.7,
                    "reason": "Description matches account keywords",
                    "match_type": "keyword"
                })

                if len(suggestions) >= limit:
                    break

        # 3. Sort by confidence and return top results
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        return suggestions[:limit]

    def search_by_keywords(self, keywords: List[str], limit: int = 10) -> List[MasterAccount]:
        """
        Search master accounts by keywords
        Searches in description, long_description, tags, and default_vendors

        Args:
            keywords: List of keywords to search for
            limit: Maximum number of results to return

        Returns:
            List of matching MasterAccount objects
        """
        if not keywords:
            return []

        # Get all detail accounts
        accounts = self.db.query(MasterAccount).filter(
            or_(MasterAccount.type == 'D', MasterAccount.type == 'Detail')
        ).all()

        # Filter by keywords using the model's method (if available)
        matches = []
        for acc in accounts:
            if hasattr(acc, 'matches_keywords') and acc.matches_keywords(keywords):
                matches.append(acc)

        return matches[:limit]

    def search_by_vendor(self, vendor_name: str) -> List[MasterAccount]:
        """
        Find accounts associated with a specific vendor
        Useful for automatic account suggestion based on vendor

        Args:
            vendor_name: Vendor name to search for

        Returns:
            List of matching MasterAccount objects
        """
        if not vendor_name:
            return []

        # Get accounts with vendor mappings
        accounts = self.db.query(MasterAccount).filter(
            MasterAccount.default_vendors.isnot(None)
        ).all()

        # Filter by vendor using the model's method (if available)
        matches = []
        for acc in accounts:
            if hasattr(acc, 'matches_vendor') and acc.matches_vendor(vendor_name):
                matches.append(acc)

        return matches

    # ========================================
    # CLASSIFICATION & FILTERING
    # ========================================

    def get_accounts_by_category(self, category: str) -> List[MasterAccount]:
        """
        Get all accounts in a specific category

        Args:
            category: Category name (e.g., "Asset", "Expense", "Revenue")

        Returns:
            List of MasterAccount objects
        """
        return self.db.query(MasterAccount).filter(
            and_(
                MasterAccount.category == category,
                or_(MasterAccount.type == 'D', MasterAccount.type == 'Detail')
            )
        ).order_by(MasterAccount.code).all()

    def get_accounts_by_fs_mapping(self, fs_type: str) -> List[MasterAccount]:
        """
        Get accounts by financial statement mapping

        Args:
            fs_type: "Balance Sheet" or "Income Statement"

        Returns:
            List of MasterAccount objects
        """
        return self.db.query(MasterAccount).filter(
            and_(
                MasterAccount.fs_mapping == fs_type,
                or_(MasterAccount.type == 'D', MasterAccount.type == 'Detail')
            )
        ).order_by(MasterAccount.code).all()

    def get_accounts_by_normal_balance(self, balance_type: str) -> List[MasterAccount]:
        """
        Get accounts by normal balance type

        Args:
            balance_type: "Debit" or "Credit"

        Returns:
            List of MasterAccount objects
        """
        return self.db.query(MasterAccount).filter(
            and_(
                MasterAccount.normal_balance == balance_type,
                or_(MasterAccount.type == 'D', MasterAccount.type == 'Detail')
            )
        ).order_by(MasterAccount.code).all()

    def get_expense_accounts_with_vendors(self) -> List[MasterAccount]:
        """
        Get all expense accounts that have vendor mappings
        Useful for building vendor-to-account rules

        Returns:
            List of MasterAccount objects
        """
        return self.db.query(MasterAccount).filter(
            and_(
                MasterAccount.category == 'Expense',
                MasterAccount.default_vendors.isnot(None),
                or_(MasterAccount.type == 'D', MasterAccount.type == 'Detail')
            )
        ).order_by(MasterAccount.code).all()

    # ========================================
    # STATISTICS & REPORTING
    # ========================================

    def get_category_summary(self) -> Dict[str, int]:
        """
        Get a summary of accounts by category

        Returns:
            Dict mapping category names to account counts
        """
        results = self.db.query(
            MasterAccount.category,
            func.count(MasterAccount.id)
        ).filter(
            or_(MasterAccount.type == 'D', MasterAccount.type == 'Detail')
        ).group_by(
            MasterAccount.category
        ).all()

        return {category: count for category, count in results}

    def get_master_chart_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the master chart
        Useful for dashboard and reporting

        Returns:
            Dict with various statistics including enrichment coverage
        """
        total_accounts = self.db.query(MasterAccount).count()

        headers = self.db.query(MasterAccount).filter(
            or_(MasterAccount.type == 'H', MasterAccount.type == 'Header')
        ).count()

        details = self.db.query(MasterAccount).filter(
            or_(MasterAccount.type == 'D', MasterAccount.type == 'Detail')
        ).count()

        with_vendors = self.db.query(MasterAccount).filter(
            MasterAccount.default_vendors.isnot(None)
        ).count()

        with_tags = self.db.query(MasterAccount).filter(
            MasterAccount.tags.isnot(None)
        ).count()

        category_summary = self.get_category_summary()

        return {
            "total_accounts": total_accounts,
            "header_accounts": headers,
            "detail_accounts": details,
            "accounts_with_vendors": with_vendors,
            "accounts_with_tags": with_tags,
            "category_breakdown": category_summary,
            "enrichment_coverage": {
                "vendor_mappings": f"{(with_vendors/details*100):.1f}%" if details > 0 else "0%",
                "ai_tags": f"{(with_tags/details*100):.1f}%" if details > 0 else "0%",
            }
        }

    def get_coa_stats(self) -> Dict[str, Any]:
        """
        Get chart of accounts statistics with orphan detection

        Returns:
            Dict with statistics including orphans
        """
        accounts = self.get_all_accounts()
        total_accounts = len(accounts)

        header_count = sum(1 for acc in accounts if acc.type in ['H', 'Header'])
        detail_count = total_accounts - header_count
        max_depth = max((acc.level for acc in accounts), default=0)

        # Create set of all codes for O(1) lookup
        all_codes = {acc.code for acc in accounts}

        # Identify orphans (accounts with parent_code that doesn't exist)
        orphans = [
            acc.code for acc in accounts
            if acc.parent_code and acc.parent_code not in all_codes
        ]

        return {
            "total_accounts": total_accounts,
            "header_count": header_count,
            "detail_count": detail_count,
            "max_depth": max_depth,
            "orphans": len(orphans),
            "orphan_codes": orphans,
        }

    def get_accounts_as_dataframe(self) -> pd.DataFrame:
        """
        Returns all accounts as a pandas DataFrame
        Useful for analysis and export

        Returns:
            DataFrame with all account data
        """
        accounts = self.get_all_accounts()
        account_dicts = []

        for acc in accounts:
            if hasattr(acc, 'as_dict'):
                account_dicts.append(acc.as_dict())
            else:
                # Fallback if as_dict method doesn't exist
                account_dicts.append({
                    "id": str(acc.id),
                    "code": acc.code,
                    "account_name": acc.account_name,
                    "description": acc.description,
                    "type": acc.type,
                    "category": acc.category,
                    "normal_balance": acc.normal_balance,
                    "fs_mapping": acc.fs_mapping,
                    "parent_code": acc.parent_code,
                    "level": acc.level
                })

        return pd.DataFrame(account_dicts)

    # ========================================
    # HELPER METHODS
    # ========================================

    def _get_code_generator_service(self):
        """
        Lazy load CodeGeneratorService to prevent circular imports

        Returns:
            CodeGeneratorService instance
        """
        from app.services.code_generator.service import CodeGeneratorService
        return CodeGeneratorService(self.db)
