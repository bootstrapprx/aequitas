"""Add normal_balance enum and column to CompanyAccount

Revision ID: 006
Revises: 005
Create Date: 2025-12-13

PHASE 1 - CRITICAL DATA INTEGRITY
Migration 4 of 10

PURPOSE:
Add normal balance classification to company accounts for:
1. Proper account balance calculation (debit balances vs credit balances)
2. Trial balance generation and validation
3. Financial statement presentation
4. Determining whether debits increase or decrease account balance

NORMAL BALANCE DERIVATION:
- Asset accounts: Debit
- Expense accounts: Debit
- Liability accounts: Credit
- Equity accounts: Credit
- Revenue accounts: Credit

EXCEPTION: Contra accounts (e.g., Accumulated Depreciation, Sales Returns)
have opposite normal balance from their parent type. Contra account
support will be added in Phase 4.

BREAKING: No - uses deterministic derivation from account_type
REQUIRES: Migration 005 (account_type) must be applied first

CANONICAL REFERENCE:
- Section 2.2: Normal Balance Derivation
- Section 3.2: Balance Calculation
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add normal_balance classification to company_accounts table.

    ENUM VALUES: Debit, Credit

    Normal balance is DERIVED from account_type:
    - Asset → Debit
    - Expense → Debit
    - Liability → Credit
    - Equity → Credit
    - Revenue → Credit

    MIGRATION STEPS:
    1. Create normalbalance ENUM
    2. Add normal_balance column (nullable initially)
    3. Backfill using derivation rules from account_type
    4. Make NOT NULL after validation
    """

    # ========================================================================
    # STEP 1: Create ENUM Type
    # ========================================================================
    # JUSTIFICATION: Normal balance is either Debit or Credit, never both,
    # never neither. ENUM provides type safety.
    # ========================================================================

    op.execute("""
        CREATE TYPE normalbalance AS ENUM ('Debit', 'Credit')
    """)

    # ========================================================================
    # STEP 2: Add Column (Nullable initially)
    # ========================================================================

    op.add_column(
        'company_accounts',
        sa.Column('normal_balance', sa.Enum('Debit', 'Credit', name='normalbalance'), nullable=True)
    )

    # ========================================================================
    # STEP 3: Backfill using account_type derivation
    # ========================================================================
    # DERIVATION RULES (standard accounting):
    #
    # Debit normal balance (increases with debit):
    #   - Assets (represent resources owned, increase with debit)
    #   - Expenses (represent resources consumed, increase with debit)
    #
    # Credit normal balance (increases with credit):
    #   - Liabilities (represent obligations, increase with credit)
    #   - Equity (represents ownership, increases with credit)
    #   - Revenue (represents income, increases with credit)
    #
    # EXCEPTION (future): Contra accounts reverse this rule
    # ========================================================================

    op.execute("""
        UPDATE company_accounts
        SET normal_balance = CASE account_type
            WHEN 'Asset' THEN 'Debit'::normalbalance
            WHEN 'Expense' THEN 'Debit'::normalbalance
            WHEN 'Liability' THEN 'Credit'::normalbalance
            WHEN 'Equity' THEN 'Credit'::normalbalance
            WHEN 'Revenue' THEN 'Credit'::normalbalance
            ELSE NULL
        END
        WHERE normal_balance IS NULL;
    """)

    # ========================================================================
    # STEP 4: Validate backfill completeness
    # ========================================================================

    op.execute("""
        DO $$
        DECLARE
            v_null_count INTEGER;
            v_total_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO v_total_count FROM company_accounts;
            SELECT COUNT(*) INTO v_null_count FROM company_accounts WHERE normal_balance IS NULL;

            IF v_null_count > 0 THEN
                RAISE WARNING 'Found % company accounts (out of %) without normal_balance. This indicates missing account_type.', v_null_count, v_total_count;
                RAISE WARNING 'Query: SELECT id, company_id, code, description, account_type FROM company_accounts WHERE normal_balance IS NULL;';
            ELSE
                RAISE NOTICE 'All % company accounts successfully assigned normal_balance.', v_total_count;
            END IF;
        END $$;
    """)

    # ========================================================================
    # STEP 5: Make NOT NULL (enforced now, not deferred)
    # ========================================================================
    # Since normal_balance is 100% derivable from account_type, we can
    # enforce NOT NULL immediately. Any NULL values indicate data issues
    # that should block migration.
    # ========================================================================

    op.execute("""
        ALTER TABLE company_accounts
        ALTER COLUMN normal_balance SET NOT NULL
    """)


def downgrade() -> None:
    """
    Remove normal_balance column and ENUM type.

    WARNING: This destroys normal balance classification data.
    Only use for rollback during migration issues.
    """

    # Drop column first
    op.drop_column('company_accounts', 'normal_balance')

    # Drop ENUM type
    op.execute("DROP TYPE IF EXISTS normalbalance CASCADE")
