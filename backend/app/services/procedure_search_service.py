"""Procedure code (CPT/HCPCS) search service with semantic and hybrid search capabilities"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text

from app.models.procedure_code import ProcedureCode
from app.models.procedure_code_facet import ProcedureCodeFacet
from app.models.code_mapping import CodeMapping
from app.services.embedding_service import generate_embedding

logger = logging.getLogger(__name__)


async def semantic_search(
    db: Session,
    query_text: str,
    code_system: Optional[str] = None,
    version_year: Optional[int] = None,
    limit: int = 10,
    min_similarity: float = 0.0
) -> List[tuple[ProcedureCode, float]]:
    """
    Perform semantic search using vector similarity on procedure codes.

    Args:
        db: Database session
        query_text: Search query text (e.g., "office visit for diabetes")
        code_system: Optional filter by code system (CPT, HCPCS)
        version_year: Optional filter by version year (e.g., 2024, 2025)
        limit: Maximum number of results
        min_similarity: Minimum similarity threshold (0-1)

    Returns:
        List of (ProcedureCode, similarity_score) tuples sorted by similarity

    Note:
        Embeddings are generated from paraphrased_desc only (not AMA-licensed text)
        to comply with AMA copyright restrictions.
    """
    try:
        # Generate embedding for query
        query_embedding = generate_embedding(query_text)

        # Build query with vector similarity
        # Using cosine distance: 1 - (embedding <=> query_embedding)
        query = db.query(
            ProcedureCode,
            (1 - ProcedureCode.embedding.cosine_distance(query_embedding)).label('similarity')
        ).filter(
            ProcedureCode.embedding.isnot(None)
        )

        # Filter by code system if specified
        if code_system:
            query = query.filter(ProcedureCode.code_system == code_system)

        # Filter by version year if specified
        if version_year is not None:
            query = query.filter(ProcedureCode.version_year == version_year)

        # Filter by minimum similarity
        if min_similarity > 0:
            query = query.filter(
                (1 - ProcedureCode.embedding.cosine_distance(query_embedding)) >= min_similarity
            )

        # Order by similarity (highest first) and limit results
        results = query.order_by(text('similarity DESC')).limit(limit).all()

        return [(code, float(similarity)) for code, similarity in results]

    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        # Fallback to keyword search if semantic fails
        return await keyword_search(db, query_text, code_system, version_year, limit)


async def keyword_search(
    db: Session,
    query_text: str,
    code_system: Optional[str] = None,
    version_year: Optional[int] = None,
    limit: int = 10
) -> List[tuple[ProcedureCode, float]]:
    """
    Perform keyword-based full-text search on procedure codes.

    Args:
        db: Database session
        query_text: Search query text
        code_system: Optional filter by code system (CPT, HCPCS)
        version_year: Optional filter by version year
        limit: Maximum number of results

    Returns:
        List of (ProcedureCode, relevance_score) tuples

    Note:
        Searches both paraphrased (free) and licensed descriptions if available.
    """
    query = db.query(ProcedureCode)

    # Build search conditions
    search_conditions = []

    # Search in code (exact or partial match)
    search_conditions.append(ProcedureCode.code.ilike(f"%{query_text}%"))

    # Search in descriptions (paraphrased and licensed)
    search_conditions.append(ProcedureCode.paraphrased_desc.ilike(f"%{query_text}%"))
    search_conditions.append(ProcedureCode.short_desc.ilike(f"%{query_text}%"))
    search_conditions.append(ProcedureCode.long_desc.ilike(f"%{query_text}%"))

    # Search in category
    search_conditions.append(ProcedureCode.category.ilike(f"%{query_text}%"))

    # Combine conditions with OR
    query = query.filter(or_(*search_conditions))

    # Filter by code system if specified
    if code_system:
        query = query.filter(ProcedureCode.code_system == code_system)

    # Filter by version year if specified
    if version_year is not None:
        query = query.filter(ProcedureCode.version_year == version_year)

    # Filter by active codes only
    query = query.filter(ProcedureCode.is_active == True)

    # Limit results
    results = query.limit(limit).all()

    # Return with default relevance score of 0.5 for keyword matches
    return [(code, 0.5) for code in results]


async def hybrid_search(
    db: Session,
    query_text: str,
    code_system: Optional[str] = None,
    version_year: Optional[int] = None,
    semantic_weight: float = 0.7,
    limit: int = 10
) -> List[tuple[ProcedureCode, float]]:
    """
    Perform hybrid search combining semantic and keyword search.

    Args:
        db: Database session
        query_text: Search query text
        code_system: Optional filter by code system (CPT, HCPCS)
        version_year: Optional filter by version year
        semantic_weight: Weight for semantic results (0-1), keyword weight is (1 - semantic_weight)
        limit: Maximum number of results

    Returns:
        List of (ProcedureCode, combined_score) tuples

    Example:
        # 70% semantic, 30% keyword
        results = await hybrid_search(db, "knee arthroscopy", semantic_weight=0.7)
    """
    # Get both semantic and keyword results (fetch more to ensure good coverage)
    semantic_results = await semantic_search(db, query_text, code_system, version_year, limit * 2)
    keyword_results = await keyword_search(db, query_text, code_system, version_year, limit * 2)

    # Combine results with weighted scores
    combined_scores: Dict[str, tuple[ProcedureCode, float]] = {}

    # Add semantic results
    for code, score in semantic_results:
        key = f"{code.code}_{code.code_system}_{code.version_year}"
        combined_scores[key] = (code, score * semantic_weight)

    # Add/merge keyword results
    keyword_weight = 1 - semantic_weight
    for code, score in keyword_results:
        key = f"{code.code}_{code.code_system}_{code.version_year}"
        if key in combined_scores:
            # Combine scores
            existing_code, existing_score = combined_scores[key]
            combined_scores[key] = (existing_code, existing_score + (score * keyword_weight))
        else:
            combined_scores[key] = (code, score * keyword_weight)

    # Sort by combined score and return top results
    sorted_results = sorted(
        combined_scores.values(),
        key=lambda x: x[1],
        reverse=True
    )[:limit]

    return sorted_results


async def get_code_with_details(
    db: Session,
    code: str,
    code_system: str = "CPT",
    version_year: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific procedure code.

    Args:
        db: Database session
        code: Procedure code (e.g., "99213", "J0585")
        code_system: Code system (default: CPT)
        version_year: Optional filter by version year

    Returns:
        Dictionary with code info, facets, and mappings, or None if not found

    Example:
        details = await get_code_with_details(db, "99213", "CPT", 2025)
        # Returns: {"code_info": ProcedureCode, "facets": ProcedureCodeFacet, "mappings": [CodeMapping]}
    """
    # Build query for the code
    query = db.query(ProcedureCode).filter(
        and_(
            ProcedureCode.code == code,
            ProcedureCode.code_system == code_system
        )
    )

    # Filter by version year if specified
    if version_year is not None:
        query = query.filter(ProcedureCode.version_year == version_year)
    else:
        # Get most recent version if year not specified
        query = query.order_by(ProcedureCode.version_year.desc())

    procedure_code = query.first()

    if not procedure_code:
        return None

    # Get procedure facets
    facets = db.query(ProcedureCodeFacet).filter(
        and_(
            ProcedureCodeFacet.code == code,
            ProcedureCodeFacet.code_system == code_system
        )
    ).first()

    # Get code mappings (CPT to ICD-10, SNOMED, etc.)
    mappings = db.query(CodeMapping).filter(
        and_(
            CodeMapping.from_code == code,
            CodeMapping.from_system == code_system
        )
    ).all()

    return {
        "code_info": procedure_code,
        "facets": facets,
        "mappings": mappings
    }


