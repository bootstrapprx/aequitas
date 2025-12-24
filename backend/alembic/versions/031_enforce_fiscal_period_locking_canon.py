"""Enforce FiscalPeriod Locking Canon (Invariants E1, E2, E3)

Revision ID: 031
Revises: 030
Create Date: 2025-12-23

CANON ENFORCEMENT: FiscalPeriod (Time Discipline)
Canonical References: Canon III (Time)

PURPOSE:
FiscalPeriod enforces time discipline across the ledger.
Closed periods are immutable. Overlapping periods are forbidden.

INVARIANTS ENFORCED:

E1 - Close Is Final
  Rule: CLOSED/LOCKED periods are immutable
  Enforcement: Trigger blocking UPDATE on CLOSED/LOCKED rows
  Rationale: Period closing is an audit milestone

E2 - No Deletion After Posting
  Rule: If any JournalEntry exists, deletion is forbidden
  Enforcement: FK RESTRICT (prevents CASCADE deletion)
  Note: Already enforced by FK, hardened here

E3 - No Overlaps
  Rule: Periods for same company may not overlap
  Enforcement: EXCLUDE constraint on date ranges
  Requires: PostgreSQL BTREE_GIST extension

BREAKING: Yes - prevents UPDATE of closed periods, adds overlap constraint
REQUIRES: fiscal_periods table, PostgreSQL 12+
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '031'
down_revision = '030'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Enforce FiscalPeriod time discipline constraints.
    """

    # =========================================================================
    # PREREQUISITE: Enable BTREE_GIST extension for EXCLUDE constraint
    # =========================================================================

    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")

    # =========================================================================
    # INVARIANT E1: Close Is Final (No UPDATE on CLOSED/LOCKED)
    # =========================================================================

    # Create trigger function to prevent modification of closed periods
    op.execute("""
    CREATE OR REPLACE FUNCTION enforce_fiscal_period_immutability()
    RETURNS TRIGGER AS $$
    BEGIN
        -- Block UPDATE of CLOSED or LOCKED periods
        IF TG_OP = 'UPDATE' AND (OLD.status = 'CLOSED' OR OLD.status = 'LOCKED') THEN
            -- Only allow status transition CLOSED → LOCKED
            -- All other fields are immutable once CLOSED
            IF OLD.status = 'CLOSED' AND NEW.status = 'LOCKED' THEN
                -- Allow CLOSED → LOCKED transition
                -- Ensure no other fields changed
                IF (OLD.period_type IS DISTINCT FROM NEW.period_type OR
                    OLD.period_number IS DISTINCT FROM NEW.period_number OR
                    OLD.start_date IS DISTINCT FROM NEW.start_date OR
                    OLD.end_date IS DISTINCT FROM NEW.end_date OR
                    OLD.closed_at IS DISTINCT FROM NEW.closed_at OR
                    OLD.closed_by IS DISTINCT FROM NEW.closed_by) THEN

                    RAISE EXCEPTION
                        'CANON VIOLATION (E1): Cannot UPDATE closed fiscal period (%). Only status transition CLOSED → LOCKED allowed.',
                        OLD.period_number
                    USING ERRCODE = 'integrity_constraint_violation',
                          HINT = 'Closed periods are immutable. Create adjusting entries before closing.';
                END IF;

                -- Allow status change
                RETURN NEW;
            END IF;

            -- Block all other updates to CLOSED or LOCKED periods
            RAISE EXCEPTION
                'CANON VIOLATION (E1): Cannot UPDATE % fiscal period (%). Period is immutable.',
                OLD.status, OLD.period_number
            USING ERRCODE = 'integrity_constraint_violation',
                  HINT = 'Closed periods cannot be modified. Reopen period (if allowed by policy) before making changes.';
        END IF;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Attach trigger to fiscal_periods table
    op.execute("""
    CREATE TRIGGER trigger_enforce_fiscal_period_immutability
        BEFORE UPDATE ON fiscal_periods
        FOR EACH ROW
        EXECUTE FUNCTION enforce_fiscal_period_immutability();
    """)

    # =========================================================================
    # INVARIANT E2: No Deletion After Posting (FK Hardening)
    # =========================================================================

    # Ensure FK from journal_entries to fiscal_periods is RESTRICT
    op.execute("""
    DO $$
    BEGIN
        -- Drop existing FK constraint if exists
        IF EXISTS (
            SELECT 1
            FROM information_schema.table_constraints
            WHERE constraint_name = 'journal_entries_fiscal_period_id_fkey'
              AND table_name = 'journal_entries'
        ) THEN
            ALTER TABLE journal_entries
                DROP CONSTRAINT journal_entries_fiscal_period_id_fkey;

            RAISE NOTICE 'Dropped existing FK constraint journal_entries_fiscal_period_id_fkey';
        END IF;

        -- Add new FK constraint with RESTRICT
        ALTER TABLE journal_entries
            ADD CONSTRAINT journal_entries_fiscal_period_id_fkey
            FOREIGN KEY (fiscal_period_id)
            REFERENCES fiscal_periods(id)
            ON DELETE RESTRICT
            ON UPDATE CASCADE;

        RAISE NOTICE 'CANON E2 ENFORCED: fiscal_period_id FK now uses ON DELETE RESTRICT';
    END $$;
    """)

    # Create additional trigger for better error messaging
    op.execute("""
    CREATE OR REPLACE FUNCTION prevent_deletion_of_used_periods()
    RETURNS TRIGGER AS $$
    DECLARE
        entry_count INTEGER;
    BEGIN
        -- Check if period has journal entries
        SELECT COUNT(*) INTO entry_count
        FROM journal_entries
        WHERE fiscal_period_id = OLD.id;

        IF entry_count > 0 THEN
            RAISE EXCEPTION
                'CANON VIOLATION (E2): Cannot delete fiscal period (%). Period has % journal entries.',
                OLD.period_number, entry_count
            USING ERRCODE = 'foreign_key_violation',
                  HINT = 'Periods with posted entries cannot be deleted.';
        END IF;

        RETURN OLD;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Attach trigger to fiscal_periods table
    op.execute("""
    CREATE TRIGGER trigger_prevent_deletion_of_used_periods
        BEFORE DELETE ON fiscal_periods
        FOR EACH ROW
        EXECUTE FUNCTION prevent_deletion_of_used_periods();
    """)

    # =========================================================================
    # INVARIANT E3: No Overlaps (EXCLUDE Constraint)
    # =========================================================================

    # Add EXCLUDE constraint to prevent overlapping date ranges for same company
    # Uses daterange type and overlaps operator (&&)
    op.execute("""
    ALTER TABLE fiscal_periods
        ADD CONSTRAINT fiscal_periods_no_overlap_per_company
        EXCLUDE USING gist (
            company_id WITH =,
            daterange(start_date, end_date, '[]') WITH &&
        );
    """)

    # =========================================================================
    # DOCUMENTATION
    # =========================================================================

    # Add table-level comment
    op.execute("""
    COMMENT ON TABLE fiscal_periods IS
    'Canon III: Time Discipline. Close is final (E1). No deletion after posting (E2). No overlaps (E3).';
    """)

    op.execute("""
    COMMENT ON COLUMN fiscal_periods.status IS
    'Period status. State machine: OPEN → CLOSED → LOCKED. CLOSED/LOCKED periods are immutable (E1).';
    """)

    op.execute("""
    COMMENT ON CONSTRAINT fiscal_periods_no_overlap_per_company ON fiscal_periods IS
    'Canon E3: Prevents overlapping fiscal periods for same company. Enforces unambiguous time boundaries.';
    """)


def downgrade() -> None:
    """
    Remove FiscalPeriod constraint enforcement.

    WARNING: Downgrading removes canon enforcement. Only permitted in development.
    """

    # Drop EXCLUDE constraint
    op.execute("ALTER TABLE fiscal_periods DROP CONSTRAINT IF EXISTS fiscal_periods_no_overlap_per_company;")

    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trigger_enforce_fiscal_period_immutability ON fiscal_periods;")
    op.execute("DROP TRIGGER IF EXISTS trigger_prevent_deletion_of_used_periods ON fiscal_periods;")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS enforce_fiscal_period_immutability();")
    op.execute("DROP FUNCTION IF EXISTS prevent_deletion_of_used_periods();")

    # Restore FK to CASCADE (if that was original)
    op.execute("""
    ALTER TABLE journal_entries
        DROP CONSTRAINT IF EXISTS journal_entries_fiscal_period_id_fkey;
    """)

    op.execute("""
    ALTER TABLE journal_entries
        ADD CONSTRAINT journal_entries_fiscal_period_id_fkey
        FOREIGN KEY (fiscal_period_id)
        REFERENCES fiscal_periods(id)
        ON DELETE CASCADE;
    """)

    # Remove comments
    op.execute("COMMENT ON TABLE fiscal_periods IS NULL;")
    op.execute("COMMENT ON COLUMN fiscal_periods.status IS NULL;")
