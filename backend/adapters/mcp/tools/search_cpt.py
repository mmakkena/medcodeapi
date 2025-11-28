"""
Search CPT MCP Tool

Searches CPT/HCPCS procedure codes using semantic similarity.
Finds relevant procedure codes based on clinical descriptions.
"""

from typing import Any
from mcp.types import Tool

from infrastructure.db.postgres import get_db_sync
from infrastructure.db.repositories.code_repository import CodeRepository

SEARCH_CPT_TOOL = Tool(
    name="search_cpt",
    description="""Searches CPT/HCPCS procedure codes using semantic similarity.

Finds relevant procedure codes based on clinical descriptions. Supports:
- Procedure names (e.g., "chest x-ray")
- Code lookup (e.g., "99213")
- Clinical descriptions (e.g., "established patient office visit")
- Equipment codes (HCPCS)

Returns matching codes with descriptions, categories, and relevance scores.""",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (procedure description or code)"
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return (1-20)",
                "default": 5
            },
            "code_type": {
                "type": "string",
                "description": "Filter by code type",
                "enum": ["all", "cpt", "hcpcs"],
                "default": "all"
            }
        },
        "required": ["query"]
    }
)


async def handle_search_cpt(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Handle the search_cpt tool call.

    Args:
        arguments: Tool arguments containing query and options

    Returns:
        Matching CPT/HCPCS codes with descriptions and relevance scores
    """
    query = arguments.get("query", "")
    top_k = min(arguments.get("top_k", 5), 20)  # Cap at 20
    code_type = arguments.get("code_type", "all")

    if not query.strip():
        return {"error": "query is required and cannot be empty"}

    try:
        # Get database session
        db = next(get_db_sync())
        repo = CodeRepository(db)

        # Perform semantic search
        results = repo.search_cpt(
            query=query,
            limit=top_k,
            code_type=code_type if code_type != "all" else None
        )

        # Format results
        codes = []
        for result in results:
            code_dict = {
                "code": result.code,
                "description": result.description,
                "category": result.category if hasattr(result, 'category') else None,
                "code_type": result.code_type if hasattr(result, 'code_type') else "CPT",
                "is_active": result.is_active if hasattr(result, 'is_active') else True,
                "relevance_score": result.score if hasattr(result, 'score') else None
            }
            codes.append(code_dict)

        return {
            "success": True,
            "query": query,
            "results": codes,
            "result_count": len(codes),
            "search_type": "semantic",
            "code_type_filter": code_type
        }

    except Exception as e:
        # Fallback to basic search if semantic search fails
        return await _fallback_cpt_search(query, top_k, code_type)
    finally:
        if 'db' in locals():
            db.close()


async def _fallback_cpt_search(query: str, top_k: int, code_type: str) -> dict[str, Any]:
    """
    Fallback CPT/HCPCS search using basic pattern matching.

    Used when database/semantic search is unavailable.
    """
    # Common CPT/HCPCS codes for fallback
    common_codes = {
        "office visit": [
            {"code": "99213", "description": "Office visit, established patient, low complexity", "code_type": "CPT"},
            {"code": "99214", "description": "Office visit, established patient, moderate complexity", "code_type": "CPT"},
            {"code": "99215", "description": "Office visit, established patient, high complexity", "code_type": "CPT"},
            {"code": "99203", "description": "Office visit, new patient, low complexity", "code_type": "CPT"},
            {"code": "99204", "description": "Office visit, new patient, moderate complexity", "code_type": "CPT"},
        ],
        "x-ray": [
            {"code": "71046", "description": "Chest X-ray, 2 views", "code_type": "CPT"},
            {"code": "71045", "description": "Chest X-ray, single view", "code_type": "CPT"},
        ],
        "ecg": [
            {"code": "93000", "description": "Electrocardiogram, complete", "code_type": "CPT"},
            {"code": "93005", "description": "Electrocardiogram, tracing only", "code_type": "CPT"},
        ],
        "blood": [
            {"code": "85025", "description": "Complete blood count (CBC) with differential", "code_type": "CPT"},
            {"code": "80053", "description": "Comprehensive metabolic panel", "code_type": "CPT"},
        ],
        "hba1c": [
            {"code": "83036", "description": "Hemoglobin A1c", "code_type": "CPT"},
        ],
        "colonoscopy": [
            {"code": "45378", "description": "Colonoscopy, diagnostic", "code_type": "CPT"},
            {"code": "45380", "description": "Colonoscopy with biopsy", "code_type": "CPT"},
        ],
        "mammogram": [
            {"code": "77067", "description": "Screening mammography, bilateral", "code_type": "CPT"},
        ],
        "injection": [
            {"code": "96372", "description": "Therapeutic injection, subcutaneous or intramuscular", "code_type": "CPT"},
        ],
    }

    query_lower = query.lower()
    results = []

    for keyword, codes in common_codes.items():
        if keyword in query_lower or query_lower in keyword:
            for code in codes:
                if code_type == "all" or code.get("code_type", "").lower() == code_type.lower():
                    results.append(code)

    return {
        "success": True,
        "query": query,
        "results": results[:top_k],
        "result_count": len(results[:top_k]),
        "search_type": "fallback",
        "code_type_filter": code_type,
        "note": "Using fallback search - database connection unavailable"
    }
