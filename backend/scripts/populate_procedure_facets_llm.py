#!/usr/bin/env python3
"""
Populate AI facets for procedure codes using Claude LLM

This script uses Claude API to generate high-accuracy clinical facets for procedure codes.
Much more accurate than rule-based classification (~90%+ vs ~50%).

Requirements:
- anthropic package: pip install anthropic
- ANTHROPIC_API_KEY environment variable

Cost estimate (Claude 3.5 Sonnet):
- ~8,642 codes × 500 tokens/request = ~4.3M tokens
- Input: $3/1M tokens, Output: $15/1M tokens
- Estimated: $50-75 for full dataset
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from tqdm import tqdm

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed")
    print("Install with: pip install anthropic")
    sys.exit(1)

from app.database import Base
from app.models.procedure_code import ProcedureCode
from app.models.procedure_code_facet import ProcedureCodeFacet

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Cost tracking
COST_PER_1M_INPUT_TOKENS = 3.00  # Claude 3.5 Sonnet
COST_PER_1M_OUTPUT_TOKENS = 15.00  # Claude 3.5 Sonnet


def get_database_url() -> str:
    """Get database URL from environment or use default."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/medcodeapi"
    )


def get_anthropic_client() -> anthropic.Anthropic:
    """Initialize Anthropic client with API key."""
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        logger.error("Get your API key from: https://console.anthropic.com")
        sys.exit(1)

    return anthropic.Anthropic(api_key=api_key)


CLASSIFICATION_PROMPT_TEMPLATE = """You are a medical coding expert specializing in CPT and HCPCS procedure codes. Your task is to classify this procedure code into clinical facets.

CODE INFORMATION:
Code: {code}
Code System: {code_system}
Description: {description}
Category: {category}

CLASSIFICATION TASK:
Analyze the code and description, then classify into the following facets. Use your medical knowledge and the description context.

FACET DEFINITIONS:

1. body_region (where the procedure is performed):
   - head_neck, thorax, abdomen, pelvis, spine, upper_extremity, lower_extremity, integumentary, multiple, or null

2. body_system (which body system):
   - cardiovascular, respiratory, digestive, musculoskeletal, nervous, genitourinary, endocrine, integumentary, eye, ear, hematologic, immune, or null

3. procedure_category (type of procedure):
   - evaluation (E/M, consultation, examination)
   - surgical (excision, repair, reconstruction)
   - diagnostic_imaging (xray, CT, MRI, ultrasound)
   - laboratory (blood tests, cultures, analysis)
   - therapeutic (injections, infusions, physical therapy)
   - preventive (screening, vaccination)
   - anesthesia
   - supplies (DME, prosthetics)
   - or null

4. complexity_level (procedure complexity):
   - simple, moderate, complex, highly_complex, or null

5. service_location (typical setting):
   - office, hospital_inpatient, hospital_outpatient, emergency, ambulatory, home, or null

6. em_level (for E/M codes only, based on MDM/time):
   - level_1, level_2, level_3, level_4, level_5, critical_care, consultation, or null

7. em_patient_type (for E/M codes only):
   - new_patient, established_patient, inpatient, outpatient, or null

8. imaging_modality (for imaging codes only):
   - xray, ct, mri, ultrasound, nuclear_medicine, pet, fluoroscopy, or null

9. surgical_approach (for surgical codes only):
   - open, laparoscopic, endoscopic, percutaneous, robotic, or null

10. is_major_surgery (boolean):
    - true if major/extensive surgery (e.g., bypass, transplant, major reconstruction)
    - false otherwise

11. uses_contrast (boolean, for imaging):
    - true if imaging uses contrast material
    - false otherwise

IMPORTANT RULES:
- Return ONLY valid JSON
- Use null for inapplicable facets
- Be conservative: if unsure, use null
- For E/M codes, always include em_level and em_patient_type
- For imaging codes, always include imaging_modality
- For surgical codes, always include surgical_approach and is_major_surgery

Return your classification as a JSON object with these exact keys:
{{
  "body_region": "...",
  "body_system": "...",
  "procedure_category": "...",
  "complexity_level": "...",
  "service_location": "...",
  "em_level": "...",
  "em_patient_type": "...",
  "imaging_modality": "...",
  "surgical_approach": "...",
  "is_major_surgery": false,
  "uses_contrast": false
}}"""


