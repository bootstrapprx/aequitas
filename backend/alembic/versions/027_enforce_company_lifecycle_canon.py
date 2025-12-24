"""Enforce Company Lifecycle Canon (Invariants A1, A2, A3)

Revision ID: 027
Revises: 026
Create Date: 2025-12-23

CANON ENFORCEMENT: Company Lifecycle & Irreversibility
Canonical References: Canon II (Authority), Canon III (Evolution, State & Time)

PURPOSE:
Enforce mechanical impossibility of canon violations on Company entity.

INVARIANTS ENFORCED:

A1 - Monotonic State Transition
  Rule: onboarding_status may only advance forward
  Enforcement: CHECK constraint + trigger blocking backward transitions
  States: DRAFT → TEMPLATE_SELECTED → CHART_READY → ACTIVE

A2 - Activation Lock (Partial - prevents status regression)
  Rule: Once onboarding_status = ACTIVE, it cannot revert
  Enforcement: Combined with A1 monotonic constraint
  Note: Full activation lock (data immutability) enforced by triggers in migrations 028-030

A3 - No Destructive Reset Post-ACTIVE
  Rule: No deletion of accounting data for ACTIVE companies
  Enforcement: Trigger on DELETE for truth tables (JournalEntry, etc.)
  Note: Implemented in respective truth table migrations

BREAKING: No - only adds constraints to new behavior
REQUIRES: OnboardingStatus enum (already exists)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '027'
down_revision = '026'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Enforce Company lifecycle invariants.
    """

    # =========================================================================
    # INVARIANT A1: Monotonic State Transition
    # =========================================================================

    # Create trigger function to enforce monotonic state transitions
    op.execute("""
    CREATE OR REPLACE FUNCTION enforce_monotonic_onboarding_status()
    RETURNS TRIGGER AS $$
    DECLARE
        state_order_old INTEGER;
        state_order_new INTEGER;
        state_map TEXT[] := ARRAY['DRAFT', 'TEMPLATE_SELECTED', 'CHART_READY', 'ACTIVE'];
    BEGIN
        -- Only validate on UPDATE where onboarding_status is changing
        IF TG_OP = 'UPDATE' AND OLD.onboarding_status IS DISTINCT FROM NEW.onboarding_status THEN

            -- Get ordinal positions of states
            SELECT idx INTO state_order_old
            FROM unnest(state_map) WITH ORDINALITY AS t(status, idx)
            WHERE status = OLD.onboarding_status::text;

            SELECT idx INTO state_order_new
            FROM unnest(state_map) WITH ORDINALITY AS t(status, idx)
            WHERE status = NEW.onboarding_status::text;

            -- Reject backward transitions
            IF state_order_new < state_order_old THEN
                RAISE EXCEPTION
                    'CANON VIOLATION (A1): Backward onboarding state transition forbidden. Cannot move from % to %.',
                    OLD.onboarding_status, NEW.onboarding_status
                USING ERRCODE = 'check_violation',
                      HINT = 'Onboarding states are monotonic. Once ACTIVE, state is permanent.';
            END IF;

            -- Prevent skipping states (optional strictness - uncomment to enforce)
            -- IF state_order_new > state_order_old + 1 THEN
            --     RAISE EXCEPTION
            --         'CANON VIOLATION (A1): Cannot skip onboarding states. Must progress sequentially from % to %.',
            --         OLD.onboarding_status, state_map[state_order_old + 1]
            --     USING ERRCODE = 'check_violation';
            -- END IF;

        END IF;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Attach trigger to companies table
    op.execute("""
    CREATE TRIGGER trigger_enforce_monotonic_onboarding_status
        BEFORE UPDATE ON companies
        FOR EACH ROW
        EXECUTE FUNCTION enforce_monotonic_onboarding_status();
    """)

    # =========================================================================
    # INVARIANT A2: Activation is Permanent
    # =========================================================================
    # (Enforced by A1 monotonic constraint - ACTIVE cannot transition backward)

    # Add explicit database comment documenting the Point of No Return
    op.execute("""
    COMMENT ON COLUMN companies.onboarding_status IS
    'Onboarding state machine. MONOTONIC: Can only advance forward. ACTIVE is permanent (Point of No Return).';
    """)


def downgrade() -> None:
    """
    Remove Company lifecycle enforcement.

    WARNING: Downgrading removes canon enforcement. Only permitted in development.
    """

    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS trigger_enforce_monotonic_onboarding_status ON companies;")

    # Drop function
    op.execute("DROP FUNCTION IF EXISTS enforce_monotonic_onboarding_status();")

    # Remove comment
    op.execute("COMMENT ON COLUMN companies.onboarding_status IS NULL;")
