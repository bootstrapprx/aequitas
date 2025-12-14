"""Add mandatory account enforcement for template compliance

Revision ID: 018
Revises: 017
Create Date: 2025-12-13

PHASE 2A - SCHEMA NORMALIZATION (Structured Template Tables)
Migration 6 of 6

PURPOSE:
Enforce that companies using chart templates include all mandatory accounts:
1. Create company_template_usage table to track template assignment
2. Add triggers to prevent deletion of mandatory accounts
3. Add triggers to prevent deactivation of mandatory accounts
4. Validate mandatory account presence on template assignment

BACKGROUND:
chart_template_accounts.is_mandatory indicates accounts that MUST exist
in any company chart using that template.

Examples of mandatory accounts:
- Cash (required for any business)
- Retained Earnings (required for equity tracking)
- Revenue/Expense summary accounts (required for closing entries)

ENFORCEMENT:
- When company assigns template, all mandatory accounts must be created
- Once created, mandatory accounts cannot be deleted
- Once created, mandatory accounts cannot be deactivated (is_active = false)
- Manual override requires superuser privileges (application-level)

BREAKING: No - new table and enforcement only
REQUIRES: Migrations 013-017 complete

CANONICAL REFERENCE:
- Phase 2A Specification: Mandatory Account Enforcement
- Section: Template Compliance Rules
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add mandatory account enforcement infrastructure.

    TABLES ADDED:
    - company_template_usage: Tracks which template each company uses

    TRIGGERS ADDED:
    - prevent_mandatory_account_deletion
    - prevent_mandatory_account_deactivation
    """

    # ========================================================================
    # STEP 1: Create company_template_usage table
    # ========================================================================
    # Tracks which template each company's chart is based on.
    # Used to enforce mandatory account presence.
    # ========================================================================

    op.create_table(
        'company_template_usage',

        # Primary key
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Foreign keys
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('template_id', UUID(as_uuid=True), sa.ForeignKey('chart_templates.id', ondelete='RESTRICT'), nullable=False, index=True),

        # Metadata
        sa.Column('assigned_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('assigned_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),

        # Constraints
        sa.UniqueConstraint('company_id', name='uq_company_template_usage_company_id'),
    )

    # Indexes for company_id and template_id are automatically created
    # by index=True on their column definitions

    # ========================================================================
    # STEP 2: Add template_account_id to company_accounts (optional)
    # ========================================================================
    # Tracks which template account a company account was created from.
    # Used to identify mandatory accounts for enforcement.
    # ========================================================================

    op.add_column(
        'company_accounts',
        sa.Column('template_account_id', UUID(as_uuid=True), nullable=True)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_company_accounts_template_account_id',
        'company_accounts',
        'chart_template_accounts',
        ['template_account_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Add index
    op.create_index(
        'ix_company_accounts_template_account_id',
        'company_accounts',
        ['template_account_id']
    )

    # ========================================================================
    # STEP 3: Create trigger to prevent mandatory account deletion
    # ========================================================================
    # If company_account.template_account_id references a mandatory template
    # account, deletion is blocked.
    # ========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_mandatory_account_deletion()
        RETURNS TRIGGER AS $$
        DECLARE
            v_is_mandatory BOOLEAN;
            v_template_account_name TEXT;
        BEGIN
            -- Skip check if account not linked to template
            IF OLD.template_account_id IS NULL THEN
                RETURN OLD;
            END IF;

            -- Check if template account is mandatory
            SELECT is_mandatory, name
            INTO v_is_mandatory, v_template_account_name
            FROM chart_template_accounts
            WHERE id = OLD.template_account_id;

            IF v_is_mandatory = true THEN
                RAISE EXCEPTION 'Cannot delete mandatory account "%" (code: %). This account is required by the chart template.',
                    OLD.description, OLD.code
                    USING ERRCODE = '23514',  -- check_violation
                          HINT = 'Mandatory accounts ensure compliance with accounting standards and cannot be removed.';
            END IF;

            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_prevent_mandatory_account_deletion
        BEFORE DELETE ON company_accounts
        FOR EACH ROW
        EXECUTE FUNCTION prevent_mandatory_account_deletion();
    """)

    # ========================================================================
    # STEP 4: Create trigger to prevent mandatory account deactivation
    # ========================================================================
    # Prevent is_active = false on mandatory accounts.
    # ========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_mandatory_account_deactivation()
        RETURNS TRIGGER AS $$
        DECLARE
            v_is_mandatory BOOLEAN;
        BEGIN
            -- Only enforce on UPDATE
            IF TG_OP != 'UPDATE' THEN
                RETURN NEW;
            END IF;

            -- Skip check if is_active unchanged or being activated
            IF NEW.is_active = OLD.is_active OR NEW.is_active = true THEN
                RETURN NEW;
            END IF;

            -- Skip check if account not linked to template
            IF NEW.template_account_id IS NULL THEN
                RETURN NEW;
            END IF;

            -- Check if template account is mandatory
            SELECT is_mandatory
            INTO v_is_mandatory
            FROM chart_template_accounts
            WHERE id = NEW.template_account_id;

            IF v_is_mandatory = true THEN
                RAISE EXCEPTION 'Cannot deactivate mandatory account "%" (code: %). This account is required by the chart template.',
                    OLD.description, OLD.code
                    USING ERRCODE = '23514',  -- check_violation
                          HINT = 'Mandatory accounts must remain active for accounting compliance.';
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_prevent_mandatory_account_deactivation
        BEFORE UPDATE OF is_active ON company_accounts
        FOR EACH ROW
        EXECUTE FUNCTION prevent_mandatory_account_deactivation();
    """)

    # ========================================================================
    # STEP 5: Create helper function to validate mandatory accounts
    # ========================================================================
    # Validates that all mandatory accounts from template exist in company chart.
    # Can be called by application layer when assigning template.
    # ========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION validate_mandatory_accounts(
            p_company_id UUID,
            p_template_id UUID
        )
        RETURNS TABLE (
            missing_account_code TEXT,
            missing_account_name TEXT
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT
                cta.code,
                cta.name
            FROM chart_template_accounts cta
            WHERE cta.template_id = p_template_id
              AND cta.is_mandatory = true
              AND NOT EXISTS (
                  SELECT 1
                  FROM company_accounts ca
                  WHERE ca.company_id = p_company_id
                    AND ca.template_account_id = cta.id
              );
        END;
        $$ LANGUAGE plpgsql;
    """)

    # ========================================================================
    # STEP 6: Log creation
    # ========================================================================

    op.execute("""
        DO $$
        BEGIN
            RAISE NOTICE '=== MIGRATION 018: Mandatory Account Enforcement Added ===';
            RAISE NOTICE 'Tables:';
            RAISE NOTICE '  ✓ company_template_usage';
            RAISE NOTICE 'Columns:';
            RAISE NOTICE '  ✓ company_accounts.template_account_id';
            RAISE NOTICE 'Triggers:';
            RAISE NOTICE '  ✓ prevent_mandatory_account_deletion';
            RAISE NOTICE '  ✓ prevent_mandatory_account_deactivation';
            RAISE NOTICE 'Functions:';
            RAISE NOTICE '  ✓ validate_mandatory_accounts(company_id, template_id)';
            RAISE NOTICE 'Enforcement:';
            RAISE NOTICE '  - Mandatory accounts cannot be deleted';
            RAISE NOTICE '  - Mandatory accounts cannot be deactivated';
            RAISE NOTICE '  - Application must create all mandatory accounts on template assignment';
            RAISE NOTICE '';
            RAISE NOTICE '=== PHASE 2A COMPLETE ===';
            RAISE NOTICE 'All 6 migrations successfully applied.';
            RAISE NOTICE 'Schema normalization is complete.';
            RAISE NOTICE 'Next: Update application models and services.';
        END $$;
    """)


def downgrade() -> None:
    """
    Remove mandatory account enforcement.

    WARNING: This removes protection against deleting required accounts.
    Only use for rollback during migration issues.
    """

    # Drop helper function
    op.execute("DROP FUNCTION IF EXISTS validate_mandatory_accounts(UUID, UUID)")

    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_mandatory_account_deactivation ON company_accounts")
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_mandatory_account_deletion ON company_accounts")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS prevent_mandatory_account_deactivation()")
    op.execute("DROP FUNCTION IF EXISTS prevent_mandatory_account_deletion()")

    # Drop column
    op.drop_index('ix_company_accounts_template_account_id', 'company_accounts')
    op.drop_constraint('fk_company_accounts_template_account_id', 'company_accounts', type_='foreignkey')
    op.drop_column('company_accounts', 'template_account_id')

    # Drop table (indexes automatically dropped with table)
    op.drop_table('company_template_usage')
