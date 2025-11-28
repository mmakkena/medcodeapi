"""
Documentation Gap Analysis Schemas

Pydantic models for clinical documentation gap detection API endpoints.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class GapPriority(str, Enum):
    """Priority level for documentation gaps."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GapCategory(str, Enum):
    """Category of documentation gap."""
    DIAGNOSIS = "diagnosis"
    PROCEDURE = "procedure"
    VITAL_SIGNS = "vital_signs"
    LAB_RESULT = "lab_result"
    MEDICATION = "medication"
    SCREENING = "screening"
    ASSESSMENT = "assessment"
    PLAN = "plan"
    SPECIFICITY = "specificity"
    ACUITY = "acuity"
    LINKAGE = "linkage"


class DocumentationGapResponse(BaseModel):
    """Single documentation gap."""
    gap_id: str
    category: GapCategory
    priority: GapPriority
    title: str
    description: str
    clinical_indicator: Optional[str] = None
    suggested_query: Optional[str] = None
    revenue_impact: Optional[str] = None
    hedis_impact: Optional[List[str]] = None
    evidence_text: Optional[str] = None
    confidence: float = Field(ge=0, le=1)


class GapAnalysisRequest(BaseModel):
    """Request for documentation gap analysis."""
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
    encounter_type: Optional[str] = Field(
        None,
        description="Type of encounter (inpatient, outpatient, emergency)"
    )
    include_hedis_gaps: bool = True
    include_revenue_gaps: bool = True
    include_quality_gaps: bool = True
    min_priority: Optional[GapPriority] = None


class GapSummary(BaseModel):
    """Summary of gaps by category and priority."""
    by_priority: Dict[str, int] = Field(default_factory=dict)
    by_category: Dict[str, int] = Field(default_factory=dict)
    total_gaps: int = 0
    critical_count: int = 0
    high_count: int = 0


class GapAnalysisResponse(BaseModel):
    """Response for documentation gap analysis."""
    success: bool
    gaps: List[DocumentationGapResponse]
    summary: GapSummary
    top_priorities: List[str] = Field(
        default_factory=list,
        description="Top 3 priority actions"
    )
    estimated_revenue_impact: Optional[float] = None
    hedis_gaps_count: int = 0
    processing_time_ms: Optional[float] = None


class GapResolutionRequest(BaseModel):
    """Request to mark a gap as resolved."""
    gap_id: str
    resolution_note: Optional[str] = None
    resolved_by: Optional[str] = None


class GapResolutionResponse(BaseModel):
    """Response for gap resolution."""
    success: bool
    gap_id: str
    message: str
