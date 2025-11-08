"""Tests for ICD-10 enhanced models"""

import pytest
import uuid
from datetime import date, datetime
from sqlalchemy.exc import IntegrityError

from app.models.icd10_code import ICD10Code
from app.models.icd10_ai_facet import ICD10AIFacet
from app.models.code_mapping import CodeMapping
from app.models.icd10_relation import ICD10Relation
from app.models.icd10_synonym import ICD10Synonym


class TestICD10Code:
    """Tests for enhanced ICD10Code model"""

    def test_create_basic_icd10_code(self, db_session):
        """Test creating a basic ICD-10 code"""
        code = ICD10Code(
            code="E11.9",
            code_system="ICD10-CM",
            short_desc="Type 2 diabetes mellitus without complications",
            long_desc="Type 2 diabetes mellitus without complications - detailed description",
            chapter="Endocrine, nutritional and metabolic diseases",
            category="Diabetes mellitus",
            is_active=True,
            version_year=2024
        )

        db_session.add(code)
        db_session.commit()
        db_session.refresh(code)

        assert code.id is not None
        assert code.code == "E11.9"
        assert code.code_system == "ICD10-CM"
        assert code.short_desc == "Type 2 diabetes mellitus without complications"
        assert code.is_active is True
        assert code.version_year == 2024

    def test_icd10_code_with_embedding(self, db_session):
        """Test ICD-10 code with vector embedding"""
        # Create a mock 768-dim embedding (in SQLite it stores as JSON)
        embedding = [0.1] * 768  # Mock embedding vector

        code = ICD10Code(
            code="I10",
            code_system="ICD10-CM",
            short_desc="Essential (primary) hypertension",
            embedding=embedding
        )

        db_session.add(code)
        db_session.commit()
        db_session.refresh(code)

        assert code.embedding is not None
        # In SQLite, embedding is stored as JSON string
        assert len(code.embedding) == 768

    def test_unique_code_system_constraint(self, db_session):
        """Test that code + code_system must be unique"""
        code1 = ICD10Code(
            code="E11.9",
            code_system="ICD10-CM",
            short_desc="Type 2 diabetes"
        )
        db_session.add(code1)
        db_session.commit()

        # Try to add same code + code_system combination
        code2 = ICD10Code(
            code="E11.9",
            code_system="ICD10-CM",
            short_desc="Duplicate"
        )
        db_session.add(code2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_same_code_different_systems(self, db_session):
        """Test that same code can exist in different code systems"""
        code1 = ICD10Code(
            code="A00",
            code_system="ICD10",
            short_desc="Cholera (ICD10)"
        )
        code2 = ICD10Code(
            code="A00",
            code_system="ICD10-CM",
            short_desc="Cholera (ICD10-CM)"
        )

        db_session.add(code1)
        db_session.add(code2)
        db_session.commit()

        # Should not raise error - different code systems
        codes = db_session.query(ICD10Code).filter_by(code="A00").all()
        assert len(codes) == 2

    def test_effective_and_expiry_dates(self, db_session):
        """Test effective and expiry date fields"""
        code = ICD10Code(
            code="Z99.0",
            code_system="ICD10-CM",
            short_desc="Dependence on aspirator",
            effective_date=date(2024, 1, 1),
            expiry_date=date(2025, 12, 31),
            version_year=2024
        )

        db_session.add(code)
        db_session.commit()
        db_session.refresh(code)

        assert code.effective_date == date(2024, 1, 1)
        assert code.expiry_date == date(2025, 12, 31)

    def test_backward_compatibility_description(self, db_session):
        """Test legacy description field still works"""
        code = ICD10Code(
            code="J44.0",
            code_system="ICD10-CM",
            description="Legacy description",  # Old field
            short_desc="COPD with acute lower respiratory infection"  # New field
        )

        db_session.add(code)
        db_session.commit()
        db_session.refresh(code)

        assert code.description == "Legacy description"
        assert code.short_desc == "COPD with acute lower respiratory infection"


class TestICD10AIFacet:
    """Tests for ICD10AIFacet model"""

    def test_create_ai_facet(self, db_session):
        """Test creating AI facets for a code"""
        facet = ICD10AIFacet(
            code="E11.9",
            code_system="ICD10-CM",
            concept_type="diagnosis",
            body_system="endocrine",
            chronicity="chronic",
            severity="moderate",
            risk_flag=True,
            extra={"complication_prone": True, "requires_monitoring": True}
        )

        db_session.add(facet)
        db_session.commit()
        db_session.refresh(facet)

        assert facet.code == "E11.9"
        assert facet.concept_type == "diagnosis"
        assert facet.body_system == "endocrine"
        assert facet.chronicity == "chronic"
        assert facet.risk_flag is True
        assert facet.extra["complication_prone"] is True

    def test_facet_with_all_attributes(self, db_session):
        """Test facet with all possible attributes"""
        facet = ICD10AIFacet(
            code="S72.001A",
            code_system="ICD10-CM",
            concept_type="injury",
            body_system="musculoskeletal",
            acuity="acute",
            severity="severe",
            chronicity="acute",
            laterality="right",
            onset_context="traumatic",
            age_band="adult",
            sex_specific="both",
            risk_flag=True
        )

        db_session.add(facet)
        db_session.commit()
        db_session.refresh(facet)

        assert facet.laterality == "right"
        assert facet.onset_context == "traumatic"
        assert facet.age_band == "adult"
        assert facet.acuity == "acute"

    def test_facet_primary_key_constraint(self, db_session):
        """Test that code + code_system is primary key"""
        facet1 = ICD10AIFacet(
            code="E11.9",
            code_system="ICD10-CM",
            body_system="endocrine"
        )
        db_session.add(facet1)
        db_session.commit()

        # Try to add another facet with same code + code_system
        facet2 = ICD10AIFacet(
            code="E11.9",
            code_system="ICD10-CM",
            body_system="metabolic"  # Different value
        )
        db_session.add(facet2)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestCodeMapping:
    """Tests for CodeMapping model"""

    def test_create_code_mapping(self, db_session):
        """Test creating a code mapping"""
        mapping = CodeMapping(
            from_system="ICD10-CM",
            from_code="E11.9",
            to_system="SNOMED",
            to_code="44054006",
            map_type="exact",
            confidence=0.95,
            source_name="CMS",
            source_version="2024"
        )

        db_session.add(mapping)
        db_session.commit()
        db_session.refresh(mapping)

        assert mapping.id is not None
        assert mapping.from_system == "ICD10-CM"
        assert mapping.from_code == "E11.9"
        assert mapping.to_system == "SNOMED"
        assert mapping.to_code == "44054006"
        assert mapping.map_type == "exact"
        assert float(mapping.confidence) == 0.95  # Numeric returns Decimal

    def test_multiple_mappings_same_code(self, db_session):
        """Test that one code can have multiple mappings"""
        mapping1 = CodeMapping(
            from_system="ICD10-CM",
            from_code="E11.9",
            to_system="SNOMED",
            to_code="44054006",
            map_type="exact"
        )
        mapping2 = CodeMapping(
            from_system="ICD10-CM",
            from_code="E11.9",
            to_system="LOINC",
            to_code="1234-5",
            map_type="related"
        )

        db_session.add_all([mapping1, mapping2])
        db_session.commit()

        mappings = db_session.query(CodeMapping).filter_by(from_code="E11.9").all()
        assert len(mappings) == 2

    def test_mapping_with_review_info(self, db_session):
        """Test mapping with review information"""
        mapping = CodeMapping(
            from_system="ICD10-CM",
            from_code="I10",
            to_system="CPT",
            to_code="99201",
            map_type="billing",
            confidence=0.70,
            reviewed_by="Dr. Smith",
            review_note="Verified for primary care visits",
            effective_date=date(2024, 1, 1)
        )

        db_session.add(mapping)
        db_session.commit()
        db_session.refresh(mapping)

        assert mapping.reviewed_by == "Dr. Smith"
        assert mapping.review_note == "Verified for primary care visits"
        assert mapping.effective_date == date(2024, 1, 1)


class TestICD10Relation:
    """Tests for ICD10Relation model"""

    def test_create_parent_child_relation(self, db_session):
        """Test creating a parent-child relationship"""
        relation = ICD10Relation(
            code="E11",
            related_code="E11.9",
            relation_type="parent"
        )

        db_session.add(relation)
        db_session.commit()
        db_session.refresh(relation)

        assert relation.code == "E11"
        assert relation.related_code == "E11.9"
        assert relation.relation_type == "parent"

    def test_bidirectional_relations(self, db_session):
        """Test creating bidirectional relationships"""
        rel1 = ICD10Relation(
            code="E11",
            related_code="E11.9",
            relation_type="parent"
        )
        rel2 = ICD10Relation(
            code="E11.9",
            related_code="E11",
            relation_type="child"
        )

        db_session.add_all([rel1, rel2])
        db_session.commit()

        parent_rels = db_session.query(ICD10Relation).filter_by(
            relation_type="parent"
        ).all()
        assert len(parent_rels) == 1

    def test_various_relation_types(self, db_session):
        """Test different types of relationships"""
        relations = [
            ICD10Relation(code="E11.9", related_code="E11.65", relation_type="see-also"),
            ICD10Relation(code="E11.9", related_code="E10", relation_type="excludes"),
            ICD10Relation(code="O24.4", related_code="E11.9", relation_type="complication-of"),
        ]

        db_session.add_all(relations)
        db_session.commit()

        all_rels = db_session.query(ICD10Relation).filter_by(code="E11.9").all()
        assert len(all_rels) == 2  # see-also and excludes


class TestICD10Synonym:
    """Tests for ICD10Synonym model"""

    def test_create_synonym(self, db_session):
        """Test creating a synonym"""
        synonym = ICD10Synonym(
            code="E11.9",
            synonym="diabetes type 2 without complications"
        )

        db_session.add(synonym)
        db_session.commit()

        result = db_session.query(ICD10Synonym).filter_by(code="E11.9").first()
        assert result.synonym == "diabetes type 2 without complications"

    def test_multiple_synonyms_same_code(self, db_session):
        """Test that one code can have multiple synonyms"""
        synonyms = [
            ICD10Synonym(code="E11.9", synonym="diabetes type 2"),
            ICD10Synonym(code="E11.9", synonym="type 2 DM"),
            ICD10Synonym(code="E11.9", synonym="adult-onset diabetes"),
            ICD10Synonym(code="E11.9", synonym="non-insulin dependent diabetes"),
        ]

        db_session.add_all(synonyms)
        db_session.commit()

        results = db_session.query(ICD10Synonym).filter_by(code="E11.9").all()
        assert len(results) == 4

    def test_synonym_composite_primary_key(self, db_session):
        """Test that (code, synonym) is the primary key"""
        syn1 = ICD10Synonym(code="E11.9", synonym="diabetes")
        db_session.add(syn1)
        db_session.commit()

        # Try to add exact same code + synonym
        syn2 = ICD10Synonym(code="E11.9", synonym="diabetes")
        db_session.add(syn2)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestIntegratedScenario:
    """Test integrated scenarios with multiple related models"""

    def test_full_code_with_facets_and_mappings(self, db_session):
        """Test creating a complete code entry with all related data"""
        # Create the main code
        code = ICD10Code(
            code="E11.9",
            code_system="ICD10-CM",
            short_desc="Type 2 diabetes mellitus without complications",
            long_desc="Type 2 diabetes mellitus without complications - full description",
            chapter="Endocrine, nutritional and metabolic diseases",
            category="Diabetes mellitus",
            is_active=True,
            version_year=2024,
            embedding=[0.1] * 768  # Mock embedding
        )
        db_session.add(code)
        db_session.commit()

        # Add AI facets
        facet = ICD10AIFacet(
            code="E11.9",
            code_system="ICD10-CM",
            concept_type="diagnosis",
            body_system="endocrine",
            chronicity="chronic",
            risk_flag=True
        )
        db_session.add(facet)

        # Add mappings
        mappings = [
            CodeMapping(
                from_system="ICD10-CM", from_code="E11.9",
                to_system="SNOMED", to_code="44054006", map_type="exact", confidence=0.95
            ),
            CodeMapping(
                from_system="ICD10-CM", from_code="E11.9",
                to_system="LOINC", to_code="1234-5", map_type="related", confidence=0.80
            ),
        ]
        db_session.add_all(mappings)

        # Add synonyms
        synonyms = [
            ICD10Synonym(code="E11.9", synonym="type 2 diabetes"),
            ICD10Synonym(code="E11.9", synonym="NIDDM"),
        ]
        db_session.add_all(synonyms)

        # Add relations
        relations = [
            ICD10Relation(code="E11", related_code="E11.9", relation_type="parent"),
            ICD10Relation(code="E11.9", related_code="E11", relation_type="child"),
        ]
        db_session.add_all(relations)

        db_session.commit()

        # Verify everything was created
        assert db_session.query(ICD10Code).filter_by(code="E11.9").count() == 1
        assert db_session.query(ICD10AIFacet).filter_by(code="E11.9").count() == 1
        assert db_session.query(CodeMapping).filter_by(from_code="E11.9").count() == 2
        assert db_session.query(ICD10Synonym).filter_by(code="E11.9").count() == 2
        assert db_session.query(ICD10Relation).filter_by(code="E11.9").count() == 1
