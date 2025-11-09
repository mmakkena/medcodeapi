#!/usr/bin/env python3
"""
Parse ICD-10-CM guideline PDFs and extract code-specific guidance

This script extracts coding guidelines, clinical notes, and coding tips
from the official ICD-10-CM guideline PDFs and associates them with
specific codes in the database.

Requirements:
- PyPDF2 or pdfplumber for PDF extraction
- Database with ICD-10 codes loaded
"""

import os
import sys
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from app.database import Base
from app.models.icd10_code import ICD10Code

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


def extract_pdf_text(pdf_path: Path) -> str:
    """
    Extract text from PDF file.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text content
    """
    try:
        # Try pdfplumber first (better text extraction)
        import pdfplumber

        logger.info(f"Extracting text from {pdf_path.name} using pdfplumber...")
        text = ""

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

                if page_num % 10 == 0:
                    logger.info(f"  Processed {page_num}/{len(pdf.pages)} pages")

        logger.info(f"✓ Extracted {len(text)} characters from {pdf_path.name}")
        return text

    except ImportError:
        # Fallback to PyPDF2
        try:
            import PyPDF2

            logger.info(f"Extracting text from {pdf_path.name} using PyPDF2...")
            text = ""

            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

                    if page_num % 10 == 0:
                        logger.info(f"  Processed {page_num}/{len(pdf_reader.pages)} pages")

            logger.info(f"✓ Extracted {len(text)} characters from {pdf_path.name}")
            return text

        except ImportError:
            logger.error("Neither pdfplumber nor PyPDF2 is installed")
            logger.error("Install with: pip install pdfplumber")
            raise RuntimeError("PDF extraction library not available")


def extract_code_pattern(text: str) -> List[str]:
    """
    Extract ICD-10 code patterns from text.

    Args:
        text: Text to search

    Returns:
        List of found ICD-10 codes
    """
    # Pattern for ICD-10 codes: Letter followed by 2 digits, optional decimal and more digits
    pattern = r'\b([A-Z]\d{2}(?:\.\d{1,4})?)\b'
    codes = re.findall(pattern, text)
    return list(set(codes))  # Remove duplicates


def parse_guideline_sections(text: str) -> Dict[str, str]:
    """
    Parse guideline text into sections.

    Args:
        text: Full guideline text

    Returns:
        Dictionary mapping section names to content
    """
    sections = {}

    # Common section headers in ICD-10-CM guidelines
    section_patterns = [
        r'Section\s+[IVX]+[A-Z]?\.\s+(.+?)(?=Section\s+[IVX]+|$)',
        r'Chapter\s+\d+\s+(.+?)(?=Chapter\s+\d+|$)',
        r'(\d+\.\s+.+?)(?=\d+\.|$)',
    ]

    for pattern in section_patterns:
        matches = re.finditer(pattern, text, re.DOTALL | re.MULTILINE)
        for match in matches:
            section_name = match.group(1).strip()[:100]  # Limit length
            sections[section_name] = match.group(0).strip()

    return sections


def extract_coding_guidelines(text: str, code: str) -> Optional[str]:
    """
    Extract coding guidelines for a specific code.

    Args:
        text: Guideline text
        code: ICD-10 code to search for

    Returns:
        Relevant guideline text or None
    """
    # Search for code mentions with surrounding context
    pattern = rf'(.{{0,500}}\b{re.escape(code)}\b.{{0,500}})'
    matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)

    if matches:
        # Join and clean up matches
        guidelines = ' '.join(matches)
        # Clean up excessive whitespace
        guidelines = re.sub(r'\s+', ' ', guidelines).strip()
        # Limit length to avoid database issues
        return guidelines[:2000] if len(guidelines) > 2000 else guidelines

    return None


def extract_clinical_context(text: str, code: str) -> Optional[str]:
    """
    Extract clinical context for a specific code.

    Args:
        text: Guideline text
        code: ICD-10 code

    Returns:
        Clinical context or None
    """
    # Look for clinical indicator keywords near the code
    clinical_keywords = [
        'clinical', 'diagnosis', 'condition', 'disease', 'disorder',
        'symptom', 'treatment', 'patient', 'medical'
    ]

    pattern = rf'(.{{0,300}}\b(?:{"|".join(clinical_keywords)})\b.{{0,300}}\b{re.escape(code)}\b.{{0,300}})'
    matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)

    if matches:
        context = ' '.join(matches)
        context = re.sub(r'\s+', ' ', context).strip()
        return context[:1500] if len(context) > 1500 else context

    return None


