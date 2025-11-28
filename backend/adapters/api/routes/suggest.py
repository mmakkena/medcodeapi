"""Code suggestion endpoint with keyword + fuzzy matching"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from infrastructure.db.postgres import get_db
from infrastructure.db.models.icd10_code import ICD10Code
from infrastructure.db.models.cpt_code import CPTCode
from infrastructure.db.models.api_key import APIKey
from infrastructure.db.models.user import User
from adapters.api.schemas.code import CodeSuggestionRequest, CodeSuggestionResponse, CodeSuggestion
from adapters.api.middleware.api_key import verify_api_key_with_usage
from adapters.api.middleware.rate_limit import check_rate_limit
from infrastructure.db.repositories.usage_repository import log_api_request
import time
import re
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from text"""
    # Remove punctuation and convert to lowercase
    text = re.sub(r'[^\w\s]', ' ', text.lower())

    # Common medical stop words to filter out
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'was', 'are', 'were', 'been', 'be',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
        'could', 'may', 'might', 'must', 'can', 'patient', 'presents', 'comes'
    }

    # Split and filter
    words = [w for w in text.split() if w not in stop_words and len(w) > 2]

    return words


def calculate_relevance_score(keywords: list[str], description: str) -> float:
    """Calculate relevance score based on keyword matches"""
    description_lower = description.lower()
    matches = sum(1 for keyword in keywords if keyword in description_lower)
    return matches / len(keywords) if keywords else 0.0


@router.post("/suggest", response_model=CodeSuggestionResponse)
async def suggest_codes(
    request: CodeSuggestionRequest,
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    Suggest relevant ICD-10 and CPT codes based on free-text clinical notes.
    Uses keyword extraction and fuzzy matching for MVP.

    Note: This can be enhanced with LLM integration for premium tier.
    """
    logger.info(f"[SUGGEST] Starting suggest_codes endpoint - text length: {len(request.text)}")
    api_key, user = api_key_data
    logger.info(f"[SUGGEST] Got API key and user - user_id: {user.id}")
    start_time = time.time()

    # Check rate limit
    logger.info(f"[SUGGEST] Checking rate limit for user: {user.id}")
    await check_rate_limit(api_key, user)
    logger.info(f"[SUGGEST] Rate limit check passed")

    try:
        # Extract keywords from input text
        logger.info(f"[SUGGEST] Extracting keywords from text: {request.text[:50]}...")
        keywords = extract_keywords(request.text)
        logger.info(f"[SUGGEST] Extracted {len(keywords)} keywords: {keywords}")

        if not keywords:
            return CodeSuggestionResponse(suggestions=[], query=request.text)

        suggestions = []

        # Search ICD-10 codes
        logger.info(f"[SUGGEST] Starting ICD-10 code search")
        for keyword in keywords[:5]:  # Limit to top 5 keywords
            logger.info(f"[SUGGEST] Querying ICD-10 for keyword: {keyword}")
            icd10_results = db.query(ICD10Code).filter(
                ICD10Code.description.ilike(f"%{keyword}%")
            ).limit(3).all()
            logger.info(f"[SUGGEST] Found {len(icd10_results)} ICD-10 results for '{keyword}'")

            for code in icd10_results:
                score = calculate_relevance_score(keywords, code.description)
                suggestions.append(CodeSuggestion(
                    code=code.code,
                    description=code.description,
                    score=score,
                    type="icd10"
                ))

        # Search CPT codes
        logger.info(f"[SUGGEST] Starting CPT code search")
        for keyword in keywords[:5]:
            logger.info(f"[SUGGEST] Querying CPT for keyword: {keyword}")
            cpt_results = db.query(CPTCode).filter(
                CPTCode.description.ilike(f"%{keyword}%")
            ).limit(3).all()
            logger.info(f"[SUGGEST] Found {len(cpt_results)} CPT results for '{keyword}'")

            for code in cpt_results:
                score = calculate_relevance_score(keywords, code.description)
                suggestions.append(CodeSuggestion(
                    code=code.code,
                    description=code.description,
                    score=score,
                    type="cpt"
                ))

        # Sort by relevance score and deduplicate
        logger.info(f"[SUGGEST] Sorting and deduplicating {len(suggestions)} suggestions")
        seen_codes = set()
        unique_suggestions = []
        for suggestion in sorted(suggestions, key=lambda x: x.score, reverse=True):
            if suggestion.code not in seen_codes:
                seen_codes.add(suggestion.code)
                unique_suggestions.append(suggestion)

        # Limit to max_results
        final_suggestions = unique_suggestions[:request.max_results]
        logger.info(f"[SUGGEST] Returning {len(final_suggestions)} final suggestions")

        # Log the request
        logger.info(f"[SUGGEST] Logging API request")
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/suggest",
            method="POST",
            query_params={"text_length": len(request.text)},
            status_code=200,
            response_time_ms=response_time_ms,
            ip_address=None
        )

        logger.info(f"[SUGGEST] Successfully completed request in {response_time_ms}ms")
        return CodeSuggestionResponse(
            suggestions=final_suggestions,
            query=request.text
        )

    except Exception as e:
        # Log error
        logger.error(f"[SUGGEST] Error occurred: {str(e)}", exc_info=True)
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/suggest",
            method="POST",
            query_params={"text_length": len(request.text)},
            status_code=500,
            response_time_ms=response_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail="Internal server error")
