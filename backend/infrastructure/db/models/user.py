"""User model for authentication"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from infrastructure.db.postgres import Base
from domain.common.db_types import GUID


class User(Base):
    """User model for authentication and account management"""

    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Additional user information
    full_name = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    role = Column(String(100), nullable=True)
    auth_provider = Column(String(50), nullable=True)  # 'email', 'google', 'azure-ad'
    oauth_provider_id = Column(String(255), nullable=True, index=True)
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("StripeSubscription", back_populates="user", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="user", cascade="all, delete-orphan")
    support_tickets = relationship("SupportTicket", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"
