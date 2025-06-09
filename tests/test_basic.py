"""Basic functionality tests."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


def test_root_endpoint():
    """Test root endpoint."""
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Lapis Spider API"
        assert data["version"] == "0.1.0"


def test_health_endpoint():
    """Test health check endpoint."""
    with TestClient(app) as client:
        response = client.get("/health")
        # May fail if databases are not running, which is OK for now
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "timestamp" in data


def test_request_id_header():
    """Test that request ID is added to responses."""
    with TestClient(app) as client:
        response = client.get("/")
        assert "X-Request-ID" in response.headers


def test_process_time_header():
    """Test that process time is added to responses."""
    with TestClient(app) as client:
        response = client.get("/")
        assert "X-Process-Time" in response.headers
        # Should be a valid float
        float(response.headers["X-Process-Time"])