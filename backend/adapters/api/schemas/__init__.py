"""Pydantic schemas for request/response validation"""

from adapters.api.schemas.user import UserCreate, UserLogin, UserResponse, Token
from adapters.api.schemas.api_key import APIKeyCreate, APIKeyResponse, APIKeyWithSecret
from adapters.api.schemas.code import ICD10Response, CPTResponse, CodeSuggestionRequest, CodeSuggestionResponse
from adapters.api.schemas.usage import UsageLogResponse, UsageStatsResponse
from adapters.api.schemas.plan import PlanResponse

# Clinical Entity Extraction schemas
from adapters.api.schemas.clinical_entities import (
    ClinicalNoteInput,
    VitalSignsResponse,
    LabResultResponse,
    DiagnosisResponse,
    MedicationResponse,
    ScreeningResponse,
    ConfidenceMetrics,
    ClinicalEntitiesResponse,
    EntityExtractionRequest,
    EntityExtractionResponse,
)

# HEDIS Evaluation schemas
from adapters.api.schemas.hedis import (
    MeasureStatus,
    HEDISMeasureResponse,
    HEDISEvaluationRequest,
    ExclusionInfo,
    HEDISEvaluationResponse,
    HEDISMeasureInfo,
    HEDISMeasureListResponse,
)

# Documentation Gap schemas
from adapters.api.schemas.documentation_gaps import (
    GapPriority,
    GapCategory,
    DocumentationGapResponse,
    GapAnalysisRequest,
    GapSummary,
    GapAnalysisResponse,
)

# CDI Query schemas
from adapters.api.schemas.cdi_queries import (
    QueryType,
    QueryPriority,
    CDIQueryResponse,
    CDIQueryGenerationRequest,
    QuerySummary,
    CDIQueryGenerationResponse,
)

# Revenue Optimization schemas
from adapters.api.schemas.revenue import (
    EMLevel,
    ClinicalSetting,
    PatientType,
    EMCodeResponse,
    HCCOpportunity,
    DRGOptimizationResponse,
    MissingChargeOpportunity,
    RevenueAnalysisRequest,
    RevenueSummary,
    RevenueAnalysisResponse,
)

__all__ = [
    # User schemas
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    # API Key schemas
    "APIKeyCreate",
    "APIKeyResponse",
    "APIKeyWithSecret",
    # Code schemas
    "ICD10Response",
    "CPTResponse",
    "CodeSuggestionRequest",
    "CodeSuggestionResponse",
    # Usage schemas
    "UsageLogResponse",
    "UsageStatsResponse",
    # Plan schemas
    "PlanResponse",
    # Clinical Entity schemas
    "ClinicalNoteInput",
    "VitalSignsResponse",
    "LabResultResponse",
    "DiagnosisResponse",
    "MedicationResponse",
    "ScreeningResponse",
    "ConfidenceMetrics",
    "ClinicalEntitiesResponse",
    "EntityExtractionRequest",
    "EntityExtractionResponse",
    # HEDIS schemas
    "MeasureStatus",
    "HEDISMeasureResponse",
    "HEDISEvaluationRequest",
    "ExclusionInfo",
    "HEDISEvaluationResponse",
    "HEDISMeasureInfo",
    "HEDISMeasureListResponse",
    # Documentation Gap schemas
    "GapPriority",
    "GapCategory",
    "DocumentationGapResponse",
    "GapAnalysisRequest",
    "GapSummary",
    "GapAnalysisResponse",
    # CDI Query schemas
    "QueryType",
    "QueryPriority",
    "CDIQueryResponse",
    "CDIQueryGenerationRequest",
    "QuerySummary",
    "CDIQueryGenerationResponse",
    # Revenue schemas
    "EMLevel",
    "ClinicalSetting",
    "PatientType",
    "EMCodeResponse",
    "HCCOpportunity",
    "DRGOptimizationResponse",
    "MissingChargeOpportunity",
    "RevenueAnalysisRequest",
    "RevenueSummary",
    "RevenueAnalysisResponse",
]
