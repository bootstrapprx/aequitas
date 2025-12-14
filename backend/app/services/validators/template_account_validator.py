"""
TemplateAccountValidator - Enforce template-based account rules.

CANONICAL COMPLIANCE:
- Phase 3B: Template-based account enforcement
- Each company must reference one active chart_template
- Mandatory template accounts must exist in company_accounts
- Mandatory accounts have strict mutation rules

TEMPLATE RULES:
- Mandatory accounts cannot be deleted
- Mandatory accounts cannot change normal_balance
- Mandatory accounts cannot change mapped_master_account_id
- Non-mandatory accounts remain fully editable

ENFORCEMENT POINTS:
- Company creation: All mandatory template accounts must exist
- Account deletion: Mandatory accounts cannot be deleted
- Account update: Mandatory accounts have restricted fields
"""

from typing import List, Dict, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.exceptions import ValidationError, ErrorCode


class TemplateAccountValidator:
    """
    Validator for template-based account enforcement.

    CANONICAL COMPLIANCE:
    - Validates mandatory template account existence
    - Prevents deletion of mandatory accounts
    - Prevents mutation of restricted fields on mandatory accounts
    - Ensures company-template relationship integrity
    """

    def __init__(self, db: Session):
        """
        Initialize validator with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_company_template(self, company_id: UUID) -> Optional[UUID]:
        """
        Get the active template ID for a company.

        Args:
            company_id: Company UUID

        Returns:
            Template UUID if company has an active template, None otherwise

        Raises:
            ValidationError: If company has no active template
        """
        from app.db.models.company import Company

        # Get company
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValidationError(
                message=f"Company {company_id} not found",
                code=ErrorCode.PERMISSION_DENIED
            )

        # Check for active template via company_template_usage
        from app.db.models import CompanyTemplateUsage

        usage = self.db.query(CompanyTemplateUsage).filter(
            CompanyTemplateUsage.company_id == company_id
        ).first()

        if not usage:
            return None

        return usage.template_id

    def get_mandatory_template_accounts(self, template_id: UUID) -> List[Dict]:
        """
        Get all mandatory accounts for a template.

        Args:
            template_id: Template UUID

        Returns:
            List of mandatory account dictionaries with:
            - id: Template account ID
            - code: Account code
            - name: Account name
            - master_account_id: Mapped master account ID
            - normal_balance: Expected normal balance
        """
        from app.db.models import ChartTemplateAccount

        mandatory_accounts = self.db.query(ChartTemplateAccount).filter(
            and_(
                ChartTemplateAccount.template_id == template_id,
                ChartTemplateAccount.is_mandatory == True
            )
        ).all()

        return [
            {
                "id": acc.id,
                "code": acc.code,
                "name": acc.name,
                "master_account_id": acc.master_account_id,
                # Note: normal_balance comes from master_account
            }
            for acc in mandatory_accounts
        ]

    def validate_company_has_mandatory_accounts(
        self,
        company_id: UUID,
        template_id: Optional[UUID] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that company has all mandatory template accounts.

        Args:
            company_id: Company UUID
            template_id: Template UUID (if None, will look up company's template)

        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if all mandatory accounts exist
            - (False, error_message) if missing mandatory accounts

        CANONICAL RULE:
        - All mandatory template accounts must exist in company_accounts
        - Company accounts must reference the template account via template_account_id
        """
        # Get template ID if not provided
        if template_id is None:
            template_id = self.get_company_template(company_id)
            if template_id is None:
                # Company has no template - no validation needed
                return (True, None)

        # Get mandatory accounts from template
        mandatory_accounts = self.get_mandatory_template_accounts(template_id)
        if not mandatory_accounts:
            # No mandatory accounts - validation passes
            return (True, None)

        # Check each mandatory account exists in company_accounts
        from app.db.models.company_account import CompanyAccount

        missing_accounts = []
        for template_acc in mandatory_accounts:
            # Look for company account that references this template account
            company_acc = self.db.query(CompanyAccount).filter(
                and_(
                    CompanyAccount.company_id == company_id,
                    CompanyAccount.template_account_id == template_acc["id"],
                    CompanyAccount.is_active == True
                )
            ).first()

            if not company_acc:
                missing_accounts.append(
                    f"  - {template_acc['code']}: {template_acc['name']}"
                )

        if missing_accounts:
            error_message = (
                f"Company is missing mandatory template accounts.\n"
                f"Template ID: {template_id}\n"
                f"Missing accounts:\n" + "\n".join(missing_accounts) + "\n\n"
                f"These accounts must exist to maintain template compliance."
            )
            return (False, error_message)

        return (True, None)

    def is_mandatory_template_account(
        self,
        account_id: UUID
    ) -> bool:
        """
        Check if a company account is a mandatory template account.

        Args:
            account_id: Company account UUID

        Returns:
            True if account is derived from a mandatory template account
        """
        from app.db.models.company_account import CompanyAccount
        from app.db.models import ChartTemplateAccount

        # Get company account
        account = self.db.query(CompanyAccount).filter(
            CompanyAccount.id == account_id
        ).first()

        if not account or not account.template_account_id:
            return False

        # Check if template account is mandatory
        template_account = self.db.query(ChartTemplateAccount).filter(
            ChartTemplateAccount.id == account.template_account_id
        ).first()

        if not template_account:
            return False

        return template_account.is_mandatory

    def validate_account_deletion(
        self,
        account_id: UUID
    ) -> None:
        """
        Validate that account can be deleted (not mandatory).

        Args:
            account_id: Company account UUID

        Raises:
            ValidationError: If account is mandatory and cannot be deleted
        """
        if self.is_mandatory_template_account(account_id):
            from app.db.models.company_account import CompanyAccount

            account = self.db.query(CompanyAccount).filter(
                CompanyAccount.id == account_id
            ).first()

            raise ValidationError(
                message=(
                    f"Cannot delete mandatory template account.\n"
                    f"Account: {account.code} ({account.description})\n"
                    f"This account is required by the company's chart template.\n"
                    f"To remove this account, you must change the company's template."
                ),
                code=ErrorCode.TEMPLATE_MANDATORY_DELETE,
                details={
                    "account_id": str(account_id),
                    "account_code": account.code,
                    "template_account_id": str(account.template_account_id)
                }
            )

    def validate_account_update(
        self,
        account_id: UUID,
        update_data: Dict
    ) -> None:
        """
        Validate that update to mandatory account doesn't violate template rules.

        MANDATORY ACCOUNT RESTRICTIONS:
        - Cannot change normal_balance
        - Cannot change mapped_master_account_id

        Args:
            account_id: Company account UUID
            update_data: Dictionary of fields being updated

        Raises:
            ValidationError: If update violates template rules
        """
        if not self.is_mandatory_template_account(account_id):
            # Not a mandatory account - no restrictions
            return

        from app.db.models.company_account import CompanyAccount

        account = self.db.query(CompanyAccount).filter(
            CompanyAccount.id == account_id
        ).first()

        # Check restricted fields
        violations = []

        # Check normal_balance
        if 'normal_balance' in update_data:
            new_balance = update_data['normal_balance']
            current_balance = account.normal_balance.value if account.normal_balance else None

            if new_balance != current_balance:
                violations.append(
                    f"  - normal_balance: cannot change from '{current_balance}' to '{new_balance}' (template restriction)"
                )

        # Check mapped_master_account_id
        if 'mapped_master_account_id' in update_data:
            new_mapping = update_data['mapped_master_account_id']
            current_mapping = account.mapped_master_account_id

            if new_mapping != current_mapping:
                violations.append(
                    f"  - mapped_master_account_id: cannot change master chart mapping (template restriction)"
                )

        if violations:
            raise ValidationError(
                message=(
                    f"Cannot modify restricted fields on mandatory template account.\n"
                    f"Account: {account.code} ({account.description})\n"
                    f"This account is required by the company's chart template.\n"
                    f"Attempted changes:\n" + "\n".join(violations) + "\n\n"
                    f"These fields are locked to maintain template consistency."
                ),
                code=ErrorCode.TEMPLATE_VIOLATION,
                details={
                    "account_id": str(account_id),
                    "account_code": account.code,
                    "template_account_id": str(account.template_account_id),
                    "violations": violations
                }
            )

    def validate_company_creation(
        self,
        company_id: UUID,
        template_id: UUID
    ) -> None:
        """
        Validate company has all mandatory template accounts after creation.

        This should be called after initializing a company's chart from a template.

        Args:
            company_id: Company UUID
            template_id: Template UUID

        Raises:
            ValidationError: If company is missing mandatory template accounts
        """
        is_valid, error_message = self.validate_company_has_mandatory_accounts(
            company_id, template_id
        )

        if not is_valid:
            raise ValidationError(
                message=error_message,
                code=ErrorCode.TEMPLATE_MISSING_MANDATORY,
                details={
                    "company_id": str(company_id),
                    "template_id": str(template_id)
                }
            )


# Export
__all__ = ["TemplateAccountValidator"]
