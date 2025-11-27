"""
Fee Schedule Service

Provides functionality for:
- Looking up Medicare rates by CPT code and location
- Calculating prices using RVUs and GPCIs
- ZIP code to locality mapping
- Searching fee schedule data
- Contract analysis (comparing private rates to Medicare)
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from app.models.cms_locality import CMSLocality, ZIPToLocality
from app.models.mpfs_rate import MPFSRate, ConversionFactor

logger = logging.getLogger(__name__)


class FeeScheduleService:
    """Service for Medicare Physician Fee Schedule operations."""

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db

    def get_locality_from_zip(
        self,
        zip_code: str,
        year: int = 2025
    ) -> Optional[Dict[str, Any]]:
        """
        Get CMS locality information from a ZIP code.

        Args:
            zip_code: 5-digit ZIP code
            year: Fee schedule year

        Returns:
            Dictionary with locality info and GPCI values, or None
        """
        # Normalize ZIP code
        zip_code = zip_code.strip().zfill(5)[:5]

        # Look up ZIP to locality mapping
        mapping = self.db.query(ZIPToLocality).filter(
            and_(
                ZIPToLocality.zip_code == zip_code,
                ZIPToLocality.year == year
            )
        ).first()

        if not mapping:
            # Try to find any year's mapping as fallback
            mapping = self.db.query(ZIPToLocality).filter(
                ZIPToLocality.zip_code == zip_code
            ).order_by(ZIPToLocality.year.desc()).first()

        if not mapping:
            return None

        # Get locality details with GPCI values
        locality = self.db.query(CMSLocality).filter(
            and_(
                CMSLocality.locality_code == mapping.locality_code,
                CMSLocality.year == year
            )
        ).first()

        if not locality:
            # Fallback to any year
            locality = self.db.query(CMSLocality).filter(
                CMSLocality.locality_code == mapping.locality_code
            ).order_by(CMSLocality.year.desc()).first()

        if not locality:
            return None

        return {
            "zip_code": zip_code,
            "locality_code": locality.locality_code,
            "locality_name": locality.locality_name,
            "mac_code": locality.mac_code,
            "state": locality.state or mapping.state,
            "work_gpci": locality.work_gpci,
            "pe_gpci": locality.pe_gpci,
            "mp_gpci": locality.mp_gpci,
            "year": locality.year
        }

    def get_conversion_factor(self, year: int = 2025) -> Optional[float]:
        """
        Get the Medicare conversion factor for a given year.

        Args:
            year: Fee schedule year

        Returns:
            Conversion factor value or None
        """
        cf = self.db.query(ConversionFactor).filter(
            ConversionFactor.year == year
        ).first()

        if cf:
            return cf.conversion_factor

        # Fallback to most recent year
        cf = self.db.query(ConversionFactor).order_by(
            ConversionFactor.year.desc()
        ).first()

        return cf.conversion_factor if cf else None

    def calculate_price(
        self,
        work_rvu: float,
        pe_rvu: float,
        mp_rvu: float,
        work_gpci: float,
        pe_gpci: float,
        mp_gpci: float,
        conversion_factor: float
    ) -> float:
        """
        Calculate Medicare payment using RVU formula.

        Formula: [(Work RVU * Work GPCI) + (PE RVU * PE GPCI) + (MP RVU * MP GPCI)] * CF

        Args:
            work_rvu: Work Relative Value Unit
            pe_rvu: Practice Expense RVU (facility or non-facility)
            mp_rvu: Malpractice RVU
            work_gpci: Work Geographic Practice Cost Index
            pe_gpci: Practice Expense GPCI
            mp_gpci: Malpractice GPCI
            conversion_factor: Annual conversion factor

        Returns:
            Calculated payment amount
        """
        adjusted_rvu = (
            (work_rvu * work_gpci) +
            (pe_rvu * pe_gpci) +
            (mp_rvu * mp_gpci)
        )
        return round(adjusted_rvu * conversion_factor, 2)

    def get_rate_by_code(
        self,
        hcpcs_code: str,
        year: int = 2025,
        modifier: Optional[str] = None
    ) -> Optional[MPFSRate]:
        """
        Get MPFS rate record for a specific code.

        Args:
            hcpcs_code: CPT or HCPCS code
            year: Fee schedule year
            modifier: Optional modifier (TC, 26, etc.)

        Returns:
            MPFSRate object or None
        """
        query = self.db.query(MPFSRate).filter(
            and_(
                MPFSRate.hcpcs_code == hcpcs_code.upper().strip(),
                MPFSRate.year == year
            )
        )

        if modifier:
            query = query.filter(MPFSRate.modifier == modifier.upper().strip())
        else:
            # Get base rate (no modifier)
            query = query.filter(
                or_(MPFSRate.modifier.is_(None), MPFSRate.modifier == '')
            )

        return query.first()

    def get_price(
        self,
        hcpcs_code: str,
        zip_code: str,
        year: int = 2025,
        modifier: Optional[str] = None,
        setting: str = "non_facility"
    ) -> Optional[Dict[str, Any]]:
        """
        Get Medicare price for a code at a specific location.

        Args:
            hcpcs_code: CPT or HCPCS code
            zip_code: 5-digit ZIP code
            year: Fee schedule year
            modifier: Optional modifier (TC, 26, etc.)
            setting: 'facility' or 'non_facility' (default)

        Returns:
            Dictionary with price details or None
        """
        # Get rate
        rate = self.get_rate_by_code(hcpcs_code, year, modifier)
        if not rate:
            return None

        # Get locality info
        locality = self.get_locality_from_zip(zip_code, year)
        if not locality:
            # Use national average (GPCI = 1.0)
            locality = {
                "zip_code": zip_code,
                "locality_code": "00",
                "locality_name": "National Average",
                "state": None,
                "work_gpci": 1.0,
                "pe_gpci": 1.0,
                "mp_gpci": 1.0,
                "year": year
            }

        # Get conversion factor
        cf = self.get_conversion_factor(year)
        if not cf:
            return None

        # Select PE RVU based on setting
        if setting == "facility":
            pe_rvu = rate.facility_pe_rvu or 0.0
        else:
            pe_rvu = rate.non_facility_pe_rvu or 0.0

        # Calculate price
        price = self.calculate_price(
            work_rvu=rate.work_rvu or 0.0,
            pe_rvu=pe_rvu,
            mp_rvu=rate.mp_rvu or 0.0,
            work_gpci=locality["work_gpci"],
            pe_gpci=locality["pe_gpci"],
            mp_gpci=locality["mp_gpci"],
            conversion_factor=cf
        )

        # Also calculate national price for comparison
        national_price = self.calculate_price(
            work_rvu=rate.work_rvu or 0.0,
            pe_rvu=pe_rvu,
            mp_rvu=rate.mp_rvu or 0.0,
            work_gpci=1.0,
            pe_gpci=1.0,
            mp_gpci=1.0,
            conversion_factor=cf
        )

        return {
            "hcpcs_code": rate.hcpcs_code,
            "modifier": rate.modifier,
            "description": rate.description,
            "setting": setting,
            "price": price,
            "national_price": national_price,
            "work_rvu": rate.work_rvu,
            "pe_rvu": pe_rvu,
            "mp_rvu": rate.mp_rvu,
            "total_rvu": (rate.work_rvu or 0) + pe_rvu + (rate.mp_rvu or 0),
            "conversion_factor": cf,
            "locality": locality,
            "global_days": rate.global_days,
            "status_code": rate.status_code,
            "year": year
        }

    def search_codes(
        self,
        query: str,
        year: int = 2025,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search fee schedule by code or description.

        Args:
            query: Search query (code or description text)
            year: Fee schedule year
            limit: Maximum results to return
            offset: Results offset for pagination

        Returns:
            List of matching codes with RVU info
        """
        query = query.strip().upper()

        # Check if query looks like a code (starts with number or specific pattern)
        is_code_query = query.isdigit() or (
            len(query) <= 5 and query[0].isdigit()
        )

        if is_code_query:
            # Exact code match or prefix match
            results = self.db.query(MPFSRate).filter(
                and_(
                    MPFSRate.hcpcs_code.like(f"{query}%"),
                    MPFSRate.year == year,
                    or_(MPFSRate.modifier.is_(None), MPFSRate.modifier == '')
                )
            ).order_by(MPFSRate.hcpcs_code).limit(limit).offset(offset).all()
        else:
            # Description search (case-insensitive)
            results = self.db.query(MPFSRate).filter(
                and_(
                    MPFSRate.description.ilike(f"%{query}%"),
                    MPFSRate.year == year,
                    or_(MPFSRate.modifier.is_(None), MPFSRate.modifier == '')
                )
            ).order_by(MPFSRate.hcpcs_code).limit(limit).offset(offset).all()

        return [self._rate_to_dict(r) for r in results]

    def _rate_to_dict(self, rate: MPFSRate) -> Dict[str, Any]:
        """Convert MPFSRate to dictionary."""
        return {
            "hcpcs_code": rate.hcpcs_code,
            "modifier": rate.modifier,
            "description": rate.description,
            "work_rvu": rate.work_rvu,
            "non_facility_pe_rvu": rate.non_facility_pe_rvu,
            "facility_pe_rvu": rate.facility_pe_rvu,
            "mp_rvu": rate.mp_rvu,
            "non_facility_total": rate.non_facility_total,
            "facility_total": rate.facility_total,
            "global_days": rate.global_days,
            "status_code": rate.status_code,
            "year": rate.year
        }

    def get_available_years(self) -> List[int]:
        """Get list of years with fee schedule data."""
        years = self.db.query(MPFSRate.year).distinct().order_by(
            MPFSRate.year.desc()
        ).all()
        return [y[0] for y in years]

    def get_localities(self, year: int = 2025, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of localities with GPCI values.

        Args:
            year: Fee schedule year
            state: Optional state filter (2-letter code)

        Returns:
            List of locality dictionaries
        """
        query = self.db.query(CMSLocality).filter(CMSLocality.year == year)

        if state:
            query = query.filter(CMSLocality.state == state.upper())

        localities = query.order_by(CMSLocality.locality_name).all()

        return [
            {
                "locality_code": loc.locality_code,
                "locality_name": loc.locality_name,
                "mac_code": loc.mac_code,
                "state": loc.state,
                "work_gpci": loc.work_gpci,
                "pe_gpci": loc.pe_gpci,
                "mp_gpci": loc.mp_gpci,
                "year": loc.year
            }
            for loc in localities
        ]

    def analyze_fee_schedule(
        self,
        codes_with_rates: List[Dict[str, Any]],
        zip_code: str,
        year: int = 2025,
        setting: str = "non_facility"
    ) -> Dict[str, Any]:
        """
        Analyze a list of codes with contracted rates against Medicare.

        This is the "Contract Analyzer" feature - compares private payer
        rates against Medicare baseline.

        Args:
            codes_with_rates: List of dicts with 'code' and 'rate' keys,
                             optionally 'volume' for revenue impact
            zip_code: ZIP code for locality-adjusted pricing
            year: CMS year to compare against
            setting: 'facility' or 'non_facility'

        Returns:
            Analysis results with variance details
        """
        results = {
            "total_codes": len(codes_with_rates),
            "codes_matched": 0,
            "codes_unmatched": 0,
            "codes_below_medicare": 0,
            "codes_above_medicare": 0,
            "codes_equal": 0,
            "total_variance": 0.0,
            "total_revenue_impact": 0.0,
            "line_items": [],
            "red_flags": [],  # Codes significantly below Medicare
        }

        for item in codes_with_rates:
            code = item.get("code", "").strip()
            contracted_rate = float(item.get("rate", 0))
            volume = int(item.get("volume", 0)) if item.get("volume") else None
            description = item.get("description", "")

            # Get Medicare price
            medicare_data = self.get_price(
                hcpcs_code=code,
                zip_code=zip_code,
                year=year,
                setting=setting
            )

            if medicare_data:
                medicare_rate = medicare_data["price"]
                variance = contracted_rate - medicare_rate
                variance_pct = (variance / medicare_rate * 100) if medicare_rate > 0 else 0

                results["codes_matched"] += 1

                if variance < 0:
                    results["codes_below_medicare"] += 1
                    is_below = True
                    # Flag if more than 10% below Medicare
                    if variance_pct < -10:
                        results["red_flags"].append({
                            "code": code,
                            "description": medicare_data["description"] or description,
                            "contracted_rate": contracted_rate,
                            "medicare_rate": medicare_rate,
                            "variance": variance,
                            "variance_pct": round(variance_pct, 2)
                        })
                elif variance > 0:
                    results["codes_above_medicare"] += 1
                    is_below = False
                else:
                    results["codes_equal"] += 1
                    is_below = False

                results["total_variance"] += variance

                # Calculate revenue impact if volume provided
                revenue_impact = None
                if volume:
                    revenue_impact = variance * volume
                    results["total_revenue_impact"] += revenue_impact

                results["line_items"].append({
                    "code": code,
                    "description": medicare_data["description"] or description,
                    "contracted_rate": contracted_rate,
                    "medicare_rate": medicare_rate,
                    "variance": round(variance, 2),
                    "variance_pct": round(variance_pct, 2),
                    "is_below_medicare": is_below,
                    "volume": volume,
                    "revenue_impact": round(revenue_impact, 2) if revenue_impact else None
                })
            else:
                results["codes_unmatched"] += 1
                results["line_items"].append({
                    "code": code,
                    "description": description,
                    "contracted_rate": contracted_rate,
                    "medicare_rate": None,
                    "variance": None,
                    "variance_pct": None,
                    "is_below_medicare": None,
                    "volume": volume,
                    "revenue_impact": None,
                    "error": "Code not found in Medicare fee schedule"
                })

        results["total_variance"] = round(results["total_variance"], 2)
        results["total_revenue_impact"] = round(results["total_revenue_impact"], 2)

        return results


def get_fee_schedule_service(db: Session) -> FeeScheduleService:
    """Factory function to get FeeScheduleService instance."""
    return FeeScheduleService(db)
