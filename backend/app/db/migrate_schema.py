"""
Database Schema Migration Utility
Ensures the database schema is up-to-date with the latest model definitions.
"""

import logging
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def check_column_exists(db: Session, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    try:
        result = db.execute(text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = :table_name 
            AND column_name = :column_name
        """), {"table_name": table_name, "column_name": column_name})
        return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking column {column_name}: {e}")
        return False


def migrate_master_accounts_schema(db: Session) -> bool:
    """
    Migrate master_accounts table to include enriched fields.
    Returns True if migration was successful or not needed.
    """
    try:
        logger.info("Checking master_accounts schema...")
        
        # Check if enriched fields exist
        enriched_fields = [
            "long_description",
            "fs_mapping",
            "tags",
            "default_vendors",
            "regulatory_mapping",
            "normal_balance",
            "cash_flow_classification",
            "cost_center"
        ]
        
        missing_fields = []
        for field in enriched_fields:
            if not check_column_exists(db, "master_accounts", field):
                missing_fields.append(field)
        
        if not missing_fields:
            logger.info("✓ Master accounts schema is up-to-date")
            return True
        
        logger.info(f"⚠ Missing fields in master_accounts: {', '.join(missing_fields)}")
        logger.info("Running schema migration...")
        
        # Add missing columns
        migration_sql = """
        -- Add enriched fields to master_accounts table
        ALTER TABLE master_accounts 
        ADD COLUMN IF NOT EXISTS long_description TEXT,
        ADD COLUMN IF NOT EXISTS fs_mapping VARCHAR(50),
        ADD COLUMN IF NOT EXISTS tags TEXT[],
        ADD COLUMN IF NOT EXISTS default_vendors TEXT[],
        ADD COLUMN IF NOT EXISTS regulatory_mapping JSONB,
        ADD COLUMN IF NOT EXISTS normal_balance VARCHAR(20),
        ADD COLUMN IF NOT EXISTS cash_flow_classification VARCHAR(50),
        ADD COLUMN IF NOT EXISTS cost_center VARCHAR(50);

        -- Add indexes for better query performance
        CREATE INDEX IF NOT EXISTS idx_master_accounts_category ON master_accounts(category);
        CREATE INDEX IF NOT EXISTS idx_master_accounts_fs_mapping ON master_accounts(fs_mapping);
        CREATE INDEX IF NOT EXISTS idx_master_accounts_normal_balance ON master_accounts(normal_balance);
        CREATE INDEX IF NOT EXISTS idx_master_accounts_tags ON master_accounts USING GIN(tags);
        CREATE INDEX IF NOT EXISTS idx_master_accounts_default_vendors ON master_accounts USING GIN(default_vendors);

        -- Add comments for documentation
        COMMENT ON COLUMN master_accounts.long_description IS 'Professional IFRS/GAAP explanation of the account';
        COMMENT ON COLUMN master_accounts.fs_mapping IS 'Financial statement mapping: Balance Sheet or Income Statement';
        COMMENT ON COLUMN master_accounts.tags IS 'AI-friendly keywords for intelligent classification';
        COMMENT ON COLUMN master_accounts.default_vendors IS 'Common vendor associations for automatic suggestion';
        COMMENT ON COLUMN master_accounts.regulatory_mapping IS 'IFRS/IPSAS/ASC standard references';
        COMMENT ON COLUMN master_accounts.normal_balance IS 'Normal balance type: Debit or Credit';
        COMMENT ON COLUMN master_accounts.cash_flow_classification IS 'Cash flow statement classification';
        COMMENT ON COLUMN master_accounts.cost_center IS 'Default cost center assignment';
        """
        
        # Execute migration
        db.execute(text(migration_sql))
        db.commit()
        
        logger.info("✓ Schema migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Schema migration failed: {e}")
        db.rollback()
        return False



def migrate_companies_schema(db: Session) -> bool:
    """
    Migrate companies table to include subscription_type field.
    Returns True if migration was successful or not needed.
    """
    try:
        logger.info("Checking companies schema...")
        
        has_subscription_type = check_column_exists(db, "companies", "subscription_type")
        
        if has_subscription_type:
            logger.info("✓ Companies schema is up-to-date")
            return True
            
        logger.info("⚠ Missing subscription_type in companies table")
        logger.info("Running companies schema migration...")
        
        migration_sql = """
        -- Create subscription_type enum type if not exists
        DO $$ BEGIN
            CREATE TYPE subscriptiontype AS ENUM ('native', 'stripe');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;

        -- Add subscription_type column
        ALTER TABLE companies 
        ADD COLUMN IF NOT EXISTS subscription_type subscriptiontype NOT NULL DEFAULT 'stripe';
        """
        
        # Execute migration
        db.execute(text(migration_sql))
        db.commit()
        
        logger.info("✓ Companies schema migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Companies schema migration failed: {e}")
        db.rollback()
        return False


def migrate_users_schema(db: Session) -> bool:
    """
    Migrate users table to include user_uid and preferred_company_id fields.
    Returns True if migration was successful or not needed.
    """
    try:
        logger.info("Checking users schema...")
        
        has_user_uid = check_column_exists(db, "users", "user_uid")
        has_preferred_company_id = check_column_exists(db, "users", "preferred_company_id")
        
        if has_user_uid and has_preferred_company_id:
            logger.info("✓ Users schema is up-to-date")
            return True
            
        logger.info("⚠ Missing columns in users table")
        logger.info("Running users schema migration...")
        
        migration_sql = ""
        
        if not has_user_uid:
            logger.info("Adding user_uid column...")
            migration_sql += """
            -- Add user_uid column
            ALTER TABLE users ADD COLUMN IF NOT EXISTS user_uid VARCHAR;
            
            -- Populate existing rows with UUIDs
            UPDATE users SET user_uid = gen_random_uuid()::text WHERE user_uid IS NULL;
            
            -- Make it not null
            ALTER TABLE users ALTER COLUMN user_uid SET NOT NULL;
            
            -- Add unique index
            CREATE UNIQUE INDEX IF NOT EXISTS ix_users_user_uid ON users(user_uid);
            """
            
        if not has_preferred_company_id:
            logger.info("Adding preferred_company_id column...")
            migration_sql += """
            -- Add preferred_company_id column
            ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_company_id UUID;
            """
        
        # Execute migration
        if migration_sql:
            db.execute(text(migration_sql))
            db.commit()
        
        logger.info("✓ Users schema migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Users schema migration failed: {e}")
        db.rollback()
        return False


def ensure_schema_updated(db: Session) -> bool:
    """
    Ensure all database schemas are up-to-date.
    This should be called on application startup.
    """
    try:
        logger.info("="*60)
        logger.info("DATABASE SCHEMA CHECK")
        logger.info("="*60)
        
        # Migrate master_accounts table
        success_master = migrate_master_accounts_schema(db)
        
        # Migrate users table
        success_users = migrate_users_schema(db)

        # Migrate companies table
        success_companies = migrate_companies_schema(db)
        
        if success_master and success_users and success_companies:
            logger.info("="*60)
            logger.info("✓ ALL SCHEMAS UP-TO-DATE")
            logger.info("="*60)
            return True
        else:
            logger.warning("="*60)
            logger.warning("⚠ SCHEMA MIGRATION HAD ISSUES")
            logger.warning("="*60)
            return False
        
    except Exception as e:
        logger.error(f"Schema check failed: {e}")
        return False


if __name__ == "__main__":
    # For manual execution
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        ensure_schema_updated(db)
    finally:
        db.close()
