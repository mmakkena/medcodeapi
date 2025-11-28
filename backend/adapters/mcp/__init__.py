"""
MCP Server Adapter

Provides Model Context Protocol (MCP) server for LLM agent integration.
Compatible with Claude Desktop, VS Code, and other MCP clients.

Tools available:
- analyze_note: Comprehensive clinical note analysis
- generate_query: CDI query generation for physicians
- search_icd10: ICD-10 diagnosis code search
- search_cpt: CPT/HCPCS procedure code search
- calculate_fees: Medicare fee schedule lookup
- optimize_revenue: Revenue optimization analysis
- evaluate_hedis: HEDIS quality measure evaluation
- extract_entities: Clinical entity extraction
"""

from adapters.mcp.tools import (
    ANALYZE_NOTE_TOOL,
    GENERATE_QUERY_TOOL,
    SEARCH_ICD10_TOOL,
    SEARCH_CPT_TOOL,
    CALCULATE_FEES_TOOL,
    OPTIMIZE_REVENUE_TOOL,
    EVALUATE_HEDIS_TOOL,
    EXTRACT_ENTITIES_TOOL,
)

__all__ = [
    "ANALYZE_NOTE_TOOL",
    "GENERATE_QUERY_TOOL",
    "SEARCH_ICD10_TOOL",
    "SEARCH_CPT_TOOL",
    "CALCULATE_FEES_TOOL",
    "OPTIMIZE_REVENUE_TOOL",
    "EVALUATE_HEDIS_TOOL",
    "EXTRACT_ENTITIES_TOOL",
]
