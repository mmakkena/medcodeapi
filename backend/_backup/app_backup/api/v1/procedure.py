"""Procedure code (CPT/HCPCS) search endpoints"""

import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.procedure_code import ProcedureCode
from app.models.api_key import APIKey
from app.models.user import User
from app.schemas.code import (
    ProcedureCodeResponse,
    ProcedureCodeDetailResponse,
    ProcedureCodeEnhancedResponse,
    ProcedureCodeFacetResponse,
    CodeMappingResponse,
    ProcedureSemanticSearchResponse
)
from app.middleware.api_key import verify_api_key_with_usage
from app.middleware.rate_limit import check_rate_limit
from app.services.usage_service import log_api_request
from app.services.procedure_search_service import (
    semantic_search,
    hybrid_search,
    faceted_search,
    get_code_with_details,
    suggest_codes_from_text
)
from app.config import settings
import time

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search", response_model=list[ProcedureCodeResponse])
async def search_procedures(
    query: str = Query(..., description="Search query (code or description)"),
    code_system: str | None = Query(None, description="Filter by CPT or HCPCS"),
    version_year: int | None = Query(None, description="Filter by version year (e.g., 2024, 2025)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Search procedure codes (CPT/HCPCS) by code or description.
    Supports exact code match and fuzzy text search.

    Examples:
    - Search by code: "99213" → Returns E/M office visit codes
    - Search by description: "office visit" → Returns related E/M codes
    - Search by procedure: "knee arthroscopy" → Returns surgical codes

    Use code_system to filter by CPT or HCPCS.
    Use version_year to search within a specific year's codes (e.g., 2025).
    """
    api_key, user = api_key_data
    start_time = time.time()

    # Check rate limit
    await check_rate_limit(api_key, user)

    try:
        # Use config default for procedures (2025) if not specified
        year = version_year if version_year is not None else settings.DEFAULT_PROCEDURE_VERSION_YEAR

        # Build base query
        base_query = db.query(ProcedureCode).filter(
            ProcedureCode.is_active == True,
            ProcedureCode.version_year == year
        )

        # Add code_system filter if specified
        if code_system:
            base_query = base_query.filter(ProcedureCode.code_system == code_system)

        # Search by exact code match first
        results = base_query.filter(
            ProcedureCode.code.ilike(f"{query}%")
        ).limit(limit).all()

        # If no exact matches, do fuzzy text search on descriptions
        if not results:
            description_query = db.query(ProcedureCode).filter(
                ProcedureCode.is_active == True,
                ProcedureCode.version_year == year
            )

            if code_system:
                description_query = description_query.filter(ProcedureCode.code_system == code_system)

            results = description_query.filter(
                or_(
                    ProcedureCode.paraphrased_desc.ilike(f"%{query}%"),
                    ProcedureCode.short_desc.ilike(f"%{query}%"),
                    ProcedureCode.category.ilike(f"%{query}%")
                )
            ).limit(limit).all()

        # Format response with appropriate description based on license_status
        response_items = []
        for code in results:
            response_items.append({
                "id": code.id,
                "code": code.code,
                "code_system": code.code_system,
                "description": code.get_display_description(),
                "category": code.category,
                "license_status": code.license_status,
                "version_year": code.version_year
            })

        # Log the request
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/procedure/search",
            method="GET",
            query_params={"query": query, "code_system": code_system, "version_year": version_year, "limit": limit},
            status_code=200,
            response_time_ms=response_time_ms,
            ip_address=None
        )

        return response_items

    except Exception as e:
        # Log error
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/procedure/search",
            method="GET",
            query_params={"query": query, "code_system": code_system, "version_year": version_year, "limit": limit},
            status_code=500,
            response_time_ms=response_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/semantic-search", response_model=ProcedureSemanticSearchResponse)
async def semantic_search_procedures(
    query: str = Query(..., description="Query text for semantic search", min_length=1),
    code_system: str | None = Query(None, description="Filter by CPT or HCPCS"),
    version_year: int | None = Query(None, description="Filter by version year (e.g., 2024, 2025)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    min_similarity: float = Query(0.0, ge=0.0, le=1.0, description="Minimum similarity threshold (0-1)"),
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Semantic search using AI embeddings for natural language queries.
    Returns procedure codes most similar to the query text based on meaning, not just keywords.

    Examples:
    - "routine follow-up visit for diabetes" → Returns appropriate E/M codes (99213, 99214)
    - "remove skin lesion from arm" → Returns excision codes
    - "blood sugar test" → Returns glucose testing codes
    - "CT scan of chest with contrast" → Returns chest CT codes

    This endpoint uses MedCPT embeddings to understand clinical intent.
    Note: Embeddings are based on paraphrased descriptions (license-compliant).
    """
    api_key, user = api_key_data
    start_time = time.time()

    # Check rate limit
    await check_rate_limit(api_key, user)

    try:
        # Use config default for procedures (2025) if not specified
        year = version_year if version_year is not None else settings.DEFAULT_PROCEDURE_VERSION_YEAR

        # Perform semantic search
        results = await semantic_search(
            db=db,
            query_text=query,
            code_system=code_system,
            version_year=year,
            limit=limit,
            min_similarity=min_similarity
        )

        # Build response with similarity scores and facets
        response_items = []
        for code, similarity in results:
            # Get facets for this code
            from app.models.procedure_code_facet import ProcedureCodeFacet
            from sqlalchemy import and_
            facets = db.query(ProcedureCodeFacet).filter(
                and_(
                    ProcedureCodeFacet.code == code.code,
                    ProcedureCodeFacet.code_system == code.code_system
                )
            ).first()

            # Create enhanced response
            code_dict = {
                "id": code.id,
                "code": code.code,
                "code_system": code.code_system,
                "description": code.get_display_description(),  # Add description for UI (uses paraphrased for license safety)
                "paraphrased_desc": code.paraphrased_desc,
                "short_desc": code.short_desc if code.license_status == 'AMA_licensed' else None,
                "long_desc": code.long_desc if code.license_status == 'AMA_licensed' else None,
                "category": code.category,
                "procedure_type": code.procedure_type,
                "version_year": code.version_year,
                "is_active": code.is_active,
                "effective_date": code.effective_date,
                "expiry_date": code.expiry_date,
                "license_status": code.license_status,
                "relative_value_units": code.relative_value_units,
                "global_period": code.global_period,
                "modifier_51_exempt": code.modifier_51_exempt,
                "created_at": code.created_at,
                "last_updated": code.last_updated
            }
            response_items.append({
                "code_info": code_dict,
                "facets": facets,
                "mappings": [],
                "similarity": similarity
            })

        # Log the request
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/procedure/semantic-search",
            method="GET",
            query_params={"query": query, "code_system": code_system, "version_year": version_year, "limit": limit, "min_similarity": min_similarity},
            status_code=200,
            response_time_ms=response_time_ms,
            ip_address=None
        )

        return {
            "query": query,
            "results": response_items,
            "total_results": len(response_items)
        }

    except Exception as e:
        # Log error
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/procedure/semantic-search",
            method="GET",
            query_params={"query": query, "code_system": code_system, "version_year": version_year, "limit": limit},
            status_code=500,
            response_time_ms=response_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail=f"Semantic search error: {str(e)}")


