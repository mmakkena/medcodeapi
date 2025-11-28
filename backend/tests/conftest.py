"""Shared test fixtures and configuration"""

import os
import sys
from unittest.mock import MagicMock, AsyncMock

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, Float, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from adapters.api.main import app


# Create a test-specific Base to avoid PostgreSQL-specific types
TestBase = declarative_base()

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Define test-compatible models (without PostgreSQL ARRAY types)
class TestUser(TestBase):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)


class TestAPIKey(TestBase):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    name = Column(String)
    key_hash = Column(String)
    key_prefix = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)


class TestUsageLog(TestBase):
    __tablename__ = "usage_logs"
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer)
    user_id = Column(Integer)
    endpoint = Column(String)
    method = Column(String)
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    created_at = Column(DateTime)


@pytest.fixture
def db_session():
    """Create a fresh database session for each test"""
    TestBase.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        TestBase.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Create a test client with mocked dependencies"""
    from unittest.mock import patch
    from infrastructure.db.postgres import get_db
    from adapters.api.middleware.api_key import verify_api_key_with_usage
    from adapters.api.middleware.rate_limit import check_rate_limit

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Create mock user and API key
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.is_active = True

    mock_api_key = MagicMock()
    mock_api_key.id = 1
    mock_api_key.user_id = 1
    mock_api_key.name = "Test Key"
    mock_api_key.is_active = True

    async def mock_verify_api_key():
        return (mock_api_key, mock_user)

    async def mock_rate_limit(api_key, user):
        pass  # No rate limiting in tests

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_api_key_with_usage] = mock_verify_api_key
    app.dependency_overrides[check_rate_limit] = mock_rate_limit

    # Mock log_api_request to avoid database issues
    async def mock_log_api_request(*args, **kwargs):
        pass  # Skip logging in tests

    with patch('adapters.api.routes.cdi.log_api_request', mock_log_api_request), \
         patch('adapters.api.routes.revenue.log_api_request', mock_log_api_request), \
         patch('adapters.api.routes.hedis.log_api_request', mock_log_api_request), \
         TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client, db_session):
    """Create authentication headers with a test user"""
    return {
        "Authorization": "Bearer test_token",
        "user_id": 1
    }


@pytest.fixture
def api_key_headers(db_session):
    """Create API key authentication headers"""
    return {
        "Authorization": "Bearer test_api_key_12345",
        "api_key": "test_api_key_12345",
        "user_id": 1
    }
