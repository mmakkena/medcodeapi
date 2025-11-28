"""
Revenue Optimization API Routes

Revenue analysis and optimization endpoints including:
- E/M coding analysis (2021 guidelines)
- HCC risk adjustment opportunities
- DRG optimization
- Missing charge detection
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
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
from domain.revenue_optimization import RevenueOptimizer

# Schema imports
from adapters.api.schemas.revenue import (
    RevenueAnalysisRequest,
    RevenueAnalysisResponse,
    EMCodeResponse,
    HCCOpportunity,
    DRGOptimizationResponse,
    MissingChargeOpportunity,
    RevenueSummary,
    ClinicalSetting,
    PatientType,
    EMCodingGuidelinesResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# E/M Coding Guidelines Reference
# ============================================================================

EM_GUIDELINES = {
    "outpatient": {
        "established": {
            "99211": {"mdm": "N/A", "time": 0, "description": "Minimal problem (nurse visit)"},
            "99212": {"mdm": "Straightforward", "time": 10, "description": "Low complexity"},
            "99213": {"mdm": "Low", "time": 20, "description": "Moderate complexity"},
            "99214": {"mdm": "Moderate", "time": 30, "description": "Moderate-high complexity"},
            "99215": {"mdm": "High", "time": 40, "description": "High complexity"},
        },
        "new": {
            "99202": {"mdm": "Straightforward", "time": 15, "description": "Low complexity"},
            "99203": {"mdm": "Low", "time": 30, "description": "Moderate complexity"},
            "99204": {"mdm": "Moderate", "time": 45, "description": "Moderate-high complexity"},
            "99205": {"mdm": "High", "time": 60, "description": "High complexity"},
        }
    },
    "inpatient": {
        "initial": {
            "99221": {"mdm": "Straightforward/Low", "time": 40, "description": "Low severity"},
            "99222": {"mdm": "Moderate", "time": 55, "description": "Moderate severity"},
            "99223": {"mdm": "High", "time": 75, "description": "High severity"},
        },
        "subsequent": {
            "99231": {"mdm": "Straightforward/Low", "time": 25, "description": "Stable/improving"},
            "99232": {"mdm": "Moderate", "time": 35, "description": "Responding to treatment"},
            "99233": {"mdm": "High", "time": 50, "description": "Unstable/significant complication"},
        }
    }
}

MDM_CRITERIA = {
    "straightforward": [
        "1 self-limited or minor problem",
        "Minimal data review",
        "Minimal risk"
    ],
    "low": [
        "2+ self-limited problems OR 1 stable chronic illness",
        "Limited data (review of external records)",
        "Low risk (OTC drugs, minor surgery)"
    ],
    "moderate": [
        "1 chronic illness with mild exacerbation OR 2 stable chronic illnesses OR 1 undiagnosed new problem",
        "Moderate data (independent interpretation, discussion with external physician)",
        "Moderate risk (prescription drugs, minor surgery with risk factors)"
    ],
    "high": [
        "1 chronic illness with severe exacerbation OR 1 acute life-threatening condition",
        "Extensive data (independent interpretation of complex tests)",
        "High risk (hospitalization, drugs requiring intensive monitoring, major surgery)"
    ]
}


# ============================================================================
# Revenue Analysis Endpoint
# ============================================================================

@router.post("/analyze", response_model=RevenueAnalysisResponse)
async def analyze_revenue_opportunities(
    request: RevenueAnalysisRequest,
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Comprehensive revenue optimization analysis.

    Analyzes clinical documentation for:
    - **E/M Coding**: Recommends appropriate E/M code based on 2021 guidelines
    - **HCC Opportunities**: Identifies hierarchical condition categories for risk adjustment
    - **DRG Optimization**: Suggests DRG improvements for inpatient encounters
    - **Missing Charges**: Detects procedures/tests documented but not captured

    Returns prioritized opportunities with estimated revenue impact.
    """
    api_key, user = api_key_data
    start_time = time.time()

    await check_rate_limit(api_key, user)

    try:
        # Extract clinical entities
        extractor = ClinicalEntityExtractor()
        entities = extractor.extract(request.clinical_note)

        # Map setting and patient type
        setting = request.clinical_setting.value if request.clinical_setting else "outpatient"
        patient_type = request.patient_type.value if request.patient_type else "established"

        # Run revenue optimization
        optimizer = RevenueOptimizer()
        result = optimizer.analyze(
            clinical_note=request.clinical_note,
            entities=entities,
            setting=setting,
            patient_type=patient_type
        )

        # Build E/M response
        em_response = None
        if request.include_em_analysis and result.em_recommendation:
            em = result.em_recommendation
            em_response = EMCodeResponse(
                recommended_code=em.recommended_code,
                code_description=em.documented_level,
                current_code=request.current_em_code,
                mdm_level=em.documented_level,
                time_based_option=None,
                supporting_elements=[],
                documentation_gaps=em.documentation_gaps,
                estimated_reimbursement=em.reimbursement,
                confidence=em.confidence
            )

        # Build HCC opportunities (from string list)
        hcc_opportunities = []
        if request.include_hcc_analysis and result.hcc_opportunities:
            for i, hcc_desc in enumerate(result.hcc_opportunities):
                hcc_opportunities.append(HCCOpportunity(
                    hcc_code=f"HCC{i+1}",
                    hcc_description=hcc_desc,
                    associated_diagnosis=result.condition or "",
                    icd10_code="",
                    risk_adjustment_factor=0.0,
                    annual_value=result.hcc_revenue_opportunity / max(len(result.hcc_opportunities), 1),
                    evidence_in_note=result.condition or "",
                    documentation_needed="Additional specificity may be needed",
                    confidence=result.confidence
                ))

        # Build DRG optimization response
        drg_response = None
        if request.include_drg_analysis and result.drg_optimization:
            drg = result.drg_optimization
            drg_response = DRGOptimizationResponse(
                current_drg=drg.current_drg or request.current_drg,
                current_drg_weight=None,
                potential_drg=drg.potential_drg or "",
                potential_drg_weight=0.0,
                weight_difference=0.0,
                estimated_revenue_increase=drg.revenue_impact,
                required_documentation=drg.documentation_improvements,
                clinical_indicators=[result.condition] if result.condition else [],
                cc_mcc_opportunities=[],
                confidence=result.confidence
            )

        # Build missing charges from tests_missing
        missing_charges = []
        if request.include_missing_charges and result.tests_missing:
            for test in result.tests_missing:
                missing_charges.append(MissingChargeOpportunity(
                    item_type="test",
                    item_name=test.get("test", "Unknown"),
                    suggested_code=test.get("cpt", None),
                    code_system="CPT",
                    evidence_in_note=test.get("reason", ""),
                    estimated_value=test.get("value", 0),
                    confidence=result.confidence
                ))

        # Build summary - em_upgrade_potential must be a bool
        em_upgrade = False
        if em_response is not None and request.current_em_code and em_response.recommended_code:
            em_upgrade = em_response.recommended_code > request.current_em_code

        summary = RevenueSummary(
            total_opportunities=len(hcc_opportunities) + len(missing_charges) + (1 if drg_response else 0),
            estimated_total_impact=result.total_revenue_opportunity,
            em_upgrade_potential=em_upgrade,
            hcc_opportunities_count=len(hcc_opportunities),
            drg_optimization_available=drg_response is not None,
            missing_charges_count=len(missing_charges)
        )

        processing_time_ms = (time.time() - start_time) * 1000

        # Log request
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/revenue/analyze",
            method="POST",
            query_params={
                "note_length": len(request.clinical_note),
                "setting": setting,
                "opportunities_found": summary.total_opportunities
            },
            status_code=200,
            response_time_ms=int(processing_time_ms),
            ip_address=None
        )

        return RevenueAnalysisResponse(
            success=True,
            em_recommendation=em_response,
            hcc_opportunities=hcc_opportunities,
            drg_optimization=drg_response,
            missing_charges=missing_charges,
            summary=summary,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Revenue analysis failed: {e}", exc_info=True)
        processing_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/revenue/analyze",
            method="POST",
            query_params={"note_length": len(request.clinical_note)},
            status_code=500,
            response_time_ms=processing_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail=f"Revenue analysis failed: {str(e)}")


