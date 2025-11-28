"""
Entity Extraction Domain Module

Extracts clinical entities (diagnoses, vitals, labs, screenings) from clinical notes.
Supports:
- Diagnoses and conditions
- Vital signs (BP, HR, BMI, etc.)
- Lab results (HbA1c, LDL, etc.)
- Medications
- Screenings (mammogram, colonoscopy, etc.)
- Patient demographics
"""

from domain.entity_extraction.extractor import (
    ClinicalEntityExtractor,
    extract_entities,
    extract_vitals,
    extract_labs,
    extract_diagnoses,
)

__all__ = [
    "ClinicalEntityExtractor",
    "extract_entities",
    "extract_vitals",
    "extract_labs",
    "extract_diagnoses",
]
