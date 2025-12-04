from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.user_service import UserService
from app.db.models.user import User
from app.db.models.master_account import MasterAccount
from app.core.security import get_password_hash
import logging

logger = logging.getLogger(__name__)

def init_db(db: Session) -> None:
    """
    Initialize the database with:
    1. Schema Migration (ensure all columns exist)
    2. Superuser (if doesn't exist)
    3. Master Chart of Accounts (if doesn't exist)
    
    This ensures the application always has the foundational data needed.
    """
    # Step 1: Ensure schema is up-to-date
    try:
        from app.db.migrate_schema import ensure_schema_updated
        ensure_schema_updated(db)
    except Exception as e:
        logger.error(f"Schema migration failed: {e}")
        logger.warning("Continuing with initialization...")

    # Step 2: Initialize superuser
    _seed_superuser(db)
    
    # Step 3: Initialize Master Chart of Accounts
    _seed_master_chart(db)


def _seed_superuser(db: Session) -> None:
    """
    Seed the default superuser if configured and not already exists.
    Uses SUPERUSER_EMAIL and SUPERUSER_PASSWORD properties which handle
    both new (DEFAULT_SUPERUSER_*) and legacy (FIRST_SUPERUSER*) env vars.
    """
    user_service = UserService(db)
    superuser_email = settings.SUPERUSER_EMAIL
    superuser_password = settings.SUPERUSER_PASSWORD
    
    if not superuser_password:
        logger.warning("⚠ No superuser password configured - skipping superuser seed")
        logger.info("  Set DEFAULT_SUPERUSER_PASSWORD in .env to create a superuser")
        return
    
    user = user_service.get_user_by_email(superuser_email)
    if not user:
        user = User(
            email=superuser_email,
            hashed_password=get_password_hash(superuser_password),
            is_superuser=True,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"✓ Superuser created: {superuser_email}")
        print(f"✓ Superuser {superuser_email} created")
    else:
        logger.info(f"✓ Superuser already exists: {superuser_email}")
        print(f"✓ Superuser {superuser_email} already exists")


def _seed_master_chart(db: Session) -> None:
    """Seed the Master Chart of Accounts if not already loaded."""
    master_chart_count = db.query(MasterAccount).count()
    if master_chart_count == 0:
        print("\n" + "="*60)
        print("INITIALIZING MASTER CHART OF ACCOUNTS")
        print("="*60)
        try:
            from app.data.seed_enriched_master_chart import load_enriched_master_chart
            success = load_enriched_master_chart(db, force_reload=False)
            if success:
                print("✓ Master Chart of Accounts initialized successfully")
            else:
                print("⚠ Master Chart initialization skipped (already exists)")
        except Exception as e:
            print(f"✗ Error initializing Master Chart: {e}")
            print("  You can manually load it by running:")
            print("  python -m app.data.seed_enriched_master_chart")
        print("="*60 + "\n")
    else:
        print(f"✓ Master Chart already loaded ({master_chart_count} accounts)")

