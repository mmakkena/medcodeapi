"""add_multi_version_support_for_icd10_codes

Revision ID: 7787b0e5d54d
Revises: 2025_11_08_0001
Create Date: 2025-11-09 07:51:11.053146

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7787b0e5d54d'
down_revision = '2025_11_08_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Make version_year NOT NULL with default value of 2024
    # First, set existing NULL values to 2024
    op.execute("""
        UPDATE icd10_codes
        SET version_year = 2024
        WHERE version_year IS NULL
    """)

    # Step 2: Backfill effective_date and expiry_date for 2024 codes
    # FY 2024: October 1, 2023 - September 30, 2024
    op.execute("""
        UPDATE icd10_codes
        SET
            effective_date = '2023-10-01',
            expiry_date = '2024-09-30',
            is_active = true
        WHERE version_year = 2024
        AND effective_date IS NULL
    """)

    # Step 3: Drop the old unique constraint (code, code_system) if it exists
    # Make this idempotent - only drop if exists
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uix_icd10_code'
                AND conrelid = 'icd10_codes'::regclass
            ) THEN
                ALTER TABLE icd10_codes DROP CONSTRAINT uix_icd10_code;
            END IF;
        END $$;
    """)

    # Step 4: Create new unique constraint (code, code_system, version_year) if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uix_icd10_code_version'
                AND conrelid = 'icd10_codes'::regclass
            ) THEN
                ALTER TABLE icd10_codes ADD CONSTRAINT uix_icd10_code_version
                    UNIQUE (code, code_system, version_year);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Step 1: Drop the new unique constraint
    op.drop_constraint('uix_icd10_code_version', 'icd10_codes', type_='unique')

    # Step 2: Recreate the old unique constraint (code, code_system)
    # Note: This will fail if there are multiple versions of the same code
    # This is expected behavior - you can't downgrade if you have multi-version data
    op.create_unique_constraint(
        'uix_icd10_code',
        'icd10_codes',
        ['code', 'code_system']
    )

    # Step 3: Optionally clear version metadata
    # (Commented out to preserve data - uncomment if needed)
    # op.execute("""
    #     UPDATE icd10_codes
    #     SET
    #         version_year = NULL,
    #         effective_date = NULL,
    #         expiry_date = NULL
    # """)
