"""
Comprehensive tests for procedure code (CPT/HCPCS) search endpoints.

Tests cover:
- Basic keyword and code search
- Semantic search with embeddings
- Hybrid search with different weights
- Faceted search
- Filtering by code system and year
- Edge cases and error handling
"""

import pytest
from datetime import datetime, date
from app.models.procedure_code import ProcedureCode
from app.models.procedure_code_facet import ProcedureCodeFacet
from app.models.api_key import APIKey
from app.models.user import User
from app.utils.security import hash_password, generate_api_key, hash_api_key, get_api_key_prefix


@pytest.fixture
def test_user(db_session):
    """Create a test user for API authentication"""
    hashed_password = hash_password("testpassword123")
    user = User(
        email="test@example.com",
        password_hash=hashed_password,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_api_key(db_session, test_user):
    """Create a test API key"""
    # Generate API key
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    key_prefix = get_api_key_prefix(api_key)

    # Create API key record
    api_key_obj = APIKey(
        user_id=test_user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name="Test API Key",
        is_active=True
    )
    db_session.add(api_key_obj)
    db_session.commit()
    db_session.refresh(api_key_obj)

    # Store the plain key for use in tests
    api_key_obj.key = api_key
    return api_key_obj


@pytest.fixture
def sample_cpt_codes(db_session):
    """Create sample CPT codes for testing"""
    codes = [
        ProcedureCode(
            code="99213",
            code_system="CPT",
            paraphrased_desc="Office visit for established patient, 20 minute typical time, medical decision making level 2",
            short_desc="Office visit, established patient, 20 min",
            category="E/M",
            version_year=2025,
            is_active=True,
            effective_date=date(2025, 1, 1),
            license_status="free",
            modifier_51_exempt=False,
            embedding=[0.1] * 768  # Mock embedding vector
        ),
        ProcedureCode(
            code="99214",
            code_system="CPT",
            paraphrased_desc="Office visit for established patient, 30 minute typical time, medical decision making level 3",
            short_desc="Office visit, established patient, 30 min",
            category="E/M",
            version_year=2025,
            is_active=True,
            effective_date=date(2025, 1, 1),
            license_status="free",
            modifier_51_exempt=False,
            embedding=[0.15] * 768
        ),
        ProcedureCode(
            code="29870",
            code_system="CPT",
            paraphrased_desc="Knee arthroscopy, diagnostic with or without synovial biopsy",
            short_desc="Knee arthroscopy, diagnostic",
            category="Surgery",
            version_year=2025,
            is_active=True,
            effective_date=date(2025, 1, 1),
            license_status="free",
            modifier_51_exempt=False,
            embedding=[0.2] * 768
        ),
        ProcedureCode(
            code="29881",
            code_system="CPT",
            paraphrased_desc="Knee arthroscopy with meniscectomy (removal of torn cartilage)",
            short_desc="Knee arthroscopy, meniscectomy",
            category="Surgery",
            version_year=2025,
            is_active=True,
            effective_date=date(2025, 1, 1),
            license_status="free",
            modifier_51_exempt=False,
            embedding=[0.22] * 768
        ),
        ProcedureCode(
            code="E0250",
            code_system="HCPCS",
            paraphrased_desc="Hospital bed, fixed height, with any type side rails, with mattress",
            short_desc="Hospital bed, fixed height",
            category="Medical Equipment",
            version_year=2025,
            is_active=True,
            effective_date=date(2025, 1, 1),
            license_status="free",
            modifier_51_exempt=False,
            embedding=[0.3] * 768
        ),
    ]

    for code in codes:
        db_session.add(code)

    db_session.commit()

    # Refresh to get IDs
    for code in codes:
        db_session.refresh(code)

    return codes


@pytest.fixture
def sample_facets(db_session, sample_cpt_codes):
    """Create sample facets for procedure codes"""
    # Add facets for the knee arthroscopy code
    knee_code = next(c for c in sample_cpt_codes if c.code == "29870")

    facet = ProcedureCodeFacet(
        code=knee_code.code,
        code_system=knee_code.code_system,
        body_region="lower_extremity",
        body_system="musculoskeletal",
        procedure_category="surgical",
        anesthesia_type="general",
        service_location="inpatient",
        complexity_level="moderate"
    )
    db_session.add(facet)
    db_session.commit()

    return [facet]


class TestBasicProcedureSearch:
    """Tests for basic procedure code search functionality"""

    def test_search_by_exact_code(self, client, test_api_key, sample_cpt_codes):
        """Test searching by exact CPT code"""
        response = client.get(
            "/api/v1/procedure/search",
            params={"query": "99213", "limit": 10},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["code"] == "99213"
        assert data[0]["code_system"] == "CPT"

    def test_search_by_partial_code(self, client, test_api_key, sample_cpt_codes):
        """Test searching by partial code match"""
        response = client.get(
            "/api/v1/procedure/search",
            params={"query": "992", "limit": 10},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2  # Should find 99213 and 99214
        assert all(code["code"].startswith("992") for code in data)

    def test_search_by_description_keyword(self, client, test_api_key, sample_cpt_codes):
        """Test searching by description keyword"""
        response = client.get(
            "/api/v1/procedure/search",
            params={"query": "office visit", "limit": 10},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2  # Should find office visit codes
        assert any("office" in code["description"].lower() for code in data)

    def test_filter_by_code_system_cpt(self, client, test_api_key, sample_cpt_codes):
        """Test filtering by CPT code system"""
        response = client.get(
            "/api/v1/procedure/search",
            params={"query": "99", "code_system": "CPT", "limit": 10},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert all(code["code_system"] == "CPT" for code in data)

    def test_filter_by_code_system_hcpcs(self, client, test_api_key, sample_cpt_codes):
        """Test filtering by HCPCS code system"""
        response = client.get(
            "/api/v1/procedure/search",
            params={"query": "E", "code_system": "HCPCS", "limit": 10},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert all(code["code_system"] == "HCPCS" for code in data)

    def test_filter_by_version_year(self, client, test_api_key, sample_cpt_codes):
        """Test filtering by version year"""
        response = client.get(
            "/api/v1/procedure/search",
            params={"query": "99", "version_year": 2025, "limit": 10},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert all(code["version_year"] == 2025 for code in data)

    def test_limit_parameter(self, client, test_api_key, sample_cpt_codes):
        """Test limit parameter works correctly"""
        response = client.get(
            "/api/v1/procedure/search",
            params={"query": "99", "limit": 2},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_search_no_results(self, client, test_api_key, sample_cpt_codes):
        """Test search with no matching results"""
        response = client.get(
            "/api/v1/procedure/search",
            params={"query": "NONEXISTENT", "limit": 10},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_search_without_api_key(self, client, sample_cpt_codes):
        """Test that search requires API key"""
        response = client.get(
            "/api/v1/procedure/search",
            params={"query": "99213", "limit": 10}
        )

        assert response.status_code == 403  # Forbidden (no API key provided)


class TestSemanticSearch:
    """Tests for semantic search with embeddings"""

    def test_semantic_search_basic(self, client, test_api_key, sample_cpt_codes):
        """Test basic semantic search functionality"""
        response = client.get(
            "/api/v1/procedure/semantic-search",
            params={"query": "office visit", "limit": 5},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "total_results" in data
        assert data["query"] == "office visit"

    def test_semantic_search_returns_similarity_scores(self, client, test_api_key, sample_cpt_codes):
        """Test that semantic search returns similarity scores"""
        response = client.get(
            "/api/v1/procedure/semantic-search",
            params={"query": "knee procedure", "limit": 5},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()

        if len(data["results"]) > 0:
            for result in data["results"]:
                assert "similarity" in result
                assert 0.0 <= result["similarity"] <= 1.0
                assert "code_info" in result

    def test_semantic_search_with_code_system_filter(self, client, test_api_key, sample_cpt_codes):
        """Test semantic search with code system filtering"""
        response = client.get(
            "/api/v1/procedure/semantic-search",
            params={"query": "surgical procedure", "code_system": "CPT", "limit": 5},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()

        for result in data["results"]:
            assert result["code_info"]["code_system"] == "CPT"

    def test_semantic_search_with_min_similarity(self, client, test_api_key, sample_cpt_codes):
        """Test semantic search with minimum similarity threshold"""
        response = client.get(
            "/api/v1/procedure/semantic-search",
            params={"query": "office visit", "min_similarity": 0.5, "limit": 5},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()

        for result in data["results"]:
            assert result["similarity"] >= 0.5

    def test_semantic_search_natural_language_query(self, client, test_api_key, sample_cpt_codes):
        """Test semantic search with natural language query"""
        response = client.get(
            "/api/v1/procedure/semantic-search",
            params={"query": "I need to see my doctor for a routine checkup", "limit": 5},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        # Should find office visit codes

    def test_semantic_search_without_embeddings(self, client, test_api_key, db_session):
        """Test semantic search behavior when codes don't have embeddings"""
        # Create a code without embeddings
        code_no_embedding = ProcedureCode(
            code="99999",
            code_system="CPT",
            paraphrased_desc="Test code without embeddings",
            category="Test",
            version_year=2025,
            is_active=True,
            effective_date=date(2025, 1, 1),
            license_status="free",
            embedding=None  # No embedding
        )
        db_session.add(code_no_embedding)
        db_session.commit()

        response = client.get(
            "/api/v1/procedure/semantic-search",
            params={"query": "test", "limit": 5},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        # Should still return 200, just won't include codes without embeddings
        assert response.status_code == 200


class TestHybridSearch:
    """Tests for hybrid search (semantic + keyword)"""

    def test_hybrid_search_basic(self, client, test_api_key, sample_cpt_codes):
        """Test basic hybrid search functionality"""
        response = client.get(
            "/api/v1/procedure/hybrid-search",
            params={"query": "office visit", "semantic_weight": 0.7, "limit": 5},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert data["query"] == "office visit"

    def test_hybrid_search_pure_semantic_weight(self, client, test_api_key, sample_cpt_codes):
        """Test hybrid search with pure semantic weight (1.0)"""
        response = client.get(
            "/api/v1/procedure/hybrid-search",
            params={"query": "knee procedure", "semantic_weight": 1.0, "limit": 5},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should behave like pure semantic search
        assert "results" in data

    def test_hybrid_search_pure_keyword_weight(self, client, test_api_key, sample_cpt_codes):
        """Test hybrid search with pure keyword weight (0.0)"""
        response = client.get(
            "/api/v1/procedure/hybrid-search",
            params={"query": "99213", "semantic_weight": 0.0, "limit": 5},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should behave like pure keyword search
        assert "results" in data

    def test_hybrid_search_balanced_weight(self, client, test_api_key, sample_cpt_codes):
        """Test hybrid search with balanced weight (0.5)"""
        response = client.get(
            "/api/v1/procedure/hybrid-search",
            params={"query": "arthroscopy", "semantic_weight": 0.5, "limit": 5},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    def test_hybrid_search_with_filters(self, client, test_api_key, sample_cpt_codes):
        """Test hybrid search with code system and year filters"""
        response = client.get(
            "/api/v1/procedure/hybrid-search",
            params={
                "query": "procedure",
                "code_system": "CPT",
                "version_year": 2025,
                "semantic_weight": 0.7,
                "limit": 5
            },
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()

        for result in data["results"]:
            assert result["code_info"]["code_system"] == "CPT"
            assert result["code_info"]["version_year"] == 2025

    def test_hybrid_search_invalid_weight(self, client, test_api_key, sample_cpt_codes):
        """Test hybrid search with invalid semantic weight"""
        # Weight > 1.0
        response = client.get(
            "/api/v1/procedure/hybrid-search",
            params={"query": "test", "semantic_weight": 1.5, "limit": 5},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 422  # Validation error

        # Weight < 0.0
        response = client.get(
            "/api/v1/procedure/hybrid-search",
            params={"query": "test", "semantic_weight": -0.5, "limit": 5},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 422  # Validation error


class TestFacetedSearch:
    """Tests for faceted search functionality"""

    def test_faceted_search_by_category(self, client, test_api_key, sample_cpt_codes):
        """Test faceted search by procedure category"""
        response = client.get(
            "/api/v1/procedure/faceted-search",
            params={"procedure_category": "Surgery", "limit": 10},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Response is either a list or dict with results key
        results = data.get("results", data) if isinstance(data, dict) else data

        # Should find knee arthroscopy codes
        if len(results) > 0:
            assert any(result.get("category") == "Surgery" or result.get("code_info", {}).get("category") == "Surgery" for result in results)

    def test_faceted_search_by_body_region(self, client, test_api_key, sample_cpt_codes, sample_facets):
        """Test faceted search by body region"""
        response = client.get(
            "/api/v1/procedure/faceted-search",
            params={"body_region": "lower_extremity", "limit": 10},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Response is either a list or dict with results key
        results = data.get("results", data) if isinstance(data, dict) else data

        for result in results:
            if result.get("facets"):
                assert result["facets"]["body_region"] == "lower_extremity"

    def test_faceted_search_multiple_facets(self, client, test_api_key, sample_cpt_codes, sample_facets):
        """Test faceted search with multiple facet filters"""
        response = client.get(
            "/api/v1/procedure/faceted-search",
            params={
                "procedure_category": "surgical",
                "body_region": "lower_extremity",
                "limit": 10
            },
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should return results matching all specified facets


class TestErrorHandling:
    """Tests for error handling and edge cases"""

    def test_search_empty_query(self, client, test_api_key):
        """Test search with empty query string"""
        response = client.get(
            "/api/v1/procedure/search",
            params={"query": "", "limit": 10},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        # Empty query may return 200 with no results or 422 validation error
        assert response.status_code in [200, 422]

    def test_search_invalid_limit(self, client, test_api_key):
        """Test search with invalid limit values"""
        # Limit too high
        response = client.get(
            "/api/v1/procedure/search",
            params={"query": "test", "limit": 1000},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 422

        # Limit too low
        response = client.get(
            "/api/v1/procedure/search",
            params={"query": "test", "limit": 0},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 422

    def test_search_invalid_code_system(self, client, test_api_key):
        """Test search with invalid code system"""
        response = client.get(
            "/api/v1/procedure/search",
            params={"query": "test", "code_system": "INVALID"},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        # Should still return 200 but no results
        assert response.status_code == 200

    def test_semantic_search_very_long_query(self, client, test_api_key, sample_cpt_codes):
        """Test semantic search with very long query"""
        long_query = "test " * 500  # Very long query

        response = client.get(
            "/api/v1/procedure/semantic-search",
            params={"query": long_query, "limit": 5},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_search_with_inactive_api_key(self, client, test_api_key, db_session):
        """Test that inactive API keys are rejected"""
        # Deactivate the API key
        test_api_key.is_active = False
        db_session.commit()

        response = client.get(
            "/api/v1/procedure/search",
            params={"query": "99213", "limit": 10},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 401


class TestResponseFormat:
    """Tests for response data format and structure"""

    def test_basic_search_response_structure(self, client, test_api_key, sample_cpt_codes):
        """Test that basic search response has correct structure"""
        response = client.get(
            "/api/v1/procedure/search",
            params={"query": "99213", "limit": 10},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()

        if len(data) > 0:
            code = data[0]
            assert "id" in code
            assert "code" in code
            assert "code_system" in code
            assert "description" in code
            assert "category" in code
            assert "license_status" in code
            assert "version_year" in code

    def test_semantic_search_response_structure(self, client, test_api_key, sample_cpt_codes):
        """Test that semantic search response has correct structure"""
        response = client.get(
            "/api/v1/procedure/semantic-search",
            params={"query": "office visit", "limit": 5},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "query" in data
        assert "results" in data
        assert "total_results" in data

        if len(data["results"]) > 0:
            result = data["results"][0]
            assert "code_info" in result
            assert "similarity" in result
            assert "facets" in result
            assert "mappings" in result

            # Check code_info structure
            code_info = result["code_info"]
            assert "id" in code_info
            assert "code" in code_info
            assert "code_system" in code_info
            assert "paraphrased_desc" in code_info
            assert "category" in code_info

    def test_hybrid_search_response_structure(self, client, test_api_key, sample_cpt_codes):
        """Test that hybrid search response has correct structure"""
        response = client.get(
            "/api/v1/procedure/hybrid-search",
            params={"query": "arthroscopy", "semantic_weight": 0.7, "limit": 5},
            headers={"Authorization": f"Bearer {test_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "query" in data
        assert "results" in data
        assert "total_results" in data
