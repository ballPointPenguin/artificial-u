import pytest
from fastapi.testclient import TestClient

from artificial_u.api.app import app, create_application
from artificial_u.api.security.auth0 import mock_require_auth, require_auth


@pytest.fixture
def client():
    """Create a test client for the FastAPI application with mocked authentication."""
    # Override the require_auth dependency to use mock authentication
    app.dependency_overrides[require_auth] = mock_require_auth
    with TestClient(app) as client:
        yield client
    # Clean up overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def test_app():
    """Create a fresh instance of the FastAPI application for testing."""
    return create_application()
