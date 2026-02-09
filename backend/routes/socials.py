"""
Social Media Integration Routes
Handles OAuth flows and posting for Twitter/X, LinkedIn, Facebook, Instagram

Security Update (ARCH-005 Phase 5.1b):
- Added @require_permission decorators for RBAC enforcement
"""
from fastapi import APIRouter, HTTPException, Header, Query, Depends, Request
from fastapi.responses import RedirectResponse
from typing import Optional
import logging
import os
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db

# ARCH-005: Authorization decorator
from services.authorization_decorator import require_permission

router = APIRouter(prefix="/social", tags=["social"])
logger = logging.getLogger(__name__)

# Database instance (will be set by main app)
db = None

# Frontend URL for redirects
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    """Set the database instance for this router"""
    global db
    db = database


# ==================== CONNECTION STATUS ====================

@router.get("-connections")
@require_permission("social.view")
async def get_social_connections(request: Request, user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get user's social media connection status.
    
    Security (ARCH-005): Requires social.view permission.
    """
    user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(404, "User not found")
    
    connections = user.get("social_connections", {
        "Facebook": False,
        "Instagram": False,
        "LinkedIn": False,
        "YouTube": False,
        "Twitter": False
    })
    
    # Get configuration status
    from services.social_media_service import social_media_service
    config_status = social_media_service.get_configuration_status()
    
    return {
        "connections": connections,
        "api_status": config_status
    }


@router.get("/config-status")
@require_permission("social.view")
async def get_api_configuration_status(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get social media API configuration status.
    
    Security (ARCH-005): Requires social.view permission.
    """
    from services.social_media_service import social_media_service
    return social_media_service.get_configuration_status()


# ==================== TWITTER/X OAUTH ====================

@router.get("/twitter/auth")
@require_permission("social.manage")
async def twitter_auth_url(request: Request, user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get Twitter OAuth authorization URL.
    
    Security (ARCH-005): Requires social.manage permission.
    """
    from services.social_media_service import social_media_service
    
    result = social_media_service.get_twitter_auth_url(user_id)
    
    if result.get("is_mocked"):
        return {
            "auth_url": None,
            "is_mocked": True,
            "message": "Twitter API credentials not configured. Add TWITTER_CLIENT_ID and TWITTER_CLIENT_SECRET to .env"
        }
    
    return result


@router.get("/twitter/callback")
@require_permission("social.manage")
async def twitter_callback(request: Request, code: str, state: str, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Handle Twitter OAuth callback.
    
    Security (ARCH-005): Requires social.manage permission.
    """
    from services.social_media_service import social_media_service
    
    result = await social_media_service.handle_twitter_callback(code, state)
    
    if result.get("success"):
        return RedirectResponse(
            f"{FRONTEND_URL}/contentry/settings?twitter_connected=true"
        )
    else:
        error_msg = result.get("error", "Authentication failed")
        return RedirectResponse(
            f"{FRONTEND_URL}/contentry/settings?twitter_error={error_msg}"
        )


@router.post("/twitter/disconnect")
@require_permission("social.manage")
async def disconnect_twitter(request: Request, user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Disconnect Twitter account.
    
    Security (ARCH-005): Requires social.manage permission.
    """
    from services.social_media_service import social_media_service
    
    success = await social_media_service.revoke_tokens(user_id, "twitter")
    
    if success:
        return {"message": "Twitter disconnected successfully"}
    else:
        raise HTTPException(500, "Failed to disconnect Twitter")


@router.post("/twitter/post")
@require_permission("social.post")
async def post_to_twitter(
    request: Request,
    data: dict,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Post content to Twitter.
    
    Security (ARCH-005): Requires social.post permission.
    """
    from services.social_media_service import social_media_service
    
    content = data.get("content")
    if not content:
        raise HTTPException(400, "Content is required")
    
    result = await social_media_service.post_to_twitter(
        user_id=user_id,
        content=content,
        media_ids=data.get("media_ids")
    )
    
    return result


# ==================== LINKEDIN OAUTH ====================

@router.get("/linkedin/auth")
@require_permission("social.manage")
async def linkedin_auth_url(request: Request, user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get LinkedIn OAuth authorization URL.
    
    Security (ARCH-005): Requires social.manage permission.
    """
    from services.social_media_service import social_media_service
    
    result = social_media_service.get_linkedin_auth_url(user_id)
    
    if result.get("is_mocked"):
        return {
            "auth_url": None,
            "is_mocked": True,
            "message": "LinkedIn API credentials not configured. Add LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET to .env"
        }
    
    return result


@router.get("/linkedin/callback")
@require_permission("social.manage")
async def linkedin_callback(request: Request, code: str, state: str, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Handle LinkedIn OAuth callback.
    
    Security (ARCH-005): Requires social.manage permission.
    """
    from services.social_media_service import social_media_service
    
    result = await social_media_service.handle_linkedin_callback(code, state)
    
    if result.get("success"):
        return RedirectResponse(
            f"{FRONTEND_URL}/contentry/settings?linkedin_connected=true"
        )
    else:
        error_msg = result.get("error", "Authentication failed")
        return RedirectResponse(
            f"{FRONTEND_URL}/contentry/settings?linkedin_error={error_msg}"
        )


@router.post("/linkedin/disconnect")
@require_permission("social.manage")
async def disconnect_linkedin(request: Request, user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Disconnect LinkedIn account.
    
    Security (ARCH-005): Requires social.manage permission.
    """
    from services.social_media_service import social_media_service
    
    success = await social_media_service.revoke_tokens(user_id, "linkedin")
    
    if success:
        return {"message": "LinkedIn disconnected successfully"}
    else:
        raise HTTPException(500, "Failed to disconnect LinkedIn")


@router.post("/linkedin/post")
@require_permission("social.post")
async def post_to_linkedin(
    request: Request,
    data: dict,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Post content to LinkedIn.
    
    Security (ARCH-005): Requires social.post permission.
    """
    from services.social_media_service import social_media_service
    
    content = data.get("content")
    if not content:
        raise HTTPException(400, "Content is required")
    
    result = await social_media_service.post_to_linkedin(
        user_id=user_id,
        content=content,
        media_url=data.get("media_url")
    )
    
    return result


# ==================== LEGACY ENDPOINTS (BACKWARD COMPATIBILITY) ====================

@router.post("-connections/connect")
@require_permission("social.manage")
async def connect_social_media(request: Request, data: dict, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Connect a social media account (mock/placeholder for OAuth flow).
    This endpoint provides backward compatibility.
    
    Security (ARCH-005): Requires social.manage permission.
    """
    user_id = data.get("user_id")
    platform = data.get("platform")
    
    if not user_id or not platform:
        raise HTTPException(400, "Missing user_id or platform")
    
    # For real OAuth flow, redirect to respective auth endpoints
    platform_lower = platform.lower()
    
    if platform_lower in ["twitter", "linkedin"]:
        return {
            "message": f"Use /api/social/{platform_lower}/auth endpoint for OAuth flow",
            "auth_endpoint": f"/api/social/{platform_lower}/auth"
        }
    
    # For platforms not yet implemented, use mock connection
    await db_conn.users.update_one(
        {"id": user_id},
        {"$set": {f"social_connections.{platform}": True}}
    )
    
    logger.info(f"User {user_id} connected {platform} (mock)")
    
    return {
        "message": f"{platform} connected successfully",
        "is_mocked": True,
        "note": "This is a mock connection. Real API integration not yet configured."
    }


@router.post("-connections/disconnect")
@require_permission("social.manage")
async def disconnect_social_media(request: Request, data: dict, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Disconnect a social media account.
    
    Security (ARCH-005): Requires social.manage permission.
    """
    user_id = data.get("user_id")
    platform = data.get("platform")
    
    if not user_id or not platform:
        raise HTTPException(400, "Missing user_id or platform")
    
    # For Twitter/LinkedIn, use proper token revocation
    platform_lower = platform.lower()
    if platform_lower in ["twitter", "linkedin"]:
        from services.social_media_service import social_media_service
        await social_media_service.revoke_tokens(user_id, platform_lower)
    
    # Update user's social connections
    await db_conn.users.update_one(
        {"id": user_id},
        {"$set": {f"social_connections.{platform}": False}}
    )
    
    return {"message": f"{platform} disconnected successfully"}


@router.post("/connect")
@require_permission("social.manage")
async def connect_social(request: Request, data: dict, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Mock social connection endpoint (legacy).
    
    Security (ARCH-005): Requires social.manage permission.
    """
    return {"message": f"Connected to {data.get('platform')}", "connected": True, "is_mocked": True}


@router.post("/post")
@require_permission("social.post")
async def post_to_social(request: Request, data: dict, user_id: str = Header(None, alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Post to social media (routes to appropriate platform).
    
    Security (ARCH-005): Requires social.post permission.
    """
    from services.social_media_service import social_media_service
    
    platform = data.get("platform", "").lower()
    content = data.get("content", "")
    
    if not content:
        raise HTTPException(400, "Content is required")
    
    if platform == "twitter":
        if user_id:
            return await social_media_service.post_to_twitter(user_id, content)
        return {"success": True, "is_mocked": True, "message": "Mock post to Twitter"}
    
    elif platform == "linkedin":
        if user_id:
            return await social_media_service.post_to_linkedin(user_id, content)
        return {"success": True, "is_mocked": True, "message": "Mock post to LinkedIn"}
    
    # For other platforms, return mock response
    return {
        "message": f"Posted to {platform}",
        "success": True,
        "is_mocked": True,
        "note": f"{platform} API integration not yet implemented"
    }
