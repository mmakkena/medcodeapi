"""
Anthropic Claude LLM Engine

Implementation of the LLM engine interface for Anthropic's Claude models.
This is the primary LLM engine for the CDI Agent.
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

# Default system prompts for CDI use cases
CDI_SYSTEM_PROMPT = """You are an expert Clinical Documentation Integrity (CDI) specialist assistant.
Your role is to analyze clinical documentation and provide accurate, evidence-based guidance for:
- Documentation gap identification
- ICD-10 and CPT code suggestions
- CDI query generation for physicians
- Revenue optimization through accurate coding
- HEDIS quality measure evaluation

Always provide clinically accurate, non-leading responses that support documentation improvement
without suggesting diagnoses that aren't clearly documented."""

RAG_SYSTEM_PROMPT = """You are a knowledgeable assistant that answers questions based on the provided context.
Always ground your responses in the context documents provided.
If the context doesn't contain enough information to answer, say so clearly.
Do not make up information or hallucinate facts not present in the context."""


class AnthropicEngine(BaseLLMEngine):
    """
    Anthropic Claude LLM engine implementation.

    Uses the Anthropic Python SDK for API calls.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: int = 60,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the Anthropic engine.

        Args:
            model: Claude model ID (defaults to settings.CLAUDE_MODEL)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
            api_key: API key (defaults to settings.ANTHROPIC_API_KEY)
        """
        model = model or settings.CLAUDE_MODEL
        super().__init__(model, temperature, max_tokens, timeout)

        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self._client = None

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.ANTHROPIC

    def _get_client(self):
        """Lazy initialization of Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(
                    api_key=self.api_key,
                    timeout=self.timeout
                )
            except ImportError:
                raise RuntimeError(
                    "anthropic package not installed. "
                    "Install with: pip install anthropic"
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
        """Generate text from a prompt using Claude."""
        client = self._get_client()

        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature if temperature is not None else self.temperature,
                system=system_prompt or CDI_SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                stop_sequences=stop_sequences,
            )

            return LLMResponse(
                content=message.content[0].text,
                model=self.model,
                provider=self.provider,
                usage={
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens,
                },
                finish_reason=message.stop_reason,
                metadata={
                    "message_id": message.id,
                }
            )

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise RuntimeError(f"Claude API request failed: {e}")

    async def generate_with_context(
        self,
        query: str,
        context_documents: List[str],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        """Generate text with RAG context documents."""
        # Format the RAG prompt
        formatted_prompt = self.format_rag_prompt(query, context_documents)

        return await self.generate(
            prompt=formatted_prompt,
            system_prompt=system_prompt or RAG_SYSTEM_PROMPT,
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

        # Convert Message objects to Anthropic format
        anthropic_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature if temperature is not None else self.temperature,
                system=system_prompt or CDI_SYSTEM_PROMPT,
                messages=anthropic_messages,
            )

            return LLMResponse(
                content=message.content[0].text,
                model=self.model,
                provider=self.provider,
                usage={
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens,
                },
                finish_reason=message.stop_reason,
            )

        except Exception as e:
            logger.error(f"Anthropic chat error: {e}")
            raise RuntimeError(f"Claude chat request failed: {e}")

    async def extract_structured(
        self,
        text: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Extract structured data from text according to a schema."""
        extraction_prompt = f"""Extract information from the following text and return it as JSON matching this schema:

SCHEMA:
{json.dumps(schema, indent=2)}

TEXT:
{text}

Return ONLY valid JSON matching the schema. Do not include any other text."""

        system = system_prompt or "You are a precise data extraction assistant. Return only valid JSON."

        response = await self.generate(
            prompt=extraction_prompt,
            system_prompt=system,
            temperature=0.1,  # Low temperature for consistent extraction
        )

        # Parse JSON from response
        try:
            # Try to find JSON in response
            content = response.content.strip()

            # Handle markdown code blocks
            if content.startswith("```"):
                lines = content.split("\n")
                # Remove first and last lines (code block markers)
                content = "\n".join(lines[1:-1])

            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Claude response: {e}")
            logger.debug(f"Response content: {response.content}")
            raise ValueError(f"Failed to extract structured data: {e}")

    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Stream generated text."""
        client = self._get_client()

        try:
            with client.messages.stream(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature if temperature is not None else self.temperature,
                system=system_prompt or CDI_SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            ) as stream:
                for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            raise RuntimeError(f"Claude streaming request failed: {e}")

    # CDI-specific methods

    async def analyze_clinical_note(
        self,
        note_text: str,
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Analyze a clinical note for CDI purposes.

        Args:
            note_text: Clinical note text
            analysis_type: Type of analysis (comprehensive, gaps, codes, hedis)

        Returns:
            Analysis results dictionary
        """
        schema = {
            "type": "object",
            "properties": {
                "findings": {"type": "array", "items": {"type": "string"}},
                "documentation_gaps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "description": {"type": "string"},
                            "severity": {"type": "string", "enum": ["high", "medium", "low"]}
                        }
                    }
                },
                "suggested_codes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                            "description": {"type": "string"},
                            "confidence": {"type": "number"}
                        }
                    }
                },
                "entities": {
                    "type": "object",
                    "properties": {
                        "diagnoses": {"type": "array", "items": {"type": "string"}},
                        "medications": {"type": "array", "items": {"type": "string"}},
                        "procedures": {"type": "array", "items": {"type": "string"}},
                        "labs": {"type": "array", "items": {"type": "string"}}
                    }
                }
            }
        }

        prompt = f"""Analyze this clinical note for documentation quality and coding opportunities:

CLINICAL NOTE:
{note_text}

Identify:
1. Key clinical findings
2. Documentation gaps (missing specificity, acuity, etc.)
3. Suggested ICD-10/CPT codes
4. Clinical entities (diagnoses, medications, procedures, labs)"""

        return await self.extract_structured(
            text=prompt,
            schema=schema,
            system_prompt=CDI_SYSTEM_PROMPT
        )

    async def generate_cdi_query(
        self,
        note_text: str,
        gap_description: Optional[str] = None
    ) -> str:
        """
        Generate a CDI query for physicians.

        Args:
            note_text: Clinical note text
            gap_description: Optional description of specific gap to address

        Returns:
            Non-leading physician query
        """
        prompt = f"""Generate a professional, non-leading CDI query for the physician based on this clinical note.

CLINICAL NOTE:
{note_text}
"""

        if gap_description:
            prompt += f"\nSPECIFIC GAP TO ADDRESS: {gap_description}\n"

        prompt += """
The query should:
- Be non-leading (not suggest a specific diagnosis)
- Request clarification or additional documentation
- Be professionally worded
- Reference the relevant clinical findings

Return ONLY the query text, nothing else."""

        response = await self.generate(
            prompt=prompt,
            system_prompt=CDI_SYSTEM_PROMPT,
            temperature=0.5,  # Moderate temperature for consistent queries
        )

        return response.content.strip()


# Factory function for easy instantiation
def get_anthropic_engine(
    model: Optional[str] = None,
    **kwargs
) -> AnthropicEngine:
    """
    Get an Anthropic engine instance.

    Args:
        model: Optional model override
        **kwargs: Additional engine parameters

    Returns:
        Configured AnthropicEngine instance
    """
    return AnthropicEngine(model=model, **kwargs)
