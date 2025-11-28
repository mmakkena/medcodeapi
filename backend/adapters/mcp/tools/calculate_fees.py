"""
Calculate Fees MCP Tool

Calculates Medicare reimbursement for procedure codes.
Uses CMS Medicare Physician Fee Schedule with locality-specific rates.
"""

from typing import Any
from mcp.types import Tool

from infrastructure.db.postgres import get_db_sync
from infrastructure.db.repositories.fee_repository import FeeRepository

CALCULATE_FEES_TOOL = Tool(
    name="calculate_fees",
    description="""Calculates Medicare reimbursement for procedure codes.

Uses CMS Medicare Physician Fee Schedule with locality-specific rates.
Returns pricing breakdown including:
- Work, Practice Expense, and Malpractice RVUs
- Geographic Practice Cost Indices (GPCIs)
- Facility vs Non-Facility rates
- Conversion factor applied

Use this tool to estimate reimbursement for procedures or compare facility/non-facility pricing.""",
    inputSchema={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "CPT or HCPCS code"
            },
            "zip_code": {
                "type": "string",
                "description": "ZIP code for locality-specific pricing (e.g., '10001')"
            },
            "year": {
                "type": "integer",
                "description": "Fee schedule year (2024 or 2025)",
                "default": 2025
            },
            "facility": {
                "type": "boolean",
                "description": "Whether to use facility rate (hospital) or non-facility rate (office)",
                "default": False
            }
        },
        "required": ["code", "zip_code"]
    }
)


