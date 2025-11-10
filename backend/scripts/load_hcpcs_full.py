#!/usr/bin/env python3
"""Load full HCPCS 2025 dataset (15,700 codes) into production database

This script is optimized for loading large datasets with:
- Batch processing (500 codes per batch)
- Progress tracking and ETA
- Duplicate detection
- Transaction safety
- Production database connection

Usage:
    # Local development
    python scripts/load_hcpcs_full.py

    # Production (via ECS task or direct connection)
    python scripts/load_hcpcs_full.py --env production

Data Source:
    data/procedure_codes/hcpcs_2025_full.csv (15,700 codes)
"""

import csv
import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime, date
from time import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.procedure_code import ProcedureCode
import uuid

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_csv_data(file_path: str) -> list[dict]:
    """Load procedure codes from CSV file

    Args:
        file_path: Path to CSV file

    Returns:
        List of procedure code dictionaries
    """
    codes = []

    logger.info(f"Reading CSV file: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            codes.append(row)

    logger.info(f"Loaded {len(codes):,} codes from CSV")
    return codes


def insert_procedure_codes(session, codes: list[dict], batch_size: int = 500):
    """Insert procedure codes into database with batch processing

    Args:
        session: Database session
        codes: List of code dictionaries from CSV
        batch_size: Number of codes to insert per batch (default: 500)

    Returns:
        Tuple of (inserted_count, skipped_count)
    """
    inserted = 0
    skipped = 0
    total = len(codes)
    start_time = time()

    logger.info(f"Starting batch insert ({batch_size} codes per batch)")
    logger.info("="*70)

    for i in range(0, total, batch_size):
        batch_start = time()
        batch = codes[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total + batch_size - 1) // batch_size

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

            # Calculate progress and ETA
            batch_time = time() - batch_start
            elapsed_time = time() - start_time
            codes_processed = i + len(batch)
            progress_pct = (codes_processed / total) * 100

            if codes_processed > 0:
                avg_time_per_code = elapsed_time / codes_processed
                remaining_codes = total - codes_processed
                eta_seconds = avg_time_per_code * remaining_codes
                eta_mins = eta_seconds / 60
            else:
                eta_mins = 0

            logger.info(
                f"Batch {batch_num}/{total_batches} ✓ | "
                f"Progress: {codes_processed:,}/{total:,} ({progress_pct:.1f}%) | "
                f"Inserted: {len(batch)} | "
                f"Time: {batch_time:.2f}s | "
                f"ETA: {eta_mins:.1f}m"
            )

        except Exception as e:
            session.rollback()
            logger.error(f"Error in batch {batch_num}: {e}")
            raise

    total_time = time() - start_time
    logger.info("="*70)
    logger.info(f"Batch processing completed in {total_time:.2f}s ({total_time/60:.2f}m)")

    return inserted, skipped


def get_database_stats(session):
    """Get current database statistics

    Args:
        session: Database session

    Returns:
        Dictionary with statistics
    """
    stats = {
        'total_codes': session.query(ProcedureCode).count(),
        'cpt_codes': session.query(ProcedureCode).filter_by(code_system='CPT').count(),
        'hcpcs_codes': session.query(ProcedureCode).filter_by(code_system='HCPCS').count(),
        'year_2025': session.query(ProcedureCode).filter_by(version_year=2025).count(),
        'free_codes': session.query(ProcedureCode).filter_by(license_status='free').count(),
        'licensed_codes': session.query(ProcedureCode).filter_by(license_status='AMA_licensed').count(),
    }
    return stats


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Load full HCPCS 2025 dataset into database"
    )
    parser.add_argument(
        "--env",
        type=str,
        choices=['development', 'production'],
        default='development',
        help="Environment (development or production)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Batch size for inserts (default: 500)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run - don't actually insert data"
    )

    args = parser.parse_args()

    # Print header
    logger.info("="*70)
    logger.info("HCPCS 2025 Full Dataset Loader")
    logger.info("="*70)
    logger.info(f"Environment: {args.env}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info("="*70)
    logger.info("")

    # Get data file path
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / 'data' / 'procedure_codes'
    csv_file = data_dir / 'hcpcs_2025_full.csv'

    # Check if file exists
    if not csv_file.exists():
        logger.error(f"Data file not found: {csv_file}")
        logger.info("\nPlease ensure HCPCS data has been downloaded and converted:")
        logger.info("  1. python scripts/download_procedure_data.py --hcpcs-only --year 2025")
        logger.info("  2. python scripts/convert_hcpcs_to_csv.py --year 2025")
        return 1

    logger.info(f"📁 Data file: {csv_file}")
    logger.info(f"   Size: {csv_file.stat().st_size:,} bytes\n")

    # Load CSV data
    try:
        codes = load_csv_data(str(csv_file))
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        return 1

    if args.dry_run:
        logger.info("\n🔍 DRY RUN MODE - No data will be inserted")
        logger.info(f"Would process {len(codes):,} codes in batches of {args.batch_size}")
        logger.info("\nSample codes:")
        for i, code in enumerate(codes[:5], 1):
            logger.info(f"  {i}. {code['code']:6} - {code['paraphrased_desc'][:60]}")
        return 0

    # Create database connection
    logger.info(f"🔗 Connecting to database...")
    try:
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        logger.info("   Connected successfully\n")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return 1

    try:
        # Get pre-load statistics
        logger.info("📊 Pre-load database statistics:")
        pre_stats = get_database_stats(session)
        for key, value in pre_stats.items():
            logger.info(f"   {key.replace('_', ' ').title()}: {value:,}")
        logger.info("")

        # Insert codes
        logger.info(f"📥 Inserting {len(codes):,} HCPCS codes...")
        logger.info("")

        inserted, skipped = insert_procedure_codes(session, codes, batch_size=args.batch_size)

        # Get post-load statistics
        logger.info("")
        logger.info("📊 Post-load database statistics:")
        post_stats = get_database_stats(session)
        for key, value in post_stats.items():
            logger.info(f"   {key.replace('_', ' ').title()}: {value:,}")
        logger.info("")

        # Summary
        logger.info("="*70)
        logger.info("✅ LOADING COMPLETED SUCCESSFULLY")
        logger.info("="*70)
        logger.info(f"Total codes in CSV: {len(codes):,}")
        logger.info(f"Inserted: {inserted:,}")
        logger.info(f"Skipped (duplicates): {skipped:,}")
        logger.info(f"Database total: {post_stats['total_codes']:,} procedure codes")
        logger.info("")
        logger.info("📈 Breakdown:")
        logger.info(f"   CPT codes: {post_stats['cpt_codes']:,}")
        logger.info(f"   HCPCS codes: {post_stats['hcpcs_codes']:,}")
        logger.info(f"   Year 2025: {post_stats['year_2025']:,}")
        logger.info(f"   Free tier: {post_stats['free_codes']:,}")
        logger.info(f"   Licensed: {post_stats['licensed_codes']:,}")
        logger.info("")
        logger.info("📋 Next steps:")
        logger.info("   1. Generate embeddings: python scripts/generate_procedure_embeddings.py")
        logger.info("   2. Populate facets: python scripts/populate_procedure_facets.py")
        logger.info("="*70)

        return 0

    except Exception as e:
        logger.error(f"\n❌ Error during loading: {e}")
        session.rollback()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
