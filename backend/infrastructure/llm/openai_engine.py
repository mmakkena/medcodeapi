"""
OpenAI GPT LLM Engine

Implementation of the LLM engine interface for OpenAI's GPT models.
This serves as a fallback when Claude is unavailable.
"""

import json
import logging
from typing import List, Optional, Dict, Any, AsyncIterator

from infrastructure.llm.base_engine import (
    BaseLLMEngine,
    LLMProvider,
    LLMResponse,
    Message,
)
from infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

# Default model
DEFAULT_MODEL = "gpt-4-turbo-preview"

# System prompts
CDI_SYSTEM_PROMPT = """You are an expert Clinical Documentation Integrity (CDI) specialist assistant.
Your role is to analyze clinical documentation and provide accurate, evidence-based guidance for:
- Documentation gap identification
- ICD-10 and CPT code suggestions
- CDI query generation for physicians
- Revenue optimization through accurate coding
- HEDIS quality measure evaluation

Always provide clinically accurate, non-leading responses that support documentation improvement
without suggesting diagnoses that aren't clearly documented."""


class OpenAIEngine(BaseLLMEngine):
    """
    OpenAI GPT LLM engine implementation.

    Uses the OpenAI Python SDK for API calls.
    Serves as a fallback when Anthropic is unavailable.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: int = 60,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the OpenAI engine.

        Args:
            model: GPT model ID (e.g., "gpt-4-turbo-preview")
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
            api_key: API key (defaults to settings.OPENAI_API_KEY if available)
        """
        super().__init__(model, temperature, max_tokens, timeout)

        self.api_key = api_key or getattr(settings, 'OPENAI_API_KEY', None)
        self._client = None

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.OPENAI

    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            if not self.api_key:
                raise RuntimeError(
                    "OpenAI API key not configured. "
                    "Set OPENAI_API_KEY in settings."
                )
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    timeout=self.timeout
                )
            except ImportError:
                raise RuntimeError(
                    "openai package not installed. "
                    "Install with: pip install openai"
                )
        return self._client

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
    ) -> LLMResponse:
        """Generate text from a prompt using GPT."""
        client = self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature if temperature is not None else self.temperature,
                stop=stop_sequences,
            )

            choice = response.choices[0]

            return LLMResponse(
                content=choice.message.content,
                model=self.model,
                provider=self.provider,
                usage={
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                },
                finish_reason=choice.finish_reason,
                metadata={
                    "response_id": response.id,
                }
            )

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise RuntimeError(f"OpenAI API request failed: {e}")

    async def generate_with_context(
        self,
        query: str,
        context_documents: List[str],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        """Generate text with RAG context documents."""
        formatted_prompt = self.format_rag_prompt(query, context_documents)

        rag_system = """You are a knowledgeable assistant that answers questions based on the provided context.
Always ground your responses in the context documents provided.
If the context doesn't contain enough information to answer, say so clearly."""

        return await self.generate(
            prompt=formatted_prompt,
            system_prompt=system_prompt or rag_system,
            temperature=temperature,
        )

    async def chat(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Multi-turn chat conversation."""
        client = self._get_client()

        # Build messages list
        openai_messages = []
        if system_prompt:
            openai_messages.append({"role": "system", "content": system_prompt})

        openai_messages.extend([
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ])

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature if temperature is not None else self.temperature,
            )

            choice = response.choices[0]

            return LLMResponse(
                content=choice.message.content,
                model=self.model,
                provider=self.provider,
                usage={
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                },
                finish_reason=choice.finish_reason,
            )

        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            raise RuntimeError(f"OpenAI chat request failed: {e}")

    async def extract_structured(
        self,
        text: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Extract structured data using GPT's JSON mode."""
        client = self._get_client()

        extraction_prompt = f"""Extract information from the following text and return it as JSON matching this schema:

SCHEMA:
{json.dumps(schema, indent=2)}

TEXT:
{text}

Return ONLY valid JSON matching the schema."""

        system = system_prompt or "You are a precise data extraction assistant. Return only valid JSON."

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": extraction_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.1,
                response_format={"type": "json_object"},  # Enable JSON mode
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from OpenAI response: {e}")
            raise ValueError(f"Failed to extract structured data: {e}")
        except Exception as e:
            logger.error(f"OpenAI extraction error: {e}")
            raise RuntimeError(f"OpenAI extraction request failed: {e}")

    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Stream generated text."""
        client = self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            stream = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature if temperature is not None else self.temperature,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise RuntimeError(f"OpenAI streaming request failed: {e}")


# Factory function
def get_openai_engine(
    model: str = DEFAULT_MODEL,
    **kwargs
) -> OpenAIEngine:
    """
    Get an OpenAI engine instance.

    Args:
        model: GPT model ID
        **kwargs: Additional engine parameters

    Returns:
        Configured OpenAIEngine instance
    """
    return OpenAIEngine(model=model, **kwargs)
