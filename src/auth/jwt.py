"""JWT token handling and utilities."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from fastapi import HTTPException, status

from src.config import settings
from src.database.redis import RedisCache
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Initialize token blacklist cache
token_blacklist = RedisCache(prefix="blacklist", ttl=settings.jwt_access_token_expire_minutes * 60)


class JWTHandler:
    """JWT token handler with blacklist support."""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        
        try:
            encoded_jwt = jwt.encode(
                to_encode, 
                settings.jwt_secret_key, 
                algorithm=settings.jwt_algorithm
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create access token"
            )
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        try:
            encoded_jwt = jwt.encode(
                to_encode,
                settings.jwt_secret_key,
                algorithm=settings.jwt_algorithm
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create refresh token"
            )
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode token."""
        try:
            # Check if token is blacklisted
            if token_blacklist.exists(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            
            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Check expiration
            exp = payload.get("exp")
            if exp is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing expiration",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if datetime.utcnow() > datetime.fromtimestamp(exp):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return payload
            
        except JWTError as e:
            logger.warning(f"JWT decode error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def blacklist_token(token: str) -> bool:
        """Add token to blacklist."""
        try:
            # Decode to get expiration time
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
                options={"verify_exp": False}  # Don't verify expiration for blacklisting
            )
            
            exp = payload.get("exp")
            if exp:
                # Calculate TTL until token would naturally expire
                ttl = max(0, exp - int(datetime.utcnow().timestamp()))
                token_blacklist.set(token, True, ttl=ttl)
                return True
                
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            
        return False
    
    @staticmethod
    def get_token_claims(token: str) -> Optional[Dict[str, Any]]:
        """Get token claims without verification (for debugging)."""
        try:
            return jwt.get_unverified_claims(token)
        except Exception:
            return None


class TokenData:
    """Token data model."""
    
    def __init__(self, user_id: str, email: str, is_superuser: bool = False):
        self.user_id = user_id
        self.email = email
        self.is_superuser = is_superuser
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JWT payload."""
        return {
            "sub": self.user_id,
            "email": self.email,
            "is_superuser": self.is_superuser,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenData":
        """Create from dictionary."""
        return cls(
            user_id=data["sub"],
            email=data["email"],
            is_superuser=data.get("is_superuser", False)
        )


def create_tokens(user_id: str, email: str, is_superuser: bool = False) -> Dict[str, str]:
    """Create both access and refresh tokens."""
    token_data = TokenData(user_id, email, is_superuser)
    payload = token_data.to_dict()
    
    access_token = JWTHandler.create_access_token(payload)
    refresh_token = JWTHandler.create_refresh_token(payload)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


def refresh_access_token(refresh_token: str) -> Dict[str, str]:
    """Create new access token from refresh token."""
    payload = JWTHandler.verify_token(refresh_token, token_type="refresh")
    token_data = TokenData.from_dict(payload)
    
    # Create new access token
    new_access_token = JWTHandler.create_access_token(token_data.to_dict())
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }