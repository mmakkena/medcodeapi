"""
Clinical Entity Extraction Schemas

Pydantic models for clinical entity extraction API endpoints.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ClinicalNoteInput(BaseModel):
    """Input model for clinical note analysis."""
    clinical_note: str = Field(
        ...,
        min_length=10,
        description="Clinical note text to analyze"
    )
    patient_age: Optional[int] = Field(
        None,
        ge=0,
        le=150,
        description="Patient age in years"
    )
    patient_gender: Optional[str] = Field(
        None,
        pattern="^(M|F|Male|Female|Other|Unknown)$",
        description="Patient gender"
    )


class VitalSignsResponse(BaseModel):
    """Vital signs extracted from clinical note."""
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    temperature: Optional[float] = None
    respiratory_rate: Optional[int] = None
    spo2: Optional[float] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    bmi: Optional[float] = None


class LabResultResponse(BaseModel):
    """Single lab result."""
    name: str
    value: float
    unit: str
    reference_range: Optional[str] = None
    is_abnormal: bool = False


class DiagnosisResponse(BaseModel):
    """Diagnosis extracted from clinical note."""
    name: str
    icd10_code: Optional[str] = None
    status: str = "active"  # active, resolved, chronic
    severity: Optional[str] = None


class MedicationResponse(BaseModel):
    """Medication extracted from clinical note."""
    name: str
    dose: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None


class ScreeningResponse(BaseModel):
    """Screening result extracted from clinical note."""
    name: str
    date: Optional[str] = None
    result: Optional[str] = None
    is_completed: bool = False


class ConfidenceMetrics(BaseModel):
    """Confidence metrics for extraction."""
    overall_confidence: float = Field(ge=0, le=1)
    extraction_confidence: float = Field(ge=0, le=1)
    parsing_confidence: float = Field(ge=0, le=1)
    completeness_score: float = Field(ge=0, le=1)


class ClinicalEntitiesResponse(BaseModel):
    """Response model for clinical entity extraction."""
    vitals: VitalSignsResponse
    labs: List[LabResultResponse]
    diagnoses: List[DiagnosisResponse]
    medications: List[MedicationResponse]
    screenings: List[ScreeningResponse]
    confidence: ConfidenceMetrics
    processing_time_ms: Optional[float] = None


class EntityExtractionRequest(BaseModel):
    """Request for entity extraction."""
    clinical_note: str = Field(
        ...,
        min_length=10,
        description="Clinical note text"
    )
    extract_vitals: bool = True
    extract_labs: bool = True
    extract_diagnoses: bool = True
    extract_medications: bool = True
    extract_screenings: bool = True


class EntityExtractionResponse(BaseModel):
    """Response for entity extraction."""
    success: bool
    entities: ClinicalEntitiesResponse
    warnings: List[str] = []
