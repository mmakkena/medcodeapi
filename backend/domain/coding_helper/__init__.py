"""
Coding Helper Domain Module

ICD-10 and CPT code suggestion, validation, and comparison:
- Rule-based code suggestions from clinical text
- Code validation (format and lookup)
- Entity to code mapping
- Related code discovery
"""

from domain.coding_helper.helper import (
    ClinicalCodingHelper,
    CodeSuggestion,
    CodeValidationResult,
    suggest_codes,
    validate_code,
)

__all__ = [
    "ClinicalCodingHelper",
    "CodeSuggestion",
    "CodeValidationResult",
    "suggest_codes",
    "validate_code",
]
