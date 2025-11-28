"""
Microsoft Teams CDI Bot Implementation

Bot class that handles Teams messages, adaptive cards, and messaging extensions.
Uses the Microsoft Bot Framework SDK for Python.

Usage:
    from adapters.teams import TeamsCDIBot

    bot = TeamsCDIBot()
    # Use with FastAPI or aiohttp

Environment Variables:
    TEAMS_APP_ID: Microsoft App ID
    TEAMS_APP_PASSWORD: Microsoft App Password
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TeamsConfig:
    """Teams bot configuration."""
    app_id: str
    app_password: str

    @classmethod
    def from_env(cls) -> "TeamsConfig":
        """Load configuration from environment variables."""
        return cls(
            app_id=os.environ.get("TEAMS_APP_ID", ""),
            app_password=os.environ.get("TEAMS_APP_PASSWORD", ""),
        )


class TeamsCDIBot:
    """
    Microsoft Teams bot for Clinical Documentation Improvement.

    Provides:
    - Message handling for clinical notes
    - Adaptive Card responses with rich formatting
    - Messaging extension for code lookup
    - Proactive messaging capabilities

    Commands (via @mention or direct message):
    - "analyze <note>": Analyze clinical note
    - "query <condition>": Generate CDI query
    - "code <code/term>": Look up medical codes
    - "revenue <note>": Revenue analysis
    """

    def __init__(self, config: Optional[TeamsConfig] = None):
        """
        Initialize the Teams CDI Bot.

        Args:
            config: Bot configuration. If None, loads from environment.
        """
        self.config = config or TeamsConfig.from_env()
        self._adapter = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of Bot Framework adapter."""
        if self._initialized:
            return

        try:
            from botbuilder.core import (
                BotFrameworkAdapter,
                BotFrameworkAdapterSettings,
                TurnContext,
            )
            from botbuilder.schema import Activity, ActivityTypes
        except ImportError:
            raise ImportError(
                "botbuilder-core not installed. Install with: "
                "pip install botbuilder-core botbuilder-schema"
            )

        settings = BotFrameworkAdapterSettings(
            app_id=self.config.app_id,
            app_password=self.config.app_password,
        )
        self._adapter = BotFrameworkAdapter(settings)
        self._initialized = True

    @property
    def adapter(self):
        """Get the Bot Framework adapter."""
        self._ensure_initialized()
        return self._adapter

    async def on_turn(self, turn_context) -> None:
        """
        Handle incoming activity from Teams.

        Args:
            turn_context: Bot Framework turn context
        """
        from botbuilder.schema import ActivityTypes

        if turn_context.activity.type == ActivityTypes.message:
            await self._handle_message(turn_context)
        elif turn_context.activity.type == ActivityTypes.invoke:
            await self._handle_invoke(turn_context)
        elif turn_context.activity.type == ActivityTypes.conversation_update:
            await self._handle_conversation_update(turn_context)

    async def _handle_message(self, turn_context) -> None:
        """Handle incoming message."""
        text = turn_context.activity.text or ""

        # Remove bot mention if present
        text = self._remove_mention(text, turn_context)

        # Parse command
        command, args = self._parse_command(text)

        # Send typing indicator
        await turn_context.send_activity(
            Activity(type=ActivityTypes.typing)
        )

        try:
            if command == "analyze":
                await self._cmd_analyze(turn_context, args)
            elif command == "query":
                await self._cmd_query(turn_context, args)
            elif command == "code":
                await self._cmd_code(turn_context, args)
            elif command == "revenue":
                await self._cmd_revenue(turn_context, args)
            elif command == "help":
                await self._cmd_help(turn_context)
            else:
                # Default: treat as clinical note analysis
                if text.strip():
                    await self._cmd_analyze(turn_context, text)
                else:
                    await self._cmd_help(turn_context)

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await turn_context.send_activity(
                f"Sorry, I encountered an error: {str(e)}"
            )

    def _remove_mention(self, text: str, turn_context) -> str:
        """Remove bot mention from message text."""
        if turn_context.activity.entities:
            for entity in turn_context.activity.entities:
                if entity.type == "mention":
                    mention_text = entity.text
                    text = text.replace(mention_text, "").strip()
        return text

    def _parse_command(self, text: str) -> tuple:
        """Parse command and arguments from text."""
        text = text.strip()
        if not text:
            return ("help", "")

        parts = text.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        known_commands = ["analyze", "query", "code", "revenue", "help"]
        if command not in known_commands:
            return ("analyze", text)

        return (command, args)

    async def _cmd_analyze(self, turn_context, text: str) -> None:
        """Handle analyze command."""
        if not text:
            await turn_context.send_activity(
                "Please provide a clinical note to analyze.\n"
                "Example: `analyze Patient presents with chest pain...`"
            )
            return

        try:
            result = self._process_clinical_note(text)
            card = self._create_analysis_card(result)
            await turn_context.send_activity(
                Activity(
                    type=ActivityTypes.message,
                    attachments=[card]
                )
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            await turn_context.send_activity(f"Error analyzing note: {str(e)}")

    async def _cmd_query(self, turn_context, text: str) -> None:
        """Handle query command."""
        if not text:
            await turn_context.send_activity(
                "Please provide a condition or gap for query generation.\n"
                "Example: `query diabetes specificity`"
            )
            return

        try:
            from domain.query_generation import CDIQueryGenerator

            generator = CDIQueryGenerator()
            result = generator.generate_condition_query(text)

            card = self._create_query_card(result, text)
            await turn_context.send_activity(
                Activity(
                    type=ActivityTypes.message,
                    attachments=[card]
                )
            )
        except ImportError:
            await turn_context.send_activity(
                f"**CDI Query for: {text}**\n\n"
                "_Query generation requires domain layer configuration._"
            )
        except Exception as e:
            await turn_context.send_activity(f"Error generating query: {str(e)}")

    async def _cmd_code(self, turn_context, text: str) -> None:
        """Handle code lookup command."""
        if not text:
            await turn_context.send_activity(
                "Please provide a code or search term.\n"
                "Examples:\n"
                "- `code I10` - Look up ICD-10 code\n"
                "- `code hypertension` - Search for codes"
            )
            return

        try:
            result = self._lookup_or_search_code(text)
            card = self._create_code_card(result, text)
            await turn_context.send_activity(
                Activity(
                    type=ActivityTypes.message,
                    attachments=[card]
                )
            )
        except Exception as e:
            await turn_context.send_activity(f"Error looking up code: {str(e)}")

    async def _cmd_revenue(self, turn_context, text: str) -> None:
        """Handle revenue analysis command."""
        if not text:
            await turn_context.send_activity(
                "Please provide a clinical note or diagnosis list.\n"
                "Example: `revenue Patient with diabetes, CHF, and COPD`"
            )
            return

        try:
            from domain.revenue_optimization import RevenueOptimizer

            optimizer = RevenueOptimizer()
            result = optimizer.analyze(text)

            card = self._create_revenue_card(result)
            await turn_context.send_activity(
                Activity(
                    type=ActivityTypes.message,
                    attachments=[card]
                )
            )
        except ImportError:
            await turn_context.send_activity(
                "**Revenue Analysis**\n\n"
                "_Revenue optimization requires domain layer configuration._"
            )
        except Exception as e:
            await turn_context.send_activity(f"Error in revenue analysis: {str(e)}")

    async def _cmd_help(self, turn_context) -> None:
        """Send help message."""
        card = self._create_help_card()
        await turn_context.send_activity(
            Activity(
                type=ActivityTypes.message,
                attachments=[card]
            )
        )

    def _process_clinical_note(self, text: str) -> Dict[str, Any]:
        """Process clinical note and return analysis results."""
        try:
            from domain.entity_extraction import ClinicalEntityExtractor
            from domain.documentation_gaps import DocumentationGapAnalyzer

            extractor = ClinicalEntityExtractor()
            entities = extractor.extract(text)

            analyzer = DocumentationGapAnalyzer()
            gap_analysis = analyzer.analyze(entities=entities)

            return {
                "entities": entities,
                "gaps": gap_analysis,
                "success": True
            }
        except ImportError:
            return self._simple_analysis(text)

    def _simple_analysis(self, text: str) -> Dict[str, Any]:
        """Provide simplified analysis when domain layer unavailable."""
        keywords = {
            "sepsis": ["sepsis", "septic"],
            "heart_failure": ["heart failure", "chf"],
            "pneumonia": ["pneumonia", "pna"],
            "diabetes": ["diabetes", "dm"],
        }

        text_lower = text.lower()
        detected = []

        for condition, terms in keywords.items():
            if any(term in text_lower for term in terms):
                detected.append(condition.replace("_", " ").title())

        return {
            "conditions": detected,
            "success": True,
            "simplified": True
        }

    def _lookup_or_search_code(self, text: str) -> Dict[str, Any]:
        """Look up or search for medical codes."""
        import re

        # Check if it looks like a code
        code_patterns = [
            r'^[A-Z]\d{2}(\.\d{1,4})?$',
            r'^\d{5}$',
            r'^[A-Z]\d{4}$',
        ]
        is_code = any(re.match(p, text.upper().strip()) for p in code_patterns)

        try:
            from infrastructure.db.postgres import SessionLocal
            from infrastructure.db.models import ICD10Code, ProcedureCode

            db = SessionLocal()
            try:
                if is_code:
                    # Direct lookup
                    code_upper = text.upper().strip()
                    icd = db.query(ICD10Code).filter(ICD10Code.code == code_upper).first()
                    if icd:
                        return {"type": "icd10", "code": icd.code, "description": icd.description}

                    proc = db.query(ProcedureCode).filter(ProcedureCode.code == code_upper).first()
                    if proc:
                        return {"type": proc.code_system, "code": proc.code, "description": proc.description}

                    return {"type": "not_found", "query": code_upper}
                else:
                    # Search
                    icd_results = db.query(ICD10Code).filter(
                        ICD10Code.description.ilike(f"%{text}%")
                    ).limit(5).all()

                    proc_results = db.query(ProcedureCode).filter(
                        ProcedureCode.description.ilike(f"%{text}%")
                    ).limit(5).all()

                    return {
                        "type": "search",
                        "query": text,
                        "icd_results": [{"code": r.code, "description": r.description} for r in icd_results],
                        "proc_results": [{"code": r.code, "description": r.description} for r in proc_results]
                    }
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error in code lookup: {e}")
            return {"type": "error", "message": str(e)}

    # Adaptive Card creation methods

    def _create_analysis_card(self, result: Dict[str, Any]):
        """Create Adaptive Card for analysis results."""
        from botbuilder.schema import Attachment

        body = [
            {
                "type": "TextBlock",
                "text": "CDI Analysis Results",
                "weight": "bolder",
                "size": "large"
            }
        ]

        if result.get("simplified"):
            conditions = result.get("conditions", [])
            body.append({
                "type": "TextBlock",
                "text": f"**Conditions Detected:** {', '.join(conditions) if conditions else 'None identified'}",
                "wrap": True
            })
        else:
            entities = result.get("entities")
            gaps = result.get("gaps")

            if hasattr(entities, 'conditions') and entities.conditions:
                cond_text = ", ".join([c.name for c in entities.conditions[:5]])
                body.append({
                    "type": "TextBlock",
                    "text": f"**Conditions:** {cond_text}",
                    "wrap": True
                })

            if hasattr(gaps, 'gaps') and gaps.gaps:
                for gap in gaps.gaps[:3]:
                    body.append({
                        "type": "TextBlock",
                        "text": f"⚠️ {gap.description}",
                        "wrap": True,
                        "color": "warning"
                    })

        # Action buttons
        body.append({
            "type": "ActionSet",
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Generate Query",
                    "data": {"action": "generate_query"}
                },
                {
                    "type": "Action.Submit",
                    "title": "Revenue Analysis",
                    "data": {"action": "revenue"}
                }
            ]
        })

        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": body
        }

        return Attachment(
            content_type="application/vnd.microsoft.card.adaptive",
            content=card
        )

    def _create_query_card(self, result, condition: str):
        """Create Adaptive Card for CDI query."""
        from botbuilder.schema import Attachment

        query_text = getattr(result, 'query_text', str(result)) if result else "Query unavailable"
        rationale = getattr(result, 'rationale', '') if result else ""

        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "📝 CDI Query",
                    "weight": "bolder",
                    "size": "large"
                },
                {
                    "type": "TextBlock",
                    "text": f"**Condition:** {condition}",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": query_text,
                    "wrap": True,
                    "fontType": "monospace"
                }
            ]
        }

        if rationale:
            card["body"].append({
                "type": "TextBlock",
                "text": f"_Rationale: {rationale}_",
                "wrap": True,
                "isSubtle": True
            })

        return Attachment(
            content_type="application/vnd.microsoft.card.adaptive",
            content=card
        )

    def _create_code_card(self, result: Dict[str, Any], query: str):
        """Create Adaptive Card for code lookup results."""
        from botbuilder.schema import Attachment

        body = [
            {
                "type": "TextBlock",
                "text": f"🔍 Code Lookup: {query}",
                "weight": "bolder",
                "size": "large"
            }
        ]

        if result.get("type") == "not_found":
            body.append({
                "type": "TextBlock",
                "text": f"Code '{result['query']}' not found",
                "color": "warning"
            })
        elif result.get("type") in ["icd10", "CPT", "HCPCS"]:
            body.append({
                "type": "FactSet",
                "facts": [
                    {"title": "Code", "value": result["code"]},
                    {"title": "Type", "value": result["type"]},
                    {"title": "Description", "value": result["description"]}
                ]
            })
        elif result.get("type") == "search":
            icd = result.get("icd_results", [])
            proc = result.get("proc_results", [])

            if icd:
                body.append({"type": "TextBlock", "text": "**ICD-10 Results:**", "weight": "bolder"})
                for r in icd:
                    body.append({
                        "type": "TextBlock",
                        "text": f"• `{r['code']}` - {r['description'][:50]}...",
                        "wrap": True
                    })

            if proc:
                body.append({"type": "TextBlock", "text": "**CPT/HCPCS Results:**", "weight": "bolder"})
                for r in proc:
                    body.append({
                        "type": "TextBlock",
                        "text": f"• `{r['code']}` - {r['description'][:50]}...",
                        "wrap": True
                    })

            if not icd and not proc:
                body.append({
                    "type": "TextBlock",
                    "text": f"No codes found for '{query}'",
                    "color": "warning"
                })

        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": body
        }

        return Attachment(
            content_type="application/vnd.microsoft.card.adaptive",
            content=card
        )

    def _create_revenue_card(self, result):
        """Create Adaptive Card for revenue analysis."""
        from botbuilder.schema import Attachment

        body = [
            {
                "type": "TextBlock",
                "text": "📈 Revenue Analysis",
                "weight": "bolder",
                "size": "large"
            }
        ]

        if hasattr(result, 'total_opportunity'):
            body.append({
                "type": "TextBlock",
                "text": f"**Potential Impact:** ${result.total_opportunity:,.2f}",
                "size": "medium",
                "color": "good"
            })

        if hasattr(result, 'opportunities') and result.opportunities:
            for opp in result.opportunities[:3]:
                body.append({
                    "type": "TextBlock",
                    "text": f"• **{opp.condition}**: {opp.description}",
                    "wrap": True
                })

        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": body
        }

        return Attachment(
            content_type="application/vnd.microsoft.card.adaptive",
            content=card
        )

    def _create_help_card(self):
        """Create Adaptive Card for help message."""
        from botbuilder.schema import Attachment

        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "🏥 CDI Assistant",
                    "weight": "bolder",
                    "size": "large"
                },
                {
                    "type": "TextBlock",
                    "text": "I can help you with clinical documentation improvement:",
                    "wrap": True
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {"title": "analyze", "value": "Analyze clinical note for gaps"},
                        {"title": "query", "value": "Generate CDI query for physicians"},
                        {"title": "code", "value": "Look up ICD-10/CPT codes"},
                        {"title": "revenue", "value": "Analyze revenue opportunities"},
                        {"title": "help", "value": "Show this help message"}
                    ]
                },
                {
                    "type": "TextBlock",
                    "text": "💡 **Tip:** Just paste a clinical note and I'll analyze it automatically!",
                    "wrap": True,
                    "isSubtle": True
                }
            ]
        }

        return Attachment(
            content_type="application/vnd.microsoft.card.adaptive",
            content=card
        )

    async def _handle_invoke(self, turn_context) -> None:
        """Handle invoke activities (messaging extensions, card actions)."""
        invoke_name = turn_context.activity.name

        if invoke_name == "composeExtension/query":
            await self._handle_messaging_extension(turn_context)
        elif invoke_name == "adaptiveCard/action":
            await self._handle_card_action(turn_context)

    async def _handle_messaging_extension(self, turn_context) -> None:
        """Handle messaging extension queries."""
        from botbuilder.schema.teams import MessagingExtensionResponse

        query = turn_context.activity.value.get("queryOptions", {}).get("query", "")
        results = self._lookup_or_search_code(query)

        # Format as messaging extension results
        attachments = []
        # ... format results as hero cards

        response = MessagingExtensionResponse(
            compose_extension={"type": "result", "attachmentLayout": "list", "attachments": attachments}
        )
        await turn_context.send_activity(response)

    async def _handle_card_action(self, turn_context) -> None:
        """Handle adaptive card action submissions."""
        action = turn_context.activity.value.get("action")

        if action == "generate_query":
            await self._cmd_query(turn_context, "")
        elif action == "revenue":
            await self._cmd_revenue(turn_context, "")

    async def _handle_conversation_update(self, turn_context) -> None:
        """Handle conversation updates (bot added to team, etc.)."""
        if turn_context.activity.members_added:
            for member in turn_context.activity.members_added:
                if member.id != turn_context.activity.recipient.id:
                    await turn_context.send_activity(
                        "Hello! I'm the CDI Assistant. "
                        "Type **help** to see what I can do."
                    )


def create_teams_bot() -> TeamsCDIBot:
    """Factory function to create a configured Teams bot."""
    return TeamsCDIBot(TeamsConfig.from_env())


# FastAPI integration
def create_teams_router():
    """
    Create a FastAPI router for Teams webhooks.

    Returns:
        FastAPI APIRouter with Teams webhook endpoint
    """
    from fastapi import APIRouter, Request, Response
    import json

    router = APIRouter(prefix="/teams", tags=["teams"])
    bot = create_teams_bot()

    @router.post("/messages")
    async def teams_messages(request: Request):
        """Handle Teams Bot Framework messages."""
        from botbuilder.schema import Activity

        body = await request.body()
        activity = Activity().deserialize(json.loads(body))

        auth_header = request.headers.get("Authorization", "")

        async def aux_func(turn_context):
            await bot.on_turn(turn_context)

        await bot.adapter.process_activity(activity, auth_header, aux_func)
        return Response(status_code=200)

    return router
