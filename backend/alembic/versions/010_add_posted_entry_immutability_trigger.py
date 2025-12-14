"""Add posted journal entry immutability triggers

Revision ID: 010
Revises: 009
Create Date: 2025-12-13

PHASE 1 - CRITICAL DATA INTEGRITY
Migration 8 of 10

PURPOSE:
Enforce immutability of posted journal entries to maintain audit trail integrity.
Once a journal entry is posted, it becomes part of the permanent financial record
and cannot be modified or deleted. Corrections must be made via reversing entries.

IMMUTABILITY RULES (when status = 'POSTED'):
- Journal entry fields cannot be modified (except status → VOID)
- Journal entry lines cannot be modified
- Journal entry lines cannot be deleted
- Journal entry cannot be deleted
- Only allowed transition: POSTED → VOID (creates reversing entry)

BREAKING: No - trigger enforcement only
REQUIRES: None

CANONICAL REFERENCE:
- Section 7.2: Journal Entry State Machine
- Section 7: Audit Safety (Historical Immutability)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create triggers to prevent modification/deletion of POSTED journal entries.

    TRIGGERS CREATED:
    1. prevent_posted_entry_modification - Prevents UPDATE on POSTED entries
       (except status change to VOID)
    2. prevent_posted_entry_deletion - Prevents DELETE on POSTED entries
    3. prevent_posted_line_modification - Prevents UPDATE on lines of POSTED entries
    4. prevent_posted_line_deletion - Prevents DELETE on lines of POSTED entries

    ALLOWED OPERATIONS:
    - Voiding: status change from POSTED → VOID (creates reversing entry)
    - Reading: SELECT operations always allowed
    """

    # ========================================================================
    # TRIGGER 1: Prevent modification of posted journal entries
    # ========================================================================
    # JUSTIFICATION: Posted entries are permanent financial records.
    # Allowing edits would enable audit fraud and violate GAAP requirements.
    # ========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_posted_entry_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Only enforce if OLD status is POSTED
            IF OLD.status = 'POSTED' THEN
                -- Allow voiding (POSTED → VOID transition)
                IF NEW.status = 'VOID' AND OLD.status = 'POSTED' THEN
                    -- Voiding is allowed (application must create reversing entry)
                    RETURN NEW;
                END IF;

                -- Prevent any other modifications
                RAISE EXCEPTION
                    'Cannot modify posted journal entry % (%). Posted entries are immutable.',
                    OLD.entry_number,
                    OLD.id
                USING HINT = 'To correct this entry, create a reversing entry (void) and a new corrected entry.';
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_prevent_posted_entry_modification
        BEFORE UPDATE ON journal_entries
        FOR EACH ROW
        WHEN (OLD.status = 'POSTED')
        EXECUTE FUNCTION prevent_posted_entry_modification()
    """)

    # ========================================================================
    # TRIGGER 2: Prevent deletion of posted journal entries
    # ========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_posted_entry_deletion()
        RETURNS TRIGGER AS $$
        BEGIN
            IF OLD.status = 'POSTED' THEN
                RAISE EXCEPTION
                    'Cannot delete posted journal entry % (%). Posted entries are immutable.',
                    OLD.entry_number,
                    OLD.id
                USING HINT = 'To remove this entry from records, void it instead.';
            END IF;

            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_prevent_posted_entry_deletion
        BEFORE DELETE ON journal_entries
        FOR EACH ROW
        WHEN (OLD.status = 'POSTED')
        EXECUTE FUNCTION prevent_posted_entry_deletion()
    """)

    # ========================================================================
    # TRIGGER 3: Prevent modification of lines in posted journal entries
    # ========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_posted_line_modification()
        RETURNS TRIGGER AS $$
        DECLARE
            v_entry_status VARCHAR;
            v_entry_number VARCHAR;
        BEGIN
            -- Get parent journal entry status
            SELECT status, entry_number
            INTO v_entry_status, v_entry_number
            FROM journal_entries
            WHERE id = OLD.journal_entry_id;

            IF v_entry_status = 'POSTED' THEN
                RAISE EXCEPTION
                    'Cannot modify line in posted journal entry % (%). Posted entries are immutable.',
                    v_entry_number,
                    OLD.journal_entry_id
                USING HINT = 'Posted journal entry lines cannot be edited. Create a reversing entry instead.';
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_prevent_posted_line_modification
        BEFORE UPDATE ON journal_entry_lines
        FOR EACH ROW
        EXECUTE FUNCTION prevent_posted_line_modification()
    """)

    # ========================================================================
    # TRIGGER 4: Prevent deletion of lines in posted journal entries
    # ========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_posted_line_deletion()
        RETURNS TRIGGER AS $$
        DECLARE
            v_entry_status VARCHAR;
            v_entry_number VARCHAR;
        BEGIN
            -- Get parent journal entry status
            SELECT status, entry_number
            INTO v_entry_status, v_entry_number
            FROM journal_entries
            WHERE id = OLD.journal_entry_id;

            IF v_entry_status = 'POSTED' THEN
                RAISE EXCEPTION
                    'Cannot delete line from posted journal entry % (%). Posted entries are immutable.',
                    v_entry_number,
                    OLD.journal_entry_id
                USING HINT = 'Posted journal entry lines cannot be deleted. Create a reversing entry instead.';
            END IF;

            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_prevent_posted_line_deletion
        BEFORE DELETE ON journal_entry_lines
        FOR EACH ROW
        EXECUTE FUNCTION prevent_posted_line_deletion()
    """)


def downgrade() -> None:
    """
    Remove posted entry immutability triggers.

    WARNING: After downgrade, posted entries can be freely modified or deleted.
    Audit trail integrity is no longer guaranteed. Use only for emergency rollback.
    """

    # Drop triggers on journal_entry_lines
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_posted_line_deletion ON journal_entry_lines")
    op.execute("DROP FUNCTION IF EXISTS prevent_posted_line_deletion()")

    op.execute("DROP TRIGGER IF EXISTS trg_prevent_posted_line_modification ON journal_entry_lines")
    op.execute("DROP FUNCTION IF EXISTS prevent_posted_line_modification()")

    # Drop triggers on journal_entries
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_posted_entry_deletion ON journal_entries")
    op.execute("DROP FUNCTION IF EXISTS prevent_posted_entry_deletion()")

    op.execute("DROP TRIGGER IF EXISTS trg_prevent_posted_entry_modification ON journal_entries")
    op.execute("DROP FUNCTION IF EXISTS prevent_posted_entry_modification()")