async def handle_calculate_fees(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Handle the calculate_fees tool call.

    Args:
        arguments: Tool arguments containing code, zip_code, and options

    Returns:
        Fee calculation with RVU breakdown and reimbursement amount
    """
    code = arguments.get("code", "").strip().upper()
    zip_code = arguments.get("zip_code", "").strip()
    year = arguments.get("year", 2025)
    facility = arguments.get("facility", False)

    if not code:
        return {"error": "code is required"}
    if not zip_code:
        return {"error": "zip_code is required"}

    try:
        # Get database session
        db = next(get_db_sync())
        repo = FeeRepository(db)

        # Look up fee schedule data
        fee_data = repo.get_fee_by_code_and_locality(
            code=code,
            zip_code=zip_code,
            year=year
        )

        if not fee_data:
            return {
                "success": False,
                "error": f"No fee data found for code {code} in ZIP {zip_code} for year {year}",
                "suggestions": [
                    "Verify the CPT/HCPCS code is valid",
                    "Try a different ZIP code",
                    "Check if the code is covered by Medicare"
                ]
            }

        # Calculate total reimbursement
        if facility:
            pe_rvu = fee_data.facility_pe_rvu
            total_rvu = fee_data.work_rvu + pe_rvu + fee_data.mp_rvu
            rate_type = "Facility"
        else:
            pe_rvu = fee_data.non_facility_pe_rvu
            total_rvu = fee_data.work_rvu + pe_rvu + fee_data.mp_rvu
            rate_type = "Non-Facility"

        # Apply GPCIs and conversion factor
        adjusted_rvu = (
            (fee_data.work_rvu * fee_data.work_gpci) +
            (pe_rvu * fee_data.pe_gpci) +
            (fee_data.mp_rvu * fee_data.mp_gpci)
        )

        reimbursement = adjusted_rvu * fee_data.conversion_factor

        return {
            "success": True,
            "code": code,
            "description": fee_data.description if hasattr(fee_data, 'description') else None,
            "year": year,
            "locality": {
                "zip_code": zip_code,
                "locality_name": fee_data.locality_name if hasattr(fee_data, 'locality_name') else None,
                "mac": fee_data.mac if hasattr(fee_data, 'mac') else None
            },
            "rvu_breakdown": {
                "work_rvu": round(fee_data.work_rvu, 4),
                "pe_rvu": round(pe_rvu, 4),
                "mp_rvu": round(fee_data.mp_rvu, 4),
                "total_rvu": round(total_rvu, 4)
            },
            "gpci": {
                "work_gpci": round(fee_data.work_gpci, 4),
                "pe_gpci": round(fee_data.pe_gpci, 4),
                "mp_gpci": round(fee_data.mp_gpci, 4)
            },
            "calculation": {
                "rate_type": rate_type,
                "adjusted_rvu": round(adjusted_rvu, 4),
                "conversion_factor": fee_data.conversion_factor,
                "reimbursement": round(reimbursement, 2)
            },
            "comparison": {
                "facility_rate": round(
                    ((fee_data.work_rvu * fee_data.work_gpci) +
                     (fee_data.facility_pe_rvu * fee_data.pe_gpci) +
                     (fee_data.mp_rvu * fee_data.mp_gpci)) * fee_data.conversion_factor, 2
                ),
                "non_facility_rate": round(
                    ((fee_data.work_rvu * fee_data.work_gpci) +
                     (fee_data.non_facility_pe_rvu * fee_data.pe_gpci) +
                     (fee_data.mp_rvu * fee_data.mp_gpci)) * fee_data.conversion_factor, 2
                )
            }
        }

    except Exception as e:
        # Fallback with estimated values
        return await _fallback_fee_calculation(code, zip_code, year, facility)
    finally:
        if 'db' in locals():
            db.close()


async def _fallback_fee_calculation(
    code: str,
    zip_code: str,
    year: int,
    facility: bool
) -> dict[str, Any]:
    """
    Fallback fee calculation with common codes.

    Used when database is unavailable.
    """
    # Common E/M codes with approximate values (2025)
    common_fees = {
        "99213": {"work": 0.97, "pe_nf": 1.14, "pe_f": 0.59, "mp": 0.07, "desc": "Office visit, established, low complexity"},
        "99214": {"work": 1.50, "pe_nf": 1.66, "pe_f": 0.84, "mp": 0.10, "desc": "Office visit, established, moderate complexity"},
        "99215": {"work": 2.11, "pe_nf": 2.05, "pe_f": 1.07, "mp": 0.14, "desc": "Office visit, established, high complexity"},
        "99203": {"work": 1.60, "pe_nf": 1.72, "pe_f": 0.92, "mp": 0.11, "desc": "Office visit, new patient, low complexity"},
        "99204": {"work": 2.60, "pe_nf": 2.40, "pe_f": 1.30, "mp": 0.17, "desc": "Office visit, new patient, moderate complexity"},
        "99205": {"work": 3.50, "pe_nf": 2.98, "pe_f": 1.64, "mp": 0.23, "desc": "Office visit, new patient, high complexity"},
    }

    if code not in common_fees:
        return {
            "success": False,
            "error": f"Code {code} not found in fallback data",
            "note": "Database connection unavailable - only common E/M codes available"
        }

    fee_info = common_fees[code]
    conversion_factor = 32.74  # 2025 CMS conversion factor

    pe_rvu = fee_info["pe_f"] if facility else fee_info["pe_nf"]
    total_rvu = fee_info["work"] + pe_rvu + fee_info["mp"]
    reimbursement = total_rvu * conversion_factor

    return {
        "success": True,
        "code": code,
        "description": fee_info["desc"],
        "year": year,
        "locality": {
            "zip_code": zip_code,
            "locality_name": "National Average (Fallback)",
            "mac": None
        },
        "rvu_breakdown": {
            "work_rvu": fee_info["work"],
            "pe_rvu": pe_rvu,
            "mp_rvu": fee_info["mp"],
            "total_rvu": round(total_rvu, 4)
        },
        "calculation": {
            "rate_type": "Facility" if facility else "Non-Facility",
            "conversion_factor": conversion_factor,
            "reimbursement": round(reimbursement, 2)
        },
        "note": "Using national average values - database connection unavailable"
    }
