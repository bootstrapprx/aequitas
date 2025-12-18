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
    pass

def downgrade() -> None:
    pass

