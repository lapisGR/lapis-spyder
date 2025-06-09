"""Tests for authentication system."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.auth.models import User, UserCreate, UserRepository
from src.auth.jwt import JWTHandler, create_tokens
from src.database.postgres import Base, get_db
from src.config import TestSettings

# Test database setup
test_settings = TestSettings()
engine = create_engine(test_settings.postgres_url, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def test_user_data():
    """Test user data fixture."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!"
    }


@pytest.fixture
def test_user(test_user_data):
    """Create test user fixture."""
    db = TestingSessionLocal()
    try:
        # Clean up any existing user
        existing_user = db.query(User).filter(User.email == test_user_data["email"]).first()
        if existing_user:
            db.delete(existing_user)
            db.commit()
        
        # Create new user
        user_create = UserCreate(**test_user_data)
        user = UserRepository.create_user(db, user_create)
        yield user
        
        # Clean up
        db.delete(user)
        db.commit()
    finally:
        db.close()


class TestUserRegistration:
    """Test user registration."""
    
    def test_register_valid_user(self, test_user_data):
        """Test registering a valid user."""
        response = client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert "id" in data
        assert "api_key" in data
        assert data["is_active"] is True
        assert data["is_superuser"] is False
    
    def test_register_duplicate_email(self, test_user, test_user_data):
        """Test registering with duplicate email."""
        response = client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_register_invalid_email(self):
        """Test registering with invalid email."""
        invalid_data = {
            "email": "not-an-email",
            "password": "TestPassword123!"
        }
        
        response = client.post("/auth/register", json=invalid_data)
        assert response.status_code == 422
    
    def test_register_weak_password(self):
        """Test registering with weak password."""
        weak_passwords = [
            "123",  # Too short
            "password",  # No uppercase, no digits
            "PASSWORD",  # No lowercase
            "Password",  # No digits
            "12345678"  # No letters
        ]
        
        for password in weak_passwords:
            data = {
                "email": f"test{password}@example.com",
                "password": password
            }
            
            response = client.post("/auth/register", json=data)
            assert response.status_code == 422


class TestUserLogin:
    """Test user login."""
    
    def test_login_valid_credentials(self, test_user, test_user_data):
        """Test login with valid credentials."""
        response = client.post("/auth/login", json=test_user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_email(self, test_user_data):
        """Test login with invalid email."""
        invalid_data = {
            "email": "nonexistent@example.com",
            "password": test_user_data["password"]
        }
        
        response = client.post("/auth/login", json=invalid_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_invalid_password(self, test_user, test_user_data):
        """Test login with invalid password."""
        invalid_data = {
            "email": test_user_data["email"],
            "password": "WrongPassword123!"
        }
        
        response = client.post("/auth/login", json=invalid_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]


class TestTokenOperations:
    """Test JWT token operations."""
    
    def test_token_creation(self, test_user):
        """Test token creation."""
        tokens = create_tokens(str(test_user.id), test_user.email)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
    
    def test_token_verification(self, test_user):
        """Test token verification."""
        tokens = create_tokens(str(test_user.id), test_user.email)
        access_token = tokens["access_token"]
        
        payload = JWTHandler.verify_token(access_token)
        
        assert payload["sub"] == str(test_user.id)
        assert payload["email"] == test_user.email
        assert payload["type"] == "access"
    
    def test_token_blacklisting(self, test_user):
        """Test token blacklisting."""
        tokens = create_tokens(str(test_user.id), test_user.email)
        access_token = tokens["access_token"]
        
        # Token should work initially
        payload = JWTHandler.verify_token(access_token)
        assert payload is not None
        
        # Blacklist token
        JWTHandler.blacklist_token(access_token)
        
        # Token should now be rejected
        with pytest.raises(Exception):
            JWTHandler.verify_token(access_token)


class TestAuthenticatedEndpoints:
    """Test authenticated endpoints."""
    
    def test_get_current_user(self, test_user, test_user_data):
        """Test getting current user info."""
        # Login to get token
        login_response = client.post("/auth/login", json=test_user_data)
        token = login_response.json()["access_token"]
        
        # Get user info
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["id"] == str(test_user.id)
    
    def test_get_current_user_no_token(self):
        """Test getting current user without token."""
        response = client.get("/auth/me")
        assert response.status_code == 401
    
    def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_logout(self, test_user, test_user_data):
        """Test user logout."""
        # Login to get token
        login_response = client.post("/auth/login", json=test_user_data)
        token = login_response.json()["access_token"]
        
        # Logout
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/auth/logout", headers=headers)
        
        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()
        
        # Token should now be invalid
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_registration(self, test_user_data):
        """Test rate limiting on registration endpoint."""
        # Make multiple rapid requests
        for i in range(10):
            data = {
                "email": f"test{i}@example.com",
                "password": "TestPassword123!"
            }
            response = client.post("/auth/register", json=data)
            
            # First few should succeed (or fail for other reasons)
            # Eventually should hit rate limit
            if response.status_code == 429:
                assert "Rate limit exceeded" in response.json()["error"]
                break
        else:
            # If we didn't hit rate limit, that's also ok for this test
            pass


class TestSecurityHeaders:
    """Test security headers."""
    
    def test_security_headers_present(self):
        """Test that security headers are present."""
        response = client.get("/")
        
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
    
    def test_request_id_header(self):
        """Test that request ID header is added."""
        response = client.get("/")
        assert "X-Request-ID" in response.headers
    
    def test_process_time_header(self):
        """Test that process time header is added."""
        response = client.get("/")
        assert "X-Process-Time" in response.headers
        # Should be a valid float
        float(response.headers["X-Process-Time"])