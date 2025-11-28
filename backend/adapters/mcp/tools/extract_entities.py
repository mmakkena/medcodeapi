"""
Extract Entities MCP Tool

Extracts medical entities from clinical text.
Returns structured data for diagnoses, medications, labs, vitals, and more.
"""

from typing import Any
from mcp.types import Tool

from domain.entity_extraction import ClinicalEntityExtractor

EXTRACT_ENTITIES_TOOL = Tool(
    name="extract_entities",
    description="""Extracts medical entities from clinical text.

Extracts:
- diagnoses: Medical conditions and diseases with ICD-10 codes
- symptoms: Patient-reported or observed symptoms
- medications: Current and historical medications with dosages
- labs: Laboratory test results (HbA1c, glucose, creatinine, etc.)
- vitals: Vital sign measurements (BP, HR, temp, BMI, etc.)
- procedures: Performed or planned procedures
- screenings: Preventive health screenings
- social_determinants: Social factors affecting health (smoking, alcohol, etc.)

Use this tool for structured entity extraction before further analysis.""",
    inputSchema={
        "type": "object",
        "properties": {
            "note_text": {
                "type": "string",
                "description": "Clinical text to extract entities from"
            },
            "entity_types": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["diagnoses", "medications", "labs", "vitals", "procedures", "symptoms", "screenings", "social"]
                },
                "description": "Specific entity types to extract (optional, extracts all if not specified)"
            }
        },
        "required": ["note_text"]
    }
)


