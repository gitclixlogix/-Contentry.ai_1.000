"""
Pytest Configuration and Fixtures

Provides shared fixtures for all test modules including:
- Test client setup
- Database mocking
- Authentication helpers
- Test data factories
"""

import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch
import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient


# =============================================================================
# APPLICATION FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def app():
    """Get FastAPI application instance"""
    from server import app as fastapi_app
    return fastapi_app


@pytest.fixture
def sync_client(app):
    """Synchronous test client - handles event loop internally"""
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Async test client with proper lifecycle handling"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# =============================================================================
# TEST USER DATA
# =============================================================================

@pytest.fixture
def test_user_data() -> Dict[str, Any]:
    """Standard test user data"""
    return {
        "id": "test-user-001",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "user",
        "enterprise_id": None,
        "enterprise_role": None,
        "is_verified": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def test_admin_data() -> Dict[str, Any]:
    """Test admin user data"""
    return {
        "id": "security-test-user-001",
        "email": "admin@example.com",
        "full_name": "Test Admin",
        "role": "super_admin",
        "enterprise_id": None,
        "enterprise_role": None,
        "is_verified": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def test_enterprise_user_data() -> Dict[str, Any]:
    """Test enterprise user data"""
    return {
        "id": "4f7cba0f-b181-46a1-aadf-3c205522aa92",
        "email": "enterprise@example.com",
        "full_name": "Enterprise User",
        "role": "user",
        "enterprise_id": "783ff145-905f-47bf-a466-5bbd1748ce9b",
        "enterprise_role": "member",
        "is_verified": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# AUTHENTICATION HELPERS
# =============================================================================

@pytest.fixture
def user_headers(test_user_data) -> Dict[str, str]:
    """Headers for regular user requests"""
    return {
        "X-User-ID": test_user_data["id"],
        "Content-Type": "application/json",
    }


@pytest.fixture
def admin_headers(test_admin_data) -> Dict[str, str]:
    """Headers for admin requests"""
    return {
        "X-User-ID": test_admin_data["id"],
        "Content-Type": "application/json",
    }


@pytest.fixture
def enterprise_headers(test_enterprise_user_data) -> Dict[str, str]:
    """Headers for enterprise user requests"""
    return {
        "X-User-ID": test_enterprise_user_data["id"],
        "Content-Type": "application/json",
    }


# =============================================================================
# TEST DATA FACTORIES
# =============================================================================

@pytest.fixture
def sample_post_data() -> Dict[str, Any]:
    """Sample post data for testing"""
    return {
        "content": "This is a test post for content analysis. We are announcing a new product launch!",
        "title": "Test Post",
        "platforms": ["linkedin", "twitter"],
    }


@pytest.fixture
def sample_content_analysis_request() -> Dict[str, Any]:
    """Sample content analysis request"""
    return {
        "content": "Excited to announce our new product launch! This will revolutionize the industry.",
        "platforms": ["linkedin"],
        "run_accuracy_check": True,
        "run_cultural_check": True,
    }


@pytest.fixture
def sample_content_rewrite_request() -> Dict[str, Any]:
    """Sample content rewrite request"""
    return {
        "content": "This is unprofessional content that needs rewriting.",
        "issues": ["tone is too casual", "lacks professionalism"],
        "tone": "professional",
    }


@pytest.fixture
def sample_content_generation_request() -> Dict[str, Any]:
    """Sample content generation request"""
    return {
        "prompt": "Write a LinkedIn post about our new product launch",
        "tone": "professional",
        "job_title": "CEO",
        "platforms": ["linkedin"],
    }


# =============================================================================
# DATABASE MOCKING
# =============================================================================

@pytest.fixture
def mock_db():
    """Mock database for unit tests"""
    db = MagicMock()
    
    # Mock collections
    db.users = AsyncMock()
    db.posts = AsyncMock()
    db.content_analyses = AsyncMock()
    db.policies = AsyncMock()
    db.subscriptions = AsyncMock()
    db.enterprises = AsyncMock()
    db.notifications = AsyncMock()
    
    return db


@pytest.fixture
def mock_user_in_db(mock_db, test_user_data):
    """Setup mock user in database"""
    mock_db.users.find_one.return_value = test_user_data
    return mock_db


# =============================================================================
# API URL HELPER
# =============================================================================

@pytest.fixture
def api_base_url() -> str:
    """Base URL for API tests"""
    return "http://localhost:8001"


# =============================================================================
# CLEANUP HELPERS
# =============================================================================

@pytest.fixture(autouse=True)
async def cleanup():
    """Cleanup after each test"""
    yield
    # Add cleanup logic here if needed
