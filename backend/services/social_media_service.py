"""
Social Media Integration Service
Production-ready OAuth 2.0 implementation for Twitter/X and LinkedIn
Handles token storage, refresh, and posting logic
"""

import os
import logging
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any
from urllib.parse import urlencode
import base64
import hashlib
import secrets
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'contentry_db')]

# Environment variables for API credentials
TWITTER_CLIENT_ID = os.environ.get('TWITTER_CLIENT_ID', '')
TWITTER_CLIENT_SECRET = os.environ.get('TWITTER_CLIENT_SECRET', '')
TWITTER_REDIRECT_URI = os.environ.get('TWITTER_REDIRECT_URI', 'http://localhost:3000/api/social/twitter/callback')

LINKEDIN_CLIENT_ID = os.environ.get('LINKEDIN_CLIENT_ID', '')
LINKEDIN_CLIENT_SECRET = os.environ.get('LINKEDIN_CLIENT_SECRET', '')
LINKEDIN_REDIRECT_URI = os.environ.get('LINKEDIN_REDIRECT_URI', 'http://localhost:3000/api/social/linkedin/callback')

FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')


class SocialMediaService:
    """
    Unified social media service for Twitter/X and LinkedIn
    Handles OAuth 2.0 authentication and posting
    """
    
    def __init__(self):
        self.twitter_configured = bool(TWITTER_CLIENT_ID and TWITTER_CLIENT_SECRET)
        self.linkedin_configured = bool(LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET)
        
        if not self.twitter_configured:
            logger.warning("Twitter API credentials not configured - using mock mode")
        if not self.linkedin_configured:
            logger.warning("LinkedIn API credentials not configured - using mock mode")
    
    # ==================== TOKEN MANAGEMENT ====================
    
    async def store_tokens(self, user_id: str, platform: str, tokens: Dict) -> bool:
        """Store OAuth tokens securely in database"""
        try:
            token_doc = {
                "user_id": user_id,
                "platform": platform,
                "access_token": tokens.get("access_token"),
                "refresh_token": tokens.get("refresh_token"),
                "token_type": tokens.get("token_type", "Bearer"),
                "expires_at": tokens.get("expires_at"),
                "scope": tokens.get("scope"),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Upsert token document
            await db.social_tokens.update_one(
                {"user_id": user_id, "platform": platform},
                {"$set": token_doc},
                upsert=True
            )
            
            # Update user's social connection status
            await db.users.update_one(
                {"id": user_id},
                {"$set": {f"social_connections.{platform}": True}}
            )
            
            logger.info(f"Stored {platform} tokens for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing tokens: {str(e)}")
            return False
    
    async def get_tokens(self, user_id: str, platform: str) -> Optional[Dict]:
        """Retrieve OAuth tokens for a user and platform"""
        try:
            token_doc = await db.social_tokens.find_one(
                {"user_id": user_id, "platform": platform},
                {"_id": 0}
            )
            return token_doc
        except Exception as e:
            logger.error(f"Error retrieving tokens: {str(e)}")
            return None
    
    async def refresh_token_if_needed(self, user_id: str, platform: str) -> Optional[str]:
        """Check if token needs refresh and refresh if necessary"""
        tokens = await self.get_tokens(user_id, platform)
        
        if not tokens:
            return None
        
        # Check if token is expired or will expire soon (within 5 minutes)
        expires_at = tokens.get("expires_at")
        if expires_at:
            expiry_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) >= expiry_time - timedelta(minutes=5):
                # Token needs refresh
                if platform == "twitter":
                    new_tokens = await self._refresh_twitter_token(tokens.get("refresh_token"))
                elif platform == "linkedin":
                    new_tokens = await self._refresh_linkedin_token(tokens.get("refresh_token"))
                else:
                    return None
                
                if new_tokens:
                    await self.store_tokens(user_id, platform, new_tokens)
                    return new_tokens.get("access_token")
                return None
        
        return tokens.get("access_token")
    
    async def revoke_tokens(self, user_id: str, platform: str) -> bool:
        """Revoke and delete OAuth tokens"""
        try:
            # Delete from database
            await db.social_tokens.delete_one({"user_id": user_id, "platform": platform})
            
            # Update user's social connection status
            await db.users.update_one(
                {"id": user_id},
                {"$set": {f"social_connections.{platform}": False}}
            )
            
            logger.info(f"Revoked {platform} tokens for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking tokens: {str(e)}")
            return False
    
    # ==================== TWITTER/X API ====================
    
    def get_twitter_auth_url(self, user_id: str) -> Dict:
        """
        Generate Twitter OAuth 2.0 authorization URL with PKCE
        Twitter API v2 uses OAuth 2.0 with PKCE for user authentication
        """
        if not self.twitter_configured:
            return {
                "error": "Twitter API not configured",
                "is_mocked": True,
                "mock_url": f"{FRONTEND_URL}/contentry/settings?mock_twitter=true"
            }
        
        # Generate PKCE code verifier and challenge
        code_verifier = secrets.token_urlsafe(64)[:128]
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')
        
        # Store code verifier for later use
        state = secrets.token_urlsafe(32)
        
        # Store state and verifier temporarily (should use Redis in production)
        asyncio.create_task(self._store_oauth_state(user_id, "twitter", state, code_verifier))
        
        params = {
            "response_type": "code",
            "client_id": TWITTER_CLIENT_ID,
            "redirect_uri": TWITTER_REDIRECT_URI,
            "scope": "tweet.read tweet.write users.read offline.access",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        auth_url = f"https://twitter.com/i/oauth2/authorize?{urlencode(params)}"
        
        return {
            "auth_url": auth_url,
            "state": state,
            "is_mocked": False
        }
    
    async def handle_twitter_callback(self, code: str, state: str) -> Dict:
        """Handle Twitter OAuth callback and exchange code for tokens"""
        if not self.twitter_configured:
            return {"error": "Twitter API not configured", "is_mocked": True}
        
        try:
            # Retrieve stored state and code verifier
            oauth_state = await self._get_oauth_state(state)
            if not oauth_state:
                return {"error": "Invalid or expired state"}
            
            user_id = oauth_state["user_id"]
            code_verifier = oauth_state["code_verifier"]
            
            # Exchange code for tokens
            async with httpx.AsyncClient() as client:
                token_response = await client.post(
                    "https://api.twitter.com/2/oauth2/token",
                    data={
                        "code": code,
                        "grant_type": "authorization_code",
                        "client_id": TWITTER_CLIENT_ID,
                        "redirect_uri": TWITTER_REDIRECT_URI,
                        "code_verifier": code_verifier
                    },
                    auth=(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET)
                )
                
                if token_response.status_code != 200:
                    logger.error(f"Twitter token error: {token_response.text}")
                    return {"error": "Failed to get access token"}
                
                token_data = token_response.json()
                
                # Calculate expiry time
                expires_in = token_data.get("expires_in", 7200)
                expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()
                token_data["expires_at"] = expires_at
                
                # Store tokens
                await self.store_tokens(user_id, "twitter", token_data)
                
                # Clean up state
                await self._delete_oauth_state(state)
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "platform": "twitter"
                }
                
        except Exception as e:
            logger.error(f"Twitter callback error: {str(e)}")
            return {"error": str(e)}
    
    async def _refresh_twitter_token(self, refresh_token: str) -> Optional[Dict]:
        """Refresh Twitter access token"""
        if not self.twitter_configured or not refresh_token:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.twitter.com/2/oauth2/token",
                    data={
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token",
                        "client_id": TWITTER_CLIENT_ID
                    },
                    auth=(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET)
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    expires_in = token_data.get("expires_in", 7200)
                    token_data["expires_at"] = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()
                    return token_data
                    
        except Exception as e:
            logger.error(f"Twitter token refresh error: {str(e)}")
        
        return None
    
    async def post_to_twitter(self, user_id: str, content: str, media_ids: list = None) -> Dict:
        """
        Post a tweet using Twitter API v2
        """
        if not self.twitter_configured:
            logger.info(f"[MOCK] Twitter post for user {user_id}: {content[:50]}...")
            return {
                "success": True,
                "platform": "twitter",
                "post_id": f"mock_tweet_{secrets.token_hex(8)}",
                "post_url": f"https://twitter.com/user/status/mock_{secrets.token_hex(8)}",
                "posted_at": datetime.now(timezone.utc).isoformat(),
                "is_mocked": True,
                "message": "Twitter API not configured - mock response"
            }
        
        try:
            # Get valid access token
            access_token = await self.refresh_token_if_needed(user_id, "twitter")
            
            if not access_token:
                return {"success": False, "error": "No valid Twitter access token"}
            
            # Prepare tweet data
            tweet_data = {"text": content}
            if media_ids:
                tweet_data["media"] = {"media_ids": media_ids}
            
            # Post tweet
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.twitter.com/2/tweets",
                    json=tweet_data,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 201:
                    data = response.json()
                    tweet_id = data["data"]["id"]
                    
                    # Get username for URL
                    user_response = await client.get(
                        "https://api.twitter.com/2/users/me",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    username = "user"
                    if user_response.status_code == 200:
                        username = user_response.json()["data"]["username"]
                    
                    return {
                        "success": True,
                        "platform": "twitter",
                        "post_id": tweet_id,
                        "post_url": f"https://twitter.com/{username}/status/{tweet_id}",
                        "posted_at": datetime.now(timezone.utc).isoformat(),
                        "is_mocked": False
                    }
                else:
                    logger.error(f"Twitter post error: {response.text}")
                    return {"success": False, "error": response.text, "is_mocked": False}
                    
        except Exception as e:
            logger.error(f"Twitter posting error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # ==================== LINKEDIN API ====================
    
    def get_linkedin_auth_url(self, user_id: str) -> Dict:
        """
        Generate LinkedIn OAuth 2.0 authorization URL
        """
        if not self.linkedin_configured:
            return {
                "error": "LinkedIn API not configured",
                "is_mocked": True,
                "mock_url": f"{FRONTEND_URL}/contentry/settings?mock_linkedin=true"
            }
        
        state = secrets.token_urlsafe(32)
        
        # Store state temporarily
        import asyncio
        asyncio.create_task(self._store_oauth_state(user_id, "linkedin", state, ""))
        
        params = {
            "response_type": "code",
            "client_id": LINKEDIN_CLIENT_ID,
            "redirect_uri": LINKEDIN_REDIRECT_URI,
            "scope": "openid profile email w_member_social",
            "state": state
        }
        
        auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
        
        return {
            "auth_url": auth_url,
            "state": state,
            "is_mocked": False
        }
    
    async def handle_linkedin_callback(self, code: str, state: str) -> Dict:
        """Handle LinkedIn OAuth callback and exchange code for tokens"""
        if not self.linkedin_configured:
            return {"error": "LinkedIn API not configured", "is_mocked": True}
        
        try:
            # Retrieve stored state
            oauth_state = await self._get_oauth_state(state)
            if not oauth_state:
                return {"error": "Invalid or expired state"}
            
            user_id = oauth_state["user_id"]
            
            # Exchange code for tokens
            async with httpx.AsyncClient() as client:
                token_response = await client.post(
                    "https://www.linkedin.com/oauth/v2/accessToken",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "client_id": LINKEDIN_CLIENT_ID,
                        "client_secret": LINKEDIN_CLIENT_SECRET,
                        "redirect_uri": LINKEDIN_REDIRECT_URI
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if token_response.status_code != 200:
                    logger.error(f"LinkedIn token error: {token_response.text}")
                    return {"error": "Failed to get access token"}
                
                token_data = token_response.json()
                
                # Calculate expiry time
                expires_in = token_data.get("expires_in", 5184000)  # 60 days default
                expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()
                token_data["expires_at"] = expires_at
                
                # Get LinkedIn user info for profile URN
                userinfo_response = await client.get(
                    "https://api.linkedin.com/v2/userinfo",
                    headers={"Authorization": f"Bearer {token_data['access_token']}"}
                )
                
                if userinfo_response.status_code == 200:
                    user_info = userinfo_response.json()
                    token_data["linkedin_sub"] = user_info.get("sub")
                
                # Store tokens
                await self.store_tokens(user_id, "linkedin", token_data)
                
                # Clean up state
                await self._delete_oauth_state(state)
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "platform": "linkedin"
                }
                
        except Exception as e:
            logger.error(f"LinkedIn callback error: {str(e)}")
            return {"error": str(e)}
    
    async def _refresh_linkedin_token(self, refresh_token: str) -> Optional[Dict]:
        """Refresh LinkedIn access token"""
        if not self.linkedin_configured or not refresh_token:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://www.linkedin.com/oauth/v2/accessToken",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": LINKEDIN_CLIENT_ID,
                        "client_secret": LINKEDIN_CLIENT_SECRET
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    expires_in = token_data.get("expires_in", 5184000)
                    token_data["expires_at"] = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()
                    return token_data
                    
        except Exception as e:
            logger.error(f"LinkedIn token refresh error: {str(e)}")
        
        return None
    
    async def post_to_linkedin(self, user_id: str, content: str, media_url: str = None) -> Dict:
        """
        Post to LinkedIn using LinkedIn API v2
        """
        if not self.linkedin_configured:
            logger.info(f"[MOCK] LinkedIn post for user {user_id}: {content[:50]}...")
            return {
                "success": True,
                "platform": "linkedin",
                "post_id": f"mock_li_{secrets.token_hex(8)}",
                "post_url": f"https://linkedin.com/feed/update/mock_{secrets.token_hex(8)}",
                "posted_at": datetime.now(timezone.utc).isoformat(),
                "is_mocked": True,
                "message": "LinkedIn API not configured - mock response"
            }
        
        try:
            # Get tokens
            tokens = await self.get_tokens(user_id, "linkedin")
            if not tokens:
                return {"success": False, "error": "No LinkedIn access token"}
            
            access_token = await self.refresh_token_if_needed(user_id, "linkedin")
            if not access_token:
                return {"success": False, "error": "Failed to get valid access token"}
            
            linkedin_sub = tokens.get("linkedin_sub")
            if not linkedin_sub:
                return {"success": False, "error": "LinkedIn user ID not found"}
            
            # Prepare post data (UGC Post format)
            post_data = {
                "author": f"urn:li:person:{linkedin_sub}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # Post to LinkedIn
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.linkedin.com/v2/ugcPosts",
                    json=post_data,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "X-Restli-Protocol-Version": "2.0.0"
                    }
                )
                
                if response.status_code == 201:
                    # Extract post ID from header
                    post_id = response.headers.get("x-restli-id", "")
                    
                    return {
                        "success": True,
                        "platform": "linkedin",
                        "post_id": post_id,
                        "post_url": f"https://www.linkedin.com/feed/update/{post_id}",
                        "posted_at": datetime.now(timezone.utc).isoformat(),
                        "is_mocked": False
                    }
                else:
                    logger.error(f"LinkedIn post error: {response.text}")
                    return {"success": False, "error": response.text, "is_mocked": False}
                    
        except Exception as e:
            logger.error(f"LinkedIn posting error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # ==================== STATE MANAGEMENT ====================
    
    async def _store_oauth_state(self, user_id: str, platform: str, state: str, code_verifier: str):
        """Store OAuth state temporarily"""
        try:
            await db.oauth_states.update_one(
                {"state": state},
                {
                    "$set": {
                        "user_id": user_id,
                        "platform": platform,
                        "state": state,
                        "code_verifier": code_verifier,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
                    }
                },
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error storing OAuth state: {str(e)}")
    
    async def _get_oauth_state(self, state: str) -> Optional[Dict]:
        """Retrieve OAuth state"""
        try:
            state_doc = await db.oauth_states.find_one({"state": state}, {"_id": 0})
            if state_doc:
                # Check if expired
                expires_at = state_doc.get("expires_at")
                if expires_at:
                    expiry_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    if datetime.now(timezone.utc) > expiry_time:
                        await self._delete_oauth_state(state)
                        return None
            return state_doc
        except Exception as e:
            logger.error(f"Error retrieving OAuth state: {str(e)}")
            return None
    
    async def _delete_oauth_state(self, state: str):
        """Delete OAuth state"""
        try:
            await db.oauth_states.delete_one({"state": state})
        except Exception as e:
            logger.error(f"Error deleting OAuth state: {str(e)}")
    
    # ==================== UTILITY METHODS ====================
    
    def get_configuration_status(self) -> Dict:
        """Get current API configuration status"""
        return {
            "twitter": {
                "configured": self.twitter_configured,
                "api_version": "v2",
                "features": ["tweet", "read", "offline_access"] if self.twitter_configured else []
            },
            "linkedin": {
                "configured": self.linkedin_configured,
                "api_version": "v2",
                "features": ["share", "profile", "email"] if self.linkedin_configured else []
            },
            "facebook": {
                "configured": False,
                "api_version": "Graph API v18.0",
                "features": [],
                "note": "Facebook integration requires app review"
            },
            "instagram": {
                "configured": False,
                "api_version": "Graph API v18.0",
                "features": [],
                "note": "Instagram requires Facebook Business account"
            }
        }


# Create singleton instance
social_media_service = SocialMediaService()


# Import asyncio for async task creation
import asyncio
