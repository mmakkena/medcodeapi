"""
Clinical Coding Helper

Provides code suggestions and validation for clinical documentation:
- ICD-10 code suggestions based on clinical findings
- CPT code suggestions based on procedures
- Code validation and cross-referencing
- Clinical term to code mapping
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CodeSuggestion:
    """Suggested medical code."""
    code: str
    code_system: str  # ICD-10, CPT, HCPCS
    description: str
    confidence: float
    clinical_indicator: Optional[str] = None
    mapping_source: str = "rule_based"


@dataclass
class CodeValidationResult:
    """Result of code validation."""
    is_valid: bool
    code: str
    code_system: str
    description: Optional[str] = None
    issues: List[str] = None
    suggestions: List[str] = None


class ClinicalCodingHelper:
    """
    Provides clinical coding assistance.

    Features:
    - Rule-based code suggestions from clinical findings
    - Code validation
    - Cross-reference between code systems
    """

    # Common diagnosis to ICD-10 mappings
    DIAGNOSIS_ICD10_MAP = {
        # Cardiovascular
        "hypertension": [
            {"code": "I10", "description": "Essential (primary) hypertension"},
            {"code": "I11.9", "description": "Hypertensive heart disease without heart failure"},
            {"code": "I12.9", "description": "Hypertensive chronic kidney disease, stage 1-4 or unspecified"},
        ],
        "heart failure": [
            {"code": "I50.9", "description": "Heart failure, unspecified"},
            {"code": "I50.20", "description": "Unspecified systolic (congestive) heart failure"},
            {"code": "I50.30", "description": "Unspecified diastolic (congestive) heart failure"},
            {"code": "I50.40", "description": "Unspecified combined systolic and diastolic heart failure"},
        ],
        "atrial fibrillation": [
            {"code": "I48.91", "description": "Unspecified atrial fibrillation"},
            {"code": "I48.0", "description": "Paroxysmal atrial fibrillation"},
            {"code": "I48.1", "description": "Persistent atrial fibrillation"},
        ],
        "coronary artery disease": [
            {"code": "I25.10", "description": "Atherosclerotic heart disease of native coronary artery"},
            {"code": "I25.110", "description": "Atherosclerotic heart disease with unstable angina pectoris"},
        ],

        # Endocrine
        "diabetes": [
            {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications"},
            {"code": "E11.65", "description": "Type 2 diabetes mellitus with hyperglycemia"},
            {"code": "E11.21", "description": "Type 2 diabetes mellitus with diabetic nephropathy"},
            {"code": "E11.42", "description": "Type 2 diabetes mellitus with diabetic polyneuropathy"},
        ],
        "type 1 diabetes": [
            {"code": "E10.9", "description": "Type 1 diabetes mellitus without complications"},
        ],
        "hyperlipidemia": [
            {"code": "E78.5", "description": "Hyperlipidemia, unspecified"},
            {"code": "E78.00", "description": "Pure hypercholesterolemia, unspecified"},
        ],
        "obesity": [
            {"code": "E66.9", "description": "Obesity, unspecified"},
            {"code": "E66.01", "description": "Morbid (severe) obesity due to excess calories"},
        ],

        # Respiratory
        "pneumonia": [
            {"code": "J18.9", "description": "Pneumonia, unspecified organism"},
            {"code": "J15.9", "description": "Unspecified bacterial pneumonia"},
            {"code": "J13", "description": "Pneumonia due to Streptococcus pneumoniae"},
        ],
        "copd": [
            {"code": "J44.9", "description": "Chronic obstructive pulmonary disease, unspecified"},
            {"code": "J44.1", "description": "Chronic obstructive pulmonary disease with acute exacerbation"},
        ],
        "asthma": [
            {"code": "J45.909", "description": "Unspecified asthma, uncomplicated"},
            {"code": "J45.901", "description": "Unspecified asthma with acute exacerbation"},
        ],
        "respiratory failure": [
            {"code": "J96.90", "description": "Respiratory failure, unspecified, unspecified whether with hypoxia or hypercapnia"},
            {"code": "J96.00", "description": "Acute respiratory failure, unspecified whether with hypoxia or hypercapnia"},
        ],

        # Renal
        "ckd": [
            {"code": "N18.9", "description": "Chronic kidney disease, unspecified"},
            {"code": "N18.3", "description": "Chronic kidney disease, stage 3"},
            {"code": "N18.4", "description": "Chronic kidney disease, stage 4"},
            {"code": "N18.5", "description": "Chronic kidney disease, stage 5"},
        ],
        "acute kidney injury": [
            {"code": "N17.9", "description": "Acute kidney failure, unspecified"},
        ],

        # Infectious
        "sepsis": [
            {"code": "A41.9", "description": "Sepsis, unspecified organism"},
            {"code": "R65.20", "description": "Severe sepsis without septic shock"},
            {"code": "R65.21", "description": "Severe sepsis with septic shock"},
        ],
        "urinary tract infection": [
            {"code": "N39.0", "description": "Urinary tract infection, site not specified"},
        ],

        # Mental Health
        "depression": [
            {"code": "F32.9", "description": "Major depressive disorder, single episode, unspecified"},
            {"code": "F33.9", "description": "Major depressive disorder, recurrent, unspecified"},
        ],
        "anxiety": [
            {"code": "F41.9", "description": "Anxiety disorder, unspecified"},
            {"code": "F41.1", "description": "Generalized anxiety disorder"},
        ],
    }

    # Common procedure to CPT mappings
    PROCEDURE_CPT_MAP = {
        "echocardiogram": [
            {"code": "93306", "description": "Echocardiography, transthoracic, real-time with image documentation"},
            {"code": "93308", "description": "Echocardiography, transthoracic, limited"},
        ],
        "chest x-ray": [
            {"code": "71046", "description": "Radiologic examination, chest; 2 views"},
            {"code": "71045", "description": "Radiologic examination, chest; single view"},
        ],
        "ct chest": [
            {"code": "71250", "description": "Computed tomography, thorax; without contrast material"},
            {"code": "71260", "description": "Computed tomography, thorax; with contrast material(s)"},
        ],
        "ekg": [
            {"code": "93000", "description": "Electrocardiogram, routine ECG with at least 12 leads; with interpretation and report"},
        ],
        "blood culture": [
            {"code": "87040", "description": "Culture, bacterial; blood, aerobic, with isolation and presumptive identification"},
        ],
        "cbc": [
            {"code": "85025", "description": "Blood count; complete (CBC), automated"},
        ],
        "comprehensive metabolic panel": [
            {"code": "80053", "description": "Comprehensive metabolic panel"},
        ],
        "urinalysis": [
            {"code": "81003", "description": "Urinalysis, by dip stick or tablet reagent"},
        ],
    }

    def suggest_codes_from_text(
        self,
        clinical_text: str,
        code_system: str = "ICD-10",
        max_suggestions: int = 10
    ) -> List[CodeSuggestion]:
        """
        Suggest codes based on clinical text.

        Args:
            clinical_text: Clinical documentation text
            code_system: Target code system (ICD-10, CPT)
            max_suggestions: Maximum number of suggestions

        Returns:
            List of CodeSuggestion objects
        """
        suggestions = []
        text_lower = clinical_text.lower()

        if code_system.upper() in ["ICD-10", "ICD10"]:
            # Search for diagnosis matches
            for diagnosis, codes in self.DIAGNOSIS_ICD10_MAP.items():
                if diagnosis in text_lower:
                    for code_info in codes[:2]:  # Top 2 codes per condition
                        suggestions.append(CodeSuggestion(
                            code=code_info["code"],
                            code_system="ICD-10",
                            description=code_info["description"],
                            confidence=0.8,
                            clinical_indicator=diagnosis,
                            mapping_source="rule_based"
                        ))

        elif code_system.upper() == "CPT":
            # Search for procedure matches
            for procedure, codes in self.PROCEDURE_CPT_MAP.items():
                if procedure in text_lower or any(word in text_lower for word in procedure.split()):
                    for code_info in codes[:1]:  # Top code per procedure
                        suggestions.append(CodeSuggestion(
                            code=code_info["code"],
                            code_system="CPT",
                            description=code_info["description"],
                            confidence=0.85,
                            clinical_indicator=procedure,
                            mapping_source="rule_based"
                        ))

        # Sort by confidence and limit
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        return suggestions[:max_suggestions]

    def suggest_codes_from_entities(
        self,
        diagnoses: List[str],
        procedures: List[str] = None
    ) -> Dict[str, List[CodeSuggestion]]:
        """
        Suggest codes based on extracted entities.

        Args:
            diagnoses: List of diagnosis names
            procedures: List of procedure names

        Returns:
            Dict with 'icd10' and 'cpt' code suggestions
        """
        if procedures is None:
            procedures = []

        result = {
            "icd10": [],
            "cpt": []
        }

        # Map diagnoses to ICD-10
        for diagnosis in diagnoses:
            dx_lower = diagnosis.lower()
            for condition, codes in self.DIAGNOSIS_ICD10_MAP.items():
                if condition in dx_lower:
                    for code_info in codes[:2]:
                        result["icd10"].append(CodeSuggestion(
                            code=code_info["code"],
                            code_system="ICD-10",
                            description=code_info["description"],
                            confidence=0.85,
                            clinical_indicator=diagnosis,
                            mapping_source="entity_mapping"
                        ))
                    break

        # Map procedures to CPT
        for procedure in procedures:
            proc_lower = procedure.lower()
            for proc_name, codes in self.PROCEDURE_CPT_MAP.items():
                if proc_name in proc_lower:
                    for code_info in codes[:1]:
                        result["cpt"].append(CodeSuggestion(
                            code=code_info["code"],
                            code_system="CPT",
                            description=code_info["description"],
                            confidence=0.9,
                            clinical_indicator=procedure,
                            mapping_source="entity_mapping"
                        ))
                    break

        return result

    def validate_code(
        self,
        code: str,
        code_system: str = "ICD-10"
    ) -> CodeValidationResult:
        """
        Validate a medical code.

        Args:
            code: Code to validate
            code_system: Code system (ICD-10, CPT, HCPCS)

        Returns:
            CodeValidationResult
        """
        issues = []
        suggestions = []

        if code_system.upper() in ["ICD-10", "ICD10"]:
            # Basic ICD-10 format validation
            pattern = r'^[A-Z]\d{2}(\.\d{1,4})?$'
            is_valid_format = bool(re.match(pattern, code.upper()))

            if not is_valid_format:
                issues.append("Invalid ICD-10 format. Expected: Letter + 2 digits + optional decimal + 1-4 digits")

            # Look up description
            description = self._lookup_icd10_description(code)

            return CodeValidationResult(
                is_valid=is_valid_format and description is not None,
                code=code,
                code_system="ICD-10",
                description=description,
                issues=issues if issues else None,
                suggestions=suggestions if suggestions else None
            )

        elif code_system.upper() == "CPT":
            # Basic CPT format validation
            pattern = r'^\d{5}$'
            is_valid_format = bool(re.match(pattern, code))

            if not is_valid_format:
                issues.append("Invalid CPT format. Expected: 5 digits")

            description = self._lookup_cpt_description(code)

            return CodeValidationResult(
                is_valid=is_valid_format,
                code=code,
                code_system="CPT",
                description=description,
                issues=issues if issues else None,
                suggestions=suggestions if suggestions else None
            )

        else:
            return CodeValidationResult(
                is_valid=False,
                code=code,
                code_system=code_system,
                issues=[f"Unsupported code system: {code_system}"]
            )

    def _lookup_icd10_description(self, code: str) -> Optional[str]:
        """Look up ICD-10 code description."""
        code_upper = code.upper()
        for _, codes in self.DIAGNOSIS_ICD10_MAP.items():
            for code_info in codes:
                if code_info["code"].upper() == code_upper:
                    return code_info["description"]
        return None

    def _lookup_cpt_description(self, code: str) -> Optional[str]:
        """Look up CPT code description."""
        for _, codes in self.PROCEDURE_CPT_MAP.items():
            for code_info in codes:
                if code_info["code"] == code:
                    return code_info["description"]
        return None

    def get_related_codes(
        self,
        code: str,
        code_system: str = "ICD-10"
    ) -> List[CodeSuggestion]:
        """
        Get related codes for a given code.

        Args:
            code: Source code
            code_system: Code system

        Returns:
            List of related CodeSuggestion objects
        """
        related = []

        if code_system.upper() in ["ICD-10", "ICD10"]:
            # Find codes in same category
            code_prefix = code[:3]
            for _, codes in self.DIAGNOSIS_ICD10_MAP.items():
                for code_info in codes:
                    if code_info["code"].startswith(code_prefix) and code_info["code"] != code:
                        related.append(CodeSuggestion(
                            code=code_info["code"],
                            code_system="ICD-10",
                            description=code_info["description"],
                            confidence=0.7,
                            mapping_source="related_codes"
                        ))

        return related[:5]  # Limit to 5 related codes


# Convenience functions
def suggest_codes(
    clinical_note: str,
    code_system: str = "ICD-10"
) -> List[CodeSuggestion]:
    """
    Convenience function to suggest codes from clinical text.

    Args:
        clinical_note: Clinical documentation text
        code_system: Target code system

    Returns:
        List of CodeSuggestion objects
    """
    helper = ClinicalCodingHelper()
    return helper.suggest_codes_from_text(clinical_note, code_system)


def validate_code(code: str, code_system: str = "ICD-10") -> CodeValidationResult:
    """
    Convenience function to validate a code.

    Args:
        code: Code to validate
        code_system: Code system

    Returns:
        CodeValidationResult
    """
    helper = ClinicalCodingHelper()
    return helper.validate_code(code, code_system)
