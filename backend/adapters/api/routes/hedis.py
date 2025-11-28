"""
HEDIS Evaluation API Routes

Quality measure evaluation endpoints for HEDIS compliance.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import time
import logging

from infrastructure.db.postgres import get_db
from infrastructure.db.models.api_key import APIKey
from infrastructure.db.models.user import User
from adapters.api.middleware.api_key import verify_api_key_with_usage
from adapters.api.middleware.rate_limit import check_rate_limit
from infrastructure.db.repositories.usage_repository import log_api_request

# Domain layer imports
from domain.entity_extraction import ClinicalEntityExtractor
from domain.hedis_evaluation import HEDISEvaluator, check_hedis_exclusions
from domain.common import HEDIS_TARGETS

# Schema imports
from adapters.api.schemas.hedis import (
    HEDISEvaluationRequest,
    HEDISEvaluationResponse,
    HEDISMeasureResponse,
    ExclusionInfo,
    MeasureStatus,
    HEDISMeasureInfo,
    HEDISMeasureListResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# HEDIS Measure Definitions
# ============================================================================

HEDIS_MEASURE_INFO = {
    "CBP": HEDISMeasureInfo(
        measure_id="CBP",
        measure_name="Controlling High Blood Pressure",
        description="Percentage of patients 18-85 with hypertension whose BP was adequately controlled (<140/90)",
        target_population="Adults 18-85 with hypertension diagnosis",
        numerator_criteria="Most recent BP reading <140/90 mmHg",
        denominator_criteria="Diagnosis of hypertension during measurement year",
        exclusion_criteria=["Pregnancy", "ESRD", "Hospice", "Dialysis"],
        performance_target=0.65
    ),
    "CDC_HBA1C": HEDISMeasureInfo(
        measure_id="CDC_HBA1C",
        measure_name="Comprehensive Diabetes Care - HbA1c Control",
        description="Percentage of diabetic patients with HbA1c <8.0%",
        target_population="Adults 18-75 with diabetes",
        numerator_criteria="Most recent HbA1c <8.0%",
        denominator_criteria="Diagnosis of diabetes (Type 1 or Type 2)",
        exclusion_criteria=["Hospice", "Steroid-induced diabetes"],
        performance_target=0.60
    ),
    "CDC_EYE": HEDISMeasureInfo(
        measure_id="CDC_EYE",
        measure_name="Comprehensive Diabetes Care - Eye Exam",
        description="Percentage of diabetic patients with retinal eye exam",
        target_population="Adults 18-75 with diabetes",
        numerator_criteria="Retinal eye exam performed in measurement year or prior year with negative result",
        denominator_criteria="Diagnosis of diabetes (Type 1 or Type 2)",
        exclusion_criteria=["Hospice", "Bilateral eye enucleation"],
        performance_target=0.65
    ),
    "CDC_NEPHRO": HEDISMeasureInfo(
        measure_id="CDC_NEPHRO",
        measure_name="Comprehensive Diabetes Care - Nephropathy Screening",
        description="Percentage of diabetic patients with nephropathy screening or ACE/ARB",
        target_population="Adults 18-75 with diabetes",
        numerator_criteria="Nephropathy screening test OR ACE/ARB medication",
        denominator_criteria="Diagnosis of diabetes (Type 1 or Type 2)",
        exclusion_criteria=["Hospice", "ESRD"],
        performance_target=0.90
    ),
    "BCS": HEDISMeasureInfo(
        measure_id="BCS",
        measure_name="Breast Cancer Screening",
        description="Percentage of women 50-74 with mammogram in past 2 years",
        target_population="Women 50-74 years",
        numerator_criteria="Mammogram performed in measurement year or prior year",
        denominator_criteria="Women aged 50-74",
        exclusion_criteria=["Bilateral mastectomy", "Hospice"],
        performance_target=0.75
    ),
    "CCS": HEDISMeasureInfo(
        measure_id="CCS",
        measure_name="Cervical Cancer Screening",
        description="Percentage of women 21-64 appropriately screened for cervical cancer",
        target_population="Women 21-64 years",
        numerator_criteria="Pap test within 3 years (21-64) or HPV test within 5 years (30-64)",
        denominator_criteria="Women aged 21-64",
        exclusion_criteria=["Hysterectomy with no residual cervix", "Hospice"],
        performance_target=0.70
    ),
    "COL": HEDISMeasureInfo(
        measure_id="COL",
        measure_name="Colorectal Cancer Screening",
        description="Percentage of adults 50-75 appropriately screened for colorectal cancer",
        target_population="Adults 50-75 years",
        numerator_criteria="FOBT annually, FIT-DNA every 3 years, colonoscopy every 10 years, or sigmoidoscopy every 5 years",
        denominator_criteria="Adults aged 50-75",
        exclusion_criteria=["Colorectal cancer history", "Total colectomy", "Hospice"],
        performance_target=0.70
    ),
    "SPR": HEDISMeasureInfo(
        measure_id="SPR",
        measure_name="Statin Therapy for Patients with Cardiovascular Disease",
        description="Percentage of males 21-75 and females 40-75 with CVD prescribed statin therapy",
        target_population="Adults with cardiovascular disease",
        numerator_criteria="Prescribed statin therapy during measurement year",
        denominator_criteria="Diagnosis of ASCVD",
        exclusion_criteria=["Hospice", "Pregnancy", "ESRD", "Cirrhosis", "Myopathy"],
        performance_target=0.80
    ),
}


# ============================================================================
# HEDIS Evaluation Endpoint
# ============================================================================

@router.post("/evaluate", response_model=HEDISEvaluationResponse)
async def evaluate_hedis_measures(
    request: HEDISEvaluationRequest,
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Evaluate HEDIS quality measures for a clinical note.

    Evaluates measures including:
    - CBP: Controlling High Blood Pressure
    - CDC: Comprehensive Diabetes Care (HbA1c, Eye Exam, Nephropathy)
    - BCS: Breast Cancer Screening
    - CCS: Cervical Cancer Screening
    - COL: Colorectal Cancer Screening
    - SPR: Statin Therapy for Cardiovascular Disease

    Returns compliance status, gaps, and recommendations for each measure.
    """
    api_key, user = api_key_data
    start_time = time.time()

    await check_rate_limit(api_key, user)

    try:
        # Extract clinical entities
        extractor = ClinicalEntityExtractor()
        entities = extractor.extract(request.clinical_note)

        # Convert entities to format expected by evaluator
        diagnoses_list = [d.name for d in entities.diagnoses]

        vitals_dict = {}
        if entities.vitals:
            if entities.vitals.systolic and entities.vitals.diastolic:
                vitals_dict["BP"] = f"{entities.vitals.systolic}/{entities.vitals.diastolic}"

        labs_dict = {}
        if entities.labs:
            if entities.labs.hba1c:
                labs_dict["HbA1c"] = f"{entities.labs.hba1c}%"
            if entities.labs.ldl:
                labs_dict["LDL"] = str(entities.labs.ldl)

        screenings_dict = {}
        if entities.screenings:
            if entities.screenings.mammogram:
                screenings_dict["Mammogram"] = True
            if entities.screenings.colonoscopy:
                screenings_dict["Colorectal"] = True
            if entities.screenings.cervical_cancer:
                screenings_dict["Cervical"] = True

        # Check exclusions if requested
        exclusions = []
        if request.include_exclusions:
            exclusion_result = check_hedis_exclusions(
                diagnoses=diagnoses_list,
                note_text=request.clinical_note
            )
            for measure_id, exclusion_info in exclusion_result.items():
                if exclusion_info.get("is_excluded"):
                    exclusions.append(ExclusionInfo(
                        measure_id=measure_id,
                        is_excluded=True,
                        exclusion_reason=exclusion_info.get("reason"),
                        exclusion_criteria=exclusion_info.get("criteria")
                    ))

        # Get excluded measure IDs
        excluded_measure_ids = {e.measure_id for e in exclusions}

        # Evaluate HEDIS measures using converted dicts
        evaluator = HEDISEvaluator()
        evaluation_result = evaluator.evaluate(
            diagnoses=diagnoses_list,
            vitals=vitals_dict,
            labs=labs_dict,
            screenings=screenings_dict,
            patient_age=request.patient_age,
            patient_gender=request.patient_gender,
            medications=[m.name for m in entities.medications],
            note_text=request.clinical_note
        )

        # Filter to requested measures if specified
        measures_to_include = request.measures if request.measures else None

        # Convert to response format
        # evaluation_result.measures is a dict with measure_code as key
        measures_response = []
        status_counts = {"met": 0, "not_met": 0, "excluded": 0, "not_applicable": 0}
        total_gaps = 0

        for measure_code, measure in evaluation_result.measures.items():
            # Skip if not in requested list
            if measures_to_include and measure_code not in measures_to_include:
                continue

            # Check if excluded
            if measure_code in excluded_measure_ids:
                status = MeasureStatus.EXCLUDED
                status_counts["excluded"] += 1
            elif measure.meets_target:
                status = MeasureStatus.MET
                status_counts["met"] += 1
            else:
                status = MeasureStatus.NOT_MET
                status_counts["not_met"] += 1
                if measure.gap_description:
                    total_gaps += 1

            # Get recommendations from gap_description
            recommendations = []
            if measure.gap_description:
                recommendations = [measure.gap_description]

            measures_response.append(HEDISMeasureResponse(
                measure_id=measure_code,
                measure_name=measure.measure_name,
                status=status,
                value=str(measure.value) if measure.value is not None else None,
                target=str(measure.target) if measure.target is not None else None,
                is_compliant=measure.meets_target or False,
                gaps=[measure.gap_description] if measure.gap_description else [],
                recommendations=recommendations,
                evidence_text=measure.status,
                confidence=evaluation_result.overall_confidence
            ))

        # Calculate overall compliance rate
        applicable_count = status_counts["met"] + status_counts["not_met"]
        compliance_rate = status_counts["met"] / applicable_count if applicable_count > 0 else 0.0

        processing_time_ms = (time.time() - start_time) * 1000

        # Log request
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/hedis/evaluate",
            method="POST",
            query_params={
                "note_length": len(request.clinical_note),
                "measures_evaluated": len(measures_response),
                "compliance_rate": compliance_rate
            },
            status_code=200,
            response_time_ms=int(processing_time_ms),
            ip_address=None
        )

        return HEDISEvaluationResponse(
            success=True,
            measures=measures_response,
            exclusions=exclusions,
            summary=status_counts,
            overall_compliance_rate=compliance_rate,
            total_gaps_identified=total_gaps,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"HEDIS evaluation failed: {e}", exc_info=True)
        processing_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/hedis/evaluate",
            method="POST",
            query_params={"note_length": len(request.clinical_note)},
            status_code=500,
            response_time_ms=processing_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail=f"HEDIS evaluation failed: {str(e)}")


