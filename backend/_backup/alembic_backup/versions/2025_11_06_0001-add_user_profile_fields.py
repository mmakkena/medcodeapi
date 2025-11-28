"""add user profile fields

Revision ID: 2025_11_06_0001
Revises: 2025_01_05_0001
Create Date: 2025-11-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2025_11_06_0001'
down_revision = '2025_01_05_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new user profile fields
    op.add_column('users', sa.Column('full_name', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('company_name', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('role', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('auth_provider', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('oauth_provider_id', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(), nullable=True))

    # Create index on oauth_provider_id for faster lookups
    op.create_index(op.f('ix_users_oauth_provider_id'), 'users', ['oauth_provider_id'], unique=False)


def downgrade() -> None:
    # Remove index
    op.drop_index(op.f('ix_users_oauth_provider_id'), table_name='users')

    # Remove columns in reverse order
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'oauth_provider_id')
    op.drop_column('users', 'auth_provider')
    op.drop_column('users', 'role')
    op.drop_column('users', 'company_name')
    op.drop_column('users', 'full_name')
