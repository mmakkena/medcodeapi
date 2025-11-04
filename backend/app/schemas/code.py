"""Medical code schemas"""

from pydantic import BaseModel
from uuid import UUID


class ICD10Response(BaseModel):
    """Schema for ICD-10 code response"""
    id: UUID
    code: str
    description: str
    category: str | None

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
