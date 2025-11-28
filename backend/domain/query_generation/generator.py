"""
CDI Query Generator

Generates non-leading physician queries to address documentation gaps.
Follows ACDIS guidelines for compliant CDI query formulation.
"""

import logging
from typing import List, Optional, Dict, Any

from domain.common.models import (
    CDIQuery,
    CDIQueryResult,
    DocumentationGap,
    DocumentationGapAnalysis,
    GapPriority,
)

logger = logging.getLogger(__name__)


class CDIQueryGenerator:
    """
    Generates compliant CDI queries for physicians.

    Query Types:
    - Clarification: Ask for more specific information
    - Specificity: Request diagnosis specificity
    - Documentation: Request documentation of clinical indicators
    - Linkage: Request linkage between conditions
    """

    # Query templates by gap type
    QUERY_TEMPLATES = {
        "missing_vital": {
            "clarification": [
                "Clinical indicators suggest {condition_hint}. Please document current {vital_sign} value or specify if measurement was deferred and reason.",
                "Medical record shows {condition}. Would you please document the patient's {vital_sign} reading?",
            ],
        },
        "missing_lab": {
            "clarification": [
                "Please document {lab_name} result if available, or clinical indication for not obtaining this test.",
                "Medical record indicates {condition}. Would you please document the {lab_name} value or reason if not obtained?",
            ],
        },
        "missing_specificity": {
            "specificity": [
                "Please clarify the clinical characteristics of the documented {condition}. Is there any additional specificity that should be documented?",
                "Medical record documents {condition}. Would you please clarify the type/severity/chronicity for accurate coding?",
                "Documentation shows {condition}. Additional specificity regarding {specificity_needed} would assist in accurate code assignment.",
            ],
        },
        "missing_severity": {
            "specificity": [
                "Please clarify the severity/stage of the documented {condition}.",
                "Medical record shows {condition}. Would you please document the current stage or severity?",
            ],
        },
        "missing_linkage": {
            "linkage": [
                "Patient has both {condition1} and {condition2}. Is there a clinical relationship between these conditions that should be documented?",
                "Medical record shows {condition1} in a patient with {condition2}. Please clarify if these conditions are related.",
            ],
        },
        "missing_screening": {
            "documentation": [
                "Please document {screening_type} screening status (completed, refused, or contraindicated).",
                "Quality measure {measure_code} requires documentation of {screening_type}. Would you please document the current status?",
            ],
        },
        "hedis_gap": {
            "documentation": [
                "HEDIS quality measure {measure_code} documentation opportunity identified. Please review and document as clinically indicated.",
            ],
        },
    }

    # Non-leading query requirements
    NON_LEADING_REQUIREMENTS = [
        "Do not suggest a specific diagnosis",
        "Provide clinical indicators that support query",
        "Allow physician to determine appropriate response",
        "Reference documented findings only",
        "Do not hint at expected answer",
    ]

    def __init__(self, use_llm: bool = False):
        """
        Initialize the CDI query generator.

        Args:
            use_llm: Whether to use LLM for enhanced query generation
        """
        self.use_llm = use_llm
        self._llm_engine = None

    async def _get_llm_engine(self):
        """Get LLM engine for enhanced query generation."""
        if self._llm_engine is None and self.use_llm:
            from infrastructure.llm import get_default_engine
            self._llm_engine = get_default_engine()
        return self._llm_engine

    def generate_from_gaps(
        self,
        gap_analysis: DocumentationGapAnalysis,
        clinical_findings: Optional[Dict[str, Any]] = None,
    ) -> CDIQueryResult:
        """
        Generate CDI queries from documentation gap analysis.

        Args:
            gap_analysis: Documentation gap analysis result
            clinical_findings: Optional clinical context for queries

        Returns:
            CDIQueryResult with generated queries
        """
        if clinical_findings is None:
            clinical_findings = {}

        queries = []
        gaps_addressed = 0

        # Prioritize high-priority gaps
        sorted_gaps = sorted(
            gap_analysis.gaps,
            key=lambda g: (0 if g.priority == GapPriority.HIGH else
                          1 if g.priority == GapPriority.MEDIUM else 2)
        )

        for gap in sorted_gaps:
            query = self._generate_query_for_gap(gap, clinical_findings)
            if query:
                queries.append(query)
                gaps_addressed += 1

        # Limit to top 5 queries to avoid query fatigue
        queries = queries[:5]

        # Generate summary
        if queries:
            summary = f"Generated {len(queries)} CDI quer{'ies' if len(queries) != 1 else 'y'} addressing {gaps_addressed} documentation gap{'s' if gaps_addressed != 1 else ''}."
        else:
            summary = "No CDI queries generated. Documentation appears complete."

        return CDIQueryResult(
            queries=queries,
            summary=summary,
            documentation_gaps_addressed=gaps_addressed,
            confidence=0.9 if queries else 1.0,
        )

    def _generate_query_for_gap(
        self,
        gap: DocumentationGap,
        clinical_findings: Dict[str, Any]
    ) -> Optional[CDIQuery]:
        """Generate a single query for a documentation gap."""
        templates = self.QUERY_TEMPLATES.get(gap.gap_type)
        if not templates:
            templates = self.QUERY_TEMPLATES.get("missing_specificity")

        # Get query type (first key from templates)
        query_type = list(templates.keys())[0]
        template_list = templates[query_type]

        # Select template
        template = template_list[0]

        # Format template with context
        query_text = self._format_query_template(template, gap, clinical_findings)

        # Determine potential codes
        potential_codes = []
        if gap.measure_affected:
            potential_codes.append(f"HEDIS: {gap.measure_affected}")

        return CDIQuery(
            query_text=query_text,
            query_type=query_type,
            priority=gap.priority,
            clinical_finding=gap.description,
            gap_addressed=gap.gap_type,
            potential_codes=potential_codes,
            is_non_leading=True,
            compliance_notes="Query follows ACDIS non-leading guidelines",
        )

    def _format_query_template(
        self,
        template: str,
        gap: DocumentationGap,
        clinical_findings: Dict[str, Any]
    ) -> str:
        """Format query template with available context."""
        # Extract context from gap description
        replacements = {
            "{condition}": self._extract_condition(gap.description),
            "{condition_hint}": self._extract_condition(gap.description),
            "{vital_sign}": self._extract_vital(gap.description),
            "{lab_name}": self._extract_lab(gap.description),
            "{specificity_needed}": self._extract_specificity(gap.description),
            "{screening_type}": self._extract_screening(gap.description),
            "{measure_code}": gap.measure_affected or "quality",
        }

        # Add any clinical findings
        replacements.update(clinical_findings)

        # Apply replacements
        query_text = template
        for key, value in replacements.items():
            if key in query_text:
                query_text = query_text.replace(key, str(value))

        return query_text

    def _extract_condition(self, description: str) -> str:
        """Extract condition name from gap description."""
        conditions = [
            "hypertension", "diabetes", "heart failure", "copd", "ckd",
            "obesity", "depression", "pneumonia", "sepsis"
        ]
        desc_lower = description.lower()
        for condition in conditions:
            if condition in desc_lower:
                return condition.title()
        return "the documented condition"

    def _extract_vital(self, description: str) -> str:
        """Extract vital sign name from gap description."""
        vitals = {
            "blood pressure": "blood pressure",
            "bp": "blood pressure",
            "bmi": "BMI",
            "spo2": "oxygen saturation",
            "heart rate": "heart rate",
        }
        desc_lower = description.lower()
        for vital, display in vitals.items():
            if vital in desc_lower:
                return display
        return "vital signs"

    def _extract_lab(self, description: str) -> str:
        """Extract lab name from gap description."""
        labs = {
            "hba1c": "HbA1c",
            "a1c": "HbA1c",
            "creatinine": "creatinine",
            "egfr": "eGFR",
            "bnp": "BNP",
            "ldl": "LDL cholesterol",
        }
        desc_lower = description.lower()
        for lab, display in labs.items():
            if lab in desc_lower:
                return display
        return "laboratory value"

    def _extract_specificity(self, description: str) -> str:
        """Extract specificity type from gap description."""
        if "type" in description.lower():
            return "type"
        if "stage" in description.lower():
            return "stage/severity"
        if "acute" in description.lower() or "chronic" in description.lower():
            return "acuity (acute vs chronic)"
        if "systolic" in description.lower() or "diastolic" in description.lower():
            return "type (systolic vs diastolic)"
        return "additional clinical specificity"

    def _extract_screening(self, description: str) -> str:
        """Extract screening type from gap description."""
        screenings = {
            "mammogram": "breast cancer screening (mammogram)",
            "colonoscopy": "colorectal cancer screening",
            "colorectal": "colorectal cancer screening",
            "depression": "depression screening (PHQ-2/PHQ-9)",
            "chlamydia": "chlamydia screening",
        }
        desc_lower = description.lower()
        for screening, display in screenings.items():
            if screening in desc_lower:
                return display
        return "recommended screening"

    def generate_condition_query(
        self,
        condition: str,
        clinical_indicators: List[str],
        query_type: str = "clarification"
    ) -> CDIQuery:
        """
        Generate a single CDI query for a specific condition.

        Args:
            condition: Condition name
            clinical_indicators: Supporting clinical indicators
            query_type: Type of query (clarification, specificity, linkage)

        Returns:
            CDIQuery
        """
        indicators_text = ", ".join(clinical_indicators) if clinical_indicators else "documented findings"

        if query_type == "clarification":
            query_text = (
                f"Clinical documentation shows {indicators_text}. "
                f"Please clarify if this represents {condition} or provide "
                f"additional documentation to support the clinical impression."
            )
        elif query_type == "specificity":
            query_text = (
                f"The medical record documents {condition}. "
                f"Would you please clarify the clinical characteristics "
                f"(type, severity, acuity) for accurate code assignment?"
            )
        elif query_type == "linkage":
            query_text = (
                f"Patient has documented {condition}. "
                f"Are there any related conditions or complications "
                f"that should be documented?"
            )
        else:
            query_text = (
                f"Please review documentation for {condition} and "
                f"provide any additional clinical details as appropriate."
            )

        return CDIQuery(
            query_text=query_text,
            query_type=query_type,
            priority=GapPriority.MEDIUM,
            clinical_finding=indicators_text,
            is_non_leading=True,
            compliance_notes="Query follows ACDIS non-leading guidelines",
        )


