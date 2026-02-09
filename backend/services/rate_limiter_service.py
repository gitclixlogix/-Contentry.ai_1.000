"""
Rate Limiting Service for AI Endpoints (ARCH-013)

Provides per-user rate limiting with subscription tier support.
Uses MongoDB for persistence (Redis-free implementation).

Features:
- Per-user hourly rate limits
- Subscription tier-based limits (Free, Pro, Enterprise)
- Cost tracking with soft/hard caps
- Alert system for approaching limits
- Middleware integration for FastAPI

Usage:
    from services.rate_limiter_service import (
        check_rate_limit, 
        record_ai_request,
        get_rate_limit_status
    )
    
    # In route handler
    @router.post("/analyze")
    async def analyze(request: Request, user_id: str = Header(...)):
        # Check rate limit
        rate_check = await check_rate_limit(user_id, "content_analysis", db)
        if not rate_check["allowed"]:
            raise HTTPException(status_code=429, detail=rate_check)
        
        # Process request...
        await record_ai_request(user_id, "content_analysis", cost=0.002, db)
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from functools import wraps
from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

# Rate limit configuration by subscription tier (requests per hour)
RATE_LIMITS = {
    "free": {
        "requests_per_hour": 10,
        "daily_cost_soft_cap": 0.50,    # Warn at $0.50/day
        "daily_cost_hard_cap": 1.00,    # Block at $1/day
        "monthly_cost_cap": 5.00,        # Hard block at $5/month
        "alert_threshold": 0.8,          # Alert at 80% of limit
    },
    "creator": {
        "requests_per_hour": 30,
        "daily_cost_soft_cap": 1.50,
        "daily_cost_hard_cap": 3.00,
        "monthly_cost_cap": 30.00,
        "alert_threshold": 0.8,
    },
    "starter": {
        "requests_per_hour": 50,
        "daily_cost_soft_cap": 2.00,
        "daily_cost_hard_cap": 5.00,
        "monthly_cost_cap": 50.00,
        "alert_threshold": 0.8,
    },
    "pro": {
        "requests_per_hour": 100,
        "daily_cost_soft_cap": 10.00,
        "daily_cost_hard_cap": 25.00,
        "monthly_cost_cap": 200.00,
        "alert_threshold": 0.9,
    },
    "business": {
        "requests_per_hour": 200,
        "daily_cost_soft_cap": 20.00,
        "daily_cost_hard_cap": 50.00,
        "monthly_cost_cap": 500.00,
        "alert_threshold": 0.9,
    },
    "enterprise": {
        "requests_per_hour": -1,         # Unlimited
        "daily_cost_soft_cap": 100.00,
        "daily_cost_hard_cap": -1,       # No hard cap
        "monthly_cost_cap": -1,          # No monthly cap
        "alert_threshold": 0.9,
    }
}

# Estimated cost per operation (in USD)
OPERATION_COSTS = {
    "content_analysis": 0.002,      # ~$0.002 per analysis
    "content_generation": 0.003,    # ~$0.003 per generation
    "image_generation": 0.02,       # ~$0.02 per image
    "content_rewrite": 0.002,       # ~$0.002 per rewrite
    "media_analysis": 0.01,         # ~$0.01 per media analysis
    "cultural_analysis": 0.001,     # ~$0.001 per cultural check
    "promotional_check": 0.0005,    # ~$0.0005 per promo check
}


async def get_user_tier(user_id: str, db: AsyncIOMotorDatabase) -> str:
    """
    Get user's subscription tier from database.
    
    Args:
        user_id: User identifier
        db: MongoDB database connection
        
    Returns:
        Subscription tier string (free, creator, starter, pro, business, enterprise)
    """
    try:
        user = await db.users.find_one(
            {"id": user_id}, 
            {"_id": 0, "subscription": 1, "subscription_plan": 1, "plan_tier": 1}
        )
        if not user:
            return "free"
        
        # Check subscription object first, then plan_tier, then subscription_plan
        subscription = user.get("subscription", {})
        tier = (
            subscription.get("plan") or 
            user.get("plan_tier") or 
            user.get("subscription_plan") or 
            "free"
        )
        
        # Normalize tier name
        tier = tier.lower()
        if tier not in RATE_LIMITS:
            tier = "free"
            
        return tier
    except Exception as e:
        logger.error(f"Error getting user tier: {e}")
        return "free"


async def get_hourly_request_count(user_id: str, db: AsyncIOMotorDatabase) -> int:
    """
    Get user's request count for the current hour.
    
    Args:
        user_id: User identifier
        db: MongoDB database connection
        
    Returns:
        Number of requests made in the current hour
    """
    try:
        now = datetime.now(timezone.utc)
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        
        count = await db.rate_limit_tracking.count_documents({
            "user_id": user_id,
            "timestamp": {"$gte": hour_start.isoformat()}
        })
        
        return count
    except Exception as e:
        logger.error(f"Error getting hourly request count: {e}")
        return 0


async def get_daily_cost(user_id: str, db: AsyncIOMotorDatabase) -> float:
    """
    Get user's total AI costs for today.
    
    Args:
        user_id: User identifier
        db: MongoDB database connection
        
    Returns:
        Total cost in USD for today
    """
    try:
        now = datetime.now(timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "timestamp": {"$gte": day_start.isoformat()}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_cost": {"$sum": "$cost"}
                }
            }
        ]
        
        result = await db.rate_limit_tracking.aggregate(pipeline).to_list(1)
        return result[0]["total_cost"] if result else 0.0
    except Exception as e:
        logger.error(f"Error getting daily cost: {e}")
        return 0.0


async def get_monthly_cost(user_id: str, db: AsyncIOMotorDatabase) -> float:
    """
    Get user's total AI costs for the current month.
    
    Args:
        user_id: User identifier
        db: MongoDB database connection
        
    Returns:
        Total cost in USD for the current month
    """
    try:
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "timestamp": {"$gte": month_start.isoformat()}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_cost": {"$sum": "$cost"}
                }
            }
        ]
        
        result = await db.rate_limit_tracking.aggregate(pipeline).to_list(1)
        return result[0]["total_cost"] if result else 0.0
    except Exception as e:
        logger.error(f"Error getting monthly cost: {e}")
        return 0.0


async def check_rate_limit(
    user_id: str, 
    operation: str, 
    db: AsyncIOMotorDatabase
) -> Dict[str, Any]:
    """
    Check if user is within rate limits for an operation.
    
    This checks:
    1. Hourly request limit (based on tier)
    2. Daily cost soft cap (warning)
    3. Daily cost hard cap (blocking)
    4. Monthly cost cap (blocking)
    
    Args:
        user_id: User identifier
        operation: Type of AI operation (content_analysis, content_generation, etc.)
        db: MongoDB database connection
        
    Returns:
        Dict with allowed status, remaining requests, and any warnings
    """
    try:
        # Get user's tier
        tier = await get_user_tier(user_id, db)
        tier_config = RATE_LIMITS.get(tier, RATE_LIMITS["free"])
        
        # Get current usage
        hourly_count = await get_hourly_request_count(user_id, db)
        daily_cost = await get_daily_cost(user_id, db)
        monthly_cost = await get_monthly_cost(user_id, db)
        
        # Estimated cost for this operation
        estimated_cost = OPERATION_COSTS.get(operation, 0.002)
        
        # Check hourly rate limit
        hourly_limit = tier_config["requests_per_hour"]
        if hourly_limit != -1 and hourly_count >= hourly_limit:
            now = datetime.now(timezone.utc)
            next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            reset_seconds = int((next_hour - now).total_seconds())
            
            return {
                "allowed": False,
                "reason": f"Hourly rate limit exceeded ({hourly_limit} requests/hour)",
                "tier": tier,
                "hourly_limit": hourly_limit,
                "hourly_used": hourly_count,
                "reset_seconds": reset_seconds,
                "reset_at": next_hour.isoformat(),
                "upgrade_message": "Upgrade to Pro for 100 requests/hour or Enterprise for unlimited" if tier == "free" else None
            }
        
        # Check monthly cost cap (hard block)
        monthly_cap = tier_config["monthly_cost_cap"]
        if monthly_cap != -1 and monthly_cost + estimated_cost > monthly_cap:
            return {
                "allowed": False,
                "reason": f"Monthly cost limit reached (${monthly_cap:.2f})",
                "tier": tier,
                "monthly_cost": monthly_cost,
                "monthly_cap": monthly_cap,
                "upgrade_message": "Upgrade your plan to increase monthly limits"
            }
        
        # Check daily cost hard cap
        daily_hard_cap = tier_config["daily_cost_hard_cap"]
        if daily_hard_cap != -1 and daily_cost + estimated_cost > daily_hard_cap:
            return {
                "allowed": False,
                "reason": f"Daily cost limit reached (${daily_hard_cap:.2f})",
                "tier": tier,
                "daily_cost": daily_cost,
                "daily_hard_cap": daily_hard_cap,
                "upgrade_message": "Upgrade your plan for higher daily limits"
            }
        
        # Prepare response
        remaining_requests = hourly_limit - hourly_count if hourly_limit != -1 else -1
        
        response = {
            "allowed": True,
            "tier": tier,
            "hourly_limit": hourly_limit,
            "hourly_used": hourly_count,
            "remaining_requests": remaining_requests,
            "daily_cost": round(daily_cost, 4),
            "monthly_cost": round(monthly_cost, 4),
            "estimated_cost": estimated_cost,
            "warnings": []
        }
        
        # Add warnings if approaching limits
        alert_threshold = tier_config["alert_threshold"]
        
        # Warn if approaching hourly limit
        if hourly_limit != -1 and hourly_count >= hourly_limit * alert_threshold:
            response["warnings"].append({
                "type": "hourly_limit",
                "message": f"Approaching hourly limit ({hourly_count}/{hourly_limit} requests used)",
                "percentage": round((hourly_count / hourly_limit) * 100, 1)
            })
        
        # Warn if approaching daily soft cap
        daily_soft_cap = tier_config["daily_cost_soft_cap"]
        if daily_cost >= daily_soft_cap * alert_threshold:
            response["warnings"].append({
                "type": "daily_cost",
                "message": f"Approaching daily cost limit (${daily_cost:.2f}/${daily_soft_cap:.2f})",
                "percentage": round((daily_cost / daily_soft_cap) * 100, 1) if daily_soft_cap > 0 else 0
            })
        
        # Warn if approaching monthly cap
        if monthly_cap != -1 and monthly_cost >= monthly_cap * alert_threshold:
            response["warnings"].append({
                "type": "monthly_cost",
                "message": f"Approaching monthly cost limit (${monthly_cost:.2f}/${monthly_cap:.2f})",
                "percentage": round((monthly_cost / monthly_cap) * 100, 1)
            })
        
        return response
        
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}")
        # On error, allow the request but log it
        return {
            "allowed": True,
            "tier": "unknown",
            "error": str(e),
            "warnings": [{"type": "system", "message": "Rate limit check failed, proceeding cautiously"}]
        }


async def record_ai_request(
    user_id: str,
    operation: str,
    db: AsyncIOMotorDatabase,
    cost: Optional[float] = None,
    tokens_used: Optional[int] = None,
    model: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Record an AI request for rate limiting and cost tracking.
    
    Args:
        user_id: User identifier
        operation: Type of AI operation
        db: MongoDB database connection
        cost: Actual cost (if known, otherwise estimated)
        tokens_used: Number of tokens used
        model: Model name used
        metadata: Additional metadata
        
    Returns:
        Record creation result
    """
    try:
        now = datetime.now(timezone.utc)
        
        # Use provided cost or estimate
        actual_cost = cost if cost is not None else OPERATION_COSTS.get(operation, 0.002)
        
        record = {
            "user_id": user_id,
            "operation": operation,
            "cost": actual_cost,
            "tokens_used": tokens_used,
            "model": model,
            "timestamp": now.isoformat(),
            "hour_key": now.strftime("%Y-%m-%d-%H"),  # For hourly aggregation
            "day_key": now.strftime("%Y-%m-%d"),      # For daily aggregation
            "month_key": now.strftime("%Y-%m"),       # For monthly aggregation
            "metadata": metadata or {}
        }
        
        await db.rate_limit_tracking.insert_one(record)
        
        logger.info(f"Recorded AI request for user {user_id}: {operation} (cost: ${actual_cost:.4f})")
        
        return {
            "recorded": True,
            "cost": actual_cost,
            "timestamp": now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error recording AI request: {e}")
        return {
            "recorded": False,
            "error": str(e)
        }


async def get_rate_limit_status(
    user_id: str,
    db: AsyncIOMotorDatabase
) -> Dict[str, Any]:
    """
    Get comprehensive rate limit status for a user.
    
    Args:
        user_id: User identifier
        db: MongoDB database connection
        
    Returns:
        Complete rate limit status including usage and limits
    """
    try:
        tier = await get_user_tier(user_id, db)
        tier_config = RATE_LIMITS.get(tier, RATE_LIMITS["free"])
        
        hourly_count = await get_hourly_request_count(user_id, db)
        daily_cost = await get_daily_cost(user_id, db)
        monthly_cost = await get_monthly_cost(user_id, db)
        
        now = datetime.now(timezone.utc)
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        hour_reset = int((next_hour - now).total_seconds())
        
        hourly_limit = tier_config["requests_per_hour"]
        
        return {
            "tier": tier,
            "tier_name": tier.capitalize(),
            "hourly": {
                "limit": hourly_limit,
                "used": hourly_count,
                "remaining": hourly_limit - hourly_count if hourly_limit != -1 else -1,
                "reset_seconds": hour_reset,
                "reset_at": next_hour.isoformat(),
                "percentage_used": round((hourly_count / hourly_limit) * 100, 1) if hourly_limit > 0 else 0
            },
            "daily": {
                "cost": round(daily_cost, 4),
                "soft_cap": tier_config["daily_cost_soft_cap"],
                "hard_cap": tier_config["daily_cost_hard_cap"],
                "percentage_of_soft_cap": round((daily_cost / tier_config["daily_cost_soft_cap"]) * 100, 1) if tier_config["daily_cost_soft_cap"] > 0 else 0
            },
            "monthly": {
                "cost": round(monthly_cost, 4),
                "cap": tier_config["monthly_cost_cap"],
                "percentage_of_cap": round((monthly_cost / tier_config["monthly_cost_cap"]) * 100, 1) if tier_config["monthly_cost_cap"] > 0 else 0
            },
            "limits": tier_config
        }
        
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        return {
            "error": str(e),
            "tier": "unknown"
        }


async def send_rate_limit_alert(
    user_id: str,
    alert_type: str,
    details: Dict[str, Any],
    db: AsyncIOMotorDatabase
):
    """
    Send an alert when user is approaching limits.
    
    Args:
        user_id: User identifier
        alert_type: Type of alert (hourly_limit, daily_cost, monthly_cost)
        details: Alert details
        db: MongoDB database connection
    """
    try:
        now = datetime.now(timezone.utc)
        
        # Create in-app notification
        notification = {
            "id": str(__import__("uuid").uuid4()),
            "user_id": user_id,
            "type": "rate_limit_warning",
            "title": "Usage Limit Warning",
            "message": details.get("message", "You are approaching your usage limits"),
            "alert_type": alert_type,
            "details": details,
            "read": False,
            "created_at": now.isoformat()
        }
        
        await db.in_app_notifications.insert_one(notification)
        
        logger.info(f"Sent rate limit alert to user {user_id}: {alert_type}")
        
    except Exception as e:
        logger.error(f"Error sending rate limit alert: {e}")


async def cleanup_old_rate_limit_records(db: AsyncIOMotorDatabase, days_to_keep: int = 30):
    """
    Clean up old rate limit tracking records.
    
    Args:
        db: MongoDB database connection
        days_to_keep: Number of days of records to keep
    """
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days_to_keep)).isoformat()
        
        result = await db.rate_limit_tracking.delete_many({
            "timestamp": {"$lt": cutoff}
        })
        
        logger.info(f"Cleaned up {result.deleted_count} old rate limit records")
        
    except Exception as e:
        logger.error(f"Error cleaning up rate limit records: {e}")


