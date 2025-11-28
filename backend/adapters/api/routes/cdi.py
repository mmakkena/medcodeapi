"""
CDI Analysis API Routes

Comprehensive Clinical Documentation Integrity analysis endpoints:
- Entity extraction
- Documentation gap analysis
- CDI query generation
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import time
import logging
import uuid

from infrastructure.db.postgres import get_db
from infrastructure.db.models.api_key import APIKey
from infrastructure.db.models.user import User
from adapters.api.middleware.api_key import verify_api_key_with_usage
from adapters.api.middleware.rate_limit import check_rate_limit
from infrastructure.db.repositories.usage_repository import log_api_request

# Domain layer imports
from domain.entity_extraction import ClinicalEntityExtractor
from domain.documentation_gaps import DocumentationGapAnalyzer
from domain.query_generation import CDIQueryGenerator
from domain.common import (
    calculate_extraction_confidence,
    calculate_completeness_score,
    calculate_overall_confidence,
)

# Schema imports
from adapters.api.schemas.clinical_entities import (
    EntityExtractionRequest,
    EntityExtractionResponse,
    ClinicalEntitiesResponse,
    VitalSignsResponse,
    LabResultResponse,
    DiagnosisResponse,
    MedicationResponse,
    ScreeningResponse,
    ConfidenceMetrics,
)
from adapters.api.schemas.documentation_gaps import (
    GapAnalysisRequest,
    GapAnalysisResponse,
    DocumentationGapResponse,
    GapSummary,
    GapPriority,
    GapCategory,
)
from adapters.api.schemas.cdi_queries import (
    CDIQueryGenerationRequest,
    CDIQueryGenerationResponse,
    CDIQueryResponse,
    QuerySummary,
    QueryType,
    QueryPriority,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Entity Extraction Endpoint
# ============================================================================

@router.post("/entities", response_model=EntityExtractionResponse)
async def extract_entities(
    request: EntityExtractionRequest,
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Extract clinical entities from a clinical note.

    Extracts:
    - Vital signs (BP, HR, temp, SpO2, BMI, etc.)
    - Lab results (HbA1c, glucose, creatinine, etc.)
    - Diagnoses with ICD-10 suggestions
    - Medications with dosing
    - Screenings (mammogram, colonoscopy, etc.)

    Uses rule-based extraction (fast, no LLM cost).
    """
    api_key, user = api_key_data
    start_time = time.time()

    await check_rate_limit(api_key, user)

    try:
        # Initialize extractor
        extractor = ClinicalEntityExtractor()

        # Extract all entities
        entities = extractor.extract(request.clinical_note)

        # Convert to response format
        vitals_response = VitalSignsResponse(
            blood_pressure_systolic=entities.vitals.systolic if entities.vitals else None,
            blood_pressure_diastolic=entities.vitals.diastolic if entities.vitals else None,
            heart_rate=entities.vitals.heart_rate if entities.vitals else None,
            temperature=entities.vitals.temperature if entities.vitals else None,
            respiratory_rate=entities.vitals.respiratory_rate if entities.vitals else None,
            spo2=entities.vitals.spo2 if entities.vitals else None,
            weight=entities.vitals.weight if entities.vitals else None,
            height=entities.vitals.height if entities.vitals else None,
            bmi=entities.vitals.bmi if entities.vitals else None,
        )

        # Convert LabResults fields to list
        labs_response = []
        if entities.labs:
            lab_fields = [
                ("hba1c", "%", "4.0-5.6"),
                ("ldl", "mg/dL", "<100"),
                ("hdl", "mg/dL", ">40"),
                ("total_cholesterol", "mg/dL", "<200"),
                ("triglycerides", "mg/dL", "<150"),
                ("creatinine", "mg/dL", "0.7-1.3"),
                ("egfr", "mL/min", ">60"),
                ("glucose", "mg/dL", "70-100"),
                ("potassium", "mEq/L", "3.5-5.0"),
                ("sodium", "mEq/L", "136-145"),
                ("wbc", "K/uL", "4.5-11.0"),
                ("hemoglobin", "g/dL", "12-16"),
            ]
            for field_name, unit, ref_range in lab_fields:
                value = getattr(entities.labs, field_name, None)
                if value is not None:
                    # Simple abnormal check
                    is_abnormal = False
                    if field_name == "hba1c" and value > 5.7:
                        is_abnormal = True
                    elif field_name == "ldl" and value > 100:
                        is_abnormal = True
                    elif field_name == "egfr" and value < 60:
                        is_abnormal = True
                    elif field_name == "glucose" and (value < 70 or value > 100):
                        is_abnormal = True

                    labs_response.append(LabResultResponse(
                        name=field_name.upper().replace("_", " "),
                        value=value,
                        unit=unit,
                        reference_range=ref_range,
                        is_abnormal=is_abnormal
                    ))

        diagnoses_response = [
            DiagnosisResponse(
                name=dx.name,
                icd10_code=dx.icd10_code,
                status=dx.status or "active",  # Default to "active" if None
                severity=None  # Severity not available in current model
            )
            for dx in entities.diagnoses
        ]

        medications_response = [
            MedicationResponse(
                name=med.name,
                dose=med.dose,
                frequency=med.frequency,
                route=med.route
            )
            for med in entities.medications
        ]

        # Convert Screenings fields to list
        screenings_response = []
        if entities.screenings:
            screening_fields = [
                "mammogram", "colonoscopy", "fit_test", "cologuard",
                "depression_screening", "chlamydia", "cervical_cancer",
                "lung_cancer", "bone_density", "diabetic_eye", "diabetic_foot"
            ]
            for field_name in screening_fields:
                value = getattr(entities.screenings, field_name, None)
                if value is not None:
                    screenings_response.append(ScreeningResponse(
                        name=field_name.replace("_", " ").title(),
                        date=str(value) if value else None,
                        result=None,
                        is_completed=bool(value)
                    ))

        # Calculate confidence metrics
        # Convert entities to the format expected by scoring functions
        diagnoses_list = [dx.name for dx in entities.diagnoses]
        vitals_dict = {}
        if entities.vitals:
            if entities.vitals.systolic and entities.vitals.diastolic:
                vitals_dict["BP"] = f"{entities.vitals.systolic}/{entities.vitals.diastolic}"
            if entities.vitals.heart_rate:
                vitals_dict["HR"] = str(entities.vitals.heart_rate)
        labs_dict = {}
        if entities.labs:
            if entities.labs.hba1c:
                labs_dict["HbA1c"] = str(entities.labs.hba1c)
        screenings_dict = {}
        if entities.screenings:
            screenings_dict = {
                "mammogram": bool(entities.screenings.mammogram),
                "colonoscopy": bool(entities.screenings.colonoscopy),
            }

        extraction_result = calculate_extraction_confidence(
            diagnoses=diagnoses_list,
            vitals=vitals_dict,
            labs=labs_dict,
            screenings=screenings_dict,
            note_text=request.clinical_note
        )
        # extraction_result is (confidence_score, warnings, total_extracted)
        extraction_conf = extraction_result[0]
        extraction_warnings = extraction_result[1]

        # Calculate simple completeness based on extracted entities
        completeness_factors = {
            "diagnoses": len(diagnoses_list) > 0,
            "vitals": len(vitals_dict) > 0,
            "labs": len(labs_dict) > 0,
            "screenings": len(screenings_dict) > 0,
            "medications": len(entities.medications) > 0,
        }
        completeness = calculate_completeness_score(completeness_factors)

        overall_conf = calculate_overall_confidence(
            extraction_conf, 1.0, completeness
        )

        confidence = ConfidenceMetrics(
            overall_confidence=overall_conf,
            extraction_confidence=extraction_conf,
            parsing_confidence=1.0,  # Rule-based is deterministic
            completeness_score=completeness
        )

        processing_time_ms = (time.time() - start_time) * 1000

        entities_response = ClinicalEntitiesResponse(
            vitals=vitals_response,
            labs=labs_response,
            diagnoses=diagnoses_response,
            medications=medications_response,
            screenings=screenings_response,
            confidence=confidence,
            processing_time_ms=processing_time_ms
        )

        # Log request
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/cdi/entities",
            method="POST",
            query_params={"note_length": len(request.clinical_note)},
            status_code=200,
            response_time_ms=int(processing_time_ms),
            ip_address=None
        )

        return EntityExtractionResponse(
            success=True,
            entities=entities_response,
            warnings=extraction_warnings
        )

    except Exception as e:
        logger.error(f"Entity extraction failed: {e}", exc_info=True)
        processing_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/cdi/entities",
            method="POST",
            query_params={"note_length": len(request.clinical_note)},
            status_code=500,
            response_time_ms=processing_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail=f"Entity extraction failed: {str(e)}")


