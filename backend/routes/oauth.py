"""
OAuth Authentication Routes
Handles Google (Emergent), Microsoft, Apple, and Slack OAuth
"""
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import RedirectResponse
import os
import httpx
from datetime import datetime, timezone, timedelta
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db

router = APIRouter(prefix="/oauth", tags=["oauth"])

# Database instance (set by main app)
db = None

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    """Set the database instance for this router"""
    global db
    db = database


async def check_user_subscription(user_id: str) -> bool:
    """
    Check if user has active subscription
    Returns True if user can access the platform
    """
    user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        return False
    
    # Admin always has access
    if user.get("role") == "admin":
        return True
    
    # Check subscription status
    subscription = user.get("subscription", {})
    if not subscription:
        return False
    
    status = subscription.get("status")
    plan = subscription.get("plan", "free")
    
    # Allow active subscriptions or trial periods
    if status in ["active", "trialing"]:
        return True
    
    # Check if subscription end date is still valid (grace period)
    if subscription.get("current_period_end"):
        try:
            end_date = datetime.fromisoformat(subscription["current_period_end"])
            if end_date > datetime.now(timezone.utc):
                return True
        except (ValueError, TypeError) as e:
            logging.warning(f"Invalid subscription period format: {e}")
    
    # Free tier users can't access
    if plan == "free":
        return False
    
    return False