class CostTracker:
    """Track API usage and costs"""

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.requests = 0
        self.errors = 0
        self.start_time = datetime.now()

    def add_request(self, input_tokens: int, output_tokens: int):
        """Add request statistics"""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.requests += 1

    def add_error(self):
        """Increment error count"""
        self.errors += 1

    def get_cost(self) -> Dict[str, float]:
        """Calculate total cost"""
        input_cost = (self.total_input_tokens / 1_000_000) * COST_PER_1M_INPUT_TOKENS
        output_cost = (self.total_output_tokens / 1_000_000) * COST_PER_1M_OUTPUT_TOKENS
        total_cost = input_cost + output_cost

        return {
            'input_cost': round(input_cost, 2),
            'output_cost': round(output_cost, 2),
            'total_cost': round(total_cost, 2)
        }

    def get_stats(self) -> Dict:
        """Get full statistics"""
        duration = (datetime.now() - self.start_time).total_seconds()
        cost = self.get_cost()

        return {
            'requests': self.requests,
            'errors': self.errors,
            'success_rate': f"{((self.requests - self.errors) / max(self.requests, 1) * 100):.1f}%",
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
            'total_tokens': self.total_input_tokens + self.total_output_tokens,
            'duration_seconds': round(duration, 1),
            'requests_per_minute': round((self.requests / max(duration, 1)) * 60, 1),
            'cost': cost
        }


