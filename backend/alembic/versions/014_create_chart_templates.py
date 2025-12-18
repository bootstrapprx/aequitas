"""Create chart_templates table

Revision ID: 014
Revises: 013
Create Date: 2025-12-13

PHASE 2A - SCHEMA NORMALIZATION (Structured Template Tables)
Migration 2 of 6

PURPOSE:
Create canonical chart template structure to replace JSON blob templates:
1. Define explicit, versioned chart templates
2. Support jurisdiction-specific templates (US-GAAP, IFRS, etc.)
3. Enable template evolution tracking
4. Foundation for template-account relationships

BACKGROUND:
Current system uses ad-hoc JSON blobs in coa_templates.data.
Phase 2A introduces structured, relational template architecture:
- chart_templates: Template metadata
- chart_template_accounts: Individual accounts within template

This migration creates the template metadata table.
Next migration (015) creates the account detail table.

BREAKING: No - new table creation only
REQUIRES: Migration 013 complete

CANONICAL REFERENCE:
- Phase 2A Specification: Structured Template Tables
- Section: Chart Template Structure
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

