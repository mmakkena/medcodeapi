"""
Documentation Gap Analyzer

Identifies documentation gaps in clinical notes that could impact:
- HEDIS quality measures
- Revenue optimization (coding accuracy)
- Clinical quality (specificity, completeness)
"""

import logging
from typing import Dict, List, Optional

from domain.common.models import (
    DocumentationGap,
    DocumentationGapAnalysis,
    GapPriority,
    EvidenceGrade,
    ClinicalEntities,
    HEDISEvaluationResult,
)
from domain.common.validation import ClinicalDataValidator

logger = logging.getLogger(__name__)


class DocumentationGapAnalyzer:
    """
    Analyzes clinical documentation for gaps that affect quality and revenue.

    Gap Categories:
    - missing_vital: Critical vital sign not documented
    - missing_lab: Required lab result not documented
    - missing_screening: Required screening not documented
    - missing_specificity: Diagnosis lacks specificity (e.g., type, acuity, laterality)
    - missing_linkage: Conditions not properly linked (e.g., CKD due to diabetes)
    - missing_severity: Severity/stage not specified
    - missing_documentation: E/M components missing
    """

    # Condition-specific documentation requirements
    CONDITION_REQUIREMENTS = {
        "hypertension": {
            "vitals": ["blood_pressure"],
            "labs": [],
            "specificity": ["stage/severity", "controlled/uncontrolled"],
            "hedis_measures": ["CBP"],
        },
        "diabetes": {
            "vitals": [],
            "labs": ["hba1c"],
            "specificity": ["type", "with/without complications"],
            "hedis_measures": ["CDC"],
            "related_screenings": ["diabetic_eye", "diabetic_foot"],
        },
        "heart_failure": {
            "vitals": ["blood_pressure"],
            "labs": ["bnp"],
            "specificity": ["systolic/diastolic", "acute/chronic", "stage/class"],
        },
        "copd": {
            "vitals": ["spo2"],
            "labs": [],
            "specificity": ["severity/stage", "acute/chronic exacerbation"],
        },
        "ckd": {
            "vitals": [],
            "labs": ["creatinine", "egfr"],
            "specificity": ["stage", "etiology"],
        },
        "obesity": {
            "vitals": ["bmi"],
            "labs": [],
            "specificity": ["class/severity"],
        },
        "depression": {
            "vitals": [],
            "labs": [],
            "specificity": ["severity", "recurrent/single episode"],
            "hedis_measures": ["DEP", "AMM"],
        },
    }

    # Age/gender specific screenings
    PREVENTIVE_SCREENINGS = {
        "female_50_74": ["mammogram"],
        "all_45_75": ["colonoscopy", "fit_test", "cologuard"],
        "female_16_24": ["chlamydia"],
        "all_adults": ["depression_screening"],
    }

    def __init__(self):
        """Initialize the documentation gap analyzer."""
        self.validator = ClinicalDataValidator()

    def analyze(
        self,
        entities: ClinicalEntities,
        hedis_result: Optional[HEDISEvaluationResult] = None,
        patient_age: Optional[int] = None,
        patient_gender: Optional[str] = None,
    ) -> DocumentationGapAnalysis:
        """
        Analyze clinical entities for documentation gaps.

        Args:
            entities: Extracted clinical entities
            hedis_result: Optional HEDIS evaluation result (for gap integration)
            patient_age: Patient age for preventive care screening
            patient_gender: Patient gender for screening eligibility

        Returns:
            DocumentationGapAnalysis with identified gaps and recommendations
        """
        gaps = []

        # Analyze condition-specific gaps
        condition_gaps = self._analyze_condition_gaps(entities)
        gaps.extend(condition_gaps)

        # Analyze specificity gaps
        specificity_gaps = self._analyze_specificity_gaps(entities)
        gaps.extend(specificity_gaps)

        # Analyze preventive screening gaps
        if patient_age and patient_gender:
            screening_gaps = self._analyze_screening_gaps(
                entities, patient_age, patient_gender
            )
            gaps.extend(screening_gaps)

        # Integrate HEDIS gaps if available
        if hedis_result:
            hedis_gaps = self._integrate_hedis_gaps(hedis_result)
            gaps.extend(hedis_gaps)

        # Calculate priorities
        high_count = sum(1 for g in gaps if g.priority == GapPriority.HIGH)
        medium_count = sum(1 for g in gaps if g.priority == GapPriority.MEDIUM)
        low_count = sum(1 for g in gaps if g.priority == GapPriority.LOW)

        # Estimate total revenue impact
        total_revenue = sum(g.revenue_impact or 0 for g in gaps)

        # Generate recommendations
        recommendations = self._generate_recommendations(gaps)

        return DocumentationGapAnalysis(
            gaps=gaps,
            high_priority_count=high_count,
            medium_priority_count=medium_count,
            low_priority_count=low_count,
            total_revenue_impact=total_revenue,
            recommendations=recommendations,
        )

    def _analyze_condition_gaps(
        self,
        entities: ClinicalEntities
    ) -> List[DocumentationGap]:
        """Analyze gaps based on documented conditions."""
        gaps = []

        # Get lowercase diagnosis names
        diagnosis_names = [d.name.lower() for d in entities.diagnoses]

        for condition, requirements in self.CONDITION_REQUIREMENTS.items():
            # Check if condition is present
            if not any(condition in dx for dx in diagnosis_names):
                continue

            # Check required vitals
            for vital in requirements.get("vitals", []):
                if entities.vitals is None:
                    value = None
                elif vital == "blood_pressure":
                    value = entities.vitals.blood_pressure
                elif vital == "bmi":
                    value = entities.vitals.bmi
                elif vital == "spo2":
                    value = entities.vitals.spo2
                else:
                    value = getattr(entities.vitals, vital, None)

                if value is None:
                    gaps.append(DocumentationGap(
                        gap_type="missing_vital",
                        description=f"{vital.replace('_', ' ').title()} not documented for {condition}",
                        priority=GapPriority.HIGH,
                        measure_affected=requirements.get("hedis_measures", [None])[0],
                        suggested_action=f"Document {vital.replace('_', ' ')} value",
                        revenue_impact=50.0,  # Estimated impact
                        evidence_grade=EvidenceGrade.A,
                    ))

            # Check required labs
            for lab in requirements.get("labs", []):
                if entities.labs is None:
                    value = None
                else:
                    value = getattr(entities.labs, lab, None)

                if value is None:
                    gaps.append(DocumentationGap(
                        gap_type="missing_lab",
                        description=f"{lab.upper()} not documented for {condition}",
                        priority=GapPriority.HIGH,
                        measure_affected=requirements.get("hedis_measures", [None])[0],
                        suggested_action=f"Document {lab.upper()} result or order if not recently done",
                        revenue_impact=75.0,
                        evidence_grade=EvidenceGrade.A,
                    ))

        return gaps

    def _analyze_specificity_gaps(
        self,
        entities: ClinicalEntities
    ) -> List[DocumentationGap]:
        """Analyze gaps in diagnosis specificity."""
        gaps = []

        for diagnosis in entities.diagnoses:
            dx_lower = diagnosis.name.lower()

            # Check common specificity issues
            if "hypertension" in dx_lower and "essential" not in dx_lower:
                if diagnosis.icd10_code is None or diagnosis.icd10_code == "I10":
                    gaps.append(DocumentationGap(
                        gap_type="missing_specificity",
                        description="Hypertension lacks specificity (controlled vs uncontrolled)",
                        priority=GapPriority.MEDIUM,
                        measure_affected="CBP",
                        suggested_action="Specify if hypertension is controlled or uncontrolled",
                        revenue_impact=25.0,
                        evidence_grade=EvidenceGrade.B,
                    ))

            if "diabetes" in dx_lower:
                if "type" not in dx_lower and "dm" not in dx_lower:
                    gaps.append(DocumentationGap(
                        gap_type="missing_specificity",
                        description="Diabetes type not specified (Type 1 vs Type 2)",
                        priority=GapPriority.HIGH,
                        measure_affected="CDC",
                        suggested_action="Specify diabetes type (Type 1 or Type 2)",
                        revenue_impact=50.0,
                        evidence_grade=EvidenceGrade.A,
                    ))

                # Check for complications documentation
                complication_keywords = [
                    "nephropathy", "neuropathy", "retinopathy",
                    "gastroparesis", "foot ulcer", "ckd due to"
                ]
                has_complication_mention = any(
                    kw in dx_lower for kw in complication_keywords
                )

                if not has_complication_mention:
                    gaps.append(DocumentationGap(
                        gap_type="missing_linkage",
                        description="Diabetes complications not documented/linked",
                        priority=GapPriority.MEDIUM,
                        suggested_action="Document any diabetic complications (nephropathy, neuropathy, retinopathy) if present",
                        revenue_impact=100.0,  # HCC impact
                        evidence_grade=EvidenceGrade.B,
                    ))

            if "heart failure" in dx_lower:
                if "systolic" not in dx_lower and "diastolic" not in dx_lower:
                    gaps.append(DocumentationGap(
                        gap_type="missing_specificity",
                        description="Heart failure type not specified (HFrEF vs HFpEF)",
                        priority=GapPriority.HIGH,
                        suggested_action="Specify heart failure type based on ejection fraction",
                        revenue_impact=75.0,
                        evidence_grade=EvidenceGrade.A,
                    ))

                if "acute" not in dx_lower and "chronic" not in dx_lower:
                    gaps.append(DocumentationGap(
                        gap_type="missing_specificity",
                        description="Heart failure acuity not specified (acute vs chronic)",
                        priority=GapPriority.HIGH,
                        suggested_action="Specify if heart failure is acute, chronic, or acute on chronic",
                        revenue_impact=50.0,
                        evidence_grade=EvidenceGrade.A,
                    ))

            if "ckd" in dx_lower or "chronic kidney" in dx_lower:
                if not any(f"stage {i}" in dx_lower for i in range(1, 6)):
                    gaps.append(DocumentationGap(
                        gap_type="missing_severity",
                        description="CKD stage not documented",
                        priority=GapPriority.HIGH,
                        suggested_action="Document CKD stage (1-5) based on eGFR",
                        revenue_impact=75.0,
                        evidence_grade=EvidenceGrade.A,
                    ))

        return gaps

    def _analyze_screening_gaps(
        self,
        entities: ClinicalEntities,
        patient_age: int,
        patient_gender: str
    ) -> List[DocumentationGap]:
        """Analyze gaps in preventive screening documentation."""
        gaps = []

        screenings = entities.screenings
        if screenings is None:
            screenings_dict = {}
        else:
            screenings_dict = screenings.__dict__

        gender_lower = patient_gender.lower()

        # Breast cancer screening (female 50-74)
        if gender_lower == "female" and 50 <= patient_age <= 74:
            if not screenings_dict.get("mammogram", False):
                gaps.append(DocumentationGap(
                    gap_type="missing_screening",
                    description="Mammogram not documented for eligible female patient",
                    priority=GapPriority.HIGH,
                    measure_affected="BCS",
                    suggested_action="Document mammogram status or order if not done in past 2 years",
                    revenue_impact=50.0,
                    evidence_grade=EvidenceGrade.A,
                ))

        # Colorectal cancer screening (45-75)
        if 45 <= patient_age <= 75:
            has_colorectal = any([
                screenings_dict.get("colonoscopy", False),
                screenings_dict.get("fit_test", False),
                screenings_dict.get("cologuard", False),
            ])
            if not has_colorectal:
                gaps.append(DocumentationGap(
                    gap_type="missing_screening",
                    description="Colorectal cancer screening not documented",
                    priority=GapPriority.HIGH,
                    measure_affected="COL",
                    suggested_action="Document colorectal screening (colonoscopy, FIT, or Cologuard) status",
                    revenue_impact=50.0,
                    evidence_grade=EvidenceGrade.A,
                ))

        # Chlamydia screening (female 16-24)
        if gender_lower == "female" and 16 <= patient_age <= 24:
            if not screenings_dict.get("chlamydia", False):
                gaps.append(DocumentationGap(
                    gap_type="missing_screening",
                    description="Chlamydia screening not documented for sexually active young female",
                    priority=GapPriority.MEDIUM,
                    measure_affected="CHL",
                    suggested_action="Assess sexual activity and order chlamydia screening if appropriate",
                    revenue_impact=25.0,
                    evidence_grade=EvidenceGrade.A,
                ))

        # Depression screening (all adults)
        if patient_age >= 18:
            if not screenings_dict.get("depression_screening", False):
                gaps.append(DocumentationGap(
                    gap_type="missing_screening",
                    description="Depression screening not documented",
                    priority=GapPriority.MEDIUM,
                    measure_affected="DEP",
                    suggested_action="Complete PHQ-2 or PHQ-9 screening",
                    revenue_impact=25.0,
                    evidence_grade=EvidenceGrade.A,
                ))

        return gaps

    def _integrate_hedis_gaps(
        self,
        hedis_result: HEDISEvaluationResult
    ) -> List[DocumentationGap]:
        """Convert HEDIS evaluation gaps into documentation gaps."""
        gaps = []

        for gap_msg in hedis_result.gaps:
            # Parse HEDIS gap message
            priority = GapPriority.HIGH if "not documented" in gap_msg.lower() else GapPriority.MEDIUM

            # Determine measure code from message
            measure_code = None
            for code in ["CBP", "CDC", "BCS", "COL", "BMI", "DEP", "CHL", "WCC", "AWC", "AAP"]:
                if code in gap_msg:
                    measure_code = code
                    break

            gaps.append(DocumentationGap(
                gap_type="hedis_gap",
                description=gap_msg,
                priority=priority,
                measure_affected=measure_code,
                revenue_impact=50.0,  # Standard HEDIS gap impact
                evidence_grade=EvidenceGrade.A,
            ))

        return gaps

    def _generate_recommendations(
        self,
        gaps: List[DocumentationGap]
    ) -> List[str]:
        """Generate actionable recommendations based on identified gaps."""
        recommendations = []

        # Group by priority
        high_priority = [g for g in gaps if g.priority == GapPriority.HIGH]
        medium_priority = [g for g in gaps if g.priority == GapPriority.MEDIUM]

        if high_priority:
            recommendations.append(
                f"Address {len(high_priority)} high-priority documentation gaps to improve coding accuracy and quality scores."
            )

        # Condition-specific recommendations
        condition_gaps = [g for g in gaps if g.gap_type in ("missing_specificity", "missing_severity", "missing_linkage")]
        if condition_gaps:
            recommendations.append(
                "Review diagnosis specificity to capture accurate severity, type, and complications."
            )

        # HEDIS-specific recommendations
        hedis_gaps = [g for g in gaps if g.measure_affected]
        if hedis_gaps:
            measures_affected = set(g.measure_affected for g in hedis_gaps if g.measure_affected)
            recommendations.append(
                f"Address HEDIS gaps for measures: {', '.join(sorted(measures_affected))} to improve quality scores."
            )

        # Screening recommendations
        screening_gaps = [g for g in gaps if g.gap_type == "missing_screening"]
        if screening_gaps:
            recommendations.append(
                "Complete recommended preventive screenings and document results in the medical record."
            )

        return recommendations


