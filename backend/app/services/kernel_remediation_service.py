"""
Kernel 2025.2 Company Remediation Service

Detects and remediates companies missing L0 kernel accounts.

Authority: Canon III - History is immutable, changes are additive and forward-only.
"""

from datetime import datetime
from typing import Dict, List, Set
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.db.models.company import Company
from app.db.models.company_account import CompanyAccount
from app.db.models.master_account import MasterAccount
from app.db.models.journal_entry import JournalEntry
from app.db.models.enums import AccountType, NormalBalance


# L0 Universal Kernel - MANDATORY for all companies
L0_KERNEL_CODES = {
    '10000', '10100', '12000', '14000', '15000', '15900',
    '20000', '21000', '22000', '23000',
    '30000', '32000', '39999',
    '40000', '49000', '50000',
    '60000', '61000', '62000', '69000'
}

SYSTEM_ACCOUNT_CODES = {'32000', '39999'}  # Retained Earnings, Current Period Earnings


class KernelRemediationService:
    """Service for detecting and remediating kernel non-compliance."""

    def __init__(self, db: Session):
        self.db = db

    def is_company_kernel_compliant(self, company_id: UUID) -> bool:
        """
        Check if company has all L0 kernel accounts.

        Args:
            company_id: UUID of company to check

        Returns:
            True if company has all 20 L0 accounts, False otherwise
        """
        company_codes = {
            acc.code for acc in
            self.db.query(CompanyAccount.code)
            .filter(CompanyAccount.company_id == company_id)
            .all()
        }

        missing = L0_KERNEL_CODES - company_codes
        return len(missing) == 0

    def get_missing_kernel_accounts(self, company_id: UUID) -> List[str]:
        """
        Return list of missing L0 kernel account codes.

        Args:
            company_id: UUID of company to check

        Returns:
            Sorted list of missing L0 account codes
        """
        company_codes = {
            acc.code for acc in
            self.db.query(CompanyAccount.code)
            .filter(CompanyAccount.company_id == company_id)
            .all()
        }

        missing = L0_KERNEL_CODES - company_codes
        return sorted(list(missing))

    def has_posted_transactions(self, company_id: UUID) -> bool:
        """
        Check if company has any posted journal entries.

        Args:
            company_id: UUID of company to check

        Returns:
            True if company has posted entries, False otherwise
        """
        count = self.db.query(JournalEntry).filter(
            JournalEntry.company_id == company_id,
            JournalEntry.is_posted == True
        ).count()

        return count > 0

    def auto_remediate_company(
        self,
        company_id: UUID,
        dry_run: bool = False
    ) -> Dict:
        """
        Automatically add missing L0 kernel accounts to a company's chart.

        This is SAFE because:
        - Only ADDS accounts (never deletes)
        - Does not modify existing accounts
        - Does not create journal entries

        Args:
            company_id: UUID of company to remediate
            dry_run: If True, only return what would be added (don't modify)

        Returns:
            dict with 'added_count', 'added_codes', 'dry_run' status
        """
        # Get missing accounts
        missing_codes = self.get_missing_kernel_accounts(company_id)

        if not missing_codes:
            return {
                'added_count': 0,
                'added_codes': [],
                'dry_run': dry_run,
                'message': 'Company is already kernel-compliant'
            }

        if dry_run:
            return {
                'added_count': len(missing_codes),
                'added_codes': missing_codes,
                'dry_run': True,
                'message': f'Would add {len(missing_codes)} accounts (dry run)'
            }

        # Get master accounts for missing codes
        master_accounts = self.db.query(MasterAccount).filter(
            MasterAccount.code.in_(missing_codes)
        ).all()

        master_by_code = {ma.code: ma for ma in master_accounts}

        # Verify all required master accounts exist
        missing_from_master = set(missing_codes) - set(master_by_code.keys())
        if missing_from_master:
            raise ValueError(
                f"Master chart is incomplete. Missing codes: {sorted(missing_from_master)}. "
                f"Run master chart reseed first."
            )

        # Create company accounts
        added_codes = []
        for code in sorted(missing_codes):
            master = master_by_code[code]

            # Map master chart categories to CompanyAccount AccountType enum
            # Master chart may have "Cost of Goods Sold" and "Other" which aren't in the enum
            category_mapping = {
                "Asset": AccountType.ASSET,
                "Liability": AccountType.LIABILITY,
                "Equity": AccountType.EQUITY,
                "Revenue": AccountType.REVENUE,
                "Expense": AccountType.EXPENSE,
                "Cost of Goods Sold": AccountType.EXPENSE,  # COGS is a type of expense
                "Other": AccountType.EXPENSE,  # Default to expense
            }

            account_type = category_mapping.get(master.category, AccountType.EXPENSE)

            # Map normal balance strings to enum
            normal_balance_mapping = {
                "Debit": NormalBalance.DEBIT,
                "Credit": NormalBalance.CREDIT,
            }
            normal_balance = normal_balance_mapping.get(master.normal_balance, NormalBalance.DEBIT)

            company_account = CompanyAccount(
                id=uuid4(),
                company_id=company_id,
                code=code,
                name=master.description,
                description=master.description,
                type=master.type,  # 'H' or 'D'
                account_type=account_type,
                normal_balance=normal_balance,
                mapped_master_account_id=master.id,
                is_active=True,
                created_at=datetime.utcnow(),
            )

            self.db.add(company_account)
            added_codes.append(code)

        self.db.commit()

        return {
            'added_count': len(added_codes),
            'added_codes': added_codes,
            'dry_run': False,
            'message': f'Successfully added {len(added_codes)} kernel accounts'
        }

    def remediate_all_companies(
        self,
        dry_run: bool = True,
        only_without_transactions: bool = True
    ) -> Dict:
        """
        Background job to remediate all non-compliant companies.

        Args:
            dry_run: If True, only report what would be done
            only_without_transactions: If True, skip companies with posted entries

        Returns:
            dict with summary statistics
        """
        companies = self.db.query(Company).filter(Company.is_active == True).all()

        results = {
            'total': len(companies),
            'compliant': 0,
            'remediated': 0,
            'skipped': 0,
            'failed': 0,
            'dry_run': dry_run,
            'details': []
        }

        for company in companies:
            try:
                if self.is_company_kernel_compliant(company.id):
                    results['compliant'] += 1
                    continue

                # Check if company has posted transactions
                has_transactions = self.has_posted_transactions(company.id)

                if only_without_transactions and has_transactions:
                    results['skipped'] += 1
                    results['details'].append({
                        'company_id': str(company.id),
                        'status': 'skipped',
                        'reason': 'has_posted_transactions'
                    })
                    continue

                # Execute remediation
                result = self.auto_remediate_company(company.id, dry_run=dry_run)

                if not dry_run:
                    results['remediated'] += 1

                results['details'].append({
                    'company_id': str(company.id),
                    'status': 'remediated' if not dry_run else 'would_remediate',
                    'added_count': result['added_count'],
                    'added_codes': result['added_codes']
                })

            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'company_id': str(company.id),
                    'status': 'failed',
                    'error': str(e)
                })

        return results


# ============================================================================
# REMEDIATION EVENT LOGGING (for audit trail)
# ============================================================================

# Note: This would typically be a separate model, but for now we'll use
# a simple dict structure. In production, create a RemediationEvent model.

def log_remediation_event(
    db: Session,
    company_id: UUID,
    user_id: UUID | None,
    added_codes: List[str],
    triggered_by: str
) -> None:
    """
    Log a remediation event for audit trail.

    Args:
        db: Database session
        company_id: UUID of company remediated
        user_id: UUID of user who triggered (None if automated)
        added_codes: List of account codes added
        triggered_by: 'user_action', 'background_job', 'system_check'
    """
    # In production, this would create a RemediationEvent record
    # For now, we'll just log to console/file
    print(f"[REMEDIATION EVENT]")
    print(f"  Company: {company_id}")
    print(f"  User: {user_id or 'automated'}")
    print(f"  Added: {added_codes}")
    print(f"  Triggered: {triggered_by}")
    print(f"  Timestamp: {datetime.utcnow().isoformat()}")
