"""Add version field to MasterAccount

Revision ID: 011
Revises: 010
Create Date: 2025-12-13

PHASE 1 - CRITICAL DATA INTEGRITY
Migration 9 of 10

PURPOSE:
Add version tracking to master chart of accounts to support:
1. Master chart evolution over time (e.g., GAAP standard updates)
2. Multiple master chart versions for different regulatory periods
3. Audit trail of which master chart version was used for mapping
4. Future migration paths when standards change

VERSION FORMAT: "YYYY.Q" (e.g., "2024.1", "2025.1")

BREAKING: No - new field is additive
REQUIRES: None

CANONICAL REFERENCE:
- Section 1.1: Master Reference Chart (version field)
- Section 13.1: Master Chart Versioning
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add version field to master_accounts table.

    FIELD: version VARCHAR(10)
    DEFAULT: '2024.1' for existing accounts

    This field tracks which version of the master chart an account belongs to.
    Future updates to GAAP standards will create new versions while preserving
    old versions for historical reference.
    """

    # ========================================================================
    # STEP 1: Add version column
    # ========================================================================
    # JUSTIFICATION: Master chart evolves as accounting standards change
    # (ASC updates, new IFRS standards, etc.). Versioning allows companies
    # to:
    # - Reference which standard they were using at a point in time
    # - Migrate to new versions when ready
    # - Maintain audit trail of mapping provenance
    #
    # NOT NULL DEFAULT: All existing accounts are assigned version '2024.1'
    # ========================================================================

    op.add_column(
        'master_accounts',
        sa.Column('version', sa.String(10), nullable=False, server_default='2024.1')
    )

    # Remove server default after creation (only needed for migration)
    op.alter_column('master_accounts', 'version', server_default=None)

    # ========================================================================
    # STEP 2: Add index for version queries
    # ========================================================================
    # Companies will frequently query "give me all accounts for version X"
    # ========================================================================

    op.create_index(
        'ix_master_accounts_version',
        'master_accounts',
        ['version']
    )

    # ========================================================================
    # STEP 3: Log version assignment
    # ========================================================================

    op.execute("""
        DO $$
        DECLARE
            v_account_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO v_account_count FROM master_accounts;

            RAISE NOTICE 'Version field added to master_accounts table.';
            RAISE NOTICE 'All % existing accounts assigned version: 2024.1', v_account_count;
            RAISE NOTICE 'Future master chart updates should use incremented versions (e.g., 2025.1).';
        END $$;
    """)


def downgrade() -> None:
    """
    Remove version field from master_accounts.

    WARNING: This destroys version tracking information.
    Only use for rollback during migration issues.
    """

    op.drop_index('ix_master_accounts_version', table_name='master_accounts')
    op.drop_column('master_accounts', 'version')
