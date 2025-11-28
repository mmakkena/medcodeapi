#!/usr/bin/env python3
"""
Load CDI Guidelines to PostgreSQL

Loads CDI guideline documents (PDFs) from CDIAgent into the PostgreSQL
database. Documents are chunked for semantic search with embeddings.

Usage:
    python scripts/load_cdi_guidelines.py [--source PATH] [--generate-embeddings]

Source: CDIAgent/cdi_documents/
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Generator

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from infrastructure.db.postgres import SessionLocal, engine
from infrastructure.db.models.knowledge_base import CDIGuideline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default source path - CDIAgent is a sibling project
DEFAULT_SOURCE = Path("/Users/murali.local/CDIAgent/cdi_documents")

# Document categorization mapping
DOCUMENT_CATEGORIES = {
    'acdis': {'category': 'best_practices', 'subcategory': 'acdis_guidelines'},
    'ahima': {'category': 'query_writing', 'subcategory': 'ahima_toolkit'},
    'inpatient-query': {'category': 'query_writing', 'subcategory': 'inpatient'},
    'outpatient-query': {'category': 'query_writing', 'subcategory': 'outpatient'},
    'toolkit': {'category': 'reference', 'subcategory': 'toolkit'},
    'drg': {'category': 'coding', 'subcategory': 'drg'},
    'hac': {'category': 'quality', 'subcategory': 'hac_poa'},
    'quality': {'category': 'quality', 'subcategory': 'measures'},
    'respiratory': {'category': 'clinical', 'subcategory': 'respiratory'},
    'nephrology': {'category': 'clinical', 'subcategory': 'nephrology'},
}

# Chunk configuration
CHUNK_SIZE = 1000  # characters
CHUNK_OVERLAP = 200  # characters


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text content from a PDF file.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text content
    """
    try:
        import pdfplumber

        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"[Page {page_num}]\n{page_text}")

        return "\n\n".join(text_parts)

    except ImportError:
        logger.error("pdfplumber not installed. Install with: pip install pdfplumber")
        raise
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
        return ""


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
) -> Generator[tuple[int, str], None, None]:
    """
    Split text into overlapping chunks.

    Args:
        text: Text to chunk
        chunk_size: Target chunk size in characters
        overlap: Overlap between chunks

    Yields:
        Tuples of (chunk_index, chunk_text)
    """
    if not text:
        return

    # Split into paragraphs first
    paragraphs = text.split('\n\n')

    current_chunk = ""
    chunk_index = 0

    for para in paragraphs:
        # If adding this paragraph would exceed chunk size, yield current chunk
        if len(current_chunk) + len(para) > chunk_size and current_chunk:
            yield chunk_index, current_chunk.strip()
            chunk_index += 1

            # Keep overlap from previous chunk
            if overlap > 0 and len(current_chunk) > overlap:
                current_chunk = current_chunk[-overlap:] + "\n\n" + para
            else:
                current_chunk = para
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para

    # Yield final chunk
    if current_chunk.strip():
        yield chunk_index, current_chunk.strip()


def categorize_document(filename: str) -> dict:
    """
    Determine category and subcategory based on filename.

    Args:
        filename: PDF filename

    Returns:
        Dict with category, subcategory, and tags
    """
    filename_lower = filename.lower()

    for keyword, categorization in DOCUMENT_CATEGORIES.items():
        if keyword in filename_lower:
            return {
                'category': categorization['category'],
                'subcategory': categorization['subcategory'],
                'tags': [keyword]
            }

    # Default categorization
    return {
        'category': 'reference',
        'subcategory': 'general',
        'tags': []
    }


def extract_section_title(chunk_text: str) -> Optional[str]:
    """
    Try to extract a section title from chunk text.

    Args:
        chunk_text: Text chunk

    Returns:
        Section title if found, else None
    """
    lines = chunk_text.split('\n')

    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()
        # Look for potential section headers (short lines, often uppercase)
        if len(line) > 5 and len(line) < 100:
            if line.isupper() or (line[0].isupper() and ':' not in line):
                return line

    return None


