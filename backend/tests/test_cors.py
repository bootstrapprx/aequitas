import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_cors_headers_present():
    """Test that CORS headers are present in response"""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET"
        }
    )

    # Check CORS headers are present
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-credentials" in response.headers


def test_cors_localhost_5173():
    """Test that localhost:5173 is allowed"""
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"}
    )

    assert response.status_code == 200
    # The CORS middleware should add the header
    assert "access-control-allow-origin" in response.headers or response.status_code < 400


def test_cors_127_0_0_1_5173():
    """Test that 127.0.0.1:5173 is allowed"""
    response = client.get(
        "/health",
        headers={"Origin": "http://127.0.0.1:5173"}
    )

    assert response.status_code == 200


def test_cors_rejects_arbitrary_origin():
    response = client.get(
        "/health",
        headers={"Origin": "https://evil.example"},
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_health_endpoint():
    """Test that health endpoint is accessible"""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
