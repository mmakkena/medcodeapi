"""Support ticket model"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.db.postgres import Base
from domain.common.db_types import GUID


class SupportTicket(Base):
    """Customer support ticket model"""

    __tablename__ = "support_tickets"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), default="open", nullable=False)  # open, closed, pending
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="support_tickets")

    def __repr__(self):
        return f"<SupportTicket {self.subject} - {self.status}>"
