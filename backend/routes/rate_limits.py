"""
Rate Limit API Routes (ARCH-013)

Provides endpoints for:
- Getting user's rate limit status
- Getting remaining requests
- Admin rate limit management
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Request
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from services.database import get_db
from services.rate_limiter_service import (
    get_rate_limit_status,
    check_rate_limit,
    RATE_LIMITS,
    OPERATION_COSTS
)

router = APIRouter(prefix="/rate-limits", tags=["rate-limits"])


@router.get("/status")
async def get_user_rate_limit_status(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    user_id: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get current rate limit status for a user.
    
    Returns hourly requests used/remaining, daily/monthly costs, and tier info.
    """
    uid = x_user_id or user_id
    if not uid:
        raise HTTPException(status_code=400, detail="User ID required")
    
    status = await get_rate_limit_status(uid, db)
    return status


@router.get("/check/{operation}")
async def check_operation_rate_limit(
    operation: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    user_id: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Check if a specific operation is allowed for the user.
    
    Args:
        operation: Operation type (content_analysis, content_generation, image_generation, etc.)
    
    Returns:
        Whether operation is allowed and any warnings
    """
    uid = x_user_id or user_id
    if not uid:
        raise HTTPException(status_code=400, detail="User ID required")
    
    if operation not in OPERATION_COSTS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown operation. Valid operations: {list(OPERATION_COSTS.keys())}"
        )
    
    result = await check_rate_limit(uid, operation, db)
    
    # Add HTTP headers to response for rate limiting
    return result


@router.get("/tiers")
async def get_rate_limit_tiers():
    """
    Get available subscription tiers and their rate limits.
    """
    tiers = {}
    for tier_name, config in RATE_LIMITS.items():
        tiers[tier_name] = {
            "name": tier_name.capitalize(),
            "requests_per_hour": config["requests_per_hour"],
            "daily_cost_soft_cap": config["daily_cost_soft_cap"],
            "daily_cost_hard_cap": config["daily_cost_hard_cap"],
            "monthly_cost_cap": config["monthly_cost_cap"],
            "unlimited_hourly": config["requests_per_hour"] == -1,
            "unlimited_monthly": config["monthly_cost_cap"] == -1
        }
    return {"tiers": tiers}


@router.get("/operations")
async def get_operation_costs():
    """
    Get available operations and their estimated costs.
    """
    operations = {}
    for op, cost in OPERATION_COSTS.items():
        operations[op] = {
            "name": op.replace("_", " ").title(),
            "estimated_cost_usd": cost
        }
    return {"operations": operations}