@router.post("/session")
async def create_session(request: Request, response: Response, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Process Emergent Auth session_id and create authenticated session
    Called by frontend after OAuth redirect
    """
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(400, "Missing session_id")
    
    # Call Emergent Auth API to get user data
    try:
        async with httpx.AsyncClient() as client:
            auth_response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id},
                timeout=10.0
            )
            
            if auth_response.status_code != 200:
                raise HTTPException(401, "Invalid session")
            
            oauth_data = auth_response.json()
    except Exception as e:
        logging.error(f"Emergent Auth API error: {e}")
        raise HTTPException(500, "Authentication failed")
    
    # Extract user data
    email = oauth_data.get("email")
    name = oauth_data.get("name")
    picture = oauth_data.get("picture")
    session_token = oauth_data.get("session_token")
    
    if not email or not session_token:
        raise HTTPException(400, "Invalid OAuth response")
    
    # Check if user exists
    existing_user = await db_conn.users.find_one({"email": email}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["id"]
        
        # Update OAuth info if changed
        await db_conn.users.update_one(
            {"id": user_id},
            {"$set": {
                "oauth_provider": "google",
                "oauth_picture": picture,
                "last_login": datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        # Create new user
        from uuid import uuid4
        user_id = str(uuid4())
        
        # Check if email domain belongs to enterprise
        enterprise_id = None
        role = "user"
        domain = email.split("@")[1]
        
        enterprise = await db_conn.enterprises.find_one({"domain": domain}, {"_id": 0})
        if enterprise:
            enterprise_id = enterprise["id"]
            role = "enterprise_user"
        
        new_user = {
            "id": user_id,
            "email": email,
            "full_name": name or email.split("@")[0],
            "role": role,
            "oauth_provider": "google",
            "oauth_picture": picture,
            "email_verified": True,  # OAuth emails are verified
            "enterprise_id": enterprise_id,
            "subscription": {
                "plan": "free",
                "status": "inactive",
                "stripe_customer_id": None,
                "stripe_subscription_id": None
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_login": datetime.now(timezone.utc).isoformat()
        }
        
        await db_conn.users.insert_one(new_user)
    
    # Check subscription status
    has_subscription = await check_user_subscription(user_id)
    
    if not has_subscription:
        # User doesn't have active subscription
        return {
            "success": False,
            "error": "subscription_required",
            "message": "Active subscription required to access the platform",
            "user": {
                "id": user_id,
                "email": email,
                "name": name
            }
        }
    
    # Store session in database
    session_expiry = datetime.now(timezone.utc) + timedelta(days=7)
    await db_conn.sessions.insert_one({
        "session_token": session_token,
        "user_id": user_id,
        "expires_at": session_expiry.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Set httpOnly cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 60 * 60,  # 7 days
        path="/"
    )
    
    # Get full user data
    user = await db_conn.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    
    return {
        "success": True,
        "user": user,
        "session_token": session_token
    }


@router.get("/validate-session")
async def validate_session(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Validate existing session token
    Checks both cookie and Authorization header
    """
    # Try cookie first, then Authorization header
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.replace("Bearer ", "")
    
    if not session_token:
        raise HTTPException(401, "No session token")
    
    # Check session in database
    session = await db_conn.sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(401, "Invalid session")
    
    # Check expiry
    expires_at = datetime.fromisoformat(session["expires_at"])
    if expires_at < datetime.now(timezone.utc):
        await db_conn.sessions.delete_one({"session_token": session_token})
        raise HTTPException(401, "Session expired")
    
    # Get user
    user = await db_conn.users.find_one({"id": session["user_id"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(404, "User not found")
    
    # Check subscription
    has_subscription = await check_user_subscription(user["id"])
    if not has_subscription:
        return {
            "valid": False,
            "error": "subscription_required",
            "message": "Active subscription required"
        }
    
    return {
        "valid": True,
        "user": user
    }


@router.post("/logout")
async def logout(request: Request, response: Response, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Logout user and clear session (OAuth and JWT)
    
    Security (ARCH-022): Clears all authentication cookies
    """
    session_token = request.cookies.get("session_token")
    if session_token:
        await db_conn.sessions.delete_one({"session_token": session_token})
    
    # Clear all authentication cookies
    response.delete_cookie("session_token", path="/")
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    
    return {"success": True}


# Placeholder routes for other OAuth providers
# These will be implemented when credentials are provided

@router.get("/microsoft/login")
async def microsoft_login():
    """
    Microsoft OAuth login - Placeholder
    Requires: MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, MICROSOFT_TENANT_ID
    """
    client_id = os.getenv("MICROSOFT_CLIENT_ID")
    if not client_id:
        raise HTTPException(501, "Microsoft OAuth not configured. Please add MICROSOFT_CLIENT_ID to .env")
    
    # TODO: Implement Microsoft OAuth flow
    redirect_uri = os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:8001/api/oauth/microsoft/callback")
    tenant_id = os.getenv("MICROSOFT_TENANT_ID", "common")
    
    auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": "openid email profile",
        "response_mode": "query"
    }
    
    return {"message": "Microsoft OAuth ready", "auth_url": auth_url, "params": params}


@router.get("/microsoft/callback")
async def microsoft_callback(code: str):
    """
    Microsoft OAuth callback - Placeholder
    """
    raise HTTPException(501, "Microsoft OAuth callback not fully implemented")


@router.get("/apple/login")
async def apple_login():
    """
    Apple Sign In - Placeholder
    Requires: APPLE_CLIENT_ID, APPLE_TEAM_ID, APPLE_KEY_ID, APPLE_PRIVATE_KEY
    """
    client_id = os.getenv("APPLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(501, "Apple Sign In not configured. Please add APPLE_CLIENT_ID to .env")
    
    # TODO: Implement Apple Sign In flow
    return {"message": "Apple Sign In ready - implementation pending"}


@router.get("/apple/callback")
async def apple_callback():
    """
    Apple Sign In callback - Placeholder
    """
    raise HTTPException(501, "Apple Sign In callback not fully implemented")


@router.get("/slack/login")
async def slack_login():
    """
    Slack OAuth login - Placeholder
    Requires: SLACK_CLIENT_ID, SLACK_CLIENT_SECRET
    """
    client_id = os.getenv("SLACK_CLIENT_ID")
    if not client_id:
        raise HTTPException(501, "Slack OAuth not configured. Please add SLACK_CLIENT_ID to .env")
    
    # TODO: Implement Slack OAuth flow
    return {"message": "Slack OAuth ready - implementation pending"}


@router.get("/slack/callback")
async def slack_callback():
    """
    Slack OAuth callback - Placeholder
    """
    raise HTTPException(501, "Slack OAuth callback not fully implemented")
