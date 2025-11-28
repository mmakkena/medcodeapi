"""Enhance ICD-10 with semantic search and AI facets

Revision ID: 2025_11_08_0001
Revises: 2025_11_06_0001
Create Date: 2025-11-08

This migration:
1. Enables pgvector and pg_trgm extensions
2. Enhances icd10_codes table with new fields for semantic search
3. Creates icd10_ai_facets table for AI reasoning metadata
4. Creates code_mappings table for cross-system mappings
5. Creates icd10_relations table for code relationships
6. Creates icd10_synonyms table for alternative terms
7. Adds appropriate indexes for performance
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '2025_11_08_0001'
down_revision = '2025_11_06_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable required PostgreSQL extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')

    # ========================================
    # 1. Enhance icd10_codes table
    # ========================================

    # Add new columns to icd10_codes
    op.add_column('icd10_codes', sa.Column('code_system', sa.String(length=15), nullable=True))
    op.add_column('icd10_codes', sa.Column('short_desc', sa.Text(), nullable=True))
    op.add_column('icd10_codes', sa.Column('long_desc', sa.Text(), nullable=True))
    op.add_column('icd10_codes', sa.Column('chapter', sa.String(length=120), nullable=True))
    op.add_column('icd10_codes', sa.Column('block_range', sa.String(length=20), nullable=True))
    op.add_column('icd10_codes', sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))
    op.add_column('icd10_codes', sa.Column('version_year', sa.Integer(), nullable=True))
    op.add_column('icd10_codes', sa.Column('effective_date', sa.Date(), nullable=True))
    op.add_column('icd10_codes', sa.Column('expiry_date', sa.Date(), nullable=True))
    op.add_column('icd10_codes', sa.Column('embedding', postgresql.VECTOR(768), nullable=True))
    op.add_column('icd10_codes', sa.Column('last_updated', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')))

    # Migrate existing data: copy description to short_desc and set default code_system
    op.execute("UPDATE icd10_codes SET short_desc = description WHERE short_desc IS NULL")
    op.execute("UPDATE icd10_codes SET code_system = 'ICD10-CM' WHERE code_system IS NULL")

    # Now make code_system NOT NULL
    op.alter_column('icd10_codes', 'code_system', nullable=False)

    # Drop old unique constraint on code
    op.drop_constraint('icd10_codes_code_key', 'icd10_codes', type_='unique')

    # Create new composite unique index on code + code_system
    op.create_index('ix_icd10_code_system', 'icd10_codes', ['code', 'code_system'], unique=True)

    # Add check constraint for code_system
    op.create_check_constraint(
        'ck_icd10_code_system',
        'icd10_codes',
        "code_system IN ('ICD10', 'ICD10-CM', 'ICD10-PCS')"
    )

    # Update trigram index for new description fields
    op.drop_index('ix_icd10_description', table_name='icd10_codes')
    op.execute("""
        CREATE INDEX ix_icd10_description_trgm ON icd10_codes
        USING gin ((short_desc || ' ' || COALESCE(long_desc, '')) gin_trgm_ops)
    """)

    # Create IVFFlat index for vector similarity search
    op.execute("""
        CREATE INDEX ix_icd10_embedding_ivfflat ON icd10_codes
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)

    # ========================================
    # 2. Create icd10_ai_facets table
    # ========================================
    op.create_table(
        'icd10_ai_facets',
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('code_system', sa.String(length=15), nullable=False),
        sa.Column('concept_type', sa.String(length=40), nullable=True),
        sa.Column('body_system', sa.String(length=40), nullable=True),
        sa.Column('acuity', sa.String(length=40), nullable=True),
        sa.Column('severity', sa.String(length=40), nullable=True),
        sa.Column('chronicity', sa.String(length=40), nullable=True),
        sa.Column('laterality', sa.String(length=40), nullable=True),
        sa.Column('onset_context', sa.String(length=40), nullable=True),
        sa.Column('age_band', sa.String(length=40), nullable=True),
        sa.Column('sex_specific', sa.String(length=10), nullable=True),
        sa.Column('risk_flag', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('extra', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('code', 'code_system', name='pk_icd10_ai_facets')
    )

    # ========================================
    # 3. Create code_mappings table
    # ========================================
    op.create_table(
        'code_mappings',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('from_system', sa.String(length=20), nullable=False),
        sa.Column('from_code', sa.String(length=20), nullable=False),
        sa.Column('to_system', sa.String(length=20), nullable=False),
        sa.Column('to_code', sa.String(length=40), nullable=False),
        sa.Column('map_type', sa.String(length=30), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('source_name', sa.String(length=120), nullable=True),
        sa.Column('source_version', sa.String(length=40), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('reviewed_by', sa.String(length=120), nullable=True),
        sa.Column('review_note', sa.Text(), nullable=True),
        sa.Column('effective_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for code_mappings
    op.create_index('ix_code_mappings_from_system', 'code_mappings', ['from_system'])
    op.create_index('ix_code_mappings_from_code', 'code_mappings', ['from_code'])
    op.create_index('ix_code_mappings_to_system', 'code_mappings', ['to_system'])
    op.create_index('ix_code_mappings_to_code', 'code_mappings', ['to_code'])

    # ========================================
    # 4. Create icd10_relations table
    # ========================================
    op.create_table(
        'icd10_relations',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('related_code', sa.String(length=10), nullable=False),
        sa.Column('relation_type', sa.String(length=30), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for icd10_relations
    op.create_index('ix_icd10_relations_code', 'icd10_relations', ['code'])
    op.create_index('ix_icd10_relations_related_code', 'icd10_relations', ['related_code'])
    op.create_index('ix_icd10_relations_code_type', 'icd10_relations', ['code', 'relation_type'])
    op.create_index('ix_icd10_relations_related_type', 'icd10_relations', ['related_code', 'relation_type'])

    # ========================================
    # 5. Create icd10_synonyms table
    # ========================================
    op.create_table(
        'icd10_synonyms',
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('synonym', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('code', 'synonym')
    )

    # Create indexes for icd10_synonyms
    op.create_index('ix_icd10_synonyms_code', 'icd10_synonyms', ['code'])
    op.execute("""
        CREATE INDEX ix_icd10_synonyms_text ON icd10_synonyms
        USING gin (synonym gin_trgm_ops)
    """)


def downgrade() -> None:
    # Drop icd10_synonyms table
    op.drop_index('ix_icd10_synonyms_text', table_name='icd10_synonyms')
    op.drop_index('ix_icd10_synonyms_code', table_name='icd10_synonyms')
    op.drop_table('icd10_synonyms')

    # Drop icd10_relations table
    op.drop_index('ix_icd10_relations_related_type', table_name='icd10_relations')
    op.drop_index('ix_icd10_relations_code_type', table_name='icd10_relations')
    op.drop_index('ix_icd10_relations_related_code', table_name='icd10_relations')
    op.drop_index('ix_icd10_relations_code', table_name='icd10_relations')
    op.drop_table('icd10_relations')

    # Drop code_mappings table
    op.drop_index('ix_code_mappings_to_code', table_name='code_mappings')
    op.drop_index('ix_code_mappings_to_system', table_name='code_mappings')
    op.drop_index('ix_code_mappings_from_code', table_name='code_mappings')
    op.drop_index('ix_code_mappings_from_system', table_name='code_mappings')
    op.drop_table('code_mappings')

    # Drop icd10_ai_facets table
    op.drop_table('icd10_ai_facets')

    # Revert icd10_codes table changes
    op.execute('DROP INDEX IF EXISTS ix_icd10_embedding_ivfflat')
    op.execute('DROP INDEX IF EXISTS ix_icd10_description_trgm')

    # Recreate old description index
    op.execute("""
        CREATE INDEX ix_icd10_description ON icd10_codes
        USING gin (description gin_trgm_ops)
    """)

    op.drop_constraint('ck_icd10_code_system', 'icd10_codes', type_='check')
    op.drop_index('ix_icd10_code_system', table_name='icd10_codes')

    # Recreate old unique constraint
    op.create_unique_constraint('icd10_codes_code_key', 'icd10_codes', ['code'])

    # Drop new columns
    op.drop_column('icd10_codes', 'last_updated')
    op.drop_column('icd10_codes', 'embedding')
    op.drop_column('icd10_codes', 'expiry_date')
    op.drop_column('icd10_codes', 'effective_date')
    op.drop_column('icd10_codes', 'version_year')
    op.drop_column('icd10_codes', 'is_active')
    op.drop_column('icd10_codes', 'block_range')
    op.drop_column('icd10_codes', 'chapter')
    op.drop_column('icd10_codes', 'long_desc')
    op.drop_column('icd10_codes', 'short_desc')
    op.drop_column('icd10_codes', 'code_system')

    # Note: We don't drop the extensions as they might be used by other parts of the system
    # op.execute('DROP EXTENSION IF EXISTS pg_trgm')
    # op.execute('DROP EXTENSION IF EXISTS vector')