@router.get("/hybrid-search", response_model=ProcedureSemanticSearchResponse)
async def hybrid_search_procedures(
    query: str = Query(..., description="Query text for hybrid search", min_length=1),
    code_system: str | None = Query(None, description="Filter by CPT or HCPCS"),
    version_year: int | None = Query(None, description="Filter by version year (e.g., 2024, 2025)"),
    semantic_weight: float = Query(0.7, ge=0.0, le=1.0, description="Weight for semantic results (0-1)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Hybrid search combining semantic (AI embeddings) and keyword matching.
    Provides best of both worlds - finds semantically similar codes AND exact keyword matches.

    The semantic_weight parameter controls the balance:
    - 1.0 = Pure semantic search (best for natural language queries)
    - 0.7 = Default (70% semantic, 30% keyword) - recommended
    - 0.5 = Equal weight for semantic and keyword
    - 0.0 = Pure keyword search (best for code lookups)

    Examples:
    - "knee surgery" with semantic_weight=0.7 → Finds arthroscopy, arthroplasty, etc.
    - "99213" with semantic_weight=0.0 → Exact code match
    """
    api_key, user = api_key_data
    start_time = time.time()

    # Check rate limit
    await check_rate_limit(api_key, user)

    try:
        # Use config default for procedures (2025) if not specified
        year = version_year if version_year is not None else settings.DEFAULT_PROCEDURE_VERSION_YEAR

        # Perform hybrid search
        results = await hybrid_search(
            db=db,
            query_text=query,
            code_system=code_system,
            version_year=year,
            semantic_weight=semantic_weight,
            limit=limit
        )

        # Build response with combined scores and facets
        response_items = []
        for code, score in results:
            # Get facets for this code
            from app.models.procedure_code_facet import ProcedureCodeFacet
            from sqlalchemy import and_
            facets = db.query(ProcedureCodeFacet).filter(
                and_(
                    ProcedureCodeFacet.code == code.code,
                    ProcedureCodeFacet.code_system == code.code_system
                )
            ).first()

            code_dict = {
                "id": code.id,
                "code": code.code,
                "code_system": code.code_system,
                "description": code.get_display_description(),  # Add description for UI (uses paraphrased for license safety)
                "paraphrased_desc": code.paraphrased_desc,
                "short_desc": code.short_desc if code.license_status == 'AMA_licensed' else None,
                "long_desc": code.long_desc if code.license_status == 'AMA_licensed' else None,
                "category": code.category,
                "procedure_type": code.procedure_type,
                "version_year": code.version_year,
                "is_active": code.is_active,
                "effective_date": code.effective_date,
                "expiry_date": code.expiry_date,
                "license_status": code.license_status,
                "relative_value_units": code.relative_value_units,
                "global_period": code.global_period,
                "modifier_51_exempt": code.modifier_51_exempt,
                "created_at": code.created_at,
                "last_updated": code.last_updated
            }
            response_items.append({
                "code_info": code_dict,
                "facets": facets,
                "mappings": [],
                "similarity": score
            })

        # Log the request
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/procedure/hybrid-search",
            method="GET",
            query_params={"query": query, "code_system": code_system, "version_year": version_year, "semantic_weight": semantic_weight, "limit": limit},
            status_code=200,
            response_time_ms=response_time_ms,
            ip_address=None
        )

        return {
            "query": query,
            "results": response_items,
            "total_results": len(response_items)
        }

    except Exception as e:
        # Log error
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/procedure/hybrid-search",
            method="GET",
            query_params={"query": query, "code_system": code_system, "version_year": version_year, "limit": limit},
            status_code=500,
            response_time_ms=response_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail=f"Hybrid search error: {str(e)}")


@router.get("/faceted-search", response_model=list[ProcedureCodeResponse])
async def faceted_search_procedures(
    body_region: str | None = Query(None, description="Filter by body region (e.g., thorax, abdomen)"),
    body_system: str | None = Query(None, description="Filter by body system (e.g., cardiovascular)"),
    procedure_category: str | None = Query(None, description="Filter by category (e.g., surgical, evaluation)"),
    complexity_level: str | None = Query(None, description="Filter by complexity (e.g., moderate, complex)"),
    service_location: str | None = Query(None, description="Filter by location (e.g., office, hospital)"),
    em_level: str | None = Query(None, description="Filter by E/M level (e.g., level_3, level_4)"),
    em_patient_type: str | None = Query(None, description="Filter by patient type (e.g., new_patient)"),
    is_major_surgery: bool | None = Query(None, description="Filter by major surgery flag"),
    imaging_modality: str | None = Query(None, description="Filter by imaging type (e.g., ct, mri)"),
    code_system: str | None = Query(None, description="Filter by CPT or HCPCS"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Search procedure codes by clinical facets (AI-generated metadata).
    Filter codes by procedure characteristics like body region, complexity, location, etc.

    Example facet values:
    - body_region: "head_neck", "thorax", "abdomen", "upper_extremity", "lower_extremity"
    - body_system: "cardiovascular", "respiratory", "digestive", "musculoskeletal"
    - procedure_category: "evaluation", "surgical", "diagnostic_imaging", "laboratory"
    - complexity_level: "simple", "moderate", "complex", "highly_complex"
    - service_location: "office", "hospital_inpatient", "hospital_outpatient", "emergency"
    - em_level: "level_1", "level_2", "level_3", "level_4", "level_5"
    - imaging_modality: "xray", "ct", "mri", "ultrasound", "pet"

    Example use cases:
    - Find all moderate complexity office E/M visits
    - Find all knee surgical procedures
    - Find all inpatient critical care codes
    """
    api_key, user = api_key_data
    start_time = time.time()

    # Check rate limit
    await check_rate_limit(api_key, user)

    try:
        # Perform faceted search
        results = await faceted_search(
            db=db,
            body_region=body_region,
            body_system=body_system,
            procedure_category=procedure_category,
            complexity_level=complexity_level,
            service_location=service_location,
            em_level=em_level,
            em_patient_type=em_patient_type,
            is_major_surgery=is_major_surgery,
            imaging_modality=imaging_modality,
            code_system=code_system,
            limit=limit
        )

        # Format response
        response_items = []
        for code in results:
            response_items.append({
                "id": code.id,
                "code": code.code,
                "code_system": code.code_system,
                "description": code.get_display_description(),
                "category": code.category,
                "license_status": code.license_status,
                "version_year": code.version_year
            })

        # Log the request
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/procedure/faceted-search",
            method="GET",
            query_params={
                "body_region": body_region,
                "body_system": body_system,
                "procedure_category": procedure_category,
                "complexity_level": complexity_level,
                "service_location": service_location,
                "em_level": em_level,
                "limit": limit
            },
            status_code=200,
            response_time_ms=response_time_ms,
            ip_address=None
        )

        return response_items

    except Exception as e:
        # Log error
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/procedure/faceted-search",
            method="GET",
            query_params={"body_region": body_region, "procedure_category": procedure_category, "limit": limit},
            status_code=500,
            response_time_ms=response_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail=f"Faceted search error: {str(e)}")


