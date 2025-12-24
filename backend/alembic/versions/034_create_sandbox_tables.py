"""Create Sandbox Schema Tables (Zone D)

Revision ID: 034
Revises: 033
Create Date: 2025-12-23

CANON ENFORCEMENT: Sandbox & Projections Initial Tables
Canonical References: Canon IV (Intelligence Boundaries), Step 4 (Extension Boundaries, Zone D)

PURPOSE:
Create initial sandbox tables for scenario modeling and financial projections.
These tables are physically isolated from accounting truth and fully discardable.

ZONE D TABLES CREATED:

1. sandbox.scenarios - Container for what-if scenarios
2. sandbox.projections - Revenue/expense/cashflow projections
3. sandbox.bindings - Relationships between projections

CRITICAL INVARIANTS:

G1 - Physical Isolation
  - All tables in 'sandbox' schema (not 'public')
  - NO foreign key constraints to truth tables
  - company_id is logical reference only (no FK enforcement)

G2 - No Automatic Promotion
  - Data exists only in sandbox
  - Promotion to reality requires explicit service-layer API
  - No triggers writing to truth tables

BREAKING: No - creates new isolated tables
REQUIRES: Migration 033 (sandbox schema exists)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '034'
down_revision = '033'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create initial sandbox tables for scenario modeling.
    """

    # =========================================================================
    # ZONE D TABLE 1: Scenarios (Container for simulations)
    # =========================================================================

    op.execute("""
    CREATE TABLE sandbox.scenarios (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

        -- Logical reference to company (NO FK CONSTRAINT)
        company_id UUID NOT NULL,
        -- CRITICAL: No FK to public.companies - this is intentional isolation

        -- Scenario metadata
        name VARCHAR NOT NULL,
        description TEXT,

        -- Status lifecycle
        status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
        -- DRAFT: Being built
        -- ACTIVE: Ready for analysis
        -- ARCHIVED: Historical reference

        -- Ownership
        created_by UUID NOT NULL,  -- User who created scenario (logical reference only)
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

        -- Archival
        archived_at TIMESTAMP,
        archived_by UUID,

        -- Constraint: status must be valid
        CONSTRAINT scenarios_status_check CHECK (status IN ('DRAFT', 'ACTIVE', 'ARCHIVED'))
    );
    """)

    # Add indexes for performance
    op.execute("CREATE INDEX idx_scenarios_company_id ON sandbox.scenarios(company_id);")
    op.execute("CREATE INDEX idx_scenarios_status ON sandbox.scenarios(status);")
    op.execute("CREATE INDEX idx_scenarios_created_by ON sandbox.scenarios(created_by);")

    # Add table comment
    op.execute("""
    COMMENT ON TABLE sandbox.scenarios IS
    'Canon IV (Zone D): Simulation container. Isolated from truth. company_id is logical reference only (NO FK). Fully discardable.';
    """)

    # =========================================================================
    # ZONE D TABLE 2: Projections (Financial forecasts)
    # =========================================================================

    op.execute("""
    CREATE TABLE sandbox.projections (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

        -- Parent scenario (FK within sandbox schema only)
        scenario_id UUID NOT NULL REFERENCES sandbox.scenarios(id) ON DELETE CASCADE,

        -- Projection type
        type VARCHAR(20) NOT NULL,
        -- REVENUE: Expected income
        -- EXPENSE: Expected costs
        -- CASHFLOW: Expected cash movement

        -- Projection details
        name VARCHAR NOT NULL,
        description TEXT,

        -- Financial amounts
        amount NUMERIC(15, 2) NOT NULL,
        currency VARCHAR(3) NOT NULL DEFAULT 'USD',

        -- Recurrence
        frequency VARCHAR(20),
        -- ONE_TIME, MONTHLY, QUARTERLY, ANNUALLY

        -- Time boundaries
        start_date DATE NOT NULL,
        end_date DATE,

        -- Flexible metadata (for custom attributes)
        metadata JSONB,

        -- Audit
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

        -- Constraints
        CONSTRAINT projections_type_check CHECK (type IN ('REVENUE', 'EXPENSE', 'CASHFLOW')),
        CONSTRAINT projections_frequency_check CHECK (frequency IS NULL OR frequency IN ('ONE_TIME', 'MONTHLY', 'QUARTERLY', 'ANNUALLY')),
        CONSTRAINT projections_amount_positive CHECK (amount > 0),
        CONSTRAINT projections_dates_valid CHECK (end_date IS NULL OR end_date >= start_date)
    );
    """)

    # Add indexes
    op.execute("CREATE INDEX idx_projections_scenario_id ON sandbox.projections(scenario_id);")
    op.execute("CREATE INDEX idx_projections_type ON sandbox.projections(type);")
    op.execute("CREATE INDEX idx_projections_start_date ON sandbox.projections(start_date);")

    # Add table comment
    op.execute("""
    COMMENT ON TABLE sandbox.projections IS
    'Canon IV (Zone D): Financial projections. Revenue/Expense/Cashflow forecasts. Never posted to ledger automatically.';
    """)

    # =========================================================================
    # ZONE D TABLE 3: Bindings (Projection relationships)
    # =========================================================================

    op.execute("""
    CREATE TABLE sandbox.bindings (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

        -- Parent scenario
        scenario_id UUID NOT NULL REFERENCES sandbox.scenarios(id) ON DELETE CASCADE,

        -- Source and target projections
        source_projection_id UUID NOT NULL REFERENCES sandbox.projections(id) ON DELETE CASCADE,
        target_projection_id UUID NOT NULL REFERENCES sandbox.projections(id) ON DELETE CASCADE,

        -- Binding rule
        rule_type VARCHAR(50) NOT NULL,
        -- DRIVES: Source drives target (e.g., revenue drives commission expense)
        -- OFFSETS: Source offsets target (e.g., revenue offsets cost of goods)
        -- CONSTRAINS: Source constrains target (e.g., budget caps spending)

        rule_description TEXT,

        -- Binding strength (0.00 - 1.00)
        -- Example: 0.15 = 15% commission on revenue
        coefficient NUMERIC(5, 4),

        -- Metadata
        metadata JSONB,

        -- Audit
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

        -- Constraints
        CONSTRAINT bindings_rule_type_check CHECK (rule_type IN ('DRIVES', 'OFFSETS', 'CONSTRAINS')),
        CONSTRAINT bindings_no_self_binding CHECK (source_projection_id != target_projection_id),
        CONSTRAINT bindings_coefficient_valid CHECK (coefficient IS NULL OR (coefficient >= 0 AND coefficient <= 1))
    );
    """)

    # Add indexes
    op.execute("CREATE INDEX idx_bindings_scenario_id ON sandbox.bindings(scenario_id);")
    op.execute("CREATE INDEX idx_bindings_source ON sandbox.bindings(source_projection_id);")
    op.execute("CREATE INDEX idx_bindings_target ON sandbox.bindings(target_projection_id);")

    # Add table comment
    op.execute("""
    COMMENT ON TABLE sandbox.bindings IS
    'Canon IV (Zone D): What-if bindings between projections. Defines relationships (revenue → commission). Simulation only, never creates real entries.';
    """)

    # =========================================================================
    # ZONE D SAFEGUARDS: Enforce Isolation
    # =========================================================================

    # Create trigger function to prevent accidental FK creation to truth tables
    op.execute("""
    CREATE OR REPLACE FUNCTION sandbox.prevent_truth_leakage()
    RETURNS event_trigger AS $$
    DECLARE
        obj record;
    BEGIN
        -- Check for foreign keys from sandbox schema to public schema
        FOR obj IN
            SELECT objid::regclass AS table_name,
                   objsubid AS constraint_oid
            FROM pg_event_trigger_ddl_commands()
            WHERE command_tag = 'ALTER TABLE'
        LOOP
            -- Check if any FK points to public schema from sandbox
            IF EXISTS (
                SELECT 1
                FROM pg_constraint c
                JOIN pg_namespace ns ON c.connamespace = ns.oid
                WHERE ns.nspname = 'sandbox'
                  AND c.contype = 'f'
                  AND c.confrelid::regnamespace::text = 'public'
            ) THEN
                RAISE EXCEPTION
                    'CANON VIOLATION (G1): Sandbox tables cannot have foreign keys to truth tables (public schema). This violates Zone D isolation.'
                USING HINT = 'Use logical references (UUID without FK constraint) instead.';
            END IF;
        END LOOP;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Note: Event triggers require superuser privileges
    # This is documented but not enforced at migration level
    # Uncomment in production with appropriate privileges:
    # op.execute("""
    # CREATE EVENT TRIGGER prevent_sandbox_truth_fk
    #     ON ddl_command_end
    #     WHEN TAG IN ('ALTER TABLE')
    #     EXECUTE FUNCTION sandbox.prevent_truth_leakage();
    # """)

    # Add schema-level documentation
    op.execute("""
    COMMENT ON SCHEMA sandbox IS
    'Canon IV (Zone D): Simulation & Future. CRITICAL RULES: (1) No FK to public schema, (2) Fully discardable, (3) No auto-promotion to truth. Tables created: scenarios, projections, bindings.';
    """)


def downgrade() -> None:
    """
    Remove sandbox tables.

    WARNING: This will delete all sandbox data. Only permitted in development.
    """

    # Drop event trigger if it exists
    # op.execute("DROP EVENT TRIGGER IF EXISTS prevent_sandbox_truth_fk;")
    op.execute("DROP FUNCTION IF EXISTS sandbox.prevent_truth_leakage();")

    # Drop tables (CASCADE will handle dependencies)
    op.execute("DROP TABLE IF EXISTS sandbox.bindings CASCADE;")
    op.execute("DROP TABLE IF EXISTS sandbox.projections CASCADE;")
    op.execute("DROP TABLE IF EXISTS sandbox.scenarios CASCADE;")

    # Restore original schema comment
    op.execute("""
    COMMENT ON SCHEMA sandbox IS
    'Canon IV (Zone D): Simulation & Future. Physically isolated from truth core. No FK to accounting tables. Fully discardable.';
    """)
