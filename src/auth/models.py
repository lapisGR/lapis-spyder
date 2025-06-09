"""Authentication models and schemas."""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, validator

from src.database.postgres import Base
from src.utils.hashing import hash_password, verify_password, generate_api_key
from src.utils.logging import get_logger

logger = get_logger(__name__)


# SQLAlchemy Models
class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    api_key = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
    
    def set_password(self, password: str):
        """Set user password."""
        self.password_hash = hash_password(password)
    
    def verify_password(self, password: str) -> bool:
        """Verify user password."""
        return verify_password(password, self.password_hash)
    
    def generate_api_key(self):
        """Generate new API key."""
        self.api_key = generate_api_key()


class APIKey(Base):
    """API Key model."""
    
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    permissions = Column(JSON, default=list)
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name={self.name})>"


# Pydantic Schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    
    class Config:
        from_attributes = True


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator("password")
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, and one digit"
            )
        
        return v


class UserUpdate(BaseModel):
    """User update schema."""
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    is_active: Optional[bool] = None
    
    @validator("password")
    def validate_password(cls, v):
        """Validate password strength."""
        if v is None:
            return v
        
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, and one digit"
            )
        
        return v


class UserResponse(UserBase):
    """User response schema."""
    id: str
    api_key: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    
    @validator("id", pre=True)
    def convert_uuid_to_string(cls, v):
        """Convert UUID to string."""
        return str(v) if v else None


class UserLogin(BaseModel):
    """User login schema."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(default=1800)  # 30 minutes in seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class APIKeyCreate(BaseModel):
    """API key creation schema."""
    name: str = Field(..., min_length=1, max_length=255)
    permissions: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    """API key response schema."""
    id: str
    name: str
    key: str  # Only returned on creation
    permissions: List[str]
    expires_at: Optional[datetime]
    created_at: datetime
    
    @validator("id", pre=True)
    def convert_uuid_to_string(cls, v):
        """Convert UUID to string."""
        return str(v) if v else None


class APIKeyList(BaseModel):
    """API key list item schema."""
    id: str
    name: str
    permissions: List[str]
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    
    @validator("id", pre=True)
    def convert_uuid_to_string(cls, v):
        """Convert UUID to string."""
        return str(v) if v else None


# Database operations
class APIKeyRepository:
    """API Key database operations."""
    
    @staticmethod
    def create_api_key(db: Session, user_id: str, key_data: APIKeyCreate) -> APIKey:
        """Create new API key."""
        from src.utils.hashing import generate_api_key, hash_content
        
        # Generate API key
        raw_key = generate_api_key()
        key_hash = hash_content(raw_key)
        
        # Create API key record
        api_key = APIKey(
            user_id=user_id,
            key_hash=key_hash,
            name=key_data.name,
            permissions=key_data.permissions,
            expires_at=key_data.expires_at
        )
        
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        
        logger.info(f"Created API key for user {user_id}: {key_data.name}")
        
        # Return the raw key for the response (only time it's shown)
        api_key.raw_key = raw_key
        return api_key
    
    @staticmethod
    def get_api_keys_for_user(db: Session, user_id: str) -> List[APIKey]:
        """Get all API keys for a user."""
        return db.query(APIKey).filter(
            APIKey.user_id == user_id,
            APIKey.is_active == True
        ).order_by(APIKey.created_at.desc()).all()
    
    @staticmethod
    def get_api_key_by_id(db: Session, key_id: str, user_id: str) -> Optional[APIKey]:
        """Get API key by ID (for the user only)."""
        try:
            return db.query(APIKey).filter(
                APIKey.id == key_id,
                APIKey.user_id == user_id,
                APIKey.is_active == True
            ).first()
        except Exception as e:
            logger.error(f"Error getting API key {key_id}: {e}")
            return None
    
    @staticmethod
    def validate_api_key(db: Session, raw_key: str) -> Optional[APIKey]:
        """Validate API key and return associated key record."""
        from src.utils.hashing import hash_content
        
        try:
            key_hash = hash_content(raw_key)
            api_key = db.query(APIKey).filter(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True
            ).first()
            
            if api_key:
                # Check expiration
                if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                    return None
                
                # Update last used timestamp
                api_key.last_used_at = datetime.utcnow()
                db.commit()
                
                return api_key
            
            return None
            
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return None
    
    @staticmethod
    def delete_api_key(db: Session, key_id: str, user_id: str) -> bool:
        """Delete API key."""
        try:
            api_key = APIKeyRepository.get_api_key_by_id(db, key_id, user_id)
            if not api_key:
                return False
            
            api_key.is_active = False
            db.commit()
            
            logger.info(f"Deleted API key {key_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting API key {key_id}: {e}")
            return False


class UserRepository:
    """User database operations."""
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Create new user."""
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Create new user
        user = User(email=user_data.email)
        user.set_password(user_data.password)
        user.generate_api_key()
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"Created new user: {user.email}")
        return user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            return db.query(User).filter(User.id == user_id, User.is_active == True).first()
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            return db.query(User).filter(User.email == email, User.is_active == True).first()
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    @staticmethod
    def get_user_by_api_key(db: Session, api_key: str) -> Optional[User]:
        """Get user by API key."""
        try:
            return db.query(User).filter(User.api_key == api_key, User.is_active == True).first()
        except Exception as e:
            logger.error(f"Error getting user by API key: {e}")
            return None
    
    @staticmethod
    def update_user(db: Session, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update user."""
        user = UserRepository.get_user_by_id(db, user_id)
        if not user:
            return None
        
        update_data = user_data.dict(exclude_unset=True)
        
        if "password" in update_data:
            user.set_password(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"Updated user: {user.email}")
        return user
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user."""
        user = UserRepository.get_user_by_email(db, email)
        if not user or not user.verify_password(password):
            return None
        return user