"""Authentication API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from src.auth.dependencies import (
    get_current_user, 
    require_auth, 
    rate_limit_auth, 
    rate_limit_api,
    get_client_ip
)
from src.auth.jwt import JWTHandler, create_tokens, refresh_access_token
from src.auth.models import (
    User, UserRepository, APIKeyRepository, UserCreate, UserLogin, UserResponse, 
    TokenResponse, RefreshTokenRequest, UserUpdate,
    APIKeyCreate, APIKeyResponse, APIKeyList
)
from src.database.postgres import get_db
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(rate_limit_auth)
):
    """Register a new user."""
    client_ip = get_client_ip(request)
    logger.info(f"Registration attempt from {client_ip} for email: {user_data.email}")
    
    try:
        user = UserRepository.create_user(db, user_data)
        logger.info(f"User registered successfully: {user.email}")
        
        return UserResponse.from_orm(user)
        
    except ValueError as e:
        logger.warning(f"Registration failed for {user_data.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error for {user_data.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(rate_limit_auth)
):
    """Login user and return JWT tokens."""
    client_ip = get_client_ip(request)
    logger.info(f"Login attempt from {client_ip} for email: {user_data.email}")
    
    try:
        # Authenticate user
        user = UserRepository.authenticate_user(db, user_data.email, user_data.password)
        if not user:
            logger.warning(f"Failed login attempt for {user_data.email} from {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Create tokens
        tokens = create_tokens(str(user.id), user.email, user.is_superuser)
        
        logger.info(f"User logged in successfully: {user.email}")
        
        return TokenResponse(**tokens)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {user_data.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(
    token_data: RefreshTokenRequest,
    request: Request,
    _: bool = Depends(rate_limit_api)
):
    """Refresh access token using refresh token."""
    client_ip = get_client_ip(request)
    logger.info(f"Token refresh attempt from {client_ip}")
    
    try:
        new_tokens = refresh_access_token(token_data.refresh_token)
        logger.info(f"Token refreshed successfully from {client_ip}")
        return new_tokens
        
    except Exception as e:
        logger.warning(f"Token refresh failed from {client_ip}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Logout user and blacklist token."""
    client_ip = get_client_ip(request)
    
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        
        # Blacklist the token
        if JWTHandler.blacklist_token(token):
            logger.info(f"User {current_user.email} logged out from {client_ip}")
            return {"message": "Successfully logged out"}
    
    logger.warning(f"Logout attempt without valid token from {client_ip}")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: bool = Depends(rate_limit_api)
):
    """Update current user information."""
    client_ip = get_client_ip(request)
    logger.info(f"User update attempt from {client_ip} for user: {current_user.email}")
    
    try:
        updated_user = UserRepository.update_user(db, str(current_user.id), user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User updated successfully: {updated_user.email}")
        return UserResponse.from_orm(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User update error for {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Update failed"
        )


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: bool = Depends(rate_limit_api)
):
    """Create a new API key."""
    client_ip = get_client_ip(request)
    logger.info(f"API key creation from {client_ip} for user: {current_user.email}")
    
    try:
        api_key = APIKeyRepository.create_api_key(db, str(current_user.id), key_data)
        
        logger.info(f"API key created for user: {current_user.email}")
        
        return APIKeyResponse(
            id=str(api_key.id),
            name=api_key.name,
            key=api_key.raw_key,  # Only shown once
            permissions=api_key.permissions,
            expires_at=api_key.expires_at,
            created_at=api_key.created_at
        )
        
    except Exception as e:
        logger.error(f"API key creation error for {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key creation failed"
        )


@router.get("/api-keys", response_model=List[APIKeyList])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: bool = Depends(rate_limit_api)
):
    """List user's API keys."""
    try:
        api_keys = APIKeyRepository.get_api_keys_for_user(db, str(current_user.id))
        
        return [
            APIKeyList(
                id=str(key.id),
                name=key.name,
                permissions=key.permissions,
                last_used_at=key.last_used_at,
                expires_at=key.expires_at,
                is_active=key.is_active,
                created_at=key.created_at
            )
            for key in api_keys
        ]
        
    except Exception as e:
        logger.error(f"API key listing error for {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys"
        )


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: bool = Depends(rate_limit_api)
):
    """Delete an API key."""
    client_ip = get_client_ip(request)
    logger.info(f"API key deletion from {client_ip} for user: {current_user.email}")
    
    try:
        success = APIKeyRepository.delete_api_key(db, key_id, str(current_user.id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        logger.info(f"API key {key_id} deleted for user: {current_user.email}")
        return {"message": "API key deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key deletion error for {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API key"
        )


@router.post("/forgot-password")
async def forgot_password(
    email: str,
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(rate_limit_auth)
):
    """Request password reset."""
    client_ip = get_client_ip(request)
    logger.info(f"Password reset request from {client_ip} for email: {email}")
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(rate_limit_auth)
):
    """Reset password with token."""
    client_ip = get_client_ip(request)
    logger.info(f"Password reset attempt from {client_ip}")
    
    # Placeholder implementation
    return {"message": "Password reset functionality will be implemented later"}