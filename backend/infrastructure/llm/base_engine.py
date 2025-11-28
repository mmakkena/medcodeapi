"""
Base LLM Engine Interface

Abstract base class defining the interface for LLM engines.
All LLM implementations (Claude, OpenAI, local) must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncIterator
from dataclasses import dataclass
from enum import Enum


class LLMProvider(Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    LOCAL = "local"


@dataclass
class LLMResponse:
    """Response from an LLM engine."""
    content: str
    model: str
    provider: LLMProvider
    usage: Optional[Dict[str, int]] = None  # tokens used
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Message:
    """Chat message for conversation history."""
    role: str  # "user", "assistant", "system"
    content: str


class BaseLLMEngine(ABC):
    """
    Abstract base class for LLM engines.

    All LLM implementations must implement these methods to ensure
    consistent behavior across different providers.
    """

    def __init__(
        self,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: int = 60
    ):
        """
        Initialize the LLM engine.

        Args:
            model: Model identifier (e.g., "claude-3-5-sonnet-20241022")
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    @property
    @abstractmethod
    def provider(self) -> LLMProvider:
        """Return the LLM provider type."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
    ) -> LLMResponse:
        """
        Generate text from a prompt.

        Args:
            prompt: User prompt text
            system_prompt: Optional system instructions
            temperature: Override default temperature
            max_tokens: Override default max tokens
            stop_sequences: Optional stop sequences

        Returns:
            LLMResponse with generated content
        """
        pass

    @abstractmethod
    async def generate_with_context(
        self,
        query: str,
        context_documents: List[str],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        """
        Generate text with RAG context documents.

        Args:
            query: User query
            context_documents: List of context documents for RAG
            system_prompt: Optional system instructions
            temperature: Override default temperature

        Returns:
            LLMResponse with generated content grounded in context
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Multi-turn chat conversation.

        Args:
            messages: List of conversation messages
            system_prompt: Optional system instructions
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            LLMResponse with assistant's reply
        """
        pass

    @abstractmethod
    async def extract_structured(
        self,
        text: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract structured data from text according to a schema.

        Args:
            text: Input text to extract from
            schema: JSON schema defining expected output structure
            system_prompt: Optional system instructions

        Returns:
            Dictionary matching the provided schema
        """
        pass

    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """
        Stream generated text (optional implementation).

        Args:
            prompt: User prompt text
            system_prompt: Optional system instructions
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Yields:
            Text chunks as they are generated
        """
        # Default implementation: no streaming, yield full response
        response = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        yield response.content

    def format_rag_prompt(
        self,
        query: str,
        context_documents: List[str],
        instruction: Optional[str] = None
    ) -> str:
        """
        Format a RAG prompt with context documents.

        Args:
            query: User query
            context_documents: List of context documents
            instruction: Optional additional instruction

        Returns:
            Formatted prompt string
        """
        context_text = "\n\n---\n\n".join(context_documents)

        prompt = f"""Based on the following context documents, answer the question.

CONTEXT:
{context_text}

QUESTION: {query}
"""

        if instruction:
            prompt = f"{instruction}\n\n{prompt}"

        return prompt

    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the LLM engine is operational.

        Returns:
            Dictionary with health status
        """
        try:
            response = await self.generate(
                prompt="Say 'OK' if you can read this.",
                max_tokens=10
            )
            return {
                "status": "healthy",
                "provider": self.provider.value,
                "model": self.model,
                "response": response.content[:50]
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.provider.value,
                "model": self.model,
                "error": str(e)
            }
