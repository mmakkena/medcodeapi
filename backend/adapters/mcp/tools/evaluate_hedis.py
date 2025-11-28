"""
Evaluate HEDIS MCP Tool

Evaluates clinical documentation against HEDIS quality measures.
Supports 19 measures including CBP, CDC, BCS, COL, BMI, DEP, and more.
"""

from typing import Any
from mcp.types import Tool

from domain.entity_extraction import ClinicalEntityExtractor
from domain.hedis_evaluation import HEDISEvaluator, check_hedis_exclusions

EVALUATE_HEDIS_TOOL = Tool(
    name="evaluate_hedis",
    description="""Evaluates clinical documentation against HEDIS quality measures.

Supports measures including:
- CBP: Controlling High Blood Pressure
- CDC: Comprehensive Diabetes Care (HbA1c, Eye Exam, Nephropathy)
- BCS: Breast Cancer Screening
- CCS: Cervical Cancer Screening
- COL: Colorectal Cancer Screening
- BMI: Adult BMI Assessment
- DEP: Depression Screening and Follow-up
- SPR: Statin Therapy for CVD

Returns compliance status, gaps, and recommendations for each applicable measure.
Automatically checks for exclusion criteria (hospice, ESRD, etc.).""",
    inputSchema={
        "type": "object",
        "properties": {
            "note_text": {
                "type": "string",
                "description": "Clinical note to evaluate"
            },
            "patient_age": {
                "type": "integer",
                "description": "Patient age in years"
            },
            "patient_gender": {
                "type": "string",
                "description": "Patient gender",
                "enum": ["male", "female"]
            },
            "measures": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific measures to evaluate (optional, evaluates all if not specified)"
            },
            "include_exclusions": {
                "type": "boolean",
                "description": "Check for exclusion criteria",
                "default": True
            }
        },
        "required": ["note_text", "patient_age", "patient_gender"]
    }
)


async def handle_evaluate_hedis(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Handle the evaluate_hedis tool call.

    Args:
        arguments: Tool arguments containing note_text and patient info

    Returns:
        HEDIS measure evaluation results with compliance status and gaps
    """
    note_text = arguments.get("note_text", "")
    patient_age = arguments.get("patient_age")
    patient_gender = arguments.get("patient_gender", "").lower()
    measures = arguments.get("measures", [])
    include_exclusions = arguments.get("include_exclusions", True)

    if not note_text.strip():
        return {"error": "note_text is required and cannot be empty"}
    if patient_age is None:
        return {"error": "patient_age is required"}
    if not patient_gender:
        return {"error": "patient_gender is required"}

    # Extract clinical entities
    extractor = ClinicalEntityExtractor()
    entities = extractor.extract(note_text)

    # Convert entities to format expected by evaluator
    diagnoses_list = [d.name for d in entities.diagnoses]

    vitals_dict = {}
    if entities.vitals:
        if entities.vitals.systolic and entities.vitals.diastolic:
            vitals_dict["BP"] = f"{entities.vitals.systolic}/{entities.vitals.diastolic}"
        if entities.vitals.bmi:
            vitals_dict["BMI"] = entities.vitals.bmi

    labs_dict = {}
    if entities.labs:
        if entities.labs.hba1c:
            labs_dict["HbA1c"] = f"{entities.labs.hba1c}%"
        if entities.labs.ldl:
            labs_dict["LDL"] = str(entities.labs.ldl)

    screenings_dict = {}
    if entities.screenings:
        if entities.screenings.mammogram:
            screenings_dict["Mammogram"] = True
        if entities.screenings.colonoscopy:
            screenings_dict["Colorectal"] = True
        if entities.screenings.cervical_cancer:
            screenings_dict["Cervical"] = True
        if entities.screenings.diabetic_eye:
            screenings_dict["Eye Exam"] = True

    # Check exclusions
    exclusions = []
    if include_exclusions:
        exclusion_result = check_hedis_exclusions(
            diagnoses=diagnoses_list,
            note_text=note_text
        )
        for excl_type, excl_info in exclusion_result.items():
            if excl_info.get("present"):
                exclusions.append({
                    "type": excl_type,
                    "reason": excl_info.get("reason"),
                    "description": excl_info.get("description"),
                    "affects_measures": excl_info.get("affects", [])
                })

    excluded_measure_ids = set()
    for excl in exclusions:
        excluded_measure_ids.update(excl.get("affects_measures", []))

    # Evaluate HEDIS measures
    evaluator = HEDISEvaluator()
    evaluation_result = evaluator.evaluate(
        diagnoses=diagnoses_list,
        vitals=vitals_dict,
        labs=labs_dict,
        screenings=screenings_dict,
        patient_age=patient_age,
        patient_gender=patient_gender,
        medications=[m.name for m in entities.medications],
        note_text=note_text
    )

    # Format results
    measure_results = []
    status_counts = {"met": 0, "not_met": 0, "excluded": 0, "not_applicable": 0}
    all_gaps = []

    # evaluation_result.measures is a dict with measure_code as keys
    for measure_code, measure in evaluation_result.measures.items():
        # Filter to requested measures if specified
        if measures and measure_code not in measures:
            continue

        # Determine status
        if measure_code in excluded_measure_ids:
            status = "excluded"
            status_counts["excluded"] += 1
        elif measure.meets_target:
            status = "met"
            status_counts["met"] += 1
        elif not measure.applicable:
            status = "not_applicable"
            status_counts["not_applicable"] += 1
        else:
            status = "not_met"
            status_counts["not_met"] += 1
            if measure.gap_description:
                all_gaps.append(measure.gap_description)

        measure_results.append({
            "measure_id": measure_code,
            "measure_name": measure.measure_name,
            "status": status,
            "value": measure.value,
            "target": measure.target,
            "is_compliant": measure.meets_target if measure.meets_target is not None else False,
            "gaps": [measure.gap_description] if measure.gap_description else [],
            "recommendations": [],
            "evidence_text": measure.raw_value,
            "confidence": 0.9 if measure.documented else 0.5
        })

    # Calculate compliance rate
    applicable_count = status_counts["met"] + status_counts["not_met"]
    compliance_rate = status_counts["met"] / applicable_count if applicable_count > 0 else 0.0

    return {
        "success": True,
        "patient_info": {
            "age": patient_age,
            "gender": patient_gender
        },
        "measures": measure_results,
        "exclusions": exclusions,
        "summary": {
            "total_evaluated": len(measure_results),
            "met": status_counts["met"],
            "not_met": status_counts["not_met"],
            "excluded": status_counts["excluded"],
            "compliance_rate": round(compliance_rate * 100, 1)
        },
        "gaps_summary": {
            "total_gaps": len(all_gaps),
            "gaps": all_gaps[:10]  # Top 10 gaps
        },
        "interpretation": _get_compliance_interpretation(compliance_rate, status_counts)
    }


def _get_compliance_interpretation(compliance_rate: float, status_counts: dict) -> str:
    """Generate interpretation of HEDIS compliance results."""
    if compliance_rate >= 0.9:
        return "Excellent HEDIS compliance. Documentation supports quality measure requirements."
    elif compliance_rate >= 0.7:
        return "Good HEDIS compliance with some gaps. Address noted gaps to improve quality scores."
    elif compliance_rate >= 0.5:
        return "Moderate HEDIS compliance. Multiple gaps identified that may affect quality ratings."
    else:
        return "Significant HEDIS gaps identified. Review documentation and care gaps for improvement."
