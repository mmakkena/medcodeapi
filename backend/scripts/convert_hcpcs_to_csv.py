#!/usr/bin/env python3
"""Convert HCPCS fixed-width text file to CSV format

This script reads the CMS HCPCS alpha-numeric file (fixed-width format)
and converts it to CSV format compatible with our procedure code loader.

Input: HCPC2025_JAN_ANWEB_*.txt (fixed-width 320-character records)
Output: hcpcs_2025_full.csv (CSV format)

Usage:
    python scripts/convert_hcpcs_to_csv.py --year 2025
"""

import os
import sys
import csv
import argparse
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "procedure_codes"


def parse_hcpcs_line(line: str) -> dict:
    """Parse a single line from HCPCS fixed-width file

    Fixed-width format (320 chars total):
    - Position 0-5 (5 chars): HCPCS code (right-aligned with leading spaces)
    - Position 5-10 (5 chars): Additional metadata
    - Position 10-11 (1 char): Flag
    - Position 11-91 (80 chars): Long description
    - Position 91-171 (80 chars): Short description
    - Position 171+: Additional metadata (pricing, dates, etc.)

    Args:
        line: Fixed-width record line

    Returns:
        Dictionary with parsed fields
    """
    # Fixed-width field positions
    code = line[0:5].strip()
    long_desc = line[11:91].strip()
    short_desc = line[91:171].strip()

    # Determine category based on code prefix
    category = determine_category(code)

    # Create paraphrased description (use long desc as base, fall back to short)
    paraphrased_desc = long_desc if long_desc else short_desc

    return {
        'code': code,
        'code_system': 'HCPCS',
        'paraphrased_desc': paraphrased_desc,
        'short_desc': short_desc if short_desc else '',
        'category': category,
        'license_status': 'free',  # HCPCS is public domain
        'version_year': '2025'
    }


def determine_category(code: str) -> str:
    """Determine HCPCS category based on code prefix

    HCPCS Level II code categories:
    - A codes: Medical supplies, transportation, administrative
    - B codes: Enteral and parenteral therapy
    - C codes: Outpatient PPS (hospital outpatient)
    - D codes: Dental procedures
    - E codes: Durable medical equipment (DME)
    - G codes: Procedures/services (temporary)
    - H codes: Alcohol and drug abuse treatment
    - J codes: Drugs (non-oral administration)
    - K codes: Temporary codes
    - L codes: Orthotics and prosthetics
    - M codes: Medical services
    - P codes: Pathology and laboratory
    - Q codes: Temporary codes
    - R codes: Diagnostic radiology
    - S codes: Temporary national codes
    - T codes: State Medicaid agency codes
    - V codes: Vision and hearing services

    Args:
        code: HCPCS code (5 chars, starting with letter)

    Returns:
        Category name
    """
    if not code:
        return 'Unknown'

    prefix = code[0].upper()

    categories = {
        'A': 'Supplies',
        'B': 'Enteral/Parenteral',
        'C': 'Outpatient PPS',
        'D': 'Dental',
        'E': 'Equipment',
        'G': 'Services',
        'H': 'Substance Abuse',
        'J': 'Drugs',
        'K': 'Temporary',
        'L': 'Orthotics/Prosthetics',
        'M': 'Medical Services',
        'P': 'Laboratory',
        'Q': 'Temporary',
        'R': 'Radiology',
        'S': 'Temporary',
        'T': 'State Codes',
        'V': 'Vision/Hearing'
    }

    return categories.get(prefix, 'Other')


def convert_hcpcs_to_csv(input_file: Path, output_file: Path) -> int:
    """Convert HCPCS fixed-width file to CSV

    Args:
        input_file: Path to HCPCS text file
        output_file: Path to output CSV file

    Returns:
        Number of codes processed
    """
    logger.info(f"Reading HCPCS data from: {input_file}")

    codes_processed = 0
    codes_data = []

    with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
        for line_num, line in enumerate(f, 1):
            try:
                # Skip empty lines
                if not line.strip():
                    continue

                # Parse line
                code_data = parse_hcpcs_line(line)

                # Skip if no valid code
                if not code_data['code']:
                    continue

                codes_data.append(code_data)
                codes_processed += 1

                # Log progress every 1000 codes
                if codes_processed % 1000 == 0:
                    logger.info(f"  Processed {codes_processed:,} codes...")

            except Exception as e:
                logger.warning(f"  Error parsing line {line_num}: {e}")
                continue

    # Write to CSV
    logger.info(f"\nWriting CSV to: {output_file}")

    fieldnames = ['code', 'code_system', 'paraphrased_desc', 'short_desc',
                  'category', 'license_status', 'version_year']

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(codes_data)

    return codes_processed


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Convert HCPCS fixed-width text file to CSV format"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2025,
        help="HCPCS year (default: 2025)"
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Input file path (optional, auto-detected if not provided)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (optional, defaults to hcpcs_{year}_full.csv)"
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("HCPCS Fixed-Width to CSV Converter")
    logger.info("=" * 70)
    logger.info(f"Year: {args.year}")
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info("=" * 70 + "\n")

    # Auto-detect input file if not provided
    if args.input:
        input_file = Path(args.input)
    else:
        # Look for HCPCS text file in data directory
        pattern = f"HCPC{args.year}_*_ANWEB_*.txt"
        matching_files = list(DATA_DIR.glob(pattern))

        if not matching_files:
            logger.error(f"No HCPCS text file found matching pattern: {pattern}")
            logger.info(f"  in directory: {DATA_DIR}")
            logger.info("\nPlease download HCPCS data first:")
            logger.info(f"  python scripts/download_procedure_data.py --hcpcs-only --year {args.year}")
            return 1

        input_file = matching_files[0]
        logger.info(f"Auto-detected input file: {input_file.name}\n")

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return 1

    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = DATA_DIR / f"hcpcs_{args.year}_full.csv"

    # Convert
    try:
        codes_count = convert_hcpcs_to_csv(input_file, output_file)

        logger.info("\n" + "=" * 70)
        logger.info("✅ Conversion completed successfully!")
        logger.info("=" * 70)
        logger.info(f"\nTotal codes processed: {codes_count:,}")
        logger.info(f"Output file: {output_file}")
        logger.info(f"File size: {output_file.stat().st_size:,} bytes")

        # Show sample codes
        logger.info("\n📋 Sample codes (first 5):")
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= 5:
                    break
                logger.info(f"  {row['code']:6} - {row['paraphrased_desc'][:60]}")

        logger.info("\n📊 Next steps:")
        logger.info("1. Load codes into database:")
        logger.info("   python scripts/load_procedure_codes.py")
        logger.info("\n2. Generate embeddings:")
        logger.info("   python scripts/generate_procedure_embeddings.py")
        logger.info("\n3. Populate facets:")
        logger.info("   python scripts/populate_procedure_facets.py")
        logger.info("=" * 70 + "\n")

        return 0

    except Exception as e:
        logger.error(f"\n✗ Conversion failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
