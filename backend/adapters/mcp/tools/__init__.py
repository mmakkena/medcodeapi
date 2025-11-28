"""
MCP Tools Package

All MCP tools for the Nuvii CDI Agent.
"""

from adapters.mcp.tools.analyze_note import ANALYZE_NOTE_TOOL, handle_analyze_note
from adapters.mcp.tools.generate_query import GENERATE_QUERY_TOOL, handle_generate_query
from adapters.mcp.tools.search_icd10 import SEARCH_ICD10_TOOL, handle_search_icd10
from adapters.mcp.tools.search_cpt import SEARCH_CPT_TOOL, handle_search_cpt
from adapters.mcp.tools.calculate_fees import CALCULATE_FEES_TOOL, handle_calculate_fees
from adapters.mcp.tools.optimize_revenue import OPTIMIZE_REVENUE_TOOL, handle_optimize_revenue
from adapters.mcp.tools.evaluate_hedis import EVALUATE_HEDIS_TOOL, handle_evaluate_hedis
from adapters.mcp.tools.extract_entities import EXTRACT_ENTITIES_TOOL, handle_extract_entities

__all__ = [
    # Tools
    "ANALYZE_NOTE_TOOL",
    "GENERATE_QUERY_TOOL",
    "SEARCH_ICD10_TOOL",
    "SEARCH_CPT_TOOL",
    "CALCULATE_FEES_TOOL",
    "OPTIMIZE_REVENUE_TOOL",
    "EVALUATE_HEDIS_TOOL",
    "EXTRACT_ENTITIES_TOOL",
    # Handlers
    "handle_analyze_note",
    "handle_generate_query",
    "handle_search_icd10",
    "handle_search_cpt",
    "handle_calculate_fees",
    "handle_optimize_revenue",
    "handle_evaluate_hedis",
    "handle_extract_entities",
]
