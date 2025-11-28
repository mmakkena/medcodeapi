#!/usr/bin/env python3
"""
Master Migration Script for CDI Agent Knowledge Base

Runs all data migrations to load CDI Agent knowledge base data
into PostgreSQL with vector embeddings for semantic search.

Usage:
    # Local development
    python scripts/migrate_cdi_agent_data.py [--all] [--em-codes] [--protocols] [--guidelines]

    # ECS with S3 source
    python scripts/migrate_cdi_agent_data.py --all --use-s3

    # Or set environment variable
    CDI_USE_S3=true python scripts/migrate_cdi_agent_data.py --all

This script loads:
1. E/M Codes: Evaluation & Management coding reference
2. Investigation Protocols: Clinical investigation guidelines
3. CDI Guidelines: Document-based CDI best practices

Source: Local CDIAgent directory or S3 bucket
Target: PostgreSQL with pgvector

Environment Variables:
    CDI_USE_S3: Set to "true" to use S3 as data source
    CDI_S3_BUCKET: S3 bucket name (default: nuvii-data-793523315434)
    CDI_S3_PREFIX: S3 key prefix (default: cdi-knowledge-base)
    CDI_LOCAL_ROOT: Local CDIAgent root path
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from infrastructure.db.postgres import SessionLocal, engine, Base
from infrastructure.db.models.knowledge_base import (
    EMCode, InvestigationProtocol, CDIGuideline, DRGRule, BillingNote
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default paths - CDIAgent is a sibling project
CDIAGENT_ROOT = Path("/Users/murali.local/CDIAgent")
EM_CODES_PATH = CDIAGENT_ROOT / "knowledge_base" / "em_codes" / "em_codes.json"
INVESTIGATIONS_PATH = CDIAGENT_ROOT / "knowledge_base" / "investigations"
CDI_DOCUMENTS_PATH = CDIAGENT_ROOT / "cdi_documents"

# Global flag for S3 usage
USE_S3 = False


def setup_data_paths(use_s3: bool = False) -> dict:
    """
    Setup data paths, downloading from S3 if needed.

    Args:
        use_s3: Force S3 usage

    Returns:
        Dict with paths to data sources
    """
    global EM_CODES_PATH, INVESTIGATIONS_PATH, CDI_DOCUMENTS_PATH, USE_S3

    USE_S3 = use_s3 or os.environ.get("CDI_USE_S3", "false").lower() == "true"

    if USE_S3:
        logger.info("Using S3 as data source")
        from scripts.s3_data_utils import (
            get_em_codes_path,
            get_investigations_path,
            get_cdi_documents_path
        )

        EM_CODES_PATH = get_em_codes_path()
        INVESTIGATIONS_PATH = get_investigations_path()
        CDI_DOCUMENTS_PATH = get_cdi_documents_path()
    else:
        logger.info("Using local data source")

    return {
        'em_codes': EM_CODES_PATH,
        'investigations': INVESTIGATIONS_PATH,
        'cdi_documents': CDI_DOCUMENTS_PATH,
    }


def create_tables():
    """Create knowledge base tables if they don't exist."""
    logger.info("Creating knowledge base tables...")

    tables = [
        EMCode.__table__,
        InvestigationProtocol.__table__,
        CDIGuideline.__table__,
        DRGRule.__table__,
        BillingNote.__table__,
    ]

    for table in tables:
        table.create(engine, checkfirst=True)
        logger.info(f"  Table '{table.name}' ready")


def verify_source_paths() -> dict:
    """Verify that source data paths exist."""
    paths = {
        'em_codes': EM_CODES_PATH,
        'investigations': INVESTIGATIONS_PATH,
        'cdi_documents': CDI_DOCUMENTS_PATH,
    }

    results = {}
    for name, path in paths.items():
        exists = path.exists()
        results[name] = exists
        status = "OK" if exists else "MISSING"
        logger.info(f"  {name}: {path} [{status}]")

    return results


