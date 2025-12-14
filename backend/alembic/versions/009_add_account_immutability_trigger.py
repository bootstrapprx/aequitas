"""Add account type immutability trigger for locked accounts

Revision ID: 009
Revises: 008
Create Date: 2025-12-13

PHASE 1 - CRITICAL DATA INTEGRITY
Migration 7 of 10

PURPOSE:
Prevent modification of critical account fields when account is locked.
This maintains consistency of historical financial data and prevents
corruption of financial statements that rely on account classification.

IMMUTABLE FIELDS (when is_locked = true):
- account_type (Asset, Liability, Equity, Revenue, Expense)
- code (account identifier in chart of accounts)
- normal_balance (Debit, Credit)

MUTABLE FIELDS (even when locked):
- description / name (cosmetic changes allowed)
- is_active (soft delete allowed if zero balance)
- currency (if not used in transactions)

BREAKING: No - trigger enforcement only
REQUIRES: Migration 007 (account locking fields)

CANONICAL REFERENCE:
- Section 5.2: Locked Account Restrictions
- Section 8.1: Database-Level Invariants
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create trigger to prevent modification of critical fields when account is locked.

    TRIGGER FUNCTION: prevent_locked_account_mutation()
    - Fires BEFORE UPDATE on company_accounts
    - Blocks changes to account_type, code, normal_balance if is_locked = true
    - Allows changes to cosmetic fields (description, name)

    EXCEPTION: Unlocking the account (is_locked: true → false) is allowed
    and requires superuser privileges (enforced at application level).
    """

    # ========================================================================
    # CREATE TRIGGER FUNCTION
    # ========================================================================
    # JUSTIFICATION: Once an account is used in financial transactions,
    # changing its type or code would invalidate historical data integrity.
    # For example, changing an Asset account to a Liability account would
    # corrupt the balance sheet. This must be prevented at the database level.
    #
    # ENFORCEMENT: PostgreSQL BEFORE UPDATE trigger
    # ========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_locked_account_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Only enforce if account is currently locked
            IF OLD.is_locked = true THEN
                -- Allow unlocking (is_locked: true → false)
                -- This is a privileged operation validated at application level
                IF NEW.is_locked = false AND OLD.is_locked = true THEN
                    -- Unlocking is allowed, return early
                    RETURN NEW;
                END IF;

                -- Check for forbidden field changes
                IF OLD.account_type IS DISTINCT FROM NEW.account_type THEN
                    RAISE EXCEPTION
                        'Cannot change account_type of locked account % (%). Account is locked since %.',
                        OLD.code,
                        OLD.id,
                        OLD.locked_at
                    USING HINT = 'Unlock the account first (requires superuser privileges) or create a new account.';
                END IF;

                IF OLD.code IS DISTINCT FROM NEW.code THEN
                    RAISE EXCEPTION
                        'Cannot change code of locked account % (%). Account is locked since %.',
                        OLD.code,
                        OLD.id,
                        OLD.locked_at
                    USING HINT = 'Unlock the account first (requires superuser privileges) or create a new account.';
                END IF;

                IF OLD.normal_balance IS DISTINCT FROM NEW.normal_balance THEN
                    RAISE EXCEPTION
                        'Cannot change normal_balance of locked account % (%). Account is locked since %.',
                        OLD.code,
                        OLD.id,
                        OLD.locked_at
                    USING HINT = 'Normal balance is derived from account_type and cannot be changed independently.';
                END IF;

                -- Other fields (description, name, is_active, currency) are allowed to change
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # ========================================================================
    # CREATE TRIGGER
    # ========================================================================
    # Fires BEFORE UPDATE to prevent the change before it's committed
    # ========================================================================

    op.execute("""
        CREATE TRIGGER trg_prevent_locked_account_mutation
        BEFORE UPDATE ON company_accounts
        FOR EACH ROW
        EXECUTE FUNCTION prevent_locked_account_mutation()
    """)


def downgrade() -> None:
    """
    Remove account immutability trigger.

    WARNING: After downgrade, locked accounts can be freely modified.
    Data integrity is no longer guaranteed.
    """

    op.execute("DROP TRIGGER IF EXISTS trg_prevent_locked_account_mutation ON company_accounts")
    op.execute("DROP FUNCTION IF EXISTS prevent_locked_account_mutation()")
