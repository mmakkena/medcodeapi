#!/usr/bin/env python3
"""
Generate embeddings for ICD-10 codes

This script generates MedCPT embeddings for all ICD-10 codes in the database.
It processes codes in batches for efficiency and can resume from interruptions.

Requirements:
- sentence-transformers
- torch
- Database with ICD-10 codes loaded
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from tqdm import tqdm

from app.database import Base
from app.models.icd10_code import ICD10Code
from app.services.embedding_service import generate_embeddings_batch

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_url() -> str:
    """Get database URL from environment or use default."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/medcodeapi"
    )


def create_embedding_text(code: ICD10Code) -> str:
    """
    Create text for embedding generation from ICD-10 code.

    Combines code, descriptions, and year-specific guideline information
    for better semantic representation.

    Args:
        code: ICD10Code object

    Returns:
        Text string for embedding
    """
    parts = []

    # Add code
    parts.append(f"Code: {code.code}")

    # Add short description
    if code.short_desc:
        parts.append(code.short_desc)

    # Add long description if different from short
    if code.long_desc and code.long_desc != code.short_desc:
        parts.append(code.long_desc)

    # Add chapter for context
    if code.chapter:
        parts.append(f"({code.chapter})")

    # Add year-specific guideline information
    if code.coding_guidelines:
        parts.append(f"Guidelines: {code.coding_guidelines}")

    if code.clinical_notes:
        parts.append(f"Clinical context: {code.clinical_notes}")

    if code.coding_tips:
        parts.append(f"Coding tips: {code.coding_tips}")

    # Add version year for temporal context
    if code.version_year:
        parts.append(f"(FY {code.version_year})")

    # Join and truncate to prevent extremely long texts
    # MedCPT can handle long text, but truncating saves memory and processing time
    text = " ".join(parts)

    # Limit to ~512 tokens (roughly 2000 characters)
    # This is a good balance between context and performance
    MAX_LENGTH = 2000
    if len(text) > MAX_LENGTH:
        text = text[:MAX_LENGTH] + "..."

    return text


def generate_embeddings_for_codes(
    db: Session,
    batch_size: int = 32,
    code_system: str = "ICD10-CM",
    skip_existing: bool = True,
    year: Optional[int] = None
) -> int:
    """
    Generate embeddings for all codes in the database using streaming/chunked processing.

    OPTIMIZED VERSION:
    - Streams data in chunks instead of loading all into memory
    - Reduces memory usage from ~1-2GB to ~100-200MB
    - Adds garbage collection to prevent memory leaks
    - Supports large datasets (100k+ codes)

    Args:
        db: Database session
        batch_size: Number of codes to process at once
        code_system: Code system to process
        skip_existing: Skip codes that already have embeddings
        year: Filter by version_year (optional)

    Returns:
        Number of codes processed
    """
    import gc

    # Build query for codes without embeddings
    query = db.query(ICD10Code).filter(ICD10Code.code_system == code_system)

    # Filter by year if specified
    if year is not None:
        query = query.filter(ICD10Code.version_year == year)

    if skip_existing:
        query = query.filter(ICD10Code.embedding.is_(None))

    # Get total count without loading all data
    total_codes = query.count()

    if total_codes == 0:
        logger.info("No codes to process")
        return 0

    logger.info(f"Processing {total_codes} codes (year: {year or 'all'})...")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Memory optimization: Streaming mode enabled")

    processed = 0

    # Chunk size for streaming (load this many codes at a time)
    CHUNK_SIZE = 1000

    # Process in chunks with progress bar
    with tqdm(total=total_codes, desc="Generating embeddings", unit="code") as pbar:
        for offset in range(0, total_codes, CHUNK_SIZE):
            # Load chunk of codes
            chunk_codes = query.offset(offset).limit(CHUNK_SIZE).all()

            if not chunk_codes:
                break

            # Process chunk in batches
            for i in range(0, len(chunk_codes), batch_size):
                batch = chunk_codes[i:i + batch_size]

                # Create texts for embedding (with truncation)
                texts = [create_embedding_text(code) for code in batch]

                try:
                    # Generate embeddings
                    embeddings = generate_embeddings_batch(texts, batch_size=batch_size)

                    # Update codes with embeddings
                    for code, embedding in zip(batch, embeddings):
                        code.embedding = embedding
                        code.last_updated = datetime.utcnow()

                    # Commit batch
                    db.commit()

                    processed += len(batch)
                    pbar.update(len(batch))

                    # Log progress every 10 batches
                    if (processed % (batch_size * 10)) == 0:
                        logger.info(f"Progress: {processed}/{total_codes} codes ({(processed/total_codes*100):.1f}%)")

                except Exception as e:
                    logger.error(f"Error processing batch at offset {offset + i}: {e}")
                    db.rollback()
                    # Continue with next batch
                    continue

            # Clear chunk from memory and run garbage collection every chunk
            del chunk_codes
            gc.collect()

    logger.info(f"✓ Processed {processed} codes")

    return processed


