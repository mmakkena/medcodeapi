"""
Domain Layer - Core Business Logic

This layer contains pure business logic with no external I/O dependencies.
All domain modules are independent of infrastructure (database, LLM, etc.)
and can be used by any adapter (API, MCP, CLI).

Modules:
    - entity_extraction: Clinical entity extraction from notes
    - hedis_evaluation: HEDIS quality measure evaluation
    - documentation_gaps: Clinical documentation gap detection
    - query_generation: CDI query generation for physicians
    - revenue_optimization: Revenue analysis, E/M coding, HCC, DRG
    - coding_helper: ICD-10/CPT code suggestion and validation
    - semantic_search: Vector and text search services
    - fee_schedule: Medicare fee schedule pricing
    - common: Shared utilities, scoring, validation
"""

__version__ = "2.0.0"

# Entity Extraction
from domain.entity_extraction import (
    ClinicalEntityExtractor,
    extract_entities,
    extract_vitals,
    extract_labs,
    extract_diagnoses,
)

# HEDIS Evaluation
from domain.hedis_evaluation import (
    HEDISEvaluator,
    evaluate_hedis_measures,
    check_hedis_exclusions,
    is_measure_excluded,
)

# Documentation Gaps
from domain.documentation_gaps import (
    DocumentationGapAnalyzer,
    analyze_documentation_gaps,
)

# Query Generation
from domain.query_generation import (
    CDIQueryGenerator,
    generate_cdi_queries,
)

# Revenue Optimization
from domain.revenue_optimization import (
    RevenueOptimizer,
    analyze_revenue_opportunities,
)

# Coding Helper
from domain.coding_helper import (
    ClinicalCodingHelper,
    CodeSuggestion,
    CodeValidationResult,
    suggest_codes,
    validate_code,
)

# Common Models and Utilities
from domain.common import (
    # Enums
    Severity,
    EvidenceGrade,
    MeasureStatus,
    GapPriority,
    # Models
    ClinicalEntities,
    HEDISMeasureResult,
    HEDISEvaluationResult,
    DocumentationGap,
    DocumentationGapAnalysis,
    EMCodeRecommendation,
    RevenueOptimizationResult,
    CDIQuery,
    CDIQueryResult,
    # Scoring
    HEDIS_TARGETS,
    evaluate_bp_target,
    evaluate_hba1c_target,
    evaluate_bmi_category,
)

__all__ = [
    # Entity Extraction
    "ClinicalEntityExtractor",
    "extract_entities",
    "extract_vitals",
    "extract_labs",
    "extract_diagnoses",
    # HEDIS Evaluation
    "HEDISEvaluator",
    "evaluate_hedis_measures",
    "check_hedis_exclusions",
    "is_measure_excluded",
    # Documentation Gaps
    "DocumentationGapAnalyzer",
    "analyze_documentation_gaps",
    # Query Generation
    "CDIQueryGenerator",
    "generate_cdi_queries",
    # Revenue Optimization
    "RevenueOptimizer",
    "analyze_revenue_opportunities",
    # Coding Helper
    "ClinicalCodingHelper",
    "CodeSuggestion",
    "CodeValidationResult",
    "suggest_codes",
    "validate_code",
    # Enums
    "Severity",
    "EvidenceGrade",
    "MeasureStatus",
    "GapPriority",
    # Models
    "ClinicalEntities",
    "HEDISMeasureResult",
    "HEDISEvaluationResult",
    "DocumentationGap",
    "DocumentationGapAnalysis",
    "EMCodeRecommendation",
    "RevenueOptimizationResult",
    "CDIQuery",
    "CDIQueryResult",
    # Scoring
    "HEDIS_TARGETS",
    "evaluate_bp_target",
    "evaluate_hba1c_target",
    "evaluate_bmi_category",
]
