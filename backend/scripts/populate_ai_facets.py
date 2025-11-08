#!/usr/bin/env python3
"""
Populate AI facets for ICD-10 codes

This script generates AI-powered clinical facets for ICD-10 codes.
Facets include: body_system, concept_type, chronicity, severity, acuity, etc.

Note: This script uses rule-based classification for initial facets.
For production, you would integrate with an LLM API (OpenAI, Claude, etc.)
to generate more accurate facets.
"""

import os
import sys
import re
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from tqdm import tqdm

from app.database import Base
from app.models.icd10_code import ICD10Code
from app.models.icd10_ai_facet import ICD10AIFacet

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


# Rule-based classification mappings
# In production, replace with LLM-based classification

BODY_SYSTEM_KEYWORDS = {
    'cardiovascular': ['heart', 'cardiac', 'vascular', 'artery', 'vein', 'blood pressure', 'hypertension', 'coronary'],
    'respiratory': ['lung', 'respiratory', 'bronch', 'pneumo', 'asthma', 'copd', 'breathing'],
    'digestive': ['stomach', 'intestin', 'colon', 'liver', 'pancrea', 'gallbladder', 'digestive', 'gastro'],
    'endocrine': ['diabetes', 'thyroid', 'hormone', 'endocrine', 'adrenal', 'pituitary', 'metabolic'],
    'nervous': ['brain', 'nerve', 'neural', 'spinal', 'cerebral', 'seizure', 'stroke'],
    'musculoskeletal': ['bone', 'muscle', 'joint', 'arthritis', 'fracture', 'skeletal', 'osteo'],
    'genitourinary': ['kidney', 'bladder', 'urinary', 'renal', 'prostate', 'uterus', 'genital'],
    'skin': ['skin', 'derma', 'cutaneous', 'rash', 'ulcer'],
    'hematologic': ['blood', 'anemia', 'hemato', 'leukemia', 'lymphoma', 'coagulation'],
    'immune': ['immune', 'autoimmune', 'infection', 'sepsis', 'hiv'],
    'eye': ['eye', 'ocular', 'vision', 'retina', 'cataract', 'glaucoma'],
    'ear': ['ear', 'hearing', 'auditory', 'otitis'],
    'mental': ['mental', 'psychiatric', 'depression', 'anxiety', 'psycho', 'schizophren'],
}

CONCEPT_TYPE_KEYWORDS = {
    'diagnosis': ['disease', 'disorder', 'syndrome', 'condition'],
    'procedure': ['procedure', 'surgery', 'operation', 'intervention'],
    'symptom': ['symptom', 'sign', 'pain', 'fever', 'cough'],
    'injury': ['injury', 'trauma', 'fracture', 'wound', 'burn', 'poisoning'],
    'screening': ['screening', 'examination', 'encounter for'],
    'history': ['history of', 'personal history', 'family history'],
}

CHRONICITY_KEYWORDS = {
    'acute': ['acute', 'sudden', 'abrupt'],
    'chronic': ['chronic', 'persistent', 'long-term', 'recurrent'],
    'subacute': ['subacute', 'prolonged'],
}

SEVERITY_KEYWORDS = {
    'mild': ['mild', 'minor', 'slight'],
    'moderate': ['moderate'],
    'severe': ['severe', 'major', 'serious'],
    'life-threatening': ['life-threatening', 'critical', 'fatal', 'emergency'],
}

ACUITY_KEYWORDS = {
    'acute': ['acute', 'sudden onset'],
    'chronic': ['chronic', 'long-standing'],
    'subacute': ['subacute'],
}

LATERALITY_KEYWORDS = {
    'left': ['left'],
    'right': ['right'],
    'bilateral': ['bilateral', 'both'],
    'unspecified': ['unspecified side', 'not specified'],
}