def verify_embeddings(db: Session, code_system: str = "ICD10-CM") -> dict:
    """
    Verify embedding generation results.

    Args:
        db: Database session
        code_system: Code system to verify

    Returns:
        Dictionary with verification stats
    """
    total_codes = db.query(ICD10Code).filter(
        ICD10Code.code_system == code_system
    ).count()

    codes_with_embeddings = db.query(ICD10Code).filter(
        and_(
            ICD10Code.code_system == code_system,
            ICD10Code.embedding.isnot(None)
        )
    ).count()

    codes_without_embeddings = total_codes - codes_with_embeddings

    return {
        'total_codes': total_codes,
        'with_embeddings': codes_with_embeddings,
        'without_embeddings': codes_without_embeddings,
        'coverage_percent': (codes_with_embeddings / total_codes * 100) if total_codes > 0 else 0
    }


def show_sample_embeddings(db: Session, limit: int = 5):
    """
    Show sample codes with embeddings for verification.

    Args:
        db: Database session
        limit: Number of samples to show
    """
    codes = db.query(ICD10Code).filter(
        ICD10Code.embedding.isnot(None)
    ).limit(limit).all()

    logger.info(f"\nSample codes with embeddings:")

    for code in codes:
        embedding_preview = code.embedding[:5] if code.embedding else None
        logger.info(f"\n  Code: {code.code}")
        logger.info(f"  Description: {code.short_desc}")
        logger.info(f"  Embedding (first 5 dims): {embedding_preview}")
        logger.info(f"  Embedding dimension: {len(code.embedding) if code.embedding else 0}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate MedCPT embeddings for ICD-10 codes"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Number of codes to process in each batch (default: 32)"
    )
    parser.add_argument(
        "--code-system",
        type=str,
        default="ICD10-CM",
        help="Code system to process (default: ICD10-CM)"
    )
    parser.add_argument(
        "--db-url",
        type=str,
        help="Database URL (default: from DATABASE_URL env or local postgres)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate embeddings even if they already exist"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing embeddings, don't generate new ones"
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Show sample embeddings after generation"
    )
    parser.add_argument(
        "--year",
        type=int,
        help="Filter by version year (e.g., 2024, 2025, 2026)"
    )

    args = parser.parse_args()

    # Connect to database
    db_url = args.db_url or get_database_url()
    logger.info(f"Connecting to database...")

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Verify existing embeddings
        logger.info(f"\nChecking current embedding status...")
        stats = verify_embeddings(db, args.code_system)

        logger.info(f"\nCurrent status:")
        logger.info(f"  Total codes: {stats['total_codes']}")
        logger.info(f"  With embeddings: {stats['with_embeddings']}")
        logger.info(f"  Without embeddings: {stats['without_embeddings']}")
        logger.info(f"  Coverage: {stats['coverage_percent']:.1f}%")

        if args.verify_only:
            logger.info("\nVerify-only mode - exiting")
            return 0

        if stats['without_embeddings'] == 0 and not args.force:
            logger.info("\n✓ All codes already have embeddings")
            logger.info("  Use --force to regenerate embeddings")
            return 0

        # Generate embeddings
        logger.info(f"\n{'Regenerating' if args.force else 'Generating'} embeddings...")

        start_time = datetime.now()

        processed = generate_embeddings_for_codes(
            db,
            batch_size=args.batch_size,
            code_system=args.code_system,
            skip_existing=not args.force,
            year=args.year  # FIX: Pass year parameter so it actually filters!
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Verify again
        stats = verify_embeddings(db, args.code_system)

        logger.info(f"\n✓ Embedding generation complete!")
        logger.info(f"  Codes processed: {processed}")
        logger.info(f"  Duration: {duration:.1f} seconds")
        logger.info(f"  Rate: {processed/duration:.1f} codes/second")
        logger.info(f"\nFinal status:")
        logger.info(f"  Total codes: {stats['total_codes']}")
        logger.info(f"  With embeddings: {stats['with_embeddings']}")
        logger.info(f"  Coverage: {stats['coverage_percent']:.1f}%")

        # Show samples if requested
        if args.sample:
            show_sample_embeddings(db, limit=5)

        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
