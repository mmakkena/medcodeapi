"""Plan model for pricing tiers"""

import uuid
from sqlalchemy import Column, String, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Plan(Base):
    """Pricing plan model"""

    __tablename__ = "plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)  # Free, Developer, Growth, Enterprise
    monthly_requests = Column(Integer, nullable=False)  # Request limit per month
    price_cents = Column(Integer, nullable=False)  # Price in cents (e.g., 4900 = $49.00)
    stripe_price_id = Column(String(100), nullable=True)  # Stripe Price ID
    features = Column(JSON, nullable=True)  # Additional features as JSON

    # Relationships
    subscriptions = relationship("StripeSubscription", back_populates="plan")

    def __repr__(self):
        return f"<Plan {self.name} - {self.monthly_requests} req/mo>"