async def handle_extract_entities(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Handle the extract_entities tool call.

    Args:
        arguments: Tool arguments containing note_text and optional filters

    Returns:
        Extracted entities in structured format
    """
    note_text = arguments.get("note_text", "")
    entity_types = arguments.get("entity_types", [])

    if not note_text.strip():
        return {"error": "note_text is required and cannot be empty"}

    # Extract all entities
    extractor = ClinicalEntityExtractor()
    entities = extractor.extract(note_text)

    # Build response based on requested entity types
    result = {"success": True}
    all_types = not entity_types  # If no types specified, return all

    # Diagnoses
    if all_types or "diagnoses" in entity_types:
        result["diagnoses"] = [
            {
                "name": d.name,
                "icd10_code": d.icd10_code,
                "confidence": d.confidence,
                "context": d.context if hasattr(d, 'context') else None
            }
            for d in entities.diagnoses
        ]

    # Medications
    if all_types or "medications" in entity_types:
        result["medications"] = [
            {
                "name": m.name,
                "dose": m.dose,
                "frequency": m.frequency,
                "route": m.route if hasattr(m, 'route') else None,
                "drug_class": m.drug_class if hasattr(m, 'drug_class') else None
            }
            for m in entities.medications
        ]

    # Labs
    if all_types or "labs" in entity_types:
        labs_dict = {}
        if entities.labs:
            if entities.labs.hba1c:
                labs_dict["HbA1c"] = {
                    "value": entities.labs.hba1c,
                    "unit": "%",
                    "interpretation": _interpret_hba1c(entities.labs.hba1c)
                }
            if entities.labs.glucose:
                labs_dict["Glucose"] = {
                    "value": entities.labs.glucose,
                    "unit": "mg/dL",
                    "interpretation": _interpret_glucose(entities.labs.glucose)
                }
            if entities.labs.ldl:
                labs_dict["LDL"] = {
                    "value": entities.labs.ldl,
                    "unit": "mg/dL",
                    "interpretation": _interpret_ldl(entities.labs.ldl)
                }
            if entities.labs.creatinine:
                labs_dict["Creatinine"] = {
                    "value": entities.labs.creatinine,
                    "unit": "mg/dL"
                }
            if entities.labs.egfr:
                labs_dict["eGFR"] = {
                    "value": entities.labs.egfr,
                    "unit": "mL/min/1.73m2",
                    "interpretation": _interpret_egfr(entities.labs.egfr)
                }
            if entities.labs.potassium:
                labs_dict["Potassium"] = {
                    "value": entities.labs.potassium,
                    "unit": "mEq/L"
                }
            if entities.labs.sodium:
                labs_dict["Sodium"] = {
                    "value": entities.labs.sodium,
                    "unit": "mEq/L"
                }
            if entities.labs.hemoglobin:
                labs_dict["Hemoglobin"] = {
                    "value": entities.labs.hemoglobin,
                    "unit": "g/dL"
                }
            if entities.labs.wbc:
                labs_dict["WBC"] = {
                    "value": entities.labs.wbc,
                    "unit": "K/uL"
                }
            if entities.labs.platelets:
                labs_dict["Platelets"] = {
                    "value": entities.labs.platelets,
                    "unit": "K/uL"
                }
        result["labs"] = labs_dict

    # Vitals
    if all_types or "vitals" in entity_types:
        vitals_dict = {}
        if entities.vitals:
            if entities.vitals.systolic and entities.vitals.diastolic:
                vitals_dict["blood_pressure"] = {
                    "systolic": entities.vitals.systolic,
                    "diastolic": entities.vitals.diastolic,
                    "interpretation": _interpret_bp(entities.vitals.systolic, entities.vitals.diastolic)
                }
            if entities.vitals.heart_rate:
                vitals_dict["heart_rate"] = {
                    "value": entities.vitals.heart_rate,
                    "unit": "bpm"
                }
            if entities.vitals.temperature:
                vitals_dict["temperature"] = {
                    "value": entities.vitals.temperature,
                    "unit": "F"
                }
            if entities.vitals.respiratory_rate:
                vitals_dict["respiratory_rate"] = {
                    "value": entities.vitals.respiratory_rate,
                    "unit": "breaths/min"
                }
            if entities.vitals.spo2:
                vitals_dict["oxygen_saturation"] = {
                    "value": entities.vitals.spo2,
                    "unit": "%"
                }
            if entities.vitals.bmi:
                vitals_dict["bmi"] = {
                    "value": entities.vitals.bmi,
                    "interpretation": _interpret_bmi(entities.vitals.bmi)
                }
            if entities.vitals.weight:
                vitals_dict["weight"] = {
                    "value": entities.vitals.weight,
                    "unit": "kg" if entities.vitals.weight < 200 else "lbs"
                }
            if entities.vitals.height:
                vitals_dict["height"] = {
                    "value": entities.vitals.height,
                    "unit": "cm"
                }
        result["vitals"] = vitals_dict

    # Procedures
    if all_types or "procedures" in entity_types:
        result["procedures"] = [
            {
                "name": p.name,
                "cpt_code": p.cpt_code if hasattr(p, 'cpt_code') else None,
                "date": p.date if hasattr(p, 'date') else None
            }
            for p in (entities.procedures or [])
        ]

    # Symptoms (not currently extracted - placeholder for future)
    if all_types or "symptoms" in entity_types:
        result["symptoms"] = getattr(entities, 'symptoms', []) or []

    # Screenings
    if all_types or "screenings" in entity_types:
        screenings_dict = {}
        if entities.screenings:
            if entities.screenings.mammogram:
                screenings_dict["mammogram"] = entities.screenings.mammogram
            if entities.screenings.colonoscopy:
                screenings_dict["colonoscopy"] = entities.screenings.colonoscopy
            if entities.screenings.cervical_cancer:
                screenings_dict["cervical_cancer"] = entities.screenings.cervical_cancer
            if entities.screenings.diabetic_eye:
                screenings_dict["eye_exam"] = entities.screenings.diabetic_eye
            if entities.screenings.diabetic_foot:
                screenings_dict["foot_exam"] = entities.screenings.diabetic_foot
            if entities.screenings.depression_screening:
                screenings_dict["depression"] = entities.screenings.depression_screening
            if entities.screenings.fit_test:
                screenings_dict["fit_test"] = entities.screenings.fit_test
            if entities.screenings.lung_cancer:
                screenings_dict["lung_cancer"] = entities.screenings.lung_cancer
        result["screenings"] = screenings_dict

    # Social determinants (extracted from demographics if available)
    if all_types or "social" in entity_types:
        social_dict = {}
        social_history = getattr(entities, 'social_history', None)
        if social_history:
            if getattr(social_history, 'smoking_status', None):
                social_dict["smoking_status"] = social_history.smoking_status
            if getattr(social_history, 'alcohol_use', None):
                social_dict["alcohol_use"] = social_history.alcohol_use
            if getattr(social_history, 'drug_use', None):
                social_dict["drug_use"] = social_history.drug_use
            if getattr(social_history, 'occupation', None):
                social_dict["occupation"] = social_history.occupation
        result["social_determinants"] = social_dict

    # Summary
    result["summary"] = {
        "diagnoses_count": len(entities.diagnoses),
        "medications_count": len(entities.medications),
        "labs_found": len(result.get("labs", {})),
        "vitals_found": len(result.get("vitals", {})),
        "procedures_count": len(entities.procedures or [])
    }

    return result


def _interpret_hba1c(value: float) -> str:
    """Interpret HbA1c value."""
    if value < 5.7:
        return "Normal"
    elif value < 6.5:
        return "Prediabetes"
    elif value < 7.0:
        return "Diabetes - Well controlled"
    elif value < 8.0:
        return "Diabetes - Moderate control"
    elif value < 9.0:
        return "Diabetes - Poor control"
    else:
        return "Diabetes - Very poor control"


def _interpret_glucose(value: float) -> str:
    """Interpret fasting glucose value."""
    if value < 100:
        return "Normal"
    elif value < 126:
        return "Prediabetes (impaired fasting glucose)"
    else:
        return "Diabetes range"


def _interpret_ldl(value: float) -> str:
    """Interpret LDL cholesterol value."""
    if value < 70:
        return "Optimal (high-risk patients)"
    elif value < 100:
        return "Optimal"
    elif value < 130:
        return "Near optimal"
    elif value < 160:
        return "Borderline high"
    elif value < 190:
        return "High"
    else:
        return "Very high"


def _interpret_egfr(value: float) -> str:
    """Interpret eGFR value (CKD staging)."""
    if value >= 90:
        return "Normal or high (G1)"
    elif value >= 60:
        return "Mildly decreased (G2)"
    elif value >= 45:
        return "Mild-moderately decreased (G3a)"
    elif value >= 30:
        return "Moderately-severely decreased (G3b)"
    elif value >= 15:
        return "Severely decreased (G4)"
    else:
        return "Kidney failure (G5)"


def _interpret_bp(systolic: int, diastolic: int) -> str:
    """Interpret blood pressure."""
    if systolic < 120 and diastolic < 80:
        return "Normal"
    elif systolic < 130 and diastolic < 80:
        return "Elevated"
    elif systolic < 140 or diastolic < 90:
        return "Stage 1 Hypertension"
    elif systolic >= 140 or diastolic >= 90:
        return "Stage 2 Hypertension"
    else:
        return "Unknown"


def _interpret_bmi(value: float) -> str:
    """Interpret BMI value."""
    if value < 18.5:
        return "Underweight"
    elif value < 25:
        return "Normal weight"
    elif value < 30:
        return "Overweight"
    elif value < 35:
        return "Obesity Class I"
    elif value < 40:
        return "Obesity Class II"
    else:
        return "Obesity Class III (Severe)"
