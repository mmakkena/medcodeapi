"""
HEDIS Exclusion Criteria

Defines exclusion criteria for HEDIS measures and provides
functions to check if a patient should be excluded from measures.
"""

import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


# HEDIS Exclusion Categories
HEDIS_EXCLUSIONS = {
    # Hospice care - excludes patient from most quality measures
    "hospice": {
        "keywords": ["hospice", "hospice care", "end of life care", "comfort care only",
                     "palliative care consultation"],
        "description": "Patient enrolled in hospice or receiving end-of-life care",
        "affects_measures": ["CBP", "CDC", "BCS", "COL", "BMI", "DEP", "AAP", "WCC", "AWC"]
    },

    # End-Stage Renal Disease (ESRD) - excludes from certain measures
    "esrd": {
        "keywords": ["ESRD", "end-stage renal disease", "dialysis", "hemodialysis",
                     "peritoneal dialysis", "kidney failure", "renal failure stage 5",
                     "chronic kidney disease stage 5"],
        "description": "Patient with End-Stage Renal Disease",
        "affects_measures": ["CBP", "CDC"]
    },

    # Advanced illness - excludes from certain preventive measures
    "advanced_illness": {
        "keywords": ["metastatic cancer", "stage IV cancer", "advanced cancer",
                     "terminal illness", "advanced COPD", "severe dementia",
                     "advanced heart failure NYHA IV", "advanced cirrhosis",
                     "end-stage liver disease"],
        "description": "Patient with advanced/terminal illness",
        "affects_measures": ["BCS", "COL", "AAP"]
    },

    # Frailty - excludes from certain measures when combined with advanced illness
    "frailty": {
        "keywords": ["frailty", "frail elderly", "failure to thrive",
                     "severe functional decline", "bedbound", "wheelchair-bound",
                     "nursing home resident"],
        "description": "Patient with documented frailty",
        "affects_measures": []  # Usually combined with advanced_illness
    },

    # Pregnancy - excludes from certain measures
    "pregnancy": {
        "keywords": ["pregnant", "pregnancy", "gravid", "gestational", "prenatal",
                     "antepartum", "trimester", "weeks gestation", "intrauterine pregnancy"],
        "description": "Patient is currently pregnant",
        "affects_measures": ["CBP", "BMI"]  # Different targets during pregnancy
    },

    # Dementia - excludes from certain behavioral health measures
    "dementia": {
        "keywords": ["dementia", "Alzheimer", "vascular dementia",
                     "cognitive impairment severe", "advanced dementia",
                     "frontotemporal dementia"],
        "description": "Patient with dementia diagnosis",
        "affects_measures": ["DEP", "AMM"]  # Depression screening may not be valid
    },

    # Bilateral mastectomy - excludes from breast cancer screening
    "bilateral_mastectomy": {
        "keywords": ["bilateral mastectomy", "total mastectomy bilateral",
                     "both breasts removed", "status post bilateral mastectomy",
                     "s/p bilateral mastectomy"],
        "description": "Patient has had bilateral mastectomy",
        "affects_measures": ["BCS"]
    },

    # Colorectal cancer - excludes from colorectal screening
    "colorectal_cancer": {
        "keywords": ["colorectal cancer", "colon cancer", "rectal cancer",
                     "history of colon cancer", "status post colectomy for cancer",
                     "total colectomy"],
        "description": "Patient with history of colorectal cancer or total colectomy",
        "affects_measures": ["COL"]
    },

    # Institutional care - affects certain measures
    "institutional_care": {
        "keywords": ["nursing home", "skilled nursing facility", "long-term care facility",
                     "psychiatric institution", "institutionalized"],
        "description": "Patient residing in institutional care setting",
        "affects_measures": ["AAP"]
    },

    # Blindness - may exclude from certain screenings
    "blindness": {
        "keywords": ["blind", "blindness", "bilateral vision loss", "legal blindness",
                     "no light perception bilateral"],
        "description": "Patient with bilateral blindness",
        "affects_measures": ["BCS", "COL"]
    }
}

# Measure-specific exclusion combinations
MEASURE_EXCLUSION_RULES = {
    "CBP": ["hospice", "esrd", "pregnancy"],
    "CDC": ["hospice", "esrd"],
    "BCS": ["hospice", "bilateral_mastectomy", "advanced_illness", "blindness"],
    "COL": ["hospice", "colorectal_cancer", "advanced_illness", "blindness"],
    "BMI": ["hospice", "pregnancy"],
    "DEP": ["hospice", "dementia"],
    "AAP": ["hospice", "institutional_care", "advanced_illness"],
    "WCC": ["hospice"],
    "AWC": ["hospice"],
    "AMM": ["hospice", "dementia"],
    "FUH": ["hospice"],
    "FUM": ["hospice"],
    "FUA": ["hospice"],
    "ADD": ["hospice"],
    "CHL": ["hospice", "pregnancy"],
    "IMA": ["hospice"],
    "CIS": ["hospice"],
    "W15": ["hospice"],
    "W34": ["hospice"],
    "PPC": [],  # Pregnancy measure, no pregnancy exclusion
    "PCE": ["hospice"]
}


def check_hedis_exclusions(
    diagnoses: List[str],
    note_text: str = ""
) -> Dict[str, Dict]:
    """
    Check for HEDIS exclusion criteria in diagnoses and clinical note.

    Args:
        diagnoses: List of extracted diagnoses
        note_text: Full clinical note text (optional, for context-based detection)

    Returns:
        Dict of identified exclusions:
        {
            "hospice": {
                "present": True,
                "reason": "hospice care",
                "affects": ["CBP", "CDC", "BCS", ...]
            },
            ...
        }
    """
    identified_exclusions = {}

    # Combine diagnoses into searchable text
    # Handle both string diagnoses and Diagnosis objects
    diagnosis_texts = []
    for dx in diagnoses:
        if hasattr(dx, 'name'):
            diagnosis_texts.append(dx.name)
        else:
            diagnosis_texts.append(str(dx))
    all_text = " ".join(diagnosis_texts).lower() + " " + note_text.lower()

    for exclusion_type, criteria in HEDIS_EXCLUSIONS.items():
        keywords = criteria["keywords"]

        # Check if any keyword matches
        found = False
        matched_keyword = None
        for keyword in keywords:
            if keyword.lower() in all_text:
                found = True
                matched_keyword = keyword
                break

        if found:
            identified_exclusions[exclusion_type] = {
                "present": True,
                "reason": matched_keyword,
                "description": criteria["description"],
                "affects": criteria["affects_measures"]
            }

    return identified_exclusions


def is_measure_excluded(
    measure_code: str,
    exclusions: Dict[str, Dict]
) -> Tuple[bool, Optional[str]]:
    """
    Check if a specific HEDIS measure should be excluded.

    Args:
        measure_code: HEDIS measure code (e.g., "CBP", "CDC")
        exclusions: Dict of identified exclusions from check_hedis_exclusions()

    Returns:
        Tuple of (is_excluded, exclusion_reason)
    """
    if measure_code not in MEASURE_EXCLUSION_RULES:
        return False, None

    applicable_exclusions = MEASURE_EXCLUSION_RULES[measure_code]

    for exclusion_type in applicable_exclusions:
        if exclusion_type in exclusions and exclusions[exclusion_type]["present"]:
            reason = f"Excluded: {exclusions[exclusion_type]['description']}"
            return True, reason

    return False, None
