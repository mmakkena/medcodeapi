"""AI-powered clinical note coding endpoint using LLM + semantic search"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from app.database import get_db
from app.models.api_key import APIKey
from app.models.user import User
from app.middleware.api_key import verify_api_key_with_usage
from app.middleware.rate_limit import check_rate_limit
from app.services.usage_service import log_api_request
from app.services.icd10_search_service import semantic_search as icd10_semantic_search
from app.services.procedure_search_service import semantic_search as procedure_semantic_search
import time
import logging
import os
import anthropic

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Request/Response Schemas
# ============================================================================

class ClinicalNoteRequest(BaseModel):
    """Request schema for clinical note coding"""
    clinical_note: str = Field(..., min_length=50, description="Full clinical documentation text")
    max_codes_per_type: int = Field(5, ge=1, le=20, description="Max codes to return per type")
    include_explanations: bool = Field(True, description="Include AI explanations for suggested codes")
    version_year: Optional[int] = Field(None, description="Filter by code version year")


class CodeSuggestion(BaseModel):
    """Individual code suggestion with metadata"""
    code: str
    code_system: str  # ICD10-CM, CPT, HCPCS
    description: str
    confidence_score: float  # 0-1
    similarity_score: float  # 0-1 from semantic search
    suggestion_type: str  # primary_diagnosis, secondary_diagnosis, procedure
    explanation: Optional[str] = None  # Why this code was suggested


class ClinicalCodingResponse(BaseModel):
    """Response schema for clinical note coding"""
    clinical_note_summary: str
    primary_diagnoses: List[CodeSuggestion]
    secondary_diagnoses: List[CodeSuggestion]
    procedures: List[CodeSuggestion]
    total_suggestions: int
    processing_time_ms: int


# ============================================================================
# LLM Entity Extraction
# ============================================================================

async def extract_clinical_entities(clinical_note: str) -> dict:
    """
    Use Claude to extract structured clinical entities from free-text notes

    Returns:
        {
            "summary": str,
            "primary_diagnoses": [str],
            "secondary_diagnoses": [str],
            "procedures": [str],
            "chief_complaint": str
        }
    """
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY not set, using fallback extraction")
        return fallback_entity_extraction(clinical_note)

    try:
        client = anthropic.Anthropic(api_key=anthropic_api_key)

        prompt = f"""You are a medical coding expert. Analyze this clinical note and extract structured information.

Clinical Note:
{clinical_note}

Extract and return ONLY a JSON object (no other text) with this structure:
{{
    "summary": "Brief 1-2 sentence summary of the visit",
    "chief_complaint": "Main reason for visit",
    "primary_diagnoses": ["diagnosis 1", "diagnosis 2"],
    "secondary_diagnoses": ["secondary diagnosis 1"],
    "procedures": ["procedure 1", "procedure 2"],
    "symptoms": ["symptom 1", "symptom 2"]
}}

