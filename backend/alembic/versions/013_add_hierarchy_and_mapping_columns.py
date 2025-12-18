"""Add parent_id and mapped_master_account_id to CompanyAccount

Revision ID: 013
Revises: 012
Create Date: 2025-12-13

PHASE 2A - SCHEMA NORMALIZATION (Structured Template Tables)
Migration 1 of 6

PURPOSE:
Enable proper account hierarchy and master chart mapping:
1. Replace string-based parent_code with UUID FK parent_id
2. Replace string-based master_account_code with UUID FK mapped_master_account_id
3. Support deterministic account hierarchy within company charts
4. Enable structural enforcement of account relationships

BACKGROUND:
Current schema uses:
- parent_code (String) - weak reference, no FK enforcement
- master_account_code (String) - weak reference to master_accounts.code

Phase 2A introduces:
- parent_id (UUID FK) - strong reference with cascade control
- mapped_master_account_id (UUID FK) - strong reference to master_accounts.id

MIGRATION STRATEGY:
1. Add new columns as nullable
2. Backfill parent_id from parent_code (string → UUID lookup)
3. Backfill mapped_master_account_id from master_account_code (string → UUID lookup)
4. Validate data integrity
5. Keep old columns temporarily for rollback safety
6. Later migration will drop old columns and make new ones NOT NULL

BREAKING: No - additive columns only
REQUIRES: Phase 1 complete (migrations 003-012)

CANONICAL REFERENCE:
- Phase 2A Specification: Structured Template Tables
- Section: Company Account Hierarchy
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

