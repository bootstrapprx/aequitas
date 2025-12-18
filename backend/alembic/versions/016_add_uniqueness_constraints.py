"""Add uniqueness constraints to company_accounts

Revision ID: 016
Revises: 015
Create Date: 2025-12-13

PHASE 2A - SCHEMA NORMALIZATION (Structured Template Tables)
Migration 4 of 6

PURPOSE:
Enforce account uniqueness within company charts:
1. Prevent duplicate account codes within same company
2. Prevent duplicate account names within same company
3. Optional: Prevent duplicate master mappings within same company
4. Ensure data integrity and deterministic account lookups

BACKGROUND:
Current schema allows:
- Multiple accounts with same code in same company (ambiguous)
- Multiple accounts with same name in same company (confusing)
- Multiple company accounts mapping to same master account (may be valid)

Phase 2A enforces:
- UNIQUE(company_id, code): One code per company
- UNIQUE(company_id, name): One name per company
- Optional UNIQUE(company_id, mapped_master_account_id): One mapping per company

MIGRATION STRATEGY:
1. Identify and report duplicate codes/names
2. Provide remediation queries for duplicates
3. Add UNIQUE constraints after validation
4. Add indexes for performance

BREAKING: Yes - may fail if duplicate codes/names exist
REQUIRES: Migrations 013, 014, 015 complete

CANONICAL REFERENCE:
- Phase 2A Specification: Account Uniqueness
- Section: Company Chart Integrity
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

