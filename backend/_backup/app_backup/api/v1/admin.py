"""Admin analytics and user management endpoints"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.plan import Plan
from app.models.subscription import StripeSubscription
from app.models.usage_log import UsageLog
from app.models.api_key import APIKey
from app.middleware.auth import get_current_admin_user

router = APIRouter()


# ============================================================================
# Response Schemas
# ============================================================================

class UserAnalytics(BaseModel):
    """User with analytics data"""
    id: str
    email: str
    full_name: Optional[str]
    company_name: Optional[str]
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    # Subscription info
    current_plan: Optional[str]
    subscription_status: Optional[str]

    # Usage stats
    total_api_calls: int
    api_calls_last_30_days: int
    api_calls_today: int

    # API keys
    active_api_keys: int


class PlatformAnalytics(BaseModel):
    """Overall platform analytics"""
    # User stats
    total_users: int
    active_users_last_30_days: int
    new_users_last_7_days: int
    new_users_last_30_days: int

    # Subscription stats
    total_paid_subscriptions: int
    subscriptions_by_plan: dict

    # Usage stats
    total_api_calls: int
    api_calls_last_30_days: int
    api_calls_today: int

    # Top endpoints
    top_endpoints: List[dict]

    # Revenue (in cents)
    monthly_recurring_revenue: int


class UserUsageDetail(BaseModel):
    """Detailed usage for a specific user"""
    user_id: str
    email: str

    # Time series data (last 30 days)
    daily_usage: List[dict]

    # Endpoint breakdown
    endpoint_usage: List[dict]

    # Recent API calls
    recent_calls: List[dict]

    # Summary stats
    total_calls: int
    avg_response_time_ms: Optional[float]
    error_rate: Optional[float]


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/analytics", response_model=PlatformAnalytics)
async def get_platform_analytics(
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get overall platform analytics. Admin only.

    Returns:
    - User signup statistics
    - Subscription breakdown by plan
    - API usage statistics
    - Revenue metrics
    - Top endpoints
    """
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)
    today_start = datetime(now.year, now.month, now.day)

    # User stats
    total_users = db.query(func.count(User.id)).scalar()

    active_users_last_30_days = db.query(func.count(func.distinct(UsageLog.user_id))).filter(
        UsageLog.created_at >= thirty_days_ago
    ).scalar() or 0

    new_users_last_7_days = db.query(func.count(User.id)).filter(
        User.created_at >= seven_days_ago
    ).scalar() or 0

    new_users_last_30_days = db.query(func.count(User.id)).filter(
        User.created_at >= thirty_days_ago
    ).scalar() or 0

    # Subscription stats
    active_subscriptions = db.query(StripeSubscription).filter(
        StripeSubscription.status.in_(['active', 'trialing'])
    ).all()

    total_paid_subscriptions = len([s for s in active_subscriptions])

    # Subscriptions by plan
    subscriptions_by_plan = {}
    monthly_recurring_revenue = 0

    for subscription in active_subscriptions:
        plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
        if plan:
            plan_name = plan.name
            subscriptions_by_plan[plan_name] = subscriptions_by_plan.get(plan_name, 0) + 1

            if plan.name.lower() != 'free':
                monthly_recurring_revenue += plan.price_cents

    # Usage stats
    total_api_calls = db.query(func.count(UsageLog.id)).scalar() or 0

    api_calls_last_30_days = db.query(func.count(UsageLog.id)).filter(
        UsageLog.created_at >= thirty_days_ago
    ).scalar() or 0

    api_calls_today = db.query(func.count(UsageLog.id)).filter(
        UsageLog.created_at >= today_start
    ).scalar() or 0

    # Top endpoints
    top_endpoints_query = db.query(
        UsageLog.endpoint,
        UsageLog.method,
        func.count(UsageLog.id).label('call_count')
    ).filter(
        UsageLog.created_at >= thirty_days_ago
    ).group_by(
        UsageLog.endpoint,
        UsageLog.method
    ).order_by(
        func.count(UsageLog.id).desc()
    ).limit(10).all()

    top_endpoints = [
        {
            "endpoint": endpoint,
            "method": method,
            "call_count": count
        }
        for endpoint, method, count in top_endpoints_query
    ]

    return PlatformAnalytics(
        total_users=total_users or 0,
        active_users_last_30_days=active_users_last_30_days,
        new_users_last_7_days=new_users_last_7_days or 0,
        new_users_last_30_days=new_users_last_30_days or 0,
        total_paid_subscriptions=total_paid_subscriptions,
        subscriptions_by_plan=subscriptions_by_plan,
        total_api_calls=total_api_calls,
        api_calls_last_30_days=api_calls_last_30_days,
        api_calls_today=api_calls_today,
        top_endpoints=top_endpoints,
        monthly_recurring_revenue=monthly_recurring_revenue
    )


