"""Pydantic schemas for Fee Schedule API"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field


class LocalityInfo(BaseModel):
    """Locality information with GPCI values."""
    zip_code: Optional[str] = None
    locality_code: str
    locality_name: str
    mac_code: Optional[str] = None
    state: Optional[str] = None
    work_gpci: float
    pe_gpci: float
    mp_gpci: float
    year: int


class RateInfo(BaseModel):
    """MPFS rate information."""
    hcpcs_code: str
    modifier: Optional[str] = None
    description: Optional[str] = None
    work_rvu: Optional[float] = None
    non_facility_pe_rvu: Optional[float] = None
    facility_pe_rvu: Optional[float] = None
    mp_rvu: Optional[float] = None
    non_facility_total: Optional[float] = None
    facility_total: Optional[float] = None
    global_days: Optional[str] = None
    status_code: Optional[str] = None
    year: int


class PriceResponse(BaseModel):
    """Response for price lookup."""
    hcpcs_code: str
    modifier: Optional[str] = None
    description: Optional[str] = None
    setting: str = "non_facility"
    price: float = Field(..., description="Calculated Medicare price for the location")
    national_price: float = Field(..., description="National average price (GPCI=1.0)")
    work_rvu: Optional[float] = None
    pe_rvu: Optional[float] = None
    mp_rvu: Optional[float] = None
    total_rvu: Optional[float] = None
    conversion_factor: float
    locality: LocalityInfo
    global_days: Optional[str] = None
    status_code: Optional[str] = None
    year: int


class SearchResult(BaseModel):
    """Search result item."""
    hcpcs_code: str
    modifier: Optional[str] = None
    description: Optional[str] = None
    work_rvu: Optional[float] = None
    non_facility_pe_rvu: Optional[float] = None
    facility_pe_rvu: Optional[float] = None
    mp_rvu: Optional[float] = None
    non_facility_total: Optional[float] = None
    facility_total: Optional[float] = None
    global_days: Optional[str] = None
    year: int


class SearchResponse(BaseModel):
    """Response for code search."""
    query: str
    year: int
    count: int
    results: List[SearchResult]


class YearsResponse(BaseModel):
    """Response for available years."""
    years: List[int]


class LocalitiesResponse(BaseModel):
    """Response for localities list."""
    year: int
    state: Optional[str] = None
    count: int
    localities: List[LocalityInfo]


class ConversionFactorResponse(BaseModel):
    """Response for conversion factor lookup."""
    year: int
    conversion_factor: float
    anesthesia_conversion_factor: Optional[float] = None


# Contract Analyzer schemas

class ContractCodeItem(BaseModel):
    """Single code item for contract analysis."""
    code: str = Field(..., description="CPT or HCPCS code")
    rate: float = Field(..., description="Contracted rate")
    volume: Optional[int] = Field(None, description="Annual volume for revenue impact")
    description: Optional[str] = None


class ContractAnalysisRequest(BaseModel):
    """Request for contract analysis."""
    codes: List[ContractCodeItem] = Field(..., description="List of codes with contracted rates")
    zip_code: str = Field(..., description="ZIP code for location-based pricing")
    year: int = Field(2025, description="CMS year to compare against")
    setting: str = Field("non_facility", description="'facility' or 'non_facility'")


class AnalysisLineItem(BaseModel):
    """Single line item in analysis results."""
    code: str
    description: Optional[str] = None
    contracted_rate: float
    medicare_rate: Optional[float] = None
    variance: Optional[float] = None
    variance_pct: Optional[float] = None
    is_below_medicare: Optional[bool] = None
    volume: Optional[int] = None
    revenue_impact: Optional[float] = None
    error: Optional[str] = None


class RedFlagItem(BaseModel):
    """Code significantly below Medicare rate."""
    code: str
    description: Optional[str] = None
    contracted_rate: float
    medicare_rate: float
    variance: float
    variance_pct: float


class ContractAnalysisResponse(BaseModel):
    """Response for contract analysis."""
    total_codes: int
    codes_matched: int
    codes_unmatched: int
    codes_below_medicare: int
    codes_above_medicare: int
    codes_equal: int
    total_variance: float = Field(..., description="Sum of all variances (contracted - Medicare)")
    total_revenue_impact: float = Field(..., description="Total revenue impact based on volumes")
    line_items: List[AnalysisLineItem]
    red_flags: List[RedFlagItem] = Field(..., description="Codes more than 10% below Medicare")


# Saved Lists schemas

class SavedCodeListItem(BaseModel):
    """Item in a saved code list."""
    code: str
    notes: Optional[str] = None


class SavedCodeListCreate(BaseModel):
    """Create a new saved code list."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    codes: List[SavedCodeListItem] = Field(default_factory=list)


class SavedCodeListUpdate(BaseModel):
    """Update a saved code list."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    codes: Optional[List[SavedCodeListItem]] = None


class SavedCodeListResponse(BaseModel):
    """Response for saved code list."""
    id: str
    name: str
    description: Optional[str] = None
    codes: List[SavedCodeListItem]
    created_at: str
    updated_at: str


class SavedCodeListsResponse(BaseModel):
    """Response for list of saved code lists."""
    count: int
    lists: List[SavedCodeListResponse]
