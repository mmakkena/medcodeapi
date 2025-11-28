"""
Slack CDI Bot Implementation

Main bot class that handles Slack events, slash commands, and interactive components.
Uses the Slack Bolt framework for Python.

Usage:
    from adapters.slack import SlackCDIBot

    bot = SlackCDIBot()
    bot.start()  # Starts the bot in socket mode

Environment Variables:
    SLACK_BOT_TOKEN: Slack Bot User OAuth Token
    SLACK_APP_TOKEN: Slack App-Level Token (for Socket Mode)
    SLACK_SIGNING_SECRET: Slack Signing Secret
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SlackConfig:
    """Slack bot configuration."""
    bot_token: str
    app_token: Optional[str] = None
    signing_secret: Optional[str] = None

    @classmethod
    def from_env(cls) -> "SlackConfig":
        """Load configuration from environment variables."""
        return cls(
            bot_token=os.environ.get("SLACK_BOT_TOKEN", ""),
            app_token=os.environ.get("SLACK_APP_TOKEN"),
            signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
        )


class SlackCDIBot:
    """
    Slack bot for Clinical Documentation Improvement.

    Provides:
    - /cdi-analyze: Analyze clinical note for documentation gaps
    - /cdi-query: Generate CDI query for physicians
    - /cdi-code: Look up ICD-10/CPT codes
    - /cdi-revenue: Analyze revenue optimization opportunities

    Also handles:
    - Direct messages with clinical notes
    - Interactive message buttons/modals
    - Thread-based conversations
    """

    def __init__(self, config: Optional[SlackConfig] = None):
        """
        Initialize the Slack CDI Bot.

        Args:
            config: Bot configuration. If None, loads from environment.
        """
        self.config = config or SlackConfig.from_env()
        self._app = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of Slack app."""
        if self._initialized:
            return

        try:
            from slack_bolt import App
            from slack_bolt.adapter.socket_mode import SocketModeHandler
        except ImportError:
            raise ImportError(
                "slack-bolt not installed. Install with: pip install slack-bolt"
            )

        if not self.config.bot_token:
            raise ValueError("SLACK_BOT_TOKEN environment variable is required")

        self._app = App(
            token=self.config.bot_token,
            signing_secret=self.config.signing_secret,
        )

        self._register_commands()
        self._register_events()
        self._register_actions()
        self._initialized = True

    def _register_commands(self):
        """Register slash commands."""
        from adapters.slack.handlers import (
            handle_analyze_note,
            handle_generate_query,
            handle_code_lookup,
            handle_revenue_analysis,
        )

        @self._app.command("/cdi-analyze")
        def analyze_command(ack, command, client):
            ack()
            handle_analyze_note(command, client)

        @self._app.command("/cdi-query")
        def query_command(ack, command, client):
            ack()
            handle_generate_query(command, client)

        @self._app.command("/cdi-code")
        def code_command(ack, command, client):
            ack()
            handle_code_lookup(command, client)

        @self._app.command("/cdi-revenue")
        def revenue_command(ack, command, client):
            ack()
            handle_revenue_analysis(command, client)

    def _register_events(self):
        """Register event handlers."""

        @self._app.event("app_mention")
        def handle_mention(event, say, client):
            """Handle @mentions of the bot."""
            text = event.get("text", "")
            user = event.get("user")
            channel = event.get("channel")
            thread_ts = event.get("thread_ts") or event.get("ts")

            # Remove the bot mention from the text
            # Format: <@BOTID> actual text
            import re
            text = re.sub(r"<@[A-Z0-9]+>", "", text).strip()

            if not text:
                say(
                    text="Hi! I'm the CDI Assistant. I can help you with:\n"
                         "• Analyzing clinical notes for documentation gaps\n"
                         "• Generating CDI queries for physicians\n"
                         "• Looking up ICD-10 and CPT codes\n"
                         "• Identifying revenue optimization opportunities\n\n"
                         "Just paste a clinical note or ask me a question!",
                    thread_ts=thread_ts
                )
                return

            # Process as clinical note analysis
            self._process_message(text, channel, thread_ts, client)

        @self._app.event("message")
        def handle_dm(event, say, client):
            """Handle direct messages."""
            # Only respond to DMs (channel type 'im')
            if event.get("channel_type") != "im":
                return

            # Ignore bot messages
            if event.get("bot_id"):
                return

            text = event.get("text", "")
            channel = event.get("channel")
            thread_ts = event.get("thread_ts") or event.get("ts")

            self._process_message(text, channel, thread_ts, client)

    def _register_actions(self):
        """Register interactive component handlers."""

        @self._app.action("generate_query")
        def handle_generate_query_action(ack, body, client):
            """Handle 'Generate Query' button click."""
            ack()
            from adapters.slack.handlers import handle_generate_query_action
            handle_generate_query_action(body, client)

        @self._app.action("view_codes")
        def handle_view_codes_action(ack, body, client):
            """Handle 'View Suggested Codes' button click."""
            ack()
            from adapters.slack.handlers import handle_view_codes_action
            handle_view_codes_action(body, client)

        @self._app.action("revenue_details")
        def handle_revenue_details_action(ack, body, client):
            """Handle 'Revenue Details' button click."""
            ack()
            from adapters.slack.handlers import handle_revenue_details_action
            handle_revenue_details_action(body, client)

    def _process_message(
        self,
        text: str,
        channel: str,
        thread_ts: str,
        client
    ):
        """
        Process an incoming message and respond with CDI analysis.

        Args:
            text: Message text (clinical note or question)
            channel: Slack channel ID
            thread_ts: Thread timestamp for reply
            client: Slack client
        """
        from adapters.slack.handlers import process_clinical_note

        # Send "thinking" message
        response = client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=":hourglass_flowing_sand: Analyzing clinical note..."
        )

        try:
            # Process the note and get results
            result = process_clinical_note(text)

            # Update with results
            client.chat_update(
                channel=channel,
                ts=response["ts"],
                blocks=result["blocks"],
                text=result["text"]
            )

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            client.chat_update(
                channel=channel,
                ts=response["ts"],
                text=f":x: Sorry, I encountered an error: {str(e)}"
            )

    @property
    def app(self):
        """Get the Slack Bolt App instance."""
        self._ensure_initialized()
        return self._app

    def start(self, port: int = 3000):
        """
        Start the bot in Socket Mode.

        Args:
            port: Port for local server (used for OAuth redirects)
        """
        self._ensure_initialized()

        if not self.config.app_token:
            raise ValueError(
                "SLACK_APP_TOKEN environment variable is required for Socket Mode"
            )

        from slack_bolt.adapter.socket_mode import SocketModeHandler

        logger.info("Starting Slack CDI Bot in Socket Mode...")
        handler = SocketModeHandler(self._app, self.config.app_token)
        handler.start()

    def start_http(self, port: int = 3000):
        """
        Start the bot with HTTP server (for Events API).

        Args:
            port: Port to listen on
        """
        self._ensure_initialized()

        logger.info(f"Starting Slack CDI Bot HTTP server on port {port}...")
        self._app.start(port=port)


def create_slack_bot() -> SlackCDIBot:
    """Factory function to create a configured Slack bot."""
    return SlackCDIBot(SlackConfig.from_env())


# FastAPI integration for webhook handling
def create_slack_router():
    """
    Create a FastAPI router for Slack webhooks.

    Returns:
        FastAPI APIRouter with Slack webhook endpoints
    """
    from fastapi import APIRouter, Request
    from slack_bolt.adapter.fastapi import SlackRequestHandler

    router = APIRouter(prefix="/slack", tags=["slack"])
    bot = create_slack_bot()
    handler = SlackRequestHandler(bot.app)

    @router.post("/events")
    async def slack_events(request: Request):
        """Handle Slack Events API webhooks."""
        return await handler.handle(request)

    @router.post("/commands")
    async def slack_commands(request: Request):
        """Handle Slack slash commands."""
        return await handler.handle(request)

    @router.post("/interactions")
    async def slack_interactions(request: Request):
        """Handle Slack interactive components."""
        return await handler.handle(request)

    return router
