"""ICD-10 search service with semantic and hybrid search capabilities"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text

from infrastructure.db.models.icd10_code import ICD10Code
from infrastructure.db.models.icd10_ai_facet import ICD10AIFacet
from infrastructure.db.models.code_mapping import CodeMapping
from infrastructure.llm.embedding_engine import generate_embedding
from domain.semantic_search.search_enhancements import enhance_search_results, log_score_distribution

logger = logging.getLogger(__name__)


async def semantic_search(
    db: Session,
    query_text: str,
    code_system: Optional[str] = None,
    version_year: Optional[int] = None,
    limit: int = 10,
    min_similarity: float = 0.0,
    enhance_scores: bool = True
) -> List[tuple[ICD10Code, float]]:
    """
    Perform semantic search using vector similarity.

    Args:
        db: Database session
        query_text: Search query text
        code_system: Optional filter by code system (ICD10, ICD10-CM, ICD10-PCS)
        version_year: Optional filter by version year (e.g., 2024, 2025, 2026)
        limit: Maximum number of results
        min_similarity: Minimum similarity threshold (0-1)
        enhance_scores: Whether to apply score enhancement (exact match boosting, calibration)

    Returns:
        List of (ICD10Code, similarity_score) tuples sorted by similarity
    """
    try:
        # Generate embedding for query
        query_embedding = generate_embedding(query_text)

        # Build query with vector similarity
        # Using cosine distance: 1 - (embedding <=> query_embedding)
        query = db.query(
            ICD10Code,
            (1 - ICD10Code.embedding.cosine_distance(query_embedding)).label('similarity')
        ).filter(
            ICD10Code.embedding.isnot(None)
        )

        # Filter by code system if specified
        if code_system:
            query = query.filter(ICD10Code.code_system == code_system)

        # Filter by version year if specified
        if version_year is not None:
            query = query.filter(ICD10Code.version_year == version_year)

        # Filter by minimum similarity (only apply if not enhancing, as enhancement changes scores)
        if min_similarity > 0 and not enhance_scores:
            query = query.filter(
                (1 - ICD10Code.embedding.cosine_distance(query_embedding)) >= min_similarity
            )

        # Order by similarity (highest first) and fetch more results for enhancement
        fetch_limit = limit * 3 if enhance_scores else limit
        results = query.order_by(text('similarity DESC')).limit(fetch_limit).all()

        raw_results = [(code, float(similarity)) for code, similarity in results]

        # Log raw score distribution for debugging
        if raw_results:
            log_score_distribution(raw_results, "Raw ICD-10 semantic search")

        # Apply score enhancements
        if enhance_scores and raw_results:
            enhanced_results = enhance_search_results(
                raw_results,
                query_text,
                code_field='code',
                description_fields=['short_desc', 'long_desc', 'description'],
                apply_calibration=True,
                apply_boosting=True,
                calibration_params={
                    'min_score': 0.5,   # Scores below 50% get compressed toward 0
                    'max_score': 0.95,  # Assume max realistic similarity is 95%
                    'power': 0.6        # Slightly spread out high scores
                }
            )

            # Log enhanced score distribution
            log_score_distribution(enhanced_results, "Enhanced ICD-10 semantic search")

            # Apply min_similarity filter after enhancement if specified
            if min_similarity > 0:
                enhanced_results = [(code, score) for code, score in enhanced_results if score >= min_similarity]

            # Return top results after enhancement
            return enhanced_results[:limit]

        return raw_results

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
) -> List[tuple[ICD10Code, float]]:
    """
    Perform keyword-based full-text search.

    Args:
        db: Database session
        query_text: Search query text
        code_system: Optional filter by code system
        version_year: Optional filter by version year
        limit: Maximum number of results

    Returns:
        List of (ICD10Code, relevance_score) tuples
    """
    query = db.query(ICD10Code)

    # Build search conditions
    search_conditions = []

    # Search in code (exact or partial match)
    search_conditions.append(ICD10Code.code.ilike(f"%{query_text}%"))

    # Search in descriptions
    search_conditions.append(ICD10Code.short_desc.ilike(f"%{query_text}%"))
    search_conditions.append(ICD10Code.long_desc.ilike(f"%{query_text}%"))
    search_conditions.append(ICD10Code.description.ilike(f"%{query_text}%"))  # Legacy field

    # Combine conditions with OR
    query = query.filter(or_(*search_conditions))

    # Filter by code system if specified
    if code_system:
        query = query.filter(ICD10Code.code_system == code_system)

    # Filter by version year if specified
    if version_year is not None:
        query = query.filter(ICD10Code.version_year == version_year)

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
    limit: int = 10,
    enhance_scores: bool = True
) -> List[tuple[ICD10Code, float]]:
    """
    Perform hybrid search combining semantic and keyword search.

    Args:
        db: Database session
        query_text: Search query text
        code_system: Optional filter by code system
        version_year: Optional filter by version year
        semantic_weight: Weight for semantic results (0-1), keyword weight is (1 - semantic_weight)
        limit: Maximum number of results
        enhance_scores: Whether to apply score enhancement

    Returns:
        List of (ICD10Code, combined_score) tuples
    """
    # Get both semantic and keyword results
    semantic_results = await semantic_search(
        db, query_text, code_system, version_year, limit * 2, enhance_scores=enhance_scores
    )
    keyword_results = await keyword_search(db, query_text, code_system, version_year, limit * 2)

    # Combine results with weighted scores
    combined_scores: Dict[str, tuple[ICD10Code, float]] = {}

    # Add semantic results
    for code, score in semantic_results:
        key = f"{code.code}_{code.code_system}"
        combined_scores[key] = (code, score * semantic_weight)

    # Add/merge keyword results
    keyword_weight = 1 - semantic_weight
    for code, score in keyword_results:
        key = f"{code.code}_{code.code_system}"
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
    code_system: str = "ICD10-CM",
    version_year: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific ICD-10 code.

    Args:
        db: Database session
        code: ICD-10 code
        code_system: Code system (default: ICD10-CM)
        version_year: Optional filter by version year

    Returns:
        Dictionary with code info, facets, and mappings, or None if not found
    """
    # Build query for the code
    query = db.query(ICD10Code).filter(
        and_(
            ICD10Code.code == code,
            ICD10Code.code_system == code_system
        )
    )

    # Filter by version year if specified
    if version_year is not None:
        query = query.filter(ICD10Code.version_year == version_year)

    icd_code = query.first()

    if not icd_code:
        return None

    # Get AI facets
    facets = db.query(ICD10AIFacet).filter(
        and_(
            ICD10AIFacet.code == code,
            ICD10AIFacet.code_system == code_system
        )
    ).first()

    # Get code mappings
    mappings = db.query(CodeMapping).filter(
        and_(
            CodeMapping.from_code == code,
            CodeMapping.from_system == code_system
        )
    ).all()

    return {
        "code_info": icd_code,
        "facets": facets,
        "mappings": mappings
    }