def load_em_codes(db: Session, generate_embeddings: bool = False) -> int:
    """Load E/M codes."""
    from scripts.load_em_codes import load_em_codes as _load_em_codes

    logger.info("Loading E/M codes...")
    return _load_em_codes(
        db,
        EM_CODES_PATH,
        clear_existing=True,
        generate_embeddings=generate_embeddings
    )


def load_investigation_protocols(db: Session, generate_embeddings: bool = False) -> dict:
    """Load investigation protocols."""
    from scripts.load_investigation_protocols import load_investigation_protocols as _load_protocols

    logger.info("Loading investigation protocols...")
    return _load_protocols(
        db,
        INVESTIGATIONS_PATH,
        clear_existing=True,
        generate_embeddings=generate_embeddings
    )


def load_cdi_guidelines(db: Session, generate_embeddings: bool = False) -> int:
    """Load CDI guideline documents."""
    from scripts.load_cdi_guidelines import load_cdi_guidelines as _load_guidelines

    logger.info("Loading CDI guidelines...")
    return _load_guidelines(
        db,
        CDI_DOCUMENTS_PATH,
        clear_existing=True,
        generate_embeddings=generate_embeddings
    )


def generate_all_embeddings(db: Session):
    """Generate embeddings for all knowledge base tables."""
    logger.info("Generating embeddings for all knowledge base data...")

    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer('ncbi/MedCPT-Query-Encoder')

        # E/M Codes
        em_codes = db.query(EMCode).filter(EMCode.embedding == None).all()
        logger.info(f"Generating embeddings for {len(em_codes)} E/M codes...")
        for code in em_codes:
            text = f"{code.code} {code.description} {code.category} MDM: {code.mdm_level}"
            code.embedding = model.encode(text, normalize_embeddings=True).tolist()
        db.commit()

        # Investigation Protocols
        protocols = db.query(InvestigationProtocol).filter(
            InvestigationProtocol.embedding == None
        ).all()
        logger.info(f"Generating embeddings for {len(protocols)} protocols...")
        for i, protocol in enumerate(protocols):
            text = f"{protocol.condition} {protocol.severity_level} {protocol.test_name} {protocol.rationale or ''}"
            protocol.embedding = model.encode(text, normalize_embeddings=True).tolist()
            if (i + 1) % 50 == 0:
                db.commit()
        db.commit()

        # DRG Rules
        drg_rules = db.query(DRGRule).filter(DRGRule.embedding == None).all()
        logger.info(f"Generating embeddings for {len(drg_rules)} DRG rules...")
        for rule in drg_rules:
            text = f"DRG {rule.drg_code} {rule.description} {rule.condition} {rule.optimization_notes or ''}"
            rule.embedding = model.encode(text, normalize_embeddings=True).tolist()
        db.commit()

        # CDI Guidelines
        guidelines = db.query(CDIGuideline).filter(CDIGuideline.embedding == None).all()
        logger.info(f"Generating embeddings for {len(guidelines)} guideline chunks...")
        for i, guideline in enumerate(guidelines):
            text = f"{guideline.section_title or ''} {guideline.content[:500]}"
            guideline.embedding = model.encode(text, normalize_embeddings=True).tolist()
            if (i + 1) % 50 == 0:
                db.commit()
        db.commit()

        # Billing Notes
        notes = db.query(BillingNote).filter(BillingNote.embedding == None).all()
        logger.info(f"Generating embeddings for {len(notes)} billing notes...")
        for note in notes:
            text = f"{note.condition} {note.content}"
            note.embedding = model.encode(text, normalize_embeddings=True).tolist()
        db.commit()

        logger.info("All embeddings generated successfully")

    except ImportError:
        logger.warning("sentence-transformers not installed. Skipping embedding generation.")
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")


