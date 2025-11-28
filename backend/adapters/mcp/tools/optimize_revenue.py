"""
Optimize Revenue MCP Tool

Analyzes clinical documentation for revenue optimization opportunities.
Focuses on accurate capture of documented conditions - not upcoding.
"""

from typing import Any
from mcp.types import Tool

from domain.entity_extraction import ClinicalEntityExtractor
from domain.revenue_optimization import RevenueOptimizer

OPTIMIZE_REVENUE_TOOL = Tool(
    name="optimize_revenue",
    description="""Analyzes clinical documentation for revenue optimization opportunities.

Identifies:
- Under-coded conditions with supporting documentation
- Severity/acuity opportunities (e.g., acute vs chronic)
- HCC risk adjustment opportunities for Medicare Advantage
- E/M coding recommendations based on MDM complexity
- Missing charges for documented procedures

Does NOT promote upcoding - focuses on accurate capture of documented clinical conditions.
All recommendations are based on documentation present in the note.""",
    inputSchema={
        "type": "object",
        "properties": {
            "note_text": {
                "type": "string",
                "description": "Clinical note to analyze"
            },
            "setting": {
                "type": "string",
                "description": "Clinical setting",
                "enum": ["outpatient", "inpatient", "emergency"],
                "default": "outpatient"
            },
            "patient_type": {
                "type": "string",
                "description": "Patient type for E/M coding",
                "enum": ["new", "established"],
                "default": "established"
            },
            "include_em_coding": {
                "type": "boolean",
                "description": "Include E/M coding analysis",
                "default": True
            },
            "include_hcc": {
                "type": "boolean",
                "description": "Include HCC risk adjustment analysis",
                "default": True
            }
        },
        "required": ["note_text"]
    }
)


async def handle_optimize_revenue(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Handle the optimize_revenue tool call.

    Args:
        arguments: Tool arguments containing note_text and options

    Returns:
        Revenue optimization opportunities with estimated impact
    """
    note_text = arguments.get("note_text", "")
    setting = arguments.get("setting", "outpatient")
    patient_type = arguments.get("patient_type", "established")
    include_em_coding = arguments.get("include_em_coding", True)
    include_hcc = arguments.get("include_hcc", True)

    if not note_text.strip():
        return {"error": "note_text is required and cannot be empty"}

    # Extract clinical entities
    extractor = ClinicalEntityExtractor()
    entities = extractor.extract(note_text)

    # Run revenue optimization
    optimizer = RevenueOptimizer()
    result = optimizer.analyze(
        clinical_note=note_text,
        entities=entities,
        setting=setting,
        patient_type=patient_type
    )

    # Build response
    response = {
        "success": True,
        "analysis_summary": {
            "diagnoses_found": len(entities.diagnoses),
            "total_revenue_opportunity": result.total_revenue_opportunity,
            "confidence": result.confidence
        }
    }

    # E/M Coding Analysis
    if include_em_coding and result.em_recommendation:
        em = result.em_recommendation
        response["em_coding"] = {
            "recommended_code": em.recommended_code,
            "mdm_level": em.documented_level,
            "supporting_factors": [],
            "documentation_gaps": em.documentation_gaps,
            "estimated_reimbursement": em.reimbursement,
            "confidence": em.confidence
        }

        # Add E/M guidelines context
        em_context = _get_em_guidelines_context(setting, patient_type, em.recommended_code)
        if em_context:
            response["em_coding"]["guidelines_context"] = em_context

    # HCC Analysis
    if include_hcc and result.hcc_opportunities:
        hcc_list = []
        for hcc_desc in result.hcc_opportunities:
            hcc_list.append({
                "description": hcc_desc,
                "potential_impact": result.hcc_revenue_opportunity / max(len(result.hcc_opportunities), 1),
                "documentation_evidence": result.condition or ""
            })
        response["hcc_opportunities"] = hcc_list
        response["hcc_total_impact"] = result.hcc_revenue_opportunity

    # DRG Optimization (for inpatient)
    if setting == "inpatient" and result.drg_optimization:
        drg = result.drg_optimization
        response["drg_optimization"] = {
            "current_drg": drg.current_drg,
            "potential_drg": drg.potential_drg,
            "revenue_impact": drg.revenue_impact,
            "documentation_needed": drg.documentation_improvements
        }

    # Missing Charges
    if result.tests_missing:
        missing_charges = []
        for test in result.tests_missing:
            missing_charges.append({
                "item": test.get("test", "Unknown"),
                "cpt_code": test.get("cpt"),
                "reason": test.get("reason", ""),
                "estimated_value": test.get("value", 0)
            })
        response["missing_charges"] = missing_charges

    # Compliance note
    response["compliance_note"] = (
        "All recommendations are based solely on clinical documentation present in the note. "
        "Coding should reflect the documented clinical picture. Do not code conditions that "
        "are not clearly supported by documentation."
    )

    return response


def _get_em_guidelines_context(setting: str, patient_type: str, code: str) -> dict[str, Any]:
    """Get E/M guidelines context for the recommended code."""
    em_guidelines = {
        "outpatient": {
            "established": {
                "99212": {"mdm": "Straightforward", "time": 10},
                "99213": {"mdm": "Low", "time": 20},
                "99214": {"mdm": "Moderate", "time": 30},
                "99215": {"mdm": "High", "time": 40},
            },
            "new": {
                "99202": {"mdm": "Straightforward", "time": 15},
                "99203": {"mdm": "Low", "time": 30},
                "99204": {"mdm": "Moderate", "time": 45},
                "99205": {"mdm": "High", "time": 60},
            }
        },
        "inpatient": {
            "established": {
                "99231": {"mdm": "Low", "time": 25},
                "99232": {"mdm": "Moderate", "time": 35},
                "99233": {"mdm": "High", "time": 50},
            },
            "new": {
                "99221": {"mdm": "Low", "time": 40},
                "99222": {"mdm": "Moderate", "time": 55},
                "99223": {"mdm": "High", "time": 75},
            }
        }
    }

    try:
        codes = em_guidelines.get(setting, {}).get(patient_type, {})
        if code in codes:
            return {
                "mdm_requirement": codes[code]["mdm"],
                "time_threshold": codes[code]["time"],
                "note": f"MDM-based: {codes[code]['mdm']} complexity OR Time-based: {codes[code]['time']}+ minutes"
            }
    except Exception:
        pass

    return None
