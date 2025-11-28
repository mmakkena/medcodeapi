"""
MCP Server for Nuvii CDI Agent

Provides Model Context Protocol (MCP) server for LLM agent integration.
Compatible with Claude Desktop, VS Code, and other MCP clients.

Tools available:
- analyze_note: Comprehensive clinical note analysis
- generate_query: Create CDI queries for physicians
- search_icd10: Semantic ICD-10 code search
- search_cpt: Semantic CPT/HCPCS code search
- calculate_fees: Medicare fee schedule lookup
- optimize_revenue: Revenue optimization analysis
- evaluate_hedis: HEDIS quality measure evaluation
- extract_entities: Clinical entity extraction
"""

import asyncio
import json
import logging
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import tool handlers
from adapters.mcp.tools.analyze_note import handle_analyze_note, ANALYZE_NOTE_TOOL
from adapters.mcp.tools.generate_query import handle_generate_query, GENERATE_QUERY_TOOL
from adapters.mcp.tools.search_icd10 import handle_search_icd10, SEARCH_ICD10_TOOL
from adapters.mcp.tools.search_cpt import handle_search_cpt, SEARCH_CPT_TOOL
from adapters.mcp.tools.calculate_fees import handle_calculate_fees, CALCULATE_FEES_TOOL
from adapters.mcp.tools.optimize_revenue import handle_optimize_revenue, OPTIMIZE_REVENUE_TOOL
from adapters.mcp.tools.evaluate_hedis import handle_evaluate_hedis, EVALUATE_HEDIS_TOOL
from adapters.mcp.tools.extract_entities import handle_extract_entities, EXTRACT_ENTITIES_TOOL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create server instance
server = Server("nuvii-cdi-agent")

# Tool registry mapping tool names to handlers
TOOL_HANDLERS = {
    "analyze_note": handle_analyze_note,
    "generate_query": handle_generate_query,
    "search_icd10": handle_search_icd10,
    "search_cpt": handle_search_cpt,
    "calculate_fees": handle_calculate_fees,
    "optimize_revenue": handle_optimize_revenue,
    "evaluate_hedis": handle_evaluate_hedis,
    "extract_entities": handle_extract_entities,
}

# All available tools
ALL_TOOLS = [
    ANALYZE_NOTE_TOOL,
    GENERATE_QUERY_TOOL,
    SEARCH_ICD10_TOOL,
    SEARCH_CPT_TOOL,
    CALCULATE_FEES_TOOL,
    OPTIMIZE_REVENUE_TOOL,
    EVALUATE_HEDIS_TOOL,
    EXTRACT_ENTITIES_TOOL,
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available MCP tools."""
    return ALL_TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle tool calls from MCP clients.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List of TextContent with tool results
    """
    logger.info(f"Tool call: {name} with args: {arguments}")

    handler = TOOL_HANDLERS.get(name)
    if not handler:
        error_msg = f"Unknown tool: {name}. Available tools: {list(TOOL_HANDLERS.keys())}"
        logger.error(error_msg)
        return [TextContent(type="text", text=json.dumps({"error": error_msg}))]

    try:
        result = await handler(arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({
            "error": str(e),
            "tool": name
        }))]


async def main():
    """Run the MCP server."""
    logger.info("Starting Nuvii CDI Agent MCP Server...")
    logger.info(f"Available tools: {[t.name for t in ALL_TOOLS]}")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
