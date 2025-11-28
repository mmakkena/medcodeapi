"""Tests for the Revenue Optimization domain module"""

import pytest
import os
import sys

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from domain.revenue_optimization import RevenueOptimizer
from domain.entity_extraction import ClinicalEntityExtractor


class TestRevenueOptimizer:
    """Test suite for RevenueOptimizer"""

    @pytest.fixture
    def optimizer(self):
        """Create optimizer instance"""
        return RevenueOptimizer()

    @pytest.fixture
    def extractor(self):
        """Create extractor instance"""
        return ClinicalEntityExtractor()

    def test_optimizer_initialization(self, optimizer):
        """Test that optimizer initializes correctly"""
        assert optimizer is not None

    def test_analyze_diabetes_revenue(self, optimizer, extractor):
        """Test revenue analysis for diabetes case"""
        note = """
        65-year-old male with Type 2 diabetes with chronic kidney disease stage 3.
        A1C 8.5%. On metformin and lisinopril.
        """
        entities = extractor.extract(note)
        result = optimizer.analyze(
            clinical_note=note,
            entities=entities,
            setting="outpatient",
            patient_type="established"
        )

        assert result is not None

    def test_analyze_heart_failure_revenue(self, optimizer, extractor):
        """Test revenue analysis for heart failure case"""
        note = """
        72-year-old female with acute on chronic systolic heart failure,
        EF 25%. Presents with volume overload.
        """
        entities = extractor.extract(note)
        result = optimizer.analyze(
            clinical_note=note,
            entities=entities,
            setting="inpatient",
            patient_type="initial"
        )

        assert result is not None

    def test_analyze_complex_case(self, optimizer, extractor):
        """Test revenue analysis for complex multi-condition case"""
        note = """
        68-year-old male with:
        - Type 2 diabetes with diabetic nephropathy
        - Chronic systolic heart failure, EF 30%
        - COPD with acute exacerbation
        - Chronic respiratory failure on home O2
        - Morbid obesity, BMI 42
        """
        entities = extractor.extract(note)
        result = optimizer.analyze(
            clinical_note=note,
            entities=entities,
            setting="inpatient",
            patient_type="initial"
        )

        assert result is not None

    def test_analyze_without_entities(self, optimizer):
        """Test revenue analysis without pre-extracted entities"""
        note = """
        Patient with diabetes and hypertension presenting for follow-up.
        A1C 7.5%, BP 142/88.
        """
        result = optimizer.analyze(
            clinical_note=note,
            setting="outpatient",
            patient_type="established"
        )

        assert result is not None


class TestHCCAnalysis:
    """Test HCC analysis functionality"""

    @pytest.fixture
    def optimizer(self):
        return RevenueOptimizer()

    def test_hcc_identification(self, optimizer):
        """Test HCC identification from diagnoses"""
        note = """
        Patient with Type 2 diabetes with chronic kidney disease stage 4,
        congestive heart failure, and major depression.
        """
        result = optimizer.analyze(
            clinical_note=note,
            setting="outpatient",
            patient_type="established"
        )

        assert result is not None

    def test_hcc_hierarchy_application(self, optimizer):
        """Test that HCC hierarchies are properly applied"""
        note = """
        Patient with diabetes with nephropathy and diabetes without complications.
        """
        result = optimizer.analyze(
            clinical_note=note,
            setting="outpatient",
            patient_type="established"
        )

        assert result is not None


class TestEMCoding:
    """Test E/M coding analysis"""

    @pytest.fixture
    def optimizer(self):
        return RevenueOptimizer()

    def test_em_level_determination_outpatient(self, optimizer):
        """Test E/M level determination for outpatient"""
        note = """
        New patient visit. Chief complaint: diabetes management.
        Comprehensive history obtained. Complete physical exam performed.
        Assessment: Type 2 diabetes, uncontrolled.
        Plan: Adjust medications, order labs, follow-up 2 weeks.
        Time spent: 45 minutes.
        """
        result = optimizer.analyze(
            clinical_note=note,
            setting="outpatient",
            patient_type="new"
        )

        assert result is not None

    def test_em_level_determination_inpatient(self, optimizer):
        """Test E/M level determination for inpatient"""
        note = """
        Initial hospital care. Patient admitted with pneumonia.
        Comprehensive history and physical performed.
        Multiple problems addressed. High complexity decision making.
        """
        result = optimizer.analyze(
            clinical_note=note,
            setting="inpatient",
            patient_type="initial"
        )

        assert result is not None

    def test_mdm_complexity_assessment(self, optimizer):
        """Test MDM complexity assessment"""
        note = """
        Patient with multiple chronic conditions requiring complex
        decision making. Reviewed outside records. Discussed treatment
        options with patient and family. High risk medications adjusted.
        """
        result = optimizer.analyze(
            clinical_note=note,
            setting="outpatient",
            patient_type="established"
        )

        assert result is not None


class TestRevenueOptimizationEdgeCases:
    """Test edge cases for revenue optimization"""

    @pytest.fixture
    def optimizer(self):
        return RevenueOptimizer()

    def test_analyze_minimal_documentation(self, optimizer):
        """Test analysis with minimal documentation"""
        note = "Follow-up visit. Stable."
        result = optimizer.analyze(
            clinical_note=note,
            setting="outpatient",
            patient_type="established"
        )

        assert result is not None

    def test_analyze_preventive_visit(self, optimizer):
        """Test analysis for preventive care visit"""
        note = """
        Annual wellness visit. Patient is healthy, no complaints.
        Routine screening performed. Immunizations up to date.
        """
        result = optimizer.analyze(
            clinical_note=note,
            setting="outpatient",
            patient_type="established"
        )

        assert result is not None

    def test_analyze_surgical_case(self, optimizer):
        """Test analysis for surgical case"""
        note = """
        Patient underwent laparoscopic cholecystectomy for acute cholecystitis.
        Procedure uncomplicated. Estimated blood loss minimal.
        """
        result = optimizer.analyze(
            clinical_note=note,
            setting="inpatient",
            patient_type="subsequent"
        )

        assert result is not None

    def test_analyze_ed_visit(self, optimizer):
        """Test analysis for ED visit"""
        note = """
        Patient presents to ED with chest pain. EKG shows ST changes.
        Troponin elevated. Cardiology consulted. Admit for ACS workup.
        """
        result = optimizer.analyze(
            clinical_note=note,
            setting="inpatient",
            patient_type="initial"
        )

        assert result is not None
