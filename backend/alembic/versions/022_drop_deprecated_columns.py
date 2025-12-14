"""Drop deprecated parent_code and master_account_code columns

Revision ID: 022
Revises: 021
Create Date: 2025-12-13

PHASE 2B - SCHEMA CLEANUP AND OPTIMIZATION
Migration 4 of 5

PURPOSE:
Remove deprecated string-based reference columns from company_accounts:
1. Drop parent_code (replaced by parent_id UUID FK in Phase 2A)
2. Drop master_account_code (replaced by mapped_master_account_id UUID FK in Phase 2A)
3. Verify all data successfully migrated before dropping
4. Clean up indexes on deprecated columns

BACKGROUND:
Phase 2A (migration 013) added parent_id and mapped_master_account_id
as proper UUID foreign keys, replacing the old string-based references.

Original columns:
- parent_code: String reference to parent account's code
- master_account_code: String reference to master account's code

Replacement columns:
- parent_id: UUID FK to company_accounts.id
- mapped_master_account_id: UUID FK to master_accounts.id

This migration completes the cleanup by removing the old columns.

BREAKING: Yes - removes columns (but they're deprecated)
REQUIRES: Migration 021 complete, Phase 2A migration complete

CANONICAL REFERENCE:
- Phase 2B Specification: Schema Cleanup and Optimization
- Section: Deprecate Legacy Columns
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '022'
down_revision = '021'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Drop deprecated parent_code and master_account_code columns.

    STRATEGY:
    1. Verify all data migrated to new UUID columns
    2. Log any unmigrated records (BLOCKER)
    3. Drop foreign key constraint on master_account_code
    4. Drop indexes on deprecated columns
    5. Drop columns
    6. Verify cleanup
    """

    print("=" * 80)
    print("MIGRATION 022: Dropping Deprecated Columns")
    print("=" * 80)

    connection = op.get_bind()

    # ========================================================================
    # STEP 1: Pre-drop validation
    # ========================================================================
    print("  Validating data migration before dropping columns...")

    # Check 1a: Unmigrated parent_code values
    unmigrated_parent_result = connection.execute(sa.text("""
        SELECT COUNT(*) as unmigrated_count
        FROM company_accounts
        WHERE parent_code IS NOT NULL
          AND parent_id IS NULL
    """))
    unmigrated_parent_count = unmigrated_parent_result.fetchone()[0]

    # Check 1b: Unmigrated master_account_code values
    unmigrated_master_result = connection.execute(sa.text("""
        SELECT COUNT(*) as unmigrated_count
        FROM company_accounts
        WHERE master_account_code IS NOT NULL
          AND mapped_master_account_id IS NULL
    """))
    unmigrated_master_count = unmigrated_master_result.fetchone()[0]

    print(f"  - Unmigrated parent_code values: {unmigrated_parent_count}")
    print(f"  - Unmigrated master_account_code values: {unmigrated_master_count}")

    # ========================================================================
    # STEP 2: BLOCKER check
    # ========================================================================

    if unmigrated_parent_count > 0:
        # Log details
        unmigrated_parents = connection.execute(sa.text("""
            SELECT id, code, description, parent_code
            FROM company_accounts
            WHERE parent_code IS NOT NULL
              AND parent_id IS NULL
            LIMIT 10
        """))

        print("")
        print("  ✗ BLOCKER: Unmigrated parent_code values detected")
        print("  Sample accounts:")
        for acc in unmigrated_parents:
            print(f"    - {acc[1]} ({acc[2]}): parent_code={acc[3]}")

        raise Exception(f"""
            Cannot drop parent_code: {unmigrated_parent_count} unmigrated values.

            Resolution:
            1. Run Phase 2A migration 013 to migrate parent_code -> parent_id
            2. Investigate why migration didn't capture these records
            3. Manually backfill parent_id for orphaned parent_code values
        """)

    if unmigrated_master_count > 0:
        # Log details
        unmigrated_masters = connection.execute(sa.text("""
            SELECT id, code, description, master_account_code
            FROM company_accounts
            WHERE master_account_code IS NOT NULL
              AND mapped_master_account_id IS NULL
            LIMIT 10
        """))

        print("")
        print("  ✗ BLOCKER: Unmigrated master_account_code values detected")
        print("  Sample accounts:")
        for acc in unmigrated_masters:
            print(f"    - {acc[1]} ({acc[2]}): master_account_code={acc[3]}")

        raise Exception(f"""
            Cannot drop master_account_code: {unmigrated_master_count} unmigrated values.

            Resolution:
            1. Run Phase 2A migration 013 to migrate master_account_code -> mapped_master_account_id
            2. Ensure master_accounts table is populated
            3. Manually backfill mapped_master_account_id for orphaned references
        """)

    print("  ✓ All data successfully migrated to UUID columns")

    # ========================================================================
    # STEP 3: Compare population statistics
    # ========================================================================
    print("  Comparing column population...")

    comparison_result = connection.execute(sa.text("""
        SELECT
            COUNT(*) as total_accounts,
            COUNT(*) FILTER (WHERE parent_code IS NOT NULL) as has_parent_code,
            COUNT(*) FILTER (WHERE parent_id IS NOT NULL) as has_parent_id,
            COUNT(*) FILTER (WHERE master_account_code IS NOT NULL) as has_master_code,
            COUNT(*) FILTER (WHERE mapped_master_account_id IS NOT NULL) as has_master_id
        FROM company_accounts
    """))
    stats = comparison_result.fetchone()

    print(f"  - Total accounts: {stats[0]}")
    print(f"  - parent_code populated: {stats[1]}")
    print(f"  - parent_id populated: {stats[2]}")
    print(f"  - master_account_code populated: {stats[3]}")
    print(f"  - mapped_master_account_id populated: {stats[4]}")

    # ========================================================================
    # STEP 4: Drop foreign key constraint on master_account_code
    # ========================================================================
    print("  Dropping foreign key constraint on master_account_code...")

    try:
        op.drop_constraint(
            'company_accounts_master_account_code_fkey',
            'company_accounts',
            type_='foreignkey'
        )
        print("  ✓ Dropped FK constraint: company_accounts_master_account_code_fkey")
    except Exception as e:
        print(f"  ℹ FK constraint may not exist or already dropped: {e}")

    # ========================================================================
    # STEP 5: Drop indexes on deprecated columns
    # ========================================================================
    print("  Dropping indexes on deprecated columns...")

    try:
        op.drop_index('ix_company_accounts_master_account_code', 'company_accounts')
        print("  ✓ Dropped index: ix_company_accounts_master_account_code")
    except Exception as e:
        print(f"  ℹ Index may not exist or already dropped: {e}")

    # Note: parent_code doesn't have a dedicated index, so nothing to drop

    # ========================================================================
    # STEP 6: Drop deprecated columns
    # ========================================================================
    print("  Dropping deprecated columns...")

    op.drop_column('company_accounts', 'parent_code')
    print("  ✓ Dropped column: parent_code")

    op.drop_column('company_accounts', 'master_account_code')
    print("  ✓ Dropped column: master_account_code")

    # ========================================================================
    # STEP 7: Verify cleanup
    # ========================================================================
    print("  Verifying cleanup...")

    column_check = connection.execute(sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'company_accounts'
          AND table_schema = 'public'
          AND column_name IN ('parent_code', 'master_account_code')
    """))

    remaining_columns = [row[0] for row in column_check]

    if remaining_columns:
        raise Exception(f"Cleanup verification failed: columns still exist: {remaining_columns}")

    print("  ✓ Deprecated columns successfully removed")

    # ========================================================================
    # STEP 8: Final schema check
    # ========================================================================
    print("  Current company_accounts schema:")

    schema_check = connection.execute(sa.text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'company_accounts'
          AND table_schema = 'public'
        ORDER BY ordinal_position
    """))

    for col in schema_check:
        nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
        print(f"    - {col[0]}: {col[1]} {nullable}")

    print("")
    print("=" * 80)
    print("MIGRATION 022: Complete")
    print("=" * 80)
    print("Deprecated columns dropped successfully")
    print(f"  - parent_code (replaced by parent_id)")
    print(f"  - master_account_code (replaced by mapped_master_account_id)")
    print("=" * 80)


