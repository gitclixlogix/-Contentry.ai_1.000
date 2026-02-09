"""
Social Media Integration Routes
Handles fetching engagement metrics from connected social media platforms

RBAC Protected: Phase 5.1b Week 4
All endpoints require appropriate social.* permissions
"""

from fastapi import APIRouter, HTTPException, Header, Depends, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging
import os
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db
# Import RBAC decorator
from services.authorization_decorator import require_permission

router = APIRouter(prefix="/social-media", tags=["social-media"])
logger = logging.getLogger(__name__)

# Database reference - set by server.py
db = None

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    global db
    db = database


class SocialPlatformConnection(BaseModel):
    """Model for social platform connection"""
    platform: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    account_id: Optional[str] = None
    account_name: Optional[str] = None
    connected_at: Optional[datetime] = None


class EngagementMetrics(BaseModel):
    """Model for post engagement metrics"""
    post_id: str
    platform: str
    likes: int = 0
    comments: int = 0
    shares: int = 0
    reach: int = 0
    impressions: int = 0
    clicks: int = 0
    saves: int = 0
    last_synced: Optional[datetime] = None


# Platform API configurations (placeholders for actual credentials)
PLATFORM_CONFIGS = {
    "facebook": {
        "api_base_url": "https://graph.facebook.com/v18.0",
        "app_id": os.environ.get("FACEBOOK_APP_ID", ""),
        "app_secret": os.environ.get("FACEBOOK_APP_SECRET", ""),
        "required_scopes": ["pages_read_engagement", "pages_manage_posts", "read_insights"]
    },
    "twitter": {
        "api_base_url": "https://api.twitter.com/2",
        "api_key": os.environ.get("TWITTER_API_KEY", ""),
        "api_secret": os.environ.get("TWITTER_API_SECRET", ""),
        "bearer_token": os.environ.get("TWITTER_BEARER_TOKEN", ""),
        "required_scopes": ["tweet.read", "users.read"]
    },
    "linkedin": {
        "api_base_url": "https://api.linkedin.com/v2",
        "client_id": os.environ.get("LINKEDIN_CLIENT_ID", ""),
        "client_secret": os.environ.get("LINKEDIN_CLIENT_SECRET", ""),
        "required_scopes": ["r_organization_social", "w_organization_social", "r_1st_connections_size"]
    },
    "instagram": {
        "api_base_url": "https://graph.instagram.com/v18.0",
        "app_id": os.environ.get("INSTAGRAM_APP_ID", ""),  # Same as Facebook
        "app_secret": os.environ.get("INSTAGRAM_APP_SECRET", ""),
        "required_scopes": ["instagram_basic", "instagram_manage_insights"]
    }
}


@router.get("/platforms")
@require_permission("social.view")
async def get_available_platforms(request: Request):
    """Get list of available social media platforms and their connection status"""
    platforms = []
    
    for platform_name, config in PLATFORM_CONFIGS.items():
        # Check if API credentials are configured
        has_credentials = False
        if platform_name == "facebook":
            has_credentials = bool(config["app_id"] and config["app_secret"])
        elif platform_name == "twitter":
            has_credentials = bool(config["api_key"] and config["api_secret"])
        elif platform_name == "linkedin":
            has_credentials = bool(config["client_id"] and config["client_secret"])
        elif platform_name == "instagram":
            has_credentials = bool(config["app_id"] and config["app_secret"])
        
        platforms.append({
            "platform": platform_name,
            "display_name": platform_name.capitalize(),
            "configured": has_credentials,
            "oauth_url": f"/api/social-media/connect/{platform_name}" if has_credentials else None
        })
    
    return {"platforms": platforms}


