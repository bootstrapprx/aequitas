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
    """
    Enable pgvector extension and add embedding columns.
    """
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Add embedding column to master_accounts (384 dimensions for all-MiniLM-L6-v2)
    op.execute('ALTER TABLE master_accounts ADD COLUMN IF NOT EXISTS embedding vector(384)')

    # Add embedding column to company_accounts
    op.execute('ALTER TABLE company_accounts ADD COLUMN IF NOT EXISTS embedding vector(384)')

    # Create indexes for fast similarity search using ivfflat
    # Note: These will be empty initially and should be reindexed after populating embeddings
    op.execute('''
        CREATE INDEX IF NOT EXISTS master_accounts_embedding_idx
        ON master_accounts USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    ''')

    op.execute('''
        CREATE INDEX IF NOT EXISTS company_accounts_embedding_idx
        ON company_accounts USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    ''')


def downgrade():
    """
    Remove embedding columns and pgvector extension.
    """
    # Drop indexes
    op.drop_index('company_accounts_embedding_idx', table_name='company_accounts')
    op.drop_index('master_accounts_embedding_idx', table_name='master_accounts')

    # Drop embedding columns
    op.drop_column('company_accounts', 'embedding')
    op.drop_column('master_accounts', 'embedding')

    # Note: We don't drop the extension as other tables might use it
    # If you want to drop it: op.execute('DROP EXTENSION IF EXISTS vector')
