"""
Usage API Routes
Endpoints for retrieving usage statistics and billing information

RBAC Protected: Phase 5.1c Week 7
All endpoints require appropriate settings.* or analytics.* permissions
"""

from fastapi import APIRouter, HTTPException, Header, Depends, Request
from typing import Optional
from datetime import datetime, timezone
import logging
from services.usage_tracking import get_usage_tracker, SUBSCRIPTION_TIERS
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db
# RBAC decorator
from services.authorization_decorator import require_permission

router = APIRouter()
logger = logging.getLogger(__name__)

# Global database reference
db = None

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    global db
    db = database


@router.get('/usage')
@require_permission("settings.view")
async def get_usage_stats(request: Request, user_id: str = Header(..., alias="X-User-ID")):
    """
    Get user usage statistics - connected to real billing system
    """
    try:
        if not user_id:
            # Return demo data for unauthenticated requests
            return {
                'creditsUsed': 0,
                'creditsTotal': 10000,
                'creditsPercentage': 0,
                'thisMonth': 0,
                'lastMonth': 0,
                'apiCalls': 0,
                'analysisCount': 0,
                'tier': 'free'
            }
        
        try:
            usage_tracker = get_usage_tracker()
            summary = await usage_tracker.get_usage_summary(user_id)
            
            # Format for frontend compatibility
            usage = summary.get("usage", {})
            subscription = summary.get("subscription", {})
            
            return {
                'creditsUsed': usage.get("tokens_used", 0),
                'creditsTotal': usage.get("tokens_limit", 10000),
                'creditsPercentage': usage.get("tokens_percentage", 0),
                'thisMonth': usage.get("tokens_used", 0),
                'lastMonth': 0,  # Would need historical query
                'apiCalls': usage.get("analyses_count", 0) + usage.get("generations_count", 0),
                'analysisCount': usage.get("analyses_count", 0),
                'generationsCount': usage.get("generations_count", 0),
                'rewritesCount': usage.get("rewrites_count", 0),
                'tier': subscription.get("tier", "free"),
                'tierName': subscription.get("tier_name", "Free"),
                'limits': summary.get("limits", {}),
                'overage': summary.get("overage", {}),
                'period': summary.get("current_period", {})
            }
        except RuntimeError:
            # Usage tracker not initialized - return basic data
            return {
                'creditsUsed': 0,
                'creditsTotal': 10000,
                'creditsPercentage': 0,
                'thisMonth': 0,
                'lastMonth': 0,
                'apiCalls': 0,
                'analysisCount': 0,
                'tier': 'free',
                'message': 'Usage tracking initializing'
            }
    except Exception as e:
        logger.error(f'Error fetching usage stats: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/usage/summary')
@require_permission("settings.view")
async def get_usage_summary(request: Request, user_id: str = Header(..., alias="X-User-ID")):
    """Get comprehensive usage summary for the current billing period"""
    
    try:
        usage_tracker = get_usage_tracker()
        summary = await usage_tracker.get_usage_summary(user_id)
        return summary
    except RuntimeError as e:
        logger.error(f"Usage tracker error: {str(e)}")
        raise HTTPException(500, "Usage tracking not available")
    except Exception as e:
        logger.error(f"Error getting usage summary: {str(e)}")
        raise HTTPException(500, f"Failed to get usage summary: {str(e)}")


@router.get('/usage/check/{operation}')
@require_permission("settings.view")
async def check_usage_limit(
    request: Request,
    operation: str,
    user_id: str = Header(..., alias="X-User-ID")
):
    """Check if user can perform a specific operation based on their tier limits"""
    
    valid_operations = ["content_analysis", "content_generation", "content_rewrite"]
    if operation not in valid_operations:
        raise HTTPException(400, f"Invalid operation. Must be one of: {valid_operations}")
    
    try:
        usage_tracker = get_usage_tracker()
        result = await usage_tracker.check_usage_limit(user_id, operation)
        return result
    except RuntimeError as e:
        logger.error(f"Usage tracker error: {str(e)}")
        return {"allowed": True, "reason": "Usage tracking not available", "tier": "unknown"}
    except Exception as e:
        logger.error(f"Error checking usage limit: {str(e)}")
        raise HTTPException(500, f"Failed to check usage limit: {str(e)}")


@router.get('/usage/history')
@require_permission("settings.view")
async def get_usage_history(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    limit: int = 50
):
    """Get detailed usage history for the user"""
    
    try:
        usage_tracker = get_usage_tracker()
        
        # Get usage history from database
        history = await usage_tracker.db.usage_history.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        # Remove MongoDB _id
        for item in history:
            item.pop("_id", None)
        
        return {
            "user_id": user_id,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Error getting usage history: {str(e)}")
        raise HTTPException(500, f"Failed to get usage history: {str(e)}")


@router.get('/usage/tiers')
@require_permission("settings.view")
async def get_subscription_tiers(request: Request):
    """Get available subscription tiers and their limits"""
    return {
        "tiers": SUBSCRIPTION_TIERS,
        "features_description": {
            "basic_analysis": "Standard content analysis",
            "advanced_analysis": "Detailed cultural and compliance analysis",
            "basic_generation": "AI content generation",
            "advanced_generation": "Platform-optimized content generation",
            "rewrite": "Content rewriting and improvement",
            "export": "Export analysis reports",
            "scheduling": "Schedule content posts",
            "multi_language": "Multi-language support",
            "all": "All features included"
        }
    }

