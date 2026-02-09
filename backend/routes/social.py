"""
Ayrshare Social Media Integration Routes
Supports both Free Plan (single primary profile) and Business Plan (multiple sub-user profiles)

Business Plan Features:
- Create isolated sub-user profiles via Ayrshare API
- Each profile has its own linked social accounts
- Profile-specific posting using Profile-Key header
- JWT-based social account linking for each profile

Security Update (ARCH-005 Phase 5.1b):
- Added @require_permission decorators for RBAC enforcement
"""
import os
import logging
import httpx
from fastapi import APIRouter, HTTPException, Depends, Header, Query, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db

# ARCH-005: Authorization decorator
from services.authorization_decorator import require_permission

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/social", tags=["social"])

# Get environment variables dynamically
def get_ayrshare_api_key():
    return os.getenv("AYRSHARE_API_KEY", "")

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "contentry_db")

# MongoDB client
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Ayrshare API base URL
AYRSHARE_BASE_URL = "https://api.ayrshare.com/api"

# Supported social platforms
SUPPORTED_PLATFORMS = [
    "twitter", "facebook", "instagram", "linkedin", 
    "tiktok", "pinterest", "youtube", "threads", 
    "bluesky", "reddit", "gmb"
]


# Pydantic Models
class SocialProfileCreate(BaseModel):
    title: str = Field(..., description="Name for this social profile (e.g., 'Company Brand', 'Personal Account')")
    enterprise_id: Optional[str] = Field(None, description="Enterprise ID for company profiles")
    is_enterprise: Optional[bool] = Field(False, description="Whether this is a company profile")
    
class SocialProfileResponse(BaseModel):
    id: str
    user_id: str
    profile_key: Optional[str]
    title: str
    linked_networks: List[str] = []
    is_primary: bool = False
    enterprise_id: Optional[str] = None
    is_enterprise: bool = False
    created_at: datetime

class PostCreate(BaseModel):
    content: str = Field(..., description="Post content")
    platforms: List[str] = Field(..., description="List of platforms to post to")
    media_urls: Optional[List[str]] = Field(None, description="Media URLs to include")
    schedule_date: Optional[str] = Field(None, description="ISO format date for scheduling")
    profile_id: Optional[str] = Field(None, description="Profile ID to post from")

class PostResponse(BaseModel):
    id: str
    status: str
    post_ids: List[dict] = []
    errors: List[dict] = []

class ImageUploadRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded image data")
    mime_type: str = Field(default="image/png", description="MIME type of the image")
    filename: Optional[str] = Field(None, description="Optional filename")


