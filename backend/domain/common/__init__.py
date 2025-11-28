"""
Common Domain Utilities

Provides shared data models, validation functions, and scoring utilities
used across the domain layer.
"""

# Data Models
from domain.common.models import (
    # Enums
    Severity,
    EvidenceGrade,
    MeasureStatus,
    GapPriority,
    # Clinical data models
    VitalSigns,
    LabResult,
    LabResults,
    Screening,
    Screenings,
    Diagnosis,
    Medication,
    PatientDemographics,
    ClinicalEntities,
    # HEDIS models
    HEDISMeasureResult,
    HEDISEvaluationResult,
    # Documentation gap models
    DocumentationGap,
    DocumentationGapAnalysis,
    # Revenue models
    EMCodeRecommendation,
    DRGOptimization,
    RevenueOpportunity,
    RevenueOptimizationResult,
    # CDI query models
    CDIQuery,
    CDIQueryResult,
)

# Validation functions
from domain.common.validation import (
    # Parsing functions
    parse_blood_pressure,
    parse_hba1c,
    parse_bmi,
    parse_ldl,
    parse_heart_rate,
    parse_temperature,
    parse_spo2,
    parse_creatinine,
    parse_glucose,
    # Code validation
    is_valid_icd10_code,
    is_valid_cpt_code,
    is_valid_hcpcs_code,
    # Validation classes
    ValidationResult,
    ClinicalDataValidator,
    ValidationIssue,
    ValidationReport,
)

# Scoring functions
from domain.common.scoring import (
    # HEDIS targets
    HEDIS_TARGETS,
    # Evaluation functions
    evaluate_bp_target,
    evaluate_hba1c_target,
    evaluate_bmi_category,
    evaluate_ldl_target,
    BPEvaluation,
    HbA1cEvaluation,
    BMIEvaluation,
    # Completeness scoring
    calculate_completeness_score,
    calculate_hedis_completeness,
    # Confidence scoring
    calculate_extraction_confidence,
    calculate_parsing_confidence,
    calculate_measure_confidence,
    calculate_overall_confidence,
    # Revenue scoring
    calculate_revenue_capture_rate,
    prioritize_revenue_gap,
    # E/M scoring
    calculate_em_level,
)

# Security utilities (from existing file)
from domain.common.security import (
    hash_api_key,
    hash_password,
    verify_password,
    generate_api_key,
)

__all__ = [
    # Enums
    "Severity",
    "EvidenceGrade",
    "MeasureStatus",
    "GapPriority",
    # Clinical data models
    "VitalSigns",
    "LabResult",
    "LabResults",
    "Screening",
    "Screenings",
    "Diagnosis",
    "Medication",
    "PatientDemographics",
    "ClinicalEntities",
    # HEDIS models
    "HEDISMeasureResult",
    "HEDISEvaluationResult",
    # Documentation gap models
    "DocumentationGap",
    "DocumentationGapAnalysis",
    # Revenue models
    "EMCodeRecommendation",
    "DRGOptimization",
    "RevenueOpportunity",
    "RevenueOptimizationResult",
    # CDI query models
    "CDIQuery",
    "CDIQueryResult",
    # Parsing functions
    "parse_blood_pressure",
    "parse_hba1c",
    "parse_bmi",
    "parse_ldl",
    "parse_heart_rate",
    "parse_temperature",
    "parse_spo2",
    "parse_creatinine",
    "parse_glucose",
    # Code validation
    "is_valid_icd10_code",
    "is_valid_cpt_code",
    "is_valid_hcpcs_code",
    # Validation classes
    "ValidationResult",
    "ClinicalDataValidator",
    "ValidationIssue",
    "ValidationReport",
    # HEDIS targets
    "HEDIS_TARGETS",
    # Evaluation functions
    "evaluate_bp_target",
    "evaluate_hba1c_target",
    "evaluate_bmi_category",
    "evaluate_ldl_target",
    "BPEvaluation",
    "HbA1cEvaluation",
    "BMIEvaluation",
    # Completeness scoring
    "calculate_completeness_score",
    "calculate_hedis_completeness",
    # Confidence scoring
    "calculate_extraction_confidence",
    "calculate_parsing_confidence",
    "calculate_measure_confidence",
    "calculate_overall_confidence",
    # Revenue scoring
    "calculate_revenue_capture_rate",
    "prioritize_revenue_gap",
    # E/M scoring
    "calculate_em_level",
    # Security
    "hash_api_key",
    "hash_password",
    "verify_password",
    "generate_api_key",
]