# Convenience function
def analyze_documentation_gaps(
    clinical_note: str,
    patient_age: Optional[int] = None,
    patient_gender: Optional[str] = None,
) -> DocumentationGapAnalysis:
    """
    Convenience function to analyze documentation gaps from a clinical note.

    Args:
        clinical_note: Clinical note text
        patient_age: Patient age for screening eligibility
        patient_gender: Patient gender for screening eligibility

    Returns:
        DocumentationGapAnalysis with identified gaps
    """
    from domain.entity_extraction import extract_entities
    from domain.hedis_evaluation import evaluate_hedis_measures

    # Extract entities
    entities = extract_entities(clinical_note)

    # Get age/gender from entities if not provided
    if patient_age is None and entities.demographics:
        patient_age = entities.demographics.age
    if patient_gender is None and entities.demographics:
        patient_gender = entities.demographics.gender

    # Evaluate HEDIS if we have demographics
    hedis_result = None
    if patient_age and patient_gender:
        hedis_result = evaluate_hedis_measures(
            clinical_note=clinical_note,
            patient_age=patient_age,
            patient_gender=patient_gender,
        )

    # Analyze gaps
    analyzer = DocumentationGapAnalyzer()
    return analyzer.analyze(
        entities=entities,
        hedis_result=hedis_result,
        patient_age=patient_age,
        patient_gender=patient_gender,
    )
