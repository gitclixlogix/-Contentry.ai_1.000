"""
Redis Caching Service for Scalability
Provides distributed caching for API responses, sessions, and rate limiting

Install: pip install redis aioredis
"""

import os
import json
import logging
import hashlib
from typing import Optional, Any, Union
from datetime import timedelta
from functools import wraps

logger = logging.getLogger(__name__)

# Redis connection (lazy initialization)
_redis_client = None


def get_redis_client():
    """Get or create Redis client (singleton pattern)"""
    global _redis_client
    
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        try:
            import redis
            _redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            _redis_client.ping()
            logger.info(f"Connected to Redis at {redis_url}")
        except ImportError:
            logger.warning("Redis package not installed. Caching disabled.")
            return None
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
            return None
    
    return _redis_client


async def get_async_redis_client():
    """Get async Redis client for FastAPI"""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    try:
        import aioredis
        return await aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    except ImportError:
        logger.warning("aioredis package not installed")
        return None
    except Exception as e:
        logger.warning(f"Failed to connect to async Redis: {e}")
        return None


class CacheService:
    """
    Caching service with TTL support and namespace isolation.
    
    Usage:
        cache = CacheService(namespace="api")
        
        # Set with 5 minute TTL
        await cache.set("user:123", user_data, ttl=300)
        
        # Get
        data = await cache.get("user:123")
        
        # Delete
        await cache.delete("user:123")
    """
    
    def __init__(self, namespace: str = "default"):
        self.namespace = namespace
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            self._client = get_redis_client()
        return self._client
    
    def _make_key(self, key: str) -> str:
        """Create namespaced cache key"""
        return f"contentry:{self.namespace}:{key}"
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = 300
    ) -> bool:
        """
        Set a cached value.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default 5 minutes)
        """
        if not self.client:
            return False
        
        try:
            full_key = self._make_key(key)
            serialized = json.dumps(value, default=str)
            
            if ttl:
                self.client.setex(full_key, ttl, serialized)
            else:
                self.client.set(full_key, serialized)
            
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get a cached value."""
        if not self.client:
            return None
        
        try:
            full_key = self._make_key(key)
            value = self.client.get(full_key)
            
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a cached value."""
        if not self.client:
            return False
        
        try:
            full_key = self._make_key(key)
            self.client.delete(full_key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        if not self.client:
            return 0
        
        try:
            full_pattern = self._make_key(pattern)
            keys = self.client.keys(full_pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error: {e}")
            return 0
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter."""
        if not self.client:
            return None
        
        try:
            full_key = self._make_key(key)
            return self.client.incr(full_key, amount)
        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return None
    
    def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a key."""
        if not self.client:
            return None
        
        try:
            full_key = self._make_key(key)
            return self.client.ttl(full_key)
        except Exception as e:
            logger.error(f"Cache TTL error: {e}")
            return None


# =============================================================================
# RATE LIMITING SERVICE (Redis-backed, distributed)
# =============================================================================

class RateLimiter:
    """
    Distributed rate limiter using Redis sliding window.
    
    Usage:
        limiter = RateLimiter()
        
        # Check if request is allowed
        allowed, remaining, reset_in = limiter.check("user:123", limit=100, window=60)
        
        if not allowed:
            raise HTTPException(429, f"Rate limit exceeded. Retry in {reset_in}s")
    """
    
    def __init__(self, namespace: str = "ratelimit"):
        self.cache = CacheService(namespace=namespace)
    
    def check(
        self, 
        identifier: str, 
        limit: int = 100, 
        window: int = 60
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit.
        
        Args:
            identifier: Unique identifier (e.g., user_id, IP address)
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            (allowed, remaining_requests, seconds_until_reset)
        """
        if not self.cache.client:
            # If Redis unavailable, allow all requests (fail open)
            return True, limit, 0
        
        try:
            import time
            
            key = f"{identifier}:{int(time.time() // window)}"
            current = self.cache.increment(key)
            
            if current == 1:
                # First request in this window, set TTL
                self.cache.client.expire(self.cache._make_key(key), window)
            
            remaining = max(0, limit - current)
            reset_in = window - (int(time.time()) % window)
            
            return current <= limit, remaining, reset_in
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True, limit, 0  # Fail open


# =============================================================================
# CACHING DECORATOR FOR API ENDPOINTS
# =============================================================================

def cached(
    ttl: int = 300,
    key_prefix: str = "",
    vary_on: list = None
):
    """
    Decorator to cache API endpoint responses.
    
    Usage:
        @router.get("/users/{user_id}")
        @cached(ttl=60, key_prefix="user", vary_on=["user_id"])
        async def get_user(user_id: str):
            return await db.users.find_one({"_id": user_id})
    
    Args:
        ttl: Cache TTL in seconds
        key_prefix: Prefix for cache key
        vary_on: List of parameter names to include in cache key
    """
    cache = CacheService(namespace="api_cache")
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            key_parts = [key_prefix or func.__name__]
            
            if vary_on:
                for param in vary_on:
                    if param in kwargs:
                        key_parts.append(f"{param}:{kwargs[param]}")
            
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache the result
            cache.set(cache_key, result, ttl=ttl)
            logger.debug(f"Cache set: {cache_key}")
            
            return result
        
        return wrapper
    return decorator


# =============================================================================
# CACHE INVALIDATION HELPERS
# =============================================================================

def invalidate_user_cache(user_id: str):
    """Invalidate all cache entries for a user."""
    cache = CacheService(namespace="api_cache")
    cache.delete_pattern(f"*user_id:{user_id}*")
    cache.delete_pattern(f"user:{user_id}*")


def invalidate_enterprise_cache(enterprise_id: str):
    """Invalidate all cache entries for an enterprise."""
    cache = CacheService(namespace="api_cache")
    cache.delete_pattern(f"*enterprise_id:{enterprise_id}*")
    cache.delete_pattern(f"enterprise:{enterprise_id}*")


# =============================================================================
# SESSION MANAGEMENT (Redis-backed)
# =============================================================================

class SessionStore:
    """
    Distributed session store for user sessions.
    Useful when JWT token needs to be invalidated (logout, password change).
    """
    
    def __init__(self):
        self.cache = CacheService(namespace="sessions")
        self.default_ttl = 86400 * 7  # 7 days
    
    def create_session(self, user_id: str, session_data: dict) -> str:
        """Create a new session."""
        import uuid
        session_id = str(uuid.uuid4())
        
        self.cache.set(
            f"session:{session_id}",
            {"user_id": user_id, **session_data},
            ttl=self.default_ttl
        )
        
        # Track user's active sessions
        user_sessions = self.cache.get(f"user_sessions:{user_id}") or []
        user_sessions.append(session_id)
        self.cache.set(f"user_sessions:{user_id}", user_sessions, ttl=self.default_ttl)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data."""
        return self.cache.get(f"session:{session_id}")
    
    def invalidate_session(self, session_id: str):
        """Invalidate a specific session."""
        self.cache.delete(f"session:{session_id}")
    
    def invalidate_user_sessions(self, user_id: str):
        """Invalidate all sessions for a user (e.g., on password change)."""
        user_sessions = self.cache.get(f"user_sessions:{user_id}") or []
        
        for session_id in user_sessions:
            self.cache.delete(f"session:{session_id}")
        
        self.cache.delete(f"user_sessions:{user_id}")


# =============================================================================
# INITIALIZATION
# =============================================================================

# Pre-instantiated services for easy import
api_cache = CacheService(namespace="api")
rate_limiter = RateLimiter()
session_store = SessionStore()


def check_redis_health() -> dict:
    """Check Redis connection health."""
    client = get_redis_client()
    
    if not client:
        return {"status": "unavailable", "message": "Redis not configured"}
    
    try:
        info = client.info()
        return {
            "status": "healthy",
            "version": info.get("redis_version"),
            "connected_clients": info.get("connected_clients"),
            "used_memory_human": info.get("used_memory_human"),
            "uptime_in_seconds": info.get("uptime_in_seconds"),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
