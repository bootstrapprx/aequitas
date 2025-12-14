"""Add account locking mechanism to CompanyAccount

Revision ID: 007
Revises: 006
Create Date: 2025-12-13

PHASE 1 - CRITICAL DATA INTEGRITY
Migration 5 of 10

PURPOSE:
Implement account locking mechanism to enforce immutability after first use:
1. Prevent account type changes after transactions posted
2. Prevent account code changes after transactions posted
3. Track when and why account was locked
4. Support manual locking for administrative purposes

LOCKING TRIGGERS:
- FirstTransaction: Account locks automatically when first POSTED journal entry uses it
- PeriodClose: Account locks when fiscal period is closed
- Manual: Administrator explicitly locks account

LOCKED RESTRICTIONS:
- Cannot change account_type
- Cannot change code
- Cannot change normal_balance
- CAN change description/name (cosmetic)
- CAN be soft-deleted (is_active=false) if zero balance

BREAKING: No - new fields are additive
REQUIRES: None

CANONICAL REFERENCE:
- Section 5: Account Locking Rules
- Section 5.2: Locked Account Restrictions
- Section 5.3: Unlocking Protocol
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add account locking fields to company_accounts table.

    FIELDS ADDED:
    - is_locked: Boolean flag indicating lock status
    - locked_at: Timestamp when account was locked
    - locked_by: User ID who locked account (nullable for system locks)
    - locked_reason: Enum indicating why account was locked
    """

    # ========================================================================
    # STEP 1: Create lockedreason ENUM
    # ========================================================================
    # JUSTIFICATION: Lock reason is a closed set of valid triggers.
    # Using ENUM ensures consistency and prevents invalid values.
    # ========================================================================

    op.execute("""
        CREATE TYPE lockedreason AS ENUM (
            'FirstTransaction',
            'PeriodClose',
            'Manual'
        )
    """)

    # ========================================================================
    # STEP 2: Add is_locked column
    # ========================================================================
    # Default FALSE for existing accounts (initially unlocked)
    # ========================================================================

    op.add_column(
        'company_accounts',
        sa.Column('is_locked', sa.Boolean(), nullable=False, server_default='false')
    )

    # Remove server default after creation (only needed for migration)
    op.alter_column('company_accounts', 'is_locked', server_default=None)

    # ========================================================================
    # STEP 3: Add locked_at column
    # ========================================================================
    # Nullable - only populated when is_locked = true
    # ========================================================================

    op.add_column(
        'company_accounts',
        sa.Column('locked_at', sa.DateTime(), nullable=True)
    )

    # ========================================================================
    # STEP 4: Add locked_by column
    # ========================================================================
    # Nullable - system locks (FirstTransaction, PeriodClose) have NULL locked_by
    # Manual locks have user_id
    # Note: We don't add FK constraint here to avoid circular dependency issues
    # ========================================================================

    op.add_column(
        'company_accounts',
        sa.Column('locked_by', UUID(as_uuid=True), nullable=True)
    )

    # ========================================================================
    # STEP 5: Add locked_reason column
    # ========================================================================
    # Nullable - only populated when is_locked = true
    # ========================================================================

    op.add_column(
        'company_accounts',
        sa.Column('locked_reason', sa.Enum('FirstTransaction', 'PeriodClose', 'Manual', name='lockedreason'), nullable=True)
    )

    # ========================================================================
    # STEP 6: Add CHECK constraint for lock consistency
    # ========================================================================
    # BUSINESS RULE: If is_locked = true, then locked_at and locked_reason
    # must be populated. If is_locked = false, all lock fields must be NULL.
    # ========================================================================

    op.execute("""
        ALTER TABLE company_accounts
        ADD CONSTRAINT chk_lock_consistency
        CHECK (
            (is_locked = true AND locked_at IS NOT NULL AND locked_reason IS NOT NULL) OR
            (is_locked = false AND locked_at IS NULL AND locked_by IS NULL AND locked_reason IS NULL)
        )
    """)

    # ========================================================================
    # STEP 7: Backfill locked status for accounts with transactions
    # ========================================================================
    # Any account that has been used in a POSTED journal entry should be
    # locked with reason = 'FirstTransaction'
    # ========================================================================

    op.execute("""
        UPDATE company_accounts ca
        SET
            is_locked = true,
            locked_at = first_usage.posted_at,
            locked_by = NULL,  -- System lock, no user
            locked_reason = 'FirstTransaction'::lockedreason
        FROM (
            SELECT
                jel.company_account_id,
                MIN(je.posted_at) as posted_at
            FROM journal_entry_lines jel
            JOIN journal_entries je ON jel.journal_entry_id = je.id
            WHERE je.status = 'POSTED'
              AND je.posted_at IS NOT NULL
            GROUP BY jel.company_account_id
        ) first_usage
        WHERE ca.id = first_usage.company_account_id
          AND ca.is_locked = false;
    """)

    # ========================================================================
    # STEP 8: Log lock status summary
    # ========================================================================

    op.execute("""
        DO $$
        DECLARE
            v_total_accounts INTEGER;
            v_locked_accounts INTEGER;
            v_unlocked_accounts INTEGER;
        BEGIN
            SELECT COUNT(*) INTO v_total_accounts FROM company_accounts;
            SELECT COUNT(*) INTO v_locked_accounts FROM company_accounts WHERE is_locked = true;
            SELECT COUNT(*) INTO v_unlocked_accounts FROM company_accounts WHERE is_locked = false;

            RAISE NOTICE 'Account locking fields added successfully:';
            RAISE NOTICE '  Total accounts: %', v_total_accounts;
            RAISE NOTICE '  Locked accounts: % (% percent of total)', v_locked_accounts, ROUND(100.0 * v_locked_accounts / NULLIF(v_total_accounts, 0), 2);
            RAISE NOTICE '  Unlocked accounts: % (% percent of total)', v_unlocked_accounts, ROUND(100.0 * v_unlocked_accounts / NULLIF(v_total_accounts, 0), 2);
        END $$;
    """)


def downgrade() -> None:
    """
    Remove account locking fields.

    WARNING: This destroys lock status and audit trail.
    Only use for rollback during migration issues.
    """

    # Drop constraint first
    op.execute("ALTER TABLE company_accounts DROP CONSTRAINT IF EXISTS chk_lock_consistency")

    # Drop columns
    op.drop_column('company_accounts', 'locked_reason')
    op.drop_column('company_accounts', 'locked_by')
    op.drop_column('company_accounts', 'locked_at')
    op.drop_column('company_accounts', 'is_locked')

    # Drop ENUM type
    op.execute("DROP TYPE IF EXISTS lockedreason CASCADE")