@router.get("/{code}", response_model=ProcedureCodeDetailResponse)
async def get_procedure_code(
    code: str,
    code_system: str = Query("CPT", description="Code system (CPT or HCPCS)"),
    version_year: int | None = Query(None, description="Version year (defaults to most recent)"),
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific procedure code.
    Returns code details, facets, and cross-system mappings.

    Examples:
    - GET /procedure/99213?code_system=CPT → Returns E/M office visit details
    - GET /procedure/J0585?code_system=HCPCS → Returns botulinum toxin details
    """
    api_key, user = api_key_data
    start_time = time.time()

    # Check rate limit
    await check_rate_limit(api_key, user)

    try:
        # Use config default for procedures (2025) if not specified
        year = version_year if version_year is not None else settings.DEFAULT_PROCEDURE_VERSION_YEAR

        # Get code with details
        result = await get_code_with_details(
            db=db,
            code=code,
            code_system=code_system,
            version_year=year
        )

        if not result:
            raise HTTPException(status_code=404, detail=f"Procedure code {code} not found")

        # Format response
        procedure_code = result["code_info"]
        facets = result["facets"]
        mappings = result["mappings"]

        code_dict = {
            "id": procedure_code.id,
            "code": procedure_code.code,
            "code_system": procedure_code.code_system,
            "description": procedure_code.get_display_description(),  # Add description for UI (uses paraphrased for license safety)
            "paraphrased_desc": procedure_code.paraphrased_desc,
            "short_desc": procedure_code.short_desc if procedure_code.license_status == 'AMA_licensed' else None,
            "long_desc": procedure_code.long_desc if procedure_code.license_status == 'AMA_licensed' else None,
            "category": procedure_code.category,
            "procedure_type": procedure_code.procedure_type,
            "version_year": procedure_code.version_year,
            "is_active": procedure_code.is_active,
            "effective_date": procedure_code.effective_date,
            "expiry_date": procedure_code.expiry_date,
            "license_status": procedure_code.license_status,
            "relative_value_units": procedure_code.relative_value_units,
            "global_period": procedure_code.global_period,
            "modifier_51_exempt": procedure_code.modifier_51_exempt,
            "created_at": procedure_code.created_at,
            "last_updated": procedure_code.last_updated
        }

        # Log the request
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint=f"/api/v1/procedure/{code}",
            method="GET",
            query_params={"code_system": code_system, "version_year": version_year},
            status_code=200,
            response_time_ms=response_time_ms,
            ip_address=None
        )

        return {
            "code_info": code_dict,
            "facets": facets,
            "mappings": mappings,
            "similarity": None
        }

    except HTTPException:
        raise
    except Exception as e:
        # Log error with details
        logger.error(f"Error getting procedure code {code}: {str(e)}", exc_info=True)
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint=f"/api/v1/procedure/{code}",
            method="GET",
            query_params={"code_system": code_system},
            status_code=500,
            response_time_ms=response_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/suggest", response_model=ProcedureSemanticSearchResponse)
async def suggest_procedure_codes(
    clinical_text: str = Query(..., description="Clinical documentation text", min_length=10),
    code_system: str | None = Query(None, description="Filter by CPT or HCPCS"),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of suggestions"),
    min_similarity: float = Query(0.6, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Suggest procedure codes based on clinical documentation text.
    Useful for coding assistance and automated code suggestion features.

    This endpoint uses high-threshold semantic search optimized for clinical notes.

    Example:
    POST /procedure/suggest
    Body: {
        "clinical_text": "Patient presents for annual wellness exam. Reviewed medications,
                          performed comprehensive history and exam. Discussed preventive care.",
        "limit": 3
    }

    Returns: Suggested CPT codes like 99397 (preventive visit), 99213 (E/M), etc.
    """
    api_key, user = api_key_data
    start_time = time.time()

    # Check rate limit
    await check_rate_limit(api_key, user)

    try:
        # Get code suggestions
        results = await suggest_codes_from_text(
            db=db,
            clinical_text=clinical_text,
            code_system=code_system,
            limit=limit,
            min_similarity=min_similarity
        )

        # Build response with facets
        response_items = []
        for code, similarity in results:
            # Get facets for this code
            from app.models.procedure_code_facet import ProcedureCodeFacet
            from sqlalchemy import and_
            facets = db.query(ProcedureCodeFacet).filter(
                and_(
                    ProcedureCodeFacet.code == code.code,
                    ProcedureCodeFacet.code_system == code.code_system
                )
            ).first()

            code_dict = {
                "id": code.id,
                "code": code.code,
                "code_system": code.code_system,
                "description": code.get_display_description(),  # Add description for UI (uses paraphrased for license safety)
                "paraphrased_desc": code.paraphrased_desc,
                "short_desc": code.short_desc if code.license_status == 'AMA_licensed' else None,
                "long_desc": code.long_desc if code.license_status == 'AMA_licensed' else None,
                "category": code.category,
                "procedure_type": code.procedure_type,
                "version_year": code.version_year,
                "is_active": code.is_active,
                "effective_date": code.effective_date,
                "expiry_date": code.expiry_date,
                "license_status": code.license_status,
                "relative_value_units": code.relative_value_units,
                "global_period": code.global_period,
                "modifier_51_exempt": code.modifier_51_exempt,
                "created_at": code.created_at,
                "last_updated": code.last_updated
            }
            response_items.append({
                "code_info": code_dict,
                "facets": facets,
                "mappings": [],
                "similarity": similarity
            })

        # Log the request
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/procedure/suggest",
            method="POST",
            query_params={"code_system": code_system, "limit": limit, "min_similarity": min_similarity},
            status_code=200,
            response_time_ms=response_time_ms,
            ip_address=None
        )

        return {
            "query": clinical_text[:100] + "..." if len(clinical_text) > 100 else clinical_text,
            "results": response_items,
            "total_results": len(response_items)
        }

    except Exception as e:
        # Log error
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/procedure/suggest",
            method="POST",
            query_params={"limit": limit},
            status_code=500,
            response_time_ms=response_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail=f"Code suggestion error: {str(e)}")
