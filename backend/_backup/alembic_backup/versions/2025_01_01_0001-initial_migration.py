"""initial migration

Revision ID: 2025_01_01_0001
Revises:
Create Date: 2025-01-01 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025_01_01_0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pg_trgm extension for fuzzy search
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')

    # Users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Plans table
    op.create_table('plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('monthly_requests', sa.Integer(), nullable=False),
        sa.Column('price_cents', sa.Integer(), nullable=False),
        sa.Column('stripe_price_id', sa.String(length=100), nullable=True),
        sa.Column('features', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # API Keys table
    op.create_table('api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('key_prefix', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash')
    )
    op.create_index(op.f('ix_api_keys_user_id'), 'api_keys', ['user_id'], unique=False)

    # Stripe Subscriptions table
    op.create_table('stripe_subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(length=100), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('current_period_start', sa.DateTime(), nullable=False),
        sa.Column('current_period_end', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_subscription_id')
    )
    op.create_index(op.f('ix_stripe_subscriptions_stripe_customer_id'), 'stripe_subscriptions', ['stripe_customer_id'], unique=False)
    op.create_index(op.f('ix_stripe_subscriptions_user_id'), 'stripe_subscriptions', ['user_id'], unique=False)

    # ICD-10 Codes table
    op.create_table('icd10_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_icd10_codes_code'), 'icd10_codes', ['code'], unique=False)
    op.create_index('ix_icd10_description', 'icd10_codes', ['description'], unique=False, postgresql_using='gin', postgresql_ops={'description': 'gin_trgm_ops'})
    op.create_index('ix_icd10_search_vector', 'icd10_codes', ['search_vector'], unique=False, postgresql_using='gin')

    # CPT Codes table
    op.create_table('cpt_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_cpt_codes_code'), 'cpt_codes', ['code'], unique=False)
    op.create_index('ix_cpt_description', 'cpt_codes', ['description'], unique=False, postgresql_using='gin', postgresql_ops={'description': 'gin_trgm_ops'})
    op.create_index('ix_cpt_search_vector', 'cpt_codes', ['search_vector'], unique=False, postgresql_using='gin')

    # Usage Logs table
    op.create_table('usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('api_key_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('endpoint', sa.String(length=255), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('query_params', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usage_logs_api_key_id'), 'usage_logs', ['api_key_id'], unique=False)
    op.create_index(op.f('ix_usage_logs_created_at'), 'usage_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_usage_logs_user_id'), 'usage_logs', ['user_id'], unique=False)
    op.create_index('ix_usage_logs_api_key_created', 'usage_logs', ['api_key_id', 'created_at'], unique=False)
    op.create_index('ix_usage_logs_user_created', 'usage_logs', ['user_id', 'created_at'], unique=False)

    # Support Tickets table
    op.create_table('support_tickets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_support_tickets_user_id'), 'support_tickets', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('support_tickets')
    op.drop_table('usage_logs')
    op.drop_table('cpt_codes')
    op.drop_table('icd10_codes')
    op.drop_table('stripe_subscriptions')
    op.drop_table('api_keys')
    op.drop_table('plans')
    op.drop_table('users')
    op.execute('DROP EXTENSION IF EXISTS pg_trgm')
