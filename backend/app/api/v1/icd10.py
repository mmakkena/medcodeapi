"""ICD-10 code search endpoints"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.database import get_db
from app.models.icd10_code import ICD10Code
from app.models.api_key import APIKey
from app.models.user import User
from app.schemas.code import (
    ICD10Response,
    ICD10DetailResponse,
    ICD10EnhancedResponse,
    ICD10AIFacetResponse,
    CodeMappingResponse,
    SemanticSearchResponse
)
from app.middleware.api_key import verify_api_key_with_usage
from app.middleware.rate_limit import check_rate_limit
from app.services.usage_service import log_api_request
from app.services.icd10_search_service import (
    semantic_search,
    hybrid_search,
    faceted_search,
    get_code_with_details
)
import time

router = APIRouter()


@router.get("/search", response_model=list[ICD10Response])
async def search_icd10(
    query: str = Query(..., description="Search query (code or description)"),
    version_year: int | None = Query(None, description="Filter by version year (e.g., 2024, 2025, 2026)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Search ICD-10 codes by code or description.
    Supports exact code match and fuzzy text search.

    Use version_year to search within a specific year's codes (e.g., 2026).
    If not specified, searches across all versions.
    """
    api_key, user = api_key_data
    start_time = time.time()

    # Check rate limit
    await check_rate_limit(api_key, user)

    try:
        # Build base query
        base_query = db.query(ICD10Code)

        # Add version_year filter if specified
        if version_year:
            base_query = base_query.filter(ICD10Code.version_year == version_year)

        # Search by exact code match first
        results = base_query.filter(
            ICD10Code.code.ilike(f"{query}%")
        ).limit(limit).all()

        # If no exact matches, do fuzzy text search on description
        if not results:
            description_query = db.query(ICD10Code)
            if version_year:
                description_query = description_query.filter(ICD10Code.version_year == version_year)

            results = description_query.filter(
                ICD10Code.description.ilike(f"%{query}%")
            ).limit(limit).all()

        # Log the request
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/icd10/search",
            method="GET",
            query_params={"query": query, "version_year": version_year, "limit": limit},
            status_code=200,
            response_time_ms=response_time_ms,
            ip_address=None
        )

        return results

    except Exception as e:
        # Log error
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/icd10/search",
            method="GET",
            query_params={"query": query, "version_year": version_year, "limit": limit},
            status_code=500,
            response_time_ms=response_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/semantic-search", response_model=SemanticSearchResponse)