# ============================================================================
# HEDIS Measure Information Endpoint
# ============================================================================

@router.get("/measures", response_model=HEDISMeasureListResponse)
async def list_hedis_measures(
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    List all available HEDIS measures with their definitions.

    Returns measure IDs, names, criteria, and performance targets.
    """
    api_key, user = api_key_data
    start_time = time.time()

    await check_rate_limit(api_key, user)

    try:
        measures = list(HEDIS_MEASURE_INFO.values())
        processing_time_ms = (time.time() - start_time) * 1000

        # Log request
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/hedis/measures",
            method="GET",
            query_params={},
            status_code=200,
            response_time_ms=int(processing_time_ms),
            ip_address=None
        )

        return HEDISMeasureListResponse(
            measures=measures,
            total_count=len(measures)
        )

    except Exception as e:
        logger.error(f"Failed to list HEDIS measures: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list measures: {str(e)}")


# ============================================================================
# HEDIS Targets Endpoint
# ============================================================================

@router.get("/targets")
async def get_hedis_targets(
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Get HEDIS performance targets and thresholds.

    Returns target values for each measure (e.g., BP < 140/90, HbA1c < 8.0%).
    """
    api_key, user = api_key_data

    await check_rate_limit(api_key, user)

    return {
        "targets": HEDIS_TARGETS,
        "description": "HEDIS performance targets and thresholds for quality measures"
    }
