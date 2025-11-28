"""Usage tracking endpoints"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.usage import UsageLogResponse, UsageStatsResponse
from app.middleware.auth import get_current_user
from app.services.usage_service import get_user_usage_stats, get_recent_logs

router = APIRouter()


@router.get("/logs", response_model=list[UsageLogResponse])
async def get_usage_logs(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent usage logs for the current user"""
    logs = await get_recent_logs(db, current_user.id, limit)
    return logs


@router.get("/stats", response_model=UsageStatsResponse)
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get usage statistics for the current user"""
    stats = await get_user_usage_stats(db, current_user.id)
    return stats
