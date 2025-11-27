#!/usr/bin/env python3
"""
Load CMS Medicare Physician Fee Schedule (MPFS) data into database

This script loads:
1. GPCI (Geographic Practice Cost Index) / Locality data
2. RVU (Relative Value Unit) data from MPFS
3. ZIP code to locality mappings
4. Conversion factors by year

Data sources:
- CMS Physician Fee Schedule: https://www.cms.gov/medicare/physician-fee-schedule/search
- GPCI Files: https://www.cms.gov/medicare/physician-fee-schedule/search/gpci-files

Run with sample data first to test, then download actual CMS data.
"""

import os
import sys
import csv
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.cms_locality import CMSLocality, ZIPToLocality
from app.models.mpfs_rate import MPFSRate, ConversionFactor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "fee_schedule"


def get_database_url() -> str:
    """Get database URL from environment or use default."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/medcodeapi"
    )


def safe_float(value: str, default: float = 0.0) -> float:
    """Safely convert string to float."""
    try:
        if value is None or value.strip() == '' or value.strip() == 'NA':
            return default
        return float(value.strip())
    except (ValueError, AttributeError):
        return default


def safe_int(value: str, default: int = 0) -> int:
    """Safely convert string to int."""
    try:
        if value is None or value.strip() == '' or value.strip() == 'NA':
            return default
        return int(float(value.strip()))
    except (ValueError, AttributeError):
        return default


def load_gpci_data(db: Session, file_path: Path, year: int) -> int:
    """
    Load GPCI (Geographic Practice Cost Index) data from CMS file.

    CMS GPCI file format (varies by year, typically CSV):
    - MAC (Medicare Administrative Contractor)
    - Locality
    - Locality Name
    - Work GPCI
    - PE GPCI
    - MP GPCI

    Args:
        db: Database session
        file_path: Path to GPCI CSV file
        year: Fee schedule year

    Returns:
        Number of records loaded
    """
    logger.info(f"Loading GPCI data from {file_path}")

    loaded = 0

    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Handle various column name formats from CMS
            mac_code = row.get('MAC', row.get('CARRIER', row.get('mac_code', ''))).strip()
            locality_code = row.get('Locality', row.get('LOCALITY', row.get('locality_code', ''))).strip()
            locality_name = row.get('Locality Name', row.get('LOCALITY_NAME', row.get('locality_name', ''))).strip()
            state = row.get('State', row.get('STATE', row.get('state', ''))).strip()[:2] if row.get('State') or row.get('STATE') or row.get('state') else None

            work_gpci = safe_float(row.get('Work GPCI', row.get('WORK_GPCI', row.get('work_gpci', '1.0'))))
            pe_gpci = safe_float(row.get('PE GPCI', row.get('PE_GPCI', row.get('pe_gpci', '1.0'))))
            mp_gpci = safe_float(row.get('MP GPCI', row.get('MP_GPCI', row.get('mp_gpci', '1.0'))))

            if not locality_code:
                continue

            locality = CMSLocality(
                id=uuid.uuid4(),
                mac_code=mac_code,
                locality_code=locality_code,
                locality_name=locality_name,
                state=state,
                work_gpci=work_gpci,
                pe_gpci=pe_gpci,
                mp_gpci=mp_gpci,
                year=year
            )
            db.add(locality)
            loaded += 1

            if loaded % 100 == 0:
                db.commit()
                logger.info(f"  Loaded {loaded} localities...")

    db.commit()
    logger.info(f"Loaded {loaded} GPCI/locality records")
    return loaded


def load_zip_to_locality(db: Session, file_path: Path, year: int) -> int:
    """
    Load ZIP code to locality mapping.

    CMS ZIP file format:
    - ZIP Code
    - Carrier/MAC
    - Locality
    - State

    Args:
        db: Database session
        file_path: Path to ZIP mapping CSV file
        year: Fee schedule year

    Returns:
        Number of records loaded
    """
    logger.info(f"Loading ZIP to locality mapping from {file_path}")

    loaded = 0

    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            zip_code = row.get('ZIP', row.get('zip_code', row.get('ZIP_CODE', ''))).strip()
            carrier = row.get('CARRIER', row.get('carrier_code', row.get('MAC', ''))).strip()
            locality = row.get('LOCALITY', row.get('locality_code', '')).strip()
            state = row.get('STATE', row.get('state', '')).strip()[:2] if row.get('STATE') or row.get('state') else None

            if not zip_code or not locality:
                continue

            # Ensure ZIP code is 5 digits
            zip_code = zip_code.zfill(5)[:5]

            mapping = ZIPToLocality(
                id=uuid.uuid4(),
                zip_code=zip_code,
                locality_code=locality,
                state=state,
                carrier_code=carrier,
                year=year
            )
            db.add(mapping)
            loaded += 1

            if loaded % 5000 == 0:
                db.commit()
                db.expire_all()  # Free memory
                logger.info(f"  Loaded {loaded} ZIP mappings...")

    db.commit()
    logger.info(f"Loaded {loaded} ZIP to locality mappings")
    return loaded


def load_mpfs_rvu_data(db: Session, file_path: Path, year: int, quarter: int = 1) -> int:
    """
    Load MPFS RVU data from CMS file.

    CMS MPFS file format (varies by year):
    - HCPCS (CPT/HCPCS code)
    - MOD (Modifier)
    - DESCRIPTION
    - STATUS CODE
    - Work RVU
    - Non-Fac PE RVU
    - Facility PE RVU
    - MP RVU
    - Non-Fac Total
    - Facility Total
    - Global Days
    - And many more columns...

    Args:
        db: Database session
        file_path: Path to MPFS RVU CSV file
        year: Fee schedule year
        quarter: Quarter (1-4) for quarterly updates

    Returns:
        Number of records loaded
    """
    logger.info(f"Loading MPFS RVU data from {file_path}")

    loaded = 0

    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Get HCPCS code (required)
            hcpcs = row.get('HCPCS', row.get('hcpcs_code', row.get('CPT', ''))).strip()
            if not hcpcs:
                continue

            # Get modifier (optional)
            modifier = row.get('MOD', row.get('MODIFIER', row.get('modifier', ''))).strip() or None

            # Description
            description = row.get('DESCRIPTION', row.get('description', '')).strip()

            # Status indicators
            status_code = row.get('STATUS CODE', row.get('STATUS', row.get('status_code', ''))).strip() or None
            pctc = row.get('PCTC IND', row.get('PC/TC', row.get('pctc_indicator', ''))).strip() or None

            # RVUs
            work_rvu = safe_float(row.get('WORK RVU', row.get('work_rvu', '0')))
            non_fac_pe = safe_float(row.get('NON-FAC PE RVU', row.get('NON_FAC_PE_RVU', row.get('non_facility_pe_rvu', '0'))))
            fac_pe = safe_float(row.get('FAC PE RVU', row.get('FAC_PE_RVU', row.get('facility_pe_rvu', '0'))))
            mp_rvu = safe_float(row.get('MP RVU', row.get('mp_rvu', '0')))

            # Totals
            non_fac_total = safe_float(row.get('NON-FAC TOTAL', row.get('NON_FAC_TOTAL', row.get('non_facility_total', '0'))))
            fac_total = safe_float(row.get('FAC TOTAL', row.get('FAC_TOTAL', row.get('facility_total', '0'))))

            # Global days
            global_days = row.get('GLOB DAYS', row.get('GLOBAL', row.get('global_days', ''))).strip() or None

            # Surgery indicators
            mult_proc = row.get('MULT PROC', row.get('mult_proc', '')).strip() or None
            bilateral = row.get('BILAT SURG', row.get('bilateral_surgery', '')).strip() or None
            asst_surg = row.get('ASST SURG', row.get('assistant_surgery', '')).strip() or None
            co_surg = row.get('CO-SURG', row.get('co_surgeons', '')).strip() or None
            team_surg = row.get('TEAM SURG', row.get('team_surgery', '')).strip() or None

            # Other indicators
            endo_base = row.get('ENDO BASE', row.get('endo_base', '')).strip() or None
            conv_factor = row.get('CONV', row.get('conv_factor_indicator', '')).strip() or None
            phys_super = row.get('PHY SUPV', row.get('physician_supervision', '')).strip() or None
            diag_family = row.get('DIAG IM FAM', row.get('diag_imaging_family', '')).strip() or None

            rate = MPFSRate(
                id=uuid.uuid4(),
                hcpcs_code=hcpcs,
                modifier=modifier,
                description=description,
                status_code=status_code,
                pctc_indicator=pctc,
                work_rvu=work_rvu,
                non_facility_pe_rvu=non_fac_pe,
                facility_pe_rvu=fac_pe,
                mp_rvu=mp_rvu,
                non_facility_total=non_fac_total,
                facility_total=fac_total,
                global_days=global_days,
                mult_proc=mult_proc,
                bilateral_surgery=bilateral,
                assistant_surgery=asst_surg,
                co_surgeons=co_surg,
                team_surgery=team_surg,
                endo_base=endo_base,
                conv_factor_indicator=conv_factor,
                physician_supervision=phys_super,
                diag_imaging_family=diag_family,
                year=year,
                quarter=quarter
            )
            db.add(rate)
            loaded += 1

            if loaded % 1000 == 0:
                db.commit()
                db.expire_all()
                logger.info(f"  Loaded {loaded} MPFS rates...")

    db.commit()
    logger.info(f"Loaded {loaded} MPFS RVU records")
    return loaded


def load_conversion_factors(db: Session) -> int:
    """
    Load historical conversion factors.

    The conversion factor is published annually by CMS and converts
    total RVUs to dollar amounts.

    Args:
        db: Database session

    Returns:
        Number of records loaded
    """
    logger.info("Loading conversion factors...")

    # Historical conversion factors (add more as needed)
    # Source: CMS Final Rule each year
    factors = [
        {"year": 2020, "cf": 36.0896, "anes_cf": 21.95, "effective_date": "2020-01-01"},
        {"year": 2021, "cf": 34.8931, "anes_cf": 21.56, "effective_date": "2021-01-01"},
        {"year": 2022, "cf": 34.6062, "anes_cf": 21.27, "effective_date": "2022-01-01"},
        {"year": 2023, "cf": 33.8872, "anes_cf": 20.97, "effective_date": "2023-01-01"},
        {"year": 2024, "cf": 32.7442, "anes_cf": 20.44, "effective_date": "2024-01-01"},
        {"year": 2025, "cf": 32.3465, "anes_cf": 20.19, "effective_date": "2025-01-01", "notes": "3.37% reduction from 2024"},
    ]

    loaded = 0
    for f in factors:
        # Check if already exists
        existing = db.query(ConversionFactor).filter(ConversionFactor.year == f["year"]).first()
        if existing:
            # Update
            existing.conversion_factor = f["cf"]
            existing.anesthesia_conversion_factor = f.get("anes_cf")
            existing.effective_date = f.get("effective_date")
            existing.notes = f.get("notes")
        else:
            # Create
            cf = ConversionFactor(
                id=uuid.uuid4(),
                year=f["year"],
                conversion_factor=f["cf"],
                anesthesia_conversion_factor=f.get("anes_cf"),
                effective_date=f.get("effective_date"),
                notes=f.get("notes")
            )
            db.add(cf)
        loaded += 1

    db.commit()
    logger.info(f"Loaded {loaded} conversion factors")
    return loaded


def create_sample_data(year: int = 2025) -> None:
    """
    Create sample data files for testing.

    This creates minimal sample CSV files that can be used to test
    the loading process before downloading full CMS data.

    Args:
        year: Year for sample data
    """
    data_dir = DATA_DIR / str(year)
    data_dir.mkdir(parents=True, exist_ok=True)

    # Sample GPCI data
    gpci_file = data_dir / "gpci_sample.csv"
    with open(gpci_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['MAC', 'Locality', 'Locality Name', 'State', 'Work GPCI', 'PE GPCI', 'MP GPCI'])
        # Sample localities
        sample_localities = [
            ('01102', '01', 'Alabama', 'AL', '0.9695', '0.8667', '0.5920'),
            ('01102', '99', 'Rest of Alabama', 'AL', '0.9501', '0.8483', '0.5411'),
            ('31143', '01', 'San Francisco-Oakland-Berkeley, CA', 'CA', '1.0734', '1.4860', '0.6693'),
            ('31143', '18', 'Rest of California', 'CA', '1.0290', '1.1140', '0.6230'),
            ('05440', '01', 'Manhattan, NY', 'NY', '1.0817', '1.3099', '1.4533'),
            ('05440', '02', 'NYC Suburbs', 'NY', '1.0528', '1.2470', '1.2110'),
            ('05102', '04', 'Rest of New York', 'NY', '1.0167', '0.9710', '0.6670'),
            ('05535', '01', 'Dallas, TX', 'TX', '1.0240', '0.9990', '0.8490'),
            ('05535', '20', 'Rest of Texas', 'TX', '0.9830', '0.9120', '0.7290'),
            ('12302', '01', 'Chicago, IL', 'IL', '1.0371', '1.0690', '1.3070'),
            ('12302', '16', 'Rest of Illinois', 'IL', '0.9820', '0.9340', '0.6970'),
        ]
        for loc in sample_localities:
            writer.writerow(loc)
    logger.info(f"Created sample GPCI file: {gpci_file}")

    # Sample ZIP to locality mapping
    zip_file = data_dir / "zip_locality_sample.csv"
    with open(zip_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ZIP', 'CARRIER', 'LOCALITY', 'STATE'])
        # Sample ZIP codes
        sample_zips = [
            ('35004', '01102', '99', 'AL'),
            ('35005', '01102', '99', 'AL'),
            ('94102', '31143', '01', 'CA'),  # San Francisco
            ('94103', '31143', '01', 'CA'),
            ('90210', '31143', '18', 'CA'),  # Beverly Hills (Rest of CA)
            ('10001', '05440', '01', 'NY'),  # Manhattan
            ('10002', '05440', '01', 'NY'),
            ('10301', '05440', '02', 'NY'),  # Staten Island
            ('14850', '05102', '04', 'NY'),  # Ithaca
            ('75001', '05535', '01', 'TX'),  # Dallas
            ('77001', '05535', '20', 'TX'),  # Houston (Rest of TX)
            ('60601', '12302', '01', 'IL'),  # Chicago
            ('61820', '12302', '16', 'IL'),  # Champaign
        ]
        for z in sample_zips:
            writer.writerow(z)
    logger.info(f"Created sample ZIP file: {zip_file}")

    # Sample MPFS RVU data
    mpfs_file = data_dir / "mpfs_rvu_sample.csv"
    with open(mpfs_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'HCPCS', 'MOD', 'DESCRIPTION', 'STATUS CODE', 'PCTC IND',
            'WORK RVU', 'NON-FAC PE RVU', 'FAC PE RVU', 'MP RVU',
            'NON-FAC TOTAL', 'FAC TOTAL', 'GLOB DAYS',
            'MULT PROC', 'BILAT SURG', 'ASST SURG', 'CO-SURG', 'TEAM SURG'
        ])
        # Sample common CPT codes
        sample_codes = [
            # E/M Codes (Office Visits)
            ('99212', '', 'Office/outpatient visit, established patient, straightforward', 'A', '', '0.70', '0.94', '0.48', '0.04', '1.68', '1.22', 'XXX', '', '', '1', '', ''),
            ('99213', '', 'Office/outpatient visit, established patient, low complexity', 'A', '', '1.30', '1.30', '0.75', '0.08', '2.68', '2.13', 'XXX', '', '', '1', '', ''),
            ('99214', '', 'Office/outpatient visit, established patient, moderate complexity', 'A', '', '1.92', '1.67', '1.10', '0.13', '3.72', '3.15', 'XXX', '', '', '1', '', ''),
            ('99215', '', 'Office/outpatient visit, established patient, high complexity', 'A', '', '2.80', '2.05', '1.50', '0.18', '5.03', '4.48', 'XXX', '', '', '1', '', ''),
            # New Patient Visits
            ('99202', '', 'Office/outpatient visit, new patient, straightforward', 'A', '', '0.93', '1.12', '0.58', '0.06', '2.11', '1.57', 'XXX', '', '', '1', '', ''),
            ('99203', '', 'Office/outpatient visit, new patient, low complexity', 'A', '', '1.60', '1.61', '0.97', '0.11', '3.32', '2.68', 'XXX', '', '', '1', '', ''),
            ('99204', '', 'Office/outpatient visit, new patient, moderate complexity', 'A', '', '2.60', '2.33', '1.60', '0.18', '5.11', '4.38', 'XXX', '', '', '1', '', ''),
            ('99205', '', 'Office/outpatient visit, new patient, high complexity', 'A', '', '3.50', '2.80', '2.06', '0.24', '6.54', '5.80', 'XXX', '', '', '1', '', ''),
            # Procedures
            ('10060', '', 'Incision and drainage of abscess; simple or single', 'A', '', '1.22', '2.61', '0.89', '0.11', '3.94', '2.22', '010', '2', '1', '0', '0', '0'),
            ('11102', '', 'Tangential biopsy of skin; single lesion', 'A', '', '0.76', '1.68', '0.55', '0.09', '2.53', '1.40', '000', '2', '0', '0', '0', '0'),
            ('20610', '', 'Arthrocentesis; major joint or bursa', 'A', '', '0.79', '1.22', '0.50', '0.06', '2.07', '1.35', '000', '2', '0', '1', '0', '0'),
            ('36415', '', 'Collection of venous blood by venipuncture', 'A', '', '0.00', '0.18', '0.18', '0.02', '0.20', '0.20', 'XXX', '', '', '9', '', ''),
            # Technical/Professional Components
            ('71046', '', 'Radiologic exam, chest; 2 views', 'A', '', '0.22', '0.23', '0.15', '0.02', '0.47', '0.39', 'XXX', '5', '', '9', '', ''),
            ('71046', '26', 'Radiologic exam, chest; 2 views - Professional component', 'A', '2', '0.22', '0.08', '0.08', '0.02', '0.32', '0.32', 'XXX', '5', '', '9', '', ''),
            ('71046', 'TC', 'Radiologic exam, chest; 2 views - Technical component', 'A', '1', '0.00', '0.15', '0.07', '0.00', '0.15', '0.07', 'XXX', '5', '', '9', '', ''),
            ('93000', '', 'Electrocardiogram, routine ECG with at least 12 leads', 'A', '', '0.17', '0.20', '0.10', '0.01', '0.38', '0.28', 'XXX', '', '', '9', '', ''),
            # Surgical codes
            ('27447', '', 'Arthroplasty, knee, condyle and plateau; total knee', 'A', '', '20.74', '45.04', '20.42', '3.96', '69.74', '45.12', '090', '2', '0', '1', '1', '1'),
            ('27130', '', 'Arthroplasty, acetabular and proximal femoral prosthetic replacement (total hip)', 'A', '', '20.67', '40.20', '18.90', '3.65', '64.52', '43.22', '090', '2', '0', '1', '1', '1'),
            ('33533', '', 'Coronary artery bypass; single arterial graft', 'A', '', '33.52', '67.21', '33.00', '6.12', '106.85', '72.64', '090', '2', '0', '2', '1', '1'),
        ]
        for code in sample_codes:
            writer.writerow(code)
    logger.info(f"Created sample MPFS file: {mpfs_file}")

    logger.info(f"\nSample data files created in {data_dir}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Load CMS Fee Schedule data into database"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2025,
        help="Fee schedule year to load (default: 2025)"
    )
    parser.add_argument(
        "--quarter",
        type=int,
        default=1,
        help="Quarter for MPFS data (1-4, default: 1)"
    )
    parser.add_argument(
        "--db-url",
        type=str,
        help="Database URL (default: from DATABASE_URL env or local postgres)"
    )
    parser.add_argument(
        "--create-sample",
        action="store_true",
        help="Create sample data files for testing"
    )
    parser.add_argument(
        "--sample-only",
        action="store_true",
        help="Only create sample data, don't load to database"
    )
    parser.add_argument(
        "--gpci-file",
        type=str,
        help="Path to GPCI CSV file"
    )
    parser.add_argument(
        "--zip-file",
        type=str,
        help="Path to ZIP-to-locality CSV file"
    )
    parser.add_argument(
        "--mpfs-file",
        type=str,
        help="Path to MPFS RVU CSV file"
    )
    parser.add_argument(
        "--conversion-factors-only",
        action="store_true",
        help="Only load conversion factors (no data files needed)"
    )

    args = parser.parse_args()

    # Create sample data if requested
    if args.create_sample or args.sample_only:
        create_sample_data(args.year)
        if args.sample_only:
            return 0

    # Connect to database
    db_url = args.db_url or get_database_url()
    logger.info(f"Connecting to database...")

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Always load conversion factors
        load_conversion_factors(db)

        if args.conversion_factors_only:
            logger.info("Loaded conversion factors only")
            return 0

        # Determine data directory
        data_dir = DATA_DIR / str(args.year)

        if not data_dir.exists():
            logger.warning(f"Data directory not found: {data_dir}")
            logger.info("Run with --create-sample to create sample data first")
            return 1

        # Load GPCI data
        gpci_file = Path(args.gpci_file) if args.gpci_file else data_dir / "gpci_sample.csv"
        if gpci_file.exists():
            load_gpci_data(db, gpci_file, args.year)
        else:
            # Try to find any GPCI file
            gpci_files = list(data_dir.glob("*gpci*.csv"))
            if gpci_files:
                load_gpci_data(db, gpci_files[0], args.year)
            else:
                logger.warning("No GPCI file found")

        # Load ZIP to locality mapping
        zip_file = Path(args.zip_file) if args.zip_file else data_dir / "zip_locality_sample.csv"
        if zip_file.exists():
            load_zip_to_locality(db, zip_file, args.year)
        else:
            zip_files = list(data_dir.glob("*zip*.csv"))
            if zip_files:
                load_zip_to_locality(db, zip_files[0], args.year)
            else:
                logger.warning("No ZIP mapping file found")

        # Load MPFS RVU data
        mpfs_file = Path(args.mpfs_file) if args.mpfs_file else data_dir / "mpfs_rvu_sample.csv"
        if mpfs_file.exists():
            load_mpfs_rvu_data(db, mpfs_file, args.year, args.quarter)
        else:
            mpfs_files = list(data_dir.glob("*mpfs*.csv")) + list(data_dir.glob("*rvu*.csv"))
            if mpfs_files:
                load_mpfs_rvu_data(db, mpfs_files[0], args.year, args.quarter)
            else:
                logger.warning("No MPFS RVU file found")

        logger.info("\n" + "="*50)
        logger.info("Fee schedule data load complete!")
        logger.info("="*50)

        return 0

    except Exception as e:
        logger.error(f"Error loading data: {e}", exc_info=True)
        db.rollback()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
