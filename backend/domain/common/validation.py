"""
Clinical Data Validation Utilities

Provides validation functions for clinical values, codes, and data quality.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ============================================================================
# Value Parsing Functions
# ============================================================================

def parse_blood_pressure(bp_string: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Parse BP string into numeric systolic/diastolic values.

    Args:
        bp_string: BP value (e.g., "128/82", "145/95 mmHg", "BP: 118/76")

    Returns:
        Tuple of (systolic, diastolic) or (None, None) if parsing fails

    Examples:
        >>> parse_blood_pressure("128/82")
        (128, 82)
        >>> parse_blood_pressure("BP: 145/95 mmHg")
        (145, 95)
    """
    if not bp_string:
        return None, None

    # Remove common prefixes/suffixes
    bp_clean = re.sub(r'(bp|blood pressure|mmhg|mm hg)', '', bp_string, flags=re.IGNORECASE)
    bp_clean = bp_clean.strip(' :')

    # Extract systolic/diastolic
    match = re.search(r'(\d{2,3})/(\d{2,3})', bp_clean)
    if match:
        systolic = int(match.group(1))
        diastolic = int(match.group(2))

        # Validation: reasonable ranges
        if 70 <= systolic <= 250 and 40 <= diastolic <= 150:
            return systolic, diastolic

    return None, None


def parse_hba1c(value_string: str) -> Optional[float]:
    """
    Parse HbA1c value.

    Args:
        value_string: HbA1c value (e.g., "7.2%", "HbA1c: 8.5", "6.8 %")

    Returns:
        Float value or None if parsing fails

    Examples:
        >>> parse_hba1c("7.2%")
        7.2
        >>> parse_hba1c("HbA1c: 8.5")
        8.5
    """
    if not value_string:
        return None

    clean = re.sub(r'(hba1c|a1c|%)', '', str(value_string), flags=re.IGNORECASE)
    clean = clean.strip(' :')

    match = re.search(r'(\d{1,2}\.?\d*)', clean)
    if match:
        value = float(match.group(1))
        # Validation: reasonable HbA1c range
        if 3.0 <= value <= 20.0:
            return value

    return None


def parse_bmi(value_string: str) -> Optional[float]:
    """
    Parse BMI value.

    Args:
        value_string: BMI value (e.g., "31.2", "BMI: 28.5")

    Returns:
        Float value or None if parsing fails

    Examples:
        >>> parse_bmi("31.2")
        31.2
        >>> parse_bmi("BMI: 28.5")
        28.5
    """
    if not value_string:
        return None

    clean = re.sub(r'bmi', '', str(value_string), flags=re.IGNORECASE)
    clean = clean.strip(' :')

    match = re.search(r'(\d{1,2}\.?\d*)', clean)
    if match:
        value = float(match.group(1))
        # Validation: reasonable BMI range
        if 10.0 <= value <= 80.0:
            return value

    return None


def parse_ldl(value_string: str) -> Optional[int]:
    """
    Parse LDL cholesterol value (mg/dL).

    Args:
        value_string: LDL value (e.g., "125", "LDL: 145 mg/dL")

    Returns:
        Integer value or None if parsing fails
    """
    if not value_string:
        return None

    clean = re.sub(r'(ldl|mg/dl)', '', str(value_string), flags=re.IGNORECASE)
    clean = clean.strip(' :')

    match = re.search(r'(\d{1,3})', clean)
    if match:
        value = int(match.group(1))
        # Validation: reasonable LDL range
        if 20 <= value <= 400:
            return value

    return None


def parse_heart_rate(value_string: str) -> Optional[int]:
    """Parse heart rate value."""
    if not value_string:
        return None

    clean = re.sub(r'(hr|heart rate|bpm|pulse)', '', str(value_string), flags=re.IGNORECASE)
    clean = clean.strip(' :')

    match = re.search(r'(\d{2,3})', clean)
    if match:
        value = int(match.group(1))
        if 30 <= value <= 250:
            return value

    return None


