"""Usage tracking service"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.usage_log import UsageLog
from app.models.api_key import APIKey
from app.models.subscription import StripeSubscription
from app.models.plan import Plan
from uuid import UUID


async def log_api_request(
    db: Session,
    api_key_id: UUID,
    user_id: UUID,
    endpoint: str,
    method: str,
    query_params: dict,
    status_code: int,
    response_time_ms: int | None,
    ip_address: str | None
) -> UsageLog:
    """Log an API request to the database"""
    usage_log = UsageLog(
        api_key_id=api_key_id,
        user_id=user_id,
        endpoint=endpoint,
        method=method,
        query_params=query_params,
        status_code=status_code,
        response_time_ms=response_time_ms,
        ip_address=ip_address
    )

    db.add(usage_log)
    db.commit()
    db.refresh(usage_log)

    return usage_log


async def get_user_usage_stats(db: Session, user_id: UUID) -> dict:
    """Get usage statistics for a user"""
    # Total requests
    total_requests = db.query(func.count(UsageLog.id)).filter(
        UsageLog.user_id == user_id
    ).scalar()

    # Requests this month
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    requests_this_month = db.query(func.count(UsageLog.id)).filter(
        UsageLog.user_id == user_id,
        UsageLog.created_at >= month_start
    ).scalar()

    # Most used endpoint
    most_used = db.query(
        UsageLog.endpoint,
        func.count(UsageLog.id).label("count")
    ).filter(
        UsageLog.user_id == user_id
    ).group_by(UsageLog.endpoint).order_by(func.count(UsageLog.id).desc()).first()

    most_used_endpoint = most_used[0] if most_used else None

    # Get user's plan limit from subscription
    monthly_limit = 100  # Default free tier

    # Check if user has an active subscription (get most recent if multiple)
    subscription = db.query(StripeSubscription).filter(
        StripeSubscription.user_id == user_id,
        StripeSubscription.status.in_(["active", "trialing", "past_due"])
    ).order_by(StripeSubscription.current_period_start.desc()).first()

    if subscription:
        # Get plan details
        plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
        if plan:
            monthly_limit = plan.monthly_requests

    percentage_used = (requests_this_month / monthly_limit * 100) if monthly_limit > 0 else 0

    return {
        "total_requests": total_requests or 0,
        "requests_this_month": requests_this_month or 0,
        "monthly_limit": monthly_limit,
        "percentage_used": round(percentage_used, 2),
        "most_used_endpoint": most_used_endpoint
    }


async def get_recent_logs(db: Session, user_id: UUID, limit: int = 50) -> list[UsageLog]:
    """Get recent usage logs for a user"""
    return db.query(UsageLog).filter(
        UsageLog.user_id == user_id
    ).order_by(UsageLog.created_at.desc()).limit(limit).all()
