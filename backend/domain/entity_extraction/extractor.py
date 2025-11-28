"""
Clinical Entity Extraction

Extracts clinical entities (diagnoses, vitals, labs, screenings) from clinical notes
using regex patterns and optional NLP enhancement.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any

from domain.common.models import (
    ClinicalEntities,
    VitalSigns,
    LabResults,
    Screenings,
    Diagnosis,
    Medication,
    PatientDemographics,
)
from domain.common.validation import (
    parse_blood_pressure,
    parse_hba1c,
    parse_bmi,
    parse_ldl,
    parse_heart_rate,
    parse_temperature,
    parse_spo2,
    parse_creatinine,
    parse_glucose,
)

logger = logging.getLogger(__name__)


class ClinicalEntityExtractor:
    """
    Extracts clinical entities from clinical notes.

    Supports:
    - Vital signs extraction (BP, HR, BMI, etc.)
    - Lab results extraction (HbA1c, LDL, etc.)
    - Diagnosis extraction
    - Medication extraction
    - Screening information extraction
    """

    # Vital signs patterns
    VITAL_PATTERNS = {
        'blood_pressure': r"(?:bp|blood pressure)[:\s]*(\d{2,3}/\d{2,3})|(\d{2,3}/\d{2,3})\s*mmhg",
        'heart_rate': r"(?:hr|heart rate|pulse)[:\s]*(\d{2,3})",
        'temperature': r"(?:temp|temperature)[:\s]*(\d{2,3}\.?\d*)\s*[°]?[fc]?",
        'respiratory_rate': r"(?:rr|respiratory rate|resp)[:\s]*(\d{1,2})",
        'spo2': r"(?:spo2|o2 sat|oxygen|sat)[:\s]*(\d{2,3})\s*%?",
        'bmi': r"bmi[:\s]*(\d{2}\.?\d*)",
        'weight': r"(?:weight|wt)[:\s]*(\d{2,3}\.?\d*)\s*(?:kg|lb)?",
        'height': r"(?:height|ht)[:\s]*(\d{1,3}\.?\d*)\s*(?:cm|in)?",
    }

    # Lab result patterns
    LAB_PATTERNS = {
        'hba1c': r"hba1c[:\s]*(\d{1,2}\.?\d*)\s*%?|a1c[:\s]*(\d{1,2}\.?\d*)",
        'ldl': r"ldl[:\s]*(\d{1,3})",
        'hdl': r"hdl[:\s]*(\d{1,3})",
        'total_cholesterol': r"(?:total cholesterol|tc)[:\s]*(\d{2,3})",
        'triglycerides': r"(?:triglycerides|tg)[:\s]*(\d{2,4})",
        'creatinine': r"(?:cr|creatinine)[:\s]*(\d{1,2}\.?\d*)",
        'egfr': r"(?:egfr|gfr)[:\s]*(\d{1,3})",
        'bnp': r"bnp[:\s]*(\d{1,5})",
        'troponin': r"troponin[:\s]*(\d*\.?\d+)",
        'procalcitonin': r"procalcitonin[:\s]*(\d*\.?\d+)",
        'lactate': r"lactate[:\s]*(\d*\.?\d+)",
        'glucose': r"(?:glucose|bg|blood sugar)[:\s]*(\d{2,4})",
        'potassium': r"(?:potassium|k\+?)[:\s]*(\d\.?\d*)",
        'sodium': r"(?:sodium|na\+?)[:\s]*(\d{2,3})",
        'wbc': r"(?:wbc|white blood count)[:\s]*(\d{1,2}\.?\d*)",
        'hemoglobin': r"(?:hgb|hemoglobin|hb)[:\s]*(\d{1,2}\.?\d*)",
        'platelets': r"(?:platelets|plt)[:\s]*(\d{2,4})",
        'inr': r"inr[:\s]*(\d\.?\d*)",
    }

    # Diagnosis patterns
    DIAGNOSIS_PATTERNS = {
        'hypertension': r"\b(?:hypertension|htn|essential hypertension|high blood pressure)\b",
        'diabetes': r"\b(?:diabetes|dm|type 2 diabetes|t2dm|diabetic)\b",
        'type_1_diabetes': r"\b(?:type 1 diabetes|t1dm|type 1 dm)\b",
        'heart_failure': r"\b(?:heart failure|chf|hfref|hfpef|congestive heart failure)\b",
        'copd': r"\b(?:copd|chronic obstructive pulmonary disease)\b",
        'asthma': r"\basthma\b",
        'ckd': r"\b(?:ckd|chronic kidney disease|renal failure)\b",
        'obesity': r"\bobesity\b",
        'hyperlipidemia': r"\b(?:hyperlipidemia|dyslipidemia|high cholesterol)\b",
        'depression': r"\b(?:depression|depressive disorder|mdd)\b",
        'anxiety': r"\b(?:anxiety|anxiety disorder|gad)\b",
        'afib': r"\b(?:afib|atrial fibrillation|a-fib)\b",
        'cad': r"\b(?:cad|coronary artery disease|coronary disease)\b",
        'pneumonia': r"\bpneumonia\b",
        'sepsis': r"\bsepsis\b",
        'stroke': r"\b(?:stroke|cva|cerebrovascular accident)\b",
        'mi': r"\b(?:mi|myocardial infarction|heart attack)\b",
    }

    # Screening patterns
    SCREENING_PATTERNS = {
        'mammogram': r"\bmammogram\b",
        'colonoscopy': r"\bcolonoscopy\b",
        'fit_test': r"\b(?:fit|fecal immunochemical)\b",
        'cologuard': r"\bcologuard\b",
        'depression_screening': r"\b(?:phq|depression screen|phq-9|phq-2)\b",
        'chlamydia': r"\b(?:chlamydia|ct screen)\b",
        'cervical_cancer': r"\b(?:pap|cervical cancer screen|pap smear)\b",
        'lung_cancer': r"\b(?:ldct|low-dose ct|lung cancer screen)\b",
        'bone_density': r"\b(?:dexa|bone density|dxa)\b",
        'diabetic_eye': r"\b(?:diabetic retinopathy|retinal exam|eye exam)\b",
        'diabetic_foot': r"\b(?:foot exam|monofilament|diabetic foot)\b",
    }

    # Medication class patterns
    MEDICATION_PATTERNS = {
        'antihypertensive': r"\b(?:lisinopril|amlodipine|losartan|metoprolol|atenolol|carvedilol|hydralazine|hctz)\b",
        'antidiabetic': r"\b(?:metformin|glipizide|glyburide|insulin|ozempic|trulicity|jardiance|farxiga)\b",
        'statin': r"\b(?:atorvastatin|simvastatin|rosuvastatin|pravastatin|lipitor|crestor)\b",
        'anticoagulant': r"\b(?:warfarin|coumadin|eliquis|xarelto|apixaban|rivaroxaban)\b",
        'antidepressant': r"\b(?:sertraline|fluoxetine|escitalopram|citalopram|prozac|zoloft|lexapro)\b",
        'diuretic': r"\b(?:furosemide|lasix|bumetanide|spironolactone)\b",
        'beta_blocker': r"\b(?:metoprolol|atenolol|carvedilol|propranolol)\b",
        'ace_inhibitor': r"\b(?:lisinopril|enalapril|ramipril|benazepril)\b",
        'arb': r"\b(?:losartan|valsartan|irbesartan|olmesartan)\b",
        'opioid': r"\b(?:oxycodone|hydrocodone|morphine|fentanyl)\b",
        'buprenorphine': r"\b(?:buprenorphine|suboxone|sublocade)\b",
        'naltrexone': r"\bnaltrexone\b",
        'methadone': r"\bmethadone\b",
        'adhd_medication': r"\b(?:adderall|ritalin|methylphenidate|amphetamine|vyvanse)\b",
    }

    # PFSH patterns
    PFSH_PATTERNS = {
        'past_history': r"\b(?:history of|h/o|past medical history|pmh|previous|prior)\b",
        'family_history': r"\b(?:family history|fh|mother|father|sibling|familial)\b",
        'social_history': r"\b(?:social history|sh|tobacco|alcohol|smoking|occupation|lives with)\b",
    }

    def __init__(self, use_nlp: bool = False):
        """
        Initialize entity extractor.

        Args:
            use_nlp: Whether to use NLP enhancement (requires spacy/medspacy)
        """
        self.use_nlp = use_nlp
        self._nlp = None

        if use_nlp:
            try:
                import medspacy
                self._nlp = medspacy.load(enable=["tok2vec", "ner", "context", "sectionizer"])
                logger.info("medSpaCy loaded for NLP-enhanced extraction")
            except ImportError:
                logger.warning("medSpaCy not available - using regex-only extraction")
                self.use_nlp = False

    def extract(self, clinical_note: str) -> ClinicalEntities:
        """
        Extract all clinical entities from a clinical note.

        Args:
            clinical_note: Clinical note text

        Returns:
            ClinicalEntities with all extracted data
        """
        if not clinical_note:
            return ClinicalEntities(
                extraction_confidence=0.0,
                extraction_warnings=["Empty clinical note"]
            )

        note_lower = clinical_note.lower()

        # Extract all entity types
        vitals = self._extract_vitals(note_lower)
        labs = self._extract_labs(note_lower)
        diagnoses = self._extract_diagnoses(note_lower)
        medications = self._extract_medications(note_lower)
        screenings = self._extract_screenings(note_lower)
        demographics = self._extract_demographics(note_lower)

        # Calculate extraction confidence
        confidence, warnings = self._calculate_confidence(
            clinical_note, vitals, labs, diagnoses, screenings
        )

        return ClinicalEntities(
            diagnoses=diagnoses,
            vitals=vitals,
            labs=labs,
            screenings=screenings,
            medications=medications,
            demographics=demographics,
            extraction_confidence=confidence,
            extraction_warnings=warnings,
            raw_text_length=len(clinical_note),
        )

    def _extract_vitals(self, note_text: str) -> VitalSigns:
        """Extract vital signs from clinical note."""
        vitals = VitalSigns()

        for vital_type, pattern in self.VITAL_PATTERNS.items():
            match = re.search(pattern, note_text, re.IGNORECASE)
            if match:
                # Get the first non-None group
                value = next((g for g in match.groups() if g), None)
                if value:
                    if vital_type == 'blood_pressure':
                        vitals.blood_pressure = value
                        systolic, diastolic = parse_blood_pressure(value)
                        vitals.systolic = systolic
                        vitals.diastolic = diastolic
                    elif vital_type == 'heart_rate':
                        vitals.heart_rate = parse_heart_rate(value)
                    elif vital_type == 'temperature':
                        vitals.temperature = parse_temperature(value)
                    elif vital_type == 'respiratory_rate':
                        try:
                            vitals.respiratory_rate = int(value)
                        except ValueError:
                            pass
                    elif vital_type == 'spo2':
                        vitals.spo2 = parse_spo2(value)
                    elif vital_type == 'bmi':
                        vitals.bmi = parse_bmi(value)
                    elif vital_type == 'weight':
                        try:
                            vitals.weight = float(value)
                        except ValueError:
                            pass
                    elif vital_type == 'height':
                        try:
                            vitals.height = float(value)
                        except ValueError:
                            pass

        return vitals

    def _extract_labs(self, note_text: str) -> LabResults:
        """Extract lab results from clinical note."""
        labs = LabResults()

        for lab_type, pattern in self.LAB_PATTERNS.items():
            match = re.search(pattern, note_text, re.IGNORECASE)
            if match:
                value = next((g for g in match.groups() if g), None)
                if value:
                    try:
                        if lab_type == 'hba1c':
                            labs.hba1c = parse_hba1c(value)
                        elif lab_type == 'ldl':
                            labs.ldl = parse_ldl(value)
                        elif lab_type == 'hdl':
                            labs.hdl = int(value)
                        elif lab_type == 'total_cholesterol':
                            labs.total_cholesterol = int(value)
                        elif lab_type == 'triglycerides':
                            labs.triglycerides = int(value)
                        elif lab_type == 'creatinine':
                            labs.creatinine = parse_creatinine(value)
                        elif lab_type == 'egfr':
                            labs.egfr = float(value)
                        elif lab_type == 'bnp':
                            labs.bnp = float(value)
                        elif lab_type == 'troponin':
                            labs.troponin = float(value)
                        elif lab_type == 'procalcitonin':
                            labs.procalcitonin = float(value)
                        elif lab_type == 'lactate':
                            labs.lactate = float(value)
                        elif lab_type == 'glucose':
                            labs.glucose = parse_glucose(value)
                        elif lab_type == 'potassium':
                            labs.potassium = float(value)
                        elif lab_type == 'sodium':
                            labs.sodium = int(value)
                        elif lab_type == 'wbc':
                            labs.wbc = float(value)
                        elif lab_type == 'hemoglobin':
                            labs.hemoglobin = float(value)
                        elif lab_type == 'platelets':
                            labs.platelets = int(value)
                        elif lab_type == 'inr':
                            labs.inr = float(value)
                    except (ValueError, TypeError):
                        logger.debug(f"Could not parse {lab_type} value: {value}")

        return labs

    def _extract_diagnoses(self, note_text: str) -> List[Diagnosis]:
        """Extract diagnoses from clinical note."""
        diagnoses = []

        for diagnosis_name, pattern in self.DIAGNOSIS_PATTERNS.items():
            if re.search(pattern, note_text, re.IGNORECASE):
                # Clean up name
                display_name = diagnosis_name.replace('_', ' ').title()
                diagnoses.append(Diagnosis(
                    name=display_name,
                    confidence=0.9
                ))

        return diagnoses

    def _extract_medications(self, note_text: str) -> List[Medication]:
        """Extract medications from clinical note."""
        medications = []

        for drug_class, pattern in self.MEDICATION_PATTERNS.items():
            matches = re.findall(pattern, note_text, re.IGNORECASE)
            for med_name in matches:
                medications.append(Medication(
                    name=med_name.lower(),
                    drug_class=drug_class
                ))

        # Remove duplicates
        seen = set()
        unique_meds = []
        for med in medications:
            if med.name not in seen:
                seen.add(med.name)
                unique_meds.append(med)

        return unique_meds

    def _extract_screenings(self, note_text: str) -> Screenings:
        """Extract screening information from clinical note."""
        screenings = Screenings()

        for screening_type, pattern in self.SCREENING_PATTERNS.items():
            if re.search(pattern, note_text, re.IGNORECASE):
                setattr(screenings, screening_type, True)

                # Extract depression score if present
                if screening_type == 'depression_screening':
                    score_match = re.search(r"phq-?9?[:\s]*(\d{1,2})", note_text, re.IGNORECASE)
                    if score_match:
                        try:
                            screenings.depression_score = int(score_match.group(1))
                            screenings.depression_tool = "PHQ-9"
                        except ValueError:
                            pass

        return screenings

    def _extract_demographics(self, note_text: str) -> PatientDemographics:
        """Extract patient demographics from clinical note."""
        demographics = PatientDemographics()

        # Age extraction
        age_match = re.search(r"(\d{1,3})\s*(?:year|y/?o|yo)[\s\-]*old", note_text, re.IGNORECASE)
        if age_match:
            try:
                demographics.age = int(age_match.group(1))
            except ValueError:
                pass

        # Gender extraction
        if re.search(r"\b(?:male|man|gentleman|he|his)\b", note_text, re.IGNORECASE):
            demographics.gender = "male"
        elif re.search(r"\b(?:female|woman|lady|she|her)\b", note_text, re.IGNORECASE):
            demographics.gender = "female"

        return demographics

    def _calculate_confidence(
        self,
        note_text: str,
        vitals: VitalSigns,
        labs: LabResults,
        diagnoses: List[Diagnosis],
        screenings: Screenings
    ) -> Tuple[float, List[str]]:
        """Calculate extraction confidence and generate warnings."""
        warnings = []
        confidence = 1.0

        # Check note length
        if len(note_text) < 50:
            warnings.append("Very short clinical note - extraction may be incomplete")
            confidence *= 0.7
        elif len(note_text) < 100:
            warnings.append("Short clinical note - may lack comprehensive data")
            confidence *= 0.85

        # Check for structured sections
        section_keywords = ['history', 'hpi', 'ros', 'exam', 'vitals', 'assessment', 'plan']
        sections_found = sum(1 for kw in section_keywords if kw in note_text.lower())
        if sections_found == 0:
            warnings.append("No structured sections detected")
            confidence *= 0.8

        # Count entities extracted
        vitals_count = sum(1 for v in [
            vitals.blood_pressure, vitals.heart_rate, vitals.bmi,
            vitals.temperature, vitals.spo2
        ] if v is not None)

        labs_count = sum(1 for v in [
            labs.hba1c, labs.ldl, labs.creatinine, labs.glucose
        ] if v is not None)

        total_entities = len(diagnoses) + vitals_count + labs_count

        # Check for sparse extraction
        if total_entities == 0 and len(note_text) > 100:
            warnings.append("No clinical entities extracted - note may be ambiguous")
            confidence = 0.2
        elif total_entities < 3 and len(note_text) > 200:
            warnings.append("Low entity extraction from substantial note")
            confidence *= 0.8

        # Context-specific checks
        note_lower = note_text.lower()
        if any(kw in note_lower for kw in ["hypertension", "htn"]):
            if vitals.blood_pressure is None:
                warnings.append("Hypertension mentioned but BP not extracted")
                confidence *= 0.9

        if any(kw in note_lower for kw in ["diabetes", "diabetic", "dm"]):
            if labs.hba1c is None:
                warnings.append("Diabetes mentioned but HbA1c not extracted")
                confidence *= 0.9

        return round(confidence, 3), warnings


# Convenience functions
def extract_entities(clinical_note: str) -> ClinicalEntities:
    """
    Extract all clinical entities from a clinical note.

    Args:
        clinical_note: Clinical note text

    Returns:
        ClinicalEntities with all extracted data
    """
    extractor = ClinicalEntityExtractor()
    return extractor.extract(clinical_note)


def extract_vitals(clinical_note: str) -> Dict[str, str]:
    """
    Extract vital signs as a simple dict.

    Args:
        clinical_note: Clinical note text

    Returns:
        Dict of vital sign name -> value
    """
    extractor = ClinicalEntityExtractor()
    entities = extractor.extract(clinical_note)
    return entities.get_vitals_dict()


def extract_labs(clinical_note: str) -> Dict[str, str]:
    """
    Extract lab results as a simple dict.

    Args:
        clinical_note: Clinical note text

    Returns:
        Dict of lab name -> value
    """
    extractor = ClinicalEntityExtractor()
    entities = extractor.extract(clinical_note)
    return entities.get_labs_dict()


def extract_diagnoses(clinical_note: str) -> List[str]:
    """
    Extract diagnosis names from clinical note.

    Args:
        clinical_note: Clinical note text

    Returns:
        List of diagnosis names
    """
    extractor = ClinicalEntityExtractor()
    entities = extractor.extract(clinical_note)
    return entities.get_diagnosis_names()