def parse_temperature(value_string: str) -> Optional[float]:
    """Parse temperature value (assumes Fahrenheit)."""
    if not value_string:
        return None

    clean = re.sub(r'(temp|temperature|[°]?f|[°]?c)', '', str(value_string), flags=re.IGNORECASE)
    clean = clean.strip(' :')

    match = re.search(r'(\d{2,3}\.?\d*)', clean)
    if match:
        value = float(match.group(1))
        # Assume F if > 50, convert C to F if < 50
        if 90 <= value <= 110:  # Valid F range
            return value
        elif 30 <= value < 50:  # Likely Celsius
            return value * 9/5 + 32

    return None


def parse_spo2(value_string: str) -> Optional[float]:
    """Parse SpO2/oxygen saturation value."""
    if not value_string:
        return None

    clean = re.sub(r'(spo2|o2 sat|oxygen|sat|%)', '', str(value_string), flags=re.IGNORECASE)
    clean = clean.strip(' :')

    match = re.search(r'(\d{2,3})', clean)
    if match:
        value = float(match.group(1))
        if 50 <= value <= 100:
            return value

    return None


def parse_creatinine(value_string: str) -> Optional[float]:
    """Parse creatinine value (mg/dL)."""
    if not value_string:
        return None

    clean = re.sub(r'(cr|creatinine|mg/dl)', '', str(value_string), flags=re.IGNORECASE)
    clean = clean.strip(' :')

    match = re.search(r'(\d{1,2}\.?\d*)', clean)
    if match:
        value = float(match.group(1))
        if 0.1 <= value <= 20.0:
            return value

    return None


def parse_glucose(value_string: str) -> Optional[int]:
    """Parse glucose value (mg/dL)."""
    if not value_string:
        return None

    clean = re.sub(r'(glucose|bg|mg/dl)', '', str(value_string), flags=re.IGNORECASE)
    clean = clean.strip(' :')

    match = re.search(r'(\d{2,3})', clean)
    if match:
        value = int(match.group(1))
        if 20 <= value <= 1000:
            return value

    return None


# ============================================================================
# ICD-10 Code Validation
# ============================================================================

def is_valid_icd10_code(code: str) -> bool:
    """
    Validate ICD-10 code format.

    Args:
        code: ICD-10 code to validate

    Returns:
        True if valid format
    """
    if not code:
        return False

    # ICD-10 format: Letter + 2 digits + optional decimal + up to 4 more characters
    pattern = r'^[A-Z]\d{2}(\.\d{1,4})?$'
    return bool(re.match(pattern, code.upper()))


def is_valid_cpt_code(code: str) -> bool:
    """
    Validate CPT code format.

    Args:
        code: CPT code to validate

    Returns:
        True if valid format (5 digits, optionally with modifier)
    """
    if not code:
        return False

    # CPT format: 5 digits, optionally followed by modifier (-XX)
    pattern = r'^\d{5}(-[A-Z0-9]{2})?$'
    return bool(re.match(pattern, code.upper()))


def is_valid_hcpcs_code(code: str) -> bool:
    """
    Validate HCPCS code format.

    Args:
        code: HCPCS code to validate

    Returns:
        True if valid format
    """
    if not code:
        return False

    # HCPCS Level II: Letter + 4 digits
    pattern = r'^[A-V]\d{4}$'
    return bool(re.match(pattern, code.upper()))


# ============================================================================
# Data Quality Validation
# ============================================================================

@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    field_name: str
    value: Any
    error_message: Optional[str] = None
    warning_message: Optional[str] = None


