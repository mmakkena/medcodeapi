#!/usr/bin/env python3
"""
Download CMS Medicare Physician Fee Schedule (MPFS) data files.

This script automates downloading and converting official CMS data files needed
for Medicare fee schedule pricing calculations.

WHAT IT DOWNLOADS:
==================
1. MPFS RVU Package (contains multiple files):
   - PPRRVU*.csv: Relative Value Units for 14,000+ CPT/HCPCS codes
   - GPCI*.csv: Geographic Practice Cost Indices by locality (~110 localities)
   - *LOCCO*.csv: Locality codes and names

2. ZIP to Locality Crosswalk:
   - ZIP5*.txt: Maps 42,000+ ZIP codes to CMS carriers and localities

DATA SOURCES (Official CMS):
============================
- RVU Files: https://www.cms.gov/medicare/payment/fee-schedules/physician/pfs-relative-value-files
- ZIP Files: https://www.cms.gov/medicare/payment/fee-schedules

OUTPUT FILES:
=============
After running, you'll get standardized CSV files in data/fee_schedule/{year}/:
- mpfs_rvu_{year}.csv    : RVU data (18,000+ codes)
- gpci_{year}.csv        : GPCI data (109 localities)
- locality_codes_{year}.csv : Locality reference data
- zip_locality_{year}.csv   : ZIP to locality mapping (42,000+ ZIPs)

USAGE EXAMPLES:
===============
    # Download and convert 2025 data
    python scripts/download_feescheduler_cms_data.py --year 2025

    # Only download (don't convert yet)
    python scripts/download_feescheduler_cms_data.py --year 2025 --download-only

    # Only convert already-downloaded files
    python scripts/download_feescheduler_cms_data.py --year 2025 --convert-only

    # Download multiple years
    python scripts/download_feescheduler_cms_data.py --year 2024 --year 2025

    # List configured URLs
    python scripts/download_feescheduler_cms_data.py --list-urls

AFTER DOWNLOAD:
===============
Load the data into the database using:
    python scripts/load_fee_schedule_data.py --year 2025 \\
        --mpfs-file data/fee_schedule/2025/mpfs_rvu_2025.csv \\
        --gpci-file data/fee_schedule/2025/gpci_2025.csv \\
        --zip-file data/fee_schedule/2025/zip_locality_2025.csv

REQUIREMENTS:
=============
- Python 3.8+
- pandas (for GPCI conversion): pip install pandas

NOTES:
======
- CMS typically releases new RVU files quarterly (Jan, Apr, Jul, Oct)
- ZIP locality files are updated quarterly
- URLs may change; update CMS_URLS dict if downloads fail
"""

import os
import sys
import csv
import zipfile
import tempfile
import logging
import argparse
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import shutil

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Base directories
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "fee_schedule"

# CMS Download URLs - Updated annually
# Format: {year: {file_type: url}}
# Note: The RVU ZIP file contains GPCI data, so we only need 2 downloads:
#   1. RVU file (contains RVU + GPCI + locality codes)
#   2. ZIP to locality crosswalk (separate file)
#
# URL patterns:
#   RVU: https://www.cms.gov/files/zip/rvu{YY}{version}.zip
#   ZIP Locality: https://www.cms.gov/files/zip/zip-code-carrier-locality-file-revised-{date}.zip
#   End of Year: https://www.cms.gov/files/zip/{YYYY}-end-year-zip-code-file.zip
CMS_URLS = {
    2025: {
        # RVU files - January 2025 release (contains GPCI2025.csv, PPRRVU25_JAN.csv, 25LOCCO.csv)
        "rvu": "https://www.cms.gov/files/zip/rvu25a.zip",
        # ZIP to Locality crosswalk - most recent revision (Nov 2025)
        "zip_locality": "https://www.cms.gov/files/zip/zip-code-carrier-locality-file-revised-11-18-2025.zip",
        # Alternative: End of year file
        "zip_locality_eoy": "https://www.cms.gov/files/zip/2025-end-year-zip-code-file.zip",
    },
    2024: {
        "rvu": "https://www.cms.gov/files/zip/rvu24d.zip",
        # Use 2024 end of year file
        "zip_locality": "https://www.cms.gov/files/zip/2024-end-year-zip-code-file.zip",
    },
    2023: {
        "rvu": "https://www.cms.gov/files/zip/rvu23d.zip",
        "zip_locality": "https://www.cms.gov/files/zip/2023-end-year-zip-code-file.zip",
    },
}

