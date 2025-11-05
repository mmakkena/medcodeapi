"""Authentication endpoints"""

import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.plan import Plan
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, OAuthSignIn, TokenWithUser
from app.utils.security import hash_password, verify_password, create_access_token
from app.middleware.auth import get_current_user

router = APIRouter()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
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
        is_active=True
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
    # Check if user exists
    user = db.query(User).filter(User.email == oauth_data.email).first()

    if not user:
        # Create new user with OAuth
        # Generate a random password hash since OAuth users don't have passwords
        random_password_hash = hash_password(secrets.token_urlsafe(32))

        user = User(
            email=oauth_data.email,
            password_hash=random_password_hash,
            is_active=True
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }
