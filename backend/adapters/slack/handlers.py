"""
Slack Event Handlers for CDI Bot

Contains handler functions for slash commands, events, and interactive actions.
All handlers use the domain layer for CDI logic.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def handle_analyze_note(command: Dict[str, Any], client) -> None:
    """
    Handle /cdi-analyze slash command.

    Analyzes a clinical note for documentation gaps and opportunities.

    Args:
        command: Slack command payload
        client: Slack client
    """
    text = command.get("text", "").strip()
    channel = command["channel_id"]
    user = command["user_id"]

    if not text:
        client.chat_postMessage(
            channel=channel,
            text="Please provide a clinical note to analyze.\n"
                 "Usage: `/cdi-analyze <clinical note text>`"
        )
        return

    # Send processing message
    response = client.chat_postMessage(
        channel=channel,
        text=":hourglass_flowing_sand: Analyzing clinical note..."
    )

    try:
        result = process_clinical_note(text)

        client.chat_update(
            channel=channel,
            ts=response["ts"],
            blocks=result["blocks"],
            text=result["text"]
        )

    except Exception as e:
        logger.error(f"Error in analyze_note: {e}")
        client.chat_update(
            channel=channel,
            ts=response["ts"],
            text=f":x: Error analyzing note: {str(e)}"
        )


def handle_generate_query(command: Dict[str, Any], client) -> None:
    """
    Handle /cdi-query slash command.

    Generates a CDI query for physician clarification.

    Args:
        command: Slack command payload
        client: Slack client
    """
    text = command.get("text", "").strip()
    channel = command["channel_id"]

    if not text:
        client.chat_postMessage(
            channel=channel,
            text="Please provide context for the query.\n"
                 "Usage: `/cdi-query <condition or documentation gap>`"
        )
        return

    response = client.chat_postMessage(
        channel=channel,
        text=":hourglass_flowing_sand: Generating CDI query..."
    )

    try:
        # Use domain layer for query generation
        from domain.query_generation import CDIQueryGenerator

        generator = CDIQueryGenerator()
        query_result = generator.generate_condition_query(text)

        blocks = _format_query_result(query_result)

        client.chat_update(
            channel=channel,
            ts=response["ts"],
            blocks=blocks,
            text="CDI Query Generated"
        )

    except ImportError:
        # Fallback if domain layer not available
        client.chat_update(
            channel=channel,
            ts=response["ts"],
            text=f":memo: *CDI Query for: {text}*\n\n"
                 f"_Query generation requires the domain layer to be configured._"
        )
    except Exception as e:
        logger.error(f"Error generating query: {e}")
        client.chat_update(
            channel=channel,
            ts=response["ts"],
            text=f":x: Error generating query: {str(e)}"
        )


def handle_code_lookup(command: Dict[str, Any], client) -> None:
    """
    Handle /cdi-code slash command.

    Looks up ICD-10 or CPT codes.

    Args:
        command: Slack command payload
        client: Slack client
    """
    text = command.get("text", "").strip()
    channel = command["channel_id"]

    if not text:
        client.chat_postMessage(
            channel=channel,
            text="Please provide a code or search term.\n"
                 "Usage: `/cdi-code <code or description>`\n"
                 "Examples:\n"
                 "  `/cdi-code I10` - Look up code I10\n"
                 "  `/cdi-code hypertension` - Search for hypertension codes"
        )
        return

    response = client.chat_postMessage(
        channel=channel,
        text=":mag: Searching codes..."
    )

    try:
        # Determine if it's a code lookup or search
        is_code = _looks_like_code(text)

        if is_code:
            result = _lookup_code(text)
        else:
            result = _search_codes(text)

        client.chat_update(
            channel=channel,
            ts=response["ts"],
            blocks=result["blocks"],
            text=result["text"]
        )

    except Exception as e:
        logger.error(f"Error in code lookup: {e}")
        client.chat_update(
            channel=channel,
            ts=response["ts"],
            text=f":x: Error looking up code: {str(e)}"
        )


def handle_revenue_analysis(command: Dict[str, Any], client) -> None:
    """
    Handle /cdi-revenue slash command.

    Analyzes revenue optimization opportunities.

    Args:
        command: Slack command payload
        client: Slack client
    """
    text = command.get("text", "").strip()
    channel = command["channel_id"]

    if not text:
        client.chat_postMessage(
            channel=channel,
            text="Please provide a clinical note or diagnosis list.\n"
                 "Usage: `/cdi-revenue <clinical note or diagnoses>`"
        )
        return

    response = client.chat_postMessage(
        channel=channel,
        text=":chart_with_upwards_trend: Analyzing revenue opportunities..."
    )

    try:
        from domain.revenue_optimization import RevenueOptimizer

        optimizer = RevenueOptimizer()
        result = optimizer.analyze(text)

        blocks = _format_revenue_result(result)

        client.chat_update(
            channel=channel,
            ts=response["ts"],
            blocks=blocks,
            text="Revenue Analysis Complete"
        )

    except ImportError:
        client.chat_update(
            channel=channel,
            ts=response["ts"],
            text=":chart_with_upwards_trend: *Revenue Analysis*\n\n"
                 "_Revenue optimization requires the domain layer to be configured._"
        )
    except Exception as e:
        logger.error(f"Error in revenue analysis: {e}")
        client.chat_update(
            channel=channel,
            ts=response["ts"],
            text=f":x: Error analyzing revenue: {str(e)}"
        )


def process_clinical_note(note_text: str) -> Dict[str, Any]:
    """
    Process a clinical note and return formatted Slack blocks.

    Args:
        note_text: The clinical note text

    Returns:
        Dict with 'blocks' (Slack Block Kit) and 'text' (fallback)
    """
    try:
        # Try to use the full domain layer
        from domain.entity_extraction import ClinicalEntityExtractor
        from domain.documentation_gaps import DocumentationGapAnalyzer
        from domain.query_generation import CDIQueryGenerator
        from domain.revenue_optimization import RevenueOptimizer

        # Extract entities
        extractor = ClinicalEntityExtractor()
        entities = extractor.extract(note_text)

        # Analyze gaps
        analyzer = DocumentationGapAnalyzer()
        gap_analysis = analyzer.analyze(entities=entities)

        # Format results
        blocks = _format_full_analysis(entities, gap_analysis)

        return {
            "blocks": blocks,
            "text": f"Analysis complete. Found {len(gap_analysis.gaps) if hasattr(gap_analysis, 'gaps') else 0} documentation gaps."
        }

    except ImportError as e:
        logger.warning(f"Domain layer not available: {e}")
        # Return simplified analysis
        return _simple_note_analysis(note_text)

    except Exception as e:
        logger.error(f"Error processing note: {e}")
        raise


def _simple_note_analysis(note_text: str) -> Dict[str, Any]:
    """Provide simplified analysis when domain layer unavailable."""
    # Basic keyword detection
    keywords = {
        "sepsis": ["sepsis", "septic", "bacteremia"],
        "heart_failure": ["heart failure", "chf", "hf", "cardiomyopathy"],
        "pneumonia": ["pneumonia", "pna", "infiltrate"],
        "diabetes": ["diabetes", "dm", "a1c", "glucose"],
        "hypertension": ["hypertension", "htn", "blood pressure", "bp"],
    }

    note_lower = note_text.lower()
    detected = []

    for condition, terms in keywords.items():
        if any(term in note_lower for term in terms):
            detected.append(condition.replace("_", " ").title())

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":clipboard: Clinical Note Analysis"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Conditions Detected:* {', '.join(detected) if detected else 'None identified'}"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":bulb: *Tip:* For full CDI analysis including documentation gaps, "
                        "query generation, and revenue optimization, ensure the domain layer is configured."
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": ":page_facing_up: Generate Query"
                    },
                    "action_id": "generate_query",
                    "value": note_text[:500]  # Truncate for button value
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": ":mag: View Suggested Codes"
                    },
                    "action_id": "view_codes",
                    "value": note_text[:500]
                }
            ]
        }
    ]

    return {
        "blocks": blocks,
        "text": f"Basic analysis complete. Detected: {', '.join(detected) if detected else 'No specific conditions'}"
    }


def _format_full_analysis(entities, gap_analysis) -> List[Dict[str, Any]]:
    """Format full CDI analysis as Slack blocks."""
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":clipboard: CDI Analysis Results"
            }
        }
    ]

    # Entities section
    if hasattr(entities, 'conditions') and entities.conditions:
        conditions_text = "\n".join([f"• {c.name}" for c in entities.conditions[:5]])
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*:stethoscope: Conditions Identified:*\n{conditions_text}"
            }
        })

    # Documentation gaps
    if hasattr(gap_analysis, 'gaps') and gap_analysis.gaps:
        gaps_text = "\n".join([f"• {g.description}" for g in gap_analysis.gaps[:5]])
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*:warning: Documentation Gaps:*\n{gaps_text}"
            }
        })

    # Opportunities
    if hasattr(gap_analysis, 'opportunities') and gap_analysis.opportunities:
        opps_text = "\n".join([f"• {o}" for o in gap_analysis.opportunities[:3]])
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*:chart_with_upwards_trend: Opportunities:*\n{opps_text}"
            }
        })

    blocks.append({"type": "divider"})

    # Action buttons
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": ":page_facing_up: Generate Query"},
                "style": "primary",
                "action_id": "generate_query"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": ":dollar: Revenue Details"},
                "action_id": "revenue_details"
            }
        ]
    })

    return blocks


def _format_query_result(query_result) -> List[Dict[str, Any]]:
    """Format CDI query result as Slack blocks."""
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":memo: CDI Query"
            }
        }
    ]

    if hasattr(query_result, 'query_text'):
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"```{query_result.query_text}```"
            }
        })

    if hasattr(query_result, 'rationale'):
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*Rationale:* {query_result.rationale}"
                }
            ]
        })

    return blocks


def _format_revenue_result(result) -> List[Dict[str, Any]]:
    """Format revenue analysis result as Slack blocks."""
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":chart_with_upwards_trend: Revenue Analysis"
            }
        }
    ]

    if hasattr(result, 'total_opportunity'):
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Potential Revenue Impact:* ${result.total_opportunity:,.2f}"
            }
        })

    if hasattr(result, 'opportunities') and result.opportunities:
        for opp in result.opportunities[:3]:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"• *{opp.condition}*: {opp.description}\n  _Impact: ${opp.value:,.2f}_"
                }
            })

    return blocks


def _looks_like_code(text: str) -> bool:
    """Check if text looks like a medical code."""
    import re
    # ICD-10: Letter followed by numbers (e.g., I10, E11.9)
    # CPT: 5 digits (e.g., 99213)
    # HCPCS: Letter + 4 digits (e.g., G0101)
    patterns = [
        r'^[A-Z]\d{2}(\.\d{1,4})?$',  # ICD-10
        r'^\d{5}$',  # CPT
        r'^[A-Z]\d{4}$',  # HCPCS
    ]
    text = text.upper().strip()
    return any(re.match(p, text) for p in patterns)


def _lookup_code(code: str) -> Dict[str, Any]:
    """Look up a specific medical code."""
    # Try ICD-10 first, then CPT/HCPCS
    try:
        from infrastructure.db.postgres import SessionLocal
        from infrastructure.db.models import ICD10Code, ProcedureCode

        db = SessionLocal()
        try:
            code_upper = code.upper().strip()

            # Try ICD-10
            icd = db.query(ICD10Code).filter(ICD10Code.code == code_upper).first()
            if icd:
                return {
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*ICD-10: {icd.code}*\n{icd.description}"
                            }
                        }
                    ],
                    "text": f"{icd.code}: {icd.description}"
                }

            # Try CPT/HCPCS
            proc = db.query(ProcedureCode).filter(ProcedureCode.code == code_upper).first()
            if proc:
                return {
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*{proc.code_system}: {proc.code}*\n{proc.description}"
                            }
                        }
                    ],
                    "text": f"{proc.code}: {proc.description}"
                }

            return {
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f":warning: Code `{code_upper}` not found"
                        }
                    }
                ],
                "text": f"Code {code_upper} not found"
            }
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error looking up code: {e}")
        return {
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f":x: Error: {str(e)}"}
                }
            ],
            "text": f"Error: {str(e)}"
        }


def _search_codes(query: str) -> Dict[str, Any]:
    """Search for medical codes by description."""
    try:
        from infrastructure.db.postgres import SessionLocal
        from infrastructure.db.models import ICD10Code, ProcedureCode
        from sqlalchemy import or_

        db = SessionLocal()
        try:
            # Search ICD-10
            icd_results = db.query(ICD10Code).filter(
                ICD10Code.description.ilike(f"%{query}%")
            ).limit(5).all()

            # Search CPT/HCPCS
            proc_results = db.query(ProcedureCode).filter(
                ProcedureCode.description.ilike(f"%{query}%")
            ).limit(5).all()

            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f":mag: Search Results: {query}"}
                }
            ]

            if icd_results:
                icd_text = "\n".join([f"• `{r.code}` - {r.description[:60]}..." for r in icd_results])
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*ICD-10 Codes:*\n{icd_text}"}
                })

            if proc_results:
                proc_text = "\n".join([f"• `{r.code}` - {r.description[:60]}..." for r in proc_results])
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*CPT/HCPCS Codes:*\n{proc_text}"}
                })

            if not icd_results and not proc_results:
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f":warning: No codes found for '{query}'"}
                })

            return {
                "blocks": blocks,
                "text": f"Found {len(icd_results)} ICD-10 and {len(proc_results)} CPT/HCPCS codes"
            }
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error searching codes: {e}")
        return {
            "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": f":x: Error: {str(e)}"}}],
            "text": f"Error: {str(e)}"
        }


# Interactive action handlers
def handle_generate_query_action(body: Dict[str, Any], client) -> None:
    """Handle Generate Query button click."""
    channel = body["channel"]["id"]
    user = body["user"]["id"]

    # Get note text from button value or message
    note_text = body.get("actions", [{}])[0].get("value", "")

    if not note_text:
        client.chat_postMessage(
            channel=channel,
            text=":warning: Unable to retrieve note text. Please use `/cdi-query` command."
        )
        return

    handle_generate_query({"text": note_text, "channel_id": channel, "user_id": user}, client)


def handle_view_codes_action(body: Dict[str, Any], client) -> None:
    """Handle View Codes button click."""
    channel = body["channel"]["id"]
    note_text = body.get("actions", [{}])[0].get("value", "")

    result = _search_codes(note_text[:100])  # Use first 100 chars as search

    client.chat_postMessage(
        channel=channel,
        blocks=result["blocks"],
        text=result["text"]
    )


def handle_revenue_details_action(body: Dict[str, Any], client) -> None:
    """Handle Revenue Details button click."""
    channel = body["channel"]["id"]
    user = body["user"]["id"]

    handle_revenue_analysis(
        {"text": "Show revenue analysis", "channel_id": channel, "user_id": user},
        client
    )
