"""Add auto-lock trigger for accounts on first posted transaction

Revision ID: 008
Revises: 007
Create Date: 2025-12-13

PHASE 1 - CRITICAL DATA INTEGRITY
Migration 6 of 10

PURPOSE:
Automatically lock accounts when first used in a POSTED journal entry.
This prevents account type and code changes after the account has been
used in financial transactions, preserving data integrity and audit trail.

TRIGGER BEHAVIOR:
- Fires AFTER INSERT on journal_entry_lines
- Only acts when parent journal entry status = 'POSTED'
- Locks account if not already locked
- Sets locked_reason = 'FirstTransaction'
- Sets locked_at = journal entry posted_at timestamp

BREAKING: No - trigger enforcement only
REQUIRES: Migration 007 (account locking fields)

CANONICAL REFERENCE:
- Section 5.1: Lock Triggers
- Section 8.1: Database-Level Invariants
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create trigger to auto-lock accounts on first POSTED transaction.

    TRIGGER FUNCTION: auto_lock_account_on_first_transaction()
    - Checks if journal entry is POSTED
    - Locks account if currently unlocked
    - Records lock timestamp and reason

    This ensures accounts cannot be modified after being used in
    financial reporting, maintaining audit trail integrity.
    """

    # ========================================================================
    # CREATE TRIGGER FUNCTION
    # ========================================================================
    # JUSTIFICATION: Account immutability after first use is a fundamental
    # requirement for audit compliance. Once an account appears in posted
    # financial records, its classification (type, code) must not change.
    #
    # ENFORCEMENT: Database trigger (cannot be bypassed by application code)
    # ========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION auto_lock_account_on_first_transaction()
        RETURNS TRIGGER AS $$
        DECLARE
            v_entry_status VARCHAR;
            v_entry_posted_at TIMESTAMP;
            v_account_locked BOOLEAN;
        BEGIN
            -- Get journal entry status and posted timestamp
            SELECT status, posted_at
            INTO v_entry_status, v_entry_posted_at
            FROM journal_entries
            WHERE id = NEW.journal_entry_id;

            -- Only proceed if entry is POSTED
            IF v_entry_status = 'POSTED' THEN
                -- Check if account is already locked
                SELECT is_locked
                INTO v_account_locked
                FROM company_accounts
                WHERE id = NEW.company_account_id;

                -- Lock account if not already locked
                IF NOT v_account_locked THEN
                    UPDATE company_accounts
                    SET
                        is_locked = true,
                        locked_at = v_entry_posted_at,
                        locked_by = NULL,  -- System lock, no user
                        locked_reason = 'FirstTransaction'
                    WHERE id = NEW.company_account_id;
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # ========================================================================
    # CREATE TRIGGER
    # ========================================================================
    # Fires AFTER INSERT on journal_entry_lines to ensure the line is
    # committed before locking the account.
    # ========================================================================

    op.execute("""
        CREATE TRIGGER trg_auto_lock_account_on_first_transaction
        AFTER INSERT ON journal_entry_lines
        FOR EACH ROW
        EXECUTE FUNCTION auto_lock_account_on_first_transaction()
    """)


def downgrade() -> None:
    """
    Remove auto-lock trigger.

    WARNING: After downgrade, accounts will not automatically lock.
    Manual locking or application-level enforcement required.
    """

    op.execute("DROP TRIGGER IF EXISTS trg_auto_lock_account_on_first_transaction ON journal_entry_lines")
    op.execute("DROP FUNCTION IF EXISTS auto_lock_account_on_first_transaction()")