# Alternative URLs if primary fails
FALLBACK_URLS = {
    2025: {
        "rvu": [
            "https://www.cms.gov/medicare/payment/fee-schedules/physician/pfs-relative-value-files/rvu25a",
        ],
        "gpci": [
            "https://www.cms.gov/medicare/physician-fee-schedule/search/documentation",
        ],
    }
}

# User agent for requests
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) MedCodeAPI/1.0"


def download_file(url: str, dest_path: Path, description: str = "file") -> bool:
    """
    Download a file from URL to destination path.

    Args:
        url: URL to download from
        dest_path: Path to save the file
        description: Description for logging

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Downloading {description} from {url}")

    try:
        request = Request(url, headers={"User-Agent": USER_AGENT})

        with urlopen(request, timeout=120) as response:
            total_size = response.headers.get('Content-Length')
            if total_size:
                total_size = int(total_size)
                logger.info(f"  File size: {total_size / 1024 / 1024:.1f} MB")

            # Download in chunks
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            with open(dest_path, 'wb') as f:
                downloaded = 0
                chunk_size = 8192

                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size:
                        pct = (downloaded / total_size) * 100
                        if downloaded % (1024 * 1024) < chunk_size:  # Log every ~1MB
                            logger.info(f"  Downloaded {downloaded / 1024 / 1024:.1f} MB ({pct:.0f}%)")

        logger.info(f"  Successfully downloaded to {dest_path}")
        return True

    except HTTPError as e:
        logger.error(f"  HTTP Error {e.code}: {e.reason}")
        return False
    except URLError as e:
        logger.error(f"  URL Error: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"  Error downloading: {e}")
        return False


def extract_zip(zip_path: Path, extract_dir: Path) -> List[Path]:
    """
    Extract a ZIP file and return list of extracted files.

    Args:
        zip_path: Path to ZIP file
        extract_dir: Directory to extract to

    Returns:
        List of extracted file paths
    """
    logger.info(f"Extracting {zip_path.name}")

    extracted_files = []

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # List contents
            for info in zip_ref.infolist():
                logger.info(f"  - {info.filename} ({info.file_size / 1024:.1f} KB)")

            # Extract all
            zip_ref.extractall(extract_dir)

            for info in zip_ref.infolist():
                extracted_path = extract_dir / info.filename
                extracted_files.append(extracted_path)

        logger.info(f"  Extracted {len(extracted_files)} files to {extract_dir}")
        return extracted_files

    except zipfile.BadZipFile:
        logger.error(f"  Invalid ZIP file: {zip_path}")
        return []
    except Exception as e:
        logger.error(f"  Error extracting: {e}")
        return []


def convert_excel_to_csv(excel_path: Path, csv_path: Path, sheet_name: Optional[str] = None) -> bool:
    """
    Convert Excel file to CSV.

    Args:
        excel_path: Path to Excel file
        csv_path: Path to output CSV
        sheet_name: Specific sheet to convert (optional)

    Returns:
        True if successful
    """
    try:
        import openpyxl
    except ImportError:
        logger.warning("openpyxl not installed. Install with: pip install openpyxl")
        # Try pandas as fallback
        try:
            import pandas as pd
            logger.info(f"Converting {excel_path.name} to CSV using pandas")
            df = pd.read_excel(excel_path, sheet_name=sheet_name or 0)
            df.to_csv(csv_path, index=False)
            logger.info(f"  Saved to {csv_path}")
            return True
        except ImportError:
            logger.error("Neither openpyxl nor pandas installed. Cannot convert Excel files.")
            return False

    logger.info(f"Converting {excel_path.name} to CSV")

    try:
        wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)

        # Get sheet
        if sheet_name:
            ws = wb[sheet_name]
        else:
            ws = wb.active

        # Write to CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for row in ws.iter_rows(values_only=True):
                # Skip completely empty rows
                if any(cell is not None for cell in row):
                    writer.writerow(row)

        wb.close()
        logger.info(f"  Saved to {csv_path}")
        return True

    except Exception as e:
        logger.error(f"  Error converting Excel: {e}")
        return False


def find_rvu_file(extracted_dir: Path) -> Optional[Path]:
    """Find the main RVU data file in extracted contents."""
    # Look for common patterns - prefer CSV over TXT
    patterns = [
        "**/PPRRVU*.csv",  # Primary RVU file (CSV preferred)
        "**/PPRRVU*.txt",
        "**/RVU*.csv",
        "**/RVU*.txt",
        "**/*rvu*.csv",
        "**/*rvu*.txt",
    ]

    for pattern in patterns:
        matches = list(extracted_dir.glob(pattern))
        if matches:
            # Prefer larger files (main data file) and CSV over TXT
            matches.sort(key=lambda p: (p.suffix == '.csv', p.stat().st_size), reverse=True)
            return matches[0]

    return None


def find_gpci_file(extracted_dir: Path) -> Optional[Path]:
    """Find the GPCI data file in extracted contents."""
    # RVU ZIP contains GPCI files like GPCI2025.csv
    patterns = [
        "**/GPCI*.csv",  # Direct GPCI file in RVU ZIP
        "**/GPCI*.xlsx",
        "**/GPCI*.txt",
        "**/Addendum*E*.xlsx",  # GPCI is typically in Addendum E
        "**/Addendum*E*.xls",
        "**/*gpci*.csv",
        "**/*gpci*.xlsx",
    ]

    for pattern in patterns:
        matches = list(extracted_dir.glob(pattern))
        if matches:
            # Prefer CSV format
            matches.sort(key=lambda p: p.suffix == '.csv', reverse=True)
            return matches[0]

    return None


def find_locality_codes_file(extracted_dir: Path) -> Optional[Path]:
    """Find the locality codes file (e.g., 25LOCCO.csv) in extracted contents."""
    patterns = [
        "**/*LOCCO*.csv",
        "**/*LOCCO*.txt",
        "**/*locality*.csv",
        "**/*locality*.txt",
    ]

    for pattern in patterns:
        matches = list(extracted_dir.glob(pattern))
        if matches:
            matches.sort(key=lambda p: p.suffix == '.csv', reverse=True)
            return matches[0]

    return None


def find_zip_locality_file(extracted_dir: Path) -> Optional[Path]:
    """Find the ZIP to locality mapping file in extracted contents.

    Prefers ZIP5 files over ZIP9 files (ZIP9 has 9-digit ZIP codes and is much larger).
    Most use cases only need 5-digit ZIP codes.
    """
    # First look for ZIP5 files specifically
    zip5_patterns = [
        "**/ZIP5*.txt",
        "**/ZIP5*.csv",
    ]

    for pattern in zip5_patterns:
        matches = list(extracted_dir.glob(pattern))
        if matches:
            # Prefer .txt over .xlsx (CMS provides both)
            matches.sort(key=lambda p: p.suffix == '.txt', reverse=True)
            return matches[0]

    # Fall back to any ZIP file
    patterns = [
        "**/ZIP*.txt",
        "**/ZIP*.csv",
        "**/*zip*carrier*.txt",
        "**/*zip*carrier*.csv",
        "**/*zip*locality*.txt",
        "**/*zip*locality*.csv",
    ]

    for pattern in patterns:
        matches = list(extracted_dir.glob(pattern))
        if matches:
            # Prefer ZIP5 over ZIP9, and smaller files (ZIP5 is ~3MB, ZIP9 is ~85MB)
            matches.sort(key=lambda p: ('ZIP5' in p.name, -p.stat().st_size), reverse=True)
            return matches[0]

    return None


def convert_rvu_to_standard_csv(source_path: Path, dest_path: Path) -> bool:
    """
    Convert CMS RVU file to standardized CSV format.

    CMS RVU files have multiple title/header rows:
    - Rows 1-4: Title, copyright, release date
    - Rows 5-8: Multi-line column descriptions
    - Row 9: Actual column headers (HCPCS, MOD, DESCRIPTION, etc.)
    - Row 10+: Data

    This normalizes them to comma-delimited CSV with headers on row 1.
    """
    logger.info(f"Converting RVU file: {source_path.name}")

    try:
        # Detect delimiter
        with open(source_path, 'r', encoding='utf-8-sig') as f:
            sample = f.read(8192)

        if '\t' in sample:
            delimiter = '\t'
        elif '|' in sample:
            delimiter = '|'
        else:
            delimiter = ','

        logger.info(f"  Detected delimiter: {repr(delimiter)}")

        # Read all rows
        all_rows = []
        with open(source_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=delimiter)
            for row in reader:
                cleaned = [cell.strip() for cell in row]
                all_rows.append(cleaned)

        if not all_rows:
            logger.error("  No data found in file")
            return False

        # Find the header row - it should contain "HCPCS" in first column
        header_row_idx = 0
        for idx, row in enumerate(all_rows[:20]):  # Check first 20 rows
            # Header row typically has HCPCS in first column
            if row and row[0].upper() == 'HCPCS':
                header_row_idx = idx
                logger.info(f"  Found header row at line {idx + 1}")
                break

        # CMS uses multi-row headers (rows 6-10 in 2025 file)
        # The row with "HCPCS" has partial column names
        # We'll use standardized column names based on known CMS structure
        # Column positions (0-indexed):
        #  0: HCPCS, 1: MOD, 2: DESCRIPTION, 3: STATUS CODE, 4: NOT USED FOR MEDICARE
        #  5: WORK RVU, 6: NON-FAC PE RVU, 7: NA INDICATOR, 8: FACILITY PE RVU, 9: NA INDICATOR
        # 10: MP RVU, 11: NON-FACILITY TOTAL, 12: FACILITY TOTAL, 13: PCTC IND, 14: GLOB DAYS
        # 15: PRE OP, 16: INTRA OP, 17: POST OP, 18: MULT PROC, 19: BILAT SURG
        # 20: ASST SURG, 21: CO-SURG, 22: TEAM SURG, 23: ENDO BASE, 24: CONV FACTOR
        # 25: DIAGNOSTIC PROCEDURES, 26: CALCULATION FLAG, 27: FAMILY INDICATOR
        # 28: NON-FAC PE OPPS, 29: FAC PE OPPS, 30: MP OPPS
        standard_headers = [
            'HCPCS', 'MOD', 'DESCRIPTION', 'STATUS CODE', 'NOT USED FOR MEDICARE',
            'WORK RVU', 'NON-FAC PE RVU', 'NON-FAC NA IND', 'FACILITY PE RVU', 'FAC NA IND',
            'MP RVU', 'NON-FACILITY TOTAL', 'FACILITY TOTAL', 'PCTC IND', 'GLOB DAYS',
            'PRE OP', 'INTRA OP', 'POST OP', 'MULT PROC', 'BILAT SURG',
            'ASST SURG', 'CO-SURG', 'TEAM SURG', 'ENDO BASE', 'CONV FACTOR',
            'DIAGNOSTIC PROC', 'CALC FLAG', 'FAMILY IND',
            'NON-FAC PE OPPS', 'FAC PE OPPS', 'MP OPPS'
        ]

        # Use standard headers or fall back to original if structure differs
        original_header = all_rows[header_row_idx]
        if len(original_header) == len(standard_headers):
            header = standard_headers
            logger.info(f"  Using standardized column names ({len(header)} columns)")
        else:
            header = original_header
            logger.info(f"  Using original column names ({len(header)} columns)")

        data_rows = all_rows[header_row_idx + 1:]

        # Filter out any remaining non-data rows (empty or partial)
        valid_rows = []
        for row in data_rows:
            # Valid data row should have HCPCS code in first column (alphanumeric)
            if row and row[0] and len(row[0]) >= 4:
                # Pad row to match header length if needed
                while len(row) < len(header):
                    row.append('')
                valid_rows.append(row[:len(header)])  # Trim to header length

        logger.info(f"  Found {len(valid_rows)} data rows")

        # Write standardized CSV
        with open(dest_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(valid_rows)

        logger.info(f"  Converted {len(valid_rows)} rows to {dest_path}")
        return True

    except Exception as e:
        logger.error(f"  Error converting RVU file: {e}")
        import traceback
        traceback.print_exc()
        return False


def convert_gpci_to_standard_csv(source_path: Path, dest_path: Path) -> bool:
    """
    Convert CMS GPCI file (Excel or CSV) to standardized CSV format.

    CMS GPCI files often have:
    - Row 1: Title (e.g., "ADDENDUM E. FINAL CY 2025 GEOGRAPHIC PRACTICE COST INDICES...")
    - Row 2: Column headers
    - Row 3+: Data

    Normalizes column headers to match loader expectations:
    - MAC, Locality, Locality Name, State, Work GPCI, PE GPCI, MP GPCI
    """
    logger.info(f"Converting GPCI file: {source_path.name}")

    try:
        import pandas as pd

        # First, read the raw file to detect structure
        if source_path.suffix.lower() in ['.xlsx', '.xls']:
            # For Excel, read without headers first
            df_raw = pd.read_excel(source_path, header=None, nrows=5)
        else:
            # For CSV, read without headers first
            df_raw = pd.read_csv(source_path, encoding='utf-8-sig', header=None, nrows=5)

        # Detect which row contains the column headers
        # Headers should have structured column names like "MAC", "State", "Locality Number", "PW GPCI"
        # NOT title rows like "ADDENDUM E. FINAL CY 2025 GEOGRAPHIC..."
        header_row = 0
        for idx, row in df_raw.iterrows():
            row_str = ' '.join(str(val).upper() for val in row.values if pd.notna(val))

            # Skip title rows (contain "ADDENDUM" or long descriptive text)
            if 'ADDENDUM' in row_str or 'GEOGRAPHIC PRACTICE COST INDICES' in row_str:
                logger.info(f"  Skipping title row at line {idx + 1}")
                continue

            # Skip empty rows
            non_empty_vals = [v for v in row.values if pd.notna(v) and str(v).strip()]
            if len(non_empty_vals) < 3:
                logger.info(f"  Skipping empty/sparse row at line {idx + 1}")
                continue

            # Look for header patterns - must have multiple column-like names
            # Valid headers contain: "MAC" or "CARRIER", AND "LOCALITY", AND "GPCI"
            has_mac = 'MAC' in row_str or 'CARRIER' in row_str
            has_locality = 'LOCALITY' in row_str
            has_gpci = 'GPCI' in row_str or 'PW GPCI' in row_str or 'PE GPCI' in row_str

            # Check if individual cells look like headers (short text, not numeric)
            header_like_count = sum(1 for v in row.values
                                    if pd.notna(v) and isinstance(v, str)
                                    and len(v) < 50 and not v.replace('.', '').replace(',', '').isdigit())

            if has_mac and has_locality and has_gpci and header_like_count >= 5:
                header_row = idx
                logger.info(f"  Detected header row at line {idx + 1}")
                break

        # Now read with correct header row
        if source_path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(source_path, header=header_row)
        else:
            df = pd.read_csv(source_path, encoding='utf-8-sig', header=header_row)

        logger.info(f"  Raw columns found: {list(df.columns)}")

        # Normalize column names - handle various CMS naming conventions
        # CMS uses names like: "Medicare Administrative Contractor (MAC)", "2025 PW GPCI (with 1.0 Floor)", etc.
        column_mapping = {
            # MAC column variants
            'CARRIER': 'MAC',
            'MAC NUMBER': 'MAC',
            'MAC_NUMBER': 'MAC',
            'MEDICARE ADMINISTRATIVE CONTRACTOR': 'MAC',
            'MEDICARE ADMINISTRATIVE CONTRACTOR (MAC)': 'MAC',
            # Locality number variants
            'LOCALITY': 'Locality',
            'LOCALITY NUMBER': 'Locality',
            'LOCALITY_NUMBER': 'Locality',
            # Locality name variants
            'LOCALITY NAME': 'Locality Name',
            'LOCALITY_NAME': 'Locality Name',
            # Work GPCI variants (also called PW GPCI - Physician Work)
            'WORK GPCI': 'Work GPCI',
            'WORK_GPCI': 'Work GPCI',
            'PW GPCI': 'Work GPCI',
            'PW_GPCI': 'Work GPCI',
            # PE GPCI variants (Practice Expense)
            'PE GPCI': 'PE GPCI',
            'PE_GPCI': 'PE GPCI',
            'PRACTICE EXPENSE GPCI': 'PE GPCI',
            # MP GPCI variants (Malpractice)
            'MP GPCI': 'MP GPCI',
            'MP_GPCI': 'MP GPCI',
            'MALPRACTICE GPCI': 'MP GPCI',
            'PLI GPCI': 'MP GPCI',
        }

        # Rename columns - strip whitespace for matching
        df.columns = [str(col).strip() for col in df.columns]
        original_cols = list(df.columns)

        # Create mapping for column renaming using partial matching
        rename_dict = {}
        for col in original_cols:
            col_upper = col.upper()

            # First try exact match
            if col_upper in column_mapping:
                rename_dict[col] = column_mapping[col_upper]
                continue

            # Then try partial/contains match for dynamic column names like "2025 PW GPCI (with 1.0 Floor)"
            # Check for GPCI columns specifically (they often have year prefixes)
            if 'PW GPCI' in col_upper or 'WORK GPCI' in col_upper:
                rename_dict[col] = 'Work GPCI'
            elif 'PE GPCI' in col_upper:
                rename_dict[col] = 'PE GPCI'
            elif 'MP GPCI' in col_upper or 'MALPRACTICE' in col_upper:
                rename_dict[col] = 'MP GPCI'
            elif 'LOCALITY NUMBER' in col_upper:
                rename_dict[col] = 'Locality'
            elif 'LOCALITY NAME' in col_upper:
                rename_dict[col] = 'Locality Name'
            elif 'MAC' in col_upper or 'CARRIER' in col_upper:
                rename_dict[col] = 'MAC'
            elif col_upper == 'STATE':
                rename_dict[col] = 'State'

        df = df.rename(columns=rename_dict)
        logger.info(f"  Normalized columns: {list(df.columns)}")

        # Select and order relevant columns
        output_cols = []
        desired_cols = ['MAC', 'Locality', 'Locality Name', 'Work GPCI', 'PE GPCI', 'MP GPCI']

        for desired in desired_cols:
            for col in df.columns:
                if desired.upper() == col.upper() or desired == col:
                    output_cols.append(col)
                    break

        if len(output_cols) < len(desired_cols):
            logger.warning(f"  Only found {len(output_cols)} of {len(desired_cols)} expected columns")
            # Include all numeric columns that might be GPCI values
            for col in df.columns:
                if col not in output_cols:
                    output_cols.append(col)

        # Filter to only rows with actual data (not empty or NaN in key columns)
        if 'Locality' in df.columns:
            df = df[df['Locality'].notna()]
        elif 'LOCALITY' in df.columns:
            df = df[df['LOCALITY'].notna()]

        # Drop rows where all values are NaN
        df = df.dropna(how='all')

        # Save to CSV
        df.to_csv(dest_path, index=False)
        logger.info(f"  Converted {len(df)} rows to {dest_path}")
        return True

    except ImportError:
        logger.error("pandas required for GPCI conversion. Install: pip install pandas openpyxl")
        return False
    except Exception as e:
        logger.error(f"  Error converting GPCI file: {e}")
        import traceback
        traceback.print_exc()
        return False


def convert_zip_locality_to_standard_csv(source_path: Path, dest_path: Path) -> bool:
    """
    Convert CMS ZIP to Locality file to standardized CSV format.

    Normalizes to: ZIP, CARRIER, LOCALITY, STATE
    """
    logger.info(f"Converting ZIP locality file: {source_path.name}")

    try:
        # Detect format
        with open(source_path, 'r', encoding='utf-8-sig') as f:
            sample = f.read(4096)

        # Check if fixed-width or delimited
        if '\t' in sample:
            delimiter = '\t'
        elif '|' in sample:
            delimiter = '|'
        elif ',' in sample:
            delimiter = ','
        else:
            # Likely fixed-width - CMS ZIP files are often fixed-width
            return convert_fixed_width_zip_file(source_path, dest_path)

        logger.info(f"  Detected delimiter: {repr(delimiter)}")

        # Read delimited file
        rows = []
        with open(source_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=delimiter)
            header = None
            for row in reader:
                cleaned = [cell.strip() for cell in row]
                if not any(cleaned):
                    continue

                if header is None:
                    # Check if first row is header
                    if any(h.upper() in ['ZIP', 'ZIPCODE', 'ZIP CODE', 'CARRIER', 'LOCALITY', 'STATE']
                           for h in cleaned):
                        header = cleaned
                    else:
                        # No header, use default
                        header = ['ZIP', 'CARRIER', 'LOCALITY', 'STATE', 'RURAL']
                        rows.append(cleaned)
                else:
                    rows.append(cleaned)

        # Write standardized CSV
        with open(dest_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ZIP', 'CARRIER', 'LOCALITY', 'STATE'])
            for row in rows:
                if len(row) >= 4:
                    writer.writerow(row[:4])
                elif len(row) >= 3:
                    writer.writerow(row + [''])

        logger.info(f"  Converted {len(rows)} rows to {dest_path}")
        return True

    except Exception as e:
        logger.error(f"  Error converting ZIP locality file: {e}")
        return False


def convert_fixed_width_zip_file(source_path: Path, dest_path: Path) -> bool:
    """
    Convert fixed-width format ZIP locality file.

    CMS ZIP5 files are in fixed-width format (per ZIP5lyout.txt):
    - State: positions 1-2 (2 chars)
    - ZIP Code: positions 3-7 (5 chars)
    - Carrier: positions 8-12 (5 chars)
    - Pricing Locality: positions 13-14 (2 chars)
    - Rural Indicator: position 15 (1 char) - Blank=urban, R=rural, B=super rural
    - Lab CB Locality: positions 16-17 (2 chars)
    - Plus Four Flag: position 21 (1 char) - 0=no +4, 1=has +4
    - Year/Quarter: positions 76-80 (5 chars)
    """
    logger.info("  Detected fixed-width format")

    try:
        rows = []
        with open(source_path, 'r', encoding='utf-8-sig') as f:
            for line in f:
                if len(line.strip()) < 14:
                    continue

                # Parse fixed-width fields (0-indexed)
                state = line[0:2].strip()          # positions 1-2
                zip_code = line[2:7].strip()       # positions 3-7
                carrier = line[7:12].strip()       # positions 8-12
                locality = line[12:14].strip()     # positions 13-14
                rural_indicator = line[14:15].strip() if len(line) > 14 else ''  # position 15

                # Validate ZIP code (must be 5 digits)
                if zip_code.isdigit() and len(zip_code) == 5:
                    # Map rural indicator: blank=Urban, R=Rural, B=Super Rural
                    rural = 'U'  # Default Urban
                    if rural_indicator == 'R':
                        rural = 'R'
                    elif rural_indicator == 'B':
                        rural = 'B'

                    rows.append([zip_code, carrier, locality, state, rural])

        # Write CSV
        with open(dest_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ZIP', 'CARRIER', 'LOCALITY', 'STATE', 'RURAL'])
            writer.writerows(rows)

        logger.info(f"  Converted {len(rows)} rows to {dest_path}")
        return True

    except Exception as e:
        logger.error(f"  Error converting fixed-width file: {e}")
        return False


def download_and_process_year(year: int, output_dir: Path, download_only: bool = False,
                              convert_only: bool = False) -> Dict[str, Path]:
    """
    Download and process all CMS data files for a given year.

    The RVU ZIP file contains:
    - PPRRVU*.csv - Main RVU data (~14,000 codes)
    - GPCI*.csv - Geographic Practice Cost Indices
    - *LOCCO*.csv - Locality codes

    Args:
        year: Fee schedule year
        output_dir: Directory to save processed files
        download_only: Only download, don't process
        convert_only: Only convert existing downloads

    Returns:
        Dictionary mapping file type to output path
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing CMS Fee Schedule data for {year}")
    logger.info(f"{'='*60}")

    if year not in CMS_URLS:
        logger.error(f"No URLs configured for year {year}")
        logger.info(f"Available years: {list(CMS_URLS.keys())}")
        return {}

    urls = CMS_URLS[year]
    output_dir = output_dir / str(year)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create temp directory for downloads
    temp_dir = output_dir / "downloads"
    temp_dir.mkdir(exist_ok=True)

    results = {}

    # Step 1: Download and extract RVU ZIP (contains RVU, GPCI, and locality codes)
    logger.info(f"\n--- Downloading RVU package (contains RVU + GPCI + locality codes) ---")

    rvu_url = urls.get("rvu")
    if rvu_url:
        rvu_zip_path = temp_dir / f"rvu_{year}.zip"
        rvu_extract_dir = temp_dir / "rvu"

        # Download if needed
        if not convert_only:
            if not rvu_zip_path.exists() or rvu_zip_path.stat().st_size == 0:
                if not download_file(rvu_url, rvu_zip_path, "RVU package"):
                    logger.error("Failed to download RVU package")
                else:
                    logger.info("RVU package downloaded successfully")
            else:
                logger.info(f"Using existing download: {rvu_zip_path}")

        if not download_only and rvu_zip_path.exists():
            # Extract RVU ZIP
            if rvu_extract_dir.exists():
                shutil.rmtree(rvu_extract_dir)
            rvu_extract_dir.mkdir(exist_ok=True)

            extracted = extract_zip(rvu_zip_path, rvu_extract_dir)
            if extracted:
                # Process RVU file
                logger.info("\n--- Processing MPFS RVU data ---")
                rvu_source = find_rvu_file(rvu_extract_dir)
                if rvu_source:
                    logger.info(f"Found RVU file: {rvu_source.name}")
                    rvu_output = output_dir / f"mpfs_rvu_{year}.csv"
                    if convert_rvu_to_standard_csv(rvu_source, rvu_output):
                        results["rvu"] = rvu_output
                else:
                    logger.warning("RVU file not found in extracted contents")

                # Process GPCI file (from same ZIP)
                logger.info("\n--- Processing GPCI locality data ---")
                gpci_source = find_gpci_file(rvu_extract_dir)
                if gpci_source:
                    logger.info(f"Found GPCI file: {gpci_source.name}")
                    gpci_output = output_dir / f"gpci_{year}.csv"
                    if convert_gpci_to_standard_csv(gpci_source, gpci_output):
                        results["gpci"] = gpci_output
                else:
                    logger.warning("GPCI file not found in extracted contents")

                # Process locality codes file (from same ZIP)
                logger.info("\n--- Processing locality codes ---")
                locco_source = find_locality_codes_file(rvu_extract_dir)
                if locco_source:
                    logger.info(f"Found locality codes file: {locco_source.name}")
                    locco_output = output_dir / f"locality_codes_{year}.csv"
                    # Just copy CSV as-is
                    shutil.copy(locco_source, locco_output)
                    results["locality_codes"] = locco_output
                    logger.info(f"Copied to {locco_output}")

                # List all extracted files for reference
                logger.info("\nAll files in RVU package:")
                for f in sorted(rvu_extract_dir.rglob("*")):
                    if f.is_file():
                        size_kb = f.stat().st_size / 1024
                        logger.info(f"  - {f.name} ({size_kb:.1f} KB)")

    # Step 2: Download and process ZIP to locality crosswalk (separate file)
    logger.info(f"\n--- Downloading ZIP to locality crosswalk ---")

    zip_url = urls.get("zip_locality")
    if zip_url:
        zip_zip_path = temp_dir / f"zip_locality_{year}.zip"
        zip_extract_dir = temp_dir / "zip_locality"

        # Download if needed
        if not convert_only:
            if not zip_zip_path.exists() or zip_zip_path.stat().st_size == 0:
                if not download_file(zip_url, zip_zip_path, "ZIP to locality crosswalk"):
                    logger.warning("Failed to download ZIP crosswalk - this file may need manual download")
                    logger.info("Visit: https://www.cms.gov/medicare/payment/fee-schedules")
                    logger.info("Look for: 'Zip Code to Carrier Locality File'")
            else:
                logger.info(f"Using existing download: {zip_zip_path}")

        if not download_only and zip_zip_path.exists():
            # Extract ZIP locality
            if zip_extract_dir.exists():
                shutil.rmtree(zip_extract_dir)
            zip_extract_dir.mkdir(exist_ok=True)

            extracted = extract_zip(zip_zip_path, zip_extract_dir)
            if extracted:
                zip_source = find_zip_locality_file(zip_extract_dir)
                if zip_source:
                    logger.info(f"Found ZIP locality file: {zip_source.name}")
                    zip_output = output_dir / f"zip_locality_{year}.csv"
                    if convert_zip_locality_to_standard_csv(zip_source, zip_output):
                        results["zip_locality"] = zip_output
                else:
                    logger.warning("ZIP locality file not found")
                    logger.info("Extracted files:")
                    for f in zip_extract_dir.rglob("*"):
                        if f.is_file():
                            logger.info(f"  - {f.relative_to(zip_extract_dir)}")

    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download CMS Medicare Fee Schedule data files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download and process 2025 data
  python download_feescheduler_cms_data.py --year 2025

  # Only download (don't process)
  python download_feescheduler_cms_data.py --year 2025 --download-only

  # Only convert already downloaded files
  python download_feescheduler_cms_data.py --year 2025 --convert-only

  # Download multiple years
  python download_feescheduler_cms_data.py --year 2024 --year 2025
        """
    )

    parser.add_argument(
        "--year",
        type=int,
        action="append",
        dest="years",
        help="Fee schedule year(s) to download (can specify multiple)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DATA_DIR),
        help=f"Output directory (default: {DATA_DIR})"
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Only download ZIP files, don't extract or convert"
    )
    parser.add_argument(
        "--convert-only",
        action="store_true",
        help="Only convert existing downloads (skip download)"
    )
    parser.add_argument(
        "--list-urls",
        action="store_true",
        help="List configured download URLs and exit"
    )

    args = parser.parse_args()

    # List URLs if requested
    if args.list_urls:
        print("\nConfigured CMS Download URLs:")
        print("="*60)
        for year, urls in sorted(CMS_URLS.items(), reverse=True):
            print(f"\n{year}:")
            for file_type, url in urls.items():
                print(f"  {file_type}: {url}")
        return 0

    # Default to current year if not specified
    years = args.years or [2025]
    output_dir = Path(args.output_dir)

    logger.info(f"CMS Fee Schedule Data Downloader")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Years to process: {years}")

    all_results = {}

    for year in years:
        results = download_and_process_year(
            year=year,
            output_dir=output_dir,
            download_only=args.download_only,
            convert_only=args.convert_only
        )
        all_results[year] = results

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("SUMMARY")
    logger.info(f"{'='*60}")

    for year, results in all_results.items():
        logger.info(f"\n{year}:")
        if results:
            for file_type, path in results.items():
                size = path.stat().st_size / 1024 / 1024
                logger.info(f"  {file_type}: {path.name} ({size:.1f} MB)")
        else:
            logger.info("  No files processed")

    # Next steps
    if all_results and not args.download_only:
        logger.info(f"\n{'='*60}")
        logger.info("NEXT STEPS")
        logger.info(f"{'='*60}")
        logger.info("\nTo load data into database, run:")
        for year, results in all_results.items():
            if results:
                cmd = f"python scripts/load_fee_schedule_data.py --year {year}"
                for file_type, path in results.items():
                    if file_type == "rvu":
                        cmd += f" --mpfs-file {path}"
                    elif file_type == "gpci":
                        cmd += f" --gpci-file {path}"
                    elif file_type == "zip_locality":
                        cmd += f" --zip-file {path}"
                logger.info(f"\n{cmd}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
