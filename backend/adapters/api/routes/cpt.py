"""CPT code search endpoints"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from infrastructure.db.postgres import get_db
from infrastructure.db.models.cpt_code import CPTCode
from infrastructure.db.models.api_key import APIKey
from infrastructure.db.models.user import User
from adapters.api.schemas.code import CPTResponse
from adapters.api.middleware.api_key import verify_api_key_with_usage
from adapters.api.middleware.rate_limit import check_rate_limit
from infrastructure.db.repositories.usage_repository import log_api_request
import time

router = APIRouter()


@router.get("/search", response_model=list[CPTResponse])
async def search_cpt(
    query: str = Query(..., description="Search query (code or description)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Search CPT codes by code or description.
    Supports exact code match and fuzzy text search.
    """
    api_key, user = api_key_data
    start_time = time.time()

    # Check rate limit
    await check_rate_limit(api_key, user)

    try:
        # Search by exact code match first
        results = db.query(CPTCode).filter(
            CPTCode.code.ilike(f"{query}%")
        ).limit(limit).all()

        # If no exact matches, do fuzzy text search on description
        if not results:
            results = db.query(CPTCode).filter(
                CPTCode.description.ilike(f"%{query}%")
            ).limit(limit).all()

        # Log the request
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/cpt/search",
            method="GET",
            query_params={"query": query, "limit": limit},
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
            endpoint="/api/v1/cpt/search",
            method="GET",
            query_params={"query": query, "limit": limit},
            status_code=500,
            response_time_ms=response_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail="Internal server error")
