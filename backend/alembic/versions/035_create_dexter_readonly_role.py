"""Create Dexter Read-Only Role (Canon IV: Intelligence Boundary)

Revision ID: 035
Revises: 034
Create Date: 2025-12-23

CANON ENFORCEMENT: Intelligence Layer Security
Canonical References: Canon IV (Intelligence Boundaries), Step 4 (Zone C)

PURPOSE:
Define PostgreSQL role for Dexter (AI intelligence layer) with read-only access.
Dexter can observe truth but never mutate it.

INVARIANT H1 - No Write Access
  Rule: Dexter code path cannot write to truth tables
  Enforcement: Read-only database role + connection-level restrictions

ROLE DEFINITION:

dexter_readonly:
  - SELECT on all truth tables (public schema)
  - SELECT on master_account_intelligence (Zone C)
  - NO INSERT / UPDATE / DELETE on truth
  - NO access to sandbox (Zone D is for user experimentation only)

BREAKING: No - creates new role (no existing usage)
REQUIRES: PostgreSQL role creation privileges

NOTE: This migration defines the role structure.
      Runtime connection pooling and role assignment are service-layer concerns.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '035'
down_revision = '034'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create read-only database role for Dexter intelligence layer.
    """

    # =========================================================================
    # ROLE CREATION: dexter_readonly
    # =========================================================================

    # Create role (if not exists)
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'dexter_readonly') THEN
            CREATE ROLE dexter_readonly WITH
                NOLOGIN
                NOSUPERUSER
                NOCREATEDB
                NOCREATEROLE
                NOINHERIT
                NOREPLICATION;

            RAISE NOTICE 'Created role: dexter_readonly';
        ELSE
            RAISE NOTICE 'Role dexter_readonly already exists, skipping creation';
        END IF;
    END $$;
    """)

    # Add role comment
    op.execute("""
    COMMENT ON ROLE dexter_readonly IS
    'Canon IV (Zone C): Read-only role for Dexter AI intelligence layer. SELECT-only access to truth tables. No write access.';
    """)

    # =========================================================================
    # GRANT PERMISSIONS: Truth Tables (Zone A - Read-Only)
    # =========================================================================

    # Grant SELECT on all current tables in public schema
    op.execute("GRANT USAGE ON SCHEMA public TO dexter_readonly;")

    # Truth Core Tables (Zone A)
    truth_tables = [
        'companies',
        'company_accounts',
        'master_accounts',
        'journal_entries',
        'journal_entry_lines',
        'fiscal_periods',
        'account_balances',
    ]

    for table in truth_tables:
        op.execute(f"GRANT SELECT ON TABLE {table} TO dexter_readonly;")

    # Supporting Tables (Read-Only Access)
    supporting_tables = [
        'users',
        'user_companies',
        'chart_templates',
        'chart_template_accounts',
        'company_template_usage',
    ]

    for table in supporting_tables:
        op.execute(f"GRANT SELECT ON TABLE {table} TO dexter_readonly;")

    # =========================================================================
    # GRANT PERMISSIONS: Intelligence Layer (Zone C - Read-Only)
    # =========================================================================

    # Intelligence tables (Dexter can read its own advisory metadata)
    op.execute("GRANT SELECT ON TABLE master_account_intelligence TO dexter_readonly;")

    # =========================================================================
    # EXPLICIT DENIALS: What Dexter CANNOT Do
    # =========================================================================

    # Explicitly document (PostgreSQL defaults to no access, but make it explicit)
    # No INSERT, UPDATE, DELETE on truth tables
    # No access to sandbox schema (Zone D)

    # Document denial in schema comment
    op.execute("""
    COMMENT ON SCHEMA sandbox IS
    'Canon IV (Zone D): Simulation & Future. NO ACCESS for dexter_readonly role. Sandbox is for user experimentation only.';
    """)

    # =========================================================================
    # FUTURE DEFAULT PRIVILEGES (for new tables)
    # =========================================================================

    # Ensure new tables in public schema are automatically readable by dexter_readonly
    op.execute("""
    ALTER DEFAULT PRIVILEGES IN SCHEMA public
        GRANT SELECT ON TABLES TO dexter_readonly;
    """)

    # =========================================================================
    # USAGE DOCUMENTATION
    # =========================================================================

    # Add database-level comment documenting Dexter role usage
    op.execute("""
    COMMENT ON DATABASE postgres IS
    'Aequitas Accounting System. Canon-enforced invariants. Dexter AI uses dexter_readonly role (read-only access to truth).';
    """)

    # Log successful creation
    op.execute("""
    DO $$
    BEGIN
        RAISE NOTICE '========================================';
        RAISE NOTICE 'CANON IV ENFORCEMENT: Dexter Read-Only Role Created';
        RAISE NOTICE '========================================';
        RAISE NOTICE 'Role: dexter_readonly';
        RAISE NOTICE 'Permissions: SELECT on truth tables (Zone A)';
        RAISE NOTICE 'Restrictions: NO INSERT/UPDATE/DELETE';
        RAISE NOTICE 'Sandbox Access: DENIED (Zone D isolation)';
        RAISE NOTICE '';
        RAISE NOTICE 'SERVICE-LAYER INTEGRATION REQUIRED:';
        RAISE NOTICE '1. Configure separate DB connection pool for Dexter';
        RAISE NOTICE '2. Use dexter_readonly role for Dexter connections';
        RAISE NOTICE '3. Never use admin/write credentials in Dexter code paths';
        RAISE NOTICE '========================================';
    END $$;
    """)


def downgrade() -> None:
    """
    Remove Dexter read-only role.

    WARNING: This removes security isolation. Only permitted in development.
    """

    # Revoke all privileges
    op.execute("REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM dexter_readonly;")
    op.execute("REVOKE USAGE ON SCHEMA public FROM dexter_readonly;")

    # Drop default privileges
    op.execute("""
    ALTER DEFAULT PRIVILEGES IN SCHEMA public
        REVOKE SELECT ON TABLES FROM dexter_readonly;
    """)

    # Drop role
    op.execute("DROP ROLE IF EXISTS dexter_readonly;")

    # Remove comments
    op.execute("COMMENT ON DATABASE postgres IS NULL;")
    op.execute("""
    COMMENT ON SCHEMA sandbox IS
    'Canon IV (Zone D): Simulation & Future. Physically isolated from truth core. No FK to accounting tables. Fully discardable.';
    """)
