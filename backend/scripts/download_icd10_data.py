#!/usr/bin/env python3
"""
Download CMS ICD-10-CM data files

This script downloads the official ICD-10-CM code files from CMS.
CMS releases annual updates of ICD-10-CM codes with effective dates.

Data source: https://www.cms.gov/medicare/coding-billing/icd-10-codes
"""

import os
import sys
import requests
import zipfile
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "icd10"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# CMS ICD-10-CM data URLs
# Note: CMS updates these URLs annually. Check https://www.cms.gov/medicare/coding-billing/icd-10-codes
# ICD-10 codes are effective October 1st each year
ICD10CM_URLS = {
    "2024": {
        "codes": "https://www.cms.gov/files/zip/2024-code-descriptions-tabular-order.zip",
        "guidelines": "https://www.cms.gov/files/document/fy-2024-icd-10-cm-coding-guidelines.pdf"
    },
    "2025": {
        # Effective: October 1, 2024 - September 30, 2025
        "codes": "https://www.cms.gov/files/zip/2025-code-descriptions-tabular-order.zip",
        "guidelines": "https://www.cms.gov/files/document/fy-2025-icd-10-cm-coding-guidelines.pdf"
    },
    "2026": {
        # Effective: October 1, 2025 - September 30, 2026
        "codes": "https://www.cms.gov/files/zip/2026-code-descriptions-tabular-order.zip",
        "guidelines": "https://www.cms.gov/files/document/fy-2026-icd-10-cm-coding-guidelines.pdf"
    }
}


def download_file(url: str, dest_path: Path) -> bool:
    """
    Download a file from a URL to a destination path.

    Args:
        url: URL to download from
        dest_path: Destination file path

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Downloading from {url}...")
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()

        # Get file size for progress tracking
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
                        # Simple progress indicator
                        percent = (downloaded / total_size) * 100
                        if downloaded % (8192 * 100) == 0:  # Log every ~800KB
                            logger.info(f"Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)")

        logger.info(f"Downloaded successfully to {dest_path}")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return False


def extract_zip(zip_path: Path, extract_to: Path) -> bool:
    """
    Extract a zip file to a destination directory.

    Args:
        zip_path: Path to zip file
        extract_to: Directory to extract to

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Extracting {zip_path} to {extract_to}...")
        extract_to.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

        logger.info(f"Extracted successfully")
        return True

    except zipfile.BadZipFile as e:
        logger.error(f"Failed to extract {zip_path}: {e}")
        return False


def download_icd10cm_data(year: str = "2024") -> bool:
    """
    Download ICD-10-CM data for a specific year.

    Args:
        year: Year of ICD-10-CM release (default: 2024)

    Returns:
        True if all downloads successful, False otherwise
    """
    if year not in ICD10CM_URLS:
        logger.error(f"No URLs configured for year {year}")
        logger.info(f"Available years: {', '.join(ICD10CM_URLS.keys())}")
        return False

    urls = ICD10CM_URLS[year]
    year_dir = DATA_DIR / year
    year_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    total_count = len(urls)

    for file_type, url in urls.items():
        # Determine file type (PDF or ZIP)
        is_pdf = url.endswith('.pdf')

        if is_pdf:
            # Download PDF directly (no extraction needed)
            pdf_filename = f"icd10cm_{year}_{file_type}.pdf"
            pdf_path = year_dir / pdf_filename

            if pdf_path.exists():
                logger.info(f"{pdf_filename} already exists, skipping download")
                success_count += 1
            else:
                if download_file(url, pdf_path):
                    success_count += 1
                else:
                    logger.warning(f"Failed to download {file_type} data")
        else:
            # Download and extract ZIP file
            zip_filename = f"icd10cm_{year}_{file_type}.zip"
            zip_path = year_dir / zip_filename

            if zip_path.exists():
                logger.info(f"{zip_filename} already exists, skipping download")
            else:
                if not download_file(url, zip_path):
                    logger.warning(f"Failed to download {file_type} data")
                    continue

            # Extract zip file
            extract_dir = year_dir / file_type
            if not extract_zip(zip_path, extract_dir):
                logger.warning(f"Failed to extract {file_type} data")
                continue

            success_count += 1

    logger.info(f"\nDownload summary: {success_count}/{total_count} files successful")
    return success_count == total_count


def list_downloaded_files():
    """List all downloaded ICD-10-CM data files."""
    logger.info("\n=== Downloaded ICD-10-CM Files ===")

    if not DATA_DIR.exists() or not any(DATA_DIR.iterdir()):
        logger.info("No files downloaded yet")
        return

    for year_dir in sorted(DATA_DIR.iterdir()):
        if year_dir.is_dir():
            logger.info(f"\nYear: {year_dir.name}")
            for item in sorted(year_dir.iterdir()):
                if item.is_dir():
                    file_count = len(list(item.glob("*")))
                    logger.info(f"  {item.name}/: {file_count} files")
                else:
                    size_mb = item.stat().st_size / (1024 * 1024)
                    logger.info(f"  {item.name}: {size_mb:.2f} MB")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Download CMS ICD-10-CM data files"
    )
    parser.add_argument(
        "--year",
        type=str,
        default="2026",
        help="Year of ICD-10-CM release to download (default: 2026)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List downloaded files and exit"
    )

    args = parser.parse_args()

    if args.list:
        list_downloaded_files()
        return 0

    logger.info(f"Starting ICD-10-CM data download for year {args.year}")
    logger.info(f"Data directory: {DATA_DIR}")

    success = download_icd10cm_data(args.year)

    if success:
        logger.info("\n✓ All files downloaded and extracted successfully")
        list_downloaded_files()
        return 0
    else:
        logger.error("\n✗ Some files failed to download")
        return 1


if __name__ == "__main__":
    sys.exit(main())
