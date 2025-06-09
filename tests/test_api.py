"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import jwt

from src.main import app
from src.auth.models import User
from src.config import settings


class TestAuthAPI:
    """Test authentication endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        with patch('src.database.postgres.get_db') as mock:
            db = MagicMock()
            mock.return_value = db
            yield db
    
    def test_register_success(self, client, mock_db):
        """Test successful user registration."""
        # Mock database queries
        mock_db.execute.return_value.fetchone.return_value = None  # No existing user
        
        response = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "id" in data
    
    def test_register_duplicate_email(self, client, mock_db):
        """Test registration with duplicate email."""
        # Mock existing user
        mock_db.execute.return_value.fetchone.return_value = ("user-123",)
        
        response = client.post("/auth/register", json={
            "email": "existing@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        })
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_login_success(self, client, mock_db):
        """Test successful login."""
        from src.utils.hashing import hash_password
        
        # Mock user data
        password_hash = hash_password("SecurePass123!")
        mock_db.execute.return_value.fetchone.return_value = (
            "user-123",  # id
            "test@example.com",  # email
            password_hash,  # password_hash
            True,  # is_active
            "Test User"  # full_name
        )
        
        response = client.post("/auth/login", data={
            "username": "test@example.com",
            "password": "SecurePass123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client, mock_db):
        """Test login with invalid credentials."""
        mock_db.execute.return_value.fetchone.return_value = None
        
        response = client.post("/auth/login", data={
            "username": "test@example.com",
            "password": "WrongPassword"
        })
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]


class TestCrawlAPI:
    """Test crawl endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        token = jwt.encode(
            {"sub": "user-123", "exp": datetime.utcnow() + timedelta(hours=1)},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def mock_user(self):
        """Mock current user."""
        with patch('src.auth.dependencies.get_current_user') as mock:
            user = User(
                id="user-123",
                email="test@example.com",
                full_name="Test User",
                is_active=True
            )
            mock.return_value = user
            yield user
    
    @patch('src.api.crawl.crawl_website_task.delay')
    def test_start_crawl_success(self, mock_task, client, auth_headers, mock_user):
        """Test starting a crawl job."""
        with patch('src.database.postgres.get_db') as mock_db:
            db = MagicMock()
            mock_db.return_value = db
            
            # Mock website query
            db.execute.return_value.fetchone.return_value = (
                "website-123",  # id
                "https://example.com",  # url
                {"max_pages": 100}  # crawl_config
            )
            
            # Mock task
            mock_task.return_value.id = "task-123"
            
            response = client.post(
                "/crawl/start",
                json={"website_id": "website-123"},
                headers=auth_headers
            )
            
            assert response.status_code == 202
            data = response.json()
            assert "crawl_job_id" in data
            assert data["status"] == "queued"
    
    def test_start_crawl_unauthorized(self, client):
        """Test starting crawl without authentication."""
        response = client.post("/crawl/start", json={"website_id": "website-123"})
        assert response.status_code == 401
    
    def test_get_crawl_status(self, client, auth_headers, mock_user):
        """Test getting crawl job status."""
        with patch('src.database.postgres.get_db') as mock_db:
            db = MagicMock()
            mock_db.return_value = db
            
            # Mock crawl job query
            db.execute.return_value.fetchone.return_value = (
                "job-123",  # id
                "website-123",  # website_id
                "completed",  # status
                datetime.utcnow(),  # created_at
                datetime.utcnow(),  # started_at
                datetime.utcnow(),  # completed_at
                100,  # pages_crawled
                None,  # error_message
                {"total_pages": 100}  # statistics
            )
            
            response = client.get("/crawl/status/job-123", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["pages_crawled"] == 100


class TestContentAPI:
    """Test content endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        token = jwt.encode(
            {"sub": "user-123", "exp": datetime.utcnow() + timedelta(hours=1)},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def mock_user(self):
        """Mock current user."""
        with patch('src.auth.dependencies.get_current_user') as mock:
            user = User(
                id="user-123",
                email="test@example.com",
                full_name="Test User",
                is_active=True
            )
            mock.return_value = user
            yield user
    
    def test_list_website_pages(self, client, auth_headers, mock_user):
        """Test listing website pages."""
        with patch('src.database.postgres.get_db') as mock_db:
            db = MagicMock()
            mock_db.return_value = db
            
            # Mock website verification
            db.execute.return_value.fetchone.side_effect = [
                ("website-123",),  # Website exists
                None  # End of results
            ]
            
            # Mock pages query
            db.execute.return_value.fetchall.return_value = [
                (
                    "page-1",  # id
                    "https://example.com/page1",  # url
                    "Page 1",  # title
                    "hash1",  # content_hash
                    datetime.utcnow()  # last_modified
                ),
                (
                    "page-2",
                    "https://example.com/page2",
                    "Page 2",
                    "hash2",
                    datetime.utcnow()
                )
            ]
            
            response = client.get("/content/website-123/pages", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["url"] == "https://example.com/page1"
    
    @patch('src.ai.tasks.process_page_with_ai.delay')
    def test_process_page_with_ai(self, mock_task, client, auth_headers, mock_user):
        """Test AI processing request."""
        with patch('src.database.postgres.get_db') as mock_db:
            db = MagicMock()
            mock_db.return_value = db
            
            # Mock page verification
            db.execute.return_value.fetchall.return_value = [
                ("page-1", "website-123"),
                ("page-2", "website-123")
            ]
            
            # Mock task
            mock_task.return_value.id = "task-123"
            
            response = client.post(
                "/content/process",
                json={"page_ids": ["page-1", "page-2"]},
                headers=auth_headers
            )
            
            assert response.status_code == 202
            data = response.json()
            assert data["pages_queued"] == 2


class TestMonitorAPI:
    """Test monitoring endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        token = jwt.encode(
            {"sub": "user-123", "exp": datetime.utcnow() + timedelta(hours=1)},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def mock_user(self):
        """Mock current user."""
        with patch('src.auth.dependencies.get_current_user') as mock:
            user = User(
                id="user-123",
                email="test@example.com",
                full_name="Test User",
                is_active=True
            )
            mock.return_value = user
            yield user
    
    def test_add_website_monitoring(self, client, auth_headers, mock_user):
        """Test adding website to monitoring."""
        with patch('src.database.postgres.get_db') as mock_db:
            db = MagicMock()
            mock_db.return_value = db
            
            # Mock website verification
            db.execute.return_value.fetchone.side_effect = [
                ("website-123", "https://example.com", "Example Site"),  # Website exists
                None  # No existing schedule
            ]
            
            response = client.post(
                "/monitor/website",
                json={
                    "website_id": "website-123",
                    "config": {
                        "check_frequency": "daily",
                        "notify_on_changes": True
                    }
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["website_id"] == "website-123"
            assert data["is_active"] is True


@pytest.fixture
def test_database():
    """Create test database."""
    # This would create a test database for integration tests
    pass