"""Usage tracking schemas"""

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class UsageLogResponse(BaseModel):
    """Schema for usage log response"""
    id: UUID
    endpoint: str
    method: str
    status_code: int
    response_time_ms: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class UsageStatsResponse(BaseModel):
    """Schema for usage statistics response"""
    total_requests: int
    requests_this_month: int
    monthly_limit: int
    percentage_used: float
    most_used_endpoint: str | None
