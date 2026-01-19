"""
Startup checks and initialization for Aequitas.

UPDATED: 2025-12-11
- Added master chart integrity validation
- Enhanced error reporting with validation results
"""
import logging
from sqlalchemy.orm import Session
from app.core.kernel import L0_KERNEL_CODES
from app.db.models.company import Company
from app.db.models.company_account import CompanyAccount
from app.db.models.master_account import MasterAccount
from app.core.validators.master_chart_validator import MasterChartValidator

logger = logging.getLogger(__name__)


def verify_master_chart(db: Session) -> bool:
    """
    Verify that the master chart is loaded.
    Returns True if loaded, False otherwise.
    """
    try:
        count = db.query(MasterAccount).count()
        if count == 0:
            logger.error("❌ Master chart is NOT loaded!")
            logger.error("   Please run: python -m app.data.reseed_kernel_master_chart")
            return False
        else:
            logger.info(f"✓ Master chart loaded with {count} accounts")
            return True
    except Exception as e:
        logger.error(f"Error checking master chart: {e}")
        return False


def validate_master_chart_integrity(db: Session) -> dict:
    """
    Validate the integrity of the master chart on startup.

    Returns validation results including errors and warnings.
    """
    validator = MasterChartValidator()
    results = {
        "is_valid": False,
        "errors": [],
        "warnings": [],
        "orphan_count": 0
    }

    try:
        # Get all accounts as dictionaries for validation
        accounts = db.query(MasterAccount).all()
        if not accounts:
            return results

        accounts_data = []
        for acc in accounts:
            accounts_data.append({
                "code": acc.code,
                "account_name": acc.description if acc.description else acc.code,
                "type": acc.type,
                "category": acc.category,
                "normal_balance": acc.normal_balance,
                "fs_mapping": acc.fs_mapping,
                "parent_code": acc.parent_code
            })

        # Validate chart structure
        validation_result = validator.validate_chart(accounts_data)

        results["is_valid"] = validation_result.is_valid
        results["errors"] = validation_result.errors
        results["warnings"] = validation_result.warnings

        # Count orphans from stats
        from app.services.master_chart_service import MasterChartService
        service = MasterChartService(db)
        stats = service.get_coa_stats()
        results["orphan_count"] = stats.get("orphans", 0)

    except Exception as e:
        results["errors"].append(f"Validation check failed: {str(e)}")

    return results


def check_company_kernel_accounts(db: Session) -> dict:
    """
    Check that all active companies have required L0 kernel accounts.

    Returns:
        dict with compliance summary and missing codes per company.
    """
    results = {
        "companies_checked": 0,
        "companies_compliant": 0,
        "companies_missing_kernel": 0,
        "missing_by_company": [],
    }

    companies = db.query(Company).filter(Company.is_active == True).all()
    results["companies_checked"] = len(companies)

    for company in companies:
        company_codes = {
            row[0] for row in db.query(CompanyAccount.code).filter(
                CompanyAccount.company_id == company.id,
                CompanyAccount.is_active == True
            ).all()
        }

        missing = sorted(L0_KERNEL_CODES - company_codes)
        if missing:
            results["companies_missing_kernel"] += 1
            results["missing_by_company"].append({
                "company_id": str(company.id),
                "ucid": company.ucid,
                "name": company.name,
                "missing_codes": missing,
            })
        else:
            results["companies_compliant"] += 1

    return results


def startup_checks(db: Session) -> dict:
    """
    Run all startup checks and return status.

    Checks:
    1. Active companies have required L0 kernel accounts
    """
    results = {
        "kernel_required_codes": sorted(L0_KERNEL_CODES),
        "companies_checked": 0,
        "companies_compliant": 0,
        "companies_missing_kernel": 0,
        "missing_by_company": [],
        "errors": []
    }

    try:
        kernel_results = check_company_kernel_accounts(db)
        results.update(kernel_results)

        if kernel_results["companies_missing_kernel"] == 0:
            logger.info("✓ Kernel compliance: All active companies have L0 accounts")
        else:
            results["errors"].append(
                f"{kernel_results['companies_missing_kernel']} company(ies) missing L0 kernel accounts"
            )
            logger.warning(
                "⚠ Kernel compliance: "
                f"{kernel_results['companies_missing_kernel']} company(ies) missing L0 accounts"
            )
            for company in kernel_results["missing_by_company"][:3]:
                logger.warning(
                    "  - Missing kernel accounts for %s (%s): %s",
                    company.get("name"),
                    company.get("ucid"),
                    ", ".join(company.get("missing_codes", [])),
                )
            if kernel_results["companies_missing_kernel"] > 3:
                logger.warning(
                    "  ... and %s more companies with missing kernel accounts",
                    kernel_results["companies_missing_kernel"] - 3
                )

    except Exception as e:
        error_msg = f"Startup check failed: {str(e)}"
        results["errors"].append(error_msg)
        logger.error(f"❌ {error_msg}")

    return results
