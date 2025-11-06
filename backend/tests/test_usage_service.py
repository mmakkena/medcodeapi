"""Tests for usage tracking service"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.usage_service import get_user_usage_stats
from app.models.user import User
from app.models.usage_log import UsageLog
from app.models.subscription import StripeSubscription
from app.models.plan import Plan


@pytest.mark.asyncio
async def test_get_usage_stats_free_tier(db_session):
    """Test usage stats for a user on free tier (no subscription)"""
    # Create user
    user = User(email="free@example.com", hashed_password="test", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create some usage logs
    for i in range(50):
        log = UsageLog(
            api_key_id=uuid4(),
            user_id=user.id,
            endpoint="/api/v1/icd10/search",
            method="GET",
            query_params={},
            status_code=200,
            response_time_ms=100,
            ip_address="127.0.0.1"
        )
        db_session.add(log)
    db_session.commit()

    # Get stats
    stats = await get_user_usage_stats(db_session, user.id)

    # Assert
    assert stats["total_requests"] == 50
    assert stats["requests_this_month"] == 50
    assert stats["monthly_limit"] == 100  # Free tier default
    assert stats["percentage_used"] == 50.0
    assert stats["most_used_endpoint"] == "/api/v1/icd10/search"


@pytest.mark.asyncio
async def test_get_usage_stats_with_subscription(db_session):
    """Test usage stats for a user with active subscription"""
    # Create user
    user = User(email="paid@example.com", hashed_password="test", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create Developer plan
    plan = Plan(
        name="Developer",
        stripe_price_id="price_test",
        price_cents=4900,
        monthly_requests=10000,
        rate_limit=300,
        features={}
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)

    # Create subscription
    subscription = StripeSubscription(
        user_id=user.id,
        plan_id=plan.id,
        stripe_subscription_id="sub_test123",
        stripe_customer_id="cus_test123",
        status="active",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30)
    )
    db_session.add(subscription)
    db_session.commit()

    # Create usage logs
    for i in range(1000):
        log = UsageLog(
            api_key_id=uuid4(),
            user_id=user.id,
            endpoint="/api/v1/cpt/search",
            method="GET",
            query_params={},
            status_code=200,
            response_time_ms=150,
            ip_address="127.0.0.1"
        )
        db_session.add(log)
    db_session.commit()

    # Get stats
    stats = await get_user_usage_stats(db_session, user.id)

    # Assert
    assert stats["total_requests"] == 1000
    assert stats["requests_this_month"] == 1000
    assert stats["monthly_limit"] == 10000  # Developer plan limit
    assert stats["percentage_used"] == 10.0
    assert stats["most_used_endpoint"] == "/api/v1/cpt/search"


@pytest.mark.asyncio
async def test_get_usage_stats_old_logs_not_counted(db_session):
    """Test that logs from previous months are not counted in current month usage"""
    # Create user
    user = User(email="test@example.com", hashed_password="test", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create old logs (last month)
    last_month = datetime.utcnow() - timedelta(days=35)
    for i in range(50):
        log = UsageLog(
            api_key_id=uuid4(),
            user_id=user.id,
            endpoint="/api/v1/icd10/search",
            method="GET",
            query_params={},
            status_code=200,
            response_time_ms=100,
            ip_address="127.0.0.1",
            created_at=last_month
        )
        db_session.add(log)

    # Create current month logs
    for i in range(25):
        log = UsageLog(
            api_key_id=uuid4(),
            user_id=user.id,
            endpoint="/api/v1/icd10/search",
            method="GET",
            query_params={},
            status_code=200,
            response_time_ms=100,
            ip_address="127.0.0.1"
        )
        db_session.add(log)
    db_session.commit()

    # Get stats
    stats = await get_user_usage_stats(db_session, user.id)

    # Assert
    assert stats["total_requests"] == 75  # All time
    assert stats["requests_this_month"] == 25  # Only current month
    assert stats["percentage_used"] == 25.0


@pytest.mark.asyncio
async def test_get_usage_stats_multiple_endpoints(db_session):
    """Test most used endpoint with multiple endpoints"""
    # Create user
    user = User(email="test@example.com", hashed_password="test", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create logs for different endpoints
    endpoints = {
        "/api/v1/icd10/search": 100,
        "/api/v1/cpt/search": 50,
        "/api/v1/suggest": 200
    }

    for endpoint, count in endpoints.items():
        for i in range(count):
            log = UsageLog(
                api_key_id=uuid4(),
                user_id=user.id,
                endpoint=endpoint,
                method="GET",
                query_params={},
                status_code=200,
                response_time_ms=100,
                ip_address="127.0.0.1"
            )
            db_session.add(log)
    db_session.commit()

    # Get stats
    stats = await get_user_usage_stats(db_session, user.id)

    # Assert
    assert stats["total_requests"] == 350
    assert stats["most_used_endpoint"] == "/api/v1/suggest"  # Highest count


@pytest.mark.asyncio
async def test_get_usage_stats_no_logs(db_session):
    """Test usage stats for a new user with no logs"""
    # Create user
    user = User(email="new@example.com", hashed_password="test", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Get stats (no logs)
    stats = await get_user_usage_stats(db_session, user.id)

    # Assert
    assert stats["total_requests"] == 0
    assert stats["requests_this_month"] == 0
    assert stats["monthly_limit"] == 100
    assert stats["percentage_used"] == 0
    assert stats["most_used_endpoint"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
