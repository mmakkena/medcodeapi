"""
HEDIS Evaluation Schemas

Pydantic models for HEDIS quality measure evaluation API endpoints.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class MeasureStatus(str, Enum):
    """Status of a HEDIS measure."""
    MET = "met"
    NOT_MET = "not_met"
    EXCLUDED = "excluded"
    NOT_APPLICABLE = "not_applicable"
    PENDING = "pending"


class HEDISMeasureResponse(BaseModel):
    """Single HEDIS measure result."""
    measure_id: str = Field(..., description="HEDIS measure identifier (e.g., CBP, CDC)")
    measure_name: str
    status: MeasureStatus
    value: Optional[str] = None
    target: Optional[str] = None
    is_compliant: bool
    gaps: List[str] = []
    recommendations: List[str] = []
    evidence_text: Optional[str] = None
    confidence: float = Field(ge=0, le=1)


class HEDISEvaluationRequest(BaseModel):
    """Request for HEDIS evaluation."""
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
    measures: Optional[List[str]] = Field(
        None,
        description="Specific measures to evaluate (e.g., ['CBP', 'CDC']). If null, evaluates all applicable."
    )
    include_exclusions: bool = Field(
        True,
        description="Check exclusion criteria"
    )


class ExclusionInfo(BaseModel):
    """Exclusion information for a measure."""
    measure_id: str
    is_excluded: bool
    exclusion_reason: Optional[str] = None
    exclusion_criteria: Optional[str] = None


class HEDISEvaluationResponse(BaseModel):
    """Response for HEDIS evaluation."""
    success: bool
    measures: List[HEDISMeasureResponse]
    exclusions: List[ExclusionInfo] = []
    summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Summary counts: met, not_met, excluded, etc."
    )
    overall_compliance_rate: float = Field(ge=0, le=1)
    total_gaps_identified: int = 0
    processing_time_ms: Optional[float] = None


class HEDISMeasureInfo(BaseModel):
    """Information about a HEDIS measure."""
    measure_id: str
    measure_name: str
    description: str
    target_population: str
    numerator_criteria: str
    denominator_criteria: str
    exclusion_criteria: List[str]
    performance_target: Optional[float] = None


class HEDISMeasureListResponse(BaseModel):
    """List of available HEDIS measures."""
    measures: List[HEDISMeasureInfo]
    total_count: int