ONSET_CONTEXT_KEYWORDS = {
    'congenital': ['congenital', 'birth', 'hereditary'],
    'acquired': ['acquired'],
    'traumatic': ['traumatic', 'injury', 'trauma'],
    'iatrogenic': ['iatrogenic', 'complication', 'postoperative'],
}


def classify_by_keywords(text: str, keyword_map: Dict[str, list]) -> Optional[str]:
    """
    Classify text using keyword matching.

    Args:
        text: Text to classify
        keyword_map: Dictionary mapping categories to keywords

    Returns:
        Best matching category or None
    """
    if not text:
        return None

    text_lower = text.lower()

    for category, keywords in keyword_map.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category

    return None


def classify_by_code_prefix(code: str) -> Dict[str, Optional[str]]:
    """
    Classify ICD-10 code by its prefix using ICD-10 chapter structure.

    Args:
        code: ICD-10 code

    Returns:
        Dictionary with facet classifications
    """
    facets = {}

    prefix = code[0] if code else ''
    code_num = int(code[1:3]) if len(code) >= 3 and code[1:3].isdigit() else 0

    # Body system classification by chapter
    if prefix in ['A', 'B']:
        facets['body_system'] = 'immune'
        facets['concept_type'] = 'diagnosis'
    elif prefix == 'C' or (prefix == 'D' and code_num < 50):
        facets['body_system'] = 'hematologic'
        facets['concept_type'] = 'diagnosis'
        facets['severity'] = 'severe'
    elif prefix == 'D' and code_num >= 50:
        facets['body_system'] = 'hematologic'
    elif prefix == 'E':
        facets['body_system'] = 'endocrine'
        facets['chronicity'] = 'chronic'
    elif prefix == 'F':
        facets['body_system'] = 'mental'
    elif prefix == 'G':
        facets['body_system'] = 'nervous'
    elif prefix == 'H' and code_num < 60:
        facets['body_system'] = 'eye'
    elif prefix == 'H' and code_num >= 60:
        facets['body_system'] = 'ear'
    elif prefix == 'I':
        facets['body_system'] = 'cardiovascular'
    elif prefix == 'J':
        facets['body_system'] = 'respiratory'
    elif prefix == 'K':
        facets['body_system'] = 'digestive'
    elif prefix == 'L':
        facets['body_system'] = 'skin'
    elif prefix == 'M':
        facets['body_system'] = 'musculoskeletal'
    elif prefix == 'N':
        facets['body_system'] = 'genitourinary'
    elif prefix == 'O':
        facets['body_system'] = 'genitourinary'
        facets['concept_type'] = 'diagnosis'
        facets['sex_specific'] = 'female'
    elif prefix == 'P':
        facets['age_band'] = 'neonatal'
    elif prefix in ['S', 'T']:
        facets['concept_type'] = 'injury'
        facets['onset_context'] = 'traumatic'
        facets['acuity'] = 'acute'
    elif prefix == 'Z':
        facets['concept_type'] = 'screening'

    return facets