async def semantic_search_icd10(
    query: str = Query(..., description="Query text for semantic search", min_length=1),
    code_system: str | None = Query(None, description="Filter by code system (ICD10-CM, ICD10-PCS)"),
    version_year: int | None = Query(None, description="Filter by version year (e.g., 2024, 2025, 2026)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    min_similarity: float = Query(0.0, ge=0.0, le=1.0, description="Minimum similarity threshold (0-1)"),
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Semantic search using AI embeddings for natural language queries.
    Returns codes most similar to the query text based on meaning, not just keywords.

    Example: "patient with chest pain and difficulty breathing" will find relevant cardiopulmonary codes

    Use version_year to search within a specific year's coding guidelines (e.g., 2026).
    """
    api_key, user = api_key_data
    start_time = time.time()

    # Check rate limit
    await check_rate_limit(api_key, user)

    try:
        # Perform semantic search
        results = await semantic_search(
            db=db,
            query_text=query,
            code_system=code_system,
            version_year=version_year,
            limit=limit,
            min_similarity=min_similarity
        )

        # Build response with similarity scores
        response_items = []
        for code, similarity in results:
            # Create enhanced response
            code_dict = {
                "id": code.id,
                "code": code.code,
                "code_system": code.code_system,
                "short_desc": code.short_desc,
                "long_desc": code.long_desc,
                "chapter": code.chapter,
                "block_range": code.block_range,
                "category": code.category,
                "is_active": code.is_active,
                "version_year": code.version_year,
                "effective_date": code.effective_date,
                "expiry_date": code.expiry_date,
                "last_updated": code.last_updated,
                "description": code.description
            }
            response_items.append({
                "code_info": code_dict,
                "facets": None,
                "mappings": [],
                "similarity": similarity
            })

        # Log the request
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/icd10/semantic-search",
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
            endpoint="/api/v1/icd10/semantic-search",
            method="GET",
            query_params={"query": query, "code_system": code_system, "version_year": version_year, "limit": limit},
            status_code=500,
            response_time_ms=response_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail=f"Semantic search error: {str(e)}")


@router.get("/hybrid-search", response_model=SemanticSearchResponse)
async def hybrid_search_icd10(
    query: str = Query(..., description="Query text for hybrid search", min_length=1),
    code_system: str | None = Query(None, description="Filter by code system (ICD10-CM, ICD10-PCS)"),
    version_year: int | None = Query(None, description="Filter by version year (e.g., 2024, 2025, 2026)"),
    semantic_weight: float = Query(0.7, ge=0.0, le=1.0, description="Weight for semantic results (0-1)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Hybrid search combining semantic (AI embeddings) and keyword matching.
    Provides best of both worlds - finds semantically similar codes AND exact keyword matches.

    The semantic_weight parameter controls the balance:
    - 1.0 = Pure semantic search
    - 0.5 = Equal weight for semantic and keyword
    - 0.0 = Pure keyword search

    Use version_year to search within a specific year's coding guidelines (e.g., 2026).
    """
    api_key, user = api_key_data
    start_time = time.time()

    # Check rate limit
    await check_rate_limit(api_key, user)

    try:
        # Perform hybrid search
        results = await hybrid_search(
            db=db,
            query_text=query,
            code_system=code_system,
            version_year=version_year,
            semantic_weight=semantic_weight,
            limit=limit
        )

        # Build response with combined scores
        response_items = []
        for code, score in results:
            code_dict = {
                "id": code.id,
                "code": code.code,
                "code_system": code.code_system,
                "short_desc": code.short_desc,
                "long_desc": code.long_desc,
                "chapter": code.chapter,
                "block_range": code.block_range,
                "category": code.category,
                "is_active": code.is_active,
                "version_year": code.version_year,
                "effective_date": code.effective_date,
                "expiry_date": code.expiry_date,
                "last_updated": code.last_updated,
                "description": code.description
            }
            response_items.append({
                "code_info": code_dict,
                "facets": None,
                "mappings": [],
                "similarity": score
            })

        # Log the request
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/icd10/hybrid-search",
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
            endpoint="/api/v1/icd10/hybrid-search",
            method="GET",
            query_params={"query": query, "code_system": code_system, "version_year": version_year, "limit": limit},
            status_code=500,
            response_time_ms=response_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail=f"Hybrid search error: {str(e)}")


@router.get("/faceted-search", response_model=list[ICD10Response])
async def faceted_search_icd10(
    body_system: str | None = Query(None, description="Filter by body system"),
    concept_type: str | None = Query(None, description="Filter by concept type"),
    chronicity: str | None = Query(None, description="Filter by chronicity"),
    severity: str | None = Query(None, description="Filter by severity"),
    acuity: str | None = Query(None, description="Filter by acuity"),
    risk_flag: bool | None = Query(None, description="Filter by risk flag"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Search ICD-10 codes by clinical facets (AI-generated metadata).
    Filter codes by clinical characteristics like body system, severity, chronicity, etc.

    Example facet values:
    - body_system: "Cardiovascular", "Respiratory", "Neurological", etc.
    - concept_type: "Disease", "Symptom", "Injury", etc.
    - chronicity: "Acute", "Chronic", "Subacute"
    - severity: "Mild", "Moderate", "Severe"
    - acuity: "Emergent", "Urgent", "Non-urgent"
    """
    api_key, user = api_key_data
    start_time = time.time()

    # Check rate limit
    await check_rate_limit(api_key, user)

    try:
        # Perform faceted search
        results = await faceted_search(
            db=db,
            body_system=body_system,
            concept_type=concept_type,
            chronicity=chronicity,
            severity=severity,
            acuity=acuity,
            risk_flag=risk_flag,
            limit=limit
        )

        # Log the request
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/icd10/faceted-search",
            method="GET",
            query_params={
                "body_system": body_system,
                "concept_type": concept_type,
                "chronicity": chronicity,
                "severity": severity,
                "acuity": acuity,
                "risk_flag": risk_flag,
                "limit": limit
            },
            status_code=200,
            response_time_ms=response_time_ms,
            ip_address=None
        )

        return results

    except Exception as e:
        # Log error
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/icd10/faceted-search",
            method="GET",
            query_params={"body_system": body_system, "limit": limit},
            status_code=500,
            response_time_ms=response_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail=f"Faceted search error: {str(e)}")