# Image storage directory
IMAGES_DIR = ROOT_DIR / "static" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload-image")
@require_permission("social.manage")
async def upload_image(
    request_obj: Request,
    request: ImageUploadRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Upload a base64 image and get a public URL for use with Ayrshare.
    The image is stored temporarily on the server.
    
    Security (ARCH-005): Requires social.manage permission.
    """
    import base64
    
    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image_base64)
        
        # Generate unique filename
        ext = "png"
        if "jpeg" in request.mime_type or "jpg" in request.mime_type:
            ext = "jpg"
        elif "gif" in request.mime_type:
            ext = "gif"
        elif "webp" in request.mime_type:
            ext = "webp"
        
        filename = request.filename or f"{uuid4()}.{ext}"
        if not filename.endswith(f".{ext}"):
            filename = f"{filename}.{ext}"
        
        # Save image to disk
        file_path = IMAGES_DIR / filename
        with open(file_path, "wb") as f:
            f.write(image_data)
        
        # Generate public URL
        frontend_url = os.getenv("FRONTEND_URL", "https://localhost:3000")
        # Use the frontend URL with /api prefix for serving static files
        if "preview.emergentagent.com" in frontend_url:
            # In production, use the same domain with /api prefix
            image_url = f"{frontend_url}/api/social/images/{filename}"
        else:
            image_url = f"http://localhost:8001/api/social/images/{filename}"
        
        logger.info(f"Image uploaded: {filename} for user {user_id}")
        
        return {
            "success": True,
            "url": image_url,
            "filename": filename
        }
        
    except Exception as e:
        logger.error(f"Image upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")


@router.get("/images/{filename}")
@require_permission("social.view")
async def serve_image(request: Request, filename: str, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Serve uploaded images.
    
    Security (ARCH-005): Requires social.view permission.
    """
    from fastapi.responses import FileResponse
    
    file_path = IMAGES_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Determine content type
    content_type = "image/png"
    if filename.endswith(".jpg") or filename.endswith(".jpeg"):
        content_type = "image/jpeg"
    elif filename.endswith(".gif"):
        content_type = "image/gif"
    elif filename.endswith(".webp"):
        content_type = "image/webp"
    
    return FileResponse(file_path, media_type=content_type)


# Helper function to get Ayrshare headers
def get_ayrshare_headers(profile_key: Optional[str] = None) -> dict:
    """Get headers for Ayrshare API requests.
    
    Args:
        profile_key: If provided, adds Profile-Key header for sub-user profile.
                    If None, uses primary API key only.
    """
    api_key = get_ayrshare_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    if profile_key:
        headers["Profile-Key"] = profile_key
    return headers


# Helper to get current user
async def get_current_user(x_user_id: str = Header(...)):
    """Get user ID from header"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    return x_user_id


async def fetch_profile_linked_accounts(profile_key: Optional[str] = None) -> Dict[str, Any]:
    """Fetch linked social accounts from Ayrshare for a specific profile.
    
    Args:
        profile_key: The profile key for sub-user profiles. None for primary profile.
        
    Returns:
        Dict containing linked_networks list and accounts_info dict
    """
    linked_networks = []
    accounts_info = {}
    
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{AYRSHARE_BASE_URL}/user",
                headers=get_ayrshare_headers(profile_key),
                timeout=30.0
            )
            
            if response.status_code == 200:
                user_data = response.json()
                active_accounts = user_data.get("activeSocialAccounts", [])
                linked_networks = [p for p in active_accounts if p in SUPPORTED_PLATFORMS]
                
                # Extract detailed info for each platform
                for display_info in user_data.get("displayNames", []):
                    platform = display_info.get("platform")
                    if platform:
                        accounts_info[platform] = {
                            "displayName": display_info.get("displayName"),
                            "username": display_info.get("username"),
                            "profileUrl": display_info.get("profileUrl"),
                            "userImage": display_info.get("userImage"),
                            "pageName": display_info.get("pageName"),
                            "type": display_info.get("type"),
                            "id": display_info.get("id")
                        }
            else:
                logger.warning(f"Failed to fetch Ayrshare accounts: {response.status_code} - {response.text}")
                
    except Exception as e:
        logger.error(f"Error fetching Ayrshare accounts: {e}")
    
    return {
        "linked_networks": linked_networks,
        "accounts_info": accounts_info
    }


# ==================== PLAN DETECTION ====================

@router.get("/plan-info")
@require_permission("social.view")
async def get_plan_info(request: Request, user_id: str = Depends(get_current_user), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get Ayrshare plan information to determine available features.
    
    Security (ARCH-005): Requires social.view permission.
    """
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{AYRSHARE_BASE_URL}/user",
                headers=get_ayrshare_headers(None),
                timeout=30.0
            )
            
            if response.status_code != 200:
                return {"plan": "unknown", "supports_profiles": False}
            
            data = response.json()
            
            # Try to create a test profile to detect Business Plan
            # Business Plan allows creating sub-user profiles
            test_response = await http_client.post(
                f"{AYRSHARE_BASE_URL}/profiles",
                headers=get_ayrshare_headers(None),
                json={"title": "_plan_test_delete_me"},
                timeout=30.0
            )
            
            if test_response.status_code == 200:
                # Business Plan detected - delete test profile
                test_data = test_response.json()
                if test_data.get("profileKey"):
                    await http_client.delete(
                        f"{AYRSHARE_BASE_URL}/profiles/{test_data['profileKey']}",
                        headers=get_ayrshare_headers(None),
                        timeout=30.0
                    )
                return {
                    "plan": "business",
                    "supports_profiles": True,
                    "monthly_post_quota": data.get("monthlyPostQuota"),
                    "monthly_post_count": data.get("monthlyPostCount")
                }
            else:
                return {
                    "plan": "free_or_premium",
                    "supports_profiles": False,
                    "monthly_post_quota": data.get("monthlyPostQuota"),
                    "monthly_post_count": data.get("monthlyPostCount"),
                    "note": "Upgrade to Business Plan to create multiple isolated profiles"
                }
                
    except Exception as e:
        logger.error(f"Error detecting plan: {e}")
        return {"plan": "unknown", "supports_profiles": False, "error": str(e)}


