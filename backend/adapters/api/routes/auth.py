"""Authentication endpoints"""

import secrets
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from infrastructure.db.postgres import get_db
from infrastructure.db.models.user import User
from infrastructure.db.models.plan import Plan
from adapters.api.schemas.user import UserCreate, UserLogin, UserResponse, Token, OAuthSignIn, TokenWithUser
from domain.common.security import hash_password, verify_password, create_access_token
from adapters.api.middleware.auth import get_current_user
from adapters.api.middleware.rate_limit import check_signup_rate_limit

router = APIRouter()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Register a new user"""
    # Get client IP address
    client_ip = request.client.host if request.client else "unknown"

    # Check rate limit (3 signups per hour, 10 per day per IP)
    await check_signup_rate_limit(client_ip)

    # Honeypot check - if website field is filled, it's likely a bot
    if user_data.website:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid registration request"
        )

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        is_active=True,
        auth_provider='email',
        full_name=user_data.full_name,
        company_name=user_data.company_name,
        role=user_data.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    # Find user
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )

    # Update last login timestamp
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.post("/oauth/signin", response_model=TokenWithUser, status_code=status.HTTP_200_OK)
async def oauth_signin(oauth_data: OAuthSignIn, db: Session = Depends(get_db)):
    """Sign in or create user via OAuth (Google/Microsoft)"""
    # Check if user exists by email or OAuth provider ID
    user = db.query(User).filter(User.email == oauth_data.email).first()

    if not user and oauth_data.providerId:
        # Also check by OAuth provider ID in case email changed
        user = db.query(User).filter(User.oauth_provider_id == oauth_data.providerId).first()

    if not user:
        # Create new user with OAuth
        # Generate a random password hash since OAuth users don't have passwords
        random_password_hash = hash_password(secrets.token_urlsafe(32))

        user = User(
            email=oauth_data.email,
            password_hash=random_password_hash,
            is_active=True,
            full_name=oauth_data.name,
            company_name=oauth_data.company_name,
            role=oauth_data.role,
            auth_provider=oauth_data.provider,
            oauth_provider_id=oauth_data.providerId
        )

        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update existing user's OAuth info and profile if not set
        if not user.full_name and oauth_data.name:
            user.full_name = oauth_data.name
        if not user.company_name and oauth_data.company_name:
            user.company_name = oauth_data.company_name
        if not user.role and oauth_data.role:
            user.role = oauth_data.role
        if not user.auth_provider:
            user.auth_provider = oauth_data.provider
        if not user.oauth_provider_id:
            user.oauth_provider_id = oauth_data.providerId

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )

    # Update last login timestamp
    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }
