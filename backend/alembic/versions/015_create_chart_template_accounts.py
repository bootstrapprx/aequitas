"""Create chart_template_accounts table

Revision ID: 015
Revises: 014
Create Date: 2025-12-13

PHASE 2A - SCHEMA NORMALIZATION (Structured Template Tables)
Migration 3 of 6

PURPOSE:
Create detailed account structure within chart templates:
1. Define individual accounts belonging to each template
2. Link template accounts to master chart accounts
3. Support account hierarchy within templates
4. Mark mandatory accounts that cannot be omitted
5. Control custom account creation per template node

BACKGROUND:
chart_templates defines template metadata (migration 014).
chart_template_accounts defines the actual accounts in each template.

Each template account:
- References a master_account (for classification/metadata)
- May have a parent_id (for hierarchy)
- Has template-specific properties (code, name, sort_order)
- Indicates if mandatory (cannot be deleted from company chart)
- Indicates if custom children allowed (extensibility)

BREAKING: No - new table creation only
REQUIRES: Migrations 013, 014 complete

CANONICAL REFERENCE:
- Phase 2A Specification: Structured Template Tables
- Section: Template Account Structure
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

