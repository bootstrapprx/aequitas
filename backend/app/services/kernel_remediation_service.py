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
from app.core.kernel import L0_KERNEL_CODES, map_category_to_account_type, map_normal_balance


SYSTEM_ACCOUNT_CODES = {"32000", "39999"}  # Retained Earnings, Current Period Earnings


class KernelRemediationService:
    """Service for detecting and remediating kernel non-compliance."""

    def __init__(self, db: Session):
        self.db = db

    def is_company_kernel_compliant(self, company_id: UUID) -> bool:
        """
        Check if company has all L0 kernel accounts with correct types.

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
        mismatches = self.get_kernel_mismatches(company_id)
        return len(missing) == 0 and not mismatches

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

    def get_kernel_mismatches(self, company_id: UUID) -> Dict[str, Dict[str, str]]:
        """
        Return L0 kernel accounts with incorrect account_type or normal_balance.

        Returns:
            Dict keyed by account code with mismatch detail.
        """
        master_accounts = self.db.query(MasterAccount).filter(
            MasterAccount.code.in_(L0_KERNEL_CODES)
        ).all()
        master_by_code = {acc.code: acc for acc in master_accounts}

        company_accounts = self.db.query(CompanyAccount).filter(
            CompanyAccount.company_id == company_id,
            CompanyAccount.code.in_(L0_KERNEL_CODES)
        ).all()
        company_by_code = {acc.code: acc for acc in company_accounts}

        mismatches: Dict[str, Dict[str, str]] = {}
        for code in L0_KERNEL_CODES:
            master = master_by_code.get(code)
            company_account = company_by_code.get(code)
            if not master or not company_account:
                continue

            expected_type = map_category_to_account_type(master.category)
            expected_balance = map_normal_balance(master.normal_balance)

            mismatch_fields: Dict[str, str] = {}
            if company_account.account_type != expected_type:
                mismatch_fields["account_type"] = (
                    f"{company_account.account_type.value if company_account.account_type else None}"
                    f" != {expected_type.value}"
                )
            if company_account.normal_balance != expected_balance:
                mismatch_fields["normal_balance"] = (
                    f"{company_account.normal_balance.value if company_account.normal_balance else None}"
                    f" != {expected_balance.value}"
                )

            if mismatch_fields:
                mismatches[code] = mismatch_fields

        return mismatches

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

            account_type = map_category_to_account_type(master.category)
            normal_balance = map_normal_balance(master.normal_balance)

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
