"""
Infrastructure Layer - External Dependencies

This layer handles all external dependencies and I/O operations.
Domain layer depends on abstractions defined here, not concrete implementations.

Modules:
    - db: Database connections, models, repositories
    - llm: LLM engine implementations (Claude, OpenAI, local)
    - config: Configuration management
    - logging: Structured logging
"""

__version__ = "2.0.0"
