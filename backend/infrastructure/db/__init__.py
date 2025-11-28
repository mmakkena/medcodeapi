"""
Database Infrastructure

PostgreSQL database connection, SQLAlchemy models, and repository pattern.
Uses pgvector for vector similarity search.
"""

from infrastructure.db.postgres import (
    Base,
    engine,
    SessionLocal,
    get_db,
    get_db_context,
    get_db_session,
    check_database_health,
    init_database,
    dispose_engine,
)

from infrastructure.db.redis import (
    init_redis,
    close_redis,
    get_redis_client,
    is_redis_available,
    check_redis_health,
    cache_get,
    cache_set,
    cache_delete,
    cache_incr,
    cache_clear_pattern,
)

__all__ = [
    # PostgreSQL
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "get_db_context",
    "get_db_session",
    "check_database_health",
    "init_database",
    "dispose_engine",
    # Redis
    "init_redis",
    "close_redis",
    "get_redis_client",
    "is_redis_available",
    "check_redis_health",
    "cache_get",
    "cache_set",
    "cache_delete",
    "cache_incr",
    "cache_clear_pattern",
]
