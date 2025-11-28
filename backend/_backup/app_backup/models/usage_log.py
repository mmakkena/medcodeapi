"""Usage log model for tracking API calls"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base
from app.utils.db_types import GUID, JSONB


class UsageLog(Base):
    """API usage tracking model"""

    __tablename__ = "usage_logs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    api_key_id = Column(GUID, ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    query_params = Column(JSONB, nullable=True)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    api_key = relationship("APIKey", back_populates="usage_logs")
    user = relationship("User", back_populates="usage_logs")

    # Indexes for efficient queries
    __table_args__ = (
        Index("ix_usage_logs_user_created", "user_id", "created_at"),
        Index("ix_usage_logs_api_key_created", "api_key_id", "created_at"),
    )

    def __repr__(self):
        return f"<UsageLog {self.method} {self.endpoint} - {self.status_code}>"
