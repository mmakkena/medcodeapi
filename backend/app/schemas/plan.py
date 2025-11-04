"""Plan schemas"""

from pydantic import BaseModel
from uuid import UUID


class PlanResponse(BaseModel):
    """Schema for plan response"""
    id: UUID
    name: str
    monthly_requests: int
    price_cents: int
    stripe_price_id: str | None
    features: dict | None

    class Config:
        from_attributes = True