def downgrade() -> None:
    """
    Restore deprecated columns.

    WARNING: This does NOT restore the original data.
    The columns will be re-created as empty (NULL).
    Only use for rollback during migration issues.

    To fully restore data, you would need to:
    1. Re-create columns
    2. Backfill from parent_id and mapped_master_account_id
    3. Re-create constraints and indexes
    """

    print("=" * 80)
    print("MIGRATION 022: Rolling back...")
    print("=" * 80)

    # Re-create columns (empty)
    op.add_column('company_accounts',
                  sa.Column('parent_code', sa.String(), nullable=True))
    print("  - Re-created column: parent_code (empty)")

    op.add_column('company_accounts',
                  sa.Column('master_account_code', sa.String(), nullable=True))
    print("  - Re-created column: master_account_code (empty)")

    # Re-create index on master_account_code
    op.create_index('ix_company_accounts_master_account_code',
                   'company_accounts',
                   ['master_account_code'])
    print("  - Re-created index: ix_company_accounts_master_account_code")

    # Re-create FK constraint
    op.create_foreign_key(
        'company_accounts_master_account_code_fkey',
        'company_accounts',
        'master_accounts',
        ['master_account_code'],
        ['code']
    )
    print("  - Re-created FK: company_accounts_master_account_code_fkey")

    print("")
    print("  ⚠ WARNING: Columns restored but data is empty")
    print("  To restore data, run backfill manually:")
    print("    UPDATE company_accounts ca")
    print("    SET parent_code = (SELECT code FROM company_accounts WHERE id = ca.parent_id)")
    print("    WHERE parent_id IS NOT NULL;")
    print("")
    print("    UPDATE company_accounts ca")
    print("    SET master_account_code = (SELECT code FROM master_accounts WHERE id = ca.mapped_master_account_id)")
    print("    WHERE mapped_master_account_id IS NOT NULL;")

    print("=" * 80)
    print("MIGRATION 022: Rollback complete")
    print("=" * 80)
