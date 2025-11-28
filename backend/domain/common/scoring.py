"""
Clinical Scoring and Calculation Utilities

Provides scoring functions for HEDIS measures, documentation quality,
and revenue optimization calculations.
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass

from domain.common.validation import parse_blood_pressure, parse_hba1c, parse_bmi

logger = logging.getLogger(__name__)


# ============================================================================
# HEDIS Clinical Targets (2024)
# ============================================================================

HEDIS_TARGETS = {
    "CBP": {
        "name": "Controlling High Blood Pressure",
        "systolic_target": 140,
        "diastolic_target": 90,
        "description": "BP <140/90 mmHg"
    },
    "CDC_HbA1c_8": {
        "name": "HbA1c Control <8%",
        "target": 8.0,
        "description": "Good diabetes control"
    },
    "CDC_HbA1c_9": {
        "name": "HbA1c Poor Control >9%",
        "target": 9.0,
        "inverted": True,
        "description": "Avoid poor diabetes control"
    },
    "CDC_HbA1c_7": {
        "name": "HbA1c Control <7%",
        "target": 7.0,
        "description": "Excellent diabetes control"
    },
    "BMI_Categories": {
        "underweight": 18.5,
        "normal_max": 24.9,
        "overweight_max": 29.9,
        "obese_1_max": 34.9,
        "obese_2_max": 39.9,
        "obese_3_min": 40.0
    },
    "LDL_Targets": {
        "general": 100,  # General population
        "high_risk": 70,  # ASCVD/diabetes
        "very_high_risk": 55,  # Very high risk
    },
}


# ============================================================================
# Value-Based Evaluation Functions
# ============================================================================

@dataclass
class BPEvaluation:
    """Blood pressure evaluation result."""
    meets_target: bool
    systolic: int
    diastolic: int
    systolic_controlled: bool
    diastolic_controlled: bool
    target_systolic: int
    target_diastolic: int
    margin_systolic: int
    margin_diastolic: int


def evaluate_bp_target(systolic: int, diastolic: int) -> BPEvaluation:
    """
    Evaluate if BP meets HEDIS CBP target.

    Args:
        systolic: Systolic BP in mmHg
        diastolic: Diastolic BP in mmHg

    Returns:
        BPEvaluation with evaluation details
    """
    target = HEDIS_TARGETS["CBP"]

    systolic_controlled = systolic < target["systolic_target"]
    diastolic_controlled = diastolic < target["diastolic_target"]

    # Both must be controlled for HEDIS CBP
    meets_target = systolic_controlled and diastolic_controlled

    return BPEvaluation(
        meets_target=meets_target,
        systolic=systolic,
        diastolic=diastolic,
        systolic_controlled=systolic_controlled,
        diastolic_controlled=diastolic_controlled,
        target_systolic=target["systolic_target"],
        target_diastolic=target["diastolic_target"],
        margin_systolic=target["systolic_target"] - systolic,
        margin_diastolic=target["diastolic_target"] - diastolic
    )


@dataclass
class HbA1cEvaluation:
    """HbA1c evaluation result."""
    value: float
    excellent_control_lt7: bool
    good_control_lt8: bool
    poor_control_gt9: bool
    target_primary: float
    margin_from_8: float


def evaluate_hba1c_target(hba1c: float) -> HbA1cEvaluation:
    """
    Evaluate HbA1c against HEDIS CDC targets.

    Args:
        hba1c: HbA1c value as percentage

    Returns:
        HbA1cEvaluation with evaluation for all control levels
    """
    return HbA1cEvaluation(
        value=hba1c,
        excellent_control_lt7=hba1c < HEDIS_TARGETS["CDC_HbA1c_7"]["target"],
        good_control_lt8=hba1c < HEDIS_TARGETS["CDC_HbA1c_8"]["target"],
        poor_control_gt9=hba1c > HEDIS_TARGETS["CDC_HbA1c_9"]["target"],
        target_primary=HEDIS_TARGETS["CDC_HbA1c_8"]["target"],
        margin_from_8=HEDIS_TARGETS["CDC_HbA1c_8"]["target"] - hba1c
    )


@dataclass
class BMIEvaluation:
    """BMI evaluation result."""
    bmi: float
    category: str
    risk_level: str
    needs_intervention: bool


def evaluate_bmi_category(bmi: float) -> BMIEvaluation:
    """
    Categorize BMI and identify risk level.

    Args:
        bmi: BMI value

    Returns:
        BMIEvaluation with category, risk level, and intervention flag
    """
    categories = HEDIS_TARGETS["BMI_Categories"]

    if bmi < categories["underweight"]:
        category = "Underweight"
        risk = "Low weight"
    elif bmi <= categories["normal_max"]:
        category = "Normal"
        risk = "None"
    elif bmi <= categories["overweight_max"]:
        category = "Overweight"
        risk = "Moderate"
    elif bmi <= categories["obese_1_max"]:
        category = "Obese Class I"
        risk = "High"
    elif bmi <= categories["obese_2_max"]:
        category = "Obese Class II"
        risk = "Very High"
    else:
        category = "Obese Class III"
        risk = "Extremely High"

    return BMIEvaluation(
        bmi=bmi,
        category=category,
        risk_level=risk,
        needs_intervention=bmi >= 25.0 or bmi < 18.5
    )


def evaluate_ldl_target(ldl: int, risk_category: str = "general") -> Dict[str, Any]:
    """
    Evaluate LDL against target based on risk category.

    Args:
        ldl: LDL cholesterol in mg/dL
        risk_category: "general", "high_risk", or "very_high_risk"

    Returns:
        Evaluation dictionary
    """
    targets = HEDIS_TARGETS["LDL_Targets"]
    target = targets.get(risk_category, targets["general"])

    return {
        "value": ldl,
        "target": target,
        "meets_target": ldl < target,
        "margin": target - ldl,
        "risk_category": risk_category,
    }


# ============================================================================
# Completeness Scoring Functions
# ============================================================================

def calculate_completeness_score(measure_results: Dict[str, bool]) -> float:
    """
    Calculate documentation completeness score based on measure results.

    Args:
        measure_results: Dict mapping measure codes to compliance bool

    Returns:
        Completeness score from 0.0 to 1.0

    Example:
        >>> results = {'CBP': True, 'CDC': True, 'BCS': False, 'COL': False}
        >>> calculate_completeness_score(results)
        0.5
    """
    if not measure_results:
        return 0.0

    total = len(measure_results)
    passed = sum(1 for v in measure_results.values() if v)

    return round(passed / total, 2)


def calculate_hedis_completeness(
    measure_results: Dict[str, Dict]
) -> Tuple[float, Dict[str, int]]:
    """
    Calculate HEDIS completeness with breakdown.

    Args:
        measure_results: Dict of HEDIS measure results

    Returns:
        Tuple of (completeness_score, breakdown_counts)
    """
    if not measure_results:
        return 0.0, {}

    counts = {
        "total": 0,
        "numerator": 0,
        "denominator_only": 0,
        "excluded": 0,
        "not_applicable": 0,
    }

    for measure_code, result in measure_results.items():
        if not isinstance(result, dict):
            continue

        counts["total"] += 1
        score = result.get("score", "not_applicable")

        if score == "numerator":
            counts["numerator"] += 1
        elif score == "denominator_only":
            counts["denominator_only"] += 1
        elif score == "excluded":
            counts["excluded"] += 1
        else:
            counts["not_applicable"] += 1

    # Completeness = numerator / (numerator + denominator_only)
    applicable = counts["numerator"] + counts["denominator_only"]
    if applicable > 0:
        completeness = counts["numerator"] / applicable
    else:
        completeness = 0.0

    return round(completeness, 2), counts


# ============================================================================
# Confidence Scoring Functions
# ============================================================================

def calculate_extraction_confidence(
    diagnoses: List[str],
    vitals: Dict[str, str],
    labs: Dict[str, str],
    screenings: Dict[str, bool],
    note_text: str
) -> Tuple[float, List[str], int]:
    """
    Calculate confidence in entity extraction quality.

    Args:
        diagnoses: Extracted diagnoses
        vitals: Extracted vital signs
        labs: Extracted lab results
        screenings: Extracted screening indicators
        note_text: Original clinical note

    Returns:
        Tuple of (confidence_score, warnings, total_extracted)
    """
    warnings = []
    total_extracted = len(diagnoses) + len(vitals) + len(labs) + len(screenings)

    # Base confidence starts high
    confidence = 1.0

    # Check if note is too short (may miss entities)
    if len(note_text) < 50:
        warnings.append("Very short clinical note - extraction may be incomplete")
        confidence *= 0.7
    elif len(note_text) < 100:
        warnings.append("Short clinical note - may lack comprehensive data")
        confidence *= 0.85

    # Check if no entities extracted from reasonable-length note
    if total_extracted == 0 and len(note_text) > 100:
        warnings.append("No clinical entities extracted - note may be ambiguous or non-clinical")
        confidence = 0.2

    # Check if extraction seems sparse
    elif total_extracted < 3 and len(note_text) > 200:
        warnings.append("Low entity extraction from substantial note - may miss important data")
        confidence *= 0.8

    # Bonus for rich extraction
    if total_extracted >= 10:
        confidence = min(1.0, confidence * 1.1)

    # Check for missing critical vitals/labs in certain contexts
    note_lower = note_text.lower()
    if any(kw in note_lower for kw in ["hypertension", "htn", "blood pressure"]):
        if "BP" not in vitals:
            warnings.append("Hypertension mentioned but BP not extracted")
            confidence *= 0.9

    if any(kw in note_lower for kw in ["diabetes", "diabetic", "dm"]):
        if "HbA1c" not in labs:
            warnings.append("Diabetes mentioned but HbA1c not extracted")
            confidence *= 0.9

    return round(confidence, 3), warnings, total_extracted


def calculate_parsing_confidence(
    vitals: Dict[str, str],
    labs: Dict[str, str]
) -> Tuple[float, List[str], int]:
    """
    Calculate confidence in value parsing (did extracted values parse correctly).

    Args:
        vitals: Extracted vital signs
        labs: Extracted lab results

    Returns:
        Tuple of (confidence_score, warnings, failed_count)
    """
    warnings = []
    failed_count = 0
    total_parseable = 0

    # Check vital sign parsing
    if "BP" in vitals:
        total_parseable += 1
        systolic, diastolic = parse_blood_pressure(vitals["BP"])
        if systolic is None or diastolic is None:
            failed_count += 1
            warnings.append(f"Unable to parse BP value: '{vitals['BP']}' (expected format: ###/##)")

    if "BMI" in vitals:
        total_parseable += 1
        bmi = parse_bmi(vitals["BMI"])
        if bmi is None:
            failed_count += 1
            warnings.append(f"Unable to parse BMI value: '{vitals['BMI']}' (expected numeric value)")

    # Check lab parsing
    if "HbA1c" in labs:
        total_parseable += 1
        hba1c = parse_hba1c(labs["HbA1c"])
        if hba1c is None:
            failed_count += 1
            warnings.append(f"Unable to parse HbA1c value: '{labs['HbA1c']}' (expected format: #.#% or #.#)")

    # Calculate confidence
    if total_parseable == 0:
        confidence = 1.0  # No values to parse = 100% success rate
    else:
        success_rate = (total_parseable - failed_count) / total_parseable
        confidence = success_rate

    return round(confidence, 3), warnings, failed_count


def calculate_measure_confidence(
    measure_results: Dict[str, Dict]
) -> Tuple[float, List[str], int, int]:
    """
    Calculate confidence in HEDIS measure evaluations.

    Args:
        measure_results: Dict of HEDIS measure evaluation results

    Returns:
        Tuple of (confidence_score, warnings, evaluated_count, excluded_count)
    """
    warnings = []
    evaluated_count = len(measure_results)
    excluded_count = 0
    partial_documented = 0
    unable_to_parse = 0

    for measure_code, result in measure_results.items():
        if not isinstance(result, dict):
            continue

        # Count exclusions
        if result.get("score") == "excluded":
            excluded_count += 1

        # Count partial documentation
        if result.get("documented") == "partial":
            partial_documented += 1
            warnings.append(f"{measure_code}: Partial documentation - {result.get('status', 'unknown')}")

        # Count parsing failures
        if result.get("status") == "Unable to Parse":
            unable_to_parse += 1
            warnings.append(f"{measure_code}: Unable to parse value")

    # Calculate confidence
    confidence = 1.0

    # Reduce confidence for partial documentation
    if evaluated_count > 0:
        partial_rate = partial_documented / evaluated_count
        if partial_rate > 0.3:  # More than 30% partial
            warnings.append(f"High rate of partial documentation ({partial_documented}/{evaluated_count} measures)")
            confidence *= (1 - partial_rate * 0.5)

    # Reduce confidence for parsing failures
    if evaluated_count > 0:
        parse_fail_rate = unable_to_parse / evaluated_count
        if parse_fail_rate > 0:
            confidence *= (1 - parse_fail_rate * 0.7)

    return round(confidence, 3), warnings, evaluated_count, excluded_count


def calculate_overall_confidence(
    extraction_confidence: float,
    parsing_confidence: float,
    measure_confidence: float
) -> float:
    """
    Calculate overall evaluation confidence.

    Args:
        extraction_confidence: Entity extraction confidence
        parsing_confidence: Value parsing confidence
        measure_confidence: Measure evaluation confidence

    Returns:
        Overall confidence score (0.0-1.0)
    """
    # Weighted average - extraction is most important
    weights = {
        "extraction": 0.4,
        "parsing": 0.3,
        "measure": 0.3,
    }

    overall = (
        extraction_confidence * weights["extraction"] +
        parsing_confidence * weights["parsing"] +
        measure_confidence * weights["measure"]
    )

    return round(overall, 3)


# ============================================================================
# Revenue Scoring Functions
# ============================================================================

def calculate_revenue_capture_rate(
    documented_revenue: float,
    potential_revenue: float
) -> float:
    """
    Calculate revenue capture rate.

    Args:
        documented_revenue: Revenue from documented items
        potential_revenue: Total potential revenue

    Returns:
        Capture rate as percentage (0.0-100.0)
    """
    if potential_revenue <= 0:
        return 0.0

    return round((documented_revenue / potential_revenue) * 100, 1)


def prioritize_revenue_gap(
    estimated_cost: float,
    required: bool,
    evidence_grade: str,
    severity: str
) -> str:
    """
    Determine priority of a revenue gap.

    Args:
        estimated_cost: Estimated revenue opportunity
        required: Whether test is clinically required
        evidence_grade: Evidence grade (A, B, C, D)
        severity: Clinical severity level

    Returns:
        Priority string: "high", "medium", or "low"
    """
    # High priority: Required tests with Grade A evidence
    if required and evidence_grade == 'A':
        return "high"

    # High priority: Expensive tests (>$100) that are required
    if required and estimated_cost > 100:
        return "high"

    # High priority: SEP-1 bundle for severe cases
    if severity == "severe" and required:
        return "high"

    # Medium priority: Required tests with Grade B evidence
    if required and evidence_grade == 'B':
        return "medium"

    # Medium priority: Optional tests with Grade A evidence and high cost
    if evidence_grade == 'A' and estimated_cost > 50:
        return "medium"

    # Low priority: Everything else
    return "low"


# ============================================================================
# E/M Coding Scoring
# ============================================================================

def calculate_em_level(
    history_level: str,
    exam_level: str,
    mdm_level: str
) -> int:
    """
    Calculate E/M level based on documentation components.

    Uses 2021 E/M guidelines which prioritize MDM.

    Args:
        history_level: History documentation level
        exam_level: Exam documentation level
        mdm_level: Medical decision making level

    Returns:
        E/M level (1-5)
    """
    # MDM level mapping (2021 guidelines prioritize MDM)
    mdm_to_level = {
        'straightforward': 1,
        'low': 2,
        'moderate': 3,
        'high': 4,
    }

    # Default to MDM-based level
    level = mdm_to_level.get(mdm_level.lower(), 2)

    # Can be reduced if history/exam are insufficient
    level_mapping = {
        'problem_focused': 1,
        'expanded_problem_focused': 2,
        'detailed': 3,
        'comprehensive': 4,
        'insufficient': 1,
    }

    history_level_num = level_mapping.get(history_level.lower(), 2)
    exam_level_num = level_mapping.get(exam_level.lower(), 2)

    # Use minimum of MDM level and supporting documentation
    supporting_level = min(history_level_num, exam_level_num)

    # MDM can only be one level higher than supporting documentation
    final_level = min(level, supporting_level + 1)

    return max(1, min(5, final_level))
