"""Enhance CPT/HCPCS with semantic search, licensing, and facets

Revision ID: 2025_11_10_0001
Revises: 4b4e517c47de
Create Date: 2025-11-10

This migration:
1. Creates procedure_codes table (replaces simple cpt_codes)
2. Creates procedure_code_synonyms table for alternative terms
3. Creates procedure_code_facets table for AI reasoning metadata
4. Adds vector embeddings support (MedCPT 768-dim)
5. Adds licensing support (free paraphrased vs AMA licensed)
6. Adds multi-year version support
7. Migrates existing cpt_codes data to new schema (if exists)
8. Creates appropriate indexes for semantic and keyword search
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic
revision = '2025_11_10_0001'
down_revision = '4b4e517c47de'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========================================
    # 0. Ensure required PostgreSQL extensions
    # ========================================
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ========================================
    # 1. Create procedure_codes table
    # ========================================
    op.create_table(
        'procedure_codes',
        # Primary identifiers
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('code_system', sa.String(length=10), nullable=False, server_default='CPT'),

        # Dual description strategy for licensing compliance
        sa.Column('paraphrased_desc', sa.Text(), nullable=True,
                  comment='Free paraphrased description (no license required)'),
        sa.Column('short_desc', sa.Text(), nullable=True,
                  comment='Official short descriptor (AMA licensed for CPT)'),
        sa.Column('long_desc', sa.Text(), nullable=True,
                  comment='Official long descriptor (AMA licensed for CPT)'),

        # Classification and categorization
        sa.Column('category', sa.String(length=50), nullable=True,
                  comment='E/M, Surgery, Radiology, Pathology, Medicine, etc.'),
        sa.Column('procedure_type', sa.String(length=30), nullable=True,
                  comment='diagnostic, therapeutic, preventive, screening'),

        # Versioning and lifecycle management
        sa.Column('version_year', sa.Integer(), nullable=False, server_default='2025',
                  comment='CPT version year (e.g., 2024, 2025)'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true',
                  comment='Whether code is currently active'),
        sa.Column('effective_date', sa.Date(), nullable=True,
                  comment='Date when code becomes effective'),
        sa.Column('expiry_date', sa.Date(), nullable=True,
                  comment='Date when code is retired/expires'),

        # Licensing and compliance
        sa.Column('license_status', sa.String(length=20), nullable=False, server_default='free',
                  comment='free (paraphrased) or AMA_licensed (official text)'),

        # Usage and billing metadata
        sa.Column('relative_value_units', sa.Text(), nullable=True,
                  comment='RVU information (work, practice expense, malpractice)'),
        sa.Column('global_period', sa.String(length=10), nullable=True,
                  comment='Global surgery period (000, 010, 090, XXX, YYY, ZZZ, MMM)'),
        sa.Column('modifier_51_exempt', sa.Boolean(), nullable=False, server_default='false',
                  comment='Whether code is exempt from multiple procedure reduction'),

        # Semantic search
        sa.Column('embedding', postgresql.VECTOR(768), nullable=True,
                  comment='MedCPT 768-dimensional embedding for semantic search'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_updated', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),

        # Legacy fields for backward compatibility
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True,
                  comment='PostgreSQL full-text search vector'),
    )

    # Add unique constraint for code + code_system + version_year
    op.create_unique_constraint(
        'uq_procedure_code_system_year',
        'procedure_codes',
        ['code', 'code_system', 'version_year']
    )

    # Add check constraints
    op.create_check_constraint(
        'ck_procedure_code_system',
        'procedure_codes',
        "code_system IN ('CPT', 'HCPCS')"
    )

    op.create_check_constraint(
        'ck_procedure_license_status',
        'procedure_codes',
        "license_status IN ('free', 'AMA_licensed')"
    )

    # Create indexes for procedure_codes
    # Compound index for common queries
    op.create_index('ix_procedure_code_system', 'procedure_codes', ['code', 'code_system'])
    op.create_index('ix_procedure_code', 'procedure_codes', ['code'])
    op.create_index('ix_procedure_category', 'procedure_codes', ['category'])
    op.create_index('ix_procedure_version_year', 'procedure_codes', ['version_year'])
    op.create_index('ix_procedure_active', 'procedure_codes', ['is_active'])

    # Full-text search indexes (GIN trigram)
    op.execute("""
        CREATE INDEX ix_procedure_text_gin ON procedure_codes
        USING gin (
            (COALESCE(paraphrased_desc, '') || ' ' || COALESCE(short_desc, '')) gin_trgm_ops
        )
    """)

    # Vector similarity search index (IVFFlat with cosine distance)
    op.execute("""
        CREATE INDEX ix_procedure_embedding_ivfflat ON procedure_codes
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)

    # Full-text search vector index
    op.create_index('ix_procedure_search_vector', 'procedure_codes', ['search_vector'],
                   postgresql_using='gin')

    # ========================================
    # 2. Create procedure_code_synonyms table
    # ========================================
    op.create_table(
        'procedure_code_synonyms',
        sa.Column('code', sa.String(length=10), nullable=False,
                  comment='CPT or HCPCS code'),
        sa.Column('code_system', sa.String(length=10), nullable=False,
                  comment='CPT or HCPCS'),
        sa.Column('synonym', sa.Text(), nullable=False,
                  comment='Alternative term or lay language description'),
        sa.PrimaryKeyConstraint('code', 'code_system', 'synonym',
                               name='pk_procedure_code_synonyms')
    )

    # Create indexes for synonyms
    op.create_index('ix_procedure_synonyms_code_system', 'procedure_code_synonyms',
                   ['code', 'code_system'])

    # Full-text search index on synonyms for fuzzy matching
    op.execute("""
        CREATE INDEX ix_procedure_synonyms_text ON procedure_code_synonyms
        USING gin (synonym gin_trgm_ops)
    """)

    # ========================================
    # 3. Create procedure_code_facets table
    # ========================================
    op.create_table(
        'procedure_code_facets',
        # Composite primary key
        sa.Column('code', sa.String(length=10), nullable=False,
                  comment='CPT or HCPCS code'),
        sa.Column('code_system', sa.String(length=10), nullable=False,
                  comment='CPT or HCPCS'),

        # Anatomical and body system classification
        sa.Column('body_region', sa.String(length=50), nullable=True,
                  comment='head_neck, thorax, abdomen, pelvis, spine, upper_extremity, lower_extremity, etc.'),
        sa.Column('body_system', sa.String(length=50), nullable=True,
                  comment='cardiovascular, respiratory, digestive, musculoskeletal, nervous, etc.'),

        # Procedure classification
        sa.Column('procedure_category', sa.String(length=50), nullable=True,
                  comment='evaluation, surgical, diagnostic_imaging, laboratory, therapeutic, preventive'),
        sa.Column('procedure_type', sa.String(length=30), nullable=True,
                  comment='diagnostic, therapeutic, preventive, screening, palliative'),

        # Complexity and resource intensity
        sa.Column('complexity_level', sa.String(length=20), nullable=True,
                  comment='simple, moderate, complex, highly_complex'),
        sa.Column('typical_duration_mins', sa.Integer(), nullable=True,
                  comment='Typical procedure duration in minutes'),
        sa.Column('relative_complexity_score', sa.Integer(), nullable=True,
                  comment='1-10 scale for procedure complexity'),

        # Anesthesia information
        sa.Column('anesthesia_type', sa.String(length=30), nullable=True,
                  comment='none, local, regional, monitored, general'),
        sa.Column('anesthesia_base_units', sa.Integer(), nullable=True,
                  comment='Base anesthesia units for billing'),

        # Service setting and context
        sa.Column('service_location', sa.String(length=40), nullable=True,
                  comment='office, hospital_inpatient, hospital_outpatient, emergency, etc.'),
        sa.Column('provider_type', sa.String(length=50), nullable=True,
                  comment='physician, surgeon, nurse_practitioner, physician_assistant, etc.'),

        # Clinical and billing attributes
        sa.Column('is_bilateral', sa.Boolean(), nullable=False, server_default='false',
                  comment='Whether procedure can be performed bilaterally'),
        sa.Column('requires_modifier', sa.Boolean(), nullable=False, server_default='false',
                  comment='Whether code commonly requires modifiers'),
        sa.Column('age_specific', sa.Boolean(), nullable=False, server_default='false',
                  comment='Whether code is age-restricted'),
        sa.Column('gender_specific', sa.String(length=10), nullable=True,
                  comment='male, female, both, unspecified'),

        # Special procedure flags
        sa.Column('is_add_on_code', sa.Boolean(), nullable=False, server_default='false',
                  comment='CPT add-on code (cannot be billed alone)'),
        sa.Column('is_unlisted_code', sa.Boolean(), nullable=False, server_default='false',
                  comment='Unlisted procedure code'),
        sa.Column('requires_special_report', sa.Boolean(), nullable=False, server_default='false',
                  comment='Requires special documentation'),

        # E/M specific fields
        sa.Column('em_level', sa.String(length=20), nullable=True,
                  comment='For E/M codes: level 1-5, critical_care, consultation'),
        sa.Column('em_patient_type', sa.String(length=30), nullable=True,
                  comment='new_patient, established_patient, inpatient, outpatient'),

        # Surgical procedure fields
        sa.Column('surgical_approach', sa.String(length=40), nullable=True,
                  comment='open, laparoscopic, endoscopic, percutaneous, robotic'),
        sa.Column('is_major_surgery', sa.Boolean(), nullable=False, server_default='false',
                  comment='Whether classified as major surgical procedure'),

        # Imaging/Radiology fields
        sa.Column('imaging_modality', sa.String(length=40), nullable=True,
                  comment='xray, ct, mri, ultrasound, nuclear_medicine, pet'),
        sa.Column('uses_contrast', sa.Boolean(), nullable=False, server_default='false',
                  comment='Whether imaging uses contrast material'),

        # Additional flexible metadata
        sa.Column('extra', postgresql.JSONB(astext_type=sa.Text()), nullable=True,
                  comment='Additional flexible metadata in JSON format'),

        sa.PrimaryKeyConstraint('code', 'code_system',
                               name='pk_procedure_code_facets')
    )

    # Create indexes for faceted search
    op.create_index('ix_procedure_facets_body_region', 'procedure_code_facets', ['body_region'])
    op.create_index('ix_procedure_facets_complexity', 'procedure_code_facets', ['complexity_level'])
    op.create_index('ix_procedure_facets_category', 'procedure_code_facets', ['procedure_category'])
    op.create_index('ix_procedure_facets_location', 'procedure_code_facets', ['service_location'])
    op.create_index('ix_procedure_facets_em_level', 'procedure_code_facets', ['em_level'])

    # Composite indexes for common query patterns
    op.create_index('ix_procedure_facets_body_system_category', 'procedure_code_facets',
                   ['body_system', 'procedure_category'])
    op.create_index('ix_procedure_facets_category_complexity', 'procedure_code_facets',
                   ['procedure_category', 'complexity_level'])

    # ========================================
    # 4. Migrate existing cpt_codes data (if table exists)
    # ========================================
    # Check if old cpt_codes table exists and migrate data
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'cpt_codes' in inspector.get_table_names():
        print("Migrating data from old cpt_codes table to procedure_codes...")

        # Migrate existing CPT codes to new schema
        # Map old 'description' field to 'paraphrased_desc' (free tier)
        op.execute("""
            INSERT INTO procedure_codes
                (id, code, code_system, paraphrased_desc, category, version_year,
                 is_active, license_status, created_at, last_updated)
            SELECT
                id,
                code,
                'CPT' as code_system,
                description as paraphrased_desc,
                category,
                2024 as version_year,
                true as is_active,
                'free' as license_status,
                CURRENT_TIMESTAMP as created_at,
                CURRENT_TIMESTAMP as last_updated
            FROM cpt_codes
            ON CONFLICT (code, code_system, version_year) DO NOTHING
        """)

        print("Migration completed. Old cpt_codes table can be manually dropped if desired.")


def downgrade() -> None:
    """Downgrade: Remove new procedure code tables and restore old schema"""

    # Drop facets table
    op.drop_table('procedure_code_facets')

    # Drop synonyms table
    op.drop_table('procedure_code_synonyms')

    # Drop procedure_codes table
    op.drop_table('procedure_codes')

    # Note: We don't restore the old cpt_codes table as it may still exist
    # If you want to fully rollback, manually restore from backup
