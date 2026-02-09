"""
Usage Tracking and Billing Service
Handles token usage tracking, tier limits, and billing for LLM API calls
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Subscription tier definitions with monthly limits
SUBSCRIPTION_TIERS = {
    "free": {
        "name": "Free",
        "monthly_token_limit": 500_000,           # 500K tokens/month (increased for development)
        "monthly_analysis_limit": 100,            # 100 analyses/month
        "monthly_generation_limit": 50,           # 50 content generations/month
        "features": ["basic_analysis", "basic_generation"],
        "price_monthly": 0,
        "overage_rate_per_1k_tokens": None,      # No overage allowed
    },
    "starter": {
        "name": "Starter",
        "monthly_token_limit": 100_000,          # 100K tokens/month
        "monthly_analysis_limit": 100,           # 100 analyses/month
        "monthly_generation_limit": 50,          # 50 generations/month
        "features": ["basic_analysis", "basic_generation", "rewrite", "export"],
        "price_monthly": 19,
        "overage_rate_per_1k_tokens": 0.01,      # $0.01 per 1K tokens overage
    },
    "pro": {
        "name": "Professional",
        "monthly_token_limit": 500_000,          # 500K tokens/month
        "monthly_analysis_limit": 500,           # 500 analyses/month
        "monthly_generation_limit": 250,         # 250 generations/month
        "features": ["basic_analysis", "advanced_analysis", "basic_generation", "advanced_generation", 
                     "rewrite", "export", "scheduling", "multi_language"],
        "price_monthly": 49,
        "overage_rate_per_1k_tokens": 0.008,     # $0.008 per 1K tokens overage
    },
    "enterprise": {
        "name": "Enterprise",
        "monthly_token_limit": 2_000_000,        # 2M tokens/month
        "monthly_analysis_limit": -1,            # Unlimited
        "monthly_generation_limit": -1,          # Unlimited
        "features": ["all"],
        "price_monthly": 199,
        "overage_rate_per_1k_tokens": 0.005,     # $0.005 per 1K tokens overage
    }
}

# Token cost estimates per operation (input + output tokens)
OPERATION_TOKEN_ESTIMATES = {
    "content_analysis": 2000,           # ~2K tokens per analysis
    "content_generation": 1500,         # ~1.5K tokens per generation
    "content_rewrite": 1200,            # ~1.2K tokens per rewrite
    "promotional_check": 500,           # ~500 tokens per check
    "cultural_analysis": 800,           # ~800 tokens for cultural analysis
}


class UsageTracker:
    """Tracks and enforces usage limits for LLM operations"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_user_subscription(self, user_id: str) -> Dict[str, Any]:
        """Get user's subscription details and tier"""
        user = await self.db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            return {"tier": "free", "status": "active"}
        
        subscription = user.get("subscription", {})
        tier = subscription.get("plan") or user.get("subscription_plan") or "free"
        status = subscription.get("status") or user.get("subscription_status") or "active"
        
        return {
            "tier": tier.lower(),
            "status": status,
            "subscription": subscription,
            "user": user
        }
    
    async def get_current_period_usage(self, user_id: str) -> Dict[str, Any]:
        """Get user's usage for the current billing period"""
        # Get or create usage record for current month
        now = datetime.now(timezone.utc)
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        usage = await self.db.usage_tracking.find_one({
            "user_id": user_id,
            "period_start": {"$gte": period_start.isoformat()}
        }, {"_id": 0})
        
        if not usage:
            # Create new usage record for this period
            usage = {
                "user_id": user_id,
                "period_start": period_start.isoformat(),
                "period_end": (period_start.replace(month=period_start.month + 1) if period_start.month < 12 
                              else period_start.replace(year=period_start.year + 1, month=1)).isoformat(),
                "tokens_used": 0,
                "analyses_count": 0,
                "generations_count": 0,
                "rewrites_count": 0,
                "operations": [],
                "overage_tokens": 0,
                "overage_cost": 0.0,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
            await self.db.usage_tracking.insert_one(usage)
            usage.pop("_id", None)
        
        return usage
    
    async def check_usage_limit(self, user_id: str, operation: str) -> Dict[str, Any]:
        """
        Check if user can perform an operation based on their tier limits.
        Returns: {"allowed": bool, "reason": str, "remaining": dict}
        """
        subscription = await self.get_user_subscription(user_id)
        tier = subscription["tier"]
        tier_config = SUBSCRIPTION_TIERS.get(tier, SUBSCRIPTION_TIERS["free"])
        
        # Check subscription status
        if subscription["status"] not in ["active", "trialing"]:
            return {
                "allowed": False,
                "reason": "Subscription is not active. Please renew your subscription.",
                "tier": tier,
                "remaining": {}
            }
        
        # Get current usage
        usage = await self.get_current_period_usage(user_id)
        
        # Check token limit
        tokens_used = usage.get("tokens_used", 0)
        token_limit = tier_config["monthly_token_limit"]
        tokens_remaining = max(0, token_limit - tokens_used)
        
        # Check operation-specific limits
        if operation == "content_analysis":
            count = usage.get("analyses_count", 0)
            limit = tier_config["monthly_analysis_limit"]
            if limit != -1 and count >= limit:
                return {
                    "allowed": False,
                    "reason": f"Monthly analysis limit reached ({limit} analyses). Upgrade your plan for more.",
                    "tier": tier,
                    "remaining": {"analyses": 0, "tokens": tokens_remaining}
                }
        
        elif operation == "content_generation":
            count = usage.get("generations_count", 0)
            limit = tier_config["monthly_generation_limit"]
            if limit != -1 and count >= limit:
                return {
                    "allowed": False,
                    "reason": f"Monthly generation limit reached ({limit} generations). Upgrade your plan for more.",
                    "tier": tier,
                    "remaining": {"generations": 0, "tokens": tokens_remaining}
                }
        
        # Check token limit (unless enterprise with overage enabled)
        estimated_tokens = OPERATION_TOKEN_ESTIMATES.get(operation, 1000)
        if tokens_used + estimated_tokens > token_limit:
            if tier_config["overage_rate_per_1k_tokens"] is None:
                return {
                    "allowed": False,
                    "reason": f"Monthly token limit reached ({token_limit:,} tokens). Upgrade your plan for more.",
                    "tier": tier,
                    "remaining": {"tokens": tokens_remaining}
                }
            # Allow overage for paid tiers
            logger.info(f"User {user_id} will incur overage charges for this operation")
        
        return {
            "allowed": True,
            "reason": "OK",
            "tier": tier,
            "tier_name": tier_config["name"],
            "remaining": {
                "tokens": tokens_remaining,
                "analyses": max(0, tier_config["monthly_analysis_limit"] - usage.get("analyses_count", 0)) if tier_config["monthly_analysis_limit"] != -1 else -1,
                "generations": max(0, tier_config["monthly_generation_limit"] - usage.get("generations_count", 0)) if tier_config["monthly_generation_limit"] != -1 else -1
            },
            "limits": {
                "monthly_tokens": token_limit,
                "monthly_analyses": tier_config["monthly_analysis_limit"],
                "monthly_generations": tier_config["monthly_generation_limit"]
            }
        }
    
    async def record_usage(
        self, 
        user_id: str, 
        operation: str, 
        tokens_used: int,
        input_tokens: int = 0,
        output_tokens: int = 0,
        model: str = "gpt-4.1-nano",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Record token usage for a completed operation"""
        now = datetime.now(timezone.utc)
        
        # Get subscription tier for overage calculation
        subscription = await self.get_user_subscription(user_id)
        tier = subscription["tier"]
        tier_config = SUBSCRIPTION_TIERS.get(tier, SUBSCRIPTION_TIERS["free"])
        
        # Get current usage
        usage = await self.get_current_period_usage(user_id)
        current_tokens = usage.get("tokens_used", 0)
        token_limit = tier_config["monthly_token_limit"]
        
        # Calculate overage if applicable
        overage_tokens = 0
        overage_cost = 0.0
        if current_tokens + tokens_used > token_limit and tier_config["overage_rate_per_1k_tokens"]:
            overage_tokens = max(0, (current_tokens + tokens_used) - token_limit)
            overage_cost = (overage_tokens / 1000) * tier_config["overage_rate_per_1k_tokens"]
        
        # Create operation record
        operation_record = {
            "operation": operation,
            "tokens_used": tokens_used,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "model": model,
            "timestamp": now.isoformat(),
            "metadata": metadata or {}
        }
        
        # Update usage tracking
        update_fields = {
            "$inc": {
                "tokens_used": tokens_used,
                "overage_tokens": overage_tokens,
            },
            "$set": {
                "updated_at": now.isoformat(),
                "overage_cost": usage.get("overage_cost", 0) + overage_cost
            },
            "$push": {
                "operations": {
                    "$each": [operation_record],
                    "$slice": -100  # Keep last 100 operations
                }
            }
        }
        
        # Increment operation-specific counters
        if operation == "content_analysis":
            update_fields["$inc"]["analyses_count"] = 1
        elif operation == "content_generation":
            update_fields["$inc"]["generations_count"] = 1
        elif operation == "content_rewrite":
            update_fields["$inc"]["rewrites_count"] = 1
        
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        await self.db.usage_tracking.update_one(
            {
                "user_id": user_id,
                "period_start": {"$gte": period_start.isoformat()}
            },
            update_fields
        )
        
        # Also log to detailed usage history for billing
        await self.db.usage_history.insert_one({
            "user_id": user_id,
            "operation": operation,
            "tokens_used": tokens_used,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "model": model,
            "tier": tier,
            "overage": overage_tokens > 0,
            "overage_tokens": overage_tokens,
            "overage_cost": overage_cost,
            "timestamp": now.isoformat(),
            "metadata": metadata
        })
        
        logger.info(f"Recorded usage for user {user_id}: {operation} - {tokens_used} tokens")
        
        return {
            "tokens_used": tokens_used,
            "overage_tokens": overage_tokens,
            "overage_cost": overage_cost,
            "total_tokens_this_period": current_tokens + tokens_used
        }
    
    async def get_usage_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive usage summary for user dashboard"""
        subscription = await self.get_user_subscription(user_id)
        tier = subscription["tier"]
        tier_config = SUBSCRIPTION_TIERS.get(tier, SUBSCRIPTION_TIERS["free"])
        
        usage = await self.get_current_period_usage(user_id)
        
        tokens_used = usage.get("tokens_used", 0)
        token_limit = tier_config["monthly_token_limit"]
        
        return {
            "subscription": {
                "tier": tier,
                "tier_name": tier_config["name"],
                "status": subscription["status"],
                "price": tier_config["price_monthly"]
            },
            "current_period": {
                "start": usage.get("period_start"),
                "end": usage.get("period_end")
            },
            "usage": {
                "tokens_used": tokens_used,
                "tokens_limit": token_limit,
                "tokens_remaining": max(0, token_limit - tokens_used),
                "tokens_percentage": round((tokens_used / token_limit) * 100, 1) if token_limit > 0 else 0,
                "analyses_count": usage.get("analyses_count", 0),
                "analyses_limit": tier_config["monthly_analysis_limit"],
                "generations_count": usage.get("generations_count", 0),
                "generations_limit": tier_config["monthly_generation_limit"],
                "rewrites_count": usage.get("rewrites_count", 0)
            },
            "overage": {
                "tokens": usage.get("overage_tokens", 0),
                "cost": usage.get("overage_cost", 0),
                "rate_per_1k": tier_config["overage_rate_per_1k_tokens"]
            },
            "limits": {
                "monthly_tokens": token_limit,
                "monthly_analyses": tier_config["monthly_analysis_limit"],
                "monthly_generations": tier_config["monthly_generation_limit"],
                "features": tier_config["features"]
            }
        }


# Global instance - will be initialized by server.py
usage_tracker: Optional[UsageTracker] = None


def init_usage_tracker(db):
    """Initialize the global usage tracker with database connection"""
    global usage_tracker
    usage_tracker = UsageTracker(db)
    return usage_tracker


def get_usage_tracker() -> UsageTracker:
    """Get the global usage tracker instance"""
    if usage_tracker is None:
        raise RuntimeError("Usage tracker not initialized. Call init_usage_tracker first.")
    return usage_tracker
