#!/usr/bin/env python3
"""
Populate AI facets for procedure codes (CPT/HCPCS)

This script generates AI-powered clinical facets for procedure codes.
Facets include: body_region, procedure_category, complexity_level, etc.

Note: This script uses rule-based classification for initial facets.
For production, you would integrate with an LLM API for more accurate facets.
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
from app.models.procedure_code import ProcedureCode
from app.models.procedure_code_facet import ProcedureCodeFacet

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


# Rule-based classification mappings for procedure codes

BODY_REGION_KEYWORDS = {
    'head_neck': ['head', 'neck', 'face', 'skull', 'cervical', 'cranial', 'oral', 'nasal', 'pharynx', 'larynx'],
    'thorax': ['chest', 'thorac', 'lung', 'heart', 'mediastin', 'rib', 'sternum'],
    'abdomen': ['abdomen', 'abdominal', 'stomach', 'liver', 'spleen', 'intestin', 'colon', 'appendix'],
    'pelvis': ['pelvis', 'pelvic', 'bladder', 'prostate', 'uterus', 'ovary', 'rectum'],
    'spine': ['spine', 'spinal', 'vertebra', 'lumbar', 'thoracic', 'cervical'],
    'upper_extremity': ['arm', 'shoulder', 'elbow', 'wrist', 'hand', 'finger', 'clavicle', 'humerus', 'radius', 'ulna'],
    'lower_extremity': ['leg', 'hip', 'knee', 'ankle', 'foot', 'toe', 'femur', 'tibia', 'fibula'],
}

BODY_SYSTEM_KEYWORDS = {
    'cardiovascular': ['heart', 'cardiac', 'vascular', 'artery', 'vein', 'angioplasty', 'bypass'],
    'respiratory': ['lung', 'bronch', 'respiratory', 'airway', 'breathing'],
    'digestive': ['gastro', 'intestin', 'colon', 'liver', 'pancrea', 'esophag', 'stomach'],
    'musculoskeletal': ['bone', 'joint', 'muscle', 'tendon', 'ligament', 'fracture', 'arthro'],
    'nervous': ['nerve', 'brain', 'spinal', 'neural'],
    'genitourinary': ['kidney', 'bladder', 'urinary', 'renal', 'prostate', 'uterus'],
    'integumentary': ['skin', 'wound', 'lesion', 'tissue'],
    'eye': ['eye', 'ocular', 'vision', 'retina'],
    'ear': ['ear', 'hearing', 'auditory'],
}

PROCEDURE_CATEGORY_KEYWORDS = {
    'evaluation': ['evaluation', 'management', 'office visit', 'consultation', 'examination'],
    'surgical': ['surgery', 'excision', 'incision', 'repair', 'reconstruction', 'resection', 'removal'],
    'diagnostic_imaging': ['xray', 'ct scan', 'mri', 'ultrasound', 'mammography', 'imaging', 'radiologic'],
    'laboratory': ['lab', 'test', 'analysis', 'culture', 'screening'],
    'therapeutic': ['therapy', 'treatment', 'injection', 'infusion', 'rehabilitation'],
    'preventive': ['preventive', 'screening', 'vaccination', 'immunization'],
    'anesthesia': ['anesthesia', 'anesthetic'],
}

COMPLEXITY_KEYWORDS = {
    'simple': ['simple', 'basic', 'straightforward', 'minor'],
    'moderate': ['intermediate', 'moderate'],
    'complex': ['complex', 'extensive', 'complicated'],
    'highly_complex': ['major', 'radical', 'extensive reconstruction'],
}

SERVICE_LOCATION_KEYWORDS = {
    'office': ['office', 'outpatient'],
    'hospital_inpatient': ['inpatient', 'hospital'],
    'emergency': ['emergency', 'urgent'],
    'ambulatory': ['ambulatory', 'outpatient surgery'],
}

# E/M code ranges (CPT)
EM_CODE_RANGES = {
    'office_new': range(99201, 99216),
    'office_established': range(99211, 99216),
    'hospital_inpatient': range(99221, 99240),
    'emergency': range(99281, 99289),
    'critical_care': range(99291, 99293),
}

# Imaging modality keywords
IMAGING_MODALITY_KEYWORDS = {
    'xray': ['radiologic', 'x-ray', 'xray', 'radiograph'],
    'ct': ['ct scan', 'computed tomography', 'cat scan'],
    'mri': ['mri', 'magnetic resonance'],
    'ultrasound': ['ultrasound', 'sonogra', 'echo'],
    'nuclear_medicine': ['nuclear', 'pet scan', 'spect'],
    'fluoroscopy': ['fluoroscop'],
}

SURGICAL_APPROACH_KEYWORDS = {
    'open': ['open'],
    'laparoscopic': ['laparoscop', 'minimally invasive'],
    'endoscopic': ['endoscop', 'arthroscop', 'bronchoscop'],
    'percutaneous': ['percutaneous', 'needle'],
    'robotic': ['robotic', 'robot-assisted'],
}


def classify_by_keywords(text: str, keyword_map: Dict[str, list]) -> Optional[str]:
    """Classify text based on keyword matching."""
    if not text:
        return None

    text_lower = text.lower()

    for category, keywords in keyword_map.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return category

    return None


def get_em_level(code: str) -> Optional[str]:
    """Determine E/M level from code number."""
    try:
        code_num = int(code)
        if code_num in range(99201, 99206) or code_num in range(99211, 99216):
            # Level is last digit
            level = code_num % 10
            return f"level_{level}"
        elif code_num in EM_CODE_RANGES['critical_care']:
            return "critical_care"
    except ValueError:
        pass
    return None


def get_em_patient_type(code: str) -> Optional[str]:
    """Determine if new or established patient from code."""
    try:
        code_num = int(code)
        if code_num in EM_CODE_RANGES['office_new']:
            return "new_patient"
        elif code_num in EM_CODE_RANGES['office_established']:
            return "established_patient"
    except ValueError:
        pass
    return None


def is_major_surgery(description: str, complexity: Optional[str]) -> bool:
    """Determine if procedure is major surgery."""
    if not description:
        return False

    desc_lower = description.lower()

    # Major surgery indicators
    major_keywords = ['radical', 'total', 'complete', 'extensive', 'bypass', 'transplant',
                      'replacement', 'reconstruction', 'amputation']

    for keyword in major_keywords:
        if keyword in desc_lower:
            return True

    if complexity in ['complex', 'highly_complex']:
        return True

    return False


def generate_facets_for_code(code: ProcedureCode) -> Dict:
    """Generate facets for a single procedure code using rule-based classification."""

    # Combine all text for classification
    text = ' '.join(filter(None, [
        code.paraphrased_desc,
        code.short_desc,
        code.long_desc,
        code.category
    ]))

    # Classify based on keywords
    body_region = classify_by_keywords(text, BODY_REGION_KEYWORDS)
    body_system = classify_by_keywords(text, BODY_SYSTEM_KEYWORDS)
    procedure_category = classify_by_keywords(text, PROCEDURE_CATEGORY_KEYWORDS)
    complexity_level = classify_by_keywords(text, COMPLEXITY_KEYWORDS)
    service_location = classify_by_keywords(text, SERVICE_LOCATION_KEYWORDS)
    imaging_modality = classify_by_keywords(text, IMAGING_MODALITY_KEYWORDS)
    surgical_approach = classify_by_keywords(text, SURGICAL_APPROACH_KEYWORDS)

    # E/M specific
    em_level = get_em_level(code.code) if code.code_system == 'CPT' else None
    em_patient_type = get_em_patient_type(code.code) if code.code_system == 'CPT' else None

    # Surgery classification
    is_major = is_major_surgery(text, complexity_level)

    # Uses contrast (for imaging)
    uses_contrast = 'contrast' in text.lower() if text else False

    return {
        'code': code.code,
        'code_system': code.code_system,
        'body_region': body_region,
        'body_system': body_system,
        'procedure_category': procedure_category,
        'procedure_type': code.procedure_type,
        'complexity_level': complexity_level,
        'service_location': service_location,
        'em_level': em_level,
        'em_patient_type': em_patient_type,
        'surgical_approach': surgical_approach,
        'is_major_surgery': is_major,
        'imaging_modality': imaging_modality,
        'uses_contrast': uses_contrast,
    }


def populate_procedure_facets(
    db: Session,
    code_system: Optional[str] = None,
    batch_size: int = 100,
    force: bool = False
) -> int:
    """
    Populate facets for procedure codes.

    Args:
        db: Database session
        code_system: Filter by code system (CPT, HCPCS)
        batch_size: Number of codes to process in batch
        force: Regenerate facets even if they exist

    Returns:
        Number of codes processed
    """

    # Query codes without facets
    query = db.query(ProcedureCode)

    if code_system:
        query = query.filter(ProcedureCode.code_system == code_system)

    if not force:
        # Get codes that don't have facets yet
        existing_facets = db.query(ProcedureCodeFacet.code, ProcedureCodeFacet.code_system).all()
        existing_set = {(f.code, f.code_system) for f in existing_facets}

        # Filter out codes that already have facets
        all_codes = query.all()
        codes_to_process = [c for c in all_codes if (c.code, c.code_system) not in existing_set]
    else:
        codes_to_process = query.all()

    total = len(codes_to_process)

    if total == 0:
        logger.info("No codes to process")
        return 0

    logger.info(f"Processing {total} procedure codes...")

    processed = 0

    # Process in batches
    for i in tqdm(range(0, total, batch_size), desc="Generating facets"):
        batch = codes_to_process[i:i + batch_size]

        for code in batch:
            try:
                # Generate facets
                facet_data = generate_facets_for_code(code)

                # Check if facets already exist
                existing_facet = db.query(ProcedureCodeFacet).filter(
                    and_(
                        ProcedureCodeFacet.code == code.code,
                        ProcedureCodeFacet.code_system == code.code_system
                    )
                ).first()

                if existing_facet:
                    if force:
                        # Update existing
                        for key, value in facet_data.items():
                            setattr(existing_facet, key, value)
                else:
                    # Create new facet
                    facet = ProcedureCodeFacet(**facet_data)
                    db.add(facet)

                processed += 1

            except Exception as e:
                logger.error(f"Error processing code {code.code}: {e}")
                continue

        # Commit batch
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Error committing batch: {e}")
            db.rollback()

    logger.info(f"✓ Processed {processed} codes")

    return processed


def verify_facets(db: Session, code_system: Optional[str] = None) -> dict:
    """Verify facet generation results."""

    query = db.query(ProcedureCode)
    if code_system:
        query = query.filter(ProcedureCode.code_system == code_system)

    total_codes = query.count()

    facet_query = db.query(ProcedureCodeFacet)
    if code_system:
        facet_query = facet_query.filter(ProcedureCodeFacet.code_system == code_system)

    total_facets = facet_query.count()

    return {
        'total_codes': total_codes,
        'codes_with_facets': total_facets,
        'codes_without_facets': total_codes - total_facets,
        'coverage_percent': (total_facets / total_codes * 100) if total_codes > 0 else 0
    }


def show_sample_facets(db: Session, limit: int = 5):
    """Show sample codes with facets for verification."""

    facets = db.query(ProcedureCodeFacet).limit(limit).all()

    logger.info(f"\nSample procedure codes with facets:")

    for facet in facets:
        code = db.query(ProcedureCode).filter(
            and_(
                ProcedureCode.code == facet.code,
                ProcedureCode.code_system == facet.code_system
            )
        ).first()

        if code:
            logger.info(f"\n  Code: {code.code} ({code.code_system})")
            logger.info(f"  Description: {code.paraphrased_desc or code.short_desc}")
            logger.info(f"  Category: {facet.procedure_category}")
            logger.info(f"  Body System: {facet.body_system}")
            logger.info(f"  Complexity: {facet.complexity_level}")
            logger.info(f"  E/M Level: {facet.em_level}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate facets for procedure codes (CPT/HCPCS)"
    )
    parser.add_argument(
        "--code-system",
        type=str,
        choices=['CPT', 'HCPCS'],
        help="Code system to process (default: all)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for processing (default: 100)"
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
        logger.info(f"  With facets: {stats['codes_with_facets']}")
        logger.info(f"  Without facets: {stats['codes_without_facets']}")
        logger.info(f"  Coverage: {stats['coverage_percent']:.1f}%")

        if args.verify_only:
            logger.info("\nVerify-only mode - exiting")
            return 0

        if stats['codes_without_facets'] == 0 and not args.force:
            logger.info("\n✓ All codes already have facets")
            logger.info("  Use --force to regenerate facets")
            return 0

        # Generate facets
        logger.info(f"\n{'Regenerating' if args.force else 'Generating'} facets...")

        start_time = datetime.now()

        processed = populate_procedure_facets(
            db,
            code_system=args.code_system,
            batch_size=args.batch_size,
            force=args.force
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Verify again
        stats = verify_facets(db, args.code_system)

        logger.info(f"\n✓ Facet generation complete!")
        logger.info(f"  Codes processed: {processed}")
        logger.info(f"  Duration: {duration:.1f} seconds")
        logger.info(f"\nFinal status:")
        logger.info(f"  Total codes: {stats['total_codes']}")
        logger.info(f"  With facets: {stats['codes_with_facets']}")
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
