from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.user_service import UserService
from app.db.models.user import User
from app.db.models.master_account import MasterAccount
from app.core.security import get_password_hash

def init_db(db: Session) -> None:
    """
    Initialize the database with:
    1. Superuser (if doesn't exist)
    2. Master Chart of Accounts (if doesn't exist)
    
    This ensures the application always has the foundational data needed.
    """
    # Initialize superuser
    user_service = UserService(db)
    
    user = user_service.get_user_by_email(settings.FIRST_SUPERUSER)
    if not user:
        user = User(
            email=settings.FIRST_SUPERUSER,
            hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            is_superuser=True,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✓ Superuser {settings.FIRST_SUPERUSER} created")
    else:
        print(f"✓ Superuser {settings.FIRST_SUPERUSER} already exists")
    
    # Initialize Master Chart of Accounts
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
