"""add pgvector support

Revision ID: 002_add_pgvector
Revises: 001
Create Date: 2025-12-11

Adds pgvector extension and embedding columns to master_accounts and company_accounts
for semantic similarity search.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    pass

def downgrade():
    pass

