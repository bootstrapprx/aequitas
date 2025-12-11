"""
Startup checks and initialization for Aequitas.
"""
import logging
from sqlalchemy.orm import Session
from app.db.models.master_account import MasterAccount

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


def startup_checks(db: Session) -> dict:
    """
    Run all startup checks and return status.
    """
    results = {
        "master_chart_loaded": False,
        "master_chart_count": 0,
        "errors": []
    }

    try:
        # Check master chart
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

    except Exception as e:
        error_msg = f"Startup check failed: {str(e)}"
        results["errors"].append(error_msg)
        logger.error(f"❌ {error_msg}")

    return results
