"""Security utilities for hashing and API key generation"""

import secrets
import hashlib
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from infrastructure.config.settings import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def generate_api_key() -> str:
    """Generate a secure random API key with prefix"""
    random_part = secrets.token_urlsafe(32)  # 256 bits
    return f"{settings.API_KEY_PREFIX}{random_part}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key using SHA-256"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_api_key_prefix(api_key: str) -> str:
    """Extract the display prefix from an API key (first 8 characters)"""
    return api_key[:8] if len(api_key) >= 8 else api_key


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> dict | None:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.JWTError:
        return None
