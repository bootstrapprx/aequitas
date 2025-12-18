"""Add mandatory account enforcement for template compliance

Revision ID: 018
Revises: 017
Create Date: 2025-12-13

PHASE 2A - SCHEMA NORMALIZATION (Structured Template Tables)
Migration 6 of 6

PURPOSE:
Enforce that companies using chart templates include all mandatory accounts:
1. Create company_template_usage table to track template assignment
2. Add triggers to prevent deletion of mandatory accounts
3. Add triggers to prevent deactivation of mandatory accounts
4. Validate mandatory account presence on template assignment

BACKGROUND:
chart_template_accounts.is_mandatory indicates accounts that MUST exist
in any company chart using that template.

Examples of mandatory accounts:
- Cash (required for any business)
- Retained Earnings (required for equity tracking)
- Revenue/Expense summary accounts (required for closing entries)

ENFORCEMENT:
- When company assigns template, all mandatory accounts must be created
- Once created, mandatory accounts cannot be deleted
- Once created, mandatory accounts cannot be deactivated (is_active = false)
- Manual override requires superuser privileges (application-level)

BREAKING: No - new table and enforcement only
REQUIRES: Migrations 013-017 complete

CANONICAL REFERENCE:
- Phase 2A Specification: Mandatory Account Enforcement
- Section: Template Compliance Rules
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

