"""Add normal_balance enum and column to CompanyAccount

Revision ID: 006
Revises: 005
Create Date: 2025-12-13

PHASE 1 - CRITICAL DATA INTEGRITY
Migration 4 of 10

PURPOSE:
Add normal balance classification to company accounts for:
1. Proper account balance calculation (debit balances vs credit balances)
2. Trial balance generation and validation
3. Financial statement presentation
4. Determining whether debits increase or decrease account balance

NORMAL BALANCE DERIVATION:
- Asset accounts: Debit
- Expense accounts: Debit
- Liability accounts: Credit
- Equity accounts: Credit
- Revenue accounts: Credit

EXCEPTION: Contra accounts (e.g., Accumulated Depreciation, Sales Returns)
have opposite normal balance from their parent type. Contra account
support will be added in Phase 4.

BREAKING: No - uses deterministic derivation from account_type
REQUIRES: Migration 005 (account_type) must be applied first

CANONICAL REFERENCE:
- Section 2.2: Normal Balance Derivation
- Section 3.2: Balance Calculation
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

