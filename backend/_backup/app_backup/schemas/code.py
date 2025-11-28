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


# =============================================================================
# Procedure Code (CPT/HCPCS) Schemas
# =============================================================================

class ProcedureCodeResponse(BaseModel):
    """Basic schema for procedure code response (CPT/HCPCS)"""
    id: UUID
    code: str
    code_system: str
    description: str  # Auto-selected based on license_status
    category: Optional[str] = None
    license_status: str
    version_year: int

    class Config:
        from_attributes = True


class ProcedureCodeEnhancedResponse(BaseModel):
    """Enhanced schema for procedure code with all fields"""
    id: UUID
    code: str
    code_system: str  # CPT or HCPCS

    # Dual description strategy
    description: Optional[str] = None  # Auto-selected based on license_status (for UI display)
    paraphrased_desc: Optional[str] = None
    short_desc: Optional[str] = None  # AMA licensed for CPT
    long_desc: Optional[str] = None   # AMA licensed for CPT

    # Classification
    category: Optional[str] = None
    procedure_type: Optional[str] = None

    # Versioning and lifecycle
    version_year: int
    is_active: bool = True
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None

    # Licensing
    license_status: str  # 'free' or 'AMA_licensed'

    # Billing metadata
    relative_value_units: Optional[str] = None
    global_period: Optional[str] = None
    modifier_51_exempt: bool = False

    # Timestamps
    created_at: datetime
    last_updated: datetime

    class Config:
        from_attributes = True


class ProcedureCodeFacetResponse(BaseModel):
    """Schema for procedure code facets"""
    code: str
    code_system: str

    # Anatomical classification
    body_region: Optional[str] = None
    body_system: Optional[str] = None

    # Procedure classification
    procedure_category: Optional[str] = None
    procedure_type: Optional[str] = None

    # Complexity
    complexity_level: Optional[str] = None
    typical_duration_mins: Optional[int] = None
    relative_complexity_score: Optional[int] = None

    # Anesthesia
    anesthesia_type: Optional[str] = None
    anesthesia_base_units: Optional[int] = None

    # Service context
    service_location: Optional[str] = None
    provider_type: Optional[str] = None

    # Clinical attributes
    is_bilateral: bool = False
    requires_modifier: bool = False
    age_specific: bool = False
    gender_specific: Optional[str] = None

    # Special flags
    is_add_on_code: bool = False
    is_unlisted_code: bool = False
    requires_special_report: bool = False

    # E/M specific
    em_level: Optional[str] = None
    em_patient_type: Optional[str] = None

    # Surgical specific
    surgical_approach: Optional[str] = None
    is_major_surgery: bool = False

    # Imaging specific
    imaging_modality: Optional[str] = None
    uses_contrast: bool = False

    # Additional metadata
    extra: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ProcedureCodeDetailResponse(BaseModel):
    """Detailed procedure code response with facets and mappings"""
    code_info: ProcedureCodeEnhancedResponse
    facets: Optional[ProcedureCodeFacetResponse] = None
    mappings: List[CodeMappingResponse] = []
    similarity: Optional[float] = None  # For semantic search results

    class Config:
        from_attributes = True


class ProcedureSemanticSearchResponse(BaseModel):
    """Schema for procedure code semantic search response"""
    query: str
    results: List[ProcedureCodeDetailResponse]
    total_results: int


class ProcedureFacetedSearchRequest(BaseModel):
    """Schema for procedure faceted search request"""
    body_region: Optional[str] = Field(None, description="Filter by body region")
    body_system: Optional[str] = Field(None, description="Filter by body system")
    procedure_category: Optional[str] = Field(None, description="Filter by procedure category")
    complexity_level: Optional[str] = Field(None, description="Filter by complexity level")
    service_location: Optional[str] = Field(None, description="Filter by service location")
    em_level: Optional[str] = Field(None, description="Filter by E/M level")
    em_patient_type: Optional[str] = Field(None, description="Filter by E/M patient type")
    is_major_surgery: Optional[bool] = Field(None, description="Filter by major surgery flag")
    imaging_modality: Optional[str] = Field(None, description="Filter by imaging modality")
    code_system: Optional[str] = Field(None, description="Filter by CPT or HCPCS")
    limit: int = Field(50, ge=1, le=100, description="Maximum number of results")


class ProcedureHybridSearchRequest(BaseModel):
    """Schema for procedure hybrid search request"""
    query: str = Field(..., min_length=1, description="Search query")
    code_system: Optional[str] = Field(None, description="Filter by CPT or HCPCS")
    version_year: Optional[int] = Field(None, description="Filter by version year")
    semantic_weight: float = Field(0.7, description="Weight for semantic results (0-1)", ge=0.0, le=1.0)
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")


class ProcedureCodeSuggestionRequest(BaseModel):
    """Schema for procedure code suggestion from clinical text"""
    clinical_text: str = Field(..., min_length=10, description="Clinical documentation text")
    code_system: Optional[str] = Field(None, description="Filter by CPT or HCPCS")
    limit: int = Field(5, ge=1, le=20, description="Maximum number of suggestions")
    min_similarity: float = Field(0.6, description="Minimum similarity threshold", ge=0.0, le=1.0)
