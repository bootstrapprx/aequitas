"""Create chart_templates table

Revision ID: 014
Revises: 013
Create Date: 2025-12-13

PHASE 2A - SCHEMA NORMALIZATION (Structured Template Tables)
Migration 2 of 6

PURPOSE:
Create canonical chart template structure to replace JSON blob templates:
1. Define explicit, versioned chart templates
2. Support jurisdiction-specific templates (US-GAAP, IFRS, etc.)
3. Enable template evolution tracking
4. Foundation for template-account relationships

BACKGROUND:
Current system uses ad-hoc JSON blobs in coa_templates.data.
Phase 2A introduces structured, relational template architecture:
- chart_templates: Template metadata
- chart_template_accounts: Individual accounts within template

This migration creates the template metadata table.
Next migration (015) creates the account detail table.

BREAKING: No - new table creation only
REQUIRES: Migration 013 complete

CANONICAL REFERENCE:
- Phase 2A Specification: Structured Template Tables
- Section: Chart Template Structure
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create chart_templates table for canonical template definitions.

    SCHEMA:
    - id: UUID primary key
    - name: Human-readable template name
    - jurisdiction: Accounting standard (US-GAAP, IFRS, etc.)
    - version: Template version (semantic versioning)
    - description: Purpose and scope of template
    - is_active: Enable/disable template without deletion
    - created_at: Creation timestamp
    - updated_at: Last modification timestamp

    BUSINESS RULES:
    - UNIQUE(jurisdiction, version): One version per jurisdiction
    - Active templates appear in company setup wizards
    - Inactive templates preserved for historical companies
    """

    # ========================================================================
    # STEP 1: Create chart_templates table
    # ========================================================================

    op.create_table(
        'chart_templates',

        # Primary key
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Template identification
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('jurisdiction', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Template status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Audit timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), onupdate=sa.text('now()')),

        # Constraints
        sa.UniqueConstraint('jurisdiction', 'version', name='uq_chart_templates_jurisdiction_version'),
    )

    # ========================================================================
    # STEP 2: Create indexes
    # ========================================================================

    # Index for template lookup by jurisdiction
    op.create_index(
        'ix_chart_templates_jurisdiction',
        'chart_templates',
        ['jurisdiction']
    )

    # Index for active template queries
    op.create_index(
        'ix_chart_templates_is_active',
        'chart_templates',
        ['is_active']
    )

    # Composite index for active templates by jurisdiction
    op.create_index(
        'ix_chart_templates_jurisdiction_active',
        'chart_templates',
        ['jurisdiction', 'is_active']
    )

    # ========================================================================
    # STEP 3: Create updated_at trigger
    # ========================================================================
    # Automatically update updated_at timestamp on row modification
    # ========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION update_chart_templates_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_chart_templates_updated_at
        BEFORE UPDATE ON chart_templates
        FOR EACH ROW
        EXECUTE FUNCTION update_chart_templates_updated_at();
    """)

    # ========================================================================
    # STEP 4: Seed initial templates
    # ========================================================================
    # Create foundational templates for common jurisdictions.
    # Detailed accounts will be added in migration 015.
    # ========================================================================

    op.execute("""
        INSERT INTO chart_templates (name, jurisdiction, version, description, is_active, created_at, updated_at)
        VALUES
            (
                'US GAAP - Standard Business',
                'US-GAAP',
                '2024.1',
                'Standard chart of accounts for US businesses following Generally Accepted Accounting Principles. Includes 345 master accounts across all major categories.',
                true,
                now(),
                now()
            ),
            (
                'IFRS - International Standard',
                'IFRS',
                '2024.1',
                'International Financial Reporting Standards compliant chart of accounts. Designed for multinational entities and global reporting.',
                true,
                now(),
                now()
            ),
            (
                'US GAAP - Small Business',
                'US-GAAP',
                '2024.1-SMB',
                'Simplified chart of accounts for small businesses. Subset of full US-GAAP template focusing on essential accounts.',
                true,
                now(),
                now()
            ),
            (
                'US GAAP - Non-Profit',
                'US-GAAP',
                '2024.1-NPO',
                'Specialized chart for non-profit organizations. Includes fund accounting and grant tracking accounts.',
                false,
                now(),
                now()
            )
    """)

    # ========================================================================
    # STEP 5: Log template creation
    # ========================================================================

    op.execute("""
        DO $$
        DECLARE
            v_template_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO v_template_count FROM chart_templates;

            RAISE NOTICE '=== MIGRATION 014: Chart Templates Created ===';
            RAISE NOTICE 'Total templates: %', v_template_count;
            RAISE NOTICE 'Templates:';
            RAISE NOTICE '  - US GAAP - Standard Business (2024.1)';
            RAISE NOTICE '  - IFRS - International Standard (2024.1)';
            RAISE NOTICE '  - US GAAP - Small Business (2024.1-SMB)';
            RAISE NOTICE '  - US GAAP - Non-Profit (2024.1-NPO) [INACTIVE]';
        END $$;
    """)


def downgrade() -> None:
    """
    Drop chart_templates table and associated triggers.

    WARNING: This destroys all template metadata.
    Template accounts (chart_template_accounts) must be dropped first.
    Only use for rollback during migration issues.
    """

    # Drop trigger first
    op.execute("DROP TRIGGER IF EXISTS trg_chart_templates_updated_at ON chart_templates")
    op.execute("DROP FUNCTION IF EXISTS update_chart_templates_updated_at()")

    # Drop indexes (automatically dropped with table, but explicit for clarity)
    op.drop_index('ix_chart_templates_jurisdiction_active', 'chart_templates')
    op.drop_index('ix_chart_templates_is_active', 'chart_templates')
    op.drop_index('ix_chart_templates_jurisdiction', 'chart_templates')

    # Drop table
    op.drop_table('chart_templates')
