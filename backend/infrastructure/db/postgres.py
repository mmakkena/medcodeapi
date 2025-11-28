"""
Database connection and session management.

This module provides PostgreSQL database connectivity with:
- Connection pooling
- Async support
- Health checks
- Transaction management
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

# Base class for models
Base = declarative_base()

# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,  # Number of connections to keep open
    max_overflow=20,  # Additional connections allowed
    pool_timeout=30,  # Seconds to wait for available connection
    pool_recycle=1800,  # Recycle connections after 30 minutes
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Don't expire objects after commit
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for getting database session.

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()

    Yields:
        Database session that is automatically closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions (for non-FastAPI use).

    Usage:
        with get_db_context() as db:
            db.query(User).all()

    Yields:
        Database session that is automatically closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get a new database session directly.
    Caller is responsible for closing the session.

    Returns:
        New database session.
    """
    return SessionLocal()


def get_db_sync() -> Generator[Session, None, None]:
    """
    Synchronous generator for database sessions.
    Used by MCP tools and other sync contexts.

    Usage:
        db = next(get_db_sync())
        try:
            # use db
        finally:
            db.close()

    Yields:
        Database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def check_database_health() -> dict:
    """
    Check database connectivity and health.

    Returns:
        Dictionary with health status information.
    """
    try:
        db = SessionLocal()
        try:
            # Execute a simple query to verify connection
            result = db.execute(text("SELECT 1"))
            result.fetchone()

            # Get pool status
            pool_status = {
                "pool_size": engine.pool.size(),
                "checked_in": engine.pool.checkedin(),
                "checked_out": engine.pool.checkedout(),
                "overflow": engine.pool.overflow(),
            }

            return {
                "status": "healthy",
                "connected": True,
                "pool": pool_status
            }
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }


def init_database():
    """
    Initialize database by creating all tables.
    Should only be used in development/testing.
    Production should use Alembic migrations.
    """
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def dispose_engine():
    """
    Dispose of the database engine and close all connections.
    Should be called during application shutdown.
    """
    logger.info("Disposing database engine...")
    engine.dispose()
    logger.info("Database engine disposed")
