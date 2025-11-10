"""Medical code schemas"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date, datetime
from typing import Optional, List, Dict, Any


class ICD10Response(BaseModel):
    """Schema for ICD-10 code response (backward compatible)"""
    id: UUID
    code: str
    description: str
    category: str | None

    class Config:
        from_attributes = True


class ICD10EnhancedResponse(BaseModel):
    """Enhanced schema for ICD-10 code with all new fields"""
    id: UUID
    code: str
    code_system: str
    short_desc: Optional[str] = None
    long_desc: Optional[str] = None
    chapter: Optional[str] = None
    block_range: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True
    version_year: Optional[int] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    last_updated: datetime

    # Year-specific guideline fields (populated from official ICD-10-CM guidelines)
    coding_guidelines: Optional[str] = None
    clinical_notes: Optional[str] = None
    coding_tips: Optional[str] = None

    # Legacy field for backward compatibility
    description: Optional[str] = None

    class Config:
        from_attributes = True


class ICD10AIFacetResponse(BaseModel):
    """Schema for ICD-10 AI facets"""
    code: str
    code_system: str
    concept_type: Optional[str] = None
    body_system: Optional[str] = None
    acuity: Optional[str] = None
    severity: Optional[str] = None
    chronicity: Optional[str] = None
    laterality: Optional[str] = None
    onset_context: Optional[str] = None
    age_band: Optional[str] = None
    sex_specific: Optional[str] = None
    risk_flag: Optional[bool] = False
    extra: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class CodeMappingResponse(BaseModel):
    """Schema for code mappings"""
    id: int
    from_system: str
    from_code: str
    to_system: str
    to_code: str
    map_type: str
    confidence: Optional[float] = None
    source_name: Optional[str] = None
    source_version: Optional[str] = None

    class Config:
        from_attributes = True


class ICD10DetailResponse(BaseModel):
    """Detailed ICD-10 response with facets and mappings"""
    code_info: ICD10EnhancedResponse
    facets: Optional[ICD10AIFacetResponse] = None
    mappings: List[CodeMappingResponse] = []
    similarity: Optional[float] = None  # For semantic search results

    class Config:
        from_attributes = True


class CPTResponse(BaseModel):
    """Schema for CPT code response"""
    id: UUID
    code: str
    description: str
    category: str | None

    class Config:
        from_attributes = True


class CodeSuggestionRequest(BaseModel):
    """Schema for code suggestion request"""
    text: str
    max_results: int = 5


class CodeSuggestion(BaseModel):
    """Individual code suggestion"""
    code: str
    description: str
    score: float  # Relevance score 0-1
    type: str  # "icd10" or "cpt"


class CodeSuggestionResponse(BaseModel):
    """Schema for code suggestion response"""
    suggestions: list[CodeSuggestion]
    query: str


# New schemas for semantic search

class SemanticSearchRequest(BaseModel):
    """Schema for semantic search request"""
    text: str = Field(..., description="Query text for semantic search", min_length=1)
    code_system: Optional[str] = Field(None, description="Filter by code system (ICD10, ICD10-CM, ICD10-PCS)")
    limit: int = Field(10, description="Maximum number of results", ge=1, le=100)
    include_facets: bool = Field(False, description="Include AI facets in results")
    include_mappings: bool = Field(False, description="Include cross-code mappings")
    min_similarity: float = Field(0.0, description="Minimum similarity threshold (0-1)", ge=0.0, le=1.0)


class SemanticSearchResponse(BaseModel):
    """Schema for semantic search response"""
    query: str
    results: List[ICD10DetailResponse]
    total_results: int


class FacetedSearchRequest(BaseModel):
    """Schema for faceted search request"""
    body_system: Optional[str] = None
    concept_type: Optional[str] = None
    chronicity: Optional[str] = None
    severity: Optional[str] = None
    acuity: Optional[str] = None
    risk_flag: Optional[bool] = None
    limit: int = Field(50, ge=1, le=100)


class CodeMappingRequest(BaseModel):
    """Schema for requesting code mappings"""
    from_system: str
    to_system: str
    codes: List[str] = Field(..., max_items=100)


class HybridSearchRequest(BaseModel):
    """Schema for hybrid (keyword + semantic) search"""
    query: str = Field(..., min_length=1)
    code_system: Optional[str] = None
    use_semantic: bool = Field(True, description="Enable semantic search")
    use_keyword: bool = Field(True, description="Enable keyword search")
    semantic_weight: float = Field(0.7, description="Weight for semantic results (0-1)", ge=0.0, le=1.0)
    limit: int = Field(10, ge=1, le=100)
