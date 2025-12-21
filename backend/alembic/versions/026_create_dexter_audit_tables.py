"""Create Dexter Audit Tables for Normalization and Onboarding

Revision ID: 026
Revises: 51cf6bcdf646
Create Date: 2025-12-20

CANONICAL REFERENCE:
- NORMALIZATION_CANON.md v1.0 (§6.1)
- DEXTER_CANON.md v1.1 (§7.2)

This migration creates 2 new tables:
1. normalization_audit - System-wide log of all normalization events
2. onboarding_corrections - Dedicated log for Dexter's onboarding interventions (learning dataset)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '026'
down_revision = '51cf6bcdf646'
branch_labels = None
depends_on = None


def upgrade():
    """Create Dexter Audit tables."""

    # 1. normalization_audit
    # Defined in NORMALIZATION_CANON.md §6.1
    op.create_table(
        'normalization_audit',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', sa.String(), nullable=False),  # company, user, account, etc.
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('field_name', sa.String(), nullable=False),
        sa.Column('user_input', sa.Text(), nullable=False),
        sa.Column('suggested_value', sa.Text(), nullable=False),
        sa.Column('final_value', sa.Text(), nullable=False),
        sa.Column('normalization_type', sa.String(), nullable=False),  # capitalization, whitespace, suffix, etc.
        sa.Column('confidence_score', sa.Numeric(3, 2), nullable=False),  # 0.00 to 1.00
        sa.Column('user_accepted_suggestion', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    # Indexes for analysis
    op.create_index('ix_normalization_audit_entity', 'normalization_audit', ['entity_type', 'entity_id'])
    op.create_index('ix_normalization_audit_field', 'normalization_audit', ['field_name'])
    op.create_index('ix_normalization_audit_type', 'normalization_audit', ['normalization_type'])

    # 2. onboarding_corrections
    # Defined/Inferred from DEXTER_CANON.md §7.2 and system requirements
    # Similar to normalization_audit but focused on the user interaction/correction event for learning
    op.create_table(
        'onboarding_corrections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),  # Nullable if pre-creation
        sa.Column('session_id', sa.String(), nullable=True),  # For tracking unauthenticated flows
        sa.Column('step', sa.String(), nullable=False),  # e.g., company_details
        sa.Column('field', sa.String(), nullable=False),
        sa.Column('original_input', sa.Text(), nullable=False),
        sa.Column('dexter_suggestion', sa.Text(), nullable=False),
        sa.Column('correction_type', sa.String(), nullable=False),
        sa.Column('user_action', sa.String(), nullable=False),  # ACCEPTED, REJECTED, EDITED
        sa.Column('final_value', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_onboarding_corrections_company_id', 'onboarding_corrections', ['company_id'])
    op.create_index('ix_onboarding_corrections_field', 'onboarding_corrections', ['field'])


def downgrade():
    """Drop Dexter Audit tables."""
    op.drop_table('onboarding_corrections')
    op.drop_table('normalization_audit')
