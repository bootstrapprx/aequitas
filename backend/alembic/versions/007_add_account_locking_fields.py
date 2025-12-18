"""Add account locking mechanism to CompanyAccount

Revision ID: 007
Revises: 006
Create Date: 2025-12-13

PHASE 1 - CRITICAL DATA INTEGRITY
Migration 5 of 10

PURPOSE:
Implement account locking mechanism to enforce immutability after first use:
1. Prevent account type changes after transactions posted
2. Prevent account code changes after transactions posted
3. Track when and why account was locked
4. Support manual locking for administrative purposes

LOCKING TRIGGERS:
- FirstTransaction: Account locks automatically when first POSTED journal entry uses it
- PeriodClose: Account locks when fiscal period is closed
- Manual: Administrator explicitly locks account

LOCKED RESTRICTIONS:
- Cannot change account_type
- Cannot change code
- Cannot change normal_balance
- CAN change description/name (cosmetic)
- CAN be soft-deleted (is_active=false) if zero balance

BREAKING: No - new fields are additive
REQUIRES: None

CANONICAL REFERENCE:
- Section 5: Account Locking Rules
- Section 5.2: Locked Account Restrictions
- Section 5.3: Unlocking Protocol
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

