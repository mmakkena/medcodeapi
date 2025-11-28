"""API Key schemas"""

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class APIKeyCreate(BaseModel):
    """Schema for creating an API key"""
    name: str | None = None


class APIKeyResponse(BaseModel):
    """Schema for API key response (without secret)"""
    id: UUID
    key_prefix: str
    name: str | None
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None

    class Config:
        from_attributes = True


class APIKeyWithSecret(BaseModel):
    """Schema for API key response with secret (only shown once at creation)"""
    id: UUID
    key_prefix: str
    name: str | None
    api_key: str  # Full API key - only returned on creation
    created_at: datetime

    class Config:
        from_attributes = True
