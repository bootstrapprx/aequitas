"""Relocate Advisory Metadata from MasterAccount Canon (Invariant B2, Zone C)

Revision ID: 032
Revises: 031
Create Date: 2025-12-23

CANON ENFORCEMENT: Intelligence Boundary (Zone C)
Canonical References: Canon IV (Intelligence Boundaries), Step 4 (Extension Boundaries)

PURPOSE:
Separate accounting truth (Zone A) from intelligence/advisory data (Zone C).
MasterAccount must contain ONLY conceptual accounting structure, not facts or hints.

ZONE VIOLATIONS REMEDIATED:

B2 - Concept-Only (MasterAccount Truth Purity)
  Violation: default_vendors, tags stored in master_accounts
  Solution: Extract to new master_account_intelligence table
  Impact: Clean separation of truth and intelligence

MIGRATION STRATEGY:

1. Create master_account_intelligence table (Zone C)
2. Migrate default_vendors and tags from master_accounts
3. Preserve all existing data (non-destructive)
4. Drop columns from master_accounts after migration
5. Update model relationships

BREAKING: Yes - removes columns from master_accounts
REQUIRES: master_accounts table with default_vendors, tags columns
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB


# revision identifiers, used by Alembic.
revision = '032'
down_revision = '031'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Relocate advisory metadata from MasterAccount to intelligence layer.
    """

    # =========================================================================
    # ZONE C: Create Intelligence Layer Table
    # =========================================================================

    op.create_table(
        'master_account_intelligence',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('master_account_id', UUID(as_uuid=True), sa.ForeignKey('master_accounts.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),

        # Advisory metadata (formerly in master_accounts)
        sa.Column('tags', ARRAY(sa.String), nullable=True, comment='AI-friendly keywords for classification'),
        sa.Column('default_vendors', ARRAY(sa.String), nullable=True, comment='Common vendor associations for auto-suggestion'),

        # Intelligence confidence scores
        sa.Column('classification_confidence', sa.Numeric(3, 2), nullable=True, comment='Confidence score for auto-classification (0.00-1.00)'),

        # Metadata
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),

        comment='Canon IV (Zone C): Advisory intelligence for master accounts. Read-only access to truth. Suggestions require human confirmation.'
    )

    # =========================================================================
    # DATA MIGRATION: Move Advisory Data to Intelligence Table
    # =========================================================================

    # Migrate existing default_vendors and tags to intelligence table
    op.execute("""
    INSERT INTO master_account_intelligence (master_account_id, tags, default_vendors, created_at, updated_at)
    SELECT
        id AS master_account_id,
        tags,
        default_vendors,
        NOW() AS created_at,
        NOW() AS updated_at
    FROM master_accounts
    WHERE tags IS NOT NULL OR default_vendors IS NOT NULL;
    """)

    # Log migration results
    op.execute("""
    DO $$
    DECLARE
        migrated_count INTEGER;
    BEGIN
        SELECT COUNT(*) INTO migrated_count FROM master_account_intelligence;
        RAISE NOTICE 'CANON B2 MIGRATION: Migrated advisory metadata for % master accounts to intelligence layer', migrated_count;
    END $$;
    """)

    # =========================================================================
    # SCHEMA CLEANUP: Remove Advisory Columns from Truth Core
    # =========================================================================

    # Drop default_vendors column from master_accounts
    op.drop_column('master_accounts', 'default_vendors')

    # Drop tags column from master_accounts
    op.drop_column('master_accounts', 'tags')

    # =========================================================================
    # DOCUMENTATION: Update Table Comments
    # =========================================================================

    op.execute("""
    COMMENT ON TABLE master_accounts IS
    'Canon I: Accounting Truth (Zone A). Immutable, versioned foundation. Contains ONLY conceptual accounting structure. Advisory metadata extracted to intelligence layer.';
    """)

    op.execute("""
    COMMENT ON TABLE master_account_intelligence IS
    'Canon IV (Zone C): Intelligence & Advisory Layer. Provides suggestions, tags, vendor hints. Read-only access to truth core. Must require human confirmation.';
    """)


def downgrade() -> None:
    """
    Restore advisory metadata to MasterAccount table.

    WARNING: This reverses zone separation and violates canon architecture.
    Only permitted in development for rollback purposes.
    """

    # Re-add columns to master_accounts
    op.add_column('master_accounts', sa.Column('tags', ARRAY(sa.String), nullable=True))
    op.add_column('master_accounts', sa.Column('default_vendors', ARRAY(sa.String), nullable=True))

    # Migrate data back from intelligence table
    op.execute("""
    UPDATE master_accounts ma
    SET
        tags = mai.tags,
        default_vendors = mai.default_vendors
    FROM master_account_intelligence mai
    WHERE ma.id = mai.master_account_id;
    """)

    # Drop intelligence table
    op.drop_table('master_account_intelligence')

    # Restore old comment
    op.execute("""
    COMMENT ON TABLE master_accounts IS
    'Master Chart of Accounts (US-GAAP reference). Immutable, versioned foundation.';
    """)
