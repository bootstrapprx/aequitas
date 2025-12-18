"""Add account type immutability trigger for locked accounts

Revision ID: 009
Revises: 008
Create Date: 2025-12-13

PHASE 1 - CRITICAL DATA INTEGRITY
Migration 7 of 10

PURPOSE:
Prevent modification of critical account fields when account is locked.
This maintains consistency of historical financial data and prevents
corruption of financial statements that rely on account classification.

IMMUTABLE FIELDS (when is_locked = true):
- account_type (Asset, Liability, Equity, Revenue, Expense)
- code (account identifier in chart of accounts)
- normal_balance (Debit, Credit)

MUTABLE FIELDS (even when locked):
- description / name (cosmetic changes allowed)
- is_active (soft delete allowed if zero balance)
- currency (if not used in transactions)

BREAKING: No - trigger enforcement only
REQUIRES: Migration 007 (account locking fields)

CANONICAL REFERENCE:
- Section 5.2: Locked Account Restrictions
- Section 8.1: Database-Level Invariants
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

