"""Create Fiscal Engine tables for Pass-Through Tax Exposure

Revision ID: 025_create_fiscal_engine_tables
Revises: 024_add_onboarding_fields
Create Date: 2025-12-18

CANONICAL REFERENCE:
- prompt.md (Fiscal Engine v1 Implementation)

This migration creates 6 new tables for the Fiscal Engine:
1. entity_tax_profiles - Tax assumptions per company
2. tax_rulesets - Versioned tax calculation rules
3. tax_runs - Individual engine executions
4. tax_facts - Normalized trial balance facts
5. tax_adjustments - Rule-generated adjustments
6. tax_positions - Final tax position outputs
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '025'
down_revision = '024'
branch_labels = None
depends_on = None


def upgrade():
    """Create Fiscal Engine tables."""

    # 1. entity_tax_profiles
    op.create_table(
        'entity_tax_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('entity_type', sa.String(), nullable=False, server_default='LLC'),
        sa.Column('tax_regime', sa.String(), nullable=False, server_default='PASS_THROUGH'),
        sa.Column('accounting_method', sa.String(), nullable=True),  # CASH, ACCRUAL, HYBRID
        sa.Column('fiscal_year_start', sa.Date(), nullable=True),
        sa.Column('jurisdictions', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('elections', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_entity_tax_profiles_company_id', 'entity_tax_profiles', ['company_id'])

    # 2. tax_rulesets
    op.create_table(
        'tax_rulesets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('scope', sa.String(), nullable=False),
        sa.Column('jurisdiction', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='ACTIVE'),
        sa.Column('rules', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_tax_rulesets_version', 'tax_rulesets', ['version'])
    op.create_index('ix_tax_rulesets_scope', 'tax_rulesets', ['scope'])
    op.create_index('ix_tax_rulesets_version_scope_jurisdiction', 'tax_rulesets', ['version', 'scope', 'jurisdiction'], unique=True)

    # 3. tax_runs
    op.create_table(
        'tax_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),  # null for consolidated
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('as_of_date', sa.Date(), nullable=True),
        sa.Column('ruleset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ruleset_version', sa.String(), nullable=False),
        sa.Column('engine_version', sa.String(), nullable=False),
        sa.Column('inputs_hash', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='SUCCESS'),
        sa.Column('confidence_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('missing_inputs', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('label', sa.String(), nullable=False, server_default='Estimated / Projected Tax Exposure — Not a Tax Filing'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ruleset_id'], ['tax_rulesets.id'], ondelete='RESTRICT'),
    )
    op.create_index('ix_tax_runs_company_id', 'tax_runs', ['company_id'])
    op.create_index('ix_tax_runs_ruleset_version', 'tax_runs', ['ruleset_version'])
    op.create_index('ix_tax_runs_inputs_hash', 'tax_runs', ['inputs_hash'])
    op.create_index('ix_tax_runs_company_period', 'tax_runs', ['company_id', 'period_start', 'period_end'])

    # 4. tax_facts
    op.create_table(
        'tax_facts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tax_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('account_code', sa.String(), nullable=False),
        sa.Column('account_name', sa.String(), nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('tax_tags', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('source', sa.String(), nullable=False),  # TRIAL_BALANCE, LEDGER
        sa.Column('source_trace', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tax_run_id'], ['tax_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_id'], ['company_accounts.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_tax_facts_tax_run_id', 'tax_facts', ['tax_run_id'])
    op.create_index('ix_tax_facts_company_id', 'tax_facts', ['company_id'])

    # 5. tax_adjustments
    op.create_table(
        'tax_adjustments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tax_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tax_type', sa.String(), nullable=False),
        sa.Column('adjustment_type', sa.String(), nullable=False),  # permanent, timing, reclass, limit
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('rule_id', sa.String(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('source_fact_ids', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tax_run_id'], ['tax_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_tax_adjustments_tax_run_id', 'tax_adjustments', ['tax_run_id'])
    op.create_index('ix_tax_adjustments_company_id', 'tax_adjustments', ['company_id'])

    # 6. tax_positions
    op.create_table(
        'tax_positions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tax_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),  # null for consolidated
        sa.Column('tax_type', sa.String(), nullable=False),
        sa.Column('taxable_income_estimated', sa.Numeric(15, 2), nullable=False),
        sa.Column('exposure_estimated', sa.Numeric(15, 2), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('confidence_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('missing_inputs', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('top_drivers', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tax_run_id'], ['tax_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_tax_positions_tax_run_id', 'tax_positions', ['tax_run_id'])
    op.create_index('ix_tax_positions_company_tax_type', 'tax_positions', ['company_id', 'tax_type'])


def downgrade():
    """Drop Fiscal Engine tables."""

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('tax_positions')
    op.drop_table('tax_adjustments')
    op.drop_table('tax_facts')
    op.drop_table('tax_runs')
    op.drop_table('tax_rulesets')
    op.drop_table('entity_tax_profiles')
