"""
CDI Query Generation Schemas

Pydantic models for Clinical Documentation Integrity query generation API endpoints.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class QueryType(str, Enum):
    """Type of CDI query."""
    CLARIFICATION = "clarification"
    SPECIFICITY = "specificity"
    ACUITY = "acuity"
    LINKAGE = "linkage"
    PRESENT_ON_ADMISSION = "present_on_admission"
    CLINICAL_VALIDATION = "clinical_validation"


class QueryPriority(str, Enum):
    """Priority level for CDI query."""
    URGENT = "urgent"
    HIGH = "high"
    ROUTINE = "routine"


class CDIQueryResponse(BaseModel):
    """Single CDI query."""
    query_id: str
    query_type: QueryType
    priority: QueryPriority
    query_text: str = Field(
        ...,
        description="Non-leading, ACDIS-compliant query text"
    )
    clinical_indicator: str
    supporting_evidence: List[str] = []
    potential_diagnoses: List[str] = []
    documentation_needed: str
    revenue_impact: Optional[str] = None
    drg_impact: Optional[str] = None
    confidence: float = Field(ge=0, le=1)


class CDIQueryGenerationRequest(BaseModel):
    """Request for CDI query generation."""
    clinical_note: str = Field(
        ...,
        min_length=10,
        description="Clinical note text"
    )
    patient_age: Optional[int] = Field(
        None,
        ge=0,
        le=150,
        description="Patient age in years"
    )
    patient_gender: Optional[str] = Field(
        None,
        description="Patient gender (M/F)"
    )
    encounter_type: str = Field(
        "inpatient",
        description="Type of encounter (inpatient, outpatient, emergency)"
    )
    drg_info: Optional[str] = Field(
        None,
        description="Current DRG information if available"
    )
    focus_areas: Optional[List[QueryType]] = Field(
        None,
        description="Specific query types to focus on"
    )
    max_queries: int = Field(
        10,
        ge=1,
        le=20,
        description="Maximum number of queries to generate"
    )


class QuerySummary(BaseModel):
    """Summary of generated queries."""
    total_queries: int = 0
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_priority: Dict[str, int] = Field(default_factory=dict)
    urgent_count: int = 0
    estimated_drg_impact: Optional[str] = None


class CDIQueryGenerationResponse(BaseModel):
    """Response for CDI query generation."""
    success: bool
    queries: List[CDIQueryResponse]
    summary: QuerySummary
    processing_time_ms: Optional[float] = None


class CDIQueryTemplate(BaseModel):
    """Template for CDI query."""
    template_id: str
    query_type: QueryType
    template_text: str
    applicable_conditions: List[str]
    example_usage: str


class CDIQueryTemplateListResponse(BaseModel):
    """List of available CDI query templates."""
    templates: List[CDIQueryTemplate]
    total_count: int


class QueryFeedbackRequest(BaseModel):
    """Feedback on a CDI query."""
    query_id: str
    was_useful: bool
    physician_response: Optional[str] = None
    outcome: Optional[str] = Field(
        None,
        description="Result of the query (documented, not_documented, inconclusive)"
    )
    feedback_notes: Optional[str] = None


class QueryFeedbackResponse(BaseModel):
    """Response for query feedback submission."""
    success: bool
    message: str
