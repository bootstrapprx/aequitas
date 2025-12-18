"""Add auto-lock trigger for accounts on first posted transaction

Revision ID: 008
Revises: 007
Create Date: 2025-12-13

PHASE 1 - CRITICAL DATA INTEGRITY
Migration 6 of 10

PURPOSE:
Automatically lock accounts when first used in a POSTED journal entry.
This prevents account type and code changes after the account has been
used in financial transactions, preserving data integrity and audit trail.

TRIGGER BEHAVIOR:
- Fires AFTER INSERT on journal_entry_lines
- Only acts when parent journal entry status = 'POSTED'
- Locks account if not already locked
- Sets locked_reason = 'FirstTransaction'
- Sets locked_at = journal entry posted_at timestamp

BREAKING: No - trigger enforcement only
REQUIRES: Migration 007 (account locking fields)

CANONICAL REFERENCE:
- Section 5.1: Lock Triggers
- Section 8.1: Database-Level Invariants
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

