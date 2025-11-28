"""
Shared Domain Models

Data classes and models used across the domain layer for clinical documentation,
HEDIS evaluation, and revenue optimization.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import date


class Severity(str, Enum):
    """Clinical severity levels."""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class EvidenceGrade(str, Enum):
    """Evidence-based practice grades."""
    A = "A"  # Strong evidence
    B = "B"  # Moderate evidence
    C = "C"  # Limited evidence
    D = "D"  # Expert opinion only


class MeasureStatus(str, Enum):
    """HEDIS measure compliance status."""
    NUMERATOR = "numerator"
    DENOMINATOR_ONLY = "denominator_only"
    EXCLUDED = "excluded"
    NOT_APPLICABLE = "not_applicable"


class GapPriority(str, Enum):
    """Documentation gap priority."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================================
# Clinical Data Models
# ============================================================================

@dataclass
class VitalSigns:
    """Extracted vital signs from clinical note."""
    blood_pressure: Optional[str] = None  # e.g., "128/82"
    systolic: Optional[int] = None
    diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    temperature: Optional[float] = None
    spo2: Optional[float] = None
    bmi: Optional[float] = None
    weight: Optional[float] = None  # kg
    height: Optional[float] = None  # cm

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class LabResult:
    """Individual lab result."""
    test_name: str
    value: Union[float, str]
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    is_abnormal: bool = False
    raw_text: Optional[str] = None


@dataclass
class LabResults:
    """Extracted lab results from clinical note."""
    hba1c: Optional[float] = None
    ldl: Optional[int] = None
    hdl: Optional[int] = None
    total_cholesterol: Optional[int] = None
    triglycerides: Optional[int] = None
    creatinine: Optional[float] = None
    egfr: Optional[float] = None
    bnp: Optional[float] = None
    troponin: Optional[float] = None
    procalcitonin: Optional[float] = None
    lactate: Optional[float] = None
    glucose: Optional[int] = None
    potassium: Optional[float] = None
    sodium: Optional[int] = None
    wbc: Optional[float] = None
    hemoglobin: Optional[float] = None
    platelets: Optional[int] = None
    inr: Optional[float] = None
    additional_labs: List[LabResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {k: v for k, v in asdict(self).items()
                  if v is not None and k != 'additional_labs'}
        if self.additional_labs:
            result['additional_labs'] = [asdict(lab) for lab in self.additional_labs]
        return result


@dataclass
class Screening:
    """Screening status."""
    screening_type: str
    performed: bool
    date: Optional[date] = None
    result: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class Screenings:
    """Extracted screening information."""
    mammogram: bool = False
    colonoscopy: bool = False
    fit_test: bool = False
    cologuard: bool = False
    depression_screening: bool = False
    depression_tool: Optional[str] = None  # PHQ-2, PHQ-9
    depression_score: Optional[int] = None
    chlamydia: bool = False
    cervical_cancer: bool = False
    lung_cancer: bool = False
    bone_density: bool = False
    diabetic_eye: bool = False
    diabetic_foot: bool = False
    additional_screenings: List[Screening] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v}


@dataclass
class Diagnosis:
    """Individual diagnosis."""
    name: str
    icd10_code: Optional[str] = None
    is_primary: bool = False
    is_chronic: bool = False
    status: Optional[str] = None  # active, resolved, ruled_out
    confidence: float = 1.0


@dataclass
class Medication:
    """Individual medication."""
    name: str
    dose: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    start_date: Optional[date] = None
    drug_class: Optional[str] = None


@dataclass
class PatientDemographics:
    """Patient demographic information."""
    age: Optional[int] = None
    gender: Optional[str] = None  # male, female
    race: Optional[str] = None
    ethnicity: Optional[str] = None


# ============================================================================
# Clinical Extraction Result Models
# ============================================================================

