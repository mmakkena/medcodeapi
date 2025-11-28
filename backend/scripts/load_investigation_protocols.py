#!/usr/bin/env python3
"""
Load Investigation Protocols to PostgreSQL

Loads clinical investigation protocol data from CDIAgent
JSON files into the PostgreSQL database.

Protocols contain evidence-based investigation recommendations for
specific conditions (sepsis, heart failure, pneumonia, etc.)

Usage:
    python scripts/load_investigation_protocols.py [--source PATH] [--generate-embeddings]

Source: CDIAgent/knowledge_base/investigations/*.json
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from infrastructure.db.postgres import SessionLocal, engine
from infrastructure.db.models.knowledge_base import InvestigationProtocol, DRGRule, BillingNote

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default source path - CDIAgent is a sibling project
DEFAULT_SOURCE = Path("/Users/murali.local/CDIAgent/knowledge_base/investigations")


def load_protocol_file(file_path: Path) -> dict:
    """Load a single protocol JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def extract_investigations(
    condition: str,
    severity_level: str,
    severity_data: dict,
    icd10_codes: list[str],
    test_category: str = "required"
) -> list[dict]:
    """
    Extract individual investigation records from severity level data.

    Args:
        condition: The condition name (e.g., "Sepsis")
        severity_level: Severity level (e.g., "sepsis", "severe_sepsis", "septic_shock")
        severity_data: The severity level data dict
        icd10_codes: ICD-10 codes associated with the condition
        test_category: Category of tests (required, source_directed, advanced_monitoring)

    Returns:
        List of investigation record dicts
    """
    investigations = []

    # Extract required investigations
    for test in severity_data.get('required_investigations', []):
        investigations.append({
            'condition': condition,
            'severity_level': severity_level,
            'test_name': test.get('test'),
            'cpt_code': test.get('cpt_code'),
            'timing': test.get('timing'),
            'rationale': test.get('rationale'),
            'estimated_cost': test.get('estimated_cost'),
            'evidence_grade': test.get('evidence_grade'),
            'guideline_source': test.get('guideline_source'),
            'test_category': test_category,
            'source_type': None,
            'icd10_codes': icd10_codes,
            'is_required': True,
            'is_sep1_requirement': test.get('sep1_requirement', False)
        })

    # Extract source-directed investigations
    for source in severity_data.get('source_directed_investigations', []):
        source_type = source.get('source')
        for test in source.get('tests', []):
            investigations.append({
                'condition': condition,
                'severity_level': severity_level,
                'test_name': test.get('test'),
                'cpt_code': test.get('cpt_code'),
                'timing': test.get('timing'),
                'rationale': test.get('rationale'),
                'estimated_cost': test.get('estimated_cost'),
                'evidence_grade': test.get('evidence_grade'),
                'guideline_source': None,
                'test_category': 'source_directed',
                'source_type': source_type,
                'icd10_codes': icd10_codes,
                'is_required': False,
                'is_sep1_requirement': False
            })

    # Extract advanced monitoring
    for test in severity_data.get('advanced_monitoring', []):
        investigations.append({
            'condition': condition,
            'severity_level': severity_level,
            'test_name': test.get('test'),
            'cpt_code': test.get('cpt_code'),
            'timing': test.get('timing'),
            'rationale': test.get('rationale'),
            'estimated_cost': test.get('estimated_cost'),
            'evidence_grade': test.get('evidence_grade'),
            'guideline_source': None,
            'test_category': 'advanced_monitoring',
            'source_type': None,
            'icd10_codes': icd10_codes,
            'is_required': False,
            'is_sep1_requirement': False
        })

    return investigations


def extract_drg_rules(condition: str, drg_data: list[dict]) -> list[dict]:
    """Extract DRG optimization rules from protocol data."""
    rules = []

    for drg in drg_data:
        rules.append({
            'drg_code': drg.get('current_drg'),
            'description': drg.get('description'),
            'weight': drg.get('weight'),
            'condition': condition,
            'optimization_notes': drg.get('optimization'),
            'required_documentation': drg.get('required_documentation', []),
            'potential_upgrade_drg': None,  # Could be derived
            'revenue_impact': drg.get('revenue_increase'),
            'principal_dx_codes': [],
            'mcc_codes': [],
            'cc_codes': [],
            'fiscal_year': 2024,
            'is_active': True
        })

    return rules


def extract_billing_notes(condition: str, billing_notes: list[str]) -> list[dict]:
    """Extract billing notes from protocol data."""
    notes = []

    for note in billing_notes:
        notes.append({
            'condition': condition,
            'cpt_code': None,  # Could parse from note text
            'note_type': 'tip',
            'content': note,
            'source': 'CDIAgent Knowledge Base'
        })

    return notes


