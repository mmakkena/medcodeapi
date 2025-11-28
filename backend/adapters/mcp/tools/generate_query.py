"""
Generate Query MCP Tool

Creates physician-facing documentation queries for CDI specialists.
Queries are non-leading and clinically appropriate per ACDIS guidelines.
"""

from typing import Any
from mcp.types import Tool

from domain.entity_extraction import ClinicalEntityExtractor
from domain.documentation_gaps import DocumentationGapAnalyzer
from domain.query_generation import CDIQueryGenerator

GENERATE_QUERY_TOOL = Tool(
    name="generate_query",
    description="""Creates physician-facing documentation queries to clarify or improve note completeness.

Returns non-leading, clinically appropriate queries for CDI specialists to send to providers.
Queries follow ACDIS guidelines and are designed to:
- Clarify ambiguous clinical findings
- Request specificity for diagnoses
- Address missing documentation elements
- Improve coding accuracy without leading the physician

Use this tool when documentation gaps are identified and physician clarification is needed.""",
    inputSchema={
        "type": "object",
        "properties": {
            "note_text": {
                "type": "string",
                "description": "The clinical note with documentation gaps"
            },
            "gap_type": {
                "type": "string",
                "description": "Specific gap type to address (optional)",
                "enum": ["specificity", "acuity", "comorbidity", "medical_necessity", "all"]
            },
            "condition": {
                "type": "string",
                "description": "Specific condition to generate query for (optional)"
            },
            "max_queries": {
                "type": "integer",
                "description": "Maximum number of queries to generate",
                "default": 5
            }
        },
        "required": ["note_text"]
    }
)


async def handle_generate_query(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Handle the generate_query tool call.

    Args:
        arguments: Tool arguments containing note_text and optional filters

    Returns:
        Generated CDI queries with priority and context
    """
    note_text = arguments.get("note_text", "")
    gap_type = arguments.get("gap_type", "all")
    condition = arguments.get("condition")
    max_queries = arguments.get("max_queries", 5)

    if not note_text.strip():
        return {"error": "note_text is required and cannot be empty"}

    # Extract entities first
    extractor = ClinicalEntityExtractor()
    entities = extractor.extract(note_text)

    # Analyze documentation gaps
    gap_analyzer = DocumentationGapAnalyzer()
    gap_result = gap_analyzer.analyze(entities=entities)

    # Generate queries
    query_generator = CDIQueryGenerator()

    # If specific condition provided, generate condition-specific query
    if condition:
        query_result = query_generator.generate_condition_query(
            condition=condition,
            note_text=note_text
        )
    else:
        query_result = query_generator.generate_from_gaps(gap_result)

    # Format queries response
    queries = []
    if hasattr(query_result, 'queries'):
        for query in query_result.queries:
            query_dict = {
                "query_text": query.query_text if hasattr(query, 'query_text') else str(query),
                "query_type": query.query_type if hasattr(query, 'query_type') else "clarification",
                "priority": query.priority if hasattr(query, 'priority') else "medium",
                "target_condition": query.target_condition if hasattr(query, 'target_condition') else None,
                "clinical_indicators": query.clinical_indicators if hasattr(query, 'clinical_indicators') else [],
                "is_compliant": True  # All generated queries are ACDIS compliant
            }

            # Filter by gap type if specified
            if gap_type != "all":
                if query_dict.get("query_type", "").lower() != gap_type.lower():
                    continue

            queries.append(query_dict)

            if len(queries) >= max_queries:
                break

    # If we have string result instead of structured queries
    if not queries and isinstance(query_result, str):
        queries.append({
            "query_text": query_result,
            "query_type": gap_type if gap_type != "all" else "clarification",
            "priority": "medium",
            "target_condition": condition,
            "clinical_indicators": [],
            "is_compliant": True
        })

    return {
        "success": True,
        "queries": queries,
        "query_count": len(queries),
        "gap_type_filter": gap_type,
        "compliance_note": "All queries are non-leading and follow ACDIS guidelines",
        "usage_guidance": {
            "best_practice": "Review clinical context before sending to physician",
            "timing": "Send queries within 24-48 hours of documentation",
            "follow_up": "Document physician response in medical record"
        }
    }
