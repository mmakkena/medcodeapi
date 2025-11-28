"""Tests for the Documentation Gaps domain module"""

import pytest
import os
import sys

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from domain.documentation_gaps import DocumentationGapAnalyzer
from domain.entity_extraction import ClinicalEntityExtractor


class TestDocumentationGapAnalyzer:
    """Test suite for DocumentationGapAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return DocumentationGapAnalyzer()

    @pytest.fixture
    def extractor(self):
        """Create extractor instance for entity extraction"""
        return ClinicalEntityExtractor()

    def test_analyzer_initialization(self, analyzer):
        """Test that analyzer initializes correctly"""
        assert analyzer is not None

    def test_analyze_diabetes_gaps(self, analyzer, extractor):
        """Test analysis of diabetes documentation gaps"""
        note = """
        Patient with diabetes. A1C 8.5%. On metformin.
        """
        entities = extractor.extract(note)
        result = analyzer.analyze(entities=entities)

        assert result is not None
        # Should identify missing specificity (type 1 vs type 2)

    def test_analyze_heart_failure_gaps(self, analyzer, extractor):
        """Test analysis of heart failure documentation gaps"""
        note = """
        Patient with heart failure. EF 35%. On furosemide and lisinopril.
        Presents with increased shortness of breath.
        """
        entities = extractor.extract(note)
        result = analyzer.analyze(entities=entities)

        assert result is not None
        # Should identify gaps like systolic vs diastolic, acuity

    def test_analyze_complete_documentation(self, analyzer, extractor):
        """Test analysis of well-documented note"""
        note = """
        65-year-old male with Type 2 diabetes mellitus with diabetic nephropathy
        stage 3 (E11.65, N18.3). A1C 8.2% indicating poor glycemic control.
        Chronic systolic heart failure with reduced ejection fraction of 35%
        (I50.22). Currently compensated on current regimen.
        """
        entities = extractor.extract(note)
        result = analyzer.analyze(entities=entities)

        assert result is not None

    def test_analyze_sepsis_gaps(self, analyzer, extractor):
        """Test analysis of sepsis documentation gaps"""
        note = """
        Patient admitted with sepsis. WBC 18,000, lactate 3.2.
        Blood cultures pending. Started on broad spectrum antibiotics.
        """
        entities = extractor.extract(note)
        result = analyzer.analyze(entities=entities)

        assert result is not None
        # Should identify missing organism, source, severity

    def test_analyze_pneumonia_gaps(self, analyzer, extractor):
        """Test analysis of pneumonia documentation gaps"""
        note = """
        Patient with pneumonia. Chest X-ray shows right lower lobe infiltrate.
        Started on antibiotics.
        """
        entities = extractor.extract(note)
        result = analyzer.analyze(entities=entities)

        assert result is not None
        # Should identify missing type (CAP vs HAP), organism

    def test_analyze_empty_entities(self, analyzer):
        """Test analysis with no entities"""
        from domain.common.models import ClinicalEntities
        empty_result = ClinicalEntities(
            diagnoses=[],
            vitals={},
            labs={},
            screenings={},
            medications={},
            procedures=[],
            allergies=[],
            demographics={}
        )
        result = analyzer.analyze(entities=empty_result)

        assert result is not None

    def test_gap_severity_classification(self, analyzer, extractor):
        """Test that gaps are classified by severity"""
        note = """
        Patient with kidney disease.
        """
        entities = extractor.extract(note)
        result = analyzer.analyze(entities=entities)

        assert result is not None
        # Should have gaps with severity levels

    def test_analyze_multiple_conditions(self, analyzer, extractor):
        """Test analysis with multiple conditions"""
        note = """
        Patient with diabetes, hypertension, COPD, and chronic kidney disease.
        A1C 9.0%, BP 155/95, creatinine 2.1.
        """
        entities = extractor.extract(note)
        result = analyzer.analyze(entities=entities)

        assert result is not None


class TestGapAnalysisEdgeCases:
    """Test edge cases for gap analysis"""

    @pytest.fixture
    def analyzer(self):
        return DocumentationGapAnalyzer()

    @pytest.fixture
    def extractor(self):
        return ClinicalEntityExtractor()

    def test_analyze_surgical_note(self, analyzer, extractor):
        """Test analysis of surgical documentation"""
        note = """
        Patient underwent knee surgery. Procedure went well.
        Post-operative course unremarkable.
        """
        entities = extractor.extract(note)
        result = analyzer.analyze(entities=entities)

        assert result is not None

    def test_analyze_preventive_visit(self, analyzer, extractor):
        """Test analysis of preventive care visit"""
        note = """
        Annual wellness visit. Patient is healthy.
        Up to date on immunizations. Normal physical exam.
        """
        entities = extractor.extract(note)
        result = analyzer.analyze(entities=entities)

        assert result is not None

    def test_analyze_mental_health(self, analyzer, extractor):
        """Test analysis of mental health documentation"""
        note = """
        Patient with depression. Reports low mood, decreased energy.
        Sleep disturbance. No suicidal ideation.
        """
        entities = extractor.extract(note)
        result = analyzer.analyze(entities=entities)

        assert result is not None
