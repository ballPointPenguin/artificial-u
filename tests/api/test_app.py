import pytest
from fastapi.testclient import TestClient

from artificial_u.api.app import app

client = TestClient(app)


def test_health_check():
    """Test that the health check endpoint returns a 200 status code"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "status" in data
    assert "api_version" in data
    assert "timestamp" in data

    # Check values
    assert data["status"] == "ok"
    assert data["api_version"] == "v1"
    assert isinstance(data["timestamp"], float)


def test_index_route():
    """Test that the index route returns the correct information"""
    response = client.get("/api")
    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "name" in data
    assert "version" in data
    assert "description" in data
    assert "docs_url" in data

    # Check values
    assert data["name"] == "Artificial University API"
    assert data["version"] == "v1"
    assert data["docs_url"] == "/api/docs"
