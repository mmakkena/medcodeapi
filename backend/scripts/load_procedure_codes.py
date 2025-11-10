"""Load procedure codes (CPT/HCPCS) from bundled CSV files into database

This script reads CPT and HCPCS data from local CSV files that are bundled
with the Docker image, ensuring reliable and fast data loading.

Usage:
    python scripts/load_procedure_codes.py

Data files:
    - data/procedure_codes/cpt_2025_sample.csv (151 CPT codes)
    - data/procedure_codes/hcpcs_2025_sample.csv (16 HCPCS codes)
"""

import csv
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.procedure_code import ProcedureCode
import uuid
from datetime import datetime, date


def load_csv_data(file_path: str) -> list[dict]:
    """Load procedure codes from CSV file

    Args:
        file_path: Path to CSV file

    Returns:
        List of procedure code dictionaries
    """
    codes = []

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            codes.append(row)

    return codes


def insert_procedure_codes(session, codes: list[dict], batch_size: int = 100):
    """Insert procedure codes into database

    Args:
        session: Database session
        codes: List of code dictionaries from CSV
        batch_size: Number of codes to insert per batch
    """
    inserted = 0
    skipped = 0

    for i in range(0, len(codes), batch_size):
        batch = codes[i:i + batch_size]

        for code_data in batch:
            # Check if code already exists
            existing = session.query(ProcedureCode).filter_by(
                code=code_data['code'],
                code_system=code_data['code_system'],
                version_year=int(code_data['version_year'])
            ).first()

            if existing:
                skipped += 1
                continue

            # Create new procedure code
            procedure_code = ProcedureCode(
                id=uuid.uuid4(),
                code=code_data['code'],
                code_system=code_data['code_system'],
                paraphrased_desc=code_data['paraphrased_desc'] if code_data['paraphrased_desc'] else None,
                short_desc=code_data.get('short_desc') if code_data.get('short_desc') else None,
                category=code_data.get('category'),
                license_status=code_data.get('license_status', 'free'),
                version_year=int(code_data['version_year']),
                is_active=True,
                effective_date=date(2025, 1, 1),  # FY 2025 starts Jan 1, 2025
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )

            session.add(procedure_code)
            inserted += 1

        # Commit batch
        try:
            session.commit()
            print(f"  ✓ Processed batch {i//batch_size + 1}: {len(batch)} codes")
        except Exception as e:
            session.rollback()
            print(f"  ✗ Error in batch {i//batch_size + 1}: {e}")
            raise

    return inserted, skipped


def main():
    """Main loader function"""
    print("=" * 70)
    print("Procedure Code Loader")
    print("=" * 70)

    # Get data directory
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / 'data' / 'procedure_codes'

    # Check if data files exist
    cpt_file = data_dir / 'cpt_2025_sample.csv'
    hcpcs_file = data_dir / 'hcpcs_2025_sample.csv'

    if not cpt_file.exists():
        print(f"✗ CPT data file not found: {cpt_file}")
        return 1

    if not hcpcs_file.exists():
        print(f"✗ HCPCS data file not found: {hcpcs_file}")
        return 1

    print(f"\n📁 Data files:")
    print(f"   CPT:   {cpt_file}")
    print(f"   HCPCS: {hcpcs_file}")

    # Create database engine
    print(f"\n🔗 Connecting to database...")
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Check current count
        current_count = session.query(ProcedureCode).count()
        print(f"   Current procedure codes in database: {current_count}")

        # Load CPT codes
        print(f"\n📥 Loading CPT codes from CSV...")
        cpt_codes = load_csv_data(str(cpt_file))
        print(f"   Found {len(cpt_codes)} CPT codes in file")

        cpt_inserted, cpt_skipped = insert_procedure_codes(session, cpt_codes)
        print(f"   ✓ Inserted: {cpt_inserted}")
        print(f"   ⊘ Skipped (already exist): {cpt_skipped}")

        # Load HCPCS codes
        print(f"\n📥 Loading HCPCS codes from CSV...")
        hcpcs_codes = load_csv_data(str(hcpcs_file))
        print(f"   Found {len(hcpcs_codes)} HCPCS codes in file")

        hcpcs_inserted, hcpcs_skipped = insert_procedure_codes(session, hcpcs_codes)
        print(f"   ✓ Inserted: {hcpcs_inserted}")
        print(f"   ⊘ Skipped (already exist): {hcpcs_skipped}")

        # Final count
        final_count = session.query(ProcedureCode).count()
        print(f"\n📊 Summary:")
        print(f"   Total codes processed: {len(cpt_codes) + len(hcpcs_codes)}")
        print(f"   Total inserted: {cpt_inserted + hcpcs_inserted}")
        print(f"   Total skipped: {cpt_skipped + hcpcs_skipped}")
        print(f"   Database total: {final_count} procedure codes")

        # Category breakdown
        print(f"\n📈 Breakdown by code system:")
        cpt_count = session.query(ProcedureCode).filter_by(code_system='CPT').count()
        hcpcs_count = session.query(ProcedureCode).filter_by(code_system='HCPCS').count()
        print(f"   CPT:   {cpt_count} codes")
        print(f"   HCPCS: {hcpcs_count} codes")

        print(f"\n✅ Loading completed successfully!")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"\n✗ Error: {e}")
        session.rollback()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
