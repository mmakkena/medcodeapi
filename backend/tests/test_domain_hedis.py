"""Tests for the HEDIS Evaluation domain module"""

import pytest
import os
import sys

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from domain.hedis_evaluation import HEDISEvaluator


class TestHEDISEvaluator:
    """Test suite for HEDISEvaluator"""

    @pytest.fixture
    def evaluator(self):
        """Create evaluator instance"""
        return HEDISEvaluator()

    def test_evaluator_initialization(self, evaluator):
        """Test that evaluator initializes correctly"""
        assert evaluator is not None

    def test_evaluate_diabetes_care(self, evaluator):
        """Test HEDIS evaluation for diabetes care measures"""
        result = evaluator.evaluate(
            diagnoses=["E11.9"],
            vitals={"blood_pressure": "128/78"},
            labs={"a1c": "7.2", "ldl": "95"},
            screenings={"retinal_exam": True, "foot_exam": True},
            patient_age=65,
            patient_gender="female",
            note_text="Diabetic patient with A1C 7.2%, BP 128/78, LDL 95."
        )

        assert result is not None

    def test_evaluate_preventive_care(self, evaluator):
        """Test HEDIS evaluation for preventive care measures"""
        result = evaluator.evaluate(
            diagnoses=[],
            vitals={"blood_pressure": "124/82"},
            labs={},
            screenings={"colonoscopy": True},
            patient_age=52,
            patient_gender="male",
            immunizations={"flu": True},
            note_text="Annual wellness visit. Colonoscopy performed 2 years ago."
        )

        assert result is not None

    def test_evaluate_cardiac_care(self, evaluator):
        """Test HEDIS evaluation for cardiac care measures"""
        result = evaluator.evaluate(
            diagnoses=["I21.9"],
            vitals={"blood_pressure": "118/72"},
            labs={"ldl": "68"},
            screenings={},
            patient_age=70,
            patient_gender="male",
            medications={"aspirin": ["81mg daily"], "beta_blocker": ["metoprolol 50mg"]},
            note_text="Post-MI patient on optimal medical therapy."
        )

        assert result is not None

    def test_evaluate_with_icd10_codes(self, evaluator):
        """Test evaluation with explicit ICD-10 codes"""
        result = evaluator.evaluate(
            diagnoses=["E11.9", "I10"],
            vitals={"blood_pressure": "140/90"},
            labs={"a1c": "8.0"},
            screenings={},
            patient_age=60,
            patient_gender="female",
            icd10_codes=["E11.9", "I10"]
        )

        assert result is not None


class TestHEDISMeasures:
    """Test specific HEDIS measures"""

    @pytest.fixture
    def evaluator(self):
        return HEDISEvaluator()

    def test_comprehensive_diabetes_care(self, evaluator):
        """Test CDC - Comprehensive Diabetes Care measure"""
        result = evaluator.evaluate(
            diagnoses=["E11.9"],
            vitals={"blood_pressure": "125/78"},
            labs={"a1c": "6.8", "ldl": "88"},
            screenings={"retinal_exam": True, "foot_exam": True, "nephropathy": True},
            patient_age=55,
            patient_gender="male"
        )

        assert result is not None

    def test_controlling_high_blood_pressure(self, evaluator):
        """Test CBP - Controlling High Blood Pressure measure"""
        result = evaluator.evaluate(
            diagnoses=["I10"],
            vitals={"blood_pressure": "132/84"},
            labs={},
            screenings={},
            patient_age=62,
            patient_gender="female",
            medications={"ace_inhibitor": ["lisinopril 20mg"]}
        )

        assert result is not None

    def test_breast_cancer_screening(self, evaluator):
        """Test BCS - Breast Cancer Screening measure"""
        result = evaluator.evaluate(
            diagnoses=[],
            vitals={},
            labs={},
            screenings={"mammogram": True},
            patient_age=54,
            patient_gender="female"
        )

        assert result is not None

    def test_colorectal_cancer_screening(self, evaluator):
        """Test COL - Colorectal Cancer Screening measure"""
        result = evaluator.evaluate(
            diagnoses=[],
            vitals={},
            labs={},
            screenings={"colonoscopy": True},
            patient_age=55,
            patient_gender="male"
        )

        assert result is not None


class TestHEDISEdgeCases:
    """Test edge cases for HEDIS evaluation"""

    @pytest.fixture
    def evaluator(self):
        return HEDISEvaluator()

    def test_evaluate_young_patient(self, evaluator):
        """Test evaluation for young patient (different measure set)"""
        result = evaluator.evaluate(
            diagnoses=[],
            vitals={},
            labs={},
            screenings={"pap_smear": True, "chlamydia": True},
            patient_age=25,
            patient_gender="female"
        )

        assert result is not None

    def test_evaluate_elderly_patient(self, evaluator):
        """Test evaluation for elderly patient"""
        result = evaluator.evaluate(
            diagnoses=["E11.65", "I10", "N18.3"],
            vitals={"blood_pressure": "135/82"},
            labs={},
            screenings={},
            patient_age=82,
            patient_gender="male",
            immunizations={"flu": True, "pneumonia": True}
        )

        assert result is not None

    def test_evaluate_minimal_data(self, evaluator):
        """Test evaluation with minimal clinical information"""
        result = evaluator.evaluate(
            diagnoses=[],
            vitals={},
            labs={},
            screenings={},
            patient_age=50,
            patient_gender="female"
        )

        assert result is not None

    def test_evaluate_exclusion_criteria(self, evaluator):
        """Test evaluation with exclusion criteria present"""
        result = evaluator.evaluate(
            diagnoses=["C50.919", "Z90.11"],  # Breast cancer, post-mastectomy
            vitals={},
            labs={},
            screenings={},
            patient_age=45,
            patient_gender="female",
            note_text="History of bilateral mastectomy for breast cancer treatment."
        )

        assert result is not None