async def faceted_search(
    db: Session,
    body_system: Optional[str] = None,
    concept_type: Optional[str] = None,
    chronicity: Optional[str] = None,
    severity: Optional[str] = None,
    acuity: Optional[str] = None,
    risk_flag: Optional[bool] = None,
    limit: int = 50
) -> List[ICD10Code]:
    """
    Search ICD-10 codes by clinical facets.

    Args:
        db: Database session
        body_system: Filter by body system
        concept_type: Filter by concept type
        chronicity: Filter by chronicity
        severity: Filter by severity
        acuity: Filter by acuity
        risk_flag: Filter by risk flag
        limit: Maximum number of results

    Returns:
        List of ICD10Code objects matching the facets
    """
    # Join with facets table
    query = db.query(ICD10Code).join(
        ICD10AIFacet,
        and_(
            ICD10Code.code == ICD10AIFacet.code,
            ICD10Code.code_system == ICD10AIFacet.code_system
        )
    )

    # Build filter conditions
    filters = []
    if body_system:
        filters.append(ICD10AIFacet.body_system == body_system)
    if concept_type:
        filters.append(ICD10AIFacet.concept_type == concept_type)
    if chronicity:
        filters.append(ICD10AIFacet.chronicity == chronicity)
    if severity:
        filters.append(ICD10AIFacet.severity == severity)
    if acuity:
        filters.append(ICD10AIFacet.acuity == acuity)
    if risk_flag is not None:
        filters.append(ICD10AIFacet.risk_flag == risk_flag)

    # Apply filters
    if filters:
        query = query.filter(and_(*filters))

    # Limit results
    return query.limit(limit).all()


async def get_code_mappings(
    db: Session,
    codes: List[str],
    from_system: str,
    to_system: str
) -> List[CodeMapping]:
    """
    Get code mappings for multiple codes.

    Args:
        db: Database session
        codes: List of codes to map
        from_system: Source code system
        to_system: Target code system

    Returns:
        List of CodeMapping objects
    """
    return db.query(CodeMapping).filter(
        and_(
            CodeMapping.from_code.in_(codes),
            CodeMapping.from_system == from_system,
            CodeMapping.to_system == to_system
        )
    ).all()