@dataclass
class ClinicalEntities:
    """Complete extracted clinical entities from a note."""
    diagnoses: List[Diagnosis] = field(default_factory=list)
    vitals: Optional[VitalSigns] = None
    labs: Optional[LabResults] = None
    screenings: Optional[Screenings] = None
    medications: List[Medication] = field(default_factory=list)
    procedures: List[str] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    demographics: Optional[PatientDemographics] = None

    # Extraction metadata
    extraction_confidence: float = 1.0
    extraction_warnings: List[str] = field(default_factory=list)
    raw_text_length: int = 0

    def get_diagnosis_names(self) -> List[str]:
        """Get list of diagnosis names."""
        return [d.name for d in self.diagnoses]

    def get_vitals_dict(self) -> Dict[str, str]:
        """Get vitals as a simple dict for HEDIS evaluation."""
        if not self.vitals:
            return {}
        result = {}
        if self.vitals.blood_pressure:
            result["BP"] = self.vitals.blood_pressure
        if self.vitals.heart_rate:
            result["HR"] = str(self.vitals.heart_rate)
        if self.vitals.bmi:
            result["BMI"] = str(self.vitals.bmi)
        if self.vitals.temperature:
            result["Temp"] = str(self.vitals.temperature)
        return result

    def get_labs_dict(self) -> Dict[str, str]:
        """Get labs as a simple dict for HEDIS evaluation."""
        if not self.labs:
            return {}
        result = {}
        if self.labs.hba1c:
            result["HbA1c"] = str(self.labs.hba1c)
        if self.labs.ldl:
            result["LDL"] = str(self.labs.ldl)
        return result

    def get_screenings_dict(self) -> Dict[str, bool]:
        """Get screenings as a simple dict for HEDIS evaluation."""
        if not self.screenings:
            return {}
        return {
            "Mammogram": self.screenings.mammogram,
            "Colorectal": (self.screenings.colonoscopy or
                          self.screenings.fit_test or
                          self.screenings.cologuard),
            "Depression": self.screenings.depression_screening,
            "Chlamydia": self.screenings.chlamydia,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "diagnoses": [asdict(d) for d in self.diagnoses],
            "vitals": self.vitals.to_dict() if self.vitals else None,
            "labs": self.labs.to_dict() if self.labs else None,
            "screenings": self.screenings.to_dict() if self.screenings else None,
            "medications": [asdict(m) for m in self.medications],
            "procedures": self.procedures,
            "allergies": self.allergies,
            "demographics": asdict(self.demographics) if self.demographics else None,
            "extraction_confidence": self.extraction_confidence,
            "extraction_warnings": self.extraction_warnings,
        }


# ============================================================================
# HEDIS Evaluation Models
# ============================================================================

@dataclass
class HEDISMeasureResult:
    """Result for a single HEDIS measure evaluation."""
    measure_code: str
    measure_name: str
    applicable: bool
    documented: Union[bool, str]  # True, False, or "partial"
    meets_target: Optional[bool] = None
    status: str = "Not Evaluated"
    score: str = "not_applicable"  # numerator, denominator_only, excluded

    # Value-based details
    value: Optional[Any] = None
    target: Optional[Any] = None
    raw_value: Optional[str] = None

    # Control levels for diabetes
    control_levels: Optional[Dict[str, bool]] = None

    # Exclusion info
    exclusion_reason: Optional[str] = None

    # Age/gender eligibility
    age_range: Optional[str] = None
    gender: Optional[str] = None

    # Gap description for actionable feedback
    gap_description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        # Remove None values
        return {k: v for k, v in result.items() if v is not None}


@dataclass
class HEDISEvaluationResult:
    """Complete HEDIS evaluation result."""
    measures: Dict[str, HEDISMeasureResult]
    gaps: List[str]

    # Summary statistics
    total_applicable: int = 0
    total_met: int = 0
    total_not_met: int = 0
    total_excluded: int = 0

    # Completeness score
    completeness_score: float = 0.0

    # Confidence metrics
    extraction_confidence: float = 1.0
    parsing_confidence: float = 1.0
    measure_confidence: float = 1.0
    overall_confidence: float = 1.0
    confidence_warnings: List[str] = field(default_factory=list)

    # Exclusions detected
    exclusions_detected: Dict[str, Dict] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "measures": {k: v.to_dict() for k, v in self.measures.items()},
            "gaps": self.gaps,
            "summary": {
                "total_applicable": self.total_applicable,
                "total_met": self.total_met,
                "total_not_met": self.total_not_met,
                "total_excluded": self.total_excluded,
                "completeness_score": self.completeness_score,
            },
            "confidence": {
                "extraction": self.extraction_confidence,
                "parsing": self.parsing_confidence,
                "measure": self.measure_confidence,
                "overall": self.overall_confidence,
                "warnings": self.confidence_warnings,
            },
            "exclusions_detected": self.exclusions_detected,
        }


# ============================================================================
# Documentation Gap Models
# ============================================================================

@dataclass
class DocumentationGap:
    """Individual documentation gap."""
    gap_type: str  # missing_vital, missing_lab, missing_screening, missing_specificity
    description: str
    priority: GapPriority
    measure_affected: Optional[str] = None  # HEDIS measure code if applicable
    suggested_action: Optional[str] = None
    revenue_impact: Optional[float] = None
    evidence_grade: Optional[EvidenceGrade] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gap_type": self.gap_type,
            "description": self.description,
            "priority": self.priority.value,
            "measure_affected": self.measure_affected,
            "suggested_action": self.suggested_action,
            "revenue_impact": self.revenue_impact,
            "evidence_grade": self.evidence_grade.value if self.evidence_grade else None,
        }


@dataclass
class DocumentationGapAnalysis:
    """Complete documentation gap analysis."""
    gaps: List[DocumentationGap]

    high_priority_count: int = 0
    medium_priority_count: int = 0
    low_priority_count: int = 0
    total_revenue_impact: float = 0.0

    # Recommendations
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gaps": [g.to_dict() for g in self.gaps],
            "summary": {
                "high_priority": self.high_priority_count,
                "medium_priority": self.medium_priority_count,
                "low_priority": self.low_priority_count,
                "total_revenue_impact": self.total_revenue_impact,
            },
            "recommendations": self.recommendations,
        }


