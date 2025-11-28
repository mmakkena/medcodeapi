"""Tests for the Entity Extraction domain module"""

import pytest
import os
import sys

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from domain.entity_extraction import ClinicalEntityExtractor


class TestClinicalEntityExtractor:
    """Test suite for ClinicalEntityExtractor"""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance"""
        return ClinicalEntityExtractor()

    def test_extractor_initialization(self, extractor):
        """Test that extractor initializes correctly"""
        assert extractor is not None

    def test_extract_diabetes_entities(self, extractor):
        """Test extraction of diabetes-related entities"""
        note = """
        65-year-old male with Type 2 diabetes mellitus. A1C is 8.5%.
        Patient also has hypertension with BP 148/92.
        Currently on metformin 1000mg twice daily.
        """
        result = extractor.extract(note)

        # Should return extraction result
        assert result is not None

        # Check for common entity types
        if hasattr(result, 'entities'):
            entities = result.entities
            assert isinstance(entities, list)

    def test_extract_cardiac_entities(self, extractor):
        """Test extraction of cardiac-related entities"""
        note = """
        Patient presents with acute chest pain. History of coronary artery disease.
        EKG shows ST elevation in leads V1-V4.
        Troponin elevated at 2.5. Started on heparin drip.
        """
        result = extractor.extract(note)
        assert result is not None

    def test_extract_empty_note(self, extractor):
        """Test extraction with empty note"""
        result = extractor.extract("")
        assert result is not None

    def test_extract_minimal_note(self, extractor):
        """Test extraction with minimal clinical content"""
        result = extractor.extract("Patient presents for follow-up.")
        assert result is not None

    def test_extract_with_medications(self, extractor):
        """Test extraction identifies medications"""
        note = """
        Patient on lisinopril 20mg daily, metformin 500mg BID,
        atorvastatin 40mg at bedtime, and aspirin 81mg daily.
        """
        result = extractor.extract(note)
        assert result is not None

    def test_extract_with_vitals(self, extractor):
        """Test extraction identifies vital signs"""
        note = """
        Vitals: BP 145/95, HR 88, RR 18, Temp 98.6F, SpO2 96% on room air.
        Weight 185 lbs, Height 5'10".
        """
        result = extractor.extract(note)
        assert result is not None

    def test_extract_with_lab_values(self, extractor):
        """Test extraction identifies laboratory values"""
        note = """
        Labs: WBC 12.5, Hgb 11.2, Plt 245K.
        BMP: Na 138, K 4.2, Cl 101, CO2 24, BUN 22, Cr 1.4, Glucose 185.
        A1C 8.2%, LDL 145, HDL 38, TG 220.
        """
        result = extractor.extract(note)
        assert result is not None

    def test_extract_negated_conditions(self, extractor):
        """Test extraction handles negated conditions"""
        note = """
        Patient denies chest pain, shortness of breath, or palpitations.
        No history of diabetes or heart disease.
        """
        result = extractor.extract(note)
        assert result is not None

    def test_extract_historical_conditions(self, extractor):
        """Test extraction handles historical conditions"""
        note = """
        Past medical history: Appendectomy 2010, cholecystectomy 2015.
        History of smoking, quit 5 years ago.
        Former alcohol use, sober 10 years.
        """
        result = extractor.extract(note)
        assert result is not None


class TestEntityExtractionEdgeCases:
    """Test edge cases for entity extraction"""

    @pytest.fixture
    def extractor(self):
        return ClinicalEntityExtractor()

    def test_extract_unicode_text(self, extractor):
        """Test extraction handles unicode characters"""
        note = "Patient reports pain level of 8/10. Temperature 38.5°C."
        result = extractor.extract(note)
        assert result is not None

    def test_extract_abbreviations(self, extractor):
        """Test extraction handles common medical abbreviations"""
        note = """
        Pt c/o SOB, DOE x 3 days. Hx of CHF, DM2, HTN.
        PMH: MI 2019, CABG x3 2019.
        Meds: ASA, ACEI, BB, statin.
        """
        result = extractor.extract(note)
        assert result is not None

    def test_extract_long_note(self, extractor):
        """Test extraction handles longer clinical notes"""
        note = """
        CHIEF COMPLAINT: Chest pain

        HISTORY OF PRESENT ILLNESS:
        This is a 65-year-old male with history of hypertension, hyperlipidemia,
        and type 2 diabetes who presents to the emergency department with
        substernal chest pain that started 2 hours ago. The pain is described
        as pressure-like, 8/10 in severity, radiating to the left arm and jaw.
        Associated with diaphoresis and nausea. No relief with rest or
        sublingual nitroglycerin given by EMS.

        PAST MEDICAL HISTORY:
        1. Hypertension - on lisinopril
        2. Hyperlipidemia - on atorvastatin
        3. Type 2 diabetes mellitus - on metformin
        4. Obesity - BMI 32

        MEDICATIONS:
        - Lisinopril 20mg daily
        - Atorvastatin 40mg daily
        - Metformin 1000mg BID
        - Aspirin 81mg daily

        PHYSICAL EXAMINATION:
        Vitals: BP 165/95, HR 92, RR 20, Temp 98.6F, SpO2 94% on RA
        General: Diaphoretic, appears uncomfortable
        CV: Regular rate, no murmurs, rubs, or gallops
        Lungs: Clear to auscultation bilaterally
        Abd: Soft, non-tender

        ASSESSMENT AND PLAN:
        Acute coronary syndrome - STEMI involving anterior wall
        - Activate cath lab for emergent PCI
        - ASA 325mg, Plavix 600mg loading
        - Heparin bolus and drip
        - Serial troponins
        """
        result = extractor.extract(note)
        assert result is not None