def generate_facets_with_claude(
    client: anthropic.Anthropic,
    code: ProcedureCode,
    cost_tracker: CostTracker,
    model: str = "claude-3-5-sonnet-20241022"
) -> Optional[Dict]:
    """
    Generate facets for a procedure code using Claude API.

    Args:
        client: Anthropic API client
        code: ProcedureCode object
        cost_tracker: Cost tracking object
        model: Claude model to use

    Returns:
        Dictionary of facets or None if failed
    """

    # Get best available description
    description = code.paraphrased_desc or code.short_desc or code.long_desc or "No description available"

    # Create prompt
    prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(
        code=code.code,
        code_system=code.code_system,
        description=description,
        category=code.category or "Not specified"
    )

    try:
        # Call Claude API
        response = client.messages.create(
            model=model,
            max_tokens=600,
            temperature=0,  # Deterministic for consistency
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Track usage
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost_tracker.add_request(input_tokens, output_tokens)

        # Extract response text
        response_text = response.content[0].text

        # Parse JSON
        # Claude sometimes wraps JSON in markdown, so extract it
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        facets = json.loads(response_text.strip())

        # Validate required keys exist
        required_keys = [
            'body_region', 'body_system', 'procedure_category', 'complexity_level',
            'service_location', 'em_level', 'em_patient_type', 'imaging_modality',
            'surgical_approach', 'is_major_surgery', 'uses_contrast'
        ]

        for key in required_keys:
            if key not in facets:
                facets[key] = None

        return facets

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error for code {code.code}: {e}")
        logger.error(f"Response: {response_text[:200]}")
        cost_tracker.add_error()
        return None

    except anthropic.APIError as e:
        logger.error(f"API error for code {code.code}: {e}")
        cost_tracker.add_error()
        return None

    except Exception as e:
        logger.error(f"Unexpected error for code {code.code}: {e}")
        cost_tracker.add_error()
        return None


def populate_procedure_facets_llm(
    db: Session,
    client: anthropic.Anthropic,
    code_system: Optional[str] = None,
    batch_size: int = 50,
    rate_limit_per_minute: int = 50,
    force: bool = False,
    model: str = "claude-3-5-sonnet-20241022",
    max_codes: Optional[int] = None
) -> int:
    """
    Populate facets using Claude LLM.

    Args:
        db: Database session
        client: Anthropic client
        code_system: Filter by code system (CPT, HCPCS)
        batch_size: Codes per batch before commit
        rate_limit_per_minute: API requests per minute
        force: Regenerate even if facets exist
        model: Claude model to use
        max_codes: Maximum codes to process (for testing)

    Returns:
        Number of codes processed
    """

    cost_tracker = CostTracker()

    # Query codes without facets
    query = db.query(ProcedureCode)

    if code_system:
        query = query.filter(ProcedureCode.code_system == code_system)

    if not force:
        # Get codes without facets
        existing_facets = db.query(ProcedureCodeFacet.code, ProcedureCodeFacet.code_system).all()
        existing_set = {(f.code, f.code_system) for f in existing_facets}

        all_codes = query.all()
        codes_to_process = [c for c in all_codes if (c.code, c.code_system) not in existing_set]
    else:
        codes_to_process = query.all()

    # Apply max_codes limit for testing
    if max_codes:
        codes_to_process = codes_to_process[:max_codes]

    total = len(codes_to_process)

    if total == 0:
        logger.info("No codes to process")
        return 0

    logger.info(f"Processing {total} procedure codes with Claude...")
    logger.info(f"Model: {model}")
    logger.info(f"Rate limit: {rate_limit_per_minute} requests/minute")

    if max_codes:
        logger.warning(f"TEST MODE: Processing only first {max_codes} codes")

    processed = 0
    request_times = []

    # Calculate delay between requests for rate limiting
    delay_between_requests = 60.0 / rate_limit_per_minute

    # Process codes
    with tqdm(total=total, desc="Generating facets with Claude") as pbar:
        for i, code in enumerate(codes_to_process):
            try:
                # Rate limiting: track request times
                current_time = time.time()

                # Remove times older than 1 minute
                request_times = [t for t in request_times if current_time - t < 60]

                # If we've hit rate limit, wait
                if len(request_times) >= rate_limit_per_minute:
                    wait_time = 60 - (current_time - request_times[0])
                    if wait_time > 0:
                        logger.info(f"Rate limit reached, waiting {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        request_times = []

                # Generate facets with Claude
                facet_data = generate_facets_with_claude(client, code, cost_tracker, model)

                request_times.append(time.time())

                if facet_data:
                    # Add code identifiers
                    facet_data['code'] = code.code
                    facet_data['code_system'] = code.code_system

                    # Check if facets exist
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

                # Commit in batches
                if (i + 1) % batch_size == 0:
                    try:
                        db.commit()

                        # Log progress
                        stats = cost_tracker.get_stats()
                        logger.info(f"Progress: {processed}/{total} ({processed/total*100:.1f}%) | "
                                  f"Cost: ${stats['cost']['total_cost']:.2f} | "
                                  f"Rate: {stats['requests_per_minute']:.1f} req/min")
                    except Exception as e:
                        logger.error(f"Error committing batch: {e}")
                        db.rollback()

                pbar.update(1)

                # Small delay between requests
                time.sleep(delay_between_requests)

            except Exception as e:
                logger.error(f"Error processing code {code.code}: {e}")
                cost_tracker.add_error()
                continue

    # Final commit
    try:
        db.commit()
    except Exception as e:
        logger.error(f"Error on final commit: {e}")
        db.rollback()

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
    """Show sample codes with facets."""

    facets = db.query(ProcedureCodeFacet).limit(limit).all()

    logger.info(f"\nSample procedure codes with LLM-generated facets:")

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
        description="Generate high-accuracy facets for procedure codes using Claude LLM"
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
        default=50,
        help="Batch size for database commits (default: 50)"
    )
    parser.add_argument(
        "--rate-limit",
        type=int,
        default=50,
        help="API requests per minute (default: 50)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="claude-3-5-sonnet-20241022",
        choices=[
            "claude-3-5-sonnet-20241022",
            "claude-3-haiku-20240307"
        ],
        help="Claude model to use (default: claude-3-5-sonnet-20241022)"
    )
    parser.add_argument(
        "--db-url",
        type=str,
        help="Database URL (default: from DATABASE_URL env)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate facets even if they exist"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing facets"
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Show sample facets after generation"
    )
    parser.add_argument(
        "--test",
        type=int,
        metavar="N",
        help="Test mode: only process N codes"
    )

    args = parser.parse_args()

    # Connect to database
    db_url = args.db_url or get_database_url()
    logger.info(f"Connecting to database...")

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # Initialize Anthropic client
    try:
        client = get_anthropic_client()
        logger.info("✓ Anthropic client initialized")
    except SystemExit:
        return 1

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

        # Estimate cost
        codes_to_process = stats['codes_without_facets'] if not args.force else stats['total_codes']
        if args.test:
            codes_to_process = min(codes_to_process, args.test)

        estimated_tokens = codes_to_process * 500
        estimated_cost = (estimated_tokens / 1_000_000) * (COST_PER_1M_INPUT_TOKENS + COST_PER_1M_OUTPUT_TOKENS)

        logger.info(f"\nEstimated cost for {codes_to_process} codes:")
        logger.info(f"  Model: {args.model}")
        logger.info(f"  Estimated tokens: ~{estimated_tokens:,}")
        logger.info(f"  Estimated cost: ${estimated_cost:.2f}")

        if args.test:
            logger.warning(f"\n⚠️  TEST MODE: Will only process {args.test} codes")

        # Confirm before proceeding
        if not args.test:
            response = input("\nProceed with LLM facet generation? (y/n): ")
            if response.lower() != 'y':
                logger.info("Cancelled")
                return 0

        # Generate facets
        logger.info(f"\n{'Regenerating' if args.force else 'Generating'} facets with Claude...")

        start_time = datetime.now()

        processed = populate_procedure_facets_llm(
            db,
            client,
            code_system=args.code_system,
            batch_size=args.batch_size,
            rate_limit_per_minute=args.rate_limit,
            force=args.force,
            model=args.model,
            max_codes=args.test
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Verify again
        stats = verify_facets(db, args.code_system)

        logger.info(f"\n✓ LLM facet generation complete!")
        logger.info(f"  Codes processed: {processed}")
        logger.info(f"  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
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