class ClinicalDataValidator:
    """Validates clinical data quality and completeness."""

    # Reasonable ranges for vital signs
    VITAL_RANGES = {
        'systolic': (70, 250),
        'diastolic': (40, 150),
        'heart_rate': (30, 250),
        'respiratory_rate': (4, 60),
        'temperature': (90.0, 110.0),  # Fahrenheit
        'spo2': (50, 100),
        'bmi': (10, 80),
    }

    # Reasonable ranges for lab values
    LAB_RANGES = {
        'hba1c': (3.0, 20.0),
        'ldl': (20, 400),
        'hdl': (10, 150),
        'creatinine': (0.1, 20.0),
        'glucose': (20, 1000),
        'sodium': (100, 180),
        'potassium': (1.5, 9.0),
        'wbc': (0.1, 100.0),
        'hemoglobin': (3.0, 25.0),
        'platelets': (10, 2000),
    }

    def validate_vital_sign(
        self,
        field_name: str,
        value: Any
    ) -> ValidationResult:
        """Validate a single vital sign value."""
        if value is None:
            return ValidationResult(
                is_valid=True,
                field_name=field_name,
                value=value,
                warning_message=f"{field_name} not provided"
            )

        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            return ValidationResult(
                is_valid=False,
                field_name=field_name,
                value=value,
                error_message=f"Cannot convert {field_name} to number: {value}"
            )

        if field_name in self.VITAL_RANGES:
            min_val, max_val = self.VITAL_RANGES[field_name]
            if not (min_val <= numeric_value <= max_val):
                return ValidationResult(
                    is_valid=False,
                    field_name=field_name,
                    value=value,
                    error_message=f"{field_name} value {value} outside range [{min_val}, {max_val}]"
                )

        return ValidationResult(
            is_valid=True,
            field_name=field_name,
            value=value
        )

    def validate_lab_value(
        self,
        field_name: str,
        value: Any
    ) -> ValidationResult:
        """Validate a single lab value."""
        if value is None:
            return ValidationResult(
                is_valid=True,
                field_name=field_name,
                value=value,
                warning_message=f"{field_name} not provided"
            )

        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            return ValidationResult(
                is_valid=False,
                field_name=field_name,
                value=value,
                error_message=f"Cannot convert {field_name} to number: {value}"
            )

        if field_name in self.LAB_RANGES:
            min_val, max_val = self.LAB_RANGES[field_name]
            if not (min_val <= numeric_value <= max_val):
                return ValidationResult(
                    is_valid=False,
                    field_name=field_name,
                    value=value,
                    error_message=f"{field_name} value {value} outside range [{min_val}, {max_val}]"
                )

        return ValidationResult(
            is_valid=True,
            field_name=field_name,
            value=value
        )

    def validate_clinical_note_quality(
        self,
        note_text: str
    ) -> Dict[str, Any]:
        """
        Assess quality and completeness of a clinical note.

        Returns:
            Dict with quality metrics and warnings
        """
        if not note_text:
            return {
                "is_valid": False,
                "quality_score": 0.0,
                "errors": ["Empty clinical note"],
                "warnings": [],
            }

        errors = []
        warnings = []
        quality_score = 1.0

        # Check minimum length
        if len(note_text) < 50:
            warnings.append("Very short clinical note - extraction may be incomplete")
            quality_score *= 0.7
        elif len(note_text) < 200:
            warnings.append("Short clinical note - may lack comprehensive data")
            quality_score *= 0.9

        # Check for structured sections
        section_keywords = [
            'history', 'hpi', 'ros', 'review of systems',
            'exam', 'physical', 'vitals',
            'assessment', 'plan', 'diagnosis'
        ]
        note_lower = note_text.lower()
        sections_found = sum(1 for kw in section_keywords if kw in note_lower)

        if sections_found == 0:
            warnings.append("No structured sections detected")
            quality_score *= 0.8
        elif sections_found < 3:
            warnings.append("Limited structured sections detected")
            quality_score *= 0.9

        # Check for numeric values (suggests vitals/labs documented)
        has_numbers = bool(re.search(r'\d{2,3}', note_text))
        if not has_numbers:
            warnings.append("No numeric values found - may lack vital signs or lab data")
            quality_score *= 0.85

        return {
            "is_valid": len(errors) == 0,
            "quality_score": round(quality_score, 2),
            "errors": errors,
            "warnings": warnings,
            "note_length": len(note_text),
            "sections_detected": sections_found,
        }


# ============================================================================
# Validation Issue Tracking
# ============================================================================

@dataclass
class ValidationIssue:
    """A single validation issue."""
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'guideline', 'cost', 'code', 'evidence'
    message: str
    recommendation: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "recommendation": self.recommendation,
            "expected": self.expected,
            "actual": self.actual,
        }


@dataclass
class ValidationReport:
    """Complete validation report."""
    is_valid: bool
    confidence_score: float  # 0.0 to 1.0
    issues: List[ValidationIssue]
    items_checked: int
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "confidence_score": self.confidence_score,
            "issues": [issue.to_dict() for issue in self.issues],
            "items_checked": self.items_checked,
            "summary": self.summary,
        }
