"""
Revenue Optimization Schemas

Pydantic models for revenue optimization API endpoints.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class EMLevel(str, Enum):
    """E/M code levels."""
    LEVEL_1 = "99211"  # Minimal
    LEVEL_2 = "99212"  # Low
    LEVEL_3 = "99213"  # Moderate
    LEVEL_4 = "99214"  # Moderate-High
    LEVEL_5 = "99215"  # High
    # New patient codes
    NEW_LEVEL_1 = "99201"
    NEW_LEVEL_2 = "99202"
    NEW_LEVEL_3 = "99203"
    NEW_LEVEL_4 = "99204"
    NEW_LEVEL_5 = "99205"
    # Inpatient codes
    INITIAL_LOW = "99221"
    INITIAL_MOD = "99222"
    INITIAL_HIGH = "99223"
    SUBSEQUENT_LOW = "99231"
    SUBSEQUENT_MOD = "99232"
    SUBSEQUENT_HIGH = "99233"


class ClinicalSetting(str, Enum):
    """Clinical setting for E/M coding."""
    OUTPATIENT = "outpatient"
    INPATIENT = "inpatient"
    EMERGENCY = "emergency"
    OBSERVATION = "observation"
    TELEHEALTH = "telehealth"


class PatientType(str, Enum):
    """Patient type for E/M coding."""
    NEW = "new"
    ESTABLISHED = "established"


class EMCodeResponse(BaseModel):
    """E/M code recommendation."""
    recommended_code: str
    code_description: str
    current_code: Optional[str] = None
    mdm_level: str = Field(..., description="Medical Decision Making level")
    time_based_option: Optional[str] = None
    supporting_elements: List[str] = []
    documentation_gaps: List[str] = []
    estimated_reimbursement: Optional[float] = None
    confidence: float = Field(ge=0, le=1)


class HCCOpportunity(BaseModel):
    """HCC risk adjustment opportunity."""
    hcc_code: str
    hcc_description: str
    associated_diagnosis: str
    icd10_code: str
    risk_adjustment_factor: float
    annual_value: Optional[float] = None
    evidence_in_note: str
    documentation_needed: str
    confidence: float = Field(ge=0, le=1)


class DRGOptimizationResponse(BaseModel):
    """DRG optimization opportunity."""
    current_drg: Optional[str] = None
    current_drg_weight: Optional[float] = None
    potential_drg: str
    potential_drg_weight: float
    weight_difference: float
    estimated_revenue_increase: Optional[float] = None
    required_documentation: List[str]
    clinical_indicators: List[str]
    cc_mcc_opportunities: List[str] = []
    confidence: float = Field(ge=0, le=1)


class MissingChargeOpportunity(BaseModel):
    """Missing charge or procedure opportunity."""
    item_type: str  # procedure, test, supply
    item_name: str
    suggested_code: Optional[str] = None
    code_system: str = "CPT"
    evidence_in_note: str
    estimated_value: Optional[float] = None
    confidence: float = Field(ge=0, le=1)


class RevenueAnalysisRequest(BaseModel):
    """Request for revenue optimization analysis."""
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
    clinical_setting: ClinicalSetting = ClinicalSetting.OUTPATIENT
    patient_type: PatientType = PatientType.ESTABLISHED
    current_em_code: Optional[str] = None
    current_drg: Optional[str] = None
    payer_type: Optional[str] = Field(
        None,
        description="Payer type (medicare, medicaid, commercial)"
    )
    include_em_analysis: bool = True
    include_hcc_analysis: bool = True
    include_drg_analysis: bool = True
    include_missing_charges: bool = True


class RevenueSummary(BaseModel):
    """Summary of revenue optimization findings."""
    total_opportunities: int = 0
    estimated_total_impact: Optional[float] = None
    em_upgrade_potential: bool = False
    hcc_opportunities_count: int = 0
    drg_optimization_available: bool = False
    missing_charges_count: int = 0


class RevenueAnalysisResponse(BaseModel):
    """Response for revenue optimization analysis."""
    success: bool
    em_recommendation: Optional[EMCodeResponse] = None
    hcc_opportunities: List[HCCOpportunity] = []
    drg_optimization: Optional[DRGOptimizationResponse] = None
    missing_charges: List[MissingChargeOpportunity] = []
    summary: RevenueSummary
    processing_time_ms: Optional[float] = None


class EMCodingGuidelinesResponse(BaseModel):
    """E/M coding guidelines information."""
    setting: ClinicalSetting
    patient_type: PatientType
    available_codes: List[Dict[str, str]]
    mdm_criteria: Dict[str, List[str]]
    time_thresholds: Dict[str, int]
    documentation_requirements: List[str]
