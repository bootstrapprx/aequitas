"""Enforce JournalEntry & JournalEntryLine Append-Only Canon (Invariants D1, D2, D3, D4)

Revision ID: 030
Revises: 029
Create Date: 2025-12-23

CANON ENFORCEMENT: JournalEntry (Truth Records)
Canonical References: Canon I (Truth), Canon II (Authority), Canon III (Time)

PURPOSE:
JournalEntry and JournalEntryLine are the highest-integrity objects in the system.
They are the permanent, immutable record of all accounting transactions.

INVARIANTS ENFORCED:

D1 - Append-Only Ledger
  Rule: No UPDATE or DELETE on POSTED entries
  Enforcement: Trigger blocking mutations on POSTED entries
  Rationale: Audit trail integrity requires immutability

D2 - Balanced Entry
  Rule: Sum(debits) = Sum(credits)
  Enforcement: Service-layer validation (documented here)
  Note: DB trigger exists (migration 004) but service layer is primary

D3 - Period Locking
  Rule: Cannot post to CLOSED or LOCKED periods
  Enforcement: Service-layer validation (documented here)
  Note: DB can add secondary check via FK + period status

D4 - Atomicity
  Rule: JournalEntry and lines persist together or not at all
  Enforcement: Database transactional integrity (implicit)
  Note: Documented for completeness

BREAKING: Yes - prevents UPDATE/DELETE of posted entries
REQUIRES: journal_entries table with status column
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '030'
down_revision = '029'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Enforce JournalEntry and JournalEntryLine immutability.
    """

    # =========================================================================
    # INVARIANT D1: Append-Only Ledger (No UPDATE/DELETE on POSTED)
    # =========================================================================

    # Create trigger function for journal_entries
    op.execute("""
    CREATE OR REPLACE FUNCTION enforce_journal_entry_immutability()
    RETURNS TRIGGER AS $$
    BEGIN
        -- Block DELETE of POSTED entries
        IF TG_OP = 'DELETE' THEN
            IF OLD.status = 'POSTED' THEN
                RAISE EXCEPTION
                    'CANON VIOLATION (D1): Cannot DELETE posted journal entry (%). Use VOID instead.',
                    OLD.entry_number
                USING ERRCODE = 'integrity_constraint_violation',
                      HINT = 'Posted entries are immutable. Create a reversing entry to correct.';
            END IF;
            -- Allow DELETE of DRAFT or VOID entries
            RETURN OLD;
        END IF;

        -- Block UPDATE of critical fields on POSTED entries
        IF TG_OP = 'UPDATE' AND OLD.status = 'POSTED' THEN
            -- Only allow status transition POSTED → VOID (and related void fields)
            -- All other fields are immutable
            IF (OLD.entry_number IS DISTINCT FROM NEW.entry_number OR
                OLD.entry_date IS DISTINCT FROM NEW.entry_date OR
                OLD.description IS DISTINCT FROM NEW.description OR
                OLD.reference IS DISTINCT FROM NEW.reference OR
                OLD.entry_type IS DISTINCT FROM NEW.entry_type OR
                OLD.fiscal_period_id IS DISTINCT FROM NEW.fiscal_period_id OR
                OLD.company_id IS DISTINCT FROM NEW.company_id OR
                OLD.created_by IS DISTINCT FROM NEW.created_by OR
                OLD.created_at IS DISTINCT FROM NEW.created_at OR
                OLD.posted_at IS DISTINCT FROM NEW.posted_at OR
                OLD.posted_by IS DISTINCT FROM NEW.posted_by) THEN

                RAISE EXCEPTION
                    'CANON VIOLATION (D1): Cannot UPDATE posted journal entry (%). Entry is immutable.',
                    OLD.entry_number
                USING ERRCODE = 'integrity_constraint_violation',
                      HINT = 'Only status transition POSTED → VOID is allowed. All other fields are immutable.';
            END IF;

            -- Allow status transition to VOID (with void metadata updates)
            IF NEW.status = 'VOID' THEN
                RETURN NEW;  -- Allow void transition
            END IF;

            -- Block any other status change
            IF OLD.status IS DISTINCT FROM NEW.status THEN
                RAISE EXCEPTION
                    'CANON VIOLATION (D1): Invalid status transition from POSTED to % for entry %.',
                    NEW.status, OLD.entry_number
                USING ERRCODE = 'integrity_constraint_violation',
                      HINT = 'Only POSTED → VOID transition is allowed.';
            END IF;
        END IF;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Attach trigger to journal_entries table
    op.execute("""
    CREATE TRIGGER trigger_enforce_journal_entry_immutability
        BEFORE UPDATE OR DELETE ON journal_entries
        FOR EACH ROW
        EXECUTE FUNCTION enforce_journal_entry_immutability();
    """)

    # Create trigger function for journal_entry_lines
    op.execute("""
    CREATE OR REPLACE FUNCTION enforce_journal_entry_line_immutability()
    RETURNS TRIGGER AS $$
    DECLARE
        entry_status TEXT;
    BEGIN
        -- Get parent journal entry status
        SELECT status INTO entry_status
        FROM journal_entries
        WHERE id = COALESCE(NEW.journal_entry_id, OLD.journal_entry_id);

        -- Block UPDATE/DELETE of lines if parent entry is POSTED
        IF entry_status = 'POSTED' THEN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION
                    'CANON VIOLATION (D1): Cannot DELETE line from posted journal entry. Parent entry ID: %.',
                    OLD.journal_entry_id
                USING ERRCODE = 'integrity_constraint_violation',
                      HINT = 'Lines of posted entries are immutable. Create a reversing entry instead.';
            END IF;

            IF TG_OP = 'UPDATE' THEN
                RAISE EXCEPTION
                    'CANON VIOLATION (D1): Cannot UPDATE line from posted journal entry. Parent entry ID: %.',
                    OLD.journal_entry_id
                USING ERRCODE = 'integrity_constraint_violation',
                      HINT = 'Lines of posted entries are immutable. Create a reversing entry instead.';
            END IF;
        END IF;

        -- Allow mutations if entry is DRAFT or VOID
        RETURN COALESCE(NEW, OLD);
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Attach trigger to journal_entry_lines table
    op.execute("""
    CREATE TRIGGER trigger_enforce_journal_entry_line_immutability
        BEFORE UPDATE OR DELETE ON journal_entry_lines
        FOR EACH ROW
        EXECUTE FUNCTION enforce_journal_entry_line_immutability();
    """)

    # =========================================================================
    # INVARIANT D2, D3, D4: Documentation (Service-Layer Enforcement)
    # =========================================================================

    # Add table-level comments documenting all invariants
    op.execute("""
    COMMENT ON TABLE journal_entries IS
    'Canon I, II, III: Truth-bearing record. Append-only (D1). Balanced by service layer (D2). Period-locked (D3). Atomic (D4).';
    """)

    op.execute("""
    COMMENT ON TABLE journal_entry_lines IS
    'Canon I: Atomic accounting fact. Immutable when parent entry is POSTED. Debits = Credits enforced by service layer.';
    """)

    op.execute("""
    COMMENT ON COLUMN journal_entries.status IS
    'Entry status. State machine: DRAFT → POSTED → VOID. POSTED entries are immutable (D1). Only POSTED → VOID transition allowed.';
    """)


def downgrade() -> None:
    """
    Remove JournalEntry immutability enforcement.

    WARNING: Downgrading removes canon enforcement. Only permitted in development.
    """

    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trigger_enforce_journal_entry_immutability ON journal_entries;")
    op.execute("DROP TRIGGER IF EXISTS trigger_enforce_journal_entry_line_immutability ON journal_entry_lines;")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS enforce_journal_entry_immutability();")
    op.execute("DROP FUNCTION IF EXISTS enforce_journal_entry_line_immutability();")

    # Remove comments
    op.execute("COMMENT ON TABLE journal_entries IS NULL;")
    op.execute("COMMENT ON TABLE journal_entry_lines IS NULL;")
    op.execute("COMMENT ON COLUMN journal_entries.status IS NULL;")
