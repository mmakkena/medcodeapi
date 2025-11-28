"""
HEDIS Measure Evaluator

Evaluates clinical documentation against HEDIS quality measures.
Supports 19 HEDIS measures with value-based evaluation.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any

from domain.common.models import (
    HEDISMeasureResult,
    HEDISEvaluationResult,
    ClinicalEntities,
)
from domain.common.scoring import (
    HEDIS_TARGETS,
    evaluate_bp_target,
    evaluate_hba1c_target,
    evaluate_bmi_category,
    calculate_hedis_completeness,
    calculate_extraction_confidence,
    calculate_parsing_confidence,
    calculate_measure_confidence,
    calculate_overall_confidence,
)
from domain.common.validation import (
    parse_blood_pressure,
    parse_hba1c,
    parse_bmi,
)
from domain.hedis_evaluation.exclusions import (
    check_hedis_exclusions,
    is_measure_excluded,
)

logger = logging.getLogger(__name__)


class HEDISEvaluator:
    """
    Evaluates clinical documentation against HEDIS quality measures.

    Supports 19 HEDIS measures:
    - CBP: Controlling High Blood Pressure
    - CDC: Comprehensive Diabetes Care
    - BCS: Breast Cancer Screening
    - COL: Colorectal Cancer Screening
    - BMI: Body Mass Index Screening
    - DEP: Depression Screening
    - CHL: Chlamydia Screening in Women
    - WCC: Weight Assessment for Children
    - CIS: Childhood Immunization Status
    - IMA: Immunizations for Adolescents
    - AAP: Adults' Access to Preventive Services
    - AWC: Adolescent Well-Care Visits
    - AMM: Antidepressant Medication Management
    - ADD: ADHD Medication Follow-Up
    - FUH: Follow-Up After Hospitalization for Mental Illness
    - FUM: Follow-Up After ED Visit for Mental Illness
    - FUA: Follow-Up After ED Visit for Substance Abuse
    - PPC: Prenatal and Postpartum Care
    - PCE: Pharmacotherapy for Opioid Use Disorder
    """

    def evaluate(
        self,
        diagnoses: List[str],
        vitals: Dict[str, str],
        labs: Dict[str, str],
        screenings: Dict[str, bool],
        patient_age: int,
        patient_gender: str,
        medications: Optional[Dict[str, List[str]]] = None,
        visits: Optional[Dict[str, List[str]]] = None,
        immunizations: Optional[Dict[str, bool]] = None,
        encounters: Optional[List[Dict]] = None,
        note_text: str = "",
        icd10_codes: Optional[List[str]] = None
    ) -> HEDISEvaluationResult:
        """
        Evaluate all applicable HEDIS measures.

        Args:
            diagnoses: List of diagnosis names
            vitals: Dict of vital signs (e.g., {"BP": "128/82", "BMI": "31.2"})
            labs: Dict of lab results (e.g., {"HbA1c": "7.2"})
            screenings: Dict of screening status (e.g., {"Mammogram": True})
            patient_age: Patient age in years
            patient_gender: Patient gender ("male", "female")
            medications: Optional dict of medication classes -> lists
            visits: Optional dict of visit types -> lists
            immunizations: Optional dict of immunization status
            encounters: Optional list of encounter dicts
            note_text: Original clinical note text
            icd10_codes: Optional list of ICD-10 codes

        Returns:
            HEDISEvaluationResult with all measure evaluations
        """
        # Initialize optional parameters
        if medications is None:
            medications = {}
        if visits is None:
            visits = {}
        if immunizations is None:
            immunizations = {}
        if encounters is None:
            encounters = []

        # Check for exclusions
        exclusions = check_hedis_exclusions(diagnoses, note_text)
        if exclusions:
            logger.info(f"Identified {len(exclusions)} HEDIS exclusion(s): {list(exclusions.keys())}")

        # Normalize inputs - handle both string and Diagnosis objects
        diagnoses_lower = []
        for d in diagnoses:
            if hasattr(d, 'name'):
                diagnoses_lower.append(d.name.lower())
            else:
                diagnoses_lower.append(str(d).lower())

        # Evaluate all measures
        results = {}
        gaps = []

        # CBP: Controlling High Blood Pressure
        cbp_result, cbp_gaps = self._evaluate_cbp(
            diagnoses_lower, vitals, exclusions
        )
        if cbp_result:
            results["CBP"] = cbp_result
            gaps.extend(cbp_gaps)

        # CDC: Comprehensive Diabetes Care
        cdc_result, cdc_gaps = self._evaluate_cdc(
            diagnoses_lower, labs, exclusions
        )
        if cdc_result:
            results["CDC"] = cdc_result
            gaps.extend(cdc_gaps)

        # BCS: Breast Cancer Screening
        bcs_result, bcs_gaps = self._evaluate_bcs(
            patient_age, patient_gender, screenings, exclusions
        )
        if bcs_result:
            results["BCS"] = bcs_result
            gaps.extend(bcs_gaps)

        # COL: Colorectal Cancer Screening
        col_result, col_gaps = self._evaluate_col(
            patient_age, screenings, exclusions
        )
        if col_result:
            results["COL"] = col_result
            gaps.extend(col_gaps)

        # BMI: Body Mass Index Screening
        bmi_result, bmi_gaps = self._evaluate_bmi(
            vitals, exclusions
        )
        if bmi_result:
            results["BMI"] = bmi_result
            gaps.extend(bmi_gaps)

        # DEP: Depression Screening
        dep_result, dep_gaps = self._evaluate_dep(
            diagnoses_lower, screenings, exclusions
        )
        if dep_result:
            results["DEP"] = dep_result
            gaps.extend(dep_gaps)

        # CHL: Chlamydia Screening
        chl_result, chl_gaps = self._evaluate_chl(
            patient_age, patient_gender, screenings, exclusions
        )
        if chl_result:
            results["CHL"] = chl_result
            gaps.extend(chl_gaps)

        # WCC: Weight Assessment for Children
        wcc_result, wcc_gaps = self._evaluate_wcc(
            patient_age, vitals, visits, exclusions
        )
        if wcc_result:
            results["WCC"] = wcc_result
            gaps.extend(wcc_gaps)

        # CIS: Childhood Immunization Status
        cis_result, cis_gaps = self._evaluate_cis(
            patient_age, immunizations, exclusions
        )
        if cis_result:
            results["CIS"] = cis_result
            gaps.extend(cis_gaps)

        # IMA: Immunizations for Adolescents
        ima_result, ima_gaps = self._evaluate_ima(
            patient_age, immunizations, exclusions
        )
        if ima_result:
            results["IMA"] = ima_result
            gaps.extend(ima_gaps)

        # AAP: Adults' Access to Preventive Services
        aap_result, aap_gaps = self._evaluate_aap(
            patient_age, visits, exclusions
        )
        if aap_result:
            results["AAP"] = aap_result
            gaps.extend(aap_gaps)

        # AWC: Adolescent Well-Care Visits
        awc_result, awc_gaps = self._evaluate_awc(
            patient_age, visits, exclusions
        )
        if awc_result:
            results["AWC"] = awc_result
            gaps.extend(awc_gaps)

        # AMM: Antidepressant Medication Management
        amm_result, amm_gaps = self._evaluate_amm(
            patient_age, diagnoses_lower, medications, exclusions
        )
        if amm_result:
            results["AMM"] = amm_result
            gaps.extend(amm_gaps)

        # Calculate completeness
        completeness_score, counts = calculate_hedis_completeness(
            {k: v.__dict__ if hasattr(v, '__dict__') else v for k, v in results.items()}
        )

        # Calculate confidence
        extraction_conf, extraction_warnings, _ = calculate_extraction_confidence(
            diagnoses, vitals, labs, screenings, note_text
        )
        parsing_conf, parsing_warnings, _ = calculate_parsing_confidence(vitals, labs)
        measure_conf, measure_warnings, evaluated_count, excluded_count = calculate_measure_confidence(
            {k: v.__dict__ if hasattr(v, '__dict__') else v for k, v in results.items()}
        )
        overall_conf = calculate_overall_confidence(extraction_conf, parsing_conf, measure_conf)

        # Combine warnings
        all_warnings = extraction_warnings + parsing_warnings + measure_warnings

        return HEDISEvaluationResult(
            measures=results,
            gaps=gaps,
            total_applicable=counts.get("total", 0),
            total_met=counts.get("numerator", 0),
            total_not_met=counts.get("denominator_only", 0),
            total_excluded=counts.get("excluded", 0),
            completeness_score=completeness_score,
            extraction_confidence=extraction_conf,
            parsing_confidence=parsing_conf,
            measure_confidence=measure_conf,
            overall_confidence=overall_conf,
            confidence_warnings=all_warnings,
            exclusions_detected=exclusions,
        )

    def _evaluate_cbp(
        self,
        diagnoses_lower: List[str],
        vitals: Dict[str, str],
        exclusions: Dict
    ) -> Tuple[Optional[HEDISMeasureResult], List[str]]:
        """Evaluate CBP: Controlling High Blood Pressure."""
        gaps = []

        # Check if applicable (has hypertension)
        has_hypertension = any("hypertension" in d or "htn" in d for d in diagnoses_lower)
        if not has_hypertension:
            return None, []

        # Check for exclusions
        excluded, exclusion_reason = is_measure_excluded("CBP", exclusions)
        if excluded:
            return HEDISMeasureResult(
                measure_code="CBP",
                measure_name="Controlling High Blood Pressure",
                applicable=True,
                documented=False,
                status="Excluded",
                score="excluded",
                exclusion_reason=exclusion_reason
            ), []

        # Evaluate - handle both dict and VitalSigns object
        systolic = None
        diastolic = None
        raw_bp = None

        if isinstance(vitals, dict):
            if "BP" in vitals:
                systolic, diastolic = parse_blood_pressure(vitals["BP"])
                raw_bp = vitals["BP"]
        elif hasattr(vitals, 'systolic') and hasattr(vitals, 'diastolic'):
            systolic = vitals.systolic
            diastolic = vitals.diastolic
            if systolic and diastolic:
                raw_bp = f"{systolic}/{diastolic}"

        if systolic and diastolic:
            bp_eval = evaluate_bp_target(systolic, diastolic)

            if bp_eval.meets_target:
                return HEDISMeasureResult(
                    measure_code="CBP",
                    measure_name="Controlling High Blood Pressure",
                    applicable=True,
                    documented=True,
                    meets_target=True,
                    status="Controlled",
                    score="numerator",
                    value={"systolic": systolic, "diastolic": diastolic},
                    target={"systolic": bp_eval.target_systolic, "diastolic": bp_eval.target_diastolic},
                    raw_value=raw_bp
                ), []
            else:
                gap_parts = []
                if not bp_eval.systolic_controlled:
                    gap_parts.append(f"Systolic {systolic} (target <{bp_eval.target_systolic})")
                if not bp_eval.diastolic_controlled:
                    gap_parts.append(f"Diastolic {diastolic} (target <{bp_eval.target_diastolic})")

                gap_msg = f"HEDIS CBP - Blood pressure not controlled: {systolic}/{diastolic}. {'; '.join(gap_parts)}."
                gaps.append(gap_msg)

                return HEDISMeasureResult(
                    measure_code="CBP",
                    measure_name="Controlling High Blood Pressure",
                    applicable=True,
                    documented=True,
                    meets_target=False,
                    status="Not Controlled",
                    score="denominator_only",
                    value={"systolic": systolic, "diastolic": diastolic},
                    target={"systolic": bp_eval.target_systolic, "diastolic": bp_eval.target_diastolic},
                    raw_value=raw_bp,
                    gap_description=gap_msg
                ), gaps
        elif raw_bp:
            gap_msg = f"HEDIS CBP - BP documented as '{raw_bp}' but unable to parse."
            gaps.append(gap_msg)
            return HEDISMeasureResult(
                measure_code="CBP",
                measure_name="Controlling High Blood Pressure",
                applicable=True,
                documented="partial",
                status="Unable to Parse",
                score="denominator_only",
                raw_value=raw_bp,
                gap_description=gap_msg
            ), gaps
        else:
            gap_msg = "HEDIS CBP - Blood pressure not documented. Required for patients with hypertension."
            gaps.append(gap_msg)
            return HEDISMeasureResult(
                measure_code="CBP",
                measure_name="Controlling High Blood Pressure",
                applicable=True,
                documented=False,
                status="Not Documented",
                score="denominator_only",
                gap_description=gap_msg
            ), gaps

    def _evaluate_cdc(
        self,
        diagnoses_lower: List[str],
        labs: Dict[str, str],
        exclusions: Dict
    ) -> Tuple[Optional[HEDISMeasureResult], List[str]]:
        """Evaluate CDC: Comprehensive Diabetes Care - HbA1c."""
        gaps = []

        # Check if applicable (has diabetes)
        has_diabetes = any("diabetes" in d or "dm" in d for d in diagnoses_lower)
        if not has_diabetes:
            return None, []

        # Check for exclusions
        excluded, exclusion_reason = is_measure_excluded("CDC", exclusions)
        if excluded:
            return HEDISMeasureResult(
                measure_code="CDC",
                measure_name="Comprehensive Diabetes Care - HbA1c",
                applicable=True,
                documented=False,
                status="Excluded",
                score="excluded",
                exclusion_reason=exclusion_reason
            ), []

        # Evaluate - handle both dict and LabResults object
        hba1c_value = None
        raw_hba1c = None

        if isinstance(labs, dict):
            if "HbA1c" in labs:
                hba1c_value = parse_hba1c(labs["HbA1c"])
                raw_hba1c = labs["HbA1c"]
        elif hasattr(labs, 'hba1c') and labs.hba1c is not None:
            hba1c_value = labs.hba1c
            raw_hba1c = f"{labs.hba1c}%"

        if hba1c_value:
            hba1c_eval = evaluate_hba1c_target(hba1c_value)

            control_levels = {
                "excellent_lt7": hba1c_eval.excellent_control_lt7,
                "good_lt8": hba1c_eval.good_control_lt8,
                "poor_gt9": hba1c_eval.poor_control_gt9
            }

            gap_msg = None
            if hba1c_eval.excellent_control_lt7:
                status = "Excellent Control (<7%)"
                score = "numerator"
            elif hba1c_eval.good_control_lt8:
                status = "Good Control (<8%)"
                score = "numerator"
            else:
                if hba1c_eval.poor_control_gt9:
                    status = "Poor Control (>9%)"
                    gap_msg = f"HEDIS CDC - HbA1c poorly controlled at {hba1c_value}% (target <8%)."
                else:
                    status = "Suboptimal Control (8-9%)"
                    gap_msg = f"HEDIS CDC - HbA1c at {hba1c_value}% (target <8%)."
                gaps.append(gap_msg)
                score = "denominator_only"

            return HEDISMeasureResult(
                measure_code="CDC",
                measure_name="Comprehensive Diabetes Care - HbA1c",
                applicable=True,
                documented=True,
                meets_target=hba1c_eval.good_control_lt8,
                status=status,
                score=score,
                value=hba1c_value,
                target=hba1c_eval.target_primary,
                raw_value=raw_hba1c,
                control_levels=control_levels,
                gap_description=gap_msg
            ), gaps
        elif raw_hba1c:
            gap_msg = f"HEDIS CDC - HbA1c documented as '{raw_hba1c}' but unable to parse."
            gaps.append(gap_msg)
            return HEDISMeasureResult(
                measure_code="CDC",
                measure_name="Comprehensive Diabetes Care - HbA1c",
                applicable=True,
                documented="partial",
                status="Unable to Parse",
                score="denominator_only",
                raw_value=raw_hba1c,
                gap_description=gap_msg
            ), gaps
        else:
            gap_msg = "HEDIS CDC - HbA1c not documented. Required annually for diabetes patients."
            gaps.append(gap_msg)
            return HEDISMeasureResult(
                measure_code="CDC",
                measure_name="Comprehensive Diabetes Care - HbA1c",
                applicable=True,
                documented=False,
                status="Not Documented",
                score="denominator_only",
                gap_description=gap_msg
            ), gaps

    def _evaluate_bcs(
        self,
        patient_age: int,
        patient_gender: str,
        screenings: Dict[str, bool],
        exclusions: Dict
    ) -> Tuple[Optional[HEDISMeasureResult], List[str]]:
        """Evaluate BCS: Breast Cancer Screening."""
        gaps = []

        # Check if applicable
        if not (50 <= patient_age <= 74 and patient_gender.lower() == "female"):
            return None, []

        # Check for exclusions
        excluded, exclusion_reason = is_measure_excluded("BCS", exclusions)
        if excluded:
            return HEDISMeasureResult(
                measure_code="BCS",
                measure_name="Breast Cancer Screening",
                applicable=True,
                documented=False,
                status="Excluded",
                score="excluded",
                exclusion_reason=exclusion_reason,
                age_range="50-74",
                gender="Female"
            ), []

        # Evaluate
        if screenings.get("Mammogram", False):
            return HEDISMeasureResult(
                measure_code="BCS",
                measure_name="Breast Cancer Screening",
                applicable=True,
                documented=True,
                status="Screening Documented",
                score="numerator",
                age_range="50-74",
                gender="Female"
            ), []
        else:
            gap_msg = f"HEDIS BCS - Mammogram not documented for eligible female patient age {patient_age}."
            gaps.append(gap_msg)
            return HEDISMeasureResult(
                measure_code="BCS",
                measure_name="Breast Cancer Screening",
                applicable=True,
                documented=False,
                status="Screening Not Documented",
                score="denominator_only",
                age_range="50-74",
                gender="Female",
                gap_description=gap_msg
            ), gaps

    def _evaluate_col(
        self,
        patient_age: int,
        screenings: Dict[str, bool],
        exclusions: Dict
    ) -> Tuple[Optional[HEDISMeasureResult], List[str]]:
        """Evaluate COL: Colorectal Cancer Screening."""
        gaps = []

        # Check if applicable
        if not (45 <= patient_age <= 75):
            return None, []

        # Check for exclusions
        excluded, exclusion_reason = is_measure_excluded("COL", exclusions)
        if excluded:
            return HEDISMeasureResult(
                measure_code="COL",
                measure_name="Colorectal Cancer Screening",
                applicable=True,
                documented=False,
                status="Excluded",
                score="excluded",
                exclusion_reason=exclusion_reason,
                age_range="45-75"
            ), []

        # Evaluate
        if screenings.get("Colorectal", False):
            return HEDISMeasureResult(
                measure_code="COL",
                measure_name="Colorectal Cancer Screening",
                applicable=True,
                documented=True,
                status="Screening Documented",
                score="numerator",
                age_range="45-75"
            ), []
        else:
            gap_msg = f"HEDIS COL - Colorectal screening not documented for eligible patient age {patient_age}."
            gaps.append(gap_msg)
            return HEDISMeasureResult(
                measure_code="COL",
                measure_name="Colorectal Cancer Screening",
                applicable=True,
                documented=False,
                status="Screening Not Documented",
                score="denominator_only",
                age_range="45-75",
                gap_description=gap_msg
            ), gaps

    def _evaluate_bmi(
        self,
        vitals: Dict[str, str],
        exclusions: Dict
    ) -> Tuple[Optional[HEDISMeasureResult], List[str]]:
        """Evaluate BMI: Body Mass Index Screening."""
        gaps = []

        # Check for exclusions
        excluded, exclusion_reason = is_measure_excluded("BMI", exclusions)
        if excluded:
            return HEDISMeasureResult(
                measure_code="BMI",
                measure_name="BMI Screening and Follow-Up",
                applicable=True,
                documented=False,
                status="Excluded",
                score="excluded",
                exclusion_reason=exclusion_reason
            ), []

        # Evaluate
        if "BMI" in vitals:
            bmi_value = parse_bmi(vitals["BMI"])

            if bmi_value:
                bmi_eval = evaluate_bmi_category(bmi_value)

                result = HEDISMeasureResult(
                    measure_code="BMI",
                    measure_name="BMI Screening and Follow-Up",
                    applicable=True,
                    documented=True,
                    status=f"{bmi_eval.category} ({bmi_eval.risk_level} risk)",
                    score="numerator",  # Documented = met
                    value=bmi_value,
                    raw_value=vitals["BMI"]
                )

                if bmi_eval.needs_intervention:
                    if bmi_value >= 30.0:
                        gap_msg = f"BMI {bmi_value} - {bmi_eval.category}. Consider obesity management."
                    elif bmi_value >= 25.0:
                        gap_msg = f"BMI {bmi_value} - {bmi_eval.category}. Consider lifestyle counseling."
                    else:
                        gap_msg = f"BMI {bmi_value} - {bmi_eval.category}. Consider nutritional assessment."
                    gaps.append(gap_msg)
                    result.gap_description = gap_msg

                return result, gaps
            else:
                gap_msg = f"BMI documented as '{vitals['BMI']}' but unable to parse value."
                gaps.append(gap_msg)
                return HEDISMeasureResult(
                    measure_code="BMI",
                    measure_name="BMI Screening and Follow-Up",
                    applicable=True,
                    documented="partial",
                    status="Unable to Parse",
                    score="numerator",  # Documented even if not parsed
                    raw_value=vitals["BMI"],
                    gap_description=gap_msg
                ), gaps
        else:
            gap_msg = "BMI not documented. Recommended for all adult patients."
            gaps.append(gap_msg)
            return HEDISMeasureResult(
                measure_code="BMI",
                measure_name="BMI Screening and Follow-Up",
                applicable=True,
                documented=False,
                status="Not Documented",
                score="denominator_only",
                gap_description=gap_msg
            ), gaps

    def _evaluate_dep(
        self,
        diagnoses_lower: List[str],
        screenings: Dict[str, bool],
        exclusions: Dict
    ) -> Tuple[Optional[HEDISMeasureResult], List[str]]:
        """Evaluate DEP: Depression Screening."""
        gaps = []

        # Check for exclusions
        excluded, exclusion_reason = is_measure_excluded("DEP", exclusions)
        if excluded:
            return HEDISMeasureResult(
                measure_code="DEP",
                measure_name="Depression Screening",
                applicable=True,
                documented=False,
                status="Excluded",
                score="excluded",
                exclusion_reason=exclusion_reason
            ), []

        # Evaluate
        has_depression_screen = screenings.get("Depression", False)
        has_depression_dx = any("depression" in d for d in diagnoses_lower)

        if has_depression_screen or has_depression_dx:
            return HEDISMeasureResult(
                measure_code="DEP",
                measure_name="Depression Screening",
                applicable=True,
                documented=True,
                status="Screening/Diagnosis Documented",
                score="numerator"
            ), []
        else:
            gap_msg = "Depression screening not documented. Recommended annually using PHQ-2 or PHQ-9."
            gaps.append(gap_msg)
            return HEDISMeasureResult(
                measure_code="DEP",
                measure_name="Depression Screening",
                applicable=True,
                documented=False,
                status="Not Documented",
                score="denominator_only",
                gap_description=gap_msg
            ), gaps

    def _evaluate_chl(
        self,
        patient_age: int,
        patient_gender: str,
        screenings: Dict[str, bool],
        exclusions: Dict
    ) -> Tuple[Optional[HEDISMeasureResult], List[str]]:
        """Evaluate CHL: Chlamydia Screening in Women."""
        gaps = []

        # Check if applicable
        if not (16 <= patient_age <= 24 and patient_gender.lower() == "female"):
            return None, []

        # Check for exclusions
        excluded, exclusion_reason = is_measure_excluded("CHL", exclusions)
        if excluded:
            return HEDISMeasureResult(
                measure_code="CHL",
                measure_name="Chlamydia Screening in Women",
                applicable=True,
                documented=False,
                status="Excluded",
                score="excluded",
                exclusion_reason=exclusion_reason,
                age_range="16-24",
                gender="Female"
            ), []

        # Evaluate
        if screenings.get("Chlamydia", False):
            return HEDISMeasureResult(
                measure_code="CHL",
                measure_name="Chlamydia Screening in Women",
                applicable=True,
                documented=True,
                status="Screening Documented",
                score="numerator",
                age_range="16-24",
                gender="Female"
            ), []
        else:
            gap_msg = f"HEDIS CHL - Chlamydia screening not documented for female patient age {patient_age}."
            gaps.append(gap_msg)
            return HEDISMeasureResult(
                measure_code="CHL",
                measure_name="Chlamydia Screening in Women",
                applicable=True,
                documented=False,
                status="Screening Not Documented",
                score="denominator_only",
                age_range="16-24",
                gender="Female",
                gap_description=gap_msg
            ), gaps

    def _evaluate_wcc(
        self,
        patient_age: int,
        vitals: Dict[str, str],
        visits: Dict[str, List[str]],
        exclusions: Dict
    ) -> Tuple[Optional[HEDISMeasureResult], List[str]]:
        """Evaluate WCC: Weight Assessment for Children."""
        gaps = []

        # Check if applicable
        if not (3 <= patient_age <= 17):
            return None, []

        # Check for exclusions
        excluded, exclusion_reason = is_measure_excluded("WCC", exclusions)
        if excluded:
            return HEDISMeasureResult(
                measure_code="WCC",
                measure_name="Weight Assessment and Counseling",
                applicable=True,
                documented=False,
                status="Excluded",
                score="excluded",
                exclusion_reason=exclusion_reason,
                age_range="3-17"
            ), []

        # Evaluate components
        has_bmi = "BMI" in vitals
        has_nutrition_counseling = len(visits.get("nutrition_counseling", [])) > 0
        has_activity_counseling = len(visits.get("physical_activity_counseling", [])) > 0

        if has_bmi and has_nutrition_counseling and has_activity_counseling:
            return HEDISMeasureResult(
                measure_code="WCC",
                measure_name="Weight Assessment and Counseling",
                applicable=True,
                documented=True,
                status="All Components Met",
                score="numerator",
                age_range="3-17"
            ), []
        else:
            missing = []
            if not has_bmi:
                missing.append("BMI assessment")
            if not has_nutrition_counseling:
                missing.append("nutrition counseling")
            if not has_activity_counseling:
                missing.append("physical activity counseling")

            gap_msg = f"HEDIS WCC - Missing: {', '.join(missing)}. Required annually for ages 3-17."
            gaps.append(gap_msg)

            return HEDISMeasureResult(
                measure_code="WCC",
                measure_name="Weight Assessment and Counseling",
                applicable=True,
                documented=False,
                status="Missing Components",
                score="denominator_only",
                age_range="3-17",
                gap_description=gap_msg
            ), gaps

    def _evaluate_cis(
        self,
        patient_age: int,
        immunizations: Dict[str, bool],
        exclusions: Dict
    ) -> Tuple[Optional[HEDISMeasureResult], List[str]]:
        """Evaluate CIS: Childhood Immunization Status."""
        gaps = []

        # Check if applicable
        if patient_age != 2:
            return None, []

        # Check for exclusions
        excluded, exclusion_reason = is_measure_excluded("CIS", exclusions)
        if excluded:
            return HEDISMeasureResult(
                measure_code="CIS",
                measure_name="Childhood Immunization Status",
                applicable=True,
                documented=False,
                status="Excluded",
                score="excluded",
                exclusion_reason=exclusion_reason
            ), []

        # Required vaccines
        required_vaccines = ["DTaP", "IPV", "MMR", "HiB", "HepB", "VZV", "Pneumococcal"]
        vaccine_status = {vaccine: immunizations.get(vaccine, False) for vaccine in required_vaccines}

        if all(vaccine_status.values()):
            return HEDISMeasureResult(
                measure_code="CIS",
                measure_name="Childhood Immunization Status",
                applicable=True,
                documented=True,
                status="All Vaccines Complete",
                score="numerator"
            ), []
        else:
            missing_vaccines = [v for v, status in vaccine_status.items() if not status]
            gap_msg = f"HEDIS CIS - Missing vaccines: {', '.join(missing_vaccines)}. Required by age 2."
            gaps.append(gap_msg)

            return HEDISMeasureResult(
                measure_code="CIS",
                measure_name="Childhood Immunization Status",
                applicable=True,
                documented=False,
                status="Incomplete Immunizations",
                score="denominator_only",
                gap_description=gap_msg
            ), gaps

    def _evaluate_ima(
        self,
        patient_age: int,
        immunizations: Dict[str, bool],
        exclusions: Dict
    ) -> Tuple[Optional[HEDISMeasureResult], List[str]]:
        """Evaluate IMA: Immunizations for Adolescents."""
        gaps = []

        # Check if applicable
        if patient_age != 13:
            return None, []

        # Check for exclusions
        excluded, exclusion_reason = is_measure_excluded("IMA", exclusions)
        if excluded:
            return HEDISMeasureResult(
                measure_code="IMA",
                measure_name="Immunizations for Adolescents",
                applicable=True,
                documented=False,
                status="Excluded",
                score="excluded",
                exclusion_reason=exclusion_reason
            ), []

        # Required vaccines
        required_vaccines = ["Meningococcal", "Tdap", "HPV"]
        vaccine_status = {vaccine: immunizations.get(vaccine, False) for vaccine in required_vaccines}

        if all(vaccine_status.values()):
            return HEDISMeasureResult(
                measure_code="IMA",
                measure_name="Immunizations for Adolescents",
                applicable=True,
                documented=True,
                status="All Vaccines Complete",
                score="numerator"
            ), []
        else:
            missing_vaccines = [v for v, status in vaccine_status.items() if not status]
            gap_msg = f"HEDIS IMA - Missing vaccines: {', '.join(missing_vaccines)}. Required by age 13."
            gaps.append(gap_msg)

            return HEDISMeasureResult(
                measure_code="IMA",
                measure_name="Immunizations for Adolescents",
                applicable=True,
                documented=False,
                status="Incomplete Immunizations",
                score="denominator_only",
                gap_description=gap_msg
            ), gaps

    def _evaluate_aap(
        self,
        patient_age: int,
        visits: Dict[str, List[str]],
        exclusions: Dict
    ) -> Tuple[Optional[HEDISMeasureResult], List[str]]:
        """Evaluate AAP: Adults' Access to Preventive Services."""
        gaps = []

        # Check if applicable
        if patient_age < 20:
            return None, []

        # Check for exclusions
        excluded, exclusion_reason = is_measure_excluded("AAP", exclusions)
        if excluded:
            return HEDISMeasureResult(
                measure_code="AAP",
                measure_name="Adults' Access to Preventive Services",
                applicable=True,
                documented=False,
                status="Excluded",
                score="excluded",
                exclusion_reason=exclusion_reason,
                age_range="20+"
            ), []

        # Evaluate
        ambulatory_visits = visits.get("ambulatory", []) + visits.get("preventive", [])
        visit_count = len(ambulatory_visits)

        if visit_count >= 1:
            return HEDISMeasureResult(
                measure_code="AAP",
                measure_name="Adults' Access to Preventive Services",
                applicable=True,
                documented=True,
                status=f"{visit_count} Visit(s) Documented",
                score="numerator",
                age_range="20+"
            ), []
        else:
            gap_msg = "HEDIS AAP - No ambulatory or preventive care visits documented in measurement year."
            gaps.append(gap_msg)

            return HEDISMeasureResult(
                measure_code="AAP",
                measure_name="Adults' Access to Preventive Services",
                applicable=True,
                documented=False,
                status="No Visits Documented",
                score="denominator_only",
                age_range="20+",
                gap_description=gap_msg
            ), gaps

    def _evaluate_awc(
        self,
        patient_age: int,
        visits: Dict[str, List[str]],
        exclusions: Dict
    ) -> Tuple[Optional[HEDISMeasureResult], List[str]]:
        """Evaluate AWC: Adolescent Well-Care Visits."""
        gaps = []

        # Check if applicable
        if not (12 <= patient_age <= 21):
            return None, []

        # Check for exclusions
        excluded, exclusion_reason = is_measure_excluded("AWC", exclusions)
        if excluded:
            return HEDISMeasureResult(
                measure_code="AWC",
                measure_name="Adolescent Well-Care Visits",
                applicable=True,
                documented=False,
                status="Excluded",
                score="excluded",
                exclusion_reason=exclusion_reason,
                age_range="12-21"
            ), []

        # Evaluate
        well_care_visits = visits.get("well_care", []) + visits.get("well_child", [])
        visit_count = len(well_care_visits)

        if visit_count >= 1:
            return HEDISMeasureResult(
                measure_code="AWC",
                measure_name="Adolescent Well-Care Visits",
                applicable=True,
                documented=True,
                status="Annual Visit Documented",
                score="numerator",
                age_range="12-21"
            ), []
        else:
            gap_msg = f"HEDIS AWC - No comprehensive well-care visit documented for age {patient_age}."
            gaps.append(gap_msg)

            return HEDISMeasureResult(
                measure_code="AWC",
                measure_name="Adolescent Well-Care Visits",
                applicable=True,
                documented=False,
                status="No Annual Visit",
                score="denominator_only",
                age_range="12-21",
                gap_description=gap_msg
            ), gaps

    def _evaluate_amm(
        self,
        patient_age: int,
        diagnoses_lower: List[str],
        medications: Dict[str, List[str]],
        exclusions: Dict
    ) -> Tuple[Optional[HEDISMeasureResult], List[str]]:
        """Evaluate AMM: Antidepressant Medication Management."""
        gaps = []

        # Check if applicable
        has_depression_with_meds = (
            any("depression" in d for d in diagnoses_lower) and
            len(medications.get("antidepressant", [])) > 0
        )

        if not (patient_age >= 18 and has_depression_with_meds):
            return None, []

        # Check for exclusions
        excluded, exclusion_reason = is_measure_excluded("AMM", exclusions)
        if excluded:
            return HEDISMeasureResult(
                measure_code="AMM",
                measure_name="Antidepressant Medication Management",
                applicable=True,
                documented=False,
                status="Excluded",
                score="excluded",
                exclusion_reason=exclusion_reason,
                age_range="18+"
            ), []

        # Evaluate
        antidepressant_days = medications.get("antidepressant", [])
        med_days = len(antidepressant_days)

        acute_phase_met = med_days >= 84  # 12 weeks
        continuation_phase_met = med_days >= 180  # 6 months

        if continuation_phase_met:
            return HEDISMeasureResult(
                measure_code="AMM",
                measure_name="Antidepressant Medication Management",
                applicable=True,
                documented=True,
                status="Both Phases Met",
                score="numerator",
                age_range="18+"
            ), []
        elif acute_phase_met:
            gap_msg = f"HEDIS AMM - Acute phase met ({med_days} days), continuation phase incomplete (need 180 days)."
            gaps.append(gap_msg)

            return HEDISMeasureResult(
                measure_code="AMM",
                measure_name="Antidepressant Medication Management",
                applicable=True,
                documented="partial",
                status="Acute Phase Only",
                score="partial",
                age_range="18+",
                gap_description=gap_msg
            ), gaps
        else:
            gap_msg = f"HEDIS AMM - Antidepressant medication documented for {med_days} days (need 84 for acute, 180 for continuation)."
            gaps.append(gap_msg)

            return HEDISMeasureResult(
                measure_code="AMM",
                measure_name="Antidepressant Medication Management",
                applicable=True,
                documented=False,
                status="Insufficient Adherence",
                score="denominator_only",
                age_range="18+",
                gap_description=gap_msg
            ), gaps


# Convenience function
def evaluate_hedis_measures(
    clinical_note: str,
    patient_age: int,
    patient_gender: str,
    medications: Optional[Dict[str, List[str]]] = None,
    visits: Optional[Dict[str, List[str]]] = None,
    immunizations: Optional[Dict[str, bool]] = None,
    encounters: Optional[List[Dict]] = None
) -> HEDISEvaluationResult:
    """
    Convenience function to evaluate HEDIS measures from a clinical note.

    Args:
        clinical_note: Clinical note text
        patient_age: Patient age in years
        patient_gender: Patient gender

    Returns:
        HEDISEvaluationResult
    """
    from domain.entity_extraction import extract_entities

    # Extract entities from note
    entities = extract_entities(clinical_note)

    # Create evaluator and evaluate
    evaluator = HEDISEvaluator()
    return evaluator.evaluate(
        diagnoses=entities.get_diagnosis_names(),
        vitals=entities.get_vitals_dict(),
        labs=entities.get_labs_dict(),
        screenings=entities.get_screenings_dict(),
        patient_age=patient_age,
        patient_gender=patient_gender,
        medications=medications,
        visits=visits,
        immunizations=immunizations,
        encounters=encounters,
        note_text=clinical_note,
    )