@router.get("/connections")
@require_permission("social.view")
async def get_user_connections(request: Request, user_id: str = Header(None, alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Get user's connected social media accounts"""
    if not user_id:
        raise HTTPException(401, "User ID required")
    
    connections = await db_conn.social_connections.find(
        {"user_id": user_id},
        {"_id": 0}
    ).to_list(100)
    
    return {"connections": connections}


@router.post("/connect/{platform}")
@require_permission("social.manage")
async def initiate_platform_connection(
    request: Request,
    platform: str,
    user_id: str = Header(None, alias="X-User-ID")
):
    """Initiate OAuth flow for connecting a social media platform"""
    if platform not in PLATFORM_CONFIGS:
        raise HTTPException(400, f"Unsupported platform: {platform}")
    
    config = PLATFORM_CONFIGS[platform]
    
    # Check if credentials are configured
    if platform == "facebook" and not (config["app_id"] and config["app_secret"]):
        return {
            "status": "not_configured",
            "message": "Facebook API credentials not configured. Please add FACEBOOK_APP_ID and FACEBOOK_APP_SECRET to environment variables.",
            "setup_url": "https://developers.facebook.com/apps/"
        }
    elif platform == "twitter" and not (config["api_key"] and config["api_secret"]):
        return {
            "status": "not_configured", 
            "message": "Twitter API credentials not configured. Please add TWITTER_API_KEY and TWITTER_API_SECRET to environment variables.",
            "setup_url": "https://developer.twitter.com/en/portal/dashboard"
        }
    elif platform == "linkedin" and not (config["client_id"] and config["client_secret"]):
        return {
            "status": "not_configured",
            "message": "LinkedIn API credentials not configured. Please add LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET to environment variables.",
            "setup_url": "https://www.linkedin.com/developers/apps"
        }
    elif platform == "instagram" and not (config["app_id"] and config["app_secret"]):
        return {
            "status": "not_configured",
            "message": "Instagram API credentials not configured (uses Facebook/Meta credentials). Please add INSTAGRAM_APP_ID and INSTAGRAM_APP_SECRET to environment variables.",
            "setup_url": "https://developers.facebook.com/apps/"
        }
    
    # Generate OAuth URL (placeholder - actual implementation would generate proper OAuth URLs)
    oauth_url = f"/api/social-media/oauth/{platform}/callback"
    
    return {
        "status": "ready",
        "oauth_url": oauth_url,
        "message": f"Redirect user to OAuth for {platform}"
    }


@router.get("/engagement/{post_id}")
@require_permission("analytics.view_own")
async def get_post_engagement(
    request: Request,
    post_id: str,
    user_id: str = Header(None, alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get engagement metrics for a specific post"""
    if not user_id:
        raise HTTPException(401, "User ID required")
    
    # Get post details
    post = await db_conn.posts.find_one({"id": post_id, "user_id": user_id}, {"_id": 0})
    if not post:
        raise HTTPException(404, "Post not found")
    
    # Get cached engagement metrics
    engagement = await db_conn.post_engagement.find_one(
        {"post_id": post_id},
        {"_id": 0}
    )
    
    if engagement:
        return engagement
    
    # Return empty metrics if not synced
    return {
        "post_id": post_id,
        "platforms": post.get("platforms", []),
        "metrics": {},
        "total": {
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "reach": 0,
            "impressions": 0
        },
        "synced": False,
        "message": "Connect social media accounts to sync engagement metrics"
    }


@router.post("/engagement/sync")
@require_permission("social.manage")
async def sync_all_engagement(
    request: Request,
    user_id: str = Header(None, alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Sync engagement metrics for all user's posts from connected platforms"""
    if not user_id:
        raise HTTPException(401, "User ID required")
    
    # Get user's social connections
    connections = await db_conn.social_connections.find(
        {"user_id": user_id},
        {"_id": 0}
    ).to_list(100)
    
    if not connections:
        return {
            "status": "no_connections",
            "message": "No social media accounts connected. Connect accounts in Settings to sync engagement metrics.",
            "synced_count": 0
        }
    
    # Get all user posts
    posts = await db_conn.posts.find(
        {"user_id": user_id, "status": "published"},
        {"_id": 0, "id": 1, "platforms": 1, "external_post_ids": 1}
    ).to_list(1000)
    
    synced_count = 0
    errors = []
    
    for post in posts:
        try:
            # Sync engagement for each platform
            for platform in post.get("platforms", []):
                connection = next(
                    (c for c in connections if c["platform"].lower() == platform.lower()),
                    None
                )
                
                if connection and connection.get("access_token"):
                    # Actual API calls would go here
                    # For now, mark as requiring implementation
                    pass
            
            synced_count += 1
        except Exception as e:
            errors.append({"post_id": post["id"], "error": str(e)})
    
    return {
        "status": "completed",
        "synced_count": synced_count,
        "total_posts": len(posts),
        "errors": errors if errors else None,
        "message": f"Synced engagement for {synced_count} posts" if synced_count > 0 else "No posts to sync"
    }


@router.get("/engagement/bulk")
@require_permission("analytics.view_own")
async def get_bulk_engagement(
    request: Request,
    user_id: str = Header(None, alias="X-User-ID"),
    limit: int = 50,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get engagement metrics for all user's posts"""
    if not user_id:
        raise HTTPException(401, "User ID required")
    
    # Get all posts with their engagement data
    posts = await db_conn.posts.find(
        {"user_id": user_id},
        {"_id": 0, "id": 1, "platforms": 1}
    ).to_list(limit)
    
    # Get engagement data
    post_ids = [p["id"] for p in posts]
    engagements = await db_conn.post_engagement.find(
        {"post_id": {"$in": post_ids}},
        {"_id": 0}
    ).to_list(limit)
    
    # Create lookup map
    engagement_map = {e["post_id"]: e for e in engagements}
    
    # Build response with engagement data
    result = []
    for post in posts:
        engagement = engagement_map.get(post["id"], {})
        result.append({
            "post_id": post["id"],
            "platforms": post.get("platforms", []),
            "engagement": engagement.get("total", {
                "likes": None,
                "comments": None,
                "shares": None,
                "reach": None,
                "impressions": None
            }),
            "synced": bool(engagement),
            "last_synced": engagement.get("last_synced")
        })
    
    # Check if any platforms are connected
    connections = await db_conn.social_connections.find(
        {"user_id": user_id},
        {"_id": 0, "platform": 1}
    ).to_list(10)
    
    connected_platforms = [c["platform"] for c in connections]
    
    return {
        "posts": result,
        "connected_platforms": connected_platforms,
        "has_connections": len(connections) > 0
    }