def extract_coding_tips(text: str, code: str) -> Optional[str]:
    """
    Extract coding tips for a specific code.

    Args:
        text: Guideline text
        code: ICD-10 code

    Returns:
        Coding tips or None
    """
    # Look for instructional keywords near the code
    tip_keywords = [
        'code', 'assign', 'use', 'report', 'note', 'instruction',
        'guideline', 'convention', 'rule', 'should', 'must'
    ]

    pattern = rf'(.{{0,300}}\b(?:{"|".join(tip_keywords)})\b.{{0,300}}\b{re.escape(code)}\b.{{0,300}})'
    matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)

    if matches:
        tips = ' '.join(matches)
        tips = re.sub(r'\s+', ' ', tips).strip()
        return tips[:1500] if len(tips) > 1500 else tips

    return None


def update_code_guidelines(
    db: Session,
    code: str,
    version_year: int,
    coding_guidelines: Optional[str] = None,
    clinical_notes: Optional[str] = None,
    coding_tips: Optional[str] = None
) -> bool:
    """
    Update guideline information for a code.

    Args:
        db: Database session
        code: ICD-10 code
        version_year: Year of guidelines
        coding_guidelines: Coding guidelines text
        clinical_notes: Clinical notes text
        coding_tips: Coding tips text

    Returns:
        True if updated, False if code not found
    """
    # Find code in database
    code_obj = db.query(ICD10Code).filter(
        and_(
            ICD10Code.code == code,
            ICD10Code.version_year == version_year
        )
    ).first()

    if not code_obj:
        return False

    # Update guideline fields
    if coding_guidelines:
        code_obj.coding_guidelines = coding_guidelines
    if clinical_notes:
        code_obj.clinical_notes = clinical_notes
    if coding_tips:
        code_obj.coding_tips = coding_tips

    code_obj.last_updated = datetime.utcnow()

    return True


def parse_guidelines_for_year(
    year: str,
    db: Session,
    dry_run: bool = False
) -> Tuple[int, int]:
    """
    Parse guidelines for a specific year.

    Args:
        year: Year to process
        db: Database session
        dry_run: If True, don't save to database

    Returns:
        Tuple of (codes_found, codes_updated)
    """
    year_dir = DATA_DIR / year

    if not year_dir.exists():
        logger.error(f"Data directory not found: {year_dir}")
        return 0, 0

    # Find guideline PDFs
    pdf_files = list(year_dir.glob("**/*guideline*.pdf"))

    if not pdf_files:
        logger.warning(f"No guideline PDFs found in {year_dir}")
        return 0, 0

    logger.info(f"Found {len(pdf_files)} guideline PDF(s)")

    codes_found = 0
    codes_updated = 0

    for pdf_file in pdf_files:
        logger.info(f"\nProcessing: {pdf_file.name}")

        try:
            # Extract text from PDF
            text = extract_pdf_text(pdf_file)

            # Find all codes mentioned in guidelines
            mentioned_codes = extract_code_pattern(text)
            logger.info(f"Found {len(mentioned_codes)} code mentions in guidelines")

            # Process each code
            for code in mentioned_codes:
                codes_found += 1

                # Extract different types of guidance
                guidelines = extract_coding_guidelines(text, code)
                clinical = extract_clinical_context(text, code)
                tips = extract_coding_tips(text, code)

                if any([guidelines, clinical, tips]):
                    if not dry_run:
                        updated = update_code_guidelines(
                            db, code, int(year),
                            coding_guidelines=guidelines,
                            clinical_notes=clinical,
                            coding_tips=tips
                        )

                        if updated:
                            codes_updated += 1

                            if codes_updated % 50 == 0:
                                db.commit()
                                logger.info(f"Progress: {codes_updated} codes updated")
                    else:
                        # Dry run - just log
                        logger.info(f"  {code}: G={bool(guidelines)}, C={bool(clinical)}, T={bool(tips)}")

            if not dry_run:
                db.commit()

        except Exception as e:
            logger.error(f"Error processing {pdf_file.name}: {e}")
            if not dry_run:
                db.rollback()
            continue

    return codes_found, codes_updated


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse ICD-10-CM guideline PDFs and extract code-specific guidance"
    )
    parser.add_argument(
        "--year",
        type=str,
        default="2026",
        help="Year of guidelines to parse (default: 2026)"
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

    # Connect to database
    db_url = args.db_url or get_database_url()
    logger.info(f"Connecting to database...")

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        logger.info(f"\nParsing {args.year} ICD-10-CM guidelines...")

        start_time = datetime.now()

        codes_found, codes_updated = parse_guidelines_for_year(
            args.year,
            db,
            dry_run=args.dry_run
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        if args.dry_run:
            logger.info(f"\n✓ Dry run complete!")
        else:
            logger.info(f"\n✓ Guideline parsing complete!")

        logger.info(f"  Codes found in guidelines: {codes_found}")
        logger.info(f"  Codes updated in database: {codes_updated}")
        logger.info(f"  Duration: {duration:.1f} seconds")

        if codes_updated > 0:
            logger.info(f"  Rate: {codes_updated/duration:.1f} codes/second")

        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