def generate_facets_for_code(code: ICD10Code) -> Dict[str, any]:
    """
    Generate AI facets for a single ICD-10 code using rule-based classification.

    Args:
        code: ICD10Code object

    Returns:
        Dictionary of facet values
    """
    # Start with code-prefix based classification
    facets = classify_by_code_prefix(code.code)

    # Combine code and description for text analysis
    text = f"{code.code} {code.short_desc or ''} {code.long_desc or ''}"

    # Classify by keywords (override prefix-based if found)
    body_system = classify_by_keywords(text, BODY_SYSTEM_KEYWORDS)
    if body_system:
        facets['body_system'] = body_system

    concept_type = classify_by_keywords(text, CONCEPT_TYPE_KEYWORDS)
    if concept_type:
        facets['concept_type'] = concept_type

    chronicity = classify_by_keywords(text, CHRONICITY_KEYWORDS)
    if chronicity:
        facets['chronicity'] = chronicity

    severity = classify_by_keywords(text, SEVERITY_KEYWORDS)
    if severity:
        facets['severity'] = severity

    acuity = classify_by_keywords(text, ACUITY_KEYWORDS)
    if acuity:
        facets['acuity'] = acuity

    laterality = classify_by_keywords(text, LATERALITY_KEYWORDS)
    if laterality:
        facets['laterality'] = laterality

    onset_context = classify_by_keywords(text, ONSET_CONTEXT_KEYWORDS)
    if onset_context:
        facets['onset_context'] = onset_context

    # Determine risk flag (conditions that need careful monitoring)
    risk_keywords = ['cancer', 'malignant', 'severe', 'life-threatening', 'emergency',
                     'critical', 'sepsis', 'stroke', 'infarction', 'failure']
    facets['risk_flag'] = any(keyword in text.lower() for keyword in risk_keywords)

    # Determine age band
    if 'neonatal' in text.lower() or 'newborn' in text.lower():
        facets['age_band'] = 'neonatal'
    elif 'pediatric' in text.lower() or 'child' in text.lower() or 'infant' in text.lower():
        facets['age_band'] = 'pediatric'
    elif 'geriatric' in text.lower() or 'elderly' in text.lower():
        facets['age_band'] = 'geriatric'
    else:
        facets['age_band'] = 'adult'

    # Determine sex specificity
    if 'pregnancy' in text.lower() or 'maternal' in text.lower() or 'uterus' in text.lower():
        facets['sex_specific'] = 'female'
    elif 'prostate' in text.lower() or 'testicular' in text.lower():
        facets['sex_specific'] = 'male'
    else:
        facets['sex_specific'] = 'both'

    return facets


def populate_facets(
    db: Session,
    batch_size: int = 100,
    code_system: str = "ICD10-CM",
    skip_existing: bool = True
) -> int:
    """
    Populate AI facets for all codes in the database.

    Args:
        db: Database session
        batch_size: Number of codes to process at once
        code_system: Code system to process
        skip_existing: Skip codes that already have facets

    Returns:
        Number of codes processed
    """
    # Get codes without facets (or all codes if not skipping)
    query = db.query(ICD10Code).filter(ICD10Code.code_system == code_system)

    all_codes = query.all()

    if not all_codes:
        logger.info("No codes to process")
        return 0

    # Filter codes that need facets
    codes_to_process = []

    if skip_existing:
        for code in all_codes:
            existing_facet = db.query(ICD10AIFacet).filter(
                and_(
                    ICD10AIFacet.code == code.code,
                    ICD10AIFacet.code_system == code.code_system
                )
            ).first()

            if not existing_facet:
                codes_to_process.append(code)
    else:
        codes_to_process = all_codes

    if not codes_to_process:
        logger.info("All codes already have facets")
        return 0

    logger.info(f"Processing {len(codes_to_process)} codes...")

    processed = 0

    # Process in batches with progress bar
    with tqdm(total=len(codes_to_process), desc="Generating facets", unit="code") as pbar:
        for i in range(0, len(codes_to_process), batch_size):
            batch = codes_to_process[i:i + batch_size]

            try:
                for code in batch:
                    # Generate facets
                    facets_data = generate_facets_for_code(code)

                    # Check if facet already exists
                    existing_facet = db.query(ICD10AIFacet).filter(
                        and_(
                            ICD10AIFacet.code == code.code,
                            ICD10AIFacet.code_system == code.code_system
                        )
                    ).first()

                    if existing_facet and not skip_existing:
                        # Update existing facet
                        for key, value in facets_data.items():
                            setattr(existing_facet, key, value)
                    elif not existing_facet:
                        # Create new facet
                        facet = ICD10AIFacet(
                            code=code.code,
                            code_system=code.code_system,
                            **facets_data
                        )
                        db.add(facet)

                    processed += 1

                # Commit batch
                db.commit()
                pbar.update(len(batch))

            except Exception as e:
                logger.error(f"Error processing batch: {e}")
                db.rollback()
                continue

    logger.info(f"✓ Processed {processed} codes")

    return processed


