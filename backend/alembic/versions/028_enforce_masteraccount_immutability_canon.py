"""Enforce MasterAccount Immutability Canon (Invariants B1, B2)

Revision ID: 028
Revises: 027
Create Date: 2025-12-23

CANON ENFORCEMENT: MasterAccount (Accounting Truth)
Canonical References: Canon I (Accounting Truth & Structure)

PURPOSE:
MasterAccount is the immutable, versioned foundation of the accounting system.
It represents global accounting concepts, not company-specific facts.

INVARIANTS ENFORCED:

B1 - Immutability
  Rule: No UPDATE or DELETE after publication (start_date is set)
  Enforcement: Trigger blocking all mutations except INSERT
  Rationale: Historical accounting classifications must never change

B2 - Concept-Only (Partial Schema Enforcement)
  Rule: No fact-bearing fields (vendors, banks, properties)
  Note: Advisory metadata (default_vendors, tags) to be relocated in migration 032
  This migration documents the violation and prepares for remediation

BREAKING: Yes - will prevent UPDATE/DELETE of master_accounts
REQUIRES: master_accounts table with start_date column
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '028'
down_revision = '027'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Enforce MasterAccount immutability.
    """

    # =========================================================================
    # INVARIANT B1: Immutability (No UPDATE or DELETE)
    # =========================================================================

    # Create trigger function to block UPDATE and DELETE
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
                OLD.tags IS DISTINCT FROM NEW.tags OR
                OLD.default_vendors IS DISTINCT FROM NEW.default_vendors OR
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

    # Attach trigger to master_accounts table
    op.execute("""
    CREATE TRIGGER trigger_enforce_master_account_immutability
        BEFORE UPDATE OR DELETE ON master_accounts
        FOR EACH ROW
        EXECUTE FUNCTION enforce_master_account_immutability();
    """)

    # =========================================================================
    # INVARIANT B2: Concept-Only (Documentation)
    # =========================================================================

    # Add database comment documenting that advisory metadata violates Canon IV
    # and will be relocated in a future migration
    op.execute("""
    COMMENT ON COLUMN master_accounts.default_vendors IS
    'CANON VIOLATION (B2): Advisory metadata. Belongs in intelligence layer (Zone C), not truth core. To be relocated in migration 032.';
    """)

    op.execute("""
    COMMENT ON COLUMN master_accounts.tags IS
    'CANON VIOLATION (B2): Advisory metadata. Belongs in intelligence layer (Zone C), not truth core. To be relocated in migration 032.';
    """)

    # Add table-level comment
    op.execute("""
    COMMENT ON TABLE master_accounts IS
    'Canon I: Accounting Truth. Immutable, versioned foundation. No updates/deletes after publication. Advisory metadata to be extracted.';
    """)


def downgrade() -> None:
    """
    Remove MasterAccount immutability enforcement.

    WARNING: Downgrading removes canon enforcement. Only permitted in development.
    """

    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS trigger_enforce_master_account_immutability ON master_accounts;")

    # Drop function
    op.execute("DROP FUNCTION IF EXISTS enforce_master_account_immutability();")

    # Remove comments
    op.execute("COMMENT ON TABLE master_accounts IS NULL;")
    op.execute("COMMENT ON COLUMN master_accounts.default_vendors IS NULL;")
    op.execute("COMMENT ON COLUMN master_accounts.tags IS NULL;")
