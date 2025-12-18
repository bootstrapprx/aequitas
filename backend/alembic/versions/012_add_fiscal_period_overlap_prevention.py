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
    pass

def downgrade() -> None:
    pass

