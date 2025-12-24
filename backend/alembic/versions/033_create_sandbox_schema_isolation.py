"""Create Sandbox Schema Isolation (Zone D)

Revision ID: 033
Revises: 032
Create Date: 2025-12-23

CANON ENFORCEMENT: Sandbox & Projections (Isolation)
Canonical References: Canon IV & III, Step 4 (Extension Boundaries, Zone D)

PURPOSE:
Physical isolation of simulation/forecast data from accounting truth.
Sandbox is truth-adjacent, never truth-bearing.

ZONE D REQUIREMENTS:

G1 - Physical Isolation
  Rule: Sandbox tables never FK into ledger tables
  Enforcement: Separate PostgreSQL schema
  Rationale: No accidental data leakage into truth

G2 - No Promotion Without Explicit Action
  Rule: Sandbox data cannot auto-create real objects
  Enforcement: Service-layer (explicit promotion APIs only)
  Rationale: Sandbox is for experimentation, not commitments

BREAKING: No - creates new schema (no existing dependencies)
REQUIRES: PostgreSQL 12+

NOTE: This migration creates the schema structure.
      Actual sandbox tables will be added when sandbox features are implemented.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '033'
down_revision = '032'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create sandbox schema for simulation and projection data.
    """

    # =========================================================================
    # ZONE D: Create Physically Isolated Sandbox Schema
    # =========================================================================

    # Create separate schema for sandbox data
    op.execute("CREATE SCHEMA IF NOT EXISTS sandbox;")

    # Add schema comment
    op.execute("""
    COMMENT ON SCHEMA sandbox IS
    'Canon IV (Zone D): Simulation & Future. Physically isolated from truth core. No FK to accounting tables. Fully discardable.';
    """)

    # =========================================================================
    # PLACEHOLDER: Future Sandbox Tables
    # =========================================================================

    # When sandbox features are implemented, add tables here:
    # - sandbox.scenarios
    # - sandbox.projections
    # - sandbox.forecasts
    # - sandbox.what_if_bindings
    # - sandbox.scenario_comparisons

    # CRITICAL RULES FOR FUTURE TABLES:
    # 1. All tables MUST be in 'sandbox' schema
    # 2. NO foreign keys to 'public' schema (truth tables)
    # 3. Data must be fully discardable (no CASCADE to truth)
    # 4. Promotion to real data requires explicit service-layer API

    # Add placeholder comment
    op.execute("""
    COMMENT ON SCHEMA sandbox IS
    'Canon IV (Zone D): Simulation & Future. Physically isolated from truth core. No FK to accounting tables. Fully discardable. PLACEHOLDER: Sandbox tables to be added when features are implemented.';
    """)


def downgrade() -> None:
    """
    Remove sandbox schema.

    WARNING: This will drop all sandbox data. Only permitted in development.
    """

    # Drop schema and all contained objects
    op.execute("DROP SCHEMA IF EXISTS sandbox CASCADE;")
