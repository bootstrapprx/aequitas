"""
Startup checks and initialization for Aequitas.

UPDATED: 2025-12-11
- Added master chart integrity validation
- Enhanced error reporting with validation results
"""
import logging
from sqlalchemy.orm import Session
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
            logger.error("   Please run: python -m app.data.seed_enriched_master_chart")
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


def startup_checks(db: Session) -> dict:
    """
    Run all startup checks and return status.

    Checks:
    1. Master chart is loaded
    2. Master chart integrity validation
    """
    results = {
        "master_chart_loaded": False,
        "master_chart_count": 0,
        "master_chart_valid": False,
        "validation_errors": [],
        "validation_warnings": [],
        "orphans": 0,
        "errors": []
    }

    try:
        # Check master chart existence
        count = db.query(MasterAccount).count()
        results["master_chart_count"] = count
        results["master_chart_loaded"] = count > 0

        if count == 0:
            results["errors"].append("Master chart is empty - needs to be seeded")
            logger.warning("⚠ Master chart is empty!")
            logger.warning("   New companies will fail to initialize their chart of accounts")
            logger.warning("   Run: python -m app.data.seed_enriched_master_chart")
        else:
            logger.info(f"✓ Master chart: {count} accounts loaded")

            # Validate master chart integrity
            logger.info("  Validating master chart integrity...")
            validation_results = validate_master_chart_integrity(db)

            results["master_chart_valid"] = validation_results["is_valid"]
            results["validation_errors"] = validation_results["errors"]
            results["validation_warnings"] = validation_results["warnings"]
            results["orphans"] = validation_results["orphan_count"]

            if validation_results["is_valid"]:
                logger.info("  ✓ Master chart integrity: VALID")
            else:
                logger.warning(f"  ⚠ Master chart integrity: INVALID ({len(validation_results['errors'])} errors)")
                for error in validation_results["errors"][:3]:  # Show first 3 errors
                    logger.warning(f"    - {error}")
                if len(validation_results["errors"]) > 3:
                    logger.warning(f"    ... and {len(validation_results['errors']) - 3} more errors")

            if validation_results["warnings"]:
                logger.info(f"  ℹ Master chart warnings: {len(validation_results['warnings'])}")

            if validation_results["orphan_count"] > 0:
                logger.warning(f"  ⚠ Found {validation_results['orphan_count']} orphaned accounts")

    except Exception as e:
        error_msg = f"Startup check failed: {str(e)}"
        results["errors"].append(error_msg)
        logger.error(f"❌ {error_msg}")

    return results