async def faceted_search(
    db: Session,
    body_region: Optional[str] = None,
    body_system: Optional[str] = None,
    procedure_category: Optional[str] = None,
    complexity_level: Optional[str] = None,
    service_location: Optional[str] = None,
    em_level: Optional[str] = None,
    em_patient_type: Optional[str] = None,
    is_major_surgery: Optional[bool] = None,
    imaging_modality: Optional[str] = None,
    code_system: Optional[str] = None,
    limit: int = 50
) -> List[ProcedureCode]:
    """
    Search procedure codes by clinical facets.

    Args:
        db: Database session
        body_region: Filter by body region (e.g., "thorax", "abdomen")
        body_system: Filter by body system (e.g., "cardiovascular", "respiratory")
        procedure_category: Filter by category (e.g., "surgical", "diagnostic_imaging")
        complexity_level: Filter by complexity (e.g., "moderate", "complex")
        service_location: Filter by location (e.g., "office", "hospital_inpatient")
        em_level: Filter by E/M level (e.g., "level_3", "level_4")
        em_patient_type: Filter by patient type (e.g., "new_patient", "established_patient")
        is_major_surgery: Filter by major surgery flag
        imaging_modality: Filter by imaging type (e.g., "ct", "mri")
        code_system: Filter by CPT or HCPCS
        limit: Maximum number of results

    Returns:
        List of ProcedureCode objects matching the facets

    Example:
        # Find all moderate complexity office E/M visits
        codes = await faceted_search(
            db,
            procedure_category="evaluation",
            complexity_level="moderate",
            service_location="office"
        )
    """
    # Join with facets table
    query = db.query(ProcedureCode).join(
        ProcedureCodeFacet,
        and_(
            ProcedureCode.code == ProcedureCodeFacet.code,
            ProcedureCode.code_system == ProcedureCodeFacet.code_system
        )
    )

    # Build filter conditions
    filters = []

    if body_region:
        filters.append(ProcedureCodeFacet.body_region == body_region)
    if body_system:
        filters.append(ProcedureCodeFacet.body_system == body_system)
    if procedure_category:
        filters.append(ProcedureCodeFacet.procedure_category == procedure_category)
    if complexity_level:
        filters.append(ProcedureCodeFacet.complexity_level == complexity_level)
    if service_location:
        filters.append(ProcedureCodeFacet.service_location == service_location)
    if em_level:
        filters.append(ProcedureCodeFacet.em_level == em_level)
    if em_patient_type:
        filters.append(ProcedureCodeFacet.em_patient_type == em_patient_type)
    if is_major_surgery is not None:
        filters.append(ProcedureCodeFacet.is_major_surgery == is_major_surgery)
    if imaging_modality:
        filters.append(ProcedureCodeFacet.imaging_modality == imaging_modality)
    if code_system:
        filters.append(ProcedureCode.code_system == code_system)

    # Apply filters
    if filters:
        query = query.filter(and_(*filters))

    # Filter by active codes only
    query = query.filter(ProcedureCode.is_active == True)

    # Limit results
    return query.limit(limit).all()


