"""add fee schedule tables

Revision ID: 2025_11_26_0001
Revises: 2025_11_12_0001
Create Date: 2025-11-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '2025_11_26_0001'
down_revision = '2025_11_12_0001'
branch_labels = None
depends_on = None


def upgrade():
    """Create fee schedule tables for CMS Fee Schedule Explorer"""

    # CMS Localities table (GPCI values)
    op.create_table(
        'cms_localities',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('mac_code', sa.String(5), nullable=False),
        sa.Column('locality_code', sa.String(10), nullable=False),
        sa.Column('locality_name', sa.String(255), nullable=False),
        sa.Column('state', sa.String(2), nullable=True),
        sa.Column('work_gpci', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('pe_gpci', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('mp_gpci', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('year', sa.Integer(), nullable=False),
    )
    op.create_index('ix_cms_localities_state', 'cms_localities', ['state'])
    op.create_index('ix_cms_localities_year', 'cms_localities', ['year'])
    op.create_index('ix_cms_locality_code_year', 'cms_localities', ['locality_code', 'year'])
    op.create_index('ix_cms_locality_mac_locality', 'cms_localities', ['mac_code', 'locality_code'])

    # ZIP to Locality mapping table
    op.create_table(
        'zip_to_locality',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('zip_code', sa.String(5), nullable=False),
        sa.Column('locality_code', sa.String(10), nullable=False),
        sa.Column('state', sa.String(2), nullable=True),
        sa.Column('carrier_code', sa.String(5), nullable=True),
        sa.Column('year', sa.Integer(), nullable=False),
    )
    op.create_index('ix_zip_to_locality_zip_code', 'zip_to_locality', ['zip_code'])
    op.create_index('ix_zip_to_locality_locality_code', 'zip_to_locality', ['locality_code'])
    op.create_index('ix_zip_to_locality_year', 'zip_to_locality', ['year'])
    op.create_index('ix_zip_locality_year', 'zip_to_locality', ['zip_code', 'year'])

    # MPFS Rates table (RVUs)
    op.create_table(
        'mpfs_rates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('hcpcs_code', sa.String(10), nullable=False),
        sa.Column('modifier', sa.String(5), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status_code', sa.String(1), nullable=True),
        sa.Column('pctc_indicator', sa.String(1), nullable=True),
        sa.Column('work_rvu', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('non_facility_pe_rvu', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('facility_pe_rvu', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('mp_rvu', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('non_facility_total', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('facility_total', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('global_days', sa.String(5), nullable=True),
        sa.Column('mult_proc', sa.String(1), nullable=True),
        sa.Column('bilateral_surgery', sa.String(1), nullable=True),
        sa.Column('assistant_surgery', sa.String(1), nullable=True),
        sa.Column('co_surgeons', sa.String(1), nullable=True),
        sa.Column('team_surgery', sa.String(1), nullable=True),
        sa.Column('endo_base', sa.String(10), nullable=True),
        sa.Column('conv_factor_indicator', sa.String(1), nullable=True),
        sa.Column('physician_supervision', sa.String(2), nullable=True),
        sa.Column('diag_imaging_family', sa.String(2), nullable=True),
        sa.Column('non_fac_pe_used_for_opps', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('quarter', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('effective_date', sa.String(10), nullable=True),
    )
    op.create_index('ix_mpfs_rates_hcpcs_code', 'mpfs_rates', ['hcpcs_code'])
    op.create_index('ix_mpfs_rates_year', 'mpfs_rates', ['year'])
    op.create_index('ix_mpfs_code_year', 'mpfs_rates', ['hcpcs_code', 'year'])
    op.create_index('ix_mpfs_code_mod_year', 'mpfs_rates', ['hcpcs_code', 'modifier', 'year'])

    # Conversion Factors table
    op.create_table(
        'conversion_factors',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('year', sa.Integer(), nullable=False, unique=True),
        sa.Column('conversion_factor', sa.Float(), nullable=False),
        sa.Column('anesthesia_conversion_factor', sa.Float(), nullable=True),
        sa.Column('effective_date', sa.String(10), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
    )
    op.create_index('ix_conversion_factors_year', 'conversion_factors', ['year'])

    # Saved Code Lists table (user favorites)
    op.create_table(
        'saved_code_lists',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('codes', JSONB(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_saved_code_lists_user_id', 'saved_code_lists', ['user_id'])

    # User Fee Schedule Uploads table (contract analyzer)
    op.create_table(
        'user_fee_schedule_uploads',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('payer_name', sa.String(255), nullable=True),
        sa.Column('contract_year', sa.Integer(), nullable=True),
        sa.Column('original_filename', sa.String(255), nullable=True),
        sa.Column('upload_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('comparison_year', sa.Integer(), nullable=False),
        sa.Column('comparison_zip', sa.String(5), nullable=True),
        sa.Column('total_codes', sa.Integer(), nullable=True),
        sa.Column('codes_below_medicare', sa.Integer(), nullable=True),
        sa.Column('codes_above_medicare', sa.Integer(), nullable=True),
        sa.Column('total_variance', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_user_fee_schedule_uploads_user_id', 'user_fee_schedule_uploads', ['user_id'])

    # User Fee Schedule Line Items table
    op.create_table(
        'user_fee_schedule_line_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('upload_id', UUID(as_uuid=True), sa.ForeignKey('user_fee_schedule_uploads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cpt_code', sa.String(10), nullable=False),
        sa.Column('modifier', sa.String(5), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('contracted_rate', sa.Float(), nullable=False),
        sa.Column('annual_volume', sa.Integer(), nullable=True),
        sa.Column('medicare_rate', sa.Float(), nullable=True),
        sa.Column('variance', sa.Float(), nullable=True),
        sa.Column('variance_pct', sa.Float(), nullable=True),
        sa.Column('is_below_medicare', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('revenue_impact', sa.Float(), nullable=True),
    )
    op.create_index('ix_user_fee_schedule_line_items_upload_id', 'user_fee_schedule_line_items', ['upload_id'])
    op.create_index('ix_user_fee_schedule_line_items_cpt_code', 'user_fee_schedule_line_items', ['cpt_code'])
    op.create_index('ix_fee_schedule_item_upload_code', 'user_fee_schedule_line_items', ['upload_id', 'cpt_code'])


def downgrade():
    """Drop fee schedule tables"""
    op.drop_table('user_fee_schedule_line_items')
    op.drop_table('user_fee_schedule_uploads')
    op.drop_table('saved_code_lists')
    op.drop_table('conversion_factors')
    op.drop_table('mpfs_rates')
    op.drop_table('zip_to_locality')
    op.drop_table('cms_localities')