# Convenience function
def generate_cdi_queries(
    clinical_note: str,
    patient_age: Optional[int] = None,
    patient_gender: Optional[str] = None,
) -> CDIQueryResult:
    """
    Convenience function to generate CDI queries from a clinical note.

    Args:
        clinical_note: Clinical note text
        patient_age: Patient age
        patient_gender: Patient gender

    Returns:
        CDIQueryResult with generated queries
    """
    from domain.documentation_gaps import analyze_documentation_gaps
    from domain.entity_extraction import extract_entities

    # Analyze documentation gaps
    gap_analysis = analyze_documentation_gaps(
        clinical_note=clinical_note,
        patient_age=patient_age,
        patient_gender=patient_gender,
    )

    # Extract clinical findings for context
    entities = extract_entities(clinical_note)
    clinical_findings = {
        "diagnoses": ", ".join(entities.get_diagnosis_names()[:3]),
        "vitals": entities.get_vitals_dict(),
        "labs": entities.get_labs_dict(),
    }

    # Generate queries
    generator = CDIQueryGenerator()
    result = generator.generate_from_gaps(
        gap_analysis=gap_analysis,
        clinical_findings=clinical_findings,
    )

    # Add context
    result.primary_condition = entities.get_diagnosis_names()[0] if entities.diagnoses else None

    return result
