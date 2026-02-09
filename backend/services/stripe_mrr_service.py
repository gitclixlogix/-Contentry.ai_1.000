"""
Stripe MRR Service
Handles Monthly Recurring Revenue calculation from Stripe subscriptions with caching.
"""
import os
import logging
import stripe
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Cache for MRR data
_mrr_cache: Dict[str, Any] = {
    "value": None,
    "last_updated": None,
    "error": None
}

# Cache duration: 2 hours
CACHE_DURATION_HOURS = 2


def _get_stripe_client():
    """Initialize and return Stripe client."""
    api_key = os.environ.get("STRIPE_API_KEY")
    if not api_key:
        raise ValueError("STRIPE_API_KEY not configured")
    stripe.api_key = api_key
    return stripe


def _is_cache_valid() -> bool:
    """Check if cached MRR data is still valid."""
    if _mrr_cache["last_updated"] is None:
        return False
    
    cache_age = datetime.now(timezone.utc) - _mrr_cache["last_updated"]
    return cache_age < timedelta(hours=CACHE_DURATION_HOURS)


async def calculate_mrr() -> Dict[str, Any]:
    """
    Calculate Monthly Recurring Revenue from Stripe subscriptions.
    
    Returns:
        Dict with MRR value, subscription count, status, and metadata.
    """
    global _mrr_cache
    
    # Check cache first
    if _is_cache_valid() and _mrr_cache["value"] is not None:
        logger.info(f"Returning cached MRR: ${_mrr_cache['value']}")
        return {
            "mrr": _mrr_cache["value"],
            "status": "success",
            "cached": True,
            "cache_age_minutes": int((datetime.now(timezone.utc) - _mrr_cache["last_updated"]).total_seconds() / 60),
            "subscription_count": _mrr_cache.get("subscription_count", 0),
            "last_updated": _mrr_cache["last_updated"].isoformat()
        }
    
    try:
        _get_stripe_client()
        
        # Fetch all active subscriptions
        total_mrr = 0
        subscription_count = 0
        subscriptions_by_plan = {}
        
        # Stripe pagination - get all active subscriptions
        starting_after = None
        has_more = True
        
        while has_more:
            params = {
                "status": "active",
                "limit": 100
            }
            if starting_after:
                params["starting_after"] = starting_after
            
            subscriptions = stripe.Subscription.list(**params)
            
            for sub in subscriptions.data:
                subscription_count += 1
                
                # Calculate monthly value for this subscription
                for item in sub["items"]["data"]:
                    price = item.get("price", {})
                    unit_amount = price.get("unit_amount", 0)  # Amount in cents
                    interval = price.get("recurring", {}).get("interval", "month")
                    interval_count = price.get("recurring", {}).get("interval_count", 1)
                    quantity = item.get("quantity", 1)
                    
                    # Convert to monthly value
                    if interval == "year":
                        monthly_value = (unit_amount * quantity) / (12 * interval_count)
                    elif interval == "month":
                        monthly_value = (unit_amount * quantity) / interval_count
                    elif interval == "week":
                        monthly_value = (unit_amount * quantity * 4.33) / interval_count
                    elif interval == "day":
                        monthly_value = (unit_amount * quantity * 30) / interval_count
                    else:
                        monthly_value = unit_amount * quantity
                    
                    total_mrr += monthly_value
                    
                    # Track by plan
                    plan_name = price.get("nickname") or price.get("product", "Unknown")
                    if plan_name not in subscriptions_by_plan:
                        subscriptions_by_plan[plan_name] = {"count": 0, "mrr": 0}
                    subscriptions_by_plan[plan_name]["count"] += 1
                    subscriptions_by_plan[plan_name]["mrr"] += monthly_value
            
            has_more = subscriptions.has_more
            if subscriptions.data:
                starting_after = subscriptions.data[-1].id
        
        # Convert from cents to dollars
        mrr_dollars = round(total_mrr / 100, 2)
        
        # Update cache
        _mrr_cache = {
            "value": mrr_dollars,
            "last_updated": datetime.now(timezone.utc),
            "error": None,
            "subscription_count": subscription_count,
            "by_plan": subscriptions_by_plan
        }
        
        logger.info(f"Calculated MRR: ${mrr_dollars} from {subscription_count} active subscriptions")
        
        return {
            "mrr": mrr_dollars,
            "status": "success",
            "cached": False,
            "subscription_count": subscription_count,
            "by_plan": {k: {"count": v["count"], "mrr": round(v["mrr"] / 100, 2)} for k, v in subscriptions_by_plan.items()},
            "last_updated": _mrr_cache["last_updated"].isoformat()
        }
        
    except stripe.error.AuthenticationError as e:
        logger.error(f"Stripe authentication error: {str(e)}")
        _mrr_cache["error"] = "Authentication failed"
        return {
            "mrr": None,
            "status": "error",
            "error": "Stripe authentication failed. Please check API key.",
            "cached": False
        }
        
    except stripe.error.APIConnectionError as e:
        logger.error(f"Stripe connection error: {str(e)}")
        # Return cached value if available during connection issues
        if _mrr_cache["value"] is not None:
            return {
                "mrr": _mrr_cache["value"],
                "status": "stale",
                "error": "Connection error - showing cached value",
                "cached": True,
                "subscription_count": _mrr_cache.get("subscription_count", 0),
                "last_updated": _mrr_cache["last_updated"].isoformat() if _mrr_cache["last_updated"] else None
            }
        return {
            "mrr": None,
            "status": "error",
            "error": "Unable to connect to Stripe API",
            "cached": False
        }
        
    except stripe.error.RateLimitError as e:
        logger.error(f"Stripe rate limit error: {str(e)}")
        # Return cached value if available
        if _mrr_cache["value"] is not None:
            return {
                "mrr": _mrr_cache["value"],
                "status": "stale",
                "error": "Rate limited - showing cached value",
                "cached": True,
                "subscription_count": _mrr_cache.get("subscription_count", 0),
                "last_updated": _mrr_cache["last_updated"].isoformat() if _mrr_cache["last_updated"] else None
            }
        return {
            "mrr": None,
            "status": "error",
            "error": "Stripe API rate limited",
            "cached": False
        }
        
    except Exception as e:
        logger.error(f"Error calculating MRR: {str(e)}")
        _mrr_cache["error"] = str(e)
        # Return cached value if available
        if _mrr_cache["value"] is not None:
            return {
                "mrr": _mrr_cache["value"],
                "status": "stale",
                "error": f"Error occurred - showing cached value: {str(e)}",
                "cached": True,
                "subscription_count": _mrr_cache.get("subscription_count", 0),
                "last_updated": _mrr_cache["last_updated"].isoformat() if _mrr_cache["last_updated"] else None
            }
        return {
            "mrr": None,
            "status": "error",
            "error": str(e),
            "cached": False
        }


def clear_mrr_cache():
    """Clear the MRR cache to force a fresh calculation."""
    global _mrr_cache
    _mrr_cache = {
        "value": None,
        "last_updated": None,
        "error": None
    }
    logger.info("MRR cache cleared")


def get_cache_status() -> Dict[str, Any]:
    """Get current cache status."""
    return {
        "has_cached_value": _mrr_cache["value"] is not None,
        "cached_value": _mrr_cache["value"],
        "last_updated": _mrr_cache["last_updated"].isoformat() if _mrr_cache["last_updated"] else None,
        "cache_valid": _is_cache_valid(),
        "cache_duration_hours": CACHE_DURATION_HOURS
    }
