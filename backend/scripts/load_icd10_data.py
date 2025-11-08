#!/usr/bin/env python3
"""
Load ICD-10-CM data into database

This script parses downloaded ICD-10-CM files and loads them into the database.
It handles the official CMS file formats and populates:
- ICD-10 codes with descriptions
- Chapters and categories
- Hierarchical relationships (parent-child)

Run download_icd10_data.py first to download the data files.
"""

import os
import sys
import re
import logging
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from app.database import Base
from app.models.icd10_code import ICD10Code
from app.models.icd10_relation import ICD10Relation

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "icd10"


def get_database_url() -> str:
    """Get database URL from environment or use default."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/medcodeapi"
    )


def parse_icd10cm_tabular_file(file_path: Path) -> List[Dict]:
    """
    Parse ICD-10-CM tabular order file.

    The CMS file format is typically:
    - Fixed-width text file
    - Columns: Code (7 chars), Description (varies), etc.
    - May contain headers and section markers

    Args:
        file_path: Path to tabular file

    Returns:
        List of code dictionaries
    """
    codes = []
    current_chapter = None
    current_category = None

    logger.info(f"Parsing file: {file_path}")

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            # Skip empty lines
            if not line.strip():
                continue

            # Try to extract code and description
            # Format typically: "CODE    Description text"
            match = re.match(r'^([A-Z][0-9]{2}(?:\.[0-9A-Z]{1,4})?)\s+(.+)$', line.strip())

            if match:
                code = match.group(1)
                description = match.group(2).strip()

                # Determine if this is a chapter header
                if len(code) == 3 and code.endswith('00'):
                    # This might be a chapter/category marker
                    current_category = description
                    continue

                # Determine chapter from code prefix
                chapter = get_chapter_from_code(code)

                codes.append({
                    'code': code,
                    'description': description,
                    'chapter': chapter,
                    'category': current_category,
                    'code_system': 'ICD10-CM'
                })

            # Check for chapter headers (lines starting with "Chapter")
            elif line.strip().startswith('Chapter'):
                current_chapter = line.strip()

    logger.info(f"Parsed {len(codes)} codes from {file_path.name}")
    return codes


def parse_icd10cm_codes_file(file_path: Path) -> List[Dict]:
    """
    Parse ICD-10-CM codes file (XML format or tabular).

    CMS provides codes in different formats depending on the file.
    This handles the common tabular text format.

    Args:
        file_path: Path to codes file

    Returns:
        List of code dictionaries
    """
    codes = []

    logger.info(f"Parsing file: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        for line in lines:
            # Skip headers and empty lines
            if not line.strip() or line.startswith('#'):
                continue

            # Parse fixed-width format: CODE (7 chars) + SHORT DESC (60 chars) + LONG DESC (rest)
            # This format varies by year, so we use flexible regex
            parts = line.strip().split(None, 1)

            if len(parts) >= 2:
                code = parts[0]
                description = parts[1]

                # Validate ICD-10 code format
                if re.match(r'^[A-Z][0-9]{2}(?:\.[0-9A-Z]{1,4})?$', code):
                    chapter = get_chapter_from_code(code)

                    codes.append({
                        'code': code,
                        'description': description,
                        'chapter': chapter,
                        'code_system': 'ICD10-CM'
                    })

        logger.info(f"Parsed {len(codes)} codes from {file_path.name}")

    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")

    return codes


def get_chapter_from_code(code: str) -> str:
    """
    Get ICD-10 chapter name from code prefix.

    ICD-10 chapters are organized by first letter/number:
    A00-B99: Certain infectious and parasitic diseases
    C00-D49: Neoplasms
    D50-D89: Diseases of the blood and blood-forming organs
    E00-E89: Endocrine, nutritional and metabolic diseases
    F01-F99: Mental, behavioral and neurodevelopmental disorders
    G00-G99: Diseases of the nervous system
    H00-H59: Diseases of the eye and adnexa
    H60-H95: Diseases of the ear and mastoid process
    I00-I99: Diseases of the circulatory system
    J00-J99: Diseases of the respiratory system
    K00-K95: Diseases of the digestive system
    L00-L99: Diseases of the skin and subcutaneous tissue
    M00-M99: Diseases of the musculoskeletal system and connective tissue
    N00-N99: Diseases of the genitourinary system
    O00-O9A: Pregnancy, childbirth and the puerperium
    P00-P96: Certain conditions originating in the perinatal period
    Q00-Q99: Congenital malformations, deformations and chromosomal abnormalities
    R00-R99: Symptoms, signs and abnormal clinical and laboratory findings
    S00-T88: Injury, poisoning and certain other consequences of external causes
    V00-Y99: External causes of morbidity
    Z00-Z99: Factors influencing health status and contact with health services

    Args:
        code: ICD-10 code

    Returns:
        Chapter name
    """
    prefix = code[0]
    code_num = int(code[1:3]) if len(code) >= 3 else 0

    chapters = {
        'A': 'Certain infectious and parasitic diseases',
        'B': 'Certain infectious and parasitic diseases',
        'C': 'Neoplasms',
        'D': 'Diseases of the blood and blood-forming organs' if code_num >= 50 else 'Neoplasms',
        'E': 'Endocrine, nutritional and metabolic diseases',
        'F': 'Mental, behavioral and neurodevelopmental disorders',
        'G': 'Diseases of the nervous system',
        'H': 'Diseases of the eye and adnexa' if code_num < 60 else 'Diseases of the ear and mastoid process',
        'I': 'Diseases of the circulatory system',
        'J': 'Diseases of the respiratory system',
        'K': 'Diseases of the digestive system',
        'L': 'Diseases of the skin and subcutaneous tissue',
        'M': 'Diseases of the musculoskeletal system and connective tissue',
        'N': 'Diseases of the genitourinary system',
        'O': 'Pregnancy, childbirth and the puerperium',
        'P': 'Certain conditions originating in the perinatal period',
        'Q': 'Congenital malformations, deformations and chromosomal abnormalities',
        'R': 'Symptoms, signs and abnormal clinical and laboratory findings',
        'S': 'Injury, poisoning and certain other consequences of external causes',
        'T': 'Injury, poisoning and certain other consequences of external causes',
        'V': 'External causes of morbidity',
        'W': 'External causes of morbidity',
        'X': 'External causes of morbidity',
        'Y': 'External causes of morbidity',
        'Z': 'Factors influencing health status and contact with health services',
    }

    return chapters.get(prefix, 'Unknown')


def extract_parent_code(code: str) -> Optional[str]:
    """
    Extract parent code from ICD-10 code.

    ICD-10 hierarchy:
    - E11.9 -> parent is E11
    - E11.65 -> parent is E11.6
    - E11 -> no parent (category level)

    Args:
        code: ICD-10 code

    Returns:
        Parent code or None
    """
    if '.' not in code:
        # Category level (e.g., E11) - no parent
        return None

    parts = code.split('.')
    base = parts[0]
    decimal = parts[1]

    if len(decimal) > 1:
        # E11.65 -> E11.6
        return f"{base}.{decimal[:-1]}"
    else:
        # E11.9 -> E11
        return base


def create_relations(db: Session, codes: List[ICD10Code]) -> int:
    """
    Create parent-child relationships between codes.

    Args:
        db: Database session
        codes: List of ICD10Code objects

    Returns:
        Number of relations created
    """
    logger.info("Creating code relationships...")

    # Build code lookup
    code_lookup = {f"{c.code}_{c.code_system}": c for c in codes}

    relations_created = 0

    for code in codes:
        parent_code_str = extract_parent_code(code.code)

        if parent_code_str:
            # Check if parent exists
            parent_key = f"{parent_code_str}_{code.code_system}"

            if parent_key in code_lookup:
                # Create bidirectional relationship
                # Parent -> Child
                rel1 = ICD10Relation(
                    code=parent_code_str,
                    related_code=code.code,
                    relation_type='parent'
                )
                db.add(rel1)

                # Child -> Parent
                rel2 = ICD10Relation(
                    code=code.code,
                    related_code=parent_code_str,
                    relation_type='child'
                )
                db.add(rel2)

                relations_created += 2

    db.commit()
    logger.info(f"Created {relations_created} relationships")

    return relations_created


def load_codes_to_database(codes: List[Dict], db: Session, version_year: int = 2024) -> Tuple[int, int]:
    """
    Load parsed codes into database.

    Args:
        codes: List of code dictionaries
        db: Database session
        version_year: Year of ICD-10-CM release

    Returns:
        Tuple of (codes_added, codes_updated)
    """
    added = 0
    updated = 0

    logger.info(f"Loading {len(codes)} codes to database...")

    for code_data in codes:
        # Check if code already exists
        existing = db.query(ICD10Code).filter(
            and_(
                ICD10Code.code == code_data['code'],
                ICD10Code.code_system == code_data['code_system']
            )
        ).first()

        if existing:
            # Update existing code
            existing.short_desc = code_data['description']
            existing.long_desc = code_data['description']  # Same for now
            existing.chapter = code_data.get('chapter')
            existing.category = code_data.get('category')
            existing.version_year = version_year
            existing.is_active = True
            existing.last_updated = datetime.utcnow()
            updated += 1
        else:
            # Create new code
            new_code = ICD10Code(
                code=code_data['code'],
                code_system=code_data['code_system'],
                short_desc=code_data['description'],
                long_desc=code_data['description'],
                chapter=code_data.get('chapter'),
                category=code_data.get('category'),
                version_year=version_year,
                is_active=True,
                effective_date=date(version_year, 1, 1)
            )
            db.add(new_code)
            added += 1

        # Commit in batches of 1000
        if (added + updated) % 1000 == 0:
            db.commit()
            logger.info(f"Progress: {added + updated} codes processed")

    db.commit()
    logger.info(f"Loaded: {added} added, {updated} updated")

    return added, updated


def find_data_files(year: str = "2024") -> List[Path]:
    """
    Find all ICD-10-CM data files for a given year.

    Args:
        year: Year directory to search

    Returns:
        List of data file paths
    """
    year_dir = DATA_DIR / year

    if not year_dir.exists():
        logger.error(f"Data directory not found: {year_dir}")
        logger.info("Run download_icd10_data.py first to download the data")
        return []

    # Look for text files in subdirectories
    data_files = []

    for subdir in year_dir.iterdir():
        if subdir.is_dir():
            # Look for .txt files (common format for CMS data)
            txt_files = list(subdir.glob("*.txt"))
            data_files.extend(txt_files)

    logger.info(f"Found {len(data_files)} data files in {year_dir}")

    return data_files


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Load ICD-10-CM data into database"
    )
    parser.add_argument(
        "--year",
        type=str,
        default="2024",
        help="Year of ICD-10-CM data to load (default: 2024)"
    )
    parser.add_argument(
        "--db-url",
        type=str,
        help="Database URL (default: from DATABASE_URL env or local postgres)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse files but don't write to database"
    )

    args = parser.parse_args()

    # Find data files
    data_files = find_data_files(args.year)

    if not data_files:
        logger.error("No data files found. Run download_icd10_data.py first.")
        return 1

    # Parse all files
    all_codes = []

    for file_path in data_files:
        logger.info(f"\nProcessing: {file_path.name}")

        # Try different parsers based on filename patterns
        if 'tabular' in file_path.name.lower():
            codes = parse_icd10cm_tabular_file(file_path)
        else:
            codes = parse_icd10cm_codes_file(file_path)

        all_codes.extend(codes)

    # Remove duplicates (keep last occurrence)
    unique_codes = {}
    for code in all_codes:
        key = f"{code['code']}_{code['code_system']}"
        unique_codes[key] = code

    all_codes = list(unique_codes.values())
    logger.info(f"\nTotal unique codes: {len(all_codes)}")

    if args.dry_run:
        logger.info("Dry run - not writing to database")
        # Show sample
        logger.info("\nSample codes:")
        for code in all_codes[:10]:
            logger.info(f"  {code['code']}: {code['description'][:60]}")
        return 0

    # Connect to database
    db_url = args.db_url or get_database_url()
    logger.info(f"\nConnecting to database...")

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Load codes
        added, updated = load_codes_to_database(all_codes, db, int(args.year))

        # Get all loaded codes for relationship creation
        logger.info("\nFetching loaded codes for relationship creation...")
        loaded_codes = db.query(ICD10Code).filter(
            ICD10Code.code_system == 'ICD10-CM'
        ).all()

        # Create relationships
        relations = create_relations(db, loaded_codes)

        logger.info(f"\n✓ Load complete!")
        logger.info(f"  Codes added: {added}")
        logger.info(f"  Codes updated: {updated}")
        logger.info(f"  Relationships created: {relations}")

        return 0

    except Exception as e:
        logger.error(f"Error loading data: {e}", exc_info=True)
        db.rollback()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
