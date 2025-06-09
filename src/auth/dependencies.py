"""Authentication dependencies for FastAPI."""

from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.auth.jwt import JWTHandler, TokenData
from src.auth.models import User, UserRepository, APIKeyRepository
from src.database.postgres import get_db
from src.database.redis import RateLimiter
from src.config import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)

# Rate limiter instance
rate_limiter = RateLimiter()


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Verify JWT token
        payload = JWTHandler.verify_token(credentials.credentials)
        token_data = TokenData.from_dict(payload)
        
        # Get user from database
        user = UserRepository.get_user_by_id(db, token_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise None."""
    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and ensure they are a superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_user_from_api_key(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get user from API key in header."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
    
    try:
        # Validate API key and get associated user
        api_key_record = APIKeyRepository.validate_api_key(db, api_key)
        if api_key_record:
            user = UserRepository.get_user_by_id(db, str(api_key_record.user_id))
            if user and user.is_active:
                return user
    except Exception as e:
        logger.error(f"API key authentication error: {e}")
    
    return None


async def require_auth(
    request: Request,
    jwt_user: Optional[User] = Depends(get_current_user_optional),
    api_user: Optional[User] = Depends(get_user_from_api_key)
) -> User:
    """Require authentication via JWT or API key."""
    user = jwt_user or api_user
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


class RateLimitDependency:
    """Rate limiting dependency."""
    
    def __init__(self, calls: int, window: int):
        self.calls = calls
        self.window = window
    
    def __call__(self, request: Request):
        """Apply rate limiting."""
        if not settings.rate_limit_enabled:
            return True
        
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        # Check rate limit
        allowed, info = rate_limiter.is_allowed(
            f"rate_limit:{client_ip}",
            self.calls,
            self.window
        )
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(info["window"]),
                }
            )
        
        return True


# Rate limit instances for different endpoints
rate_limit_auth = RateLimitDependency(
    calls=5,  # 5 attempts
    window=300  # 5 minutes
)

rate_limit_api = RateLimitDependency(
    calls=settings.rate_limit_per_minute,
    window=60  # 1 minute
)

rate_limit_strict = RateLimitDependency(
    calls=10,
    window=300  # 10 calls per 5 minutes
)


def get_client_ip(request: Request) -> str:
    """Get client IP address."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"


def check_permissions(required_permissions: list):
    """Dependency to check user permissions."""
    def permission_checker(current_user: User = Depends(get_current_user)):
        # For now, just check if user is active
        # In the future, implement actual permission system
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not active"
            )
        return current_user
    
    return permission_checker