"""
Test CORS configuration for the API
"""

import pytest
from fastapi.testclient import TestClient

from artificial_u.api.app import app
from artificial_u.api.middlewares.cors_middleware import split_origins


@pytest.mark.unit
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


@pytest.mark.unit
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


@pytest.mark.unit
def test_cors_headers_absent_for_non_cors_request():
    """Test CORS headers are not included for non-CORS requests"""
    client = TestClient(app)

    # A normal request without Origin header
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response.headers


@pytest.mark.unit
def test_cors_from_disallowed_origin():
    """Test requests from disallowed origins don't get CORS headers"""
    client = TestClient(app)

    # Test with a domain not in the allowlist
    response = client.get("/api/v1/health", headers={"Origin": "http://malicious-site.com"})

    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response.headers


@pytest.mark.unit
def test_cors_allows_configured_wildcard_subdomain():
    """An origin under a configured ``https://*.domain`` entry is allowed."""
    client = TestClient(app)

    response = client.get("/api/v1/health", headers={"Origin": "https://www.artificial-u.com"})

    assert response.headers["Access-Control-Allow-Origin"] == "https://www.artificial-u.com"


@pytest.mark.unit
@pytest.mark.parametrize(
    "origin",
    [
        "https://evil.example.com",
        "https://artificial-u.com.evil.example.com",
        "https://evilartificial-u.com",
        "http://www.artificial-u.com",
    ],
)
def test_cors_rejects_origins_outside_the_wildcard(origin):
    client = TestClient(app)

    response = client.get("/api/v1/health", headers={"Origin": origin})

    assert "Access-Control-Allow-Origin" not in response.headers


@pytest.mark.unit
def test_split_origins_separates_wildcards():
    exact, regex = split_origins(["http://localhost:5173", "https://*.example.com"])

    assert exact == ["http://localhost:5173"]
    assert regex == r"https://[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.example\.com"
    assert split_origins(["http://localhost:5173"]) == (["http://localhost:5173"], None)
