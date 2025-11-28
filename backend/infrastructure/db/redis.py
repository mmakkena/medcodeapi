"""
Redis connection and cache management.

This module provides Redis connectivity with:
- Async connection management
- Connection pooling
- Health checks
- Graceful fallback to in-memory when Redis unavailable
"""

import logging
from typing import Optional, Any, Dict
from datetime import timedelta

import redis.asyncio as redis

from infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

# Global Redis client
_redis_client: Optional[redis.Redis] = None

# In-memory fallback cache
_memory_cache: Dict[str, Any] = {}


async def init_redis() -> Optional[redis.Redis]:
    """
    Initialize Redis connection.

    Should be called during application startup.

    Returns:
        Redis client if connection successful, None otherwise.
    """
    global _redis_client

    if not settings.use_redis:
        logger.info("Redis disabled in settings, using in-memory cache")
        return None

    try:
        logger.info(f"Connecting to Redis at {settings.REDIS_URL}")
        _redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )

        # Verify connection
        await _redis_client.ping()
        logger.info("Redis connection established successfully")
        return _redis_client

    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}")
        logger.info("Falling back to in-memory cache")
        _redis_client = None
        return None


async def close_redis():
    """
    Close Redis connection.

    Should be called during application shutdown.
    """
    global _redis_client

    if _redis_client:
        try:
            logger.info("Closing Redis connection")
            await _redis_client.close()
            _redis_client = None
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get the Redis client instance.

    Returns:
        Redis client if available, None otherwise.
    """
    return _redis_client


def is_redis_available() -> bool:
    """
    Check if Redis is available.

    Returns:
        True if Redis client is connected.
    """
    return _redis_client is not None


async def check_redis_health() -> dict:
    """
    Check Redis connectivity and health.

    Returns:
        Dictionary with health status information.
    """
    if not _redis_client:
        return {
            "status": "disabled",
            "connected": False,
            "mode": "in-memory"
        }

    try:
        # Ping Redis
        await _redis_client.ping()

        # Get info
        info = await _redis_client.info("memory")

        return {
            "status": "healthy",
            "connected": True,
            "mode": "redis",
            "memory_used": info.get("used_memory_human", "unknown"),
            "memory_peak": info.get("used_memory_peak_human", "unknown")
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }


# Cache operations with Redis/memory fallback

async def cache_get(key: str) -> Optional[str]:
    """
    Get a value from cache.

    Args:
        key: Cache key

    Returns:
        Cached value or None if not found.
    """
    if _redis_client:
        try:
            return await _redis_client.get(key)
        except Exception as e:
            logger.warning(f"Redis get failed for {key}: {e}")
            return _memory_cache.get(key)
    return _memory_cache.get(key)


async def cache_set(
    key: str,
    value: str,
    expire_seconds: Optional[int] = None
) -> bool:
    """
    Set a value in cache.

    Args:
        key: Cache key
        value: Value to cache
        expire_seconds: Optional TTL in seconds

    Returns:
        True if successful.
    """
    if _redis_client:
        try:
            if expire_seconds:
                await _redis_client.setex(key, expire_seconds, value)
            else:
                await _redis_client.set(key, value)
            return True
        except Exception as e:
            logger.warning(f"Redis set failed for {key}: {e}")
            _memory_cache[key] = value
            return True

    _memory_cache[key] = value
    return True


async def cache_delete(key: str) -> bool:
    """
    Delete a value from cache.

    Args:
        key: Cache key

    Returns:
        True if successful.
    """
    if _redis_client:
        try:
            await _redis_client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis delete failed for {key}: {e}")
            _memory_cache.pop(key, None)
            return True

    _memory_cache.pop(key, None)
    return True


async def cache_incr(key: str, expire_seconds: Optional[int] = None) -> int:
    """
    Increment a counter in cache.

    Args:
        key: Cache key
        expire_seconds: Optional TTL for new keys

    Returns:
        New counter value.
    """
    if _redis_client:
        try:
            value = await _redis_client.incr(key)
            if value == 1 and expire_seconds:
                await _redis_client.expire(key, expire_seconds)
            return value
        except Exception as e:
            logger.warning(f"Redis incr failed for {key}: {e}")

    # In-memory fallback
    current = _memory_cache.get(key, 0)
    new_value = current + 1
    _memory_cache[key] = new_value
    return new_value


async def cache_clear_pattern(pattern: str) -> int:
    """
    Delete all keys matching a pattern.

    Args:
        pattern: Redis key pattern (e.g., "user:*")

    Returns:
        Number of keys deleted.
    """
    if _redis_client:
        try:
            keys = []
            async for key in _redis_client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await _redis_client.delete(*keys)
            return len(keys)
        except Exception as e:
            logger.warning(f"Redis clear pattern failed for {pattern}: {e}")

    # In-memory fallback
    import fnmatch
    keys_to_delete = [k for k in _memory_cache.keys() if fnmatch.fnmatch(k, pattern)]
    for key in keys_to_delete:
        del _memory_cache[key]
    return len(keys_to_delete)
