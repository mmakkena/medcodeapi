"""add_guideline_fields_to_icd10_codes

Revision ID: 4b4e517c47de
Revises: 7787b0e5d54d
Create Date: 2025-11-09 08:32:22.986709

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b4e517c47de'
down_revision = '7787b0e5d54d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add guideline-specific fields to support year-specific coding guidance
    op.add_column('icd10_codes', sa.Column('coding_guidelines', sa.Text(), nullable=True))
    op.add_column('icd10_codes', sa.Column('clinical_notes', sa.Text(), nullable=True))
    op.add_column('icd10_codes', sa.Column('coding_tips', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove guideline fields
    op.drop_column('icd10_codes', 'coding_tips')
    op.drop_column('icd10_codes', 'clinical_notes')
    op.drop_column('icd10_codes', 'coding_guidelines')
