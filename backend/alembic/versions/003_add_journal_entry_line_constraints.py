"""Add journal entry line constraints

Revision ID: 003
Revises: 002
Create Date: 2025-12-13

PHASE 1 - CRITICAL DATA INTEGRITY
Migration 1 of 10

PURPOSE:
Enforce fundamental double-entry accounting rules at the database level:
1. Amounts must be positive (no negative debits or credits)
2. Each line must have exactly one of debit OR credit (XOR constraint)

BREAKING: Yes - will fail if existing data violates constraints
REQUIRES: Data cleanup validation before applying

CANONICAL REFERENCE:
- Section 3.1: Double-Entry Validation
- Section 8.1: Database-Level Invariants
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add CHECK constraints to journal_entry_lines table.

    Constraints added:
    1. jel_positive_amounts: Ensures debit_amount >= 0 AND credit_amount >= 0
    2. jel_debit_xor_credit: Ensures exactly one of debit or credit is non-zero

    IMPORTANT: This migration will FAIL if existing data contains:
    - Negative amounts in debit_amount or credit_amount
    - Lines with both debit AND credit non-zero
    - Lines with both debit AND credit zero

    Run pre-migration validation script to identify violations before applying.
    """

    # ========================================================================
    # CONSTRAINT 1: Positive Amounts
    # ========================================================================
    # JUSTIFICATION: Accounting debits and credits are always positive values.
    # The direction (debit vs credit) determines increase/decrease, not sign.
    # Negative amounts indicate data corruption or logic errors.
    #
    # ENFORCEMENT: Database CHECK constraint (cannot be bypassed)
    # ========================================================================

    op.execute("""
        ALTER TABLE journal_entry_lines
        ADD CONSTRAINT jel_positive_amounts
        CHECK (debit_amount >= 0 AND credit_amount >= 0)
    """)

    # ========================================================================
    # CONSTRAINT 2: Debit XOR Credit (Exactly One Non-Zero)
    # ========================================================================
    # JUSTIFICATION: Each journal entry line represents a single posting to
    # an account. It must be EITHER a debit OR a credit, never both, never neither.
    # This is a fundamental rule of double-entry bookkeeping.
    #
    # ENFORCEMENT: Database CHECK constraint
    #
    # Note: We allow debit_amount = 0 or credit_amount = 0 explicitly,
    # but require exactly one to be non-zero.
    # ========================================================================

    op.execute("""
        ALTER TABLE journal_entry_lines
        ADD CONSTRAINT jel_debit_xor_credit
        CHECK (
            (debit_amount > 0 AND credit_amount = 0) OR
            (debit_amount = 0 AND credit_amount > 0)
        )
    """)


def downgrade() -> None:
    """
    Remove CHECK constraints from journal_entry_lines table.

    WARNING: Downgrading removes data integrity protection.
    Only use for rollback during migration issues.
    """

    op.execute("ALTER TABLE journal_entry_lines DROP CONSTRAINT IF EXISTS jel_debit_xor_credit")
    op.execute("ALTER TABLE journal_entry_lines DROP CONSTRAINT IF EXISTS jel_positive_amounts")
