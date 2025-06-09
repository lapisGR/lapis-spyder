"""Security middleware for authentication and protection."""

import time
from typing import Dict, List, Optional

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings
from src.database.redis import RateLimiter
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)
        
        # Security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }
        
        # Add HSTS in production
        if settings.is_production:
            security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Add CSP for non-API endpoints
        if not request.url.path.startswith(("/api", "/docs", "/redoc", "/openapi.json")):
            security_headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'"
            )
        
        # Apply headers
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Global rate limiting middleware."""
    
    def __init__(self, app, calls_per_minute: int = 60, calls_per_hour: int = 1000):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.calls_per_hour = calls_per_hour
        self.rate_limiter = RateLimiter()
        
        # Paths exempt from rate limiting
        self.exempt_paths = {
            "/health",
            "/",
            "/docs",
            "/redoc",
            "/openapi.json"
        }
    
    def get_client_key(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Check for forwarded IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key[:10]}"  # Use first 10 chars of API key
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            return f"token:{token[:10]}"  # Use first 10 chars of token
        
        return f"ip:{client_ip}"
    
    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting."""
        # Skip rate limiting if disabled
        if not settings.rate_limit_enabled:
            return await call_next(request)
        
        # Skip exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        client_key = self.get_client_key(request)
        
        # Check per-minute limit
        minute_allowed, minute_info = self.rate_limiter.is_allowed(
            f"rate_limit_minute:{client_key}",
            self.calls_per_minute,
            60
        )
        
        # Check per-hour limit
        hour_allowed, hour_info = self.rate_limiter.is_allowed(
            f"rate_limit_hour:{client_key}",
            self.calls_per_hour,
            3600
        )
        
        if not minute_allowed or not hour_allowed:
            # Use the more restrictive limit for error info
            info = minute_info if not minute_allowed else hour_info
            
            logger.warning(f"Rate limit exceeded for {client_key} on {request.url.path}")
            
            return Response(
                content='{"error": "Rate limit exceeded"}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Content-Type": "application/json",
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(info["window"]),
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit-Minute"] = str(self.calls_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(minute_info["remaining"])
        response.headers["X-RateLimit-Limit-Hour"] = str(self.calls_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(hour_info["remaining"])
        
        return response


class APIKeyValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API keys in headers."""
    
    def __init__(self, app):
        super().__init__(app)
        # Paths that require API key validation
        self.protected_paths = [
            "/crawl",
            "/content",
            "/monitor"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Validate API key for protected paths."""
        path = request.url.path
        
        # Check if path requires API key validation
        requires_validation = any(
            path.startswith(protected_path) 
            for protected_path in self.protected_paths
        )
        
        if requires_validation:
            api_key = request.headers.get("X-API-Key")
            auth_header = request.headers.get("Authorization")
            
            # Allow if either API key or Bearer token is present
            if not api_key and not (auth_header and auth_header.startswith("Bearer ")):
                return Response(
                    content='{"error": "API key or authorization token required"}',
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    headers={"Content-Type": "application/json"}
                )
        
        return await call_next(request)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for general request validation."""
    
    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024):  # 10MB
        super().__init__(app)
        self.max_request_size = max_request_size
    
    async def dispatch(self, request: Request, call_next):
        """Validate request parameters."""
        # Check content length
        content_length = request.headers.get("Content-Length")
        if content_length and int(content_length) > self.max_request_size:
            return Response(
                content='{"error": "Request too large"}',
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                headers={"Content-Type": "application/json"}
            )
        
        # Validate User-Agent
        user_agent = request.headers.get("User-Agent", "")
        if len(user_agent) > 500:  # Prevent extremely long user agents
            logger.warning(f"Suspiciously long User-Agent: {user_agent[:100]}...")
        
        # Block common attack patterns in URL
        suspicious_patterns = [
            "../", "\\x", "%2e%2e", "<script", "javascript:",
            "data:text/html", "vbscript:", "onload=", "onerror="
        ]
        
        full_url = str(request.url)
        for pattern in suspicious_patterns:
            if pattern.lower() in full_url.lower():
                logger.warning(f"Suspicious URL pattern detected: {pattern} in {full_url}")
                return Response(
                    content='{"error": "Invalid request"}',
                    status_code=status.HTTP_400_BAD_REQUEST,
                    headers={"Content-Type": "application/json"}
                )
        
        return await call_next(request)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Middleware to log security-relevant events."""
    
    def __init__(self, app):
        super().__init__(app)
        # Paths to audit
        self.audit_paths = [
            "/auth/login",
            "/auth/register", 
            "/auth/logout",
            "/auth/api-keys"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Log security events."""
        start_time = time.time()
        
        # Get client info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "Unknown")
        
        # Process request
        response = await call_next(request)
        
        # Log if it's an auditable path
        if any(request.url.path.startswith(path) for path in self.audit_paths):
            duration = time.time() - start_time
            
            log_data = {
                "event": "api_request",
                "path": request.url.path,
                "method": request.method,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "status_code": response.status_code,
                "duration": round(duration, 3),
                "timestamp": time.time()
            }
            
            if response.status_code >= 400:
                logger.warning(f"Security audit: {log_data}")
            else:
                logger.info(f"Security audit: {log_data}")
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"