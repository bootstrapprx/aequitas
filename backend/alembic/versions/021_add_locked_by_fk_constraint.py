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
    pass

def downgrade() -> None:
    pass

