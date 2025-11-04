"""API key management endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models.api_key import APIKey
from app.models.user import User
from app.schemas.api_key import APIKeyCreate, APIKeyResponse, APIKeyWithSecret
from app.middleware.auth import get_current_user
from app.utils.security import generate_api_key, hash_api_key, get_api_key_prefix

router = APIRouter()


@router.get("", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all active API keys for the current user"""
    api_keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True  # Only show active keys
    ).order_by(APIKey.created_at.desc()).all()

    return api_keys


@router.post("", response_model=APIKeyWithSecret, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new API key for the current user.
    The full API key is only shown once at creation.
    """
    # Generate API key
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    key_prefix = get_api_key_prefix(api_key)

    # Create API key record
    new_key = APIKey(
        user_id=current_user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=key_data.name,
        is_active=True
    )

    db.add(new_key)
    db.commit()
    db.refresh(new_key)

    # Return with full API key (only time it's shown)
    return APIKeyWithSecret(
        id=new_key.id,
        key_prefix=new_key.key_prefix,
        name=new_key.name,
        api_key=api_key,  # Full key - only shown once
        created_at=new_key.created_at
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke (soft delete) an API key"""
    # Find the API key
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    # Soft delete by marking as revoked
    api_key.is_active = False
    api_key.revoked_at = datetime.utcnow()

    db.commit()

    return None
