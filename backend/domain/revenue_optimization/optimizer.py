"""
Revenue Optimization Analyzer

Analyzes clinical documentation for revenue optimization opportunities:
- E/M coding analysis
- DRG optimization
- HCC risk adjustment
- Missing test/procedure revenue
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from domain.common.models import (
    ClinicalEntities,
    RevenueOptimizationResult,
    EMCodeRecommendation,
    DRGOptimization,
    GapPriority,
)
from domain.common.scoring import calculate_em_level, calculate_revenue_capture_rate

logger = logging.getLogger(__name__)


@dataclass
class HistoryComponents:
    """History documentation components for E/M coding."""
    hpi_elements: List[str]
    ros_systems: List[str]
    pfsh_elements: List[str]

    def get_level(self) -> str:
        """Determine history level based on components."""
        hpi_count = len(self.hpi_elements)
        ros_count = len(self.ros_systems)
        pfsh_count = len(self.pfsh_elements)

        if hpi_count >= 4 and ros_count >= 10 and pfsh_count == 3:
            return "comprehensive"
        elif hpi_count >= 4 and 2 <= ros_count <= 9 and pfsh_count >= 1:
            return "detailed"
        elif 1 <= hpi_count <= 3 and ros_count >= 1:
            return "expanded_problem_focused"
        elif hpi_count >= 1:
            return "problem_focused"
        return "insufficient"


@dataclass
class ExamComponents:
    """Examination documentation components for E/M coding."""
    systems_examined: List[str]

    def get_level(self) -> str:
        """Determine examination level based on systems documented."""
        count = len(self.systems_examined)
        if count >= 8:
            return "comprehensive"
        elif count >= 4:
            return "detailed"
        elif count >= 2:
            return "expanded_problem_focused"
        elif count >= 1:
            return "problem_focused"
        return "insufficient"


@dataclass
class MDMComponents:
    """Medical Decision Making components for E/M coding."""
    diagnoses_count: int
    data_reviewed: List[str]
    risk_level: str

    def get_level(self) -> str:
        """Determine MDM complexity level."""
        data_count = len(self.data_reviewed)

        if self.diagnoses_count >= 3 or data_count >= 4 or self.risk_level == "high":
            return "high"
        elif self.diagnoses_count == 2 or 2 <= data_count <= 3 or self.risk_level == "moderate":
            return "moderate"
        elif self.diagnoses_count == 1 or data_count == 1 or self.risk_level == "low":
            return "low"
        return "straightforward"


class RevenueOptimizer:
    """
    Analyzes clinical documentation for revenue optimization.

    Capabilities:
    - E/M code analysis based on documentation components
    - DRG optimization opportunities
    - HCC risk adjustment opportunities
    - Missing test/procedure revenue identification
    """

    # HPI element patterns
    HPI_PATTERNS = {
        'location': r'\b(chest|abdomen|head|leg|arm|back|neck|throat|ear|eye)\b',
        'quality': r'\b(sharp|dull|aching|burning|stabbing|throbbing|cramping|pressure)\b',
        'severity': r'\b(mild|moderate|severe|worst|excruciating|10/10|\d+/10)\b',
        'duration': r'\b(\d+\s*(day|hour|week|month|year)s?|since|started|began|chronic|acute)\b',
        'timing': r'\b(constant|intermittent|morning|evening|night|continuous|episodic)\b',
        'context': r'\b(after|during|while|when|with|following|post)\b',
        'modifying_factors': r'\b(worse|better|improved|worsened|relieved by|aggravated by)\b',
        'associated_signs': r'\b(with|associated|accompanied by|along with)\b'
    }

    # ROS system patterns
    ROS_SYSTEMS = {
        'constitutional': r'\b(fever|chills|weight loss|fatigue|malaise|night sweats)\b',
        'eyes': r'\b(vision|diplopia|blurred vision|eye pain)\b',
        'enmt': r'\b(hearing|tinnitus|sinus|nasal|throat|ear pain)\b',
        'cardiovascular': r'\b(chest pain|palpitations|edema|orthopnea|PND)\b',
        'respiratory': r'\b(dyspnea|cough|wheezing|shortness of breath|SOB|hemoptysis)\b',
        'gastrointestinal': r'\b(nausea|vomiting|diarrhea|constipation|abdominal pain)\b',
        'genitourinary': r'\b(dysuria|hematuria|frequency|urgency|incontinence)\b',
        'musculoskeletal': r'\b(joint pain|arthralgia|myalgia|back pain|weakness)\b',
        'integumentary': r'\b(rash|lesion|wound|ulcer|pruritus)\b',
        'neurological': r'\b(headache|dizziness|syncope|seizure|numbness|tingling)\b',
        'psychiatric': r'\b(anxiety|depression|mood|sleep|insomnia)\b',
        'endocrine': r'\b(polyuria|polydipsia|heat intolerance|cold intolerance)\b',
        'hematologic': r'\b(bleeding|bruising|anemia|lymphadenopathy)\b',
        'allergic': r'\b(allergies|allergic reaction|anaphylaxis)\b'
    }

    # PFSH patterns
    PFSH_PATTERNS = {
        'past_history': r'\b(history of|h/o|past medical history|PMH|previous|prior)\b',
        'family_history': r'\b(family history|FH|mother|father|sibling|familial)\b',
        'social_history': r'\b(social history|SH|tobacco|alcohol|smoking|occupation)\b'
    }

    # Examination system patterns
    EXAM_SYSTEMS = {
        'constitutional': r'\b(vital signs|vitals|BP|HR|RR|temp|weight|general appearance)\b',
        'eyes': r'\b(PERRLA|conjunctiva|sclera|EOM|visual)\b',
        'enmt': r'\b(TMs|nasal mucosa|oropharynx|pharynx|tonsils|neck)\b',
        'cardiovascular': r'\b(heart|S1|S2|murmur|rhythm|regular|pulses|JVD)\b',
        'respiratory': r'\b(lungs|breath sounds|clear|crackles|wheezes|rhonchi)\b',
        'gastrointestinal': r'\b(abdomen|bowel sounds|tender|soft|distended|hepatomegaly)\b',
        'musculoskeletal': r'\b(extremities|ROM|strength|gait|spine|joints)\b',
        'integumentary': r'\b(skin|rash|lesion|turgor|wound|ulcer)\b',
        'neurological': r'\b(neuro|cranial nerves|reflexes|sensation|motor|mental status|alert)\b',
        'psychiatric': r'\b(affect|mood|oriented|A&O|judgment|insight)\b',
    }

    # Risk indicators
    RISK_INDICATORS = {
        'high': ['sepsis', 'respiratory failure', 'cardiac arrest', 'stroke', 'MI',
                 'ICU', 'ventilator', 'intubated', 'vasopressors', 'critical', 'unstable'],
        'moderate': ['pneumonia', 'CHF', 'COPD exacerbation', 'acute', 'exacerbation',
                    'uncontrolled', 'emergency'],
        'low': ['stable', 'chronic', 'well-controlled', 'routine', 'follow-up', 'mild']
    }

    # E/M code mapping (simplified)
    EM_CODES = {
        "inpatient_initial": {
            1: {"code": "99221", "reimbursement": 145.0},
            2: {"code": "99222", "reimbursement": 205.0},
            3: {"code": "99223", "reimbursement": 295.0},
            4: {"code": "99223", "reimbursement": 295.0},
        },
        "inpatient_subsequent": {
            1: {"code": "99231", "reimbursement": 80.0},
            2: {"code": "99232", "reimbursement": 115.0},
            3: {"code": "99233", "reimbursement": 165.0},
            4: {"code": "99233", "reimbursement": 165.0},
        },
        "outpatient_new": {
            1: {"code": "99202", "reimbursement": 75.0},
            2: {"code": "99203", "reimbursement": 115.0},
            3: {"code": "99204", "reimbursement": 175.0},
            4: {"code": "99205", "reimbursement": 235.0},
        },
        "outpatient_established": {
            1: {"code": "99211", "reimbursement": 25.0},
            2: {"code": "99212", "reimbursement": 55.0},
            3: {"code": "99213", "reimbursement": 95.0},
            4: {"code": "99214", "reimbursement": 135.0},
            5: {"code": "99215", "reimbursement": 185.0},
        },
    }

    def analyze(
        self,
        clinical_note: str,
        entities: Optional[ClinicalEntities] = None,
        setting: str = "inpatient",
        patient_type: str = "initial",
    ) -> RevenueOptimizationResult:
        """
        Analyze clinical note for revenue optimization opportunities.

        Args:
            clinical_note: Clinical documentation text
            entities: Optional pre-extracted clinical entities
            setting: Clinical setting (inpatient, outpatient)
            patient_type: Patient type (initial, subsequent, new, established)

        Returns:
            RevenueOptimizationResult with all optimization opportunities
        """
        if entities is None:
            from domain.entity_extraction import extract_entities
            entities = extract_entities(clinical_note)

        # Extract E/M components
        history = self._extract_history(clinical_note)
        exam = self._extract_exam(clinical_note)
        mdm = self._extract_mdm(clinical_note, entities)

        # Calculate E/M code
        em_recommendation = self._calculate_em_code(
            history, exam, mdm, setting, patient_type
        )

        # Identify DRG opportunities
        drg_optimization = self._analyze_drg_opportunities(entities, clinical_note)

        # Identify HCC opportunities
        hcc_opportunities = self._analyze_hcc_opportunities(entities)

        # Identify missing tests
        tests_documented, tests_missing = self._analyze_test_gaps(entities, clinical_note)

        # Calculate test revenue
        test_revenue = sum(t.get("cost", 0) for t in tests_missing)

        # Calculate totals
        total_revenue = (
            em_recommendation.revenue_gap +
            drg_optimization.revenue_impact +
            test_revenue
        )

        # Determine primary condition and severity
        primary_condition = entities.get_diagnosis_names()[0] if entities.diagnoses else "Unknown"
        severity = mdm.risk_level

        return RevenueOptimizationResult(
            condition=primary_condition,
            severity=severity,
            tests_documented=tests_documented,
            tests_missing=tests_missing,
            test_revenue_opportunity=test_revenue,
            em_recommendation=em_recommendation,
            em_revenue_opportunity=em_recommendation.revenue_gap,
            drg_optimization=drg_optimization,
            drg_revenue_opportunity=drg_optimization.revenue_impact,
            hcc_opportunities=hcc_opportunities,
            hcc_revenue_opportunity=len(hcc_opportunities) * 500.0,  # Estimated HCC value
            total_revenue_opportunity=total_revenue,
            revenue_capture_rate=calculate_revenue_capture_rate(
                em_recommendation.reimbursement,
                em_recommendation.reimbursement + total_revenue
            ),
            confidence=0.85,
            warnings=[],
        )

    def _extract_history(self, clinical_note: str) -> HistoryComponents:
        """Extract history components from clinical note."""
        note_lower = clinical_note.lower()

        hpi_elements = [
            elem for elem, pattern in self.HPI_PATTERNS.items()
            if re.search(pattern, note_lower, re.IGNORECASE)
        ]

        ros_systems = [
            system for system, pattern in self.ROS_SYSTEMS.items()
            if re.search(pattern, note_lower, re.IGNORECASE)
        ]

        pfsh_elements = [
            elem for elem, pattern in self.PFSH_PATTERNS.items()
            if re.search(pattern, note_lower, re.IGNORECASE)
        ]

        return HistoryComponents(
            hpi_elements=hpi_elements,
            ros_systems=ros_systems,
            pfsh_elements=pfsh_elements
        )

    def _extract_exam(self, clinical_note: str) -> ExamComponents:
        """Extract examination components from clinical note."""
        note_lower = clinical_note.lower()

        systems_examined = [
            system for system, pattern in self.EXAM_SYSTEMS.items()
            if re.search(pattern, note_lower, re.IGNORECASE)
        ]

        return ExamComponents(systems_examined=systems_examined)

    def _extract_mdm(
        self,
        clinical_note: str,
        entities: ClinicalEntities
    ) -> MDMComponents:
        """Extract MDM components from clinical note and entities."""
        note_lower = clinical_note.lower()

        # Count diagnoses
        diagnoses_count = len(entities.diagnoses)

        # Data reviewed
        data_patterns = {
            'labs': r'\b(CBC|CMP|BMP|labs|laboratory|blood work)\b',
            'imaging': r'\b(x-ray|CT|MRI|ultrasound|echo|imaging)\b',
            'prior_records': r'\b(reviewed|previous|prior|old records|chart review)\b',
        }
        data_reviewed = [
            dtype for dtype, pattern in data_patterns.items()
            if re.search(pattern, note_lower, re.IGNORECASE)
        ]

        # Risk level
        risk_level = self._assess_risk_level(note_lower)

        return MDMComponents(
            diagnoses_count=diagnoses_count,
            data_reviewed=data_reviewed,
            risk_level=risk_level
        )

    def _assess_risk_level(self, note_text: str) -> str:
        """Assess risk level based on clinical indicators."""
        for indicator in self.RISK_INDICATORS['high']:
            if indicator.lower() in note_text:
                return "high"
        for indicator in self.RISK_INDICATORS['moderate']:
            if indicator.lower() in note_text:
                return "moderate"
        return "low"

    def _calculate_em_code(
        self,
        history: HistoryComponents,
        exam: ExamComponents,
        mdm: MDMComponents,
        setting: str,
        patient_type: str
    ) -> EMCodeRecommendation:
        """Calculate E/M code recommendation."""
        # Get component levels
        history_level = history.get_level()
        exam_level = exam.get_level()
        mdm_level = mdm.get_level()

        # Calculate E/M level
        em_level = calculate_em_level(history_level, exam_level, mdm_level)

        # Get code set
        if setting == "inpatient":
            code_key = f"inpatient_{patient_type}"
        else:
            code_key = f"outpatient_{patient_type}"

        code_set = self.EM_CODES.get(code_key, self.EM_CODES["inpatient_initial"])

        # Get current code
        current = code_set.get(em_level, code_set.get(1))

        # Check for upgrade opportunity
        upgrade = None
        revenue_gap = 0.0
        gaps = []

        if em_level < len(code_set):
            potential = code_set.get(em_level + 1)
            if potential:
                upgrade = potential["code"]
                revenue_gap = potential["reimbursement"] - current["reimbursement"]

                # Identify what's needed for upgrade
                if len(history.hpi_elements) < 4:
                    gaps.append(f"HPI incomplete - {len(history.hpi_elements)}/8 elements")
                if len(history.ros_systems) < 10:
                    gaps.append(f"ROS incomplete - {len(history.ros_systems)}/14 systems")
                if len(exam.systems_examined) < 8:
                    gaps.append(f"Exam limited - {len(exam.systems_examined)} systems")

        return EMCodeRecommendation(
            recommended_code=current["code"],
            confidence=0.85,
            documented_level=f"Level {em_level}",
            reimbursement=current["reimbursement"],
            potential_upgrade_code=upgrade,
            potential_upgrade_reimbursement=code_set.get(em_level + 1, {}).get("reimbursement"),
            documentation_gaps=gaps,
            revenue_gap=revenue_gap,
        )

    def _analyze_drg_opportunities(
        self,
        entities: ClinicalEntities,
        clinical_note: str
    ) -> DRGOptimization:
        """Analyze DRG optimization opportunities."""
        diagnosis_names = [d.name.lower() for d in entities.diagnoses]
        note_lower = clinical_note.lower()

        improvements = []
        current_drg = None
        potential_drg = None
        revenue_impact = 0.0

        # Pneumonia optimization
        if any("pneumonia" in dx for dx in diagnosis_names):
            current_drg = "DRG 193 - Simple Pneumonia"
            if "respiratory failure" in note_lower or "intubat" in note_lower:
                potential_drg = "DRG 177 - Respiratory Infections w/ MCC"
                revenue_impact = 5000.0
            improvements.extend([
                "Document specific organism if identified",
                "Document respiratory failure if present",
                "Specify acute vs chronic respiratory failure",
            ])

        # Heart failure optimization
        elif any("heart failure" in dx for dx in diagnosis_names):
            current_drg = "DRG 292 - Heart Failure w/ CC"
            if any(kw in note_lower for kw in ["acute kidney", "respiratory failure"]):
                potential_drg = "DRG 291 - Heart Failure w/ MCC"
                revenue_impact = 4500.0
            improvements.extend([
                "Document acute vs chronic heart failure",
                "Document ejection fraction percentage",
                "Document acute kidney injury if present",
            ])

        # Sepsis optimization
        elif any("sepsis" in dx for dx in diagnosis_names):
            current_drg = "DRG 872 - Septicemia w/o MCC"
            if "septic shock" in note_lower or "organ dysfunction" in note_lower:
                potential_drg = "DRG 871 - Septicemia w/ MCC"
                revenue_impact = 6000.0
            improvements.extend([
                "Document organ dysfunction",
                "Specify septic shock if vasopressors required",
                "Link infection source to sepsis",
            ])

        return DRGOptimization(
            current_drg=current_drg,
            potential_drg=potential_drg,
            revenue_impact=revenue_impact,
            documentation_improvements=improvements,
        )

    def _analyze_hcc_opportunities(
        self,
        entities: ClinicalEntities
    ) -> List[str]:
        """Analyze HCC risk adjustment opportunities."""
        opportunities = []
        diagnosis_names = [d.name.lower() for d in entities.diagnoses]

        # Check for HCC-eligible conditions that need better documentation
        if any("diabetes" in dx for dx in diagnosis_names):
            if not any("complication" in dx or "nephropathy" in dx for dx in diagnosis_names):
                opportunities.append("Document diabetic complications if present (nephropathy, neuropathy, retinopathy)")

        if any("heart failure" in dx for dx in diagnosis_names):
            if not any("ejection fraction" in dx for dx in diagnosis_names):
                opportunities.append("Document heart failure with ejection fraction (HFrEF vs HFpEF)")

        if any("ckd" in dx or "chronic kidney" in dx for dx in diagnosis_names):
            if not any("stage" in dx for dx in diagnosis_names):
                opportunities.append("Document CKD stage for HCC capture")

        return opportunities

    def _analyze_test_gaps(
        self,
        entities: ClinicalEntities,
        clinical_note: str
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Analyze documented vs recommended tests."""
        tests_documented = []
        tests_missing = []

        # Check labs based on conditions
        diagnosis_names = [d.name.lower() for d in entities.diagnoses]
        note_lower = clinical_note.lower()

        # Documented tests (simple extraction)
        test_patterns = ["cbc", "cmp", "bmp", "x-ray", "ct ", "mri", "echo", "bnp", "troponin"]
        for test in test_patterns:
            if test in note_lower:
                tests_documented.append(test.upper())

        # Missing tests based on condition
        if any("pneumonia" in dx for dx in diagnosis_names):
            if "procalcitonin" not in note_lower:
                tests_missing.append({"test": "Procalcitonin", "cost": 35.0, "priority": "medium"})
            if "blood culture" not in note_lower:
                tests_missing.append({"test": "Blood cultures", "cost": 50.0, "priority": "high"})

        if any("heart failure" in dx for dx in diagnosis_names):
            if "bnp" not in note_lower and "nt-probnp" not in note_lower:
                tests_missing.append({"test": "BNP", "cost": 40.0, "priority": "high"})
            if "echo" not in note_lower:
                tests_missing.append({"test": "Echocardiogram", "cost": 300.0, "priority": "high"})

        return tests_documented, tests_missing


# Convenience function
def analyze_revenue_opportunities(
    clinical_note: str,
    setting: str = "inpatient",
    patient_type: str = "initial"
) -> RevenueOptimizationResult:
    """
    Convenience function to analyze revenue optimization opportunities.

    Args:
        clinical_note: Clinical documentation text
        setting: Clinical setting (inpatient, outpatient)
        patient_type: Patient type (initial, subsequent, new, established)

    Returns:
        RevenueOptimizationResult
    """
    optimizer = RevenueOptimizer()
    return optimizer.analyze(
        clinical_note=clinical_note,
        setting=setting,
        patient_type=patient_type,
    )
