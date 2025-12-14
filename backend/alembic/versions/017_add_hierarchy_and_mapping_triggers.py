"""Add hierarchy and mapping enforcement triggers to company_accounts

Revision ID: 017
Revises: 016
Create Date: 2025-12-13

PHASE 2A - SCHEMA NORMALIZATION (Structured Template Tables)
Migration 5 of 6

PURPOSE:
Enforce account hierarchy and master mapping integrity at database level:
1. Prevent account hierarchy cycles (child cannot become own ancestor)
2. Enforce same-company parent relationships
3. Enforce master mapping consistency (account_type, normal_balance match)
4. Lock hierarchy fields after account is locked (immutability)

ENFORCEMENT TRIGGERS:
- Hierarchy cycle prevention (recursive CTE check)
- Same-company parent validation
- Master mapping consistency validation
- Locked account hierarchy immutability

BREAKING: No - enforcement only, no data changes
REQUIRES: Migrations 013-016 complete

CANONICAL REFERENCE:
- Phase 2A Specification: Hierarchy Enforcement
- Section: Account Hierarchy Rules
- Section: Account Locking Extensions
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add triggers to enforce hierarchy and mapping integrity.

    TRIGGERS ADDED:
    1. prevent_company_account_hierarchy_cycle - Detect and block cycles
    2. enforce_same_company_parent - Parent must be in same company
    3. enforce_master_mapping_consistency - Type/balance must match master
    4. prevent_locked_account_hierarchy_mutation - Lock parent_id and mapped_master_account_id
    """

    # ========================================================================
    # TRIGGER 1: Prevent hierarchy cycles
    # ========================================================================
    # A cycle occurs when an account becomes its own ancestor through parent_id.
    # Example: A → B → C → A (INVALID)
    #
    # DETECTION: Recursive CTE traversing upward from new parent_id.
    # If NEW.id appears in ancestry, cycle detected.
    # ========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_company_account_hierarchy_cycle()
        RETURNS TRIGGER AS $$
        DECLARE
            v_cycle_detected BOOLEAN;
        BEGIN
            -- Skip check if no parent (root account)
            IF NEW.parent_id IS NULL THEN
                RETURN NEW;
            END IF;

            -- Skip check if parent_id unchanged (UPDATE without parent change)
            IF TG_OP = 'UPDATE' AND NEW.parent_id = OLD.parent_id THEN
                RETURN NEW;
            END IF;

            -- Recursive CTE to traverse hierarchy upward
            WITH RECURSIVE hierarchy AS (
                -- Base case: immediate parent
                SELECT id, parent_id, 1 as depth
                FROM company_accounts
                WHERE id = NEW.parent_id

                UNION ALL

                -- Recursive case: traverse up
                SELECT ca.id, ca.parent_id, h.depth + 1
                FROM company_accounts ca
                JOIN hierarchy h ON ca.id = h.parent_id
                WHERE h.depth < 100  -- Prevent infinite loop
            )
            SELECT EXISTS (
                SELECT 1 FROM hierarchy WHERE id = NEW.id
            ) INTO v_cycle_detected;

            IF v_cycle_detected THEN
                RAISE EXCEPTION 'Cannot create hierarchy cycle: account "%" (code: %) would become its own ancestor',
                    NEW.description, NEW.code
                    USING ERRCODE = '23514';  -- check_violation
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_prevent_company_account_hierarchy_cycle
        BEFORE INSERT OR UPDATE OF parent_id ON company_accounts
        FOR EACH ROW
        EXECUTE FUNCTION prevent_company_account_hierarchy_cycle();
    """)

    # ========================================================================
    # TRIGGER 2: Enforce same-company parent
    # ========================================================================
    # parent_id must reference an account in the same company.
    # Cross-company parent references are nonsensical and break reporting.
    # ========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION enforce_same_company_parent()
        RETURNS TRIGGER AS $$
        DECLARE
            v_parent_company_id UUID;
        BEGIN
            -- Skip check if no parent (root account)
            IF NEW.parent_id IS NULL THEN
                RETURN NEW;
            END IF;

            -- Skip check if parent_id unchanged
            IF TG_OP = 'UPDATE' AND NEW.parent_id = OLD.parent_id THEN
                RETURN NEW;
            END IF;

            -- Lookup parent's company_id
            SELECT company_id INTO v_parent_company_id
            FROM company_accounts
            WHERE id = NEW.parent_id;

            -- Validate same company
            IF v_parent_company_id IS NULL THEN
                RAISE EXCEPTION 'Parent account (%) does not exist', NEW.parent_id
                    USING ERRCODE = '23503';  -- foreign_key_violation
            END IF;

            IF v_parent_company_id != NEW.company_id THEN
                RAISE EXCEPTION 'Parent account must be in same company: parent company_id = %, account company_id = %',
                    v_parent_company_id, NEW.company_id
                    USING ERRCODE = '23514';  -- check_violation
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_enforce_same_company_parent
        BEFORE INSERT OR UPDATE OF parent_id, company_id ON company_accounts
        FOR EACH ROW
        EXECUTE FUNCTION enforce_same_company_parent();
    """)

    # ========================================================================
    # TRIGGER 3: Enforce master mapping consistency
    # ========================================================================
    # If mapped_master_account_id is set, account_type and normal_balance
    # must match the master account's category and normal_balance.
    #
    # This ensures financial statements aggregate correctly.
    # ========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION enforce_master_mapping_consistency()
        RETURNS TRIGGER AS $$
        DECLARE
            v_master_category TEXT;
            v_master_normal_balance TEXT;
            v_expected_account_type TEXT;
        BEGIN
            -- Skip check if no master mapping
            IF NEW.mapped_master_account_id IS NULL THEN
                RETURN NEW;
            END IF;

            -- Skip check if mapping unchanged
            IF TG_OP = 'UPDATE' AND NEW.mapped_master_account_id = OLD.mapped_master_account_id THEN
                RETURN NEW;
            END IF;

            -- Lookup master account metadata
            SELECT category, normal_balance
            INTO v_master_category, v_master_normal_balance
            FROM master_accounts
            WHERE id = NEW.mapped_master_account_id;

            IF v_master_category IS NULL THEN
                RAISE EXCEPTION 'Master account (%) does not exist', NEW.mapped_master_account_id
                    USING ERRCODE = '23503';  -- foreign_key_violation
            END IF;

            -- Map master category to account_type
            -- Master uses plural ("Assets"), account_type uses singular ("Asset")
            v_expected_account_type := CASE
                WHEN v_master_category IN ('Assets', 'Asset') THEN 'Asset'
                WHEN v_master_category IN ('Liabilities', 'Liability') THEN 'Liability'
                WHEN v_master_category IN ('Equity', 'Equities') THEN 'Equity'
                WHEN v_master_category IN ('Revenue', 'Revenues') THEN 'Revenue'
                WHEN v_master_category IN ('Expenses', 'Expense') THEN 'Expense'
                ELSE NULL
            END;

            -- Validate account_type match
            IF NEW.account_type IS NOT NULL AND v_expected_account_type IS NOT NULL THEN
                IF NEW.account_type::TEXT != v_expected_account_type THEN
                    RAISE EXCEPTION 'Account type (%) does not match master account category (%)',
                        NEW.account_type, v_master_category
                        USING ERRCODE = '23514';  -- check_violation
                END IF;
            END IF;

            -- Validate normal_balance match (if master defines it)
            IF NEW.normal_balance IS NOT NULL AND v_master_normal_balance IS NOT NULL THEN
                IF NEW.normal_balance::TEXT != v_master_normal_balance THEN
                    RAISE EXCEPTION 'Normal balance (%) does not match master account normal balance (%)',
                        NEW.normal_balance, v_master_normal_balance
                        USING ERRCODE = '23514';  -- check_violation
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_enforce_master_mapping_consistency
        BEFORE INSERT OR UPDATE OF mapped_master_account_id, account_type, normal_balance ON company_accounts
        FOR EACH ROW
        EXECUTE FUNCTION enforce_master_mapping_consistency();
    """)

    # ========================================================================
    # TRIGGER 4: Prevent locked account hierarchy mutation
    # ========================================================================
    # Extends Phase 1 account locking (migration 009).
    # Once account is locked, parent_id and mapped_master_account_id are immutable.
    #
    # RATIONALE: Changing hierarchy or mapping after transactions posted
    # would invalidate historical financial statements.
    # ========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_locked_account_hierarchy_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Only enforce on UPDATE (INSERT always allowed)
            IF TG_OP != 'UPDATE' THEN
                RETURN NEW;
            END IF;

            -- Only enforce if account is locked
            IF OLD.is_locked = false THEN
                RETURN NEW;
            END IF;

            -- Check if parent_id changed
            IF NEW.parent_id IS DISTINCT FROM OLD.parent_id THEN
                RAISE EXCEPTION 'Cannot change parent_id of locked account "%". Account locked since % (reason: %)',
                    OLD.description, OLD.locked_at, OLD.locked_reason
                    USING ERRCODE = '23514';  -- check_violation
            END IF;

            -- Check if mapped_master_account_id changed
            IF NEW.mapped_master_account_id IS DISTINCT FROM OLD.mapped_master_account_id THEN
                RAISE EXCEPTION 'Cannot change mapped_master_account_id of locked account "%". Account locked since % (reason: %)',
                    OLD.description, OLD.locked_at, OLD.locked_reason
                    USING ERRCODE = '23514';  -- check_violation
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_prevent_locked_account_hierarchy_mutation
        BEFORE UPDATE OF parent_id, mapped_master_account_id ON company_accounts
        FOR EACH ROW
        EXECUTE FUNCTION prevent_locked_account_hierarchy_mutation();
    """)

    # ========================================================================
    # STEP 5: Log trigger creation
    # ========================================================================

    op.execute("""
        DO $$
        BEGIN
            RAISE NOTICE '=== MIGRATION 017: Hierarchy and Mapping Triggers Added ===';
            RAISE NOTICE 'Triggers:';
            RAISE NOTICE '  ✓ prevent_company_account_hierarchy_cycle';
            RAISE NOTICE '  ✓ enforce_same_company_parent';
            RAISE NOTICE '  ✓ enforce_master_mapping_consistency';
            RAISE NOTICE '  ✓ prevent_locked_account_hierarchy_mutation';
            RAISE NOTICE 'Enforcement:';
            RAISE NOTICE '  - No hierarchy cycles allowed';
            RAISE NOTICE '  - Parent must be in same company';
            RAISE NOTICE '  - Account type/balance must match master';
            RAISE NOTICE '  - Hierarchy immutable after account locked';
        END $$;
    """)


def downgrade() -> None:
    """
    Remove hierarchy and mapping enforcement triggers.

    WARNING: This removes critical integrity enforcement.
    Data corruption becomes possible without these triggers.
    Only use for rollback during migration issues.
    """

    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_locked_account_hierarchy_mutation ON company_accounts")
    op.execute("DROP TRIGGER IF EXISTS trg_enforce_master_mapping_consistency ON company_accounts")
    op.execute("DROP TRIGGER IF EXISTS trg_enforce_same_company_parent ON company_accounts")
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_company_account_hierarchy_cycle ON company_accounts")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS prevent_locked_account_hierarchy_mutation()")
    op.execute("DROP FUNCTION IF EXISTS enforce_master_mapping_consistency()")
    op.execute("DROP FUNCTION IF EXISTS enforce_same_company_parent()")
    op.execute("DROP FUNCTION IF EXISTS prevent_company_account_hierarchy_cycle()")