async def get_code_mappings(
    db: Session,
    codes: List[str],
    from_system: str,
    to_system: str
) -> List[CodeMapping]:
    """
    Get code mappings for multiple procedure codes.

    Args:
        db: Database session
        codes: List of codes to map (e.g., ["99213", "99214"])
        from_system: Source code system (e.g., "CPT", "HCPCS")
        to_system: Target code system (e.g., "ICD10-CM", "SNOMED")

    Returns:
        List of CodeMapping objects

    Example:
        # Map CPT codes to ICD-10-CM
        mappings = await get_code_mappings(
            db,
            ["99213", "99214"],
            "CPT",
            "ICD10-CM"
        )
    """
    return db.query(CodeMapping).filter(
        and_(
            CodeMapping.from_code.in_(codes),
            CodeMapping.from_system == from_system,
            CodeMapping.to_system == to_system
        )
    ).all()


async def suggest_codes_from_text(
    db: Session,
    clinical_text: str,
    code_system: Optional[str] = None,
    limit: int = 5,
    min_similarity: float = 0.6
) -> List[tuple[ProcedureCode, float]]:
    """
    Suggest procedure codes based on clinical documentation text.

    This is a high-level semantic search optimized for clinical notes.
    Useful for coding assistance and suggestion features.

    Args:
        db: Database session
        clinical_text: Free-text clinical documentation
        code_system: Optional filter by code system (CPT, HCPCS)
        limit: Maximum number of suggestions
        min_similarity: Minimum similarity threshold (default 0.6 for suggestions)

    Returns:
        List of (ProcedureCode, similarity_score) tuples

    Example:
        text = "Patient presents for routine follow-up of type 2 diabetes.
                Reviewed medications and discussed diet."
        suggestions = await suggest_codes_from_text(db, text, limit=3)
        # Might return: 99213 (E/M office visit), 99214, etc.
    """
    return await semantic_search(
        db,
        clinical_text,
        code_system=code_system,
        limit=limit,
        min_similarity=min_similarity
    )
