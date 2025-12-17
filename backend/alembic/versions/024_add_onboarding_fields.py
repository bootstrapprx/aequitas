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
revision = '024_add_onboarding_fields'
down_revision = '023_add_performance_indexes'
branch_labels = None
depends_on = None


def upgrade():
    """Add onboarding fields to companies table."""

    # Create OnboardingStatus enum type
    onboarding_status_enum = postgresql.ENUM(
        'DRAFT',
        'TEMPLATE_SELECTED',
        'CHART_READY',
        'CHART_FINALIZED',
        'ACTIVE',
        name='onboardingstatus',
        create_type=True
    )
    onboarding_status_enum.create(op.get_bind(), checkfirst=True)

    # Add onboarding-related columns to companies table
    with op.batch_alter_table('companies', schema=None) as batch_op:
        # Company details for wizard
        batch_op.add_column(sa.Column('trade_name', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('timezone', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('currency', sa.String(length=3), nullable=True))

        # Onboarding state machine
        batch_op.add_column(sa.Column(
            'onboarding_status',
            sa.Enum('DRAFT', 'TEMPLATE_SELECTED', 'CHART_READY', 'CHART_FINALIZED', 'ACTIVE', name='onboardingstatus'),
            nullable=False,
            server_default='DRAFT'
        ))
        batch_op.add_column(sa.Column('onboarding_current_step', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('onboarding_started_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('onboarding_completed_at', sa.DateTime(timezone=True), nullable=True))

        # Session locking for multi-session protection
        batch_op.add_column(sa.Column('onboarding_session_lock', postgresql.UUID(as_uuid=True), nullable=True))
        batch_op.add_column(sa.Column('onboarding_session_locked_at', sa.DateTime(timezone=True), nullable=True))

        # Create index on onboarding_status for efficient queries
        batch_op.create_index('ix_companies_onboarding_status', ['onboarding_status'])


def downgrade():
    """Remove onboarding fields from companies table."""

    with op.batch_alter_table('companies', schema=None) as batch_op:
        # Drop index
        batch_op.drop_index('ix_companies_onboarding_status')

        # Remove columns
        batch_op.drop_column('onboarding_session_locked_at')
        batch_op.drop_column('onboarding_session_lock')
        batch_op.drop_column('onboarding_completed_at')
        batch_op.drop_column('onboarding_started_at')
        batch_op.drop_column('onboarding_current_step')
        batch_op.drop_column('onboarding_status')
        batch_op.drop_column('currency')
        batch_op.drop_column('timezone')
        batch_op.drop_column('trade_name')

    # Drop enum type
    sa.Enum(name='onboardingstatus').drop(op.get_bind(), checkfirst=True)
