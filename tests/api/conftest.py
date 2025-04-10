import pytest
from fastapi.testclient import TestClient
from artificial_u.api.app import app, create_application


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application
    """
    return TestClient(app)


@pytest.fixture
def test_app():
    """
    Create a fresh instance of the FastAPI application for testing
    """
    return create_application()
