"""
Adapters Layer - Interface Adapters

This layer contains all interface adapters that consume the domain layer.
Each adapter transforms external requests into domain calls and formats
domain responses for external consumption.

Adapters:
    - api: REST API (FastAPI) for HTTP clients
    - mcp: MCP Server for LLM agent integration (Claude Desktop, VS Code)
    - slack: Slack bot for CDI workflows
    - teams: Microsoft Teams bot for CDI workflows
    - cli: Command-line interface (optional)
"""

__version__ = "2.0.0"

# Lazy imports to avoid dependency issues
def get_slack_bot():
    """Get Slack bot instance."""
    from adapters.slack import SlackCDIBot
    return SlackCDIBot()

def get_teams_bot():
    """Get Teams bot instance."""
    from adapters.teams import TeamsCDIBot
    return TeamsCDIBot()

def get_slack_router():
    """Get FastAPI router for Slack webhooks."""
    from adapters.slack.bot import create_slack_router
    return create_slack_router()

def get_teams_router():
    """Get FastAPI router for Teams webhooks."""
    from adapters.teams.bot import create_teams_router
    return create_teams_router()
