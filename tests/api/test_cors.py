"""
Test CORS configuration for the API
"""

import pytest
from fastapi.testclient import TestClient
from artificial_u.api.app import app


def test_cors_headers_from_allowed_origin():
    """Test CORS headers are returned for requests from allowed origins"""
    client = TestClient(app)

    # Test with localhost:5173 origin (should be allowed)
    response = client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" in response.headers
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert "Access-Control-Allow-Credentials" in response.headers
    assert response.headers["Access-Control-Allow-Credentials"] == "true"


def test_cors_preflight_request():
    """Test CORS preflight requests are handled correctly"""
    client = TestClient(app)

    # Send OPTIONS request with Origin and Access-Control-Request-Method headers
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization",
        },
    )

    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" in response.headers
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert "Access-Control-Allow-Methods" in response.headers
    assert "POST" in response.headers["Access-Control-Allow-Methods"]
    assert "Access-Control-Allow-Headers" in response.headers
    assert "Content-Type" in response.headers["Access-Control-Allow-Headers"]
    assert "Authorization" in response.headers["Access-Control-Allow-Headers"]


def test_cors_headers_absent_for_non_cors_request():
    """Test CORS headers are not included for non-CORS requests"""
    client = TestClient(app)

    # A normal request without Origin header
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response.headers


def test_cors_from_disallowed_origin():
    """Test requests from disallowed origins don't get CORS headers"""
    client = TestClient(app)

    # Test with a domain not in the allowlist
    response = client.get(
        "/api/v1/health", headers={"Origin": "http://malicious-site.com"}
    )

    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response.headers
