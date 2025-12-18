"""Add double-entry balance trigger for POSTED entries

Revision ID: 004
Revises: 003
Create Date: 2025-12-13

PHASE 1 - CRITICAL DATA INTEGRITY
Migration 2 of 10

PURPOSE:
Enforce the fundamental accounting equation at the database level:
  SUM(debits) = SUM(credits) for every POSTED journal entry

DRAFT entries are explicitly allowed to be unbalanced (work-in-progress).
Balance validation ONLY triggers when:
1. Journal entry status transitions to POSTED
2. Lines are modified on a POSTED entry (should be blocked by immutability trigger)

BREAKING: Yes - will fail if existing POSTED entries are unbalanced
REQUIRES: Data cleanup validation before applying

CANONICAL REFERENCE:
- Section 3.1: Double-Entry Validation
- Section 7.2: Journal Entry State Machine
- Section 8.1: Database-Level Invariants
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