# ============================================================================
# E/M Coding Guidelines Endpoint
# ============================================================================

@router.get("/em-guidelines", response_model=EMCodingGuidelinesResponse)
async def get_em_guidelines(
    setting: ClinicalSetting = ClinicalSetting.OUTPATIENT,
    patient_type: PatientType = PatientType.ESTABLISHED,
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Get E/M coding guidelines for a specific setting and patient type.

    Returns:
    - Available E/M codes with MDM levels and time thresholds
    - MDM criteria for each complexity level
    - Documentation requirements
    """
    api_key, user = api_key_data

    await check_rate_limit(api_key, user)

    try:
        # Get codes for setting/patient type
        if setting == ClinicalSetting.INPATIENT:
            if patient_type == PatientType.NEW:
                codes = EM_GUIDELINES["inpatient"]["initial"]
            else:
                codes = EM_GUIDELINES["inpatient"]["subsequent"]
        else:
            if patient_type == PatientType.NEW:
                codes = EM_GUIDELINES["outpatient"]["new"]
            else:
                codes = EM_GUIDELINES["outpatient"]["established"]

        available_codes = [
            {
                "code": code,
                "mdm_level": info["mdm"],
                "time_threshold": str(info["time"]),  # Convert to string for schema
                "description": info["description"]
            }
            for code, info in codes.items()
        ]

        # Time thresholds
        time_thresholds = {code: info["time"] for code, info in codes.items()}

        return EMCodingGuidelinesResponse(
            setting=setting,
            patient_type=patient_type,
            available_codes=available_codes,
            mdm_criteria=MDM_CRITERIA,
            time_thresholds=time_thresholds,
            documentation_requirements=[
                "Chief complaint",
                "History of present illness",
                "Review of systems (for moderate/high complexity)",
                "Physical examination",
                "Assessment and plan",
                "Time documentation (if time-based billing)",
                "Medical decision making documentation"
            ]
        )

    except Exception as e:
        logger.error(f"Failed to get E/M guidelines: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get guidelines: {str(e)}")
