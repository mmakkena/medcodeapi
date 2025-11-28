"""
HEDIS Evaluation Domain Module

HEDIS quality measure evaluation for 19 measures:
CBP, CDC, BCS, COL, BMI, DEP, CHL, WCC, CIS, IMA,
AAP, AWC, AMM, ADD, FUH, FUM, FUA, PPC, PCE

Supports:
- Value-based evaluation (BP, HbA1c, BMI targets)
- Screening status tracking
- Exclusion criteria handling
- Confidence scoring
- Gap identification
"""

from domain.hedis_evaluation.evaluator import (
    HEDISEvaluator,
    evaluate_hedis_measures,
)

from domain.hedis_evaluation.exclusions import (
    HEDIS_EXCLUSIONS,
    MEASURE_EXCLUSION_RULES,
    check_hedis_exclusions,
    is_measure_excluded,
)

__all__ = [
    "HEDISEvaluator",
    "evaluate_hedis_measures",
    "HEDIS_EXCLUSIONS",
    "MEASURE_EXCLUSION_RULES",
    "check_hedis_exclusions",
    "is_measure_excluded",
]