def load_investigation_protocols(
    db: Session,
    source_path: Path,
    clear_existing: bool = False,
    generate_embeddings: bool = False
) -> dict:
    """
    Load investigation protocols into the database.

    Args:
        db: Database session
        source_path: Path to investigations directory
        clear_existing: Whether to clear existing records
        generate_embeddings: Whether to generate vector embeddings

    Returns:
        Dict with counts of records loaded
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Source directory not found: {source_path}")

    # Find all JSON files
    json_files = list(source_path.glob("*.json"))
    logger.info(f"Found {len(json_files)} protocol files in {source_path}")

    if clear_existing:
        logger.info("Clearing existing investigation protocols...")
        db.query(InvestigationProtocol).delete()
        db.query(DRGRule).delete()
        db.query(BillingNote).delete()
        db.commit()

    stats = {
        'protocols': 0,
        'drg_rules': 0,
        'billing_notes': 0,
        'errors': 0
    }

    for file_path in json_files:
        try:
            logger.info(f"Processing: {file_path.name}")
            data = load_protocol_file(file_path)

            condition = data.get('condition', file_path.stem)
            icd10_codes = data.get('icd10_codes', [])

            # Process severity levels
            for severity_level, severity_data in data.get('severity_levels', {}).items():
                investigations = extract_investigations(
                    condition, severity_level, severity_data, icd10_codes
                )

                for inv_data in investigations:
                    record = InvestigationProtocol(
                        condition=inv_data['condition'],
                        severity_level=inv_data['severity_level'],
                        test_name=inv_data['test_name'],
                        cpt_code=inv_data['cpt_code'],
                        timing=inv_data['timing'],
                        rationale=inv_data['rationale'],
                        estimated_cost=inv_data['estimated_cost'],
                        evidence_grade=inv_data['evidence_grade'],
                        guideline_source=inv_data['guideline_source'],
                        test_category=inv_data['test_category'],
                        source_type=inv_data['source_type'],
                        icd10_codes=inv_data['icd10_codes'],
                        is_required=inv_data['is_required'],
                        is_sep1_requirement=inv_data['is_sep1_requirement']
                    )
                    db.add(record)
                    stats['protocols'] += 1

            # Process bundle investigations (e.g., SEP-1 bundle)
            for bundle_name, bundle_data in data.get('sepsis_bundle_investigations', {}).items():
                for test in bundle_data.get('required_investigations', []) + bundle_data.get('tests', []):
                    if not test.get('test'):
                        continue
                    record = InvestigationProtocol(
                        condition=condition,
                        severity_level=bundle_name,
                        test_name=test.get('test'),
                        cpt_code=test.get('cpt_code'),
                        timing=test.get('timing'),
                        rationale=test.get('rationale'),
                        estimated_cost=test.get('estimated_cost'),
                        test_category='bundle',
                        icd10_codes=icd10_codes,
                        is_required=True,
                        is_sep1_requirement=test.get('sep1_requirement', False)
                    )
                    db.add(record)
                    stats['protocols'] += 1

            # Process follow-up investigations
            for test in data.get('follow_up_investigations', []):
                record = InvestigationProtocol(
                    condition=condition,
                    severity_level='follow_up',
                    test_name=test.get('test'),
                    cpt_code=test.get('cpt_code'),
                    timing=test.get('timing'),
                    rationale=test.get('rationale'),
                    estimated_cost=test.get('estimated_cost'),
                    test_category='follow_up',
                    icd10_codes=icd10_codes,
                    is_required=False,
                    is_sep1_requirement=False
                )
                db.add(record)
                stats['protocols'] += 1

            # Process immunocompromised investigations
            immuno_data = data.get('immunocompromised_investigations', {})
            for test in immuno_data.get('tests', []):
                record = InvestigationProtocol(
                    condition=condition,
                    severity_level='immunocompromised',
                    test_name=test.get('test'),
                    cpt_code=test.get('cpt_code'),
                    timing=None,
                    rationale=test.get('rationale'),
                    estimated_cost=test.get('estimated_cost'),
                    test_category='immunocompromised',
                    icd10_codes=icd10_codes,
                    is_required=False,
                    is_sep1_requirement=False
                )
                db.add(record)
                stats['protocols'] += 1

            # Process DRG rules
            drg_rules = extract_drg_rules(
                condition,
                data.get('drg_optimization_opportunities', [])
            )
            for rule_data in drg_rules:
                record = DRGRule(
                    drg_code=rule_data['drg_code'],
                    description=rule_data['description'],
                    weight=rule_data['weight'],
                    condition=rule_data['condition'],
                    optimization_notes=rule_data['optimization_notes'],
                    required_documentation=rule_data['required_documentation'],
                    revenue_impact=rule_data['revenue_impact'],
                    fiscal_year=rule_data['fiscal_year'],
                    is_active=rule_data['is_active']
                )
                db.add(record)
                stats['drg_rules'] += 1

            # Process billing notes
            billing_notes = extract_billing_notes(
                condition,
                data.get('billing_notes', [])
            )
            for note_data in billing_notes:
                record = BillingNote(
                    condition=note_data['condition'],
                    cpt_code=note_data['cpt_code'],
                    note_type=note_data['note_type'],
                    content=note_data['content'],
                    source=note_data['source']
                )
                db.add(record)
                stats['billing_notes'] += 1

            db.commit()

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            stats['errors'] += 1
            db.rollback()

    logger.info(f"Investigation protocols loaded: {stats['protocols']}")
    logger.info(f"DRG rules loaded: {stats['drg_rules']}")
    logger.info(f"Billing notes loaded: {stats['billing_notes']}")
    logger.info(f"Errors: {stats['errors']}")

    # Generate embeddings if requested
    if generate_embeddings:
        logger.info("Generating embeddings...")
        generate_protocol_embeddings(db)

    return stats


def generate_protocol_embeddings(db: Session):
    """Generate vector embeddings for investigation protocols."""
    try:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model...")
        model = SentenceTransformer('ncbi/MedCPT-Query-Encoder')

        # Generate embeddings for protocols
        protocols = db.query(InvestigationProtocol).filter(
            InvestigationProtocol.embedding == None
        ).all()
        logger.info(f"Generating embeddings for {len(protocols)} protocols...")

        for i, protocol in enumerate(protocols):
            text = f"{protocol.condition} {protocol.severity_level} {protocol.test_name} {protocol.rationale or ''}"
            embedding = model.encode(text, normalize_embeddings=True)
            protocol.embedding = embedding.tolist()

            if (i + 1) % 50 == 0:
                logger.info(f"Processed {i + 1}/{len(protocols)} protocols")
                db.commit()

        db.commit()

        # Generate embeddings for DRG rules
        drg_rules = db.query(DRGRule).filter(DRGRule.embedding == None).all()
        logger.info(f"Generating embeddings for {len(drg_rules)} DRG rules...")

        for rule in drg_rules:
            text = f"DRG {rule.drg_code} {rule.description} {rule.condition} {rule.optimization_notes or ''}"
            embedding = model.encode(text, normalize_embeddings=True)
            rule.embedding = embedding.tolist()

        db.commit()

        # Generate embeddings for billing notes
        notes = db.query(BillingNote).filter(BillingNote.embedding == None).all()
        logger.info(f"Generating embeddings for {len(notes)} billing notes...")

        for note in notes:
            text = f"{note.condition} {note.content}"
            embedding = model.encode(text, normalize_embeddings=True)
            note.embedding = embedding.tolist()

        db.commit()
        logger.info("Embeddings generated successfully")

    except ImportError:
        logger.warning("sentence-transformers not installed. Skipping embedding generation.")
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")


def main():
    parser = argparse.ArgumentParser(description="Load investigation protocols to PostgreSQL")
    parser.add_argument(
        '--source',
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Path to investigations directory (default: {DEFAULT_SOURCE})"
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help="Clear existing protocols before loading"
    )
    parser.add_argument(
        '--generate-embeddings',
        action='store_true',
        help="Generate vector embeddings for semantic search"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Investigation Protocol Loader")
    logger.info("=" * 60)

    db = SessionLocal()

    try:
        # Ensure tables exist
        from infrastructure.db.models.knowledge_base import InvestigationProtocol, DRGRule, BillingNote
        InvestigationProtocol.__table__.create(engine, checkfirst=True)
        DRGRule.__table__.create(engine, checkfirst=True)
        BillingNote.__table__.create(engine, checkfirst=True)

        # Load protocols
        stats = load_investigation_protocols(
            db,
            args.source,
            clear_existing=args.clear,
            generate_embeddings=args.generate_embeddings
        )

        total = stats['protocols'] + stats['drg_rules'] + stats['billing_notes']
        logger.info(f"Successfully loaded {total} records")

    except Exception as e:
        logger.error(f"Failed to load investigation protocols: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