# ============================================================
# Rate Limit Middleware Helper
# ============================================================

def rate_limit_dependency(operation: str):
    """
    Create a FastAPI dependency for rate limiting a specific operation.
    
    Usage:
        @router.post("/analyze")
        async def analyze(
            rate_limit: Dict = Depends(rate_limit_dependency("content_analysis")),
            ...
        ):
            # rate_limit check already done, proceed with operation
    """
    async def check_limit(request: Request, x_user_id: Optional[str] = None):
        from services.database import get_db_instance
        
        # Get user ID from header or use default
        user_id = x_user_id or request.headers.get("X-User-ID") or "anonymous"
        
        # Get database
        db = get_db_instance()
        if db is None:
            # Database not available, allow request
            return {"allowed": True, "error": "Database unavailable"}
        
        # Check rate limit
        result = await check_rate_limit(user_id, operation, db)
        
        if not result["allowed"]:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "reason": result.get("reason"),
                    "tier": result.get("tier"),
                    "reset_seconds": result.get("reset_seconds"),
                    "reset_at": result.get("reset_at"),
                    "upgrade_message": result.get("upgrade_message")
                },
                headers={
                    "X-RateLimit-Limit": str(result.get("hourly_limit", -1)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(result.get("reset_seconds", 3600)),
                    "Retry-After": str(result.get("reset_seconds", 3600))
                }
            )
        
        # Add rate limit headers to response
        # (This would need to be handled in response middleware)
        
        return result
    
    return check_limit


# ============================================================
# Ensure Indexes for Performance
# ============================================================

async def ensure_rate_limit_indexes(db: AsyncIOMotorDatabase):
    """
    Create indexes for efficient rate limit queries.
    """
    try:
        # Index for hourly queries
        await db.rate_limit_tracking.create_index([
            ("user_id", 1),
            ("timestamp", -1)
        ])
        
        # Index for aggregations
        await db.rate_limit_tracking.create_index([
            ("user_id", 1),
            ("hour_key", 1)
        ])
        
        await db.rate_limit_tracking.create_index([
            ("user_id", 1),
            ("day_key", 1)
        ])
        
        await db.rate_limit_tracking.create_index([
            ("user_id", 1),
            ("month_key", 1)
        ])
        
        # TTL index to auto-delete old records (keep 90 days)
        await db.rate_limit_tracking.create_index(
            "timestamp",
            expireAfterSeconds=90 * 24 * 60 * 60  # 90 days
        )
        
        logger.info("Rate limit indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating rate limit indexes: {e}")
