"""Application configuration management"""

import os
from pydantic_settings import BaseSettings
from typing import List, Optional
from infrastructure.config.parameter_store import get_parameter_store


class Settings(BaseSettings):
    """Application settings loaded from Parameter Store or environment variables"""

    # Application
    APP_NAME: str = "MedCode API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # AWS
    AWS_REGION: str = "us-east-2"
    USE_PARAMETER_STORE: bool = True

    # Security
    SECRET_KEY: Optional[str] = None
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: Optional[str] = None

    # Redis (optional - falls back to in-memory)
    REDIS_URL: Optional[str] = None

    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_DAY: int = 10000

    # API Keys
    API_KEY_PREFIX: str = "mk_"

    # Code Version Defaults
    DEFAULT_ICD10_VERSION_YEAR: int = 2026
    DEFAULT_PROCEDURE_VERSION_YEAR: int = 2025

    # Clinical Coding Configuration
    MAX_CODES_PER_TYPE: int = 20
    DEFAULT_CODES_PER_TYPE: int = 5
    DEFAULT_MIN_SIMILARITY: float = 0.7
    DEFAULT_SEMANTIC_WEIGHT: float = 0.7

    # LLM Configuration
    ANTHROPIC_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
    CLAUDE_MAX_TOKENS: int = 1024

    def __init__(self, **kwargs):
        """Initialize settings with Parameter Store support"""
        super().__init__(**kwargs)

        # Load from Parameter Store if enabled
        if self.USE_PARAMETER_STORE and self.ENVIRONMENT != "development":
            self._load_from_parameter_store()

        # Validate required settings
        self._validate_required_settings()

    def _load_from_parameter_store(self):
        """Load configuration from Parameter Store"""
        try:
            ps = get_parameter_store()

            # Load all parameters
            parameters = ps.get_all_parameters()

            # Update settings from Parameter Store (only if not already set)
            for key, value in parameters.items():
                attr_name = key.upper()
                if hasattr(self, attr_name):
                    current_value = getattr(self, attr_name)
                    # Only override if current value is None or default
                    if current_value is None or (isinstance(current_value, str) and not current_value):
                        # Convert string values to appropriate types
                        if attr_name in ['DEBUG', 'USE_PARAMETER_STORE']:
                            value = value.lower() in ('true', '1', 'yes')
                        elif attr_name in ['ACCESS_TOKEN_EXPIRE_MINUTES', 'RATE_LIMIT_PER_MINUTE', 'RATE_LIMIT_PER_DAY',
                                           'DEFAULT_ICD10_VERSION_YEAR', 'DEFAULT_PROCEDURE_VERSION_YEAR',
                                           'MAX_CODES_PER_TYPE', 'DEFAULT_CODES_PER_TYPE', 'CLAUDE_MAX_TOKENS']:
                            value = int(value)
                        elif attr_name in ['DEFAULT_MIN_SIMILARITY', 'DEFAULT_SEMANTIC_WEIGHT']:
                            value = float(value)
                        setattr(self, attr_name, value)

            print(f"✅ Loaded configuration from Parameter Store (/{ps.app_name}/{ps.environment})")
        except Exception as e:
            print(f"⚠️  Could not load from Parameter Store: {e}")
            print("⚠️  Falling back to environment variables")

    def _validate_required_settings(self):
        """Validate that all required settings are present"""
        required_fields = [
            'SECRET_KEY',
            'JWT_SECRET_KEY',
            'DATABASE_URL',
            'STRIPE_SECRET_KEY',
            'STRIPE_WEBHOOK_SECRET',
            'STRIPE_PUBLISHABLE_KEY'
        ]

        missing = []
        for field in required_fields:
            value = getattr(self, field, None)
            if value is None or value == "":
                missing.append(field)

        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}. "
                f"Please set them in Parameter Store or environment variables."
            )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def use_redis(self) -> bool:
        """Check if Redis is configured"""
        return self.REDIS_URL is not None and self.REDIS_URL != ""

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
