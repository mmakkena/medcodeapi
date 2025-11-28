"""add is_admin field to users

Revision ID: 2025_11_12_0001
Revises: 2025_11_10_0001
Create Date: 2025-11-12

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2025_11_12_0001'
down_revision = '2025_11_10_0001'
branch_labels = None
depends_on = None


def upgrade():
    """Add is_admin field to users table"""
    # Add is_admin column
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))

    # Create index on is_admin
    op.create_index('ix_users_is_admin', 'users', ['is_admin'])

    # Remove server_default after adding the column
    op.alter_column('users', 'is_admin', server_default=None)


def downgrade():
    """Remove is_admin field from users table"""
    # Drop index
    op.drop_index('ix_users_is_admin', table_name='users')

    # Drop column
    op.drop_column('users', 'is_admin')
