"""Add parent_id and mapped_master_account_id to CompanyAccount

Revision ID: 013
Revises: 012
Create Date: 2025-12-13

PHASE 2A - SCHEMA NORMALIZATION (Structured Template Tables)
Migration 1 of 6

PURPOSE:
Enable proper account hierarchy and master chart mapping:
1. Replace string-based parent_code with UUID FK parent_id
2. Replace string-based master_account_code with UUID FK mapped_master_account_id
3. Support deterministic account hierarchy within company charts
4. Enable structural enforcement of account relationships

BACKGROUND:
Current schema uses:
- parent_code (String) - weak reference, no FK enforcement
- master_account_code (String) - weak reference to master_accounts.code

Phase 2A introduces:
- parent_id (UUID FK) - strong reference with cascade control
- mapped_master_account_id (UUID FK) - strong reference to master_accounts.id

MIGRATION STRATEGY:
1. Add new columns as nullable
2. Backfill parent_id from parent_code (string → UUID lookup)
3. Backfill mapped_master_account_id from master_account_code (string → UUID lookup)
4. Validate data integrity
5. Keep old columns temporarily for rollback safety
6. Later migration will drop old columns and make new ones NOT NULL

BREAKING: No - additive columns only
REQUIRES: Phase 1 complete (migrations 003-012)

CANONICAL REFERENCE:
- Phase 2A Specification: Structured Template Tables
- Section: Company Account Hierarchy
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add parent_id and mapped_master_account_id columns to company_accounts.

    COLUMNS ADDED:
    - parent_id: UUID FK to company_accounts(id) for hierarchy
    - mapped_master_account_id: UUID FK to master_accounts(id) for master mapping

    Both columns are nullable initially to allow gradual migration.
    Subsequent migrations will add constraints and validation.
    """

    # ========================================================================
    # STEP 1: Add parent_id column
    # ========================================================================
    # Self-referential foreign key for account hierarchy.
    # NULL indicates root-level account (no parent).
    # ========================================================================

    op.add_column(
        'company_accounts',
        sa.Column('parent_id', UUID(as_uuid=True), nullable=True)
    )

    # Add foreign key constraint to company_accounts(id)
    # ON DELETE CASCADE: If parent is deleted, children are deleted
    # (This aligns with accounting principle: can't orphan sub-accounts)
    op.create_foreign_key(
        'fk_company_accounts_parent_id',
        'company_accounts',
        'company_accounts',
        ['parent_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Add index for hierarchy traversal queries
    op.create_index(
        'ix_company_accounts_parent_id',
        'company_accounts',
        ['parent_id']
    )

    # ========================================================================
    # STEP 2: Add mapped_master_account_id column
    # ========================================================================
    # Replaces master_account_code (String) with proper UUID FK.
    # NULL indicates unmapped account (custom company account).
    # ========================================================================

    op.add_column(
        'company_accounts',
        sa.Column('mapped_master_account_id', UUID(as_uuid=True), nullable=True)
    )

    # Add foreign key constraint to master_accounts(id)
    # ON DELETE SET NULL: If master account is deleted, mapping is cleared
    # (Preserves company account, just loses master mapping)
    op.create_foreign_key(
        'fk_company_accounts_mapped_master_account_id',
        'company_accounts',
        'master_accounts',
        ['mapped_master_account_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Add index for mapping lookups
    op.create_index(
        'ix_company_accounts_mapped_master_account_id',
        'company_accounts',
        ['mapped_master_account_id']
    )

    # ========================================================================
    # STEP 3: Backfill parent_id from parent_code
    # ========================================================================
    # Lookup parent UUID from parent_code string within same company.
    # Only matches if parent exists in same company.
    # ========================================================================

    op.execute("""
        UPDATE company_accounts child
        SET parent_id = parent.id
        FROM company_accounts parent
        WHERE child.parent_code = parent.code
          AND child.company_id = parent.company_id
          AND child.parent_id IS NULL
          AND child.parent_code IS NOT NULL;
    """)

    # ========================================================================
    # STEP 4: Backfill mapped_master_account_id from master_account_code
    # ========================================================================
    # Lookup master account UUID from master_account_code string.
    # ========================================================================

    op.execute("""
        UPDATE company_accounts ca
        SET mapped_master_account_id = ma.id
        FROM master_accounts ma
        WHERE ca.master_account_code = ma.code
          AND ca.mapped_master_account_id IS NULL
          AND ca.master_account_code IS NOT NULL;
    """)

    # ========================================================================
    # STEP 5: Validate backfill results
    # ========================================================================
    # Report any accounts where parent_code or master_account_code exists
    # but couldn't be resolved to UUID.
    # ========================================================================

    op.execute("""
        DO $$
        DECLARE
            v_unresolved_parent INTEGER;
            v_unresolved_master INTEGER;
            v_resolved_parent INTEGER;
            v_resolved_master INTEGER;
        BEGIN
            -- Count unresolved parent references
            SELECT COUNT(*) INTO v_unresolved_parent
            FROM company_accounts
            WHERE parent_code IS NOT NULL
              AND parent_id IS NULL;

            -- Count unresolved master references
            SELECT COUNT(*) INTO v_unresolved_master
            FROM company_accounts
            WHERE master_account_code IS NOT NULL
              AND mapped_master_account_id IS NULL;

            -- Count resolved references
            SELECT COUNT(*) INTO v_resolved_parent
            FROM company_accounts
            WHERE parent_id IS NOT NULL;

            SELECT COUNT(*) INTO v_resolved_master
            FROM company_accounts
            WHERE mapped_master_account_id IS NOT NULL;

            -- Log results
            RAISE NOTICE '=== MIGRATION 013: Backfill Results ===';
            RAISE NOTICE 'Parent hierarchy:';
            RAISE NOTICE '  Resolved parent_code → parent_id: %', v_resolved_parent;
            RAISE NOTICE '  Unresolved parent_code: %', v_unresolved_parent;
            RAISE NOTICE 'Master mapping:';
            RAISE NOTICE '  Resolved master_account_code → mapped_master_account_id: %', v_resolved_master;
            RAISE NOTICE '  Unresolved master_account_code: %', v_unresolved_master;

            -- Warn if unresolved references exist
            IF v_unresolved_parent > 0 THEN
                RAISE WARNING '% company accounts have parent_code but no matching parent in same company', v_unresolved_parent;
                RAISE WARNING 'Query to identify: SELECT id, company_id, code, parent_code FROM company_accounts WHERE parent_code IS NOT NULL AND parent_id IS NULL;';
            END IF;

            IF v_unresolved_master > 0 THEN
                RAISE WARNING '% company accounts have master_account_code but no matching master account', v_unresolved_master;
                RAISE WARNING 'Query to identify: SELECT id, company_id, code, master_account_code FROM company_accounts WHERE master_account_code IS NOT NULL AND mapped_master_account_id IS NULL;';
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """
    Remove parent_id and mapped_master_account_id columns.

    WARNING: This destroys hierarchy and mapping relationships.
    Original parent_code and master_account_code are preserved.
    Only use for rollback during migration issues.
    """

    # Drop indexes first
    op.drop_index('ix_company_accounts_mapped_master_account_id', 'company_accounts')
    op.drop_index('ix_company_accounts_parent_id', 'company_accounts')

    # Drop foreign key constraints
    op.drop_constraint('fk_company_accounts_mapped_master_account_id', 'company_accounts', type_='foreignkey')
    op.drop_constraint('fk_company_accounts_parent_id', 'company_accounts', type_='foreignkey')

    # Drop columns
    op.drop_column('company_accounts', 'mapped_master_account_id')
    op.drop_column('company_accounts', 'parent_id')
