import pytest
from fastapi.testclient import TestClient

from artificial_u.api.app import app, create_application
from artificial_u.api.dependencies import ensure_student
from artificial_u.api.security.auth0 import mock_require_auth, require_auth
from artificial_u.models.core import Student


def mock_ensure_student() -> Student:
    """Mock student with admin role and unlimited coins for testing."""
    return Student(
        id=1,
        name="Test User",
        email="test@example.com",
        auth0_sub="test-user-123",
        role="admin",  # Admin bypasses all coin checks
        coins=999999,  # Unlimited coins for testing
        is_active=True,
    )


@pytest.fixture
def client():
    """Create a test client for the FastAPI application with mocked authentication."""
    # Override the require_auth dependency to use mock authentication
    app.dependency_overrides[require_auth] = mock_require_auth
    # Override ensure_student to return a test student with admin privileges
    app.dependency_overrides[ensure_student] = mock_ensure_student
    with TestClient(app) as client:
        yield client
    # Clean up overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def test_app():
    """Create a fresh instance of the FastAPI application for testing."""
    return create_application()
