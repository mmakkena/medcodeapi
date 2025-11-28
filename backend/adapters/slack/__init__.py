"""
Slack Bot Adapter for CDI Agent

Provides Slack integration for clinical documentation improvement workflows.
Supports slash commands, interactive messages, and event handling.
"""

from adapters.slack.bot import SlackCDIBot
from adapters.slack.handlers import (
    handle_analyze_note,
    handle_generate_query,
    handle_code_lookup,
    handle_revenue_analysis,
)

__all__ = [
    "SlackCDIBot",
    "handle_analyze_note",
    "handle_generate_query",
    "handle_code_lookup",
    "handle_revenue_analysis",
]
