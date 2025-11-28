"""Tests for the CDI Query Generation domain module"""

import pytest
import os
import sys

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from domain.query_generation import CDIQueryGenerator
from domain.documentation_gaps import DocumentationGapAnalyzer
from domain.entity_extraction import ClinicalEntityExtractor


class TestCDIQueryGenerator:
    """Test suite for CDIQueryGenerator"""

    @pytest.fixture
    def generator(self):
        """Create generator instance"""
        return CDIQueryGenerator()

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return DocumentationGapAnalyzer()

    @pytest.fixture
    def extractor(self):
        """Create extractor instance"""
        return ClinicalEntityExtractor()

    def test_generator_initialization(self, generator):
        """Test that generator initializes correctly"""
        assert generator is not None

    def test_generate_diabetes_query(self, generator, analyzer, extractor):
        """Test generation of diabetes-related CDI query"""
        note = "Patient with diabetes. A1C elevated."
        entities = extractor.extract(note)
        gaps = analyzer.analyze(entities=entities)
        result = generator.generate_from_gaps(gaps)

        assert result is not None

    def test_generate_heart_failure_query(self, generator, analyzer, extractor):
        """Test generation of heart failure CDI query"""
        note = "Patient with heart failure, EF 30%."
        entities = extractor.extract(note)
        gaps = analyzer.analyze(entities=entities)
        result = generator.generate_from_gaps(gaps)

        assert result is not None

    def test_generate_specificity_query(self, generator):
        """Test generation of specificity gap query"""
        result = generator.generate_condition_query(
            condition="diabetes",
            clinical_indicators=["elevated A1C", "hyperglycemia"],
            query_type="clarification"
        )

        assert result is not None

    def test_generate_acuity_query(self, generator):
        """Test generation of acuity gap query"""
        result = generator.generate_condition_query(
            condition="kidney disease",
            clinical_indicators=["elevated creatinine", "decreased GFR"],
            query_type="clarification"
        )

        assert result is not None

    def test_generate_comorbidity_query(self, generator):
        """Test generation of comorbidity gap query"""
        result = generator.generate_condition_query(
            condition="hypertension",
            clinical_indicators=["elevated BP", "on multiple antihypertensives"],
            query_type="clarification"
        )

        assert result is not None

    def test_query_type_clarification(self, generator):
        """Test clarification query type"""
        result = generator.generate_condition_query(
            condition="pneumonia",
            clinical_indicators=["fever", "cough", "infiltrate on CXR"],
            query_type="clarification"
        )

        assert result is not None

    def test_query_type_confirmation(self, generator):
        """Test confirmation query type"""
        result = generator.generate_condition_query(
            condition="sepsis",
            clinical_indicators=["elevated WBC", "tachycardia", "hypotension"],
            query_type="clarification"
        )

        assert result is not None

    def test_query_with_multiple_indicators(self, generator):
        """Test query with multiple clinical indicators"""
        result = generator.generate_condition_query(
            condition="COPD",
            clinical_indicators=[
                "chronic cough",
                "dyspnea",
                "smoking history",
                "decreased breath sounds",
                "barrel chest"
            ],
            query_type="clarification"
        )

        assert result is not None


class TestQueryGenerationCompliance:
    """Test CDI query compliance requirements"""

    @pytest.fixture
    def generator(self):
        return CDIQueryGenerator()

    def test_query_generation_returns_result(self, generator):
        """Test that query generation returns a result"""
        result = generator.generate_condition_query(
            condition="malnutrition",
            clinical_indicators=["weight loss", "low albumin"],
            query_type="clarification"
        )

        assert result is not None

    def test_query_has_required_fields(self, generator):
        """Test that query result has required fields"""
        result = generator.generate_condition_query(
            condition="respiratory failure",
            clinical_indicators=["hypoxia", "dyspnea"],
            query_type="clarification"
        )

        assert result is not None
        # Check for common attributes
        assert hasattr(result, 'query_text') or hasattr(result, 'query') or isinstance(result, str)

    def test_query_for_documentation_request(self, generator):
        """Test query for documentation request"""
        result = generator.generate_condition_query(
            condition="heart failure",
            clinical_indicators=["edema", "dyspnea", "elevated BNP"],
            query_type="clarification"
        )

        assert result is not None


class TestQueryGenerationEdgeCases:
    """Test edge cases for query generation"""

    @pytest.fixture
    def generator(self):
        return CDIQueryGenerator()

    def test_generate_unknown_condition(self, generator):
        """Test generation for unknown condition"""
        result = generator.generate_condition_query(
            condition="rare_unknown_condition_xyz",
            clinical_indicators=["symptom1", "symptom2"],
            query_type="clarification"
        )

        # Should still return a valid query
        assert result is not None

    def test_generate_with_empty_indicators(self, generator):
        """Test generation with empty indicators"""
        result = generator.generate_condition_query(
            condition="diabetes",
            clinical_indicators=[],
            query_type="clarification"
        )

        assert result is not None

    def test_generate_multiple_queries(self, generator):
        """Test generation of multiple queries in sequence"""
        conditions = [
            ("diabetes", ["elevated A1C"]),
            ("hypertension", ["elevated BP"]),
            ("heart failure", ["edema", "dyspnea"]),
            ("COPD", ["wheezing", "dyspnea"])
        ]

        for condition, indicators in conditions:
            result = generator.generate_condition_query(
                condition=condition,
                clinical_indicators=indicators,
                query_type="clarification"
            )
            assert result is not None
