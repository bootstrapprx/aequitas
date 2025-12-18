"""Add Phase 5 onboarding fields to companies table

Revision ID: 024_add_onboarding_fields
Revises: 023_add_performance_indexes
Create Date: 2025-12-17

CANONICAL REFERENCE:
- docs/canonical/PHASE_5_ONBOARDING_GUIDE.md

This migration adds the onboarding wizard state machine fields to the companies table.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
# revision identifiers, used by Alembic.
revision = '024'
down_revision = '023'
branch_labels = None
depends_on = None


def upgrade():
    pass

def downgrade():
    pass

