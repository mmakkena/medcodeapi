"""
Analyze Note MCP Tool

Comprehensive clinical documentation analysis including:
- Clinical entity extraction
- Documentation gap detection
- Code suggestions
- Compliance risks
"""

from typing import Any
from mcp.types import Tool

from domain.entity_extraction import ClinicalEntityExtractor
from domain.documentation_gaps import DocumentationGapAnalyzer
from domain.query_generation import CDIQueryGenerator

ANALYZE_NOTE_TOOL = Tool(
    name="analyze_note",
    description="""Analyzes clinical documentation and returns:
- findings: Key clinical findings extracted from the note
- missing_elements: Documentation gaps that need attention
- entities: Extracted clinical entities (diagnoses, medications, labs, vitals, etc.)
- queries: Suggested CDI queries to improve documentation
- documentation_risks: Compliance and coding risks identified

Use this tool for comprehensive clinical note analysis before coding or query generation.""",
    inputSchema={
        "type": "object",
        "properties": {
            "note_text": {
                "type": "string",
                "description": "The clinical note text to analyze"
            },
            "include_queries": {
                "type": "boolean",
                "description": "Whether to generate CDI queries for gaps",
                "default": True
            }
        },
        "required": ["note_text"]
    }
)


async def handle_analyze_note(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Handle the analyze_note tool call.

    Args:
        arguments: Tool arguments containing note_text

    Returns:
        Analysis results including findings, gaps, entities, and queries
    """
    note_text = arguments.get("note_text", "")
    include_queries = arguments.get("include_queries", True)

    if not note_text.strip():
        return {"error": "note_text is required and cannot be empty"}

    # Extract clinical entities
    extractor = ClinicalEntityExtractor()
    entities = extractor.extract(note_text)

    # Analyze documentation gaps
    gap_analyzer = DocumentationGapAnalyzer()
    gap_result = gap_analyzer.analyze(entities=entities)

    # Build entities response
    entities_dict = {
        "diagnoses": [
            {"name": d.name, "icd10_code": d.icd10_code, "confidence": d.confidence}
            for d in entities.diagnoses
        ],
        "medications": [
            {"name": m.name, "dose": m.dose, "frequency": m.frequency}
            for m in entities.medications
        ],
        "labs": {},
        "vitals": {},
        "screenings": {},
        "procedures": [p.name for p in entities.procedures] if entities.procedures else [],
        "symptoms": getattr(entities, 'symptoms', []) or []
    }

    # Add lab values if present
    if entities.labs:
        if entities.labs.hba1c:
            entities_dict["labs"]["HbA1c"] = f"{entities.labs.hba1c}%"
        if entities.labs.ldl:
            entities_dict["labs"]["LDL"] = entities.labs.ldl
        if entities.labs.glucose:
            entities_dict["labs"]["Glucose"] = entities.labs.glucose
        if entities.labs.creatinine:
            entities_dict["labs"]["Creatinine"] = entities.labs.creatinine
        if entities.labs.egfr:
            entities_dict["labs"]["eGFR"] = entities.labs.egfr

    # Add vitals if present
    if entities.vitals:
        if entities.vitals.systolic and entities.vitals.diastolic:
            entities_dict["vitals"]["BP"] = f"{entities.vitals.systolic}/{entities.vitals.diastolic}"
        if entities.vitals.heart_rate:
            entities_dict["vitals"]["HR"] = entities.vitals.heart_rate
        if entities.vitals.temperature:
            entities_dict["vitals"]["Temp"] = entities.vitals.temperature
        if entities.vitals.respiratory_rate:
            entities_dict["vitals"]["RR"] = entities.vitals.respiratory_rate
        if entities.vitals.spo2:
            entities_dict["vitals"]["SpO2"] = f"{entities.vitals.spo2}%"
        if entities.vitals.bmi:
            entities_dict["vitals"]["BMI"] = entities.vitals.bmi

    # Add screenings if present
    if entities.screenings:
        if entities.screenings.mammogram:
            entities_dict["screenings"]["Mammogram"] = entities.screenings.mammogram
        if entities.screenings.colonoscopy:
            entities_dict["screenings"]["Colonoscopy"] = entities.screenings.colonoscopy
        if entities.screenings.cervical_cancer:
            entities_dict["screenings"]["Cervical Cancer"] = entities.screenings.cervical_cancer
        if entities.screenings.diabetic_eye:
            entities_dict["screenings"]["Eye Exam"] = entities.screenings.diabetic_eye

    # Build gaps response
    gaps_list = []
    if hasattr(gap_result, 'gaps'):
        for gap in gap_result.gaps:
            gaps_list.append({
                "category": gap.category if hasattr(gap, 'category') else "unknown",
                "description": gap.description if hasattr(gap, 'description') else str(gap),
                "priority": gap.priority if hasattr(gap, 'priority') else "medium",
                "recommendation": gap.recommendation if hasattr(gap, 'recommendation') else None
            })

    # Generate queries if requested
    queries_list = []
    if include_queries and gaps_list:
        query_generator = CDIQueryGenerator()
        query_result = query_generator.generate_from_gaps(gap_result)
        if hasattr(query_result, 'queries'):
            for query in query_result.queries:
                queries_list.append({
                    "query_text": query.query_text if hasattr(query, 'query_text') else str(query),
                    "query_type": query.query_type if hasattr(query, 'query_type') else "clarification",
                    "priority": query.priority if hasattr(query, 'priority') else "medium",
                    "target_condition": query.target_condition if hasattr(query, 'target_condition') else None
                })

    # Identify key findings
    findings = []
    for dx in entities.diagnoses[:5]:  # Top 5 diagnoses
        findings.append(f"Diagnosis: {dx.name}")
    if entities.vitals and entities.vitals.systolic:
        findings.append(f"Blood Pressure: {entities.vitals.systolic}/{entities.vitals.diastolic}")
    if entities.labs and entities.labs.hba1c:
        findings.append(f"HbA1c: {entities.labs.hba1c}%")

    # Identify documentation risks
    risks = []
    if len(gaps_list) > 3:
        risks.append("Multiple documentation gaps may affect coding accuracy")
    if any("specificity" in g.get("category", "").lower() for g in gaps_list):
        risks.append("Lack of diagnostic specificity may result in undercoding")
    if any("acuity" in g.get("category", "").lower() for g in gaps_list):
        risks.append("Missing acuity indicators could affect severity capture")

    return {
        "success": True,
        "findings": findings,
        "missing_elements": gaps_list,
        "entities": entities_dict,
        "queries": queries_list,
        "documentation_risks": risks,
        "summary": {
            "diagnoses_found": len(entities.diagnoses),
            "medications_found": len(entities.medications),
            "gaps_identified": len(gaps_list),
            "queries_generated": len(queries_list)
        }
    }
