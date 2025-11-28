#!/usr/bin/env python3
"""
Load E/M Codes to PostgreSQL

Loads E/M (Evaluation & Management) code reference data from CDIAgent
JSON files into the PostgreSQL database.

Usage:
    python scripts/load_em_codes.py [--source PATH] [--generate-embeddings]

Source: CDIAgent/knowledge_base/em_codes/em_codes.json
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from infrastructure.db.postgres import SessionLocal, engine
from infrastructure.db.models.knowledge_base import EMCode

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default source path - CDIAgent is a sibling project
DEFAULT_SOURCE = Path("/Users/murali.local/CDIAgent/knowledge_base/em_codes/em_codes.json")


def load_em_codes_from_json(source_path: Path) -> list[dict]:
    """Load E/M codes from JSON file."""
    logger.info(f"Loading E/M codes from: {source_path}")

    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    with open(source_path, 'r') as f:
        data = json.load(f)

    logger.info(f"Loaded {len(data)} E/M codes from JSON")
    return data


def create_em_code_record(code_data: dict) -> EMCode:
    """Create an EMCode database record from JSON data."""
    time_range = code_data.get('time_range', [0, 0])

    return EMCode(
        code=code_data['code'],
        category=code_data['category'],
        level=code_data['level'],
        description=code_data['description'],
        setting=code_data['setting'],
        patient_type=code_data['patient_type'],
        mdm_level=code_data.get('mdm_level'),
        typical_time=code_data.get('typical_time'),
        time_range_min=time_range[0] if len(time_range) > 0 else None,
        time_range_max=time_range[1] if len(time_range) > 1 else None,
        reimbursement=code_data.get('reimbursement'),
        requirements=code_data.get('requirements'),
        mdm_criteria=code_data.get('mdm_criteria'),
        is_active=True,
        effective_date=datetime.utcnow()
    )


def load_em_codes(
    db: Session,
    source_path: Path,
    clear_existing: bool = False,
    generate_embeddings: bool = False
) -> int:
    """
    Load E/M codes into the database.

    Args:
        db: Database session
        source_path: Path to JSON source file
        clear_existing: Whether to clear existing records
        generate_embeddings: Whether to generate vector embeddings

    Returns:
        Number of records loaded
    """
    # Load data from JSON
    codes_data = load_em_codes_from_json(source_path)

    if clear_existing:
        logger.info("Clearing existing E/M codes...")
        db.query(EMCode).delete()
        db.commit()

    # Track stats
    created = 0
    updated = 0
    errors = 0

    for code_data in codes_data:
        try:
            code = code_data['code']

            # Check if code already exists
            existing = db.query(EMCode).filter(EMCode.code == code).first()

            if existing:
                # Update existing record
                existing.category = code_data['category']
                existing.level = code_data['level']
                existing.description = code_data['description']
                existing.setting = code_data['setting']
                existing.patient_type = code_data['patient_type']
                existing.mdm_level = code_data.get('mdm_level')
                existing.typical_time = code_data.get('typical_time')
                time_range = code_data.get('time_range', [0, 0])
                existing.time_range_min = time_range[0] if len(time_range) > 0 else None
                existing.time_range_max = time_range[1] if len(time_range) > 1 else None
                existing.reimbursement = code_data.get('reimbursement')
                existing.requirements = code_data.get('requirements')
                existing.mdm_criteria = code_data.get('mdm_criteria')
                existing.updated_at = datetime.utcnow()
                updated += 1
            else:
                # Create new record
                record = create_em_code_record(code_data)
                db.add(record)
                created += 1

        except Exception as e:
            logger.error(f"Error processing code {code_data.get('code')}: {e}")
            errors += 1

    db.commit()

    logger.info(f"E/M codes loaded: {created} created, {updated} updated, {errors} errors")

    # Generate embeddings if requested
    if generate_embeddings:
        logger.info("Generating embeddings for E/M codes...")
        generate_em_code_embeddings(db)

    return created + updated


def generate_em_code_embeddings(db: Session):
    """Generate vector embeddings for E/M codes."""
    try:
        from sentence_transformers import SentenceTransformer

        # Load MedCPT model (768-dim)
        logger.info("Loading embedding model...")
        model = SentenceTransformer('ncbi/MedCPT-Query-Encoder')

        # Get all codes without embeddings
        codes = db.query(EMCode).filter(EMCode.embedding == None).all()
        logger.info(f"Generating embeddings for {len(codes)} E/M codes...")

        for i, code in enumerate(codes):
            # Create text for embedding
            text = f"{code.code} {code.description} {code.category} MDM: {code.mdm_level}"

            # Generate embedding
            embedding = model.encode(text, normalize_embeddings=True)
            code.embedding = embedding.tolist()

            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i + 1}/{len(codes)} codes")
                db.commit()

        db.commit()
        logger.info("Embeddings generated successfully")

    except ImportError:
        logger.warning("sentence-transformers not installed. Skipping embedding generation.")
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")


def main():
    parser = argparse.ArgumentParser(description="Load E/M codes to PostgreSQL")
    parser.add_argument(
        '--source',
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Path to em_codes.json (default: {DEFAULT_SOURCE})"
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help="Clear existing E/M codes before loading"
    )
    parser.add_argument(
        '--generate-embeddings',
        action='store_true',
        help="Generate vector embeddings for semantic search"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("E/M Code Loader")
    logger.info("=" * 60)

    # Create database session
    db = SessionLocal()

    try:
        # Ensure table exists
        from infrastructure.db.models.knowledge_base import EMCode
        EMCode.__table__.create(engine, checkfirst=True)

        # Load codes
        count = load_em_codes(
            db,
            args.source,
            clear_existing=args.clear,
            generate_embeddings=args.generate_embeddings
        )

        logger.info(f"Successfully loaded {count} E/M codes")

    except Exception as e:
        logger.error(f"Failed to load E/M codes: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
