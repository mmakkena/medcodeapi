"""Stripe subscription model"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.db.postgres import Base
from domain.common.db_types import GUID


class StripeSubscription(Base):
    """Stripe subscription tracking model"""

    __tablename__ = "stripe_subscriptions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(GUID, ForeignKey("plans.id"), nullable=False)
    stripe_subscription_id = Column(String(100), unique=True, nullable=False)
    stripe_customer_id = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False)  # active, canceled, past_due, etc.
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")

    def __repr__(self):
        return f"<Subscription {self.stripe_subscription_id} - {self.status}>"
