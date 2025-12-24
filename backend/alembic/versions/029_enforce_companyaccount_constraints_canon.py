"""Enforce CompanyAccount Constraints Canon (Invariants C1, C2, C3)

Revision ID: 029
Revises: 028
Create Date: 2025-12-23

CANON ENFORCEMENT: CompanyAccount (Leaf / Posting Endpoint)
Canonical References: Canon I (Structure), Canon III (Lifecycle)

PURPOSE:
CompanyAccount is where structure ends and truth begins.
Each account is a posting endpoint with strict referential integrity.

INVARIANTS ENFORCED:

C1 - Single Master Mapping
  Rule: Each CompanyAccount maps to exactly one MasterAccount
  Enforcement: NOT NULL constraint on mapped_master_account_id
  Note: Already partially enforced; this migration hardens it

C2 - No Deletion After Use
  Rule: If referenced by any JournalEntryLine, deletion is forbidden
  Enforcement: Foreign key RESTRICT (prevents CASCADE deletion)
  Impact: Replaces soft-delete pattern with hard referential integrity

C3 - Rename Without Reinterpretation
  Rule: Renaming does not affect historical postings
  Enforcement: Service-layer (not database) - documented here
  Note: Renaming only changes display fields, not FK references

BREAKING: Yes - hardens foreign key constraints
REQUIRES: journal_entry_lines table with company_account_id FK
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '029'
down_revision = '028'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Enforce CompanyAccount referential integrity constraints.
    """

    # =========================================================================
    # INVARIANT C1: Single Master Mapping (Hardening)
    # =========================================================================

    # Add NOT NULL constraint on mapped_master_account_id if not already present
    # Note: This may fail if existing data has NULL values - data migration needed first
    op.execute("""
    DO $$
    BEGIN
        -- Check if constraint already exists
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'company_accounts'
              AND column_name = 'mapped_master_account_id'
              AND is_nullable = 'NO'
        ) THEN
            -- Add NOT NULL constraint
            -- First check for NULL values
            IF EXISTS (SELECT 1 FROM company_accounts WHERE mapped_master_account_id IS NULL) THEN
                RAISE EXCEPTION
                    'CANON ENFORCEMENT BLOCKED: Cannot enforce C1 (Single Master Mapping). Found company_accounts with NULL mapped_master_account_id. Data repair required.'
                USING HINT = 'Run data migration to map all company accounts to master accounts before applying this constraint.';
            END IF;

            -- Safe to add NOT NULL
            ALTER TABLE company_accounts
                ALTER COLUMN mapped_master_account_id SET NOT NULL;

            RAISE NOTICE 'CANON C1 ENFORCED: mapped_master_account_id is now NOT NULL';
        ELSE
            RAISE NOTICE 'CANON C1 ALREADY ENFORCED: mapped_master_account_id is already NOT NULL';
        END IF;
    END $$;
    """)

    # =========================================================================
    # INVARIANT C2: No Deletion After Use (RESTRICT on FK)
    # =========================================================================

    # Drop existing FK constraint on journal_entry_lines.company_account_id if CASCADE
    # Replace with RESTRICT to prevent deletion of referenced accounts
    op.execute("""
    DO $$
    BEGIN
        -- Drop existing FK constraint (if it exists)
        IF EXISTS (
            SELECT 1
            FROM information_schema.table_constraints
            WHERE constraint_name = 'journal_entry_lines_company_account_id_fkey'
              AND table_name = 'journal_entry_lines'
        ) THEN
            ALTER TABLE journal_entry_lines
                DROP CONSTRAINT journal_entry_lines_company_account_id_fkey;

            RAISE NOTICE 'Dropped existing FK constraint journal_entry_lines_company_account_id_fkey';
        END IF;

        -- Add new FK constraint with RESTRICT (cannot delete referenced account)
        ALTER TABLE journal_entry_lines
            ADD CONSTRAINT journal_entry_lines_company_account_id_fkey
            FOREIGN KEY (company_account_id)
            REFERENCES company_accounts(id)
            ON DELETE RESTRICT
            ON UPDATE CASCADE;

        RAISE NOTICE 'CANON C2 ENFORCED: company_account_id FK now uses ON DELETE RESTRICT';
    END $$;
    """)

    # =========================================================================
    # INVARIANT C2: Prevent Deletion of Used Accounts (Additional Guard)
    # =========================================================================

    # Create trigger function to provide better error messages
    op.execute("""
    CREATE OR REPLACE FUNCTION prevent_deletion_of_used_accounts()
    RETURNS TRIGGER AS $$
    DECLARE
        entry_count INTEGER;
    BEGIN
        -- Check if account has journal entry lines
        SELECT COUNT(*) INTO entry_count
        FROM journal_entry_lines
        WHERE company_account_id = OLD.id;

        IF entry_count > 0 THEN
            RAISE EXCEPTION
                'CANON VIOLATION (C2): Cannot delete company_account (id: %, code: %). Account has % posted journal entry lines.',
                OLD.id, OLD.code, entry_count
            USING ERRCODE = 'foreign_key_violation',
                  HINT = 'Accounts with transaction history cannot be deleted. Use soft-delete (is_active = false) instead.';
        END IF;

        RETURN OLD;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Attach trigger to company_accounts table
    op.execute("""
    CREATE TRIGGER trigger_prevent_deletion_of_used_accounts
        BEFORE DELETE ON company_accounts
        FOR EACH ROW
        EXECUTE FUNCTION prevent_deletion_of_used_accounts();
    """)

    # =========================================================================
    # INVARIANT C3: Rename Without Reinterpretation (Documentation)
    # =========================================================================

    # Add table-level comment documenting the constraint
    op.execute("""
    COMMENT ON TABLE company_accounts IS
    'Canon I & III: Posting endpoint. Single master mapping (C1). No deletion after use (C2). Renaming is cosmetic only (C3).';
    """)

    op.execute("""
    COMMENT ON COLUMN company_accounts.name IS
    'Display name (cosmetic). Can be changed without affecting historical postings. Renaming does not reinterpret history.';
    """)


def downgrade() -> None:
    """
    Remove CompanyAccount constraint enforcement.

    WARNING: Downgrading removes canon enforcement. Only permitted in development.
    """

    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trigger_prevent_deletion_of_used_accounts ON company_accounts;")
    op.execute("DROP FUNCTION IF EXISTS prevent_deletion_of_used_accounts();")

    # Restore FK to CASCADE (if that was original behavior)
    # Note: This is destructive and should only be done in development
    op.execute("""
    ALTER TABLE journal_entry_lines
        DROP CONSTRAINT IF EXISTS journal_entry_lines_company_account_id_fkey;
    """)

    op.execute("""
    ALTER TABLE journal_entry_lines
        ADD CONSTRAINT journal_entry_lines_company_account_id_fkey
        FOREIGN KEY (company_account_id)
        REFERENCES company_accounts(id)
        ON DELETE CASCADE;
    """)

    # Remove NOT NULL constraint on mapped_master_account_id
    op.execute("""
    ALTER TABLE company_accounts
        ALTER COLUMN mapped_master_account_id DROP NOT NULL;
    """)

    # Remove comments
    op.execute("COMMENT ON TABLE company_accounts IS NULL;")
    op.execute("COMMENT ON COLUMN company_accounts.name IS NULL;")