# ============================================================================
# Revenue Optimization Models
# ============================================================================

@dataclass
class EMCodeRecommendation:
    """E/M code recommendation."""
    recommended_code: str
    confidence: float
    documented_level: str
    reimbursement: float
    potential_upgrade_code: Optional[str] = None
    potential_upgrade_reimbursement: Optional[float] = None
    documentation_gaps: List[str] = field(default_factory=list)
    revenue_gap: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "recommended_code": self.recommended_code,
            "confidence": self.confidence,
            "documented_level": self.documented_level,
            "reimbursement": self.reimbursement,
            "documentation_gaps": self.documentation_gaps,
        }
        if self.potential_upgrade_code:
            result["potential_upgrade"] = {
                "code": self.potential_upgrade_code,
                "reimbursement": self.potential_upgrade_reimbursement,
                "revenue_gap": self.revenue_gap,
            }
        return result


@dataclass
class DRGOptimization:
    """DRG optimization recommendation."""
    current_drg: Optional[str] = None
    potential_drg: Optional[str] = None
    revenue_impact: float = 0.0
    documentation_improvements: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_drg": self.current_drg,
            "potential_drg": self.potential_drg,
            "revenue_impact": self.revenue_impact,
            "documentation_improvements": self.documentation_improvements,
        }


@dataclass
class RevenueOpportunity:
    """Individual revenue opportunity."""
    opportunity_type: str  # missing_test, em_upgrade, drg_optimization
    description: str
    estimated_value: float
    priority: GapPriority
    action_required: str


@dataclass
class RevenueOptimizationResult:
    """Complete revenue optimization analysis."""
    condition: str
    severity: str

    # Test analysis
    tests_documented: List[str]
    tests_missing: List[Dict[str, Any]]
    test_revenue_opportunity: float

    # E/M coding
    em_recommendation: Optional[EMCodeRecommendation] = None
    em_revenue_opportunity: float = 0.0

    # DRG optimization
    drg_optimization: Optional[DRGOptimization] = None
    drg_revenue_opportunity: float = 0.0

    # HCC risk adjustment
    hcc_opportunities: List[str] = field(default_factory=list)
    hcc_revenue_opportunity: float = 0.0

    # Total opportunity
    total_revenue_opportunity: float = 0.0
    revenue_capture_rate: float = 0.0

    # Confidence
    confidence: float = 1.0
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "condition": self.condition,
            "severity": self.severity,
            "test_analysis": {
                "documented": self.tests_documented,
                "missing": self.tests_missing,
                "opportunity": self.test_revenue_opportunity,
            },
            "em_coding": self.em_recommendation.to_dict() if self.em_recommendation else None,
            "drg_optimization": self.drg_optimization.to_dict() if self.drg_optimization else None,
            "hcc_opportunities": self.hcc_opportunities,
            "revenue_summary": {
                "test_revenue": self.test_revenue_opportunity,
                "em_revenue": self.em_revenue_opportunity,
                "drg_revenue": self.drg_revenue_opportunity,
                "hcc_revenue": self.hcc_revenue_opportunity,
                "total_opportunity": self.total_revenue_opportunity,
                "capture_rate": f"{self.revenue_capture_rate:.1f}%",
            },
            "confidence": self.confidence,
            "warnings": self.warnings,
        }


# ============================================================================
# CDI Query Models
# ============================================================================

@dataclass
class CDIQuery:
    """Generated CDI query for physicians."""
    query_text: str
    query_type: str  # clarification, specificity, documentation
    priority: GapPriority

    # Context
    clinical_finding: Optional[str] = None
    gap_addressed: Optional[str] = None
    potential_codes: List[str] = field(default_factory=list)

    # Compliance
    is_non_leading: bool = True
    compliance_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_text": self.query_text,
            "query_type": self.query_type,
            "priority": self.priority.value,
            "clinical_finding": self.clinical_finding,
            "gap_addressed": self.gap_addressed,
            "potential_codes": self.potential_codes,
            "is_non_leading": self.is_non_leading,
            "compliance_notes": self.compliance_notes,
        }


@dataclass
class CDIQueryResult:
    """Complete CDI query generation result."""
    queries: List[CDIQuery]
    summary: str

    # Analysis context
    primary_condition: Optional[str] = None
    severity_level: Optional[str] = None
    documentation_gaps_addressed: int = 0

    # Confidence
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "queries": [q.to_dict() for q in self.queries],
            "summary": self.summary,
            "context": {
                "primary_condition": self.primary_condition,
                "severity_level": self.severity_level,
                "gaps_addressed": self.documentation_gaps_addressed,
            },
            "confidence": self.confidence,
        }
