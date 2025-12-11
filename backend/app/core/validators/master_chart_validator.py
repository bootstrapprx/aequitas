"""
Master Chart Validator
Validates master chart accounts for integrity and GAAP compliance
"""

import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Result of validation check"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, message: str):
        """Add an error message"""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        """Add a warning message"""
        self.warnings.append(message)

    def __str__(self) -> str:
        """String representation"""
        if self.is_valid:
            status = "✓ Valid"
            if self.warnings:
                status += f" (with {len(self.warnings)} warning(s))"
            return status
        else:
            return f"✗ Invalid ({len(self.errors)} error(s), {len(self.warnings)} warning(s))"


class MasterChartValidator:
    """
    Validates master chart accounts for integrity
    Enforces GAAP compliance and hierarchical consistency
    """

    # Valid values for various fields
    VALID_ACCOUNT_TYPES = ["Header", "Detail", "H", "D"]  # Support both formats
    VALID_NORMAL_BALANCES = ["Debit", "Credit"]
    VALID_FS_MAPPINGS = ["Balance Sheet", "Income Statement", "Not Applicable", ""]
    VALID_CATEGORIES = [
        "Asset", "Liability", "Equity", "Revenue", "Expense",
        "Cost of Goods Sold", "Other Income", "Other Expense"
    ]

    def __init__(self):
        """Initialize validator"""
        pass

    def validate_account(self, account_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate single account

        Args:
            account_data: Dictionary containing account data

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(is_valid=True)

        # Required fields check
        required_fields = ["code", "account_name", "type"]
        for field in required_fields:
            if field not in account_data or not account_data[field]:
                result.add_error(f"Missing required field: {field}")

        # If basic validation failed, return early
        if not result.is_valid:
            return result

        # Code format validation
        code = account_data.get("code", "")
        if not self._validate_code_format(code):
            result.add_error(f"Invalid code format: '{code}'. Expected hierarchical format (e.g., 1, 1.10, 1.10.10)")

        # Account type validation
        account_type = account_data.get("type")
        if account_type not in self.VALID_ACCOUNT_TYPES:
            result.add_error(f"Invalid account type: '{account_type}'. Must be one of {self.VALID_ACCOUNT_TYPES}")

        # Normal balance validation (optional field)
        normal_balance = account_data.get("normal_balance")
        if normal_balance and normal_balance not in self.VALID_NORMAL_BALANCES:
            result.add_error(f"Invalid normal_balance: '{normal_balance}'. Must be 'Debit' or 'Credit'")

        # FS mapping validation (optional field)
        fs_mapping = account_data.get("fs_mapping")
        if fs_mapping and fs_mapping not in self.VALID_FS_MAPPINGS:
            result.add_warning(f"Unusual fs_mapping: '{fs_mapping}'. Expected one of {self.VALID_FS_MAPPINGS}")

        # Category validation (optional but recommended)
        category = account_data.get("category")
        if category and category not in self.VALID_CATEGORIES:
            result.add_warning(f"Unusual category: '{category}'. Expected one of {self.VALID_CATEGORIES}")

        # Account name validation
        account_name = account_data.get("account_name", "")
        if len(account_name) < 2:
            result.add_error(f"Account name too short: '{account_name}'. Minimum 2 characters")
        if len(account_name) > 200:
            result.add_warning(f"Account name very long: {len(account_name)} characters")

        # Parent code validation (if provided)
        parent_code = account_data.get("parent_code")
        if parent_code and not self._validate_code_format(parent_code):
            result.add_error(f"Invalid parent_code format: '{parent_code}'")

        # Logical consistency: Detail accounts should have parent
        if account_type in ["D", "Detail"] and not parent_code:
            result.add_warning(f"Detail account '{code}' has no parent_code")

        return result

    def validate_chart(self, accounts: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate entire chart for consistency

        Args:
            accounts: List of account dictionaries

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(is_valid=True)

        if not accounts:
            result.add_error("Chart is empty")
            return result

        # Build code index for fast lookup
        code_index = {}
        duplicate_codes = []

        for i, account in enumerate(accounts):
            code = account.get("code")
            if not code:
                result.add_error(f"Account at index {i} has no code")
                continue

            if code in code_index:
                duplicate_codes.append(code)
            else:
                code_index[code] = account

        # Check for duplicate codes
        if duplicate_codes:
            result.add_error(f"Duplicate codes found: {', '.join(duplicate_codes)}")

        # Validate each account
        for i, account in enumerate(accounts):
            account_result = self.validate_account(account)
            if not account_result.is_valid:
                for error in account_result.errors:
                    result.add_error(f"Account '{account.get('code', 'unknown')}': {error}")
            for warning in account_result.warnings:
                result.add_warning(f"Account '{account.get('code', 'unknown')}': {warning}")

        # Validate parent-child relationships
        orphaned_accounts = []
        for account in accounts:
            parent_code = account.get("parent_code")
            if parent_code and parent_code not in code_index:
                orphaned_accounts.append(account.get("code"))

        if orphaned_accounts:
            result.add_error(f"Orphaned accounts (parent not found): {', '.join(orphaned_accounts)}")

        # Check for circular dependencies
        circular_deps = self._detect_circular_dependencies(accounts)
        if circular_deps:
            result.add_error(f"Circular dependencies detected: {circular_deps}")

        # Validate hierarchy integrity (root accounts exist)
        root_accounts = [acc for acc in accounts if not acc.get("parent_code")]
        if not root_accounts:
            result.add_error("No root accounts found (accounts without parent_code)")

        return result

    def validate_parent_exists(self, parent_code: str, db_session) -> ValidationResult:
        """
        Validate that parent account exists in database

        Args:
            parent_code: Parent account code
            db_session: Database session

        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)

        if not parent_code:
            return result

        from app.db.models.master_account import MasterAccount
        parent = db_session.query(MasterAccount).filter(
            MasterAccount.code == parent_code
        ).first()

        if not parent:
            result.add_error(f"Parent account '{parent_code}' does not exist")
        elif parent.type in ["D", "Detail"]:
            result.add_error(f"Parent account '{parent_code}' is a Detail account (cannot have children)")

        return result

    def validate_code_format(self, code: str) -> ValidationResult:
        """
        Validate code format

        Args:
            code: Account code

        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)

        if not code:
            result.add_error("Code is empty")
            return result

        if not self._validate_code_format(code):
            result.add_error(f"Invalid code format: '{code}'. Expected hierarchical format (e.g., 1, 1.10, 1.10.10)")

        return result

    def _validate_code_format(self, code: str) -> bool:
        """
        Internal code format validator
        Validates hierarchical code format: X or X.XX or X.XX.XX or X.XX.XX.XX

        Args:
            code: Account code string

        Returns:
            True if valid, False otherwise
        """
        if not code:
            return False

        # Allow format: X, X.XX, X.XX.XX, X.XX.XX.XX
        # Each segment should be numeric
        pattern = r'^(\d+)(\.\d+)*$'
        if not re.match(pattern, code):
            return False

        parts = code.split(".")

        # Maximum 4 levels
        if len(parts) > 4:
            return False

        return True

    def _detect_circular_dependencies(self, accounts: List[Dict[str, Any]]) -> List[str]:
        """
        Detect circular dependencies in parent-child relationships

        Args:
            accounts: List of account dictionaries

        Returns:
            List of codes involved in circular dependencies
        """
        # Build parent map
        parent_map = {}
        for account in accounts:
            code = account.get("code")
            parent_code = account.get("parent_code")
            if code and parent_code:
                parent_map[code] = parent_code

        # Check each account for circular path
        circular_codes = []
        for code in parent_map:
            visited = set()
            current = code

            while current in parent_map:
                if current in visited:
                    # Circular dependency found
                    circular_codes.append(code)
                    break
                visited.add(current)
                current = parent_map[current]

        return circular_codes

    def validate_import_file_structure(self, data: List[Dict[str, Any]], file_type: str = "json") -> ValidationResult:
        """
        Validate import file structure

        Args:
            data: Parsed file data
            file_type: Type of file (json, csv)

        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)

        if not data:
            result.add_error("File is empty or could not be parsed")
            return result

        if not isinstance(data, list):
            result.add_error("Data must be a list of accounts")
            return result

        # Check first row for required columns
        if data:
            first_row = data[0]
            required_columns = ["code", "account_name", "type"]
            missing_columns = [col for col in required_columns if col not in first_row]

            if missing_columns:
                result.add_error(f"Missing required columns: {', '.join(missing_columns)}")

        return result
