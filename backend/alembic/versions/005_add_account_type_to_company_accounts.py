"""Add account_type enum and column to CompanyAccount

Revision ID: 005
Revises: 004
Create Date: 2025-12-13

PHASE 1 - CRITICAL DATA INTEGRITY
Migration 3 of 10

PURPOSE:
Add explicit account type classification to company accounts for:
1. GAAP-compliant financial statement generation
2. Trial balance calculation with proper grouping
3. Normal balance derivation
4. Account balance calculation logic

BREAKING: Yes - requires data backfill to populate account_type
REQUIRES: Master account mapping for data migration

DATA MIGRATION STRATEGY:
1. Create ENUM type for account classification
2. Add nullable account_type column
3. Backfill from master_account.category (via join)
4. For unmapped accounts, derive from code prefix or manual classification
5. Make column NOT NULL after backfill

CANONICAL REFERENCE:
- Section 1.1: Master Reference Chart (account_type field)
- Section 1.3: Company-Specific Chart
- Section 2.1: Account Type Classification
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add account_type classification to company_accounts table.

    ENUM VALUES: Asset, Liability, Equity, Revenue, Expense

    This is DIFFERENT from the existing 'type' field which indicates
    Header ('H') vs Detail ('D'). The account_type field classifies
    the account for financial statement purposes.

    MIGRATION STEPS:
    1. Create accounttype ENUM
    2. Add account_type column (nullable initially)
    3. Backfill from master_account.category
    4. Make NOT NULL (in separate migration after validation)
    """

    # ========================================================================
    # STEP 1: Create ENUM Type
    # ========================================================================
    # JUSTIFICATION: Account type is a closed set of values defined by GAAP.
    # Using ENUM provides type safety and prevents invalid values.
    #
    # NOTE: PostgreSQL ENUMs are schema-level objects and persist independently
    # of tables. Downgrade must handle this carefully.
    # ========================================================================

    op.execute("""
        CREATE TYPE accounttype AS ENUM (
            'Asset',
            'Liability',
            'Equity',
            'Revenue',
            'Expense'
        )
    """)

    # ========================================================================
    # STEP 2: Add Column (Nullable for now)
    # ========================================================================
    # Column is nullable initially to allow gradual data migration.
    # A subsequent migration will make it NOT NULL after backfill validation.
    # ========================================================================

    op.add_column(
        'company_accounts',
        sa.Column('account_type', sa.Enum('Asset', 'Liability', 'Equity', 'Revenue', 'Expense', name='accounttype'), nullable=True)
    )

    # ========================================================================
    # STEP 3: Backfill from master_accounts.category
    # ========================================================================
    # STRATEGY: Use master_account.category to populate account_type
    #
    # Expected master_account.category values:
    # - "Assets" → Asset
    # - "Liabilities" → Liability
    # - "Equity" → Equity
    # - "Revenue" → Revenue
    # - "Expenses" → Expense
    #
    # For unmapped accounts (no master_account_code), we'll need manual
    # classification or code-based heuristics:
    # - Code starting with "1" → Asset
    # - Code starting with "2" → Liability
    # - Code starting with "3" → Equity
    # - Code starting with "4" → Revenue
    # - Code starting with "5" or "6" → Expense
    # ========================================================================

    op.execute("""
        UPDATE company_accounts ca
        SET account_type = CASE
            -- Map from master account category (exact match)
            WHEN ma.category = 'Assets' THEN 'Asset'::accounttype
            WHEN ma.category = 'Liabilities' THEN 'Liability'::accounttype
            WHEN ma.category = 'Equity' THEN 'Equity'::accounttype
            WHEN ma.category = 'Revenue' THEN 'Revenue'::accounttype
            WHEN ma.category = 'Expenses' THEN 'Expense'::accounttype

            -- Map from master account category (plural variations)
            WHEN ma.category = 'Asset' THEN 'Asset'::accounttype
            WHEN ma.category = 'Liability' THEN 'Liability'::accounttype
            WHEN ma.category = 'Equities' THEN 'Equity'::accounttype
            WHEN ma.category = 'Revenues' THEN 'Revenue'::accounttype
            WHEN ma.category = 'Expense' THEN 'Expense'::accounttype

            -- Fallback: should not happen if master data is clean
            ELSE NULL
        END
        FROM master_accounts ma
        WHERE ca.master_account_code = ma.code
          AND ca.account_type IS NULL;
    """)

    # ========================================================================
    # STEP 4: Backfill unmapped accounts using code heuristics
    # ========================================================================
    # For accounts without master_account_code, use standard code prefixes
    # ========================================================================

    op.execute("""
        UPDATE company_accounts
        SET account_type = CASE
            WHEN code ~ '^1\.' THEN 'Asset'::accounttype
            WHEN code ~ '^2\.' THEN 'Liability'::accounttype
            WHEN code ~ '^3\.' THEN 'Equity'::accounttype
            WHEN code ~ '^4\.' THEN 'Revenue'::accounttype
            WHEN code ~ '^[56]\.' THEN 'Expense'::accounttype
            ELSE NULL
        END
        WHERE account_type IS NULL
          AND master_account_code IS NULL;
    """)

    # ========================================================================
    # STEP 5: Log unmapped accounts (for manual review)
    # ========================================================================
    # Any accounts still NULL need manual classification
    # ========================================================================

    op.execute("""
        DO $$
        DECLARE
            v_unmapped_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO v_unmapped_count
            FROM company_accounts
            WHERE account_type IS NULL;

            IF v_unmapped_count > 0 THEN
                RAISE WARNING 'Found % company accounts without account_type classification. Manual review required.', v_unmapped_count;
                RAISE WARNING 'Query to identify: SELECT id, company_id, code, description FROM company_accounts WHERE account_type IS NULL;';
            ELSE
                RAISE NOTICE 'All company accounts successfully classified with account_type.';
            END IF;
        END $$;
    """)

    # ========================================================================
    # NOTE: Making account_type NOT NULL deferred to migration 005b
    # ========================================================================
    # This allows for manual review and correction of unmapped accounts
    # before enforcing NOT NULL constraint.
    # ========================================================================


def downgrade() -> None:
    """
    Remove account_type column and ENUM type.

    WARNING: This destroys account type classification data.
    Only use for rollback during migration issues.
    """

    # Drop column first
    op.drop_column('company_accounts', 'account_type')

    # Drop ENUM type
    # Note: PostgreSQL requires explicit CASCADE to drop ENUM if still referenced
    op.execute("DROP TYPE IF EXISTS accounttype CASCADE")
