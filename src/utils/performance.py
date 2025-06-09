"""Performance optimization utilities."""

import asyncio
import functools
import time
from typing import Any, Callable, Dict, Optional
from contextlib import asynccontextmanager
import redis
import pickle

from src.database.redis import get_redis
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Manage caching for performance optimization."""
    
    def __init__(self, default_ttl: int = 3600):
        """Initialize cache manager.
        
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self.default_ttl = default_ttl
        self._redis = None
    
    @property
    def redis(self):
        """Get Redis connection."""
        if not self._redis:
            self._redis = get_redis()
        return self._redis
    
    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments."""
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (str, int, float)):
                key_parts.append(str(arg))
            else:
                key_parts.append(str(hash(str(arg))))
        
        # Add keyword arguments
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (str, int, float)):
                key_parts.append(f"{k}:{v}")
            else:
                key_parts.append(f"{k}:{hash(str(v))}")
        
        return ":".join(key_parts)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.redis.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        try:
            ttl = ttl or self.default_ttl
            serialized = pickle.dumps(value)
            self.redis.set(key, serialized, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache invalidate error for pattern {pattern}: {e}")
            return 0


# Global cache instance
cache_manager = CacheManager()


def cached(prefix: str = None, ttl: int = 3600, key_builder: Callable = None):
    """Decorator for caching function results.
    
    Args:
        prefix: Cache key prefix (defaults to function name)
        ttl: Time-to-live in seconds
        key_builder: Custom function to build cache key
    """
    def decorator(func):
        cache_prefix = prefix or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = cache_manager.cache_key(cache_prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {cache_key}, cached with TTL={ttl}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, run in event loop
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(async_wrapper(*args, **kwargs))
            finally:
                loop.close()
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class PerformanceMonitor:
    """Monitor and log performance metrics."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.metrics = {}
    
    @asynccontextmanager
    async def measure(self, operation: str):
        """Context manager to measure operation performance."""
        start_time = time.time()
        
        try:
            yield
        finally:
            duration = time.time() - start_time
            
            # Update metrics
            if operation not in self.metrics:
                self.metrics[operation] = {
                    "count": 0,
                    "total_time": 0,
                    "min_time": float('inf'),
                    "max_time": 0
                }
            
            metric = self.metrics[operation]
            metric["count"] += 1
            metric["total_time"] += duration
            metric["min_time"] = min(metric["min_time"], duration)
            metric["max_time"] = max(metric["max_time"], duration)
            
            # Log slow operations
            if duration > 1.0:
                logger.warning(
                    f"Slow operation '{operation}' took {duration:.2f}s"
                )
    
    def get_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics."""
        result = {}
        
        for operation, metric in self.metrics.items():
            result[operation] = {
                "count": metric["count"],
                "total_time": metric["total_time"],
                "avg_time": metric["total_time"] / metric["count"] if metric["count"] > 0 else 0,
                "min_time": metric["min_time"] if metric["min_time"] != float('inf') else 0,
                "max_time": metric["max_time"]
            }
        
        return result
    
    def reset(self):
        """Reset all metrics."""
        self.metrics = {}


# Global performance monitor
perf_monitor = PerformanceMonitor()


def measure_performance(operation: str = None):
    """Decorator to measure function performance.
    
    Args:
        operation: Operation name (defaults to function name)
    """
    def decorator(func):
        op_name = operation or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            async with perf_monitor.measure(op_name):
                return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                # Manual metric update for sync functions
                if op_name not in perf_monitor.metrics:
                    perf_monitor.metrics[op_name] = {
                        "count": 0,
                        "total_time": 0,
                        "min_time": float('inf'),
                        "max_time": 0
                    }
                
                metric = perf_monitor.metrics[op_name]
                metric["count"] += 1
                metric["total_time"] += duration
                metric["min_time"] = min(metric["min_time"], duration)
                metric["max_time"] = max(metric["max_time"], duration)
                
                if duration > 1.0:
                    logger.warning(
                        f"Slow operation '{op_name}' took {duration:.2f}s"
                    )
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class ConnectionPool:
    """Manage connection pooling for external services."""
    
    def __init__(self, 
                 pool_size: int = 10,
                 max_overflow: int = 5,
                 timeout: float = 30.0):
        """Initialize connection pool.
        
        Args:
            pool_size: Number of persistent connections
            max_overflow: Maximum overflow connections
            timeout: Connection timeout in seconds
        """
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(pool_size + max_overflow)
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire connection from pool."""
        async with self._semaphore:
            # Connection acquired
            yield
            # Connection released


# Batch processing utilities
class BatchProcessor:
    """Process items in optimized batches."""
    
    def __init__(self, batch_size: int = 100, max_wait: float = 1.0):
        """Initialize batch processor.
        
        Args:
            batch_size: Maximum batch size
            max_wait: Maximum wait time in seconds
        """
        self.batch_size = batch_size
        self.max_wait = max_wait
        self._queue = asyncio.Queue()
        self._processing = False
    
    async def add(self, item: Any):
        """Add item to batch queue."""
        await self._queue.put(item)
        
        if not self._processing:
            asyncio.create_task(self._process_batches())
    
    async def _process_batches(self):
        """Process items in batches."""
        self._processing = True
        batch = []
        last_process = time.time()
        
        try:
            while True:
                try:
                    # Wait for item with timeout
                    timeout = self.max_wait - (time.time() - last_process)
                    if timeout <= 0:
                        timeout = 0.1
                    
                    item = await asyncio.wait_for(
                        self._queue.get(), 
                        timeout=timeout
                    )
                    batch.append(item)
                    
                    # Process if batch is full
                    if len(batch) >= self.batch_size:
                        await self._process_batch(batch)
                        batch = []
                        last_process = time.time()
                    
                except asyncio.TimeoutError:
                    # Process partial batch on timeout
                    if batch:
                        await self._process_batch(batch)
                        batch = []
                        last_process = time.time()
                    
                    # Exit if queue is empty
                    if self._queue.empty():
                        break
                        
        finally:
            self._processing = False
    
    async def _process_batch(self, batch: list):
        """Process a batch of items. Override in subclass."""
        logger.info(f"Processing batch of {len(batch)} items")


# Query optimization
def optimize_query(query: str) -> str:
    """Optimize SQL query for better performance."""
    # Simple optimizations
    optimized = query.strip()
    
    # Add LIMIT if not present for SELECT
    if optimized.upper().startswith("SELECT") and "LIMIT" not in optimized.upper():
        logger.warning("Query missing LIMIT clause, adding LIMIT 1000")
        optimized += " LIMIT 1000"
    
    return optimized


# Lazy loading decorator
def lazy_property(func):
    """Decorator for lazy-loaded properties."""
    attr_name = f"_lazy_{func.__name__}"
    
    @property
    @functools.wraps(func)
    def wrapper(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)
    
    return wrapper