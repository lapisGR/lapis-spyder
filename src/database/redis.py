"""Redis connection and cache management."""

import json
import pickle
from typing import Any, Optional, Union

import redis
from redis import ConnectionPool

from src.config import settings

# Redis connection pool
redis_pool: Optional[ConnectionPool] = None


def get_redis_pool() -> ConnectionPool:
    """Get or create Redis connection pool."""
    global redis_pool
    
    if redis_pool is None:
        redis_pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            max_connections=50,
            decode_responses=True,
        )
    
    return redis_pool


def get_redis() -> redis.Redis:
    """Get Redis client."""
    return redis.Redis(connection_pool=get_redis_pool())


def check_redis_connection() -> bool:
    """Check if Redis is accessible."""
    try:
        client = get_redis()
        client.ping()
        return True
    except Exception:
        return False


class RedisCache:
    """Redis cache wrapper with common operations."""
    
    def __init__(self, prefix: str = "lapis", ttl: int = None):
        """Initialize cache with prefix and default TTL."""
        self.redis = get_redis()
        self.prefix = prefix
        self.ttl = ttl or settings.redis_cache_ttl
    
    def _make_key(self, key: str) -> str:
        """Create namespaced key."""
        return f"{self.prefix}:{key}"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        full_key = self._make_key(key)
        value = self.redis.get(full_key)
        
        if value is None:
            return default
        
        try:
            # Try to deserialize JSON first
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # Fall back to pickle for complex objects
            try:
                return pickle.loads(value.encode("latin-1"))
            except Exception:
                return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        full_key = self._make_key(key)
        ttl = ttl or self.ttl
        
        try:
            # Try to serialize as JSON first
            serialized = json.dumps(value)
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            serialized = pickle.dumps(value).decode("latin-1")
        
        return self.redis.setex(full_key, ttl, serialized)
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        full_key = self._make_key(key)
        return bool(self.redis.delete(full_key))
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        full_key = self._make_key(key)
        return bool(self.redis.exists(full_key))
    
    def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        full_key = self._make_key(key)
        return self.redis.incrby(full_key, amount)
    
    def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement counter."""
        full_key = self._make_key(key)
        return self.redis.decrby(full_key, amount)
    
    def get_many(self, keys: list) -> dict:
        """Get multiple values."""
        full_keys = [self._make_key(k) for k in keys]
        values = self.redis.mget(full_keys)
        
        result = {}
        for key, value in zip(keys, values):
            if value is not None:
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    try:
                        result[key] = pickle.loads(value.encode("latin-1"))
                    except Exception:
                        result[key] = value
        
        return result
    
    def set_many(self, mapping: dict, ttl: Optional[int] = None) -> bool:
        """Set multiple values."""
        ttl = ttl or self.ttl
        pipe = self.redis.pipeline()
        
        for key, value in mapping.items():
            full_key = self._make_key(key)
            
            try:
                serialized = json.dumps(value)
            except (TypeError, ValueError):
                serialized = pickle.dumps(value).decode("latin-1")
            
            pipe.setex(full_key, ttl, serialized)
        
        results = pipe.execute()
        return all(results)
    
    def clear_namespace(self) -> int:
        """Clear all keys with the cache prefix."""
        pattern = f"{self.prefix}:*"
        keys = self.redis.keys(pattern)
        
        if keys:
            return self.redis.delete(*keys)
        return 0


# Rate limiting
class RateLimiter:
    """Redis-based rate limiter."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize rate limiter."""
        self.redis = redis_client or get_redis()
    
    def is_allowed(self, key: str, limit: int, window: int) -> tuple[bool, dict]:
        """Check if request is allowed within rate limit."""
        full_key = f"rate_limit:{key}"
        
        try:
            pipe = self.redis.pipeline()
            now = self.redis.time()[0]
            window_start = now - window
            
            # Remove old entries
            pipe.zremrangebyscore(full_key, 0, window_start)
            
            # Count requests in current window
            pipe.zcard(full_key)
            
            # Add current request
            pipe.zadd(full_key, {str(now): now})
            
            # Set expiry
            pipe.expire(full_key, window)
            
            results = pipe.execute()
            
            request_count = results[1]
            
            # Check if limit exceeded
            allowed = request_count < limit
            
            # Calculate reset time
            if not allowed:
                oldest_request = self.redis.zrange(full_key, 0, 0, withscores=True)
                if oldest_request:
                    reset_time = int(oldest_request[0][1]) + window
                else:
                    reset_time = now + window
            else:
                reset_time = now + window
            
            return allowed, {
                "limit": limit,
                "remaining": max(0, limit - request_count - 1),
                "reset": reset_time,
                "window": window
            }
            
        except Exception as e:
            # On error, allow the request
            return True, {
                "limit": limit,
                "remaining": limit,
                "reset": 0,
                "window": window
            }