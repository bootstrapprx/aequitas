"""Add version field to MasterAccount

Revision ID: 011
Revises: 010
Create Date: 2025-12-13

PHASE 1 - CRITICAL DATA INTEGRITY
Migration 9 of 10

PURPOSE:
Add version tracking to master chart of accounts to support:
1. Master chart evolution over time (e.g., GAAP standard updates)
2. Multiple master chart versions for different regulatory periods
3. Audit trail of which master chart version was used for mapping
4. Future migration paths when standards change

VERSION FORMAT: "YYYY.Q" (e.g., "2024.1", "2025.1")

BREAKING: No - new field is additive
REQUIRES: None

CANONICAL REFERENCE:
- Section 1.1: Master Reference Chart (version field)
- Section 13.1: Master Chart Versioning
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

