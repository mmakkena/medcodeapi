"""API Key authentication middleware"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models.api_key import APIKey
from app.models.user import User
from app.utils.security import hash_api_key

security = HTTPBearer()


async def get_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> tuple[APIKey, User]:
    """
    Verify API key and return the associated API key object and user.
    Used for API endpoints that require API key authentication.
    """
    api_key = credentials.credentials

    # Hash the provided API key
    key_hash = hash_api_key(api_key)

    # Look up the API key in database
    db_api_key = db.query(APIKey).filter(APIKey.key_hash == key_hash).first()

    if not db_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if API key is active
    if not db_api_key.is_active or db_api_key.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get associated user
    user = db.query(User).filter(User.id == db_api_key.user_id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Update last_used_at timestamp
    db_api_key.last_used_at = datetime.utcnow()
    db.commit()

    return db_api_key, user


async def verify_api_key_with_usage(
    request: Request,
    api_key_data: tuple[APIKey, User] = Depends(get_api_key),
    db: Session = Depends(get_db)
) -> tuple[APIKey, User]:
    """
    Verify API key and check usage limits.
    This will be enhanced with rate limiting logic.
    """
    api_key, user = api_key_data

    # TODO: Add rate limiting check here
    # For now, just return the API key and user

    return api_key, user
