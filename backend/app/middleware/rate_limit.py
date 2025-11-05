"""Rate limiting middleware"""

from typing import Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, status
import redis.asyncio as redis
from app.config import settings
from app.models.api_key import APIKey
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

# Redis client (will be initialized in lifespan event)
redis_client: Optional[redis.Redis] = None

# In-memory fallback for rate limiting
_in_memory_store: dict[str, list[datetime]] = {}


async def init_redis():
    """Initialize Redis connection"""
    global redis_client

    if settings.use_redis:
        try:
            logger.info(f"Initializing Redis connection to {settings.REDIS_URL}")
            redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=10
            )
            # Test connection
            await redis_client.ping()
            logger.info("Redis connection successful")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.info("Falling back to in-memory rate limiting")
            redis_client = None
    else:
        logger.info("Redis disabled, using in-memory rate limiting")


async def close_redis():
    """Close Redis connection"""
    global redis_client

    if redis_client:
        try:
            logger.info("Closing Redis connection")
            await redis_client.close()
            redis_client = None
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")


def _get_rate_limit_key(user_id: str, window: str) -> str:
    """Generate Redis key for rate limiting"""
    return f"rate_limit:{user_id}:{window}"


def _clean_old_requests(requests: list[datetime], window_seconds: int) -> list[datetime]:
    """Remove requests older than the window"""
    cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
    return [req for req in requests if req > cutoff]


async def check_rate_limit(api_key: APIKey, user: User) -> None:
    """
    Check if the user has exceeded rate limits.
    Uses Redis if available, falls back to in-memory storage.

    Raises HTTPException if rate limit is exceeded.
    """
    user_id = str(user.id)

    # Define rate limits
    per_minute_limit = settings.RATE_LIMIT_PER_MINUTE
    per_day_limit = settings.RATE_LIMIT_PER_DAY

    if redis_client:
        # Redis-based rate limiting
        await _check_rate_limit_redis(user_id, per_minute_limit, per_day_limit)
    else:
        # In-memory rate limiting
        await _check_rate_limit_memory(user_id, per_minute_limit, per_day_limit)


async def _check_rate_limit_redis(user_id: str, per_minute: int, per_day: int) -> None:
    """Redis-based rate limiting"""
    minute_key = _get_rate_limit_key(user_id, "minute")
    day_key = _get_rate_limit_key(user_id, "day")

    # Increment counters
    minute_count = await redis_client.incr(minute_key)
    day_count = await redis_client.incr(day_key)

    # Set expiry on first request
    if minute_count == 1:
        await redis_client.expire(minute_key, 60)
    if day_count == 1:
        await redis_client.expire(day_key, 86400)

    # Check limits
    if minute_count > per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {per_minute} requests per minute"
        )

    if day_count > per_day:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily rate limit exceeded: {per_day} requests per day"
        )


async def _check_rate_limit_memory(user_id: str, per_minute: int, per_day: int) -> None:
    """In-memory rate limiting (fallback)"""
    now = datetime.utcnow()

    # Initialize user's request history if not exists
    if user_id not in _in_memory_store:
        _in_memory_store[user_id] = []

    # Clean old requests
    _in_memory_store[user_id] = _clean_old_requests(_in_memory_store[user_id], 86400)  # Keep last 24 hours

    # Count requests in last minute and day
    minute_ago = now - timedelta(minutes=1)
    day_ago = now - timedelta(days=1)

    requests_last_minute = sum(1 for req in _in_memory_store[user_id] if req > minute_ago)
    requests_last_day = sum(1 for req in _in_memory_store[user_id] if req > day_ago)

    # Check limits
    if requests_last_minute >= per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {per_minute} requests per minute"
        )

    if requests_last_day >= per_day:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily rate limit exceeded: {per_day} requests per day"
        )

    # Record this request
    _in_memory_store[user_id].append(now)