@router.get("/users", response_model=List[UserAnalytics])
async def get_all_users(
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Get all users with their subscription and usage analytics. Admin only.

    Query params:
    - limit: Number of users to return (max 500)
    - offset: Pagination offset

    Returns list of users with:
    - Basic info (email, name, company)
    - Current subscription plan and status
    - API usage statistics
    - Number of active API keys
    """
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    today_start = datetime(now.year, now.month, now.day)

    # Get all users
    users = db.query(User).order_by(User.created_at.desc()).limit(limit).offset(offset).all()

    result = []
    for user in users:
        # Get current subscription
        subscription = db.query(StripeSubscription).filter(
            and_(
                StripeSubscription.user_id == user.id,
                StripeSubscription.status.in_(['active', 'trialing'])
            )
        ).first()

        current_plan = None
        subscription_status = None
        if subscription:
            plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
            current_plan = plan.name if plan else None
            subscription_status = subscription.status

        # Get usage stats
        total_api_calls = db.query(func.count(UsageLog.id)).filter(
            UsageLog.user_id == user.id
        ).scalar() or 0

        api_calls_last_30_days = db.query(func.count(UsageLog.id)).filter(
            and_(
                UsageLog.user_id == user.id,
                UsageLog.created_at >= thirty_days_ago
            )
        ).scalar() or 0

        api_calls_today = db.query(func.count(UsageLog.id)).filter(
            and_(
                UsageLog.user_id == user.id,
                UsageLog.created_at >= today_start
            )
        ).scalar() or 0

        # Get active API keys
        active_api_keys = db.query(func.count(APIKey.id)).filter(
            and_(
                APIKey.user_id == user.id,
                APIKey.is_active == True
            )
        ).scalar() or 0

        result.append(UserAnalytics(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            company_name=user.company_name,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
            current_plan=current_plan,
            subscription_status=subscription_status,
            total_api_calls=total_api_calls,
            api_calls_last_30_days=api_calls_last_30_days,
            api_calls_today=api_calls_today,
            active_api_keys=active_api_keys
        ))

    return result


@router.get("/usage/{user_id}", response_model=UserUsageDetail)
async def get_user_usage_detail(
    user_id: str,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed usage analytics for a specific user. Admin only.

    Returns:
    - Daily usage chart data (last 30 days)
    - Breakdown by endpoint
    - Recent API calls with response times
    - Summary statistics (avg response time, error rate)
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)

    # Daily usage (last 30 days)
    daily_usage_query = db.query(
        func.date(UsageLog.created_at).label('date'),
        func.count(UsageLog.id).label('count')
    ).filter(
        and_(
            UsageLog.user_id == user_id,
            UsageLog.created_at >= thirty_days_ago
        )
    ).group_by(
        func.date(UsageLog.created_at)
    ).order_by(
        func.date(UsageLog.created_at)
    ).all()

    daily_usage = [
        {"date": str(date), "count": count}
        for date, count in daily_usage_query
    ]

    # Endpoint usage breakdown
    endpoint_usage_query = db.query(
        UsageLog.endpoint,
        UsageLog.method,
        func.count(UsageLog.id).label('count'),
        func.avg(UsageLog.response_time_ms).label('avg_response_time')
    ).filter(
        and_(
            UsageLog.user_id == user_id,
            UsageLog.created_at >= thirty_days_ago
        )
    ).group_by(
        UsageLog.endpoint,
        UsageLog.method
    ).order_by(
        func.count(UsageLog.id).desc()
    ).all()

    endpoint_usage = [
        {
            "endpoint": endpoint,
            "method": method,
            "count": count,
            "avg_response_time_ms": round(avg_time) if avg_time else None
        }
        for endpoint, method, count, avg_time in endpoint_usage_query
    ]

    # Recent API calls (last 50)
    recent_calls_query = db.query(UsageLog).filter(
        UsageLog.user_id == user_id
    ).order_by(
        UsageLog.created_at.desc()
    ).limit(50).all()

    recent_calls = [
        {
            "endpoint": log.endpoint,
            "method": log.method,
            "status_code": log.status_code,
            "response_time_ms": log.response_time_ms,
            "created_at": log.created_at.isoformat()
        }
        for log in recent_calls_query
    ]

    # Summary stats
    total_calls = db.query(func.count(UsageLog.id)).filter(
        UsageLog.user_id == user_id
    ).scalar() or 0

    avg_response_time = db.query(func.avg(UsageLog.response_time_ms)).filter(
        and_(
            UsageLog.user_id == user_id,
            UsageLog.response_time_ms.isnot(None)
        )
    ).scalar()

    error_count = db.query(func.count(UsageLog.id)).filter(
        and_(
            UsageLog.user_id == user_id,
            UsageLog.status_code >= 400
        )
    ).scalar() or 0

    error_rate = (error_count / total_calls * 100) if total_calls > 0 else 0

    return UserUsageDetail(
        user_id=user_id,
        email=user.email,
        daily_usage=daily_usage,
        endpoint_usage=endpoint_usage,
        recent_calls=recent_calls,
        total_calls=total_calls,
        avg_response_time_ms=round(avg_response_time, 2) if avg_response_time else None,
        error_rate=round(error_rate, 2)
    )
