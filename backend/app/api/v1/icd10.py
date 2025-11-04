"""ICD-10 code search endpoints"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.database import get_db
from app.models.icd10_code import ICD10Code
from app.models.api_key import APIKey
from app.models.user import User
from app.schemas.code import ICD10Response
from app.middleware.api_key import verify_api_key_with_usage
from app.middleware.rate_limit import check_rate_limit
from app.services.usage_service import log_api_request
import time

router = APIRouter()


@router.get("/search", response_model=list[ICD10Response])
async def search_icd10(
    query: str = Query(..., description="Search query (code or description)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Search ICD-10 codes by code or description.
    Supports exact code match and fuzzy text search.
    """
    api_key, user = api_key_data
    start_time = time.time()

    # Check rate limit
    await check_rate_limit(api_key, user)

    try:
        # Search by exact code match first
        results = db.query(ICD10Code).filter(
            ICD10Code.code.ilike(f"{query}%")
        ).limit(limit).all()

        # If no exact matches, do fuzzy text search on description
        if not results:
            results = db.query(ICD10Code).filter(
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
            endpoint="/api/v1/icd10/search",
            method="GET",
            query_params={"query": query, "limit": limit},
            status_code=500,
            response_time_ms=response_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail="Internal server error")