# ==================== PROFILE MANAGEMENT ====================

@router.post("/profiles", response_model=SocialProfileResponse)
@require_permission("social.manage")
async def create_social_profile(
    request: Request,
    profile: SocialProfileCreate,
    user_id: str = Depends(get_current_user),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Create a new social profile for managing social accounts.
    
    Business Plan: Creates an Ayrshare sub-user profile with isolated social accounts.
    Free/Premium Plan: Creates a local profile that shares the primary Ayrshare account.
    
    Security (ARCH-005): Requires social.manage permission.
    """
    api_key = get_ayrshare_api_key()
    if not api_key:
        raise HTTPException(status_code=500, detail="Ayrshare API not configured")
    
    try:
        # Try to create profile in Ayrshare (requires Business Plan)
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                f"{AYRSHARE_BASE_URL}/profiles",
                headers=get_ayrshare_headers(),
                json={
                    "title": profile.title
                },
                timeout=30.0
            )
        
        if response.status_code == 200:
            data = response.json()
            profile_key = data.get("profileKey")
            
            if not profile_key:
                raise HTTPException(status_code=500, detail="No profile key returned from Ayrshare")
            
            logger.info(f"Created Ayrshare sub-user profile: {profile.title} with key {profile_key[:8]}...")
            
            # Store profile in MongoDB with Ayrshare profile key
            profile_doc = {
                "id": str(uuid4()),
                "user_id": user_id,
                "profile_key": profile_key,
                "ref_id": data.get("refId"),
                "title": profile.title,
                "linked_networks": [],
                "linked_accounts_info": {},
                "is_primary": False,
                "is_ayrshare_profile": True,  # True = has its own Ayrshare sub-user profile
                "enterprise_id": profile.enterprise_id,
                "is_enterprise": profile.is_enterprise or False,
                "created_at": datetime.now(timezone.utc)
            }
        else:
            # Business plan not available - create local profile using Primary key
            error_data = response.json() if response.text else {}
            logger.info(f"Creating local profile (Business Plan not available): {error_data}")
            
            # Fetch current linked accounts from primary profile
            account_data = await fetch_profile_linked_accounts(None)
            
            profile_doc = {
                "id": str(uuid4()),
                "user_id": user_id,
                "profile_key": None,  # Uses primary API key
                "ref_id": None,
                "title": profile.title,
                "linked_networks": account_data["linked_networks"],
                "linked_accounts_info": account_data["accounts_info"],
                "is_primary": True,  # Uses primary API key
                "is_ayrshare_profile": False,  # No dedicated Ayrshare sub-user profile
                "enterprise_id": profile.enterprise_id,
                "is_enterprise": profile.is_enterprise or False,
                "created_at": datetime.now(timezone.utc)
            }
        
        await db_conn.social_profiles.insert_one(profile_doc)
        
        return SocialProfileResponse(
            id=profile_doc["id"],
            user_id=user_id,
            profile_key=profile_doc.get("profile_key"),
            title=profile.title,
            linked_networks=profile_doc.get("linked_networks", []),
            is_primary=profile_doc.get("is_primary", False),
            enterprise_id=profile_doc.get("enterprise_id"),
            is_enterprise=profile_doc.get("is_enterprise", False),
            created_at=profile_doc["created_at"]
        )
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Ayrshare API timeout")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating social profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles")
@require_permission("social.view")
async def list_social_profiles(
    request: Request,
    user_id: str = Depends(get_current_user),
    sync: bool = Query(True, description="Whether to sync with Ayrshare (set to false for faster reads)"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    List all social profiles for the current user.
    
    Args:
        sync: If true, fetches latest linked accounts from Ayrshare.
              If false, returns cached data for faster performance.
    
    For each profile:
    - Business Plan profiles: Fetches linked accounts specific to that profile
    - Free/Premium profiles: All share the same primary account's linked accounts
    
    Security (ARCH-005): Requires social.view permission.
    """
    try:
        # Get user's enterprise_id from the database
        user_data = await db_conn.users.find_one({"id": user_id}, {"_id": 0, "enterprise_id": 1})
        user_enterprise_id = user_data.get("enterprise_id") if user_data else None
        
        # Build query to include both user's profiles AND enterprise profiles
        query = {"$or": [{"user_id": user_id}]}
        if user_enterprise_id:
            query["$or"].append({"enterprise_id": user_enterprise_id})
        
        profiles = await db_conn.social_profiles.find(
            query,
            {"_id": 0}
        ).to_list(length=100)
        
        # Only sync with Ayrshare if requested (default) or if no profiles exist
        if sync or len(profiles) == 0:
            # Fetch primary account data (for profiles without their own key)
            primary_account_data = await fetch_profile_linked_accounts(None)
            
            # If user has no profiles, auto-create a default one
            if len(profiles) == 0:
                default_profile = {
                    "id": str(uuid4()),
                    "user_id": user_id,
                    "profile_key": None,
                    "ref_id": None,
                    "title": "My Social Profile",
                    "linked_networks": primary_account_data["linked_networks"],
                    "linked_accounts_info": primary_account_data["accounts_info"],
                    "is_primary": True,
                    "is_ayrshare_profile": False,
                    "created_at": datetime.now(timezone.utc)
                }
                await db_conn.social_profiles.insert_one(default_profile)
                profiles = [default_profile]
                logger.info(f"Auto-created default social profile for user {user_id}")
            else:
                # Update each profile with its linked accounts
                for profile in profiles:
                    if profile.get("is_ayrshare_profile") and profile.get("profile_key"):
                        # Business Plan profile - fetch its own linked accounts
                        account_data = await fetch_profile_linked_accounts(profile["profile_key"])
                    else:
                        # Free/Premium profile - uses primary account
                        account_data = primary_account_data
                    
                    # Update in database
                    await db_conn.social_profiles.update_one(
                        {"id": profile["id"]},
                        {"$set": {
                            "linked_networks": account_data["linked_networks"],
                            "linked_accounts_info": account_data["accounts_info"],
                            "last_synced": datetime.now(timezone.utc)
                        }}
                    )
                    profile["linked_networks"] = account_data["linked_networks"]
                    profile["linked_accounts_info"] = account_data["accounts_info"]
            
            primary_accounts = primary_account_data["accounts_info"]
        else:
            # Return cached data without syncing
            primary_accounts = {}
            if profiles:
                primary_accounts = profiles[0].get("linked_accounts_info", {})
        
        # Remove _id from profiles
        for profile in profiles:
            profile.pop('_id', None)
        
        return {
            "profiles": profiles,
            "primary_accounts": primary_accounts
        }
        
    except Exception as e:
        logger.error(f"Error listing profiles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles/{profile_id}")
@require_permission("social.view")
async def get_social_profile(
    request: Request,
    profile_id: str,
    user_id: str = Depends(get_current_user),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get a specific social profile with its linked accounts.
    
    Security (ARCH-005): Requires social.view permission.
    """
    try:
        profile = await db_conn.social_profiles.find_one(
            {"id": profile_id, "user_id": user_id},
            {"_id": 0}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Fetch current linked accounts
        profile_key = profile.get("profile_key") if profile.get("is_ayrshare_profile") else None
        account_data = await fetch_profile_linked_accounts(profile_key)
        
        # Update stored profile
        await db_conn.social_profiles.update_one(
            {"id": profile_id},
            {"$set": {
                "linked_networks": account_data["linked_networks"],
                "linked_accounts_info": account_data["accounts_info"],
                "last_synced": datetime.now(timezone.utc)
            }}
        )
        
        profile["linked_networks"] = account_data["linked_networks"]
        profile["linked_accounts_info"] = account_data["accounts_info"]
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/profiles/{profile_id}")
@require_permission("social.manage")
async def delete_social_profile(
    request: Request,
    profile_id: str,
    user_id: str = Depends(get_current_user),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Delete a social profile.
    
    For Business Plan profiles: Also deletes the Ayrshare sub-user profile.
    For Free/Premium profiles: Only deletes local record.
    
    Security (ARCH-005): Requires social.manage permission.
    """
    try:
        profile = await db_conn.social_profiles.find_one(
            {"id": profile_id, "user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Delete from Ayrshare if it's a Business Plan profile
        if profile.get("is_ayrshare_profile") and profile.get("profile_key"):
            try:
                async with httpx.AsyncClient() as http_client:
                    response = await http_client.delete(
                        f"{AYRSHARE_BASE_URL}/profiles/{profile['profile_key']}",
                        headers=get_ayrshare_headers(),
                        timeout=30.0
                    )
                    if response.status_code == 200:
                        logger.info(f"Deleted Ayrshare profile: {profile['profile_key']}")
                    else:
                        logger.warning(f"Failed to delete Ayrshare profile: {response.text}")
            except Exception as e:
                logger.error(f"Error deleting Ayrshare profile: {e}")
        
        # Delete from MongoDB
        await db_conn.social_profiles.delete_one({"id": profile_id})
        
        return {"status": "deleted", "profile_id": profile_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SOCIAL ACCOUNT LINKING ====================

@router.post("/profiles/{profile_id}/generate-link")
@require_permission("social.manage")
async def generate_social_linking_url(
    request: Request,
    profile_id: str,
    user_id: str = Depends(get_current_user),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Generate a URL for linking social accounts to this profile.
    
    Business Plan profiles: Returns a JWT URL for Ayrshare's secure linking page.
    Free/Premium profiles: Returns the Ayrshare dashboard link.
    
    Security (ARCH-005): Requires social.manage permission.
    """
    try:
        profile = await db_conn.social_profiles.find_one(
            {"id": profile_id, "user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Check if this is a Business Plan profile with its own key
        if profile.get("is_ayrshare_profile") and profile.get("profile_key"):
            # Generate JWT URL for sub-user profile
            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(
                    f"{AYRSHARE_BASE_URL}/profiles/generateJWT",
                    headers=get_ayrshare_headers(),
                    json={
                        "profileKey": profile["profile_key"],
                        "domain": os.getenv("FRONTEND_URL", "https://app.ayrshare.com")
                    },
                    timeout=30.0
                )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "url": data.get("url"),
                    "profile_id": profile_id,
                    "type": "jwt",
                    "message": "Use this link to connect your social accounts to this profile"
                }
            else:
                logger.error(f"JWT generation failed: {response.text}")
                # Fall back to dashboard link
                return {
                    "url": "https://app.ayrshare.com/social-accounts",
                    "profile_id": profile_id,
                    "type": "dashboard",
                    "message": "Please link your social accounts in the Ayrshare dashboard"
                }
        else:
            # Free/Premium plan - return dashboard link
            return {
                "url": "https://app.ayrshare.com/social-accounts",
                "profile_id": profile_id,
                "type": "dashboard",
                "message": "Please link your social accounts in the Ayrshare dashboard. Note: On Free/Premium plans, all profiles share the same linked accounts."
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating link URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== POSTING ====================

@router.post("/posts", response_model=PostResponse)
@require_permission("social.post")
async def create_post(
    request: Request,
    post: PostCreate,
    user_id: str = Depends(get_current_user),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Create and publish a post to multiple social networks.
    
    For scheduled posts: Saves locally and will be posted at the scheduled time.
    For immediate posts: Posts directly via Ayrshare API.
    
    For Business Plan profiles: Posts using the profile's specific API key.
    For Free/Premium profiles: Posts using the primary API key.
    
    Security (ARCH-005): Requires social.post permission.
    """
    try:
        # Get profile if specified, otherwise use first available
        profile = None
        if post.profile_id:
            profile = await db_conn.social_profiles.find_one(
                {"id": post.profile_id, "user_id": user_id}
            )
            if not profile:
                raise HTTPException(status_code=404, detail="Profile not found")
        else:
            # Use first profile for user
            profile = await db_conn.social_profiles.find_one({"user_id": user_id})
            if not profile:
                raise HTTPException(status_code=400, detail="No social profile found. Please create a profile first.")
        
        # Validate platforms
        invalid_platforms = [p for p in post.platforms if p not in SUPPORTED_PLATFORMS]
        if invalid_platforms:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported platforms: {', '.join(invalid_platforms)}"
            )
        
        # If this is a SCHEDULED post, save locally and return success
        # The scheduler will handle posting at the scheduled time
        if post.schedule_date:
            post_doc = {
                "id": str(uuid4()),
                "user_id": user_id,
                "profile_id": profile["id"],
                "ayrshare_id": None,  # Will be set when actually posted
                "content": post.content,
                "platforms": post.platforms,
                "media_urls": post.media_urls,
                "schedule_date": post.schedule_date,
                "status": "scheduled",
                "post_ids": [],
                "errors": [],
                "created_at": datetime.now(timezone.utc)
            }
            
            await db_conn.social_posts.insert_one(post_doc)
            
            logger.info(f"Scheduled post saved: {post_doc['id']} for {post.schedule_date}")
            
            return PostResponse(
                id=post_doc["id"],
                status="scheduled",
                post_ids=[],
                errors=[]
            )
        
        # IMMEDIATE POST - Send to Ayrshare now
        # Build Ayrshare payload
        payload = {
            "post": post.content,
            "platforms": post.platforms
        }
        
        if post.media_urls:
            payload["mediaUrls"] = post.media_urls
        
        # Determine profile key
        profile_key = profile.get("profile_key") if profile.get("is_ayrshare_profile") else None
        
        # Post to Ayrshare
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                f"{AYRSHARE_BASE_URL}/post",
                headers=get_ayrshare_headers(profile_key),
                json=payload,
                timeout=60.0
            )
        
        data = response.json()
        logger.info(f"Ayrshare post response: {data}")
        
        # Check for plan-related errors
        if data.get("code") == 169 or data.get("action") == "Paid Plan Required":
            raise HTTPException(
                status_code=402,
                detail={
                    "message": "Ayrshare Premium or Business Plan required to post",
                    "action": "upgrade_plan",
                    "info": "The Ayrshare Free Plan does not support posting through the API. Please upgrade to Premium or Business Plan.",
                    "url": "https://www.ayrshare.com/pricing"
                }
            )
        
        # Check for other errors
        if data.get("status") == "error" or (data.get("errors") and len(data.get("errors", [])) > 0):
            errors = data.get("errors", [])
            
            # Check if any platform is not linked
            not_linked = [e.get("platform") for e in errors if e.get("code") == 156]
            if not_linked:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": f"Some platforms are not linked: {', '.join(not_linked)}",
                        "not_linked": not_linked,
                        "action": "Please link your social accounts",
                        "profile_id": profile["id"]
                    }
                )
            
            error_messages = [e.get("message", "Unknown error") for e in errors]
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Failed to create post",
                    "errors": error_messages
                }
            )
        
        # Store post in MongoDB
        post_doc = {
            "id": str(uuid4()),
            "user_id": user_id,
            "profile_id": profile["id"],
            "ayrshare_id": data.get("id"),
            "content": post.content,
            "platforms": post.platforms,
            "media_urls": post.media_urls,
            "schedule_date": post.schedule_date,
            "status": data.get("status", "success"),
            "post_ids": data.get("postIds", []),
            "errors": data.get("errors", []),
            "created_at": datetime.now(timezone.utc)
        }
        
        await db_conn.social_posts.insert_one(post_doc)
        
        return PostResponse(
            id=post_doc["id"],
            status=data.get("status", "success"),
            post_ids=data.get("postIds", []),
            errors=data.get("errors", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts")
@require_permission("social.view")
async def list_posts(
    request: Request,
    profile_id: Optional[str] = None,
    user_id: str = Depends(get_current_user),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    List all posts for the user, optionally filtered by profile.
    
    Security (ARCH-005): Requires social.view permission.
    """
    try:
        query = {"user_id": user_id}
        if profile_id:
            query["profile_id"] = profile_id
        
        posts = await db_conn.social_posts.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).to_list(length=100)
        
        return {"posts": posts}
        
    except Exception as e:
        logger.error(f"Error listing posts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts/{post_id}")
@require_permission("social.view")
async def get_post(
    request: Request,
    post_id: str,
    user_id: str = Depends(get_current_user),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get a specific post with its details.
    
    Security (ARCH-005): Requires social.view permission.
    """
    try:
        post = await db_conn.social_posts.find_one(
            {"id": post_id, "user_id": user_id},
            {"_id": 0}
        )
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        return post
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting post: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/posts/{post_id}")
@require_permission("social.manage")
async def delete_post(
    request: Request,
    post_id: str,
    user_id: str = Depends(get_current_user),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Delete a post from social networks.
    
    Security (ARCH-005): Requires social.manage permission.
    """
    try:
        post = await db_conn.social_posts.find_one(
            {"id": post_id, "user_id": user_id}
        )
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        profile = await db_conn.social_profiles.find_one(
            {"id": post.get("profile_id")}
        )
        
        if profile and post.get("ayrshare_id"):
            # Delete from Ayrshare
            profile_key = profile.get("profile_key") if profile.get("is_ayrshare_profile") else None
            try:
                async with httpx.AsyncClient() as http_client:
                    await http_client.delete(
                        f"{AYRSHARE_BASE_URL}/post/{post['ayrshare_id']}",
                        headers=get_ayrshare_headers(profile_key),
                        timeout=30.0
                    )
            except Exception as e:
                logger.warning(f"Failed to delete from Ayrshare: {e}")
        
        # Delete from MongoDB
        await db_conn.social_posts.delete_one({"id": post_id})
        
        return {"status": "deleted", "post_id": post_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting post: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ANALYTICS ====================

@router.get("/analytics/post/{post_id}")
@require_permission("analytics.view_own")
async def get_post_analytics(
    request: Request,
    post_id: str,
    user_id: str = Depends(get_current_user),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get engagement analytics for a specific post.
    
    Security (ARCH-005): Requires analytics.view_own permission.
    """
    try:
        post = await db_conn.social_posts.find_one(
            {"id": post_id, "user_id": user_id}
        )
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        profile = await db_conn.social_profiles.find_one(
            {"id": post.get("profile_id")}
        )
        
        if not profile or not post.get("ayrshare_id"):
            raise HTTPException(status_code=400, detail="Cannot retrieve analytics")
        
        profile_key = profile.get("profile_key") if profile.get("is_ayrshare_profile") else None
        
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                f"{AYRSHARE_BASE_URL}/analytics/post",
                headers=get_ayrshare_headers(profile_key),
                json={"id": post.get("ayrshare_id")},
                timeout=30.0
            )
        
        if response.status_code != 200:
            logger.error(f"Analytics retrieval failed: {response.text}")
            raise HTTPException(
                status_code=400,
                detail="Failed to retrieve analytics"
            )
        
        return response.json()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/profile/{profile_id}")
@require_permission("analytics.view_own")
async def get_profile_analytics(
    request: Request,
    profile_id: str,
    platforms: Optional[str] = None,
    user_id: str = Depends(get_current_user),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get overall analytics for a social profile.
    
    Security (ARCH-005): Requires analytics.view_own permission.
    """
    try:
        profile = await db_conn.social_profiles.find_one(
            {"id": profile_id, "user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        profile_key = profile.get("profile_key") if profile.get("is_ayrshare_profile") else None
        
        params = {}
        if platforms:
            params["platforms"] = platforms.split(",")
        
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{AYRSHARE_BASE_URL}/analytics/social",
                headers=get_ayrshare_headers(profile_key),
                params=params,
                timeout=30.0
            )
        
        if response.status_code != 200:
            logger.error(f"Profile analytics failed: {response.text}")
            raise HTTPException(
                status_code=400,
                detail="Failed to retrieve profile analytics"
            )
        
        return response.json()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== POST HISTORY ====================

@router.get("/history/{profile_id}")
@require_permission("social.view")
async def get_post_history(
    request: Request,
    profile_id: str,
    user_id: str = Depends(get_current_user),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get post history from Ayrshare for a specific profile."""
    try:
        profile = await db_conn.social_profiles.find_one(
            {"id": profile_id, "user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        profile_key = profile.get("profile_key") if profile.get("is_ayrshare_profile") else None
        
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{AYRSHARE_BASE_URL}/history",
                headers=get_ayrshare_headers(profile_key),
                timeout=30.0
            )
        
        if response.status_code != 200:
            logger.error(f"History retrieval failed: {response.text}")
            raise HTTPException(
                status_code=400,
                detail="Failed to retrieve history"
            )
        
        return response.json()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== UTILITY ENDPOINTS ====================

@router.get("/supported-platforms")
@require_permission("social.view")
async def get_supported_platforms(request: Request):
    """Get list of supported social media platforms."""
    return {
        "platforms": SUPPORTED_PLATFORMS,
        "details": {
            "twitter": {"name": "Twitter/X", "supports_media": True, "supports_scheduling": True},
            "facebook": {"name": "Facebook Pages", "supports_media": True, "supports_scheduling": True},
            "instagram": {"name": "Instagram Business", "supports_media": True, "supports_scheduling": True},
            "linkedin": {"name": "LinkedIn", "supports_media": True, "supports_scheduling": True},
            "tiktok": {"name": "TikTok", "supports_media": True, "supports_scheduling": True},
            "pinterest": {"name": "Pinterest", "supports_media": True, "supports_scheduling": True},
            "youtube": {"name": "YouTube", "supports_media": True, "supports_scheduling": True},
            "threads": {"name": "Threads", "supports_media": True, "supports_scheduling": True},
            "bluesky": {"name": "Bluesky", "supports_media": True, "supports_scheduling": True},
            "reddit": {"name": "Reddit", "supports_media": True, "supports_scheduling": True},
            "gmb": {"name": "Google My Business", "supports_media": True, "supports_scheduling": True}
        }
    }


# ==================== IMPORT HISTORY ====================

@router.post("/import-history")
@require_permission("social.manage")
async def import_historical_posts(
    request: Request,
    profile_id: str,
    user_id: str = Depends(get_current_user),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Import historical posts from Ayrshare for linked social accounts.
    Fetches posts and stores them locally for analysis.
    """
    try:
        # Get profile
        profile = await db_conn.social_profiles.find_one(
            {"id": profile_id, "user_id": user_id},
            {"_id": 0}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        profile_key = profile.get("profile_key") if profile.get("is_ayrshare_profile") else None
        
        # Fetch history from Ayrshare
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{AYRSHARE_BASE_URL}/history",
                headers=get_ayrshare_headers(profile_key),
                timeout=60.0
            )
        
        if response.status_code != 200:
            logger.error(f"History import failed: {response.text}")
            
            # Check if it's a plan limitation
            data = response.json() if response.text else {}
            if data.get("code") == 169 or "plan" in response.text.lower():
                raise HTTPException(
                    status_code=402,
                    detail={
                        "message": "History access requires Ayrshare Premium or Business Plan",
                        "action": "upgrade_plan",
                        "url": "https://www.ayrshare.com/pricing"
                    }
                )
            
            raise HTTPException(status_code=400, detail="Failed to import history")
        
        history = response.json()
        imported_count = 0
        
        # Process each post from history
        for item in history if isinstance(history, list) else []:
            # Check if already imported
            existing = await db_conn.social_posts.find_one({"ayrshare_id": item.get("id")})
            if existing:
                continue
            
            # Create post document from history
            post_doc = {
                "id": str(uuid4()),
                "user_id": user_id,
                "profile_id": profile_id,
                "ayrshare_id": item.get("id"),
                "content": item.get("post", ""),
                "platforms": item.get("platforms", []),
                "media_urls": item.get("mediaUrls", []),
                "schedule_date": item.get("scheduleDate"),
                "status": item.get("status", "imported"),
                "post_ids": item.get("postIds", []),
                "errors": item.get("errors", []),
                "created_at": datetime.fromisoformat(item.get("created", datetime.now(timezone.utc).isoformat()).replace("Z", "+00:00")) if item.get("created") else datetime.now(timezone.utc),
                "imported_at": datetime.now(timezone.utc),
                "is_imported": True,
                "original_data": item  # Store original for reference
            }
            
            await db_conn.social_posts.insert_one(post_doc)
            imported_count += 1
        
        return {
            "success": True,
            "imported_count": imported_count,
            "total_in_history": len(history) if isinstance(history, list) else 0,
            "message": f"Successfully imported {imported_count} new posts from history"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts/{post_id}/analyze")
@require_permission("content.analyze")
async def analyze_post(
    request: Request,
    post_id: str,
    user_id: str = Depends(get_current_user),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Analyze a specific post (including imported ones) for content moderation.
    Returns cultural analysis and compliance scores.
    """
    try:
        # Get the post
        post = await db_conn.social_posts.find_one(
            {"id": post_id, "user_id": user_id},
            {"_id": 0}
        )
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Check if already analyzed
        if post.get("analysis"):
            return {
                "post_id": post_id,
                "content": post.get("content", ""),
                "analysis": post.get("analysis"),
                "analyzed_at": post.get("analyzed_at")
            }
        
        # Perform analysis using internal content analysis endpoint
        from .content import analyze_content_internal
        
        content = post.get("content", "")
        if not content:
            return {
                "post_id": post_id,
                "content": "",
                "analysis": None,
                "message": "Post has no text content to analyze"
            }
        
        analysis_result = await analyze_content_internal(content, user_id)
        
        # Update post with analysis
        await db_conn.social_posts.update_one(
            {"id": post_id},
            {
                "$set": {
                    "analysis": analysis_result,
                    "analyzed_at": datetime.now(timezone.utc)
                }
            }
        )
        
        return {
            "post_id": post_id,
            "content": content,
            "analysis": analysis_result,
            "analyzed_at": datetime.now(timezone.utc)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing post: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