def verify_facets(db: Session, code_system: str = "ICD10-CM") -> dict:
    """
    Verify facet generation results.

    Args:
        db: Database session
        code_system: Code system to verify

    Returns:
        Dictionary with verification stats
    """
    total_codes = db.query(ICD10Code).filter(
        ICD10Code.code_system == code_system
    ).count()

    codes_with_facets = db.query(ICD10AIFacet).filter(
        ICD10AIFacet.code_system == code_system
    ).count()

    codes_without_facets = total_codes - codes_with_facets

    return {
        'total_codes': total_codes,
        'with_facets': codes_with_facets,
        'without_facets': codes_without_facets,
        'coverage_percent': (codes_with_facets / total_codes * 100) if total_codes > 0 else 0
    }


def show_sample_facets(db: Session, limit: int = 5):
    """
    Show sample codes with facets for verification.

    Args:
        db: Database session
        limit: Number of samples to show
    """
    facets = db.query(ICD10AIFacet).limit(limit).all()

    logger.info(f"\nSample codes with facets:")

    for facet in facets:
        # Get the code
        code = db.query(ICD10Code).filter(
            and_(
                ICD10Code.code == facet.code,
                ICD10Code.code_system == facet.code_system
            )
        ).first()

        logger.info(f"\n  Code: {facet.code}")
        if code:
            logger.info(f"  Description: {code.short_desc}")
        logger.info(f"  Body System: {facet.body_system}")
        logger.info(f"  Concept Type: {facet.concept_type}")
        logger.info(f"  Chronicity: {facet.chronicity}")
        logger.info(f"  Severity: {facet.severity}")
        logger.info(f"  Risk Flag: {facet.risk_flag}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Populate AI facets for ICD-10 codes"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of codes to process in each batch (default: 100)"
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
        help="Regenerate facets even if they already exist"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing facets, don't generate new ones"
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Show sample facets after generation"
    )

    args = parser.parse_args()

    # Connect to database
    db_url = args.db_url or get_database_url()
    logger.info(f"Connecting to database...")

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Verify existing facets
        logger.info(f"\nChecking current facet status...")
        stats = verify_facets(db, args.code_system)

        logger.info(f"\nCurrent status:")
        logger.info(f"  Total codes: {stats['total_codes']}")
        logger.info(f"  With facets: {stats['with_facets']}")
        logger.info(f"  Without facets: {stats['without_facets']}")
        logger.info(f"  Coverage: {stats['coverage_percent']:.1f}%")

        if args.verify_only:
            if args.sample:
                show_sample_facets(db, limit=5)
            logger.info("\nVerify-only mode - exiting")
            return 0

        if stats['without_facets'] == 0 and not args.force:
            logger.info("\n✓ All codes already have facets")
            logger.info("  Use --force to regenerate facets")
            if args.sample:
                show_sample_facets(db, limit=5)
            return 0

        # Generate facets
        logger.info(f"\n{'Regenerating' if args.force else 'Generating'} facets...")
        logger.info("Note: Using rule-based classification. For production, integrate with LLM API.")

        start_time = datetime.now()

        processed = populate_facets(
            db,
            batch_size=args.batch_size,
            code_system=args.code_system,
            skip_existing=not args.force
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Verify again
        stats = verify_facets(db, args.code_system)

        logger.info(f"\n✓ Facet generation complete!")
        logger.info(f"  Codes processed: {processed}")
        logger.info(f"  Duration: {duration:.1f} seconds")
        logger.info(f"  Rate: {processed/duration:.1f} codes/second")
        logger.info(f"\nFinal status:")
        logger.info(f"  Total codes: {stats['total_codes']}")
        logger.info(f"  With facets: {stats['with_facets']}")
        logger.info(f"  Coverage: {stats['coverage_percent']:.1f}%")

        # Show samples if requested
        if args.sample:
            show_sample_facets(db, limit=5)

        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
