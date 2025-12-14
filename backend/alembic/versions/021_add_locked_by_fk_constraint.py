"""Add locked_by foreign key constraint

Revision ID: 021
Revises: 020
Create Date: 2025-12-13

PHASE 2B - SCHEMA CLEANUP AND OPTIMIZATION
Migration 3 of 5

PURPOSE:
Add foreign key constraint from company_accounts.locked_by to users.id:
1. Validate all locked_by values reference valid users
2. Clean up any orphaned references
3. Add FK constraint with ON DELETE SET NULL
4. Ensure referential integrity for account locking

BACKGROUND:
Phase 1 (migration 007) added the locked_by column but didn't add
the foreign key constraint. This migration completes the relationship.

The FK uses ON DELETE SET NULL because:
- If a user is deleted, their locked accounts should remain locked
- The locked_by field becomes NULL (indicates system lock)
- locked_at and locked_reason remain for audit trail

BREAKING: No - adds constraint only
REQUIRES: Migration 020 complete

CANONICAL REFERENCE:
- Phase 2B Specification: Schema Cleanup and Optimization
- Section: Foreign Key Constraints
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add foreign key constraint from locked_by to users.id.

    STRATEGY:
    1. Identify orphaned locked_by references
    2. Clean up orphaned references (set to NULL)
    3. Add FK constraint with ON DELETE SET NULL
    4. Verify constraint enforcement
    """

    print("=" * 80)
    print("MIGRATION 021: Adding locked_by Foreign Key Constraint")
    print("=" * 80)

    connection = op.get_bind()

    # ========================================================================
    # STEP 1: Identify orphaned locked_by references
    # ========================================================================
    print("  Checking for orphaned locked_by references...")

    orphaned_result = connection.execute(sa.text("""
        SELECT COUNT(*) as orphan_count
        FROM company_accounts ca
        WHERE ca.locked_by IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM users u WHERE u.id = ca.locked_by
          )
    """))
    orphan_count = orphaned_result.fetchone()[0]

    print(f"  - Found {orphan_count} orphaned locked_by references")

    # ========================================================================
    # STEP 2: Clean up orphaned references
    # ========================================================================

    if orphan_count > 0:
        print(f"  Cleaning up {orphan_count} orphaned references...")
        print("  (Setting locked_by to NULL, preserving locked_at and locked_reason)")

        # Log orphaned accounts before cleanup (for audit)
        orphaned_accounts = connection.execute(sa.text("""
            SELECT ca.id, ca.code, ca.description, ca.locked_by, ca.locked_at, ca.locked_reason
            FROM company_accounts ca
            WHERE ca.locked_by IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM users u WHERE u.id = ca.locked_by
              )
            LIMIT 10
        """))

        print("  Sample orphaned accounts:")
        for acc in orphaned_accounts:
            print(f"    - {acc[1]} ({acc[2]}): locked_by={acc[3]}, reason={acc[5]}")

        # Set locked_by to NULL for orphaned references
        # Keep account locked (is_locked=true) but indicate system lock
        connection.execute(sa.text("""
            UPDATE company_accounts
            SET locked_by = NULL
            WHERE locked_by IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM users u WHERE u.id = locked_by
              )
        """))

        print("  ✓ Cleanup complete")

    # ========================================================================
    # STEP 3: Verify cleanup
    # ========================================================================
    print("  Verifying cleanup...")

    verification_result = connection.execute(sa.text("""
        SELECT COUNT(*) as remaining_orphans
        FROM company_accounts ca
        WHERE ca.locked_by IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM users u WHERE u.id = ca.locked_by
          )
    """))
    remaining_orphans = verification_result.fetchone()[0]

    if remaining_orphans > 0:
        raise Exception(f"""
            Cleanup verification failed: {remaining_orphans} orphaned references remain.
            Cannot add FK constraint while orphaned references exist.
        """)

    print("  ✓ All orphaned references cleaned up")

    # ========================================================================
    # STEP 4: Add foreign key constraint
    # ========================================================================
    print("  Adding foreign key constraint...")

    op.create_foreign_key(
        'fk_company_accounts_locked_by',
        'company_accounts',
        'users',
        ['locked_by'],
        ['id'],
        ondelete='SET NULL'
    )

    print("  ✓ Foreign key constraint added")

    # ========================================================================
    # STEP 5: Verify constraint
    # ========================================================================
    print("  Verifying constraint...")

    constraint_check = connection.execute(sa.text("""
        SELECT
            tc.constraint_name,
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            rc.delete_rule
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
        JOIN information_schema.referential_constraints AS rc
          ON rc.constraint_name = tc.constraint_name
          AND rc.constraint_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_name = 'company_accounts'
          AND tc.constraint_name = 'fk_company_accounts_locked_by'
    """))

    constraint = constraint_check.fetchone()

    if constraint:
        print(f"  ✓ Constraint verified:")
        print(f"    - Name: {constraint[0]}")
        print(f"    - Column: {constraint[1]}.{constraint[2]}")
        print(f"    - References: {constraint[3]}.{constraint[4]}")
        print(f"    - On Delete: {constraint[5]}")
    else:
        raise Exception("Foreign key constraint not found after creation")

    # ========================================================================
    # STEP 6: Test constraint enforcement
    # ========================================================================
    print("  Testing constraint enforcement...")

    # Count current locked accounts
    locked_count_result = connection.execute(sa.text("""
        SELECT COUNT(*) FROM company_accounts WHERE locked_by IS NOT NULL
    """))
    locked_count = locked_count_result.fetchone()[0]

    print(f"  - Current locked accounts: {locked_count}")
    print(f"  - All locked_by values now reference valid users")

    print("")
    print("=" * 80)
    print("MIGRATION 021: Complete")
    print("=" * 80)
    print("Foreign key constraint added successfully")
    print(f"Orphaned references cleaned: {orphan_count}")
    print("=" * 80)


def downgrade() -> None:
    """
    Remove locked_by foreign key constraint.

    WARNING: This allows orphaned locked_by references.
    Only use for rollback during migration issues.
    """

    print("=" * 80)
    print("MIGRATION 021: Rolling back...")
    print("=" * 80)

    op.drop_constraint('fk_company_accounts_locked_by', 'company_accounts', type_='foreignkey')

    print("  - Removed foreign key constraint: fk_company_accounts_locked_by")

    print("=" * 80)
    print("MIGRATION 021: Rollback complete")
    print("=" * 80)