Rules:
- Primary diagnoses are the main conditions being treated
- Secondary diagnoses are comorbidities or history
- Procedures include tests, surgeries, treatments performed
- Use medical terminology suitable for code search
- Return ONLY valid JSON, no markdown or extra text"""

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON response
        import json
        response_text = message.content[0].text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]

        entities = json.loads(response_text)
        logger.info(f"Successfully extracted entities: {entities}")
        return entities

    except Exception as e:
        logger.error(f"LLM extraction failed: {e}, using fallback")
        return fallback_entity_extraction(clinical_note)


def fallback_entity_extraction(clinical_note: str) -> dict:
    """Simple keyword-based fallback when LLM is unavailable"""
    # Basic extraction - just split into sentences and use as queries
    sentences = [s.strip() for s in clinical_note.split('.') if len(s.strip()) > 20]

    return {
        "summary": sentences[0] if sentences else clinical_note[:100],
        "chief_complaint": sentences[0] if sentences else "",
        "primary_diagnoses": sentences[:2] if len(sentences) >= 2 else [clinical_note[:100]],
        "secondary_diagnoses": sentences[2:3] if len(sentences) >= 3 else [],
        "procedures": [s for s in sentences if any(word in s.lower() for word in ['perform', 'procedure', 'test', 'surgery'])],
        "symptoms": []
    }


# ============================================================================
# Semantic Code Search
# ============================================================================

async def search_diagnosis_codes(
    query_texts: List[str],
    db: Session,
    version_year: Optional[int],
    limit: int
) -> List[tuple]:
    """Search ICD-10 codes for diagnosis queries"""
    all_results = []

    for query in query_texts[:3]:  # Limit to top 3 queries
        if not query or len(query) < 3:
            continue

        try:
            results = await icd10_semantic_search(
                db=db,
                query_text=query,
                code_system=None,
                version_year=version_year,
                limit=limit,
                min_similarity=0.7
            )
            all_results.extend(results)
        except Exception as e:
            logger.error(f"ICD-10 search failed for '{query}': {e}")

    # Deduplicate and sort by similarity
    seen_codes = set()
    unique_results = []
    for code, similarity in sorted(all_results, key=lambda x: x[1], reverse=True):
        if code.code not in seen_codes:
            seen_codes.add(code.code)
            unique_results.append((code, similarity))

    return unique_results[:limit]


async def search_procedure_codes(
    query_texts: List[str],
    db: Session,
    version_year: Optional[int],
    limit: int
) -> List[tuple]:
    """Search CPT/HCPCS codes for procedure queries"""
    all_results = []

    for query in query_texts[:3]:  # Limit to top 3 queries
        if not query or len(query) < 3:
            continue

        try:
            results = await procedure_semantic_search(
                db=db,
                query_text=query,
                code_system=None,
                version_year=version_year,
                limit=limit,
                min_similarity=0.7
            )
            all_results.extend(results)
        except Exception as e:
            logger.error(f"Procedure search failed for '{query}': {e}")

    # Deduplicate and sort by similarity
    seen_codes = set()
    unique_results = []
    for code, similarity in sorted(all_results, key=lambda x: x[1], reverse=True):
        if code.code not in seen_codes:
            seen_codes.add(code.code)
            unique_results.append((code, similarity))

    return unique_results[:limit]


# ============================================================================
# Main Endpoint
# ============================================================================

@router.post("/clinical-coding", response_model=ClinicalCodingResponse)
async def code_clinical_note(
    request: ClinicalNoteRequest,
    api_key_data: tuple[APIKey, User] = Depends(verify_api_key_with_usage),
    db: Session = Depends(get_db)
):
    """
    AI-powered clinical note coding that extracts diagnoses and procedures
    from free-text clinical documentation and suggests ICD-10 and CPT/HCPCS codes.

    This endpoint uses:
    1. LLM (Claude) for entity extraction and clinical understanding
    2. Semantic search (MedCPT embeddings) for accurate code matching
    3. Confidence scoring based on similarity and context

    Example clinical note:
    "Patient presents with acute chest pain radiating to left arm. History of
    hypertension and hyperlipidemia. EKG shows ST elevation in leads II, III, aVF.
    Diagnosed with acute ST elevation myocardial infarction (STEMI). Emergency
    cardiac catheterization performed with placement of drug-eluting stent to
    right coronary artery."
    """
    api_key, user = api_key_data
    start_time = time.time()

    # Check rate limit
    await check_rate_limit(api_key, user)

    try:
        # Step 1: Extract clinical entities using LLM
        logger.info(f"Extracting entities from note (length: {len(request.clinical_note)})")
        entities = await extract_clinical_entities(request.clinical_note)

        # Step 2: Search for diagnosis codes
        logger.info(f"Searching diagnosis codes for: {entities.get('primary_diagnoses', [])}")
        primary_dx_results = await search_diagnosis_codes(
            query_texts=entities.get('primary_diagnoses', []),
            db=db,
            version_year=request.version_year,
            limit=request.max_codes_per_type
        )

        logger.info(f"Searching secondary diagnosis codes for: {entities.get('secondary_diagnoses', [])}")
        secondary_dx_results = await search_diagnosis_codes(
            query_texts=entities.get('secondary_diagnoses', []),
            db=db,
            version_year=request.version_year,
            limit=request.max_codes_per_type
        )

        # Step 3: Search for procedure codes
        logger.info(f"Searching procedure codes for: {entities.get('procedures', [])}")
        procedure_results = await search_procedure_codes(
            query_texts=entities.get('procedures', []),
            db=db,
            version_year=request.version_year,
            limit=request.max_codes_per_type
        )

        # Step 4: Format results
        primary_diagnoses = [
            CodeSuggestion(
                code=code.code,
                code_system="ICD10-CM",
                description=code.get_display_description(),
                confidence_score=similarity * 0.95,  # Slightly lower for confidence
                similarity_score=similarity,
                suggestion_type="primary_diagnosis",
                explanation=f"Matched from: {entities.get('primary_diagnoses', [''])[0]}" if request.include_explanations else None
            )
            for code, similarity in primary_dx_results
        ]

        secondary_diagnoses = [
            CodeSuggestion(
                code=code.code,
                code_system="ICD10-CM",
                description=code.get_display_description(),
                confidence_score=similarity * 0.90,
                similarity_score=similarity,
                suggestion_type="secondary_diagnosis",
                explanation=f"Matched from: {entities.get('secondary_diagnoses', [''])[0]}" if request.include_explanations else None
            )
            for code, similarity in secondary_dx_results
        ]

        procedures = [
            CodeSuggestion(
                code=code.code,
                code_system=code.code_system,
                description=code.get_display_description(),
                confidence_score=similarity * 0.95,
                similarity_score=similarity,
                suggestion_type="procedure",
                explanation=f"Matched from: {entities.get('procedures', [''])[0]}" if request.include_explanations else None
            )
            for code, similarity in procedure_results
        ]

        total_suggestions = len(primary_diagnoses) + len(secondary_diagnoses) + len(procedures)
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Log the request
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/clinical-coding",
            method="POST",
            query_params={"note_length": len(request.clinical_note), "total_suggestions": total_suggestions},
            status_code=200,
            response_time_ms=processing_time_ms,
            ip_address=None
        )

        return ClinicalCodingResponse(
            clinical_note_summary=entities.get('summary', ''),
            primary_diagnoses=primary_diagnoses,
            secondary_diagnoses=secondary_diagnoses,
            procedures=procedures,
            total_suggestions=total_suggestions,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Clinical coding failed: {e}", exc_info=True)
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_request(
            db=db,
            api_key_id=api_key.id,
            user_id=user.id,
            endpoint="/api/v1/clinical-coding",
            method="POST",
            query_params={"note_length": len(request.clinical_note)},
            status_code=500,
            response_time_ms=response_time_ms,
            ip_address=None
        )
        raise HTTPException(status_code=500, detail=f"Clinical coding failed: {str(e)}")
