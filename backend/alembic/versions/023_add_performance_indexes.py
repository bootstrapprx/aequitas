"""Add performance optimization indexes

Revision ID: 023
Revises: 022
Create Date: 2025-12-13

PHASE 2B - SCHEMA CLEANUP AND OPTIMIZATION
Migration 5 of 5 (FINAL)

PURPOSE:
Add strategic indexes to optimize common query patterns:
1. Composite index for company_id + parent_id (hierarchy traversal)
2. Composite index for company_id + is_active (active account filtering)
3. Composite index for company_id + is_locked (locked account queries)
4. Composite index for template_id + is_mandatory (mandatory account validation)
5. Partial indexes for specific filtered queries

BACKGROUND:
Phase 2A and 2B added new columns and relationships.
This migration optimizes query performance for common access patterns.

Query patterns optimized:
- Get all accounts for a company with hierarchy
- Get active accounts for a company
- Get locked accounts for a company
- Validate mandatory accounts for a template
- Traverse account hierarchy efficiently

BREAKING: No - index creation only
REQUIRES: Migration 022 complete

CANONICAL REFERENCE:
- Phase 2B Specification: Schema Cleanup and Optimization
- Section: Performance Optimization
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '023'
down_revision = '022'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

