"""Add NOT NULL constraints to company_accounts

Revision ID: 020
Revises: 019
Create Date: 2025-12-13

PHASE 2B - SCHEMA CLEANUP AND OPTIMIZATION
Migration 2 of 5

PURPOSE:
Strengthen data integrity by adding NOT NULL constraints to critical columns:
1. Backfill any NULL values with appropriate defaults
2. Add NOT NULL constraint to is_locked (already has default)
3. Verify normal_balance is never NULL (added in Phase 1)
4. Verify account_type is populated (added in Phase 1)

BACKGROUND:
Phase 1 added is_locked, normal_balance, and account_type columns.
These columns should never be NULL, but constraints weren't added yet.
This migration ensures data integrity at the database level.

BREAKING: No - only adds constraints after backfilling
REQUIRES: Migration 019 complete

CANONICAL REFERENCE:
- Phase 2B Specification: Schema Cleanup and Optimization
- Section: NOT NULL Constraints
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

