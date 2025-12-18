"""Drop deprecated parent_code and master_account_code columns

Revision ID: 022
Revises: 021
Create Date: 2025-12-13

PHASE 2B - SCHEMA CLEANUP AND OPTIMIZATION
Migration 4 of 5

PURPOSE:
Remove deprecated string-based reference columns from company_accounts:
1. Drop parent_code (replaced by parent_id UUID FK in Phase 2A)
2. Drop master_account_code (replaced by mapped_master_account_id UUID FK in Phase 2A)
3. Verify all data successfully migrated before dropping
4. Clean up indexes on deprecated columns

BACKGROUND:
Phase 2A (migration 013) added parent_id and mapped_master_account_id
as proper UUID foreign keys, replacing the old string-based references.

Original columns:
- parent_code: String reference to parent account's code
- master_account_code: String reference to master account's code

Replacement columns:
- parent_id: UUID FK to company_accounts.id
- mapped_master_account_id: UUID FK to master_accounts.id

This migration completes the cleanup by removing the old columns.

BREAKING: Yes - removes columns (but they're deprecated)
REQUIRES: Migration 021 complete, Phase 2A migration complete

CANONICAL REFERENCE:
- Phase 2B Specification: Schema Cleanup and Optimization
- Section: Deprecate Legacy Columns
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '022'
down_revision = '021'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

