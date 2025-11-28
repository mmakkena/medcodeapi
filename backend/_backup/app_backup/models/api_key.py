"""API Key model for developer authentication"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.utils.db_types import GUID


class APIKey(Base):
    """API Key model for authenticating API requests"""

    __tablename__ = "api_keys"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key_hash = Column(String(255), nullable=False, unique=True)  # SHA-256 hash
    key_prefix = Column(String(10), nullable=False)  # First 8 chars for display (e.g., "mk_abc123")
    name = Column(String(100), nullable=True)  # User-defined label
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)  # Track last usage
    revoked_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")
    usage_logs = relationship("UsageLog", back_populates="api_key", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<APIKey {self.key_prefix}... ({self.name})>"