def verify_migration(db: Session) -> dict:
    """Verify migration results."""
    logger.info("Verifying migration...")

    counts = {
        'em_codes': db.query(EMCode).count(),
        'investigation_protocols': db.query(InvestigationProtocol).count(),
        'cdi_guidelines': db.query(CDIGuideline).count(),
        'drg_rules': db.query(DRGRule).count(),
        'billing_notes': db.query(BillingNote).count(),
    }

    # Check embeddings
    embeddings = {
        'em_codes_with_embeddings': db.query(EMCode).filter(EMCode.embedding != None).count(),
        'protocols_with_embeddings': db.query(InvestigationProtocol).filter(
            InvestigationProtocol.embedding != None
        ).count(),
        'guidelines_with_embeddings': db.query(CDIGuideline).filter(
            CDIGuideline.embedding != None
        ).count(),
    }

    logger.info("Migration counts:")
    for name, count in counts.items():
        logger.info(f"  {name}: {count}")

    logger.info("Embedding counts:")
    for name, count in embeddings.items():
        logger.info(f"  {name}: {count}")

    return {**counts, **embeddings}


def main():
    parser = argparse.ArgumentParser(
        description="Master migration script for CDI Agent knowledge base"
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help="Run all migrations"
    )
    parser.add_argument(
        '--em-codes',
        action='store_true',
        help="Load E/M codes only"
    )
    parser.add_argument(
        '--protocols',
        action='store_true',
        help="Load investigation protocols only"
    )
    parser.add_argument(
        '--guidelines',
        action='store_true',
        help="Load CDI guidelines only"
    )
    parser.add_argument(
        '--generate-embeddings',
        action='store_true',
        help="Generate vector embeddings after loading"
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help="Only verify existing migration, don't load data"
    )
    parser.add_argument(
        '--use-s3',
        action='store_true',
        help="Use S3 as data source (for ECS deployment)"
    )

    args = parser.parse_args()

    # If no specific option selected, default to --all
    if not any([args.all, args.em_codes, args.protocols, args.guidelines, args.verify_only]):
        args.all = True

    logger.info("=" * 70)
    logger.info("CDI Agent Knowledge Base Migration")
    logger.info("=" * 70)
    logger.info(f"Started at: {datetime.now().isoformat()}")
    logger.info("")

    # Setup data paths (S3 or local)
    logger.info("Setting up data paths...")
    setup_data_paths(use_s3=args.use_s3)
    logger.info("")

    # Verify source paths
    logger.info("Checking source paths...")
    path_status = verify_source_paths()
    logger.info("")

    if not all(path_status.values()) and not args.verify_only:
        logger.warning("Some source paths are missing. Migration may be incomplete.")

    start_time = time.time()
    db = SessionLocal()

    try:
        # Create tables
        create_tables()
        logger.info("")

        if args.verify_only:
            verify_migration(db)
            return

        # Run migrations
        if args.all or args.em_codes:
            if path_status.get('em_codes'):
                em_count = load_em_codes(db, args.generate_embeddings)
                logger.info(f"E/M codes loaded: {em_count}")
            else:
                logger.warning("Skipping E/M codes - source not found")
            logger.info("")

        if args.all or args.protocols:
            if path_status.get('investigations'):
                protocol_stats = load_investigation_protocols(db, args.generate_embeddings)
                logger.info(f"Investigation protocols loaded: {protocol_stats}")
            else:
                logger.warning("Skipping investigation protocols - source not found")
            logger.info("")

        if args.all or args.guidelines:
            if path_status.get('cdi_documents'):
                guideline_count = load_cdi_guidelines(db, args.generate_embeddings)
                logger.info(f"CDI guidelines loaded: {guideline_count}")
            else:
                logger.warning("Skipping CDI guidelines - source not found")
            logger.info("")

        # Generate embeddings if not done during individual loads
        if args.generate_embeddings and args.all:
            generate_all_embeddings(db)
            logger.info("")

        # Verify migration
        verify_migration(db)

        elapsed = time.time() - start_time
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"Migration completed successfully in {elapsed:.1f} seconds")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
