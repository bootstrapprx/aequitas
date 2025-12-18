"""Add account_type enum and column to CompanyAccount

Revision ID: 005
Revises: 004
Create Date: 2025-12-13

PHASE 1 - CRITICAL DATA INTEGRITY
Migration 3 of 10

PURPOSE:
Add explicit account type classification to company accounts for:
1. GAAP-compliant financial statement generation
2. Trial balance calculation with proper grouping
3. Normal balance derivation
4. Account balance calculation logic

BREAKING: Yes - requires data backfill to populate account_type
REQUIRES: Master account mapping for data migration

DATA MIGRATION STRATEGY:
1. Create ENUM type for account classification
2. Add nullable account_type column
3. Backfill from master_account.category (via join)
4. For unmapped accounts, derive from code prefix or manual classification
5. Make column NOT NULL after backfill

CANONICAL REFERENCE:
- Section 1.1: Master Reference Chart (account_type field)
- Section 1.3: Company-Specific Chart
- Section 2.1: Account Type Classification
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

