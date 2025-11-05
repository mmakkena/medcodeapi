"""User schemas"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID


class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response"""
    id: UUID
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OAuthSignIn(BaseModel):
    """Schema for OAuth sign-in"""
    email: EmailStr
    provider: str
    providerId: str
    name: str | None = None


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenWithUser(BaseModel):
    """Schema for token response with user data"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
