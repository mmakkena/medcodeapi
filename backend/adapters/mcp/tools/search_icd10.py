"""
Search ICD-10 MCP Tool

Searches ICD-10 diagnosis codes using semantic similarity.
Understands clinical language and finds relevant codes.
"""

from typing import Any
from mcp.types import Tool

from infrastructure.db.postgres import get_db_sync
from infrastructure.db.repositories.code_repository import CodeRepository

SEARCH_ICD10_TOOL = Tool(
    name="search_icd10",
    description="""Searches ICD-10 diagnosis codes using semantic similarity.

Understands clinical language and finds relevant codes even with non-standard terminology.
Supports searching by:
- Clinical condition name (e.g., "heart failure")
- Code prefix (e.g., "I50")
- Symptoms or clinical descriptions
- Lay terms (e.g., "sugar diabetes")

Returns matching codes with descriptions, categories, and relevance scores.""",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (clinical term, condition, or code)"
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return (1-20)",
                "default": 5
            },
            "include_subcodes": {
                "type": "boolean",
                "description": "Include more specific subcodes in results",
                "default": True
            }
        },
        "required": ["query"]
    }
)


async def handle_search_icd10(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Handle the search_icd10 tool call.

    Args:
        arguments: Tool arguments containing query and options

    Returns:
        Matching ICD-10 codes with descriptions and relevance scores
    """
    query = arguments.get("query", "")
    top_k = min(arguments.get("top_k", 5), 20)  # Cap at 20
    include_subcodes = arguments.get("include_subcodes", True)

    if not query.strip():
        return {"error": "query is required and cannot be empty"}

    try:
        # Get database session
        db = next(get_db_sync())
        repo = CodeRepository(db)

        # Perform semantic search
        results = repo.search_icd10(
            query=query,
            limit=top_k,
            include_subcodes=include_subcodes
        )

        # Format results
        codes = []
        for result in results:
            code_dict = {
                "code": result.code,
                "description": result.description,
                "category": result.category if hasattr(result, 'category') else None,
                "chapter": result.chapter if hasattr(result, 'chapter') else None,
                "is_billable": result.is_billable if hasattr(result, 'is_billable') else True,
                "relevance_score": result.score if hasattr(result, 'score') else None
            }
            codes.append(code_dict)

        return {
            "success": True,
            "query": query,
            "results": codes,
            "result_count": len(codes),
            "search_type": "semantic"
        }

    except Exception as e:
        # Fallback to basic search if semantic search fails
        return await _fallback_icd10_search(query, top_k)
    finally:
        if 'db' in locals():
            db.close()


async def _fallback_icd10_search(query: str, top_k: int) -> dict[str, Any]:
    """
    Fallback ICD-10 search using basic pattern matching.

    Used when database/semantic search is unavailable.
    """
    # Common ICD-10 codes for fallback
    common_codes = {
        "diabetes": [
            {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications"},
            {"code": "E11.65", "description": "Type 2 diabetes mellitus with hyperglycemia"},
            {"code": "E10.9", "description": "Type 1 diabetes mellitus without complications"},
        ],
        "hypertension": [
            {"code": "I10", "description": "Essential (primary) hypertension"},
            {"code": "I11.9", "description": "Hypertensive heart disease without heart failure"},
            {"code": "I12.9", "description": "Hypertensive chronic kidney disease with stage 1-4 CKD"},
        ],
        "heart failure": [
            {"code": "I50.9", "description": "Heart failure, unspecified"},
            {"code": "I50.22", "description": "Chronic systolic (congestive) heart failure"},
            {"code": "I50.32", "description": "Chronic diastolic (congestive) heart failure"},
        ],
        "copd": [
            {"code": "J44.9", "description": "Chronic obstructive pulmonary disease, unspecified"},
            {"code": "J44.1", "description": "Chronic obstructive pulmonary disease with acute exacerbation"},
        ],
        "pneumonia": [
            {"code": "J18.9", "description": "Pneumonia, unspecified organism"},
            {"code": "J15.9", "description": "Unspecified bacterial pneumonia"},
        ],
        "ckd": [
            {"code": "N18.9", "description": "Chronic kidney disease, unspecified"},
            {"code": "N18.3", "description": "Chronic kidney disease, stage 3"},
            {"code": "N18.4", "description": "Chronic kidney disease, stage 4"},
        ],
    }

    query_lower = query.lower()
    results = []

    for keyword, codes in common_codes.items():
        if keyword in query_lower or query_lower in keyword:
            results.extend(codes)

    return {
        "success": True,
        "query": query,
        "results": results[:top_k],
        "result_count": len(results[:top_k]),
        "search_type": "fallback",
        "note": "Using fallback search - database connection unavailable"
    }
