"""
API Response Caching Middleware
Provides automatic caching for frequently accessed endpoints

Usage:
    from middleware.api_cache import cached_response, invalidate_cache
    
    @router.get("/expensive-endpoint")
    @cached_response(ttl=300, key_prefix="expensive")
    async def get_expensive_data():
        ...
"""

import os
import json
import logging
import hashlib
from functools import wraps
from typing import Optional, Any, Callable
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Redis client (lazy init)
_redis = None


def _get_redis():
    """Get Redis client with lazy initialization"""
    global _redis
    if _redis is not None:
        return _redis
    
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.debug("REDIS_URL not set, caching disabled")
        return None
    
    try:
        import redis
        _redis = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=2,
            socket_connect_timeout=2,
        )
        _redis.ping()
        logger.info(f"Redis cache connected: {redis_url}")
        return _redis
    except ImportError:
        logger.warning("redis package not installed")
        return None
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        _redis = False  # Mark as failed
        return None


def _make_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a cache key from prefix and arguments"""
    key_parts = [prefix]
    
    # Add relevant kwargs to key
    for k, v in sorted(kwargs.items()):
        if v is not None and k not in ['request', 'db_conn', 'db']:
            key_parts.append(f"{k}:{v}")
    
    key_str = ":".join(str(p) for p in key_parts)
    
    # Hash if too long
    if len(key_str) > 200:
        key_str = f"{prefix}:{hashlib.md5(key_str.encode()).hexdigest()}"
    
    return f"api_cache:{key_str}"


def cached_response(
    ttl: int = 300,
    key_prefix: str = "",
    vary_on: list = None,
    skip_user_specific: bool = False
):
    """
    Decorator to cache API endpoint responses in Redis.
    
    Args:
        ttl: Cache time-to-live in seconds (default 5 minutes)
        key_prefix: Prefix for cache key
        vary_on: List of parameter names to include in cache key
        skip_user_specific: If True, cache is shared across all users
    
    Example:
        @router.get("/plans")
        @cached_response(ttl=3600, key_prefix="plans")
        async def get_plans():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            redis_client = _get_redis()
            
            # If no Redis, just execute function
            if not redis_client:
                return await func(*args, **kwargs)
            
            # Build cache key
            key_parts = [key_prefix or func.__name__]
            
            # Add user ID if not skipped
            if not skip_user_specific:
                user_id = kwargs.get('x_user_id') or kwargs.get('user_id')
                if user_id:
                    key_parts.append(f"user:{user_id}")
            
            # Add specified parameters
            if vary_on:
                for param in vary_on:
                    if param in kwargs and kwargs[param] is not None:
                        key_parts.append(f"{param}:{kwargs[param]}")
            
            cache_key = _make_cache_key(*key_parts)
            
            # Try cache first
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.debug(f"Cache HIT: {cache_key}")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            try:
                redis_client.setex(cache_key, ttl, json.dumps(result, default=str))
                logger.debug(f"Cache SET: {cache_key} (TTL: {ttl}s)")
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """
    Invalidate cache entries matching a pattern.
    
    Args:
        pattern: Redis key pattern (e.g., "api_cache:plans:*")
    """
    redis_client = _get_redis()
    if not redis_client:
        return 0
    
    try:
        keys = redis_client.keys(f"api_cache:{pattern}")
        if keys:
            deleted = redis_client.delete(*keys)
            logger.info(f"Invalidated {deleted} cache entries matching: {pattern}")
            return deleted
        return 0
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")
        return 0


def invalidate_user_cache(user_id: str):
    """Invalidate all cache entries for a specific user"""
    return invalidate_cache(f"*user:{user_id}*")


def get_cache_stats() -> dict:
    """Get Redis cache statistics"""
    redis_client = _get_redis()
    if not redis_client:
        return {"status": "disabled", "message": "Redis not available"}
    
    try:
        info = redis_client.info()
        keys = redis_client.keys("api_cache:*")
        
        return {
            "status": "connected",
            "version": info.get("redis_version"),
            "used_memory_human": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "cache_keys": len(keys),
            "uptime_seconds": info.get("uptime_in_seconds"),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Pre-warm common caches on startup
async def warm_cache(db):
    """Pre-populate cache with frequently accessed data"""
    redis_client = _get_redis()
    if not redis_client:
        return
    
    try:
        from services.credit_service import CREDIT_COSTS, CREDIT_PACKS, PLAN_CONFIGS
        
        # Cache credit costs (rarely changes)
        costs_data = {
            "success": True,
            "data": {
                "costs": {k.value: v for k, v in CREDIT_COSTS.items()},
            }
        }
        redis_client.setex("api_cache:credit_costs", 86400, json.dumps(costs_data))
        
        # Cache plans (rarely changes)
        plans_data = {
            "success": True,
            "data": {
                "plans": [
                    {
                        "id": tier.value,
                        "name": config["name"],
                        "monthly_credits": config["monthly_credits"],
                    }
                    for tier, config in PLAN_CONFIGS.items()
                ]
            }
        }
        redis_client.setex("api_cache:plans", 86400, json.dumps(plans_data))
        
        logger.info("Cache warmed with static data")
    except Exception as e:
        logger.error(f"Cache warming failed: {e}")
