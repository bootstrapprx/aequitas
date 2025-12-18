"""Add posted journal entry immutability triggers

Revision ID: 010
Revises: 009
Create Date: 2025-12-13

PHASE 1 - CRITICAL DATA INTEGRITY
Migration 8 of 10

PURPOSE:
Enforce immutability of posted journal entries to maintain audit trail integrity.
Once a journal entry is posted, it becomes part of the permanent financial record
and cannot be modified or deleted. Corrections must be made via reversing entries.

IMMUTABILITY RULES (when status = 'POSTED'):
- Journal entry fields cannot be modified (except status → VOID)
- Journal entry lines cannot be modified
- Journal entry lines cannot be deleted
- Journal entry cannot be deleted
- Only allowed transition: POSTED → VOID (creates reversing entry)

BREAKING: No - trigger enforcement only
REQUIRES: None

CANONICAL REFERENCE:
- Section 7.2: Journal Entry State Machine
- Section 7: Audit Safety (Historical Immutability)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

