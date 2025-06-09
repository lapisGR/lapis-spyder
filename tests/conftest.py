"""Test configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.config import settings, TestSettings


@pytest.fixture(scope="session")
def test_settings():
    """Test settings fixture."""
    return TestSettings()


@pytest.fixture
def client():
    """Test client fixture."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_db_session():
    """Mock database session fixture."""
    # This will be implemented with actual database fixtures
    pass