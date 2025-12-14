"""Add fiscal period overlap prevention constraint

Revision ID: 012
Revises: 011
Create Date: 2025-12-13

PHASE 1 - CRITICAL DATA INTEGRITY
Migration 10 of 10

PURPOSE:
Prevent overlapping fiscal periods for the same company.
Overlapping periods would cause:
1. Conflicting journal entry dates (which period does entry belong to?)
2. Incorrect period-based financial reports
3. Ambiguous fiscal period closing/locking
4. Corrupted accounting cycle

CONSTRAINT BEHAVIOR:
- EXCLUDE constraint using daterange and company_id
- Prevents INSERT/UPDATE that creates overlapping date ranges
- Applies to all fiscal periods regardless of status

BREAKING: Yes - will fail if existing overlapping periods exist
REQUIRES: Data cleanup validation before applying

CANONICAL REFERENCE:
- Section 8.1: Database-Level Invariants
- Section 8.3: Temporal Invariants
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add exclusion constraint to prevent overlapping fiscal periods.

    POSTGRESQL EXCLUSION CONSTRAINT:
    Uses daterange and btree_gist extension to enforce that no two periods
    for the same company can have overlapping date ranges.

    CONSTRAINT FORMULA:
    EXCLUDE USING gist (
        company_id WITH =,
        daterange(start_date, end_date, '[]') WITH &&
    )

    Constraint applies to all periods regardless of status.

    NOTE: PostgreSQL EXCLUDE requires the btree_gist extension for
    combining equality (company_id =) with range overlap (&&).
    """

    # ========================================================================
    # STEP 1: Enable btree_gist extension
    # ========================================================================
    # Required for EXCLUDE constraint with mixed operators (= and &&)
    # ========================================================================

    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    # ========================================================================
    # STEP 2: Pre-flight check for existing overlaps
    # ========================================================================
    # Identify any existing overlapping periods and log them as warnings.
    # Migration will fail if overlaps exist.
    # ========================================================================

    op.execute("""
        DO $$
        DECLARE
            v_overlap_count INTEGER;
            overlap_record RECORD;
        BEGIN
            -- Check for overlapping periods
            SELECT COUNT(*) INTO v_overlap_count
            FROM fiscal_periods fp1
            JOIN fiscal_periods fp2
                ON fp1.company_id = fp2.company_id
                AND fp1.id < fp2.id  -- Avoid counting same pair twice
                AND daterange(fp1.start_date, fp1.end_date, '[]')
                    && daterange(fp2.start_date, fp2.end_date, '[]');

            IF v_overlap_count > 0 THEN
                RAISE WARNING 'Found % overlapping fiscal period pairs:', v_overlap_count;

                -- Log first 10 overlaps for debugging
                FOR overlap_record IN
                    SELECT
                        fp1.company_id,
                        fp1.period_number as period1,
                        fp1.start_date as start1,
                        fp1.end_date as end1,
                        fp2.period_number as period2,
                        fp2.start_date as start2,
                        fp2.end_date as end2
                    FROM fiscal_periods fp1
                    JOIN fiscal_periods fp2
                        ON fp1.company_id = fp2.company_id
                        AND fp1.id < fp2.id
                        AND daterange(fp1.start_date, fp1.end_date, '[]')
                            && daterange(fp2.start_date, fp2.end_date, '[]')
                    LIMIT 10
                LOOP
                    RAISE WARNING 'Company % has overlapping periods: % (% to %) overlaps with % (% to %)',
                        overlap_record.company_id,
                        overlap_record.period1,
                        overlap_record.start1,
                        overlap_record.end1,
                        overlap_record.period2,
                        overlap_record.start2,
                        overlap_record.end2;
                END LOOP;

                RAISE EXCEPTION 'Cannot add overlap prevention constraint: % overlapping periods exist. Fix data before migration.', v_overlap_count
                USING HINT = 'Query: SELECT * FROM fiscal_periods WHERE company_id IN (SELECT company_id FROM fiscal_periods GROUP BY company_id HAVING COUNT(*) > 1) ORDER BY company_id, start_date;';
            ELSE
                RAISE NOTICE 'Pre-flight check passed: No overlapping fiscal periods found.';
            END IF;
        END $$;
    """)

    # ========================================================================
    # STEP 3: Add EXCLUDE constraint
    # ========================================================================
    # JUSTIFICATION: Overlapping fiscal periods violate temporal consistency.
    # A transaction dated 2024-01-15 must belong to exactly one fiscal period,
    # not multiple. This constraint enforces mutual exclusivity.
    #
    # ENFORCEMENT: PostgreSQL EXCLUDE constraint (cannot be bypassed)
    #
    # Constraint applies to all periods (OPEN, CLOSED, LOCKED) to ensure
    # temporal consistency across the entire fiscal calendar.
    # ========================================================================

    # Note: Alembic doesn't have native support for EXCLUDE constraints,
    # so we use raw SQL via op.execute()

    op.execute("""
        ALTER TABLE fiscal_periods
        ADD CONSTRAINT exclude_overlapping_fiscal_periods
        EXCLUDE USING gist (
            company_id WITH =,
            daterange(start_date, end_date, '[]') WITH &&
        )
    """)

    # ========================================================================
    # STEP 4: Add helpful indexes
    # ========================================================================
    # Composite index for period lookups by company and date
    # ========================================================================

    op.create_index(
        'ix_fiscal_periods_company_date_range',
        'fiscal_periods',
        ['company_id', 'start_date', 'end_date']
    )


def downgrade() -> None:
    """
    Remove fiscal period overlap prevention constraint.

    WARNING: After downgrade, overlapping periods can be created.
    Period-based reports may become incorrect.
    """

    op.drop_index('ix_fiscal_periods_company_date_range', table_name='fiscal_periods')
    op.execute("ALTER TABLE fiscal_periods DROP CONSTRAINT IF EXISTS exclude_overlapping_fiscal_periods")

    # Note: We don't drop btree_gist extension as other parts of the
    # system might be using it