# ============================================================================
# Documentation Gap Analysis Endpoint
# ============================================================================

@router.post("/gaps", response_model=GapAnalysisResponse)
async def analyze_documentation_gaps(
    request: GapAnalysisRequest,
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Analyze clinical documentation for gaps and missing information.

    Identifies:
    - Missing specificity (unspecified laterality, acuity, etc.)
    - Missing linkages (diabetes + CKD, hypertension + heart disease)
    - Missing clinical indicators (severity, stage, type)
    - Missing HEDIS-related documentation
    - Revenue impacting omissions

    Returns prioritized gaps with suggested queries.
    """
    api_key, user = api_key_data
    start_time = time.time()

    await check_rate_limit(api_key, user)

    try:
        # First extract entities
        extractor = ClinicalEntityExtractor()
        entities = extractor.extract(request.clinical_note)

        # Analyze gaps
        analyzer = DocumentationGapAnalyzer()
        gap_analysis = analyzer.analyze(
            entities=entities,
            hedis_result=None,
            patient_age=request.patient_age,
            patient_gender=request.patient_gender
        )

        # Convert to response format
        gaps_response = []
        for gap in gap_analysis.gaps:
            # Map priority - gap.priority is a GapPriority enum
            priority_value = gap.priority.value if hasattr(gap.priority, 'value') else str(gap.priority)
            priority_map = {
                "critical": GapPriority.CRITICAL,
                "high": GapPriority.HIGH,
                "medium": GapPriority.MEDIUM,
                "low": GapPriority.LOW
            }
            priority = priority_map.get(priority_value.lower(), GapPriority.MEDIUM)

            # Map category (gap_type in model)
            gap_type_value = gap.gap_type if hasattr(gap, 'gap_type') else "diagnosis"
            category_map = {
                "diagnosis": GapCategory.DIAGNOSIS,
                "specificity": GapCategory.SPECIFICITY,
                "acuity": GapCategory.ACUITY,
                "linkage": GapCategory.LINKAGE,
                "vital_signs": GapCategory.VITAL_SIGNS,
                "lab_result": GapCategory.LAB_RESULT,
                "screening": GapCategory.SCREENING,
            }
            category = category_map.get(gap_type_value, GapCategory.DIAGNOSIS)

            # Map confidence from evidence_grade
            evidence_grade = getattr(gap, 'evidence_grade', 'medium')
            confidence_map = {'high': 0.9, 'medium': 0.7, 'low': 0.5}
            confidence = confidence_map.get(evidence_grade, 0.7)

            # Convert revenue_impact to string
            revenue_impact_str = None
            if gap.revenue_impact is not None:
                revenue_impact_str = f"${gap.revenue_impact:.2f}" if isinstance(gap.revenue_impact, (int, float)) else str(gap.revenue_impact)

            # Convert hedis_impact to list
            hedis_impact_list = None
            measure_affected = getattr(gap, 'measure_affected', None)
            if measure_affected:
                hedis_impact_list = [measure_affected] if isinstance(measure_affected, str) else measure_affected

            gaps_response.append(DocumentationGapResponse(
                gap_id=str(uuid.uuid4())[:8],
                category=category,
                priority=priority,
                title=gap.gap_type if hasattr(gap, 'gap_type') else "Documentation Gap",
                description=gap.description,
                clinical_indicator=measure_affected if isinstance(measure_affected, str) else None,
                suggested_query=getattr(gap, 'suggested_action', None),
                revenue_impact=revenue_impact_str,
                hedis_impact=hedis_impact_list,
                evidence_text=gap.description,
                confidence=confidence
            ))

        # Build summary
        by_priority = {}
        by_category = {}
        for gap in gaps_response:
            by_priority[gap.priority.value] = by_priority.get(gap.priority.value, 0) + 1
            by_category[gap.category.value] = by_category.get(gap.category.value, 0) + 1

        summary = GapSummary(
            by_priority=by_priority,
            by_category=by_category,
            total_gaps=len(gaps_response),
            critical_count=by_priority.get("critical", 0),
            high_count=by_priority.get("high", 0)
        )

        # Top priorities
        top_priorities = [
            gap.title for gap in sorted(
                gaps_response,
                key=lambda g: (
                    {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(g.priority.value, 4),
                    -g.confidence
                )
            )[:3]
        ]

        processing_time_ms = (time.time() - start_time) * 1000

        # Log request
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/cdi/gaps",
            method="POST",
            query_params={"note_length": len(request.clinical_note), "gaps_found": len(gaps_response)},
            status_code=200,
            response_time_ms=int(processing_time_ms),
            ip_address=None
        )

        return GapAnalysisResponse(
            success=True,
            gaps=gaps_response,
            summary=summary,
            top_priorities=top_priorities,
            estimated_revenue_impact=gap_analysis.total_revenue_impact,
            hedis_gaps_count=len([g for g in gaps_response if g.hedis_impact]),
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Gap analysis failed: {e}", exc_info=True)
        processing_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/cdi/gaps",
            method="POST",
            query_params={"note_length": len(request.clinical_note)},
            status_code=500,
            response_time_ms=processing_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail=f"Gap analysis failed: {str(e)}")


# ============================================================================
# CDI Query Generation Endpoint
# ============================================================================

@router.post("/queries", response_model=CDIQueryGenerationResponse)
async def generate_cdi_queries(
    request: CDIQueryGenerationRequest,
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Generate ACDIS-compliant CDI queries for physicians.

    Generates non-leading queries for:
    - Specificity clarification
    - Acuity determination
    - Diagnosis linkage
    - Present on admission status
    - Clinical validation

    All queries follow ACDIS best practices (non-leading, evidence-based).
    """
    api_key, user = api_key_data
    start_time = time.time()

    await check_rate_limit(api_key, user)

    try:
        # First extract entities
        extractor = ClinicalEntityExtractor()
        entities = extractor.extract(request.clinical_note)

        # First analyze gaps
        analyzer = DocumentationGapAnalyzer()
        gap_analysis = analyzer.analyze(
            entities=entities,
            hedis_result=None,
            patient_age=request.patient_age,
            patient_gender=request.patient_gender
        )

        # Generate queries from gaps
        generator = CDIQueryGenerator()
        query_result = generator.generate_from_gaps(
            gap_analysis=gap_analysis,
            clinical_findings=None
        )

        # Convert to response format
        queries_response = []
        for query in query_result.queries[:request.max_queries]:
            # Map query type
            type_map = {
                "clarification": QueryType.CLARIFICATION,
                "specificity": QueryType.SPECIFICITY,
                "acuity": QueryType.ACUITY,
                "linkage": QueryType.LINKAGE,
                "present_on_admission": QueryType.PRESENT_ON_ADMISSION,
                "clinical_validation": QueryType.CLINICAL_VALIDATION,
            }
            query_type = type_map.get(query.query_type, QueryType.CLARIFICATION)

            # Map priority (query.priority is a GapPriority enum)
            priority_value = query.priority.value if hasattr(query.priority, 'value') else str(query.priority)
            priority_map = {
                "critical": QueryPriority.URGENT,
                "high": QueryPriority.HIGH,
                "medium": QueryPriority.ROUTINE,
                "low": QueryPriority.ROUTINE,
            }
            priority = priority_map.get(priority_value, QueryPriority.ROUTINE)

            queries_response.append(CDIQueryResponse(
                query_id=str(uuid.uuid4())[:8],
                query_type=query_type,
                priority=priority,
                query_text=query.query_text,
                clinical_indicator=query.clinical_finding,
                supporting_evidence=[],
                potential_diagnoses=query.potential_codes or [],
                documentation_needed=query.gap_addressed or "",
                revenue_impact=None,
                drg_impact=None,
                confidence=query_result.confidence
            ))

        # Build summary
        by_type = {}
        by_priority = {}
        for q in queries_response:
            by_type[q.query_type.value] = by_type.get(q.query_type.value, 0) + 1
            by_priority[q.priority.value] = by_priority.get(q.priority.value, 0) + 1

        summary = QuerySummary(
            total_queries=len(queries_response),
            by_type=by_type,
            by_priority=by_priority,
            urgent_count=by_priority.get("urgent", 0),
            estimated_drg_impact=None
        )

        processing_time_ms = (time.time() - start_time) * 1000

        # Log request
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/cdi/queries",
            method="POST",
            query_params={"note_length": len(request.clinical_note), "queries_generated": len(queries_response)},
            status_code=200,
            response_time_ms=int(processing_time_ms),
            ip_address=None
        )

        return CDIQueryGenerationResponse(
            success=True,
            queries=queries_response,
            summary=summary,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Query generation failed: {e}", exc_info=True)
        processing_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/cdi/queries",
            method="POST",
            query_params={"note_length": len(request.clinical_note)},
            status_code=500,
            response_time_ms=processing_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail=f"Query generation failed: {str(e)}")
