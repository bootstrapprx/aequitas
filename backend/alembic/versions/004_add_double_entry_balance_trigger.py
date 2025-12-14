"""Add double-entry balance trigger for POSTED entries

Revision ID: 004
Revises: 003
Create Date: 2025-12-13

PHASE 1 - CRITICAL DATA INTEGRITY
Migration 2 of 10

PURPOSE:
Enforce the fundamental accounting equation at the database level:
  SUM(debits) = SUM(credits) for every POSTED journal entry

DRAFT entries are explicitly allowed to be unbalanced (work-in-progress).
Balance validation ONLY triggers when:
1. Journal entry status transitions to POSTED
2. Lines are modified on a POSTED entry (should be blocked by immutability trigger)

BREAKING: Yes - will fail if existing POSTED entries are unbalanced
REQUIRES: Data cleanup validation before applying

CANONICAL REFERENCE:
- Section 3.1: Double-Entry Validation
- Section 7.2: Journal Entry State Machine
- Section 8.1: Database-Level Invariants
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create trigger to validate double-entry balance for POSTED journal entries.

    TRIGGER LOGIC:
    - Fires AFTER INSERT/UPDATE/DELETE on journal_entry_lines
    - Only validates if parent journal entry status = 'POSTED'
    - Raises exception if SUM(debits) != SUM(credits)
    - DRAFT entries are NOT validated (can remain unbalanced)

    ENFORCEMENT SCOPE:
    - POSTED entries: MUST balance (enforced)
    - DRAFT entries: MAY be unbalanced (allowed)
    - VOID entries: Balance is frozen from when posted (immutability handles this)

    IMPORTANT: This migration will FAIL if existing POSTED entries are unbalanced.
    Run pre-migration validation script to identify violations.
    """

    # ========================================================================
    # CREATE TRIGGER FUNCTION: validate_journal_entry_balance()
    # ========================================================================
    # JUSTIFICATION: The fundamental accounting equation requires that
    # every transaction have equal debits and credits. This is enforced
    # at the database level to prevent data corruption from:
    # - Application bugs
    # - Direct SQL manipulation
    # - Migration errors
    # - Third-party integrations
    #
    # POSTED-ONLY VALIDATION: DRAFT entries are work-in-progress and may
    # be temporarily unbalanced. Validation only occurs when status is POSTED.
    #
    # ENFORCEMENT: PostgreSQL trigger function (cannot be bypassed)
    # ========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION validate_journal_entry_balance()
        RETURNS TRIGGER AS $$
        DECLARE
            v_entry_id UUID;
            v_entry_status VARCHAR;
            v_total_debits NUMERIC(15,2);
            v_total_credits NUMERIC(15,2);
            v_entry_number VARCHAR;
        BEGIN
            -- Determine which journal entry we're validating
            IF TG_OP = 'DELETE' THEN
                v_entry_id := OLD.journal_entry_id;
            ELSE
                v_entry_id := NEW.journal_entry_id;
            END IF;

            -- Get journal entry status and entry number
            SELECT status, entry_number
            INTO v_entry_status, v_entry_number
            FROM journal_entries
            WHERE id = v_entry_id;

            -- ONLY validate if status is POSTED
            -- DRAFT entries are allowed to be unbalanced (work-in-progress)
            IF v_entry_status = 'POSTED' THEN
                -- Calculate total debits and credits for this entry
                SELECT
                    COALESCE(SUM(debit_amount), 0),
                    COALESCE(SUM(credit_amount), 0)
                INTO v_total_debits, v_total_credits
                FROM journal_entry_lines
                WHERE journal_entry_id = v_entry_id;

                -- Check if balanced
                IF v_total_debits != v_total_credits THEN
                    RAISE EXCEPTION
                        'Journal entry % (id: %) does not balance: debits = %, credits = %. POSTED entries must have equal debits and credits.',
                        v_entry_number,
                        v_entry_id,
                        v_total_debits,
                        v_total_credits
                    USING HINT = 'Verify all journal entry lines are correct. Debits must equal credits for posted entries.';
                END IF;
            END IF;

            -- If DRAFT or balanced POSTED entry, allow operation
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # ========================================================================
    # CREATE TRIGGERS on journal_entry_lines
    # ========================================================================
    # Triggers fire AFTER modifications to catch all balance changes
    # ========================================================================

    op.execute("""
        CREATE TRIGGER trg_validate_balance_after_insert
        AFTER INSERT ON journal_entry_lines
        FOR EACH ROW
        EXECUTE FUNCTION validate_journal_entry_balance()
    """)

    op.execute("""
        CREATE TRIGGER trg_validate_balance_after_update
        AFTER UPDATE ON journal_entry_lines
        FOR EACH ROW
        EXECUTE FUNCTION validate_journal_entry_balance()
    """)

    op.execute("""
        CREATE TRIGGER trg_validate_balance_after_delete
        AFTER DELETE ON journal_entry_lines
        FOR EACH ROW
        EXECUTE FUNCTION validate_journal_entry_balance()
    """)

    # ========================================================================
    # CREATE TRIGGER on journal_entries (status change validation)
    # ========================================================================
    # When journal entry status changes TO 'POSTED', validate balance
    # This catches the transition from DRAFT → POSTED
    # ========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION validate_balance_on_post()
        RETURNS TRIGGER AS $$
        DECLARE
            v_total_debits NUMERIC(15,2);
            v_total_credits NUMERIC(15,2);
        BEGIN
            -- Only validate when transitioning TO POSTED status
            IF NEW.status = 'POSTED' AND (OLD.status IS NULL OR OLD.status != 'POSTED') THEN
                -- Calculate total debits and credits
                SELECT
                    COALESCE(SUM(debit_amount), 0),
                    COALESCE(SUM(credit_amount), 0)
                INTO v_total_debits, v_total_credits
                FROM journal_entry_lines
                WHERE journal_entry_id = NEW.id;

                -- Require at least one line
                IF v_total_debits = 0 AND v_total_credits = 0 THEN
                    RAISE EXCEPTION
                        'Cannot post journal entry % (id: %) with no lines.',
                        NEW.entry_number,
                        NEW.id
                    USING HINT = 'Add journal entry lines before posting.';
                END IF;

                -- Require balance
                IF v_total_debits != v_total_credits THEN
                    RAISE EXCEPTION
                        'Cannot post unbalanced journal entry % (id: %): debits = %, credits = %.',
                        NEW.entry_number,
                        NEW.id,
                        v_total_debits,
                        v_total_credits
                    USING HINT = 'Adjust journal entry lines so debits equal credits before posting.';
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_validate_balance_on_status_change
        BEFORE UPDATE ON journal_entries
        FOR EACH ROW
        WHEN (NEW.status = 'POSTED')
        EXECUTE FUNCTION validate_balance_on_post()
    """)


def downgrade() -> None:
    """
    Remove double-entry balance validation triggers.

    WARNING: Downgrading removes critical data integrity protection.
    Only use for rollback during migration issues.
    After downgrade, unbalanced POSTED entries can be created.
    """

    # Drop triggers on journal_entries
    op.execute("DROP TRIGGER IF EXISTS trg_validate_balance_on_status_change ON journal_entries")
    op.execute("DROP FUNCTION IF EXISTS validate_balance_on_post()")

    # Drop triggers on journal_entry_lines
    op.execute("DROP TRIGGER IF EXISTS trg_validate_balance_after_delete ON journal_entry_lines")
    op.execute("DROP TRIGGER IF EXISTS trg_validate_balance_after_update ON journal_entry_lines")
    op.execute("DROP TRIGGER IF EXISTS trg_validate_balance_after_insert ON journal_entry_lines")
    op.execute("DROP FUNCTION IF EXISTS validate_journal_entry_balance()")
