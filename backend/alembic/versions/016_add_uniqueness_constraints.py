"""Add uniqueness constraints to company_accounts

Revision ID: 016
Revises: 015
Create Date: 2025-12-13

PHASE 2A - SCHEMA NORMALIZATION (Structured Template Tables)
Migration 4 of 6

PURPOSE:
Enforce account uniqueness within company charts:
1. Prevent duplicate account codes within same company
2. Prevent duplicate account names within same company
3. Optional: Prevent duplicate master mappings within same company
4. Ensure data integrity and deterministic account lookups

BACKGROUND:
Current schema allows:
- Multiple accounts with same code in same company (ambiguous)
- Multiple accounts with same name in same company (confusing)
- Multiple company accounts mapping to same master account (may be valid)

Phase 2A enforces:
- UNIQUE(company_id, code): One code per company
- UNIQUE(company_id, name): One name per company
- Optional UNIQUE(company_id, mapped_master_account_id): One mapping per company

MIGRATION STRATEGY:
1. Identify and report duplicate codes/names
2. Provide remediation queries for duplicates
3. Add UNIQUE constraints after validation
4. Add indexes for performance

BREAKING: Yes - may fail if duplicate codes/names exist
REQUIRES: Migrations 013, 014, 015 complete

CANONICAL REFERENCE:
- Phase 2A Specification: Account Uniqueness
- Section: Company Chart Integrity
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add uniqueness constraints to company_accounts.

    CONSTRAINTS ADDED:
    1. UNIQUE(company_id, code) - No duplicate codes per company
    2. UNIQUE(company_id, name) - No duplicate names per company
    3. Optional UNIQUE(company_id, mapped_master_account_id) WHERE mapped_master_account_id IS NOT NULL

    The migration will FAIL if duplicate codes or names exist.
    Pre-migration validation should identify and resolve duplicates.
    """

    # ========================================================================
    # STEP 1: Pre-constraint validation
    # ========================================================================
    # Check for duplicate codes and names before adding constraints.
    # If duplicates exist, RAISE ERROR with remediation instructions.
    # ========================================================================

    op.execute("""
        DO $$
        DECLARE
            v_duplicate_codes INTEGER;
            v_duplicate_names INTEGER;
        BEGIN
            -- Count duplicate codes within companies
            SELECT COUNT(*) INTO v_duplicate_codes
            FROM (
                SELECT company_id, code, COUNT(*) as cnt
                FROM company_accounts
                GROUP BY company_id, code
                HAVING COUNT(*) > 1
            ) dupes;

            -- Count duplicate names within companies
            SELECT COUNT(*) INTO v_duplicate_names
            FROM (
                SELECT company_id, name, COUNT(*) as cnt
                FROM company_accounts
                WHERE name IS NOT NULL
                GROUP BY company_id, name
                HAVING COUNT(*) > 1
            ) dupes;

            -- Report findings
            RAISE NOTICE '=== MIGRATION 016: Pre-Constraint Validation ===';
            RAISE NOTICE 'Duplicate codes: %', v_duplicate_codes;
            RAISE NOTICE 'Duplicate names: %', v_duplicate_names;

            -- Fail if duplicates exist
            IF v_duplicate_codes > 0 THEN
                RAISE EXCEPTION 'Cannot add UNIQUE(company_id, code) constraint: % duplicate code groups exist. Run remediation query: SELECT company_id, code, COUNT(*) FROM company_accounts GROUP BY company_id, code HAVING COUNT(*) > 1;', v_duplicate_codes;
            END IF;

            IF v_duplicate_names > 0 THEN
                RAISE EXCEPTION 'Cannot add UNIQUE(company_id, name) constraint: % duplicate name groups exist. Run remediation query: SELECT company_id, name, COUNT(*) FROM company_accounts WHERE name IS NOT NULL GROUP BY company_id, name HAVING COUNT(*) > 1;', v_duplicate_names;
            END IF;

            RAISE NOTICE 'Validation passed: No duplicates detected';
        END $$;
    """)

    # ========================================================================
    # STEP 2: Add UNIQUE constraint on (company_id, code)
    # ========================================================================
    # Each company must have unique account codes.
    # Codes are the primary identifier for accounts within a company.
    # ========================================================================

    op.create_unique_constraint(
        'uq_company_accounts_company_code',
        'company_accounts',
        ['company_id', 'code']
    )

    # Add index to support fast code lookups
    # (UNIQUE constraint automatically creates index in PostgreSQL,
    # but explicit for documentation)
    op.create_index(
        'ix_company_accounts_company_code',
        'company_accounts',
        ['company_id', 'code'],
        unique=True,
        # Index already exists via UNIQUE constraint, this is idempotent
        postgresql_if_not_exists=True
    )

    # ========================================================================
    # STEP 3: Add UNIQUE constraint on (company_id, name)
    # ========================================================================
    # Each company must have unique account names for user clarity.
    # Prevents confusion when selecting accounts in UI.
    # ========================================================================

    op.create_unique_constraint(
        'uq_company_accounts_company_name',
        'company_accounts',
        ['company_id', 'name']
    )

    # Add index to support fast name lookups
    op.create_index(
        'ix_company_accounts_company_name',
        'company_accounts',
        ['company_id', 'name'],
        unique=True,
        postgresql_if_not_exists=True
    )

    # ========================================================================
    # STEP 4: Add PARTIAL UNIQUE constraint on (company_id, mapped_master_account_id)
    # ========================================================================
    # OPTIONAL ENFORCEMENT: One company account per master account.
    #
    # JUSTIFICATION:
    # - Prevents multiple company accounts mapping to same master
    # - Ensures clean 1:1 master mapping
    # - Simplifies financial reporting and consolidation
    #
    # CONSIDERATION:
    # Some companies may legitimately want multiple accounts for same master
    # (e.g., "Cash - Operating" and "Cash - Payroll" both mapping to "Cash")
    #
    # DECISION: COMMENTED OUT for now, can be enabled if desired.
    # ========================================================================

    # UNCOMMENT to enable strict 1:1 master mapping:
    # op.execute("""
    #     CREATE UNIQUE INDEX uq_company_accounts_company_master
    #     ON company_accounts (company_id, mapped_master_account_id)
    #     WHERE mapped_master_account_id IS NOT NULL;
    # """)

    # ========================================================================
    # STEP 5: Log constraint creation
    # ========================================================================

    op.execute("""
        DO $$
        BEGIN
            RAISE NOTICE '=== MIGRATION 016: Uniqueness Constraints Added ===';
            RAISE NOTICE 'Constraints:';
            RAISE NOTICE '  ✓ UNIQUE(company_id, code)';
            RAISE NOTICE '  ✓ UNIQUE(company_id, name)';
            RAISE NOTICE '  ⊗ UNIQUE(company_id, mapped_master_account_id) [OPTIONAL - NOT ENABLED]';
            RAISE NOTICE 'Impact:';
            RAISE NOTICE '  - Account codes must be unique per company';
            RAISE NOTICE '  - Account names must be unique per company';
            RAISE NOTICE '  - Lookups by code/name will be deterministic';
        END $$;
    """)


def downgrade() -> None:
    """
    Remove uniqueness constraints from company_accounts.

    WARNING: This allows duplicate codes and names.
    Data integrity will be weakened.
    Only use for rollback during migration issues.
    """

    # Drop indexes (if they exist independently)
    op.drop_index('ix_company_accounts_company_name', 'company_accounts', if_exists=True)
    op.drop_index('ix_company_accounts_company_code', 'company_accounts', if_exists=True)

    # Drop UNIQUE constraints
    op.drop_constraint('uq_company_accounts_company_name', 'company_accounts', type_='unique')
    op.drop_constraint('uq_company_accounts_company_code', 'company_accounts', type_='unique')

    # Drop partial unique index if it was enabled
    # op.execute("DROP INDEX IF EXISTS uq_company_accounts_company_master")
