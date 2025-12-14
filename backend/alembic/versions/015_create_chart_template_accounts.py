"""Create chart_template_accounts table

Revision ID: 015
Revises: 014
Create Date: 2025-12-13

PHASE 2A - SCHEMA NORMALIZATION (Structured Template Tables)
Migration 3 of 6

PURPOSE:
Create detailed account structure within chart templates:
1. Define individual accounts belonging to each template
2. Link template accounts to master chart accounts
3. Support account hierarchy within templates
4. Mark mandatory accounts that cannot be omitted
5. Control custom account creation per template node

BACKGROUND:
chart_templates defines template metadata (migration 014).
chart_template_accounts defines the actual accounts in each template.

Each template account:
- References a master_account (for classification/metadata)
- May have a parent_id (for hierarchy)
- Has template-specific properties (code, name, sort_order)
- Indicates if mandatory (cannot be deleted from company chart)
- Indicates if custom children allowed (extensibility)

BREAKING: No - new table creation only
REQUIRES: Migrations 013, 014 complete

CANONICAL REFERENCE:
- Phase 2A Specification: Structured Template Tables
- Section: Template Account Structure
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create chart_template_accounts table for template account details.

    SCHEMA:
    - id: UUID primary key
    - template_id: FK to chart_templates (which template)
    - master_account_id: FK to master_accounts (classification source)
    - parent_id: Self-referential FK (hierarchy within template)
    - code: Account code within template (e.g., "1.10.10.10")
    - name: Account name within template
    - is_mandatory: Cannot be omitted from company charts
    - allow_custom_children: Company can add custom sub-accounts
    - sort_order: Display order within parent
    - created_at: Creation timestamp

    BUSINESS RULES:
    - UNIQUE(template_id, code): No duplicate codes within template
    - parent_id must reference same template
    - Hierarchy must be acyclic
    - Mandatory accounts must exist in all companies using template
    """

    # ========================================================================
    # STEP 1: Create chart_template_accounts table
    # ========================================================================

    op.create_table(
        'chart_template_accounts',

        # Primary key
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Template relationship
        sa.Column('template_id', UUID(as_uuid=True), sa.ForeignKey('chart_templates.id', ondelete='CASCADE'), nullable=False, index=True),

        # Master chart reference (defines account classification)
        sa.Column('master_account_id', UUID(as_uuid=True), sa.ForeignKey('master_accounts.id', ondelete='RESTRICT'), nullable=False, index=True),

        # Hierarchy within template
        sa.Column('parent_id', UUID(as_uuid=True), nullable=True),

        # Account identification
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),

        # Template-specific properties
        sa.Column('is_mandatory', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('allow_custom_children', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sort_order', sa.Integer(), nullable=False),

        # Audit timestamp
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),

        # Constraints
        sa.UniqueConstraint('template_id', 'code', name='uq_template_accounts_template_code'),
    )

    # ========================================================================
    # STEP 2: Add self-referential foreign key for hierarchy
    # ========================================================================
    # Cannot be added inline due to self-reference.
    # ON DELETE CASCADE: If parent account removed, children removed.
    # ========================================================================

    op.create_foreign_key(
        'fk_chart_template_accounts_parent_id',
        'chart_template_accounts',
        'chart_template_accounts',
        ['parent_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # ========================================================================
    # STEP 3: Create indexes
    # ========================================================================

    # Index for template lookups
    op.create_index(
        'ix_chart_template_accounts_template_id',
        'chart_template_accounts',
        ['template_id']
    )

    # Index for hierarchy traversal
    op.create_index(
        'ix_chart_template_accounts_parent_id',
        'chart_template_accounts',
        ['parent_id']
    )

    # Index for master account lookups
    op.create_index(
        'ix_chart_template_accounts_master_account_id',
        'chart_template_accounts',
        ['master_account_id']
    )

    # Index for mandatory account queries
    op.create_index(
        'ix_chart_template_accounts_is_mandatory',
        'chart_template_accounts',
        ['template_id', 'is_mandatory']
    )

    # Index for sort order
    op.create_index(
        'ix_chart_template_accounts_sort_order',
        'chart_template_accounts',
        ['template_id', 'parent_id', 'sort_order']
    )

    # ========================================================================
    # STEP 4: Add CHECK constraint for hierarchy integrity
    # ========================================================================
    # Ensure parent_id references same template (if not NULL)
    # ========================================================================

    op.execute("""
        ALTER TABLE chart_template_accounts
        ADD CONSTRAINT chk_template_accounts_same_template_parent
        CHECK (
            parent_id IS NULL OR
            EXISTS (
                SELECT 1 FROM chart_template_accounts parent
                WHERE parent.id = chart_template_accounts.parent_id
                  AND parent.template_id = chart_template_accounts.template_id
            )
        )
    """)

    # ========================================================================
    # STEP 5: Create trigger to prevent hierarchy cycles
    # ========================================================================
    # Cycles break account aggregation and reporting.
    # Use recursive CTE to detect cycles before INSERT/UPDATE.
    # ========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_template_account_hierarchy_cycle()
        RETURNS TRIGGER AS $$
        DECLARE
            v_cycle_detected BOOLEAN;
        BEGIN
            -- Skip check if no parent (root account)
            IF NEW.parent_id IS NULL THEN
                RETURN NEW;
            END IF;

            -- Recursive CTE to traverse hierarchy upward
            WITH RECURSIVE hierarchy AS (
                -- Base case: immediate parent
                SELECT id, parent_id, 1 as depth
                FROM chart_template_accounts
                WHERE id = NEW.parent_id

                UNION ALL

                -- Recursive case: traverse up
                SELECT cta.id, cta.parent_id, h.depth + 1
                FROM chart_template_accounts cta
                JOIN hierarchy h ON cta.id = h.parent_id
                WHERE h.depth < 100  -- Prevent infinite loop
            )
            SELECT EXISTS (
                SELECT 1 FROM hierarchy WHERE id = NEW.id
            ) INTO v_cycle_detected;

            IF v_cycle_detected THEN
                RAISE EXCEPTION 'Cannot create hierarchy cycle: account % would become its own ancestor', NEW.code;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_prevent_template_account_hierarchy_cycle
        BEFORE INSERT OR UPDATE OF parent_id ON chart_template_accounts
        FOR EACH ROW
        EXECUTE FUNCTION prevent_template_account_hierarchy_cycle();
    """)

    # ========================================================================
    # STEP 6: Log table creation
    # ========================================================================

    op.execute("""
        DO $$
        BEGIN
            RAISE NOTICE '=== MIGRATION 015: Chart Template Accounts Table Created ===';
            RAISE NOTICE 'Table: chart_template_accounts';
            RAISE NOTICE 'Constraints:';
            RAISE NOTICE '  - UNIQUE(template_id, code)';
            RAISE NOTICE '  - FK template_id → chart_templates';
            RAISE NOTICE '  - FK master_account_id → master_accounts';
            RAISE NOTICE '  - FK parent_id → chart_template_accounts (self-ref)';
            RAISE NOTICE '  - CHECK same template parent';
            RAISE NOTICE 'Triggers:';
            RAISE NOTICE '  - Hierarchy cycle prevention';
            RAISE NOTICE 'Next Step: Seed template accounts from master chart data';
        END $$;
    """)


def downgrade() -> None:
    """
    Drop chart_template_accounts table and associated triggers.

    WARNING: This destroys all template account definitions.
    Must be executed before dropping chart_templates (migration 014).
    Only use for rollback during migration issues.
    """

    # Drop triggers first
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_template_account_hierarchy_cycle ON chart_template_accounts")
    op.execute("DROP FUNCTION IF EXISTS prevent_template_account_hierarchy_cycle()")

    # Drop constraints (explicit for documentation)
    op.execute("ALTER TABLE chart_template_accounts DROP CONSTRAINT IF EXISTS chk_template_accounts_same_template_parent")

    # Drop indexes (automatically dropped with table, but explicit for clarity)
    op.drop_index('ix_chart_template_accounts_sort_order', 'chart_template_accounts')
    op.drop_index('ix_chart_template_accounts_is_mandatory', 'chart_template_accounts')
    op.drop_index('ix_chart_template_accounts_master_account_id', 'chart_template_accounts')
    op.drop_index('ix_chart_template_accounts_parent_id', 'chart_template_accounts')
    op.drop_index('ix_chart_template_accounts_template_id', 'chart_template_accounts')

    # Drop foreign key constraints
    op.drop_constraint('fk_chart_template_accounts_parent_id', 'chart_template_accounts', type_='foreignkey')

    # Drop table (CASCADE will handle remaining FKs)
    op.drop_table('chart_template_accounts')
