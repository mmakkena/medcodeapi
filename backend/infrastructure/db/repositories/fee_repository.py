"""
Fee Repository

Repository for Medicare Fee Schedule operations.
Handles RVU lookups, GPCI calculations, and reimbursement calculations.
"""

import logging
from typing import Optional
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


@dataclass
class FeeData:
    """Fee schedule data for a procedure code."""
    code: str
    description: Optional[str]
    work_rvu: float
    facility_pe_rvu: float
    non_facility_pe_rvu: float
    mp_rvu: float
    work_gpci: float
    pe_gpci: float
    mp_gpci: float
    conversion_factor: float
    locality_name: Optional[str] = None
    mac: Optional[str] = None


class FeeRepository:
    """
    Repository for Medicare Fee Schedule operations.

    Supports:
    - RVU lookups by CPT/HCPCS code
    - Locality-specific GPCI values
    - Reimbursement calculations
    """

    # 2025 CMS Conversion Factor
    CONVERSION_FACTOR_2025 = 32.74
    CONVERSION_FACTOR_2024 = 32.74

    def __init__(self, db: Session):
        self.db = db

    def get_fee_by_code_and_locality(
        self,
        code: str,
        zip_code: str,
        year: int = 2025
    ) -> Optional[FeeData]:
        """
        Get fee schedule data for a code and locality.

        Args:
            code: CPT or HCPCS code
            zip_code: ZIP code for locality lookup
            year: Fee schedule year

        Returns:
            FeeData object or None if not found
        """
        try:
            # First get the locality for the ZIP code
            locality = self._get_locality_for_zip(zip_code)

            # Get RVU data for the code
            rvu_data = self._get_rvu_data(code, year)
            if not rvu_data:
                return None

            # Get GPCI data for the locality
            gpci_data = self._get_gpci_data(locality, year) if locality else None

            # Use national average GPCIs if locality not found
            if not gpci_data:
                gpci_data = {
                    "work_gpci": 1.0,
                    "pe_gpci": 1.0,
                    "mp_gpci": 1.0
                }

            conversion_factor = (
                self.CONVERSION_FACTOR_2025 if year >= 2025
                else self.CONVERSION_FACTOR_2024
            )

            return FeeData(
                code=code.upper(),
                description=rvu_data.get("description"),
                work_rvu=rvu_data.get("work_rvu", 0.0),
                facility_pe_rvu=rvu_data.get("facility_pe_rvu", 0.0),
                non_facility_pe_rvu=rvu_data.get("non_facility_pe_rvu", 0.0),
                mp_rvu=rvu_data.get("mp_rvu", 0.0),
                work_gpci=gpci_data.get("work_gpci", 1.0),
                pe_gpci=gpci_data.get("pe_gpci", 1.0),
                mp_gpci=gpci_data.get("mp_gpci", 1.0),
                conversion_factor=conversion_factor,
                locality_name=gpci_data.get("locality_name"),
                mac=gpci_data.get("mac")
            )

        except Exception as e:
            logger.error(f"Fee lookup failed for {code}: {e}")
            return None

    def _get_locality_for_zip(self, zip_code: str) -> Optional[str]:
        """Get locality code for a ZIP code."""
        try:
            sql = text("""
                SELECT locality_code, locality_name
                FROM zip_locality_mapping
                WHERE zip_code = :zip_code
                LIMIT 1
            """)

            result = self.db.execute(sql, {"zip_code": zip_code[:5]}).fetchone()

            if result:
                return result.locality_code
            return None

        except Exception as e:
            logger.debug(f"Locality lookup failed: {e}")
            return None

    def _get_rvu_data(self, code: str, year: int) -> Optional[dict]:
        """Get RVU data for a code."""
        try:
            sql = text("""
                SELECT
                    code,
                    description,
                    work_rvu,
                    facility_pe_rvu,
                    non_facility_pe_rvu,
                    mp_rvu
                FROM fee_schedule_rvu
                WHERE code = :code
                  AND year = :year
                LIMIT 1
            """)

            result = self.db.execute(sql, {
                "code": code.upper(),
                "year": year
            }).fetchone()

            if result:
                return {
                    "description": result.description if hasattr(result, 'description') else None,
                    "work_rvu": float(result.work_rvu) if result.work_rvu else 0.0,
                    "facility_pe_rvu": float(result.facility_pe_rvu) if result.facility_pe_rvu else 0.0,
                    "non_facility_pe_rvu": float(result.non_facility_pe_rvu) if result.non_facility_pe_rvu else 0.0,
                    "mp_rvu": float(result.mp_rvu) if result.mp_rvu else 0.0
                }
            return None

        except Exception as e:
            logger.debug(f"RVU lookup failed: {e}")
            return None

    def _get_gpci_data(self, locality: str, year: int) -> Optional[dict]:
        """Get GPCI data for a locality."""
        try:
            sql = text("""
                SELECT
                    locality_code,
                    locality_name,
                    mac,
                    work_gpci,
                    pe_gpci,
                    mp_gpci
                FROM gpci_values
                WHERE locality_code = :locality
                  AND year = :year
                LIMIT 1
            """)

            result = self.db.execute(sql, {
                "locality": locality,
                "year": year
            }).fetchone()

            if result:
                return {
                    "locality_name": result.locality_name if hasattr(result, 'locality_name') else None,
                    "mac": result.mac if hasattr(result, 'mac') else None,
                    "work_gpci": float(result.work_gpci) if result.work_gpci else 1.0,
                    "pe_gpci": float(result.pe_gpci) if result.pe_gpci else 1.0,
                    "mp_gpci": float(result.mp_gpci) if result.mp_gpci else 1.0
                }
            return None

        except Exception as e:
            logger.debug(f"GPCI lookup failed: {e}")
            return None

    def calculate_reimbursement(
        self,
        code: str,
        zip_code: str,
        year: int = 2025,
        facility: bool = False
    ) -> Optional[dict]:
        """
        Calculate Medicare reimbursement for a code.

        Args:
            code: CPT or HCPCS code
            zip_code: ZIP code for locality
            year: Fee schedule year
            facility: Whether to use facility or non-facility rate

        Returns:
            Dictionary with calculation details or None
        """
        fee_data = self.get_fee_by_code_and_locality(code, zip_code, year)

        if not fee_data:
            return None

        pe_rvu = fee_data.facility_pe_rvu if facility else fee_data.non_facility_pe_rvu

        # Calculate adjusted RVUs
        adjusted_work = fee_data.work_rvu * fee_data.work_gpci
        adjusted_pe = pe_rvu * fee_data.pe_gpci
        adjusted_mp = fee_data.mp_rvu * fee_data.mp_gpci

        total_adjusted_rvu = adjusted_work + adjusted_pe + adjusted_mp
        reimbursement = total_adjusted_rvu * fee_data.conversion_factor

        return {
            "code": code.upper(),
            "description": fee_data.description,
            "rate_type": "Facility" if facility else "Non-Facility",
            "year": year,
            "locality": {
                "zip_code": zip_code,
                "locality_name": fee_data.locality_name,
                "mac": fee_data.mac
            },
            "rvu": {
                "work": round(fee_data.work_rvu, 4),
                "pe": round(pe_rvu, 4),
                "mp": round(fee_data.mp_rvu, 4),
                "total": round(fee_data.work_rvu + pe_rvu + fee_data.mp_rvu, 4)
            },
            "gpci": {
                "work": round(fee_data.work_gpci, 4),
                "pe": round(fee_data.pe_gpci, 4),
                "mp": round(fee_data.mp_gpci, 4)
            },
            "adjusted_rvu": {
                "work": round(adjusted_work, 4),
                "pe": round(adjusted_pe, 4),
                "mp": round(adjusted_mp, 4),
                "total": round(total_adjusted_rvu, 4)
            },
            "conversion_factor": fee_data.conversion_factor,
            "reimbursement": round(reimbursement, 2)
        }

    def get_rvu_by_code(self, code: str, year: int = 2025) -> Optional[dict]:
        """
        Get RVU values for a code (without locality adjustment).

        Args:
            code: CPT or HCPCS code
            year: Fee schedule year

        Returns:
            Dictionary with RVU values or None
        """
        rvu_data = self._get_rvu_data(code, year)

        if not rvu_data:
            return None

        return {
            "code": code.upper(),
            "description": rvu_data.get("description"),
            "work_rvu": rvu_data.get("work_rvu", 0.0),
            "facility_pe_rvu": rvu_data.get("facility_pe_rvu", 0.0),
            "non_facility_pe_rvu": rvu_data.get("non_facility_pe_rvu", 0.0),
            "mp_rvu": rvu_data.get("mp_rvu", 0.0),
            "total_facility_rvu": round(
                rvu_data.get("work_rvu", 0.0) +
                rvu_data.get("facility_pe_rvu", 0.0) +
                rvu_data.get("mp_rvu", 0.0), 4
            ),
            "total_non_facility_rvu": round(
                rvu_data.get("work_rvu", 0.0) +
                rvu_data.get("non_facility_pe_rvu", 0.0) +
                rvu_data.get("mp_rvu", 0.0), 4
            ),
            "year": year
        }
