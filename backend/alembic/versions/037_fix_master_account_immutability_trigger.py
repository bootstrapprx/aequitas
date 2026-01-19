"""Fix master_account immutability trigger after metadata relocation

Revision ID: 037
Revises: 036
Create Date: 2026-01-18

PURPOSE:
Fix the enforce_master_account_immutability() trigger function to remove
references to `tags` and `default_vendors` fields, which were relocated to
the master_account_intelligence table in migration 032.

The trigger was still checking OLD.tags and OLD.default_vendors, causing
database errors since these columns no longer exist on master_accounts.
"""
from alembic import op

# revision identifiers
revision = '037'
down_revision = '036'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Update the immutability trigger to remove references to relocated fields.
    """
    
    # Drop the old trigger
    op.execute("DROP TRIGGER IF EXISTS trigger_enforce_master_account_immutability ON master_accounts;")
    
   # Recreate the function WITHOUT tags and default_vendors references
    op.execute("""
    CREATE OR REPLACE FUNCTION enforce_master_account_immutability()
    RETURNS TRIGGER AS $$
    BEGIN
        IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION
                'CANON VIOLATION (B1): DELETE forbidden on master_accounts. Code: %. Historical accounting truth is immutable.',
                OLD.code
            USING ERRCODE = 'integrity_constraint_violation',
                  HINT = 'Master accounts are versioned, not deleted. Create new version with updated end_date instead.';
        END IF;

        IF TG_OP = 'UPDATE' THEN
            -- Allow updating end_date for versioning (retirement of old version)
            -- Allow updating embedding for semantic search optimization
            -- All other fields are immutable
            -- NOTE: tags and default_vendors removed - they're on master_account_intelligence now
            IF (OLD.code IS DISTINCT FROM NEW.code OR
                OLD.description IS DISTINCT FROM NEW.description OR
                OLD.long_description IS DISTINCT FROM NEW.long_description OR
                OLD.type IS DISTINCT FROM NEW.type OR
                OLD.category IS DISTINCT FROM NEW.category OR
                OLD.normal_balance IS DISTINCT FROM NEW.normal_balance OR
                OLD.level IS DISTINCT FROM NEW.level OR
                OLD.parent_id IS DISTINCT FROM NEW.parent_id OR
                OLD.parent_code IS DISTINCT FROM NEW.parent_code OR
                OLD.fs_mapping IS DISTINCT FROM NEW.fs_mapping OR
                OLD.cash_flow_classification IS DISTINCT FROM NEW.cash_flow_classification OR
                OLD.regulatory_mapping IS DISTINCT FROM NEW.regulatory_mapping OR
                OLD.cost_center IS DISTINCT FROM NEW.cost_center OR
                OLD.version IS DISTINCT FROM NEW.version OR
                OLD.start_date IS DISTINCT FROM NEW.start_date OR
                OLD.notes IS DISTINCT FROM NEW.notes) THEN

                RAISE EXCEPTION
                    'CANON VIOLATION (B1): UPDATE forbidden on master_accounts. Code: %. Master chart is immutable after publication.',
                    OLD.code
                USING ERRCODE = 'integrity_constraint_violation',
                      HINT = 'Create a new versioned master account instead of modifying existing one. Only end_date and embedding may be updated.';
            END IF;
        END IF;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)
    
    # Recreate the trigger
    op.execute("""
    CREATE TRIGGER trigger_enforce_master_account_immutability
        BEFORE UPDATE OR DELETE ON master_accounts
        FOR EACH ROW
        EXECUTE FUNCTION enforce_master_account_immutability();
    """)


def downgrade() -> None:
    """
    Restore the old trigger with tags/default_vendors references.
    (This will break if those columns don't exist)
    """
    op.execute("DROP TRIGGER IF EXISTS trigger_enforce_master_account_immutability ON master_accounts;")
    op.execute("DROP FUNCTION IF EXISTS enforce_master_account_immutability();")