def load_cdi_guidelines(
    db: Session,
    source_path: Path,
    clear_existing: bool = False,
    generate_embeddings: bool = False,
    file_pattern: str = "*.pdf"
) -> int:
    """
    Load CDI guideline documents into the database.

    Args:
        db: Database session
        source_path: Path to documents directory
        clear_existing: Whether to clear existing records
        generate_embeddings: Whether to generate vector embeddings
        file_pattern: Glob pattern for files to process

    Returns:
        Number of chunks loaded
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Source directory not found: {source_path}")

    # Find all PDF files (including subdirectories)
    pdf_files = list(source_path.rglob(file_pattern))
    logger.info(f"Found {len(pdf_files)} PDF files in {source_path}")

    if clear_existing:
        logger.info("Clearing existing CDI guidelines...")
        db.query(CDIGuideline).delete()
        db.commit()

    total_chunks = 0
    errors = 0

    for pdf_path in pdf_files:
        try:
            logger.info(f"Processing: {pdf_path.name}")

            # Extract text
            text = extract_text_from_pdf(pdf_path)
            if not text:
                logger.warning(f"No text extracted from {pdf_path.name}")
                continue

            # Get categorization
            categorization = categorize_document(pdf_path.name)

            # Determine document type
            doc_type = 'practice_brief' if 'practice' in pdf_path.name.lower() else \
                       'toolkit' if 'toolkit' in pdf_path.name.lower() else \
                       'reference'

            # Process chunks
            for chunk_index, chunk_text in chunk_text(text):
                section_title = extract_section_title(chunk_text)

                record = CDIGuideline(
                    source_document=pdf_path.name,
                    document_type=doc_type,
                    section_title=section_title,
                    content=chunk_text,
                    chunk_index=chunk_index,
                    category=categorization['category'],
                    subcategory=categorization['subcategory'],
                    tags=categorization['tags'],
                    page_number=None,  # Could extract from [Page X] markers
                    source_url=None,
                    publication_date=None
                )
                db.add(record)
                total_chunks += 1

            db.commit()
            logger.info(f"  Loaded {chunk_index + 1} chunks from {pdf_path.name}")

        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            errors += 1
            db.rollback()

    logger.info(f"Total chunks loaded: {total_chunks}")
    logger.info(f"Errors: {errors}")

    # Generate embeddings if requested
    if generate_embeddings:
        logger.info("Generating embeddings for CDI guidelines...")
        generate_guideline_embeddings(db)

    return total_chunks


def generate_guideline_embeddings(db: Session, batch_size: int = 50):
    """Generate vector embeddings for CDI guidelines."""
    try:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model...")
        model = SentenceTransformer('ncbi/MedCPT-Query-Encoder')

        # Get guidelines without embeddings
        guidelines = db.query(CDIGuideline).filter(
            CDIGuideline.embedding == None
        ).all()
        logger.info(f"Generating embeddings for {len(guidelines)} chunks...")

        for i, guideline in enumerate(guidelines):
            # Create embedding text
            text = f"{guideline.section_title or ''} {guideline.content[:500]}"  # Limit content length

            # Generate embedding
            embedding = model.encode(text, normalize_embeddings=True)
            guideline.embedding = embedding.tolist()

            if (i + 1) % batch_size == 0:
                logger.info(f"Processed {i + 1}/{len(guidelines)} chunks")
                db.commit()

        db.commit()
        logger.info("Embeddings generated successfully")

    except ImportError:
        logger.warning("sentence-transformers not installed. Skipping embedding generation.")
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")


def main():
    parser = argparse.ArgumentParser(description="Load CDI guidelines to PostgreSQL")
    parser.add_argument(
        '--source',
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Path to cdi_documents directory (default: {DEFAULT_SOURCE})"
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help="Clear existing guidelines before loading"
    )
    parser.add_argument(
        '--generate-embeddings',
        action='store_true',
        help="Generate vector embeddings for semantic search"
    )
    parser.add_argument(
        '--pattern',
        default="*.pdf",
        help="File pattern to match (default: *.pdf)"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("CDI Guidelines Loader")
    logger.info("=" * 60)

    db = SessionLocal()

    try:
        # Ensure table exists
        from infrastructure.db.models.knowledge_base import CDIGuideline
        CDIGuideline.__table__.create(engine, checkfirst=True)

        # Load guidelines
        count = load_cdi_guidelines(
            db,
            args.source,
            clear_existing=args.clear,
            generate_embeddings=args.generate_embeddings,
            file_pattern=args.pattern
        )

        logger.info(f"Successfully loaded {count} guideline chunks")

    except Exception as e:
        logger.error(f"Failed to load CDI guidelines: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
