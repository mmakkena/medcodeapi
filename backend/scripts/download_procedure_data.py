#!/usr/bin/env python3
"""Download procedure code data (HCPCS and CPT framework)

This script downloads publicly available procedure code data:
- HCPCS Level II codes from CMS (public domain)
- CPT code numbers only (descriptions require AMA license)

For full CPT descriptions, you must:
1. Purchase AMA CPT license
2. Download licensed data file
3. Place in data/procedure_codes/cpt_licensed/
4. Run with --process-licensed flag

Data sources:
- HCPCS: https://www.cms.gov/medicare/coding-billing/healthcare-common-procedure-system
- CPT: https://www.ama-assn.org/practice-management/cpt (license required)
"""

import os
import sys
import csv
import requests
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "procedure_codes"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def download_file(url: str, dest_path: Path, description: str = "") -> bool:
    """Download a file from URL to destination path

    Args:
        url: URL to download from
        dest_path: Destination file path
        description: Description for logging

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Downloading {description or url}...")
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(dest_path, 'wb') as f:
            if total_size == 0:
                f.write(response.content)
            else:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if downloaded % (8192 * 100) == 0:  # Log every ~800KB
                            percent = (downloaded / total_size) * 100
                            logger.info(f"  Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)")

        logger.info(f"✓ Downloaded successfully to {dest_path}")
        return True

    except Exception as e:
        logger.error(f"✗ Failed to download {url}: {e}")
        return False


def download_hcpcs_data(year: int = 2025) -> bool:
    """Download HCPCS Level II codes from CMS

    HCPCS codes are public domain and include:
    - A codes: Medical supplies
    - B codes: Enteral/parenteral therapy
    - C codes: Outpatient PPS
    - D codes: Dental procedures
    - E codes: Durable medical equipment
    - G codes: Procedures/services
    - H codes: Alcohol/drug abuse
    - J codes: Drugs (non-oral)
    - K codes: Temporary codes
    - L codes: Orthotics/prosthetics
    - M codes: Medical services
    - P codes: Pathology/laboratory
    - Q codes: Temporary codes
    - R codes: Diagnostic radiology
    - S codes: Temporary national codes
    - T codes: State Medicaid codes
    - V codes: Vision/hearing services

    Args:
        year: HCPCS year (default: 2025)

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"Downloading HCPCS {year} Data from CMS")
    logger.info(f"{'='*70}\n")

    # CMS HCPCS file URL (updated annually)
    # Note: CMS releases HCPCS data in various formats (Excel, text files)
    # The URL pattern changes annually - check CMS website for current URL

    hcpcs_urls = {
        2025: "https://www.cms.gov/files/zip/january-2025-alpha-numeric-hcpcs-file.zip",
        2024: "https://www.cms.gov/files/zip/2024-alpha-numeric-hcpcs-file.zip",
    }

    if year not in hcpcs_urls:
        logger.error(f"No HCPCS URL configured for year {year}")
        logger.info(f"Available years: {', '.join(map(str, hcpcs_urls.keys()))}")
        logger.info("\nManual download instructions:")
        logger.info("1. Visit: https://www.cms.gov/medicare/coding-billing/healthcare-common-procedure-system")
        logger.info(f"2. Download HCPCS {year} data file")
        logger.info(f"3. Save to: {DATA_DIR}/hcpcs_{year}_download.xlsx")
        logger.info("4. Run this script with --process-manual flag")
        return False

    url = hcpcs_urls[year]
    zip_file = DATA_DIR / f"hcpcs_{year}_download.zip"

    # Download HCPCS ZIP file
    logger.info("Note: CMS URL may change. If download fails, visit CMS website for current link.")
    success = download_file(url, zip_file, f"HCPCS {year} data")

    if success:
        logger.info(f"\n✓ HCPCS {year} data downloaded")
        logger.info(f"  File: {zip_file}")
        logger.info(f"  Next step: Extract and convert to CSV format")
        logger.info(f"\n  Run: python scripts/convert_hcpcs_to_csv.py --year {year}")

    return success


