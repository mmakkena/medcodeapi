"""
LLM Infrastructure

LLM engine implementations for text generation and embeddings.
Supports Claude (primary), OpenAI (fallback), and local models.
"""

import logging
from typing import Optional

from infrastructure.llm.base_engine import (
    BaseLLMEngine,
    LLMProvider,
    LLMResponse,
    Message,
)
from infrastructure.llm.embedding_engine import (
    generate_embedding,
    generate_embeddings_batch,
    compute_similarity,
    find_most_similar,
    warmup_model,
    get_embedding_model,
)

logger = logging.getLogger(__name__)

# Global default engine
_default_engine: Optional[BaseLLMEngine] = None


def get_llm_engine(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> BaseLLMEngine:
    """
    Factory function to get an LLM engine.

    Args:
        provider: LLM provider ("anthropic", "openai", or None for default)
        model: Optional model override
        **kwargs: Additional engine parameters

    Returns:
        Configured LLM engine instance
    """
    from infrastructure.config.settings import settings

    # Determine provider
    if provider is None:
        # Default to Anthropic if API key is available
        if settings.ANTHROPIC_API_KEY:
            provider = "anthropic"
        elif getattr(settings, 'OPENAI_API_KEY', None):
            provider = "openai"
        else:
            raise RuntimeError(
                "No LLM API key configured. "
                "Set ANTHROPIC_API_KEY or OPENAI_API_KEY."
            )

    provider = provider.lower()

    if provider == "anthropic":
        from infrastructure.llm.anthropic_engine import AnthropicEngine
        return AnthropicEngine(model=model, **kwargs)
    elif provider == "openai":
        from infrastructure.llm.openai_engine import OpenAIEngine
        return OpenAIEngine(model=model, **kwargs)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def get_default_engine() -> BaseLLMEngine:
    """
    Get the default LLM engine (singleton).

    Returns:
        Default LLM engine instance (Anthropic Claude)
    """
    global _default_engine
    if _default_engine is None:
        _default_engine = get_llm_engine()
    return _default_engine


async def generate_text(
    prompt: str,
    system_prompt: Optional[str] = None,
    **kwargs
) -> str:
    """
    Convenience function to generate text using the default engine.

    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        **kwargs: Additional parameters

    Returns:
        Generated text content
    """
    engine = get_default_engine()
    response = await engine.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        **kwargs
    )
    return response.content


async def generate_with_context(
    query: str,
    context_documents: list,
    **kwargs
) -> str:
    """
    Convenience function for RAG generation.

    Args:
        query: User query
        context_documents: Context documents
        **kwargs: Additional parameters

    Returns:
        Generated text grounded in context
    """
    engine = get_default_engine()
    response = await engine.generate_with_context(
        query=query,
        context_documents=context_documents,
        **kwargs
    )
    return response.content


__all__ = [
    # Base classes
    "BaseLLMEngine",
    "LLMProvider",
    "LLMResponse",
    "Message",
    # Factory functions
    "get_llm_engine",
    "get_default_engine",
    # Convenience functions
    "generate_text",
    "generate_with_context",
    # Embedding functions
    "generate_embedding",
    "generate_embeddings_batch",
    "compute_similarity",
    "find_most_similar",
    "warmup_model",
    "get_embedding_model",
]
