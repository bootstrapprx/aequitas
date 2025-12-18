"""
Production-grade bootstrap script for the Aequitas backend.

This script ensures that the application starts in a guaranteed valid state by:
1. Waiting for the database to be reachable.
2. Applying all Alembic migrations.
3. Seeding essential, idempotent data (Master Chart, default fiscal rules).

This script is designed to be run inside the Docker container on every startup.
If any step fails, it will exit with a non-zero status code, preventing
the application server from starting.
"""
import logging
import time
from sqlalchemy.orm import Session
from alembic.config import Config
from alembic import command
from sqlalchemy import exc, text

# It's crucial to set up logging early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Attempt to import all necessary components.
# These imports are structured to reflect the Aequitas project layout.
try:
    from app.db.session import SessionLocal, engine
    from app.db.models.master_account import MasterAccount
    from app.db.models.tax_ruleset import TaxRuleset
    from app.core.config import settings
except ImportError as e:
    logger.error(f"Failed to import necessary modules: {e}", exc_info=True)
    logger.error("Please ensure that the script is run with the correct Python path and all dependencies are installed.")
    exit(1)

MAX_RETRIES = 10
RETRY_DELAY = 5

def wait_for_db():
    """
    Waits for the database to become available.
    Retries connecting several times before giving up.
    """
    logger.info("Attempting to connect to the database...")
    for i in range(MAX_RETRIES):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("Database connection successful.")
            return True
        except (exc.OperationalError, exc.DBAPIError) as e:
            logger.warning(f"Database connection attempt {i+1}/{MAX_RETRIES} failed: {e}")
            if i < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                logger.error("Could not connect to the database after several retries.", exc_info=True)
                return False

def run_alembic_migrations():
    """
    Runs Alembic migrations programmatically to upgrade the schema to the 'head'.
    """
    logger.info("Running Alembic migrations...")
    try:
        # The path to alembic.ini is relative to the backend directory where this script runs.
        alembic_cfg = Config("alembic.ini")
        # To avoid issues with relative paths in alembic.ini, especially for script_location
        alembic_cfg.set_main_option("script_location", "alembic")
        command.upgrade(alembic_cfg, "head")
        logger.info("Alembic migrations completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Alembic migrations failed: {e}", exc_info=True)
        return False

def seed_master_chart(db: Session):
    """
    Idempotently seeds the Master Chart of Accounts.
    
    This function checks if any master accounts exist. If they do, it skips
    seeding. This is a placeholder for a more sophisticated seeding mechanism
    that would handle versions and individual account updates.
    
    For now, it guarantees that the seeding process doesn't corrupt existing data.
    """
    logger.info("Checking Master Chart of Accounts seed status...")
    try:
        # Check if any master accounts already exist
        if db.query(MasterAccount).first():
            logger.info("Master Chart of Accounts is already seeded. Skipping.")
        else:
            # In a real scenario, you would load data from a file (e.g., CSV, JSON)
            # and create MasterAccount objects here.
            logger.info("Master Chart of Accounts is empty. Seeding is required.")
            logger.warning("Placeholder: No actual data seeded for Master Chart as per current implementation.")
            # Example of how seeding would look:
            # master_accounts_data = [...] # Load from a file
            # for account_data in master_accounts_data:
            #     db_account = MasterAccount(**account_data)
            #     db.add(db_account)
            # db.commit()
            # logger.info("Successfully seeded Master Chart of Accounts.")
        return True
    except Exception as e:
        logger.error(f"Failed to seed Master Chart of Accounts: {e}", exc_info=True)
        return False

def seed_default_fiscal_ruleset(db: Session):
    """
    Idempotently seeds the default fiscal ruleset for '2025.1'.

    This function checks for a specific TaxRuleset and creates it only if it
    does not exist, ensuring the system always has the baseline rules.
    """
    logger.info("Checking default fiscal ruleset seed status...")
    ruleset_version = "2025.1"
    ruleset_scope = "PASS_THROUGH_BASE"
    
    try:
        # Check if the specific ruleset already exists
        exists = db.query(TaxRuleset).filter_by(
            version=ruleset_version,
            scope=ruleset_scope
        ).first()

        if exists:
            logger.info(f"Default fiscal ruleset {ruleset_version} ('{ruleset_scope}') already exists. Skipping.")
        else:
            logger.info(f"Creating default fiscal ruleset {ruleset_version} ('{ruleset_scope}')...")
            default_ruleset = TaxRuleset(
                version=ruleset_version,
                scope=ruleset_scope,
                jurisdiction=None, # Federal/Base scope
                status="ACTIVE",
                rules=[] # Pass-through has no rules by default
            )
            db.add(default_ruleset)
            db.commit()
            logger.info(f"Successfully created default fiscal ruleset {ruleset_version} ('{ruleset_scope}').")
        return True
    except Exception as e:
        logger.error(f"Failed to seed default fiscal ruleset: {e}", exc_info=True)
        db.rollback()
        return False

def main():
    """
    Main bootstrap execution pipeline.
    """
    logger.info("Starting Aequitas bootstrap sequence...")

    if not wait_for_db():
        exit(1)

    if not run_alembic_migrations():
        exit(1)

    # Create a new session for seeding operations
    db_session = SessionLocal()
    try:
        if not seed_master_chart(db_session):
            exit(1)
        
        if not seed_default_fiscal_ruleset(db_session):
            exit(1)
    finally:
        db_session.close()

    logger.info("Aequitas bootstrap sequence completed successfully.")

if __name__ == "__main__":
    main()