def create_cpt_template(year: int = 2025) -> bool:
    """Create CPT code template file

    This creates a template showing the CPT code structure.
    For actual CPT descriptions, an AMA license is required.

    CPT Code Categories:
    - Category I: 00100-99499 (10,000+ codes)
      - E/M: 99201-99499
      - Anesthesia: 00100-01999
      - Surgery: 10004-69990
      - Radiology: 70010-79999
      - Pathology/Laboratory: 80047-89398
      - Medicine: 90281-99607
    - Category II: 0001F-9007F (Performance measures)
    - Category III: 0001T-0794T (Emerging technology)

    Args:
        year: CPT year (default: 2025)

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"Creating CPT {year} Template")
    logger.info(f"{'='*70}\n")

    template_file = DATA_DIR / f"cpt_{year}_template.csv"

    # CPT code ranges (numbers only - not copyrighted)
    cpt_template = [
        {"code": "99201", "category": "E/M", "range": "Office visit - new patient", "license_needed": True},
        {"code": "99211", "category": "E/M", "range": "Office visit - established patient", "license_needed": True},
        {"code": "00100", "category": "Anesthesia", "range": "Anesthesia procedures", "license_needed": True},
        {"code": "10004", "category": "Surgery", "range": "Surgical procedures", "license_needed": True},
        {"code": "70010", "category": "Radiology", "range": "Diagnostic imaging", "license_needed": True},
        {"code": "80047", "category": "Laboratory", "range": "Lab tests and panels", "license_needed": True},
        {"code": "90281", "category": "Medicine", "range": "Medical services", "license_needed": True},
    ]

    with open(template_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['code', 'category', 'range', 'license_needed'])
        writer.writeheader()
        writer.writerows(cpt_template)

    logger.info(f"✓ CPT template created: {template_file}")
    logger.info(f"\n{'='*70}")
    logger.info("⚠️  CPT LICENSE REQUIRED")
    logger.info(f"{'='*70}\n")
    logger.info("To obtain full CPT data with descriptions:")
    logger.info("\n1. Purchase AMA CPT License:")
    logger.info("   https://www.ama-assn.org/practice-management/cpt/cpt-licensing")
    logger.info("\n2. Download CPT data file from AMA")
    logger.info("\n3. Place licensed file in:")
    logger.info(f"   {DATA_DIR}/cpt_licensed/")
    logger.info("\n4. Run with --process-licensed flag:")
    logger.info(f"   python scripts/download_procedure_data.py --process-licensed --year {year}")
    logger.info("\n" + "="*70 + "\n")

    return True


def process_licensed_cpt(year: int = 2025) -> bool:
    """Process licensed CPT data file

    This function processes a licensed CPT data file obtained from AMA.
    The file format depends on what AMA provides (Excel, CSV, text, etc.)

    Args:
        year: CPT year

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"Processing Licensed CPT {year} Data")
    logger.info(f"{'='*70}\n")

    licensed_dir = DATA_DIR / "cpt_licensed"

    if not licensed_dir.exists():
        logger.error(f"Licensed CPT directory not found: {licensed_dir}")
        logger.info("\nCreate directory and place licensed file:")
        logger.info(f"  mkdir -p {licensed_dir}")
        logger.info(f"  cp /path/to/cpt_{year}.xlsx {licensed_dir}/")
        return False

    # Look for licensed data files
    licensed_files = list(licensed_dir.glob(f"*{year}*"))

    if not licensed_files:
        logger.error(f"No licensed CPT files found for {year}")
        logger.info(f"Place licensed file in: {licensed_dir}")
        logger.info("Supported formats: .xlsx, .csv, .txt")
        return False

    logger.info(f"Found {len(licensed_files)} licensed file(s):")
    for f in licensed_files:
        logger.info(f"  - {f.name}")

    logger.info("\n⚠️  This function requires the licensed file format specification")
    logger.info("Please update this function to match your AMA data file format")

    return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Download procedure code data (HCPCS public + CPT framework)"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2025,
        help="Year to download (default: 2025)"
    )
    parser.add_argument(
        "--hcpcs-only",
        action="store_true",
        help="Download only HCPCS data (public domain)"
    )
    parser.add_argument(
        "--cpt-template",
        action="store_true",
        help="Create CPT code template (without descriptions)"
    )
    parser.add_argument(
        "--process-licensed",
        action="store_true",
        help="Process licensed CPT data file (requires AMA license)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download HCPCS and create CPT template"
    )

    args = parser.parse_args()

    logger.info("="*70)
    logger.info("Procedure Code Data Downloader")
    logger.info("="*70)
    logger.info(f"Year: {args.year}")
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info("="*70 + "\n")

    success = True

    # Download HCPCS (public domain)
    if args.hcpcs_only or args.all:
        success = download_hcpcs_data(args.year) and success

    # Create CPT template
    if args.cpt_template or args.all:
        success = create_cpt_template(args.year) and success

    # Process licensed CPT data
    if args.process_licensed:
        success = process_licensed_cpt(args.year) and success

    # If no specific flags, download all public data
    if not any([args.hcpcs_only, args.cpt_template, args.process_licensed, args.all]):
        logger.info("No specific option selected. Use --all to download all public data.\n")
        parser.print_help()
        return 1

    if success:
        logger.info("\n" + "="*70)
        logger.info("✅ Download completed successfully!")
        logger.info("="*70)
        logger.info("\nNext steps:")
        logger.info("1. Extract/convert downloaded files to CSV")
        logger.info("2. Run: python scripts/load_procedure_codes.py")
        logger.info("3. Generate embeddings: python scripts/generate_procedure_embeddings.py")
        logger.info("="*70 + "\n")
        return 0
    else:
        logger.error("\n" + "="*70)
        logger.error("✗ Some downloads failed")
        logger.error("="*70 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
