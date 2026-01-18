"""Add kernel binding fields and align onboarding state trigger.

Revision ID: 036
Revises: 035
Create Date: 2025-12-29
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "036"
down_revision = "035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    kernel_layer_enum = sa.Enum("L0", "L1", "L2", name="kernellayer")
    kernel_layer_enum.create(op.get_bind(), checkfirst=True)

    op.add_column("companies", sa.Column("kernel_version", sa.String(length=10), nullable=True))
    op.add_column("companies", sa.Column("kernel_layer", sa.Enum("L0", "L1", "L2", name="kernellayer"), nullable=True))

    # Update onboarding status trigger to include CHART_FINALIZED
    op.execute("""
    CREATE OR REPLACE FUNCTION enforce_monotonic_onboarding_status()
    RETURNS TRIGGER AS $$
    DECLARE
        state_order_old INTEGER;
        state_order_new INTEGER;
        state_map TEXT[] := ARRAY['DRAFT', 'TEMPLATE_SELECTED', 'CHART_READY', 'CHART_FINALIZED', 'ACTIVE'];
    BEGIN
        IF TG_OP = 'UPDATE' AND OLD.onboarding_status IS DISTINCT FROM NEW.onboarding_status THEN
            SELECT idx INTO state_order_old
            FROM unnest(state_map) WITH ORDINALITY AS t(status, idx)
            WHERE status = OLD.onboarding_status::text;

            SELECT idx INTO state_order_new
            FROM unnest(state_map) WITH ORDINALITY AS t(status, idx)
            WHERE status = NEW.onboarding_status::text;

            IF state_order_new < state_order_old THEN
                RAISE EXCEPTION
                    'CANON VIOLATION (A1): Backward onboarding state transition forbidden. Cannot move from % to %.',
                    OLD.onboarding_status, NEW.onboarding_status
                USING ERRCODE = 'check_violation',
                      HINT = 'Onboarding states are monotonic. Once ACTIVE, state is permanent.';
            END IF;
        END IF;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    COMMENT ON COLUMN companies.onboarding_status IS
    'Onboarding state machine. MONOTONIC: DRAFT -> TEMPLATE_SELECTED -> CHART_READY -> CHART_FINALIZED -> ACTIVE. ACTIVE is permanent.';
    """)


def downgrade() -> None:
    op.drop_column("companies", "kernel_layer")
    op.drop_column("companies", "kernel_version")

    kernel_layer_enum = sa.Enum("L0", "L1", "L2", name="kernellayer")
    kernel_layer_enum.drop(op.get_bind(), checkfirst=True)

    # Revert onboarding status trigger to original state map
    op.execute("""
    CREATE OR REPLACE FUNCTION enforce_monotonic_onboarding_status()
    RETURNS TRIGGER AS $$
    DECLARE
        state_order_old INTEGER;
        state_order_new INTEGER;
        state_map TEXT[] := ARRAY['DRAFT', 'TEMPLATE_SELECTED', 'CHART_READY', 'ACTIVE'];
    BEGIN
        IF TG_OP = 'UPDATE' AND OLD.onboarding_status IS DISTINCT FROM NEW.onboarding_status THEN
            SELECT idx INTO state_order_old
            FROM unnest(state_map) WITH ORDINALITY AS t(status, idx)
            WHERE status = OLD.onboarding_status::text;

            SELECT idx INTO state_order_new
            FROM unnest(state_map) WITH ORDINALITY AS t(status, idx)
            WHERE status = NEW.onboarding_status::text;

            IF state_order_new < state_order_old THEN
                RAISE EXCEPTION
                    'CANON VIOLATION (A1): Backward onboarding state transition forbidden. Cannot move from % to %.',
                    OLD.onboarding_status, NEW.onboarding_status
                USING ERRCODE = 'check_violation',
                      HINT = 'Onboarding states are monotonic. Once ACTIVE, state is permanent.';
            END IF;
        END IF;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    COMMENT ON COLUMN companies.onboarding_status IS
    'Onboarding state machine. MONOTONIC: Can only advance forward. ACTIVE is permanent (Point of No Return).';
    """)
