"""
Enterprise SSO Integration
Supports Microsoft Entra ID (Azure AD) and Okta
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import os
import logging
import httpx
from datetime import datetime, timezone
import uuid
from urllib.parse import urlencode
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db

router = APIRouter(prefix="/sso", tags=["sso"])
logger = logging.getLogger(__name__)

# Database will be set by server.py
db = None

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    """Set database instance"""
    global db
    db = database


# SSO Configuration - loaded dynamically to ensure .env is loaded first
def get_microsoft_config():
    return {
        'client_id': os.getenv('MICROSOFT_CLIENT_ID', ''),
        'client_secret': os.getenv('MICROSOFT_CLIENT_SECRET', ''),
        'tenant_id': os.getenv('MICROSOFT_TENANT_ID', 'common'),
        'redirect_uri': os.getenv('MICROSOFT_REDIRECT_URI', 'http://localhost:3000/api/auth/callback/microsoft'),
        'authorize_url': os.getenv('MICROSOFT_OAUTH_AUTHORIZE_URL', 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'),
        'token_url': os.getenv('MICROSOFT_OAUTH_TOKEN_URL', 'https://login.microsoftonline.com/common/oauth2/v2.0/token'),
    }

def get_okta_config():
    return {
        'domain': os.getenv('OKTA_DOMAIN', 'your-company.okta.com'),
        'client_id': os.getenv('OKTA_CLIENT_ID', 'your-okta-client-id'),
        'client_secret': os.getenv('OKTA_CLIENT_SECRET', 'your-okta-client-secret'),
        'redirect_uri': os.getenv('OKTA_REDIRECT_URI', 'http://localhost:3000/api/sso/okta/callback'),
    }

def get_frontend_url():
    return os.getenv('FRONTEND_URL', 'http://localhost:3000')

# Legacy constants for backward compatibility - these will be empty on first load
MICROSOFT_CLIENT_ID = os.getenv('MICROSOFT_CLIENT_ID', '')
MICROSOFT_CLIENT_SECRET = os.getenv('MICROSOFT_CLIENT_SECRET', '')
MICROSOFT_TENANT_ID = os.getenv('MICROSOFT_TENANT_ID', 'common')
MICROSOFT_REDIRECT_URI = os.getenv('MICROSOFT_REDIRECT_URI', 'http://localhost:3000/api/auth/callback/microsoft')
MICROSOFT_OAUTH_AUTHORIZE_URL = os.getenv('MICROSOFT_OAUTH_AUTHORIZE_URL', 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize')
MICROSOFT_OAUTH_TOKEN_URL = os.getenv('MICROSOFT_OAUTH_TOKEN_URL', 'https://login.microsoftonline.com/common/oauth2/v2.0/token')

OKTA_DOMAIN = os.getenv('OKTA_DOMAIN', 'your-company.okta.com')
OKTA_CLIENT_ID = os.getenv('OKTA_CLIENT_ID', 'your-okta-client-id')
OKTA_CLIENT_SECRET = os.getenv('OKTA_CLIENT_SECRET', 'your-okta-client-secret')
OKTA_REDIRECT_URI = os.getenv('OKTA_REDIRECT_URI', 'http://localhost:3000/api/sso/okta/callback')

FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')


class DomainLookupRequest(BaseModel):
    """Request for SSO domain lookup"""
    email: EmailStr
    domain: str


@router.post("/lookup-domain")
async def lookup_sso_domain(request: DomainLookupRequest, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Smart SSO domain lookup.
    Given a work email, determines the SSO provider for that organization
    and returns the appropriate login URL.
    """
    domain = request.domain.lower()
    email = request.email.lower()
    
    # First, check if enterprise has configured SSO in database
    enterprise = await db_conn.enterprises.find_one(
        {"$or": [
            {"domain": domain},
            {"email_domains": domain}
        ]},
        {"_id": 0}
    )
    
    if enterprise:
        sso_config = enterprise.get("sso_config", {})
        provider = sso_config.get("provider")
        
        if provider == "microsoft" or provider == "azure-ad":
            tenant_id = sso_config.get("tenant_id", "common")
            return {
                "provider": "microsoft",
                "login_url": f"/api/sso/microsoft/login?email={email}&tenant={tenant_id}",
                "enterprise_name": enterprise.get("name")
            }
        elif provider == "okta":
            okta_domain = sso_config.get("okta_domain")
            return {
                "provider": "okta",
                "login_url": f"/api/sso/okta/login?email={email}&domain={okta_domain}",
                "enterprise_name": enterprise.get("name")
            }
        elif provider == "google-workspace":
            return {
                "provider": "google-workspace",
                "login_url": f"/api/sso/google-workspace/login?email={email}",
                "enterprise_name": enterprise.get("name")
            }
    
    # Domain not found in database - check for common enterprise domains
    # These are well-known domains that likely use specific SSO providers
    common_microsoft_domains = ['microsoft.com', 'outlook.com', 'hotmail.com']
    
    if domain in common_microsoft_domains or domain.endswith('.onmicrosoft.com'):
        return {
            "provider": "microsoft",
            "login_url": f"/api/sso/microsoft/login?email={email}",
            "enterprise_name": None
        }
    
    # If we can't determine the provider, return empty to let user know
    return {
        "provider": None,
        "login_url": None,
        "message": f"No SSO configuration found for {domain}. Please contact your IT administrator."
    }


class SSOUserInfo(BaseModel):
    """User information from SSO provider"""
    external_id: str  # ID from IdP
    email: EmailStr
    name: str
    manager_email: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None


async def get_or_create_sso_user(user_info: SSOUserInfo, provider: str, enterprise_id: str) -> Dict[str, Any]:
    """Get or create user from SSO authentication"""
    try:
        # Check if user exists by external_id
        user = await db_conn.users.find_one({
            "external_id": user_info.external_id,
            "sso_provider": provider
        }, {"_id": 0})
        
        if user:
            # Update last login
            await db_conn.users.update_one(
                {"id": user["id"]},
                {"$set": {"last_login": datetime.now(timezone.utc)}}
            )
            return user
        
        # Check if user exists by email (migration case)
        user = await db_conn.users.find_one({"email": user_info.email}, {"_id": 0})
        
        if user:
            # Link existing account with SSO
            await db_conn.users.update_one(
                {"id": user["id"]},
                {
                    "$set": {
                        "external_id": user_info.external_id,
                        "sso_provider": provider,
                        "last_login": datetime.now(timezone.utc)
                    }
                }
            )
            return user
        
        # Create new user
        user_id = str(uuid.uuid4())
        
        # Try to find manager by email if provided
        manager_id = None
        if user_info.manager_email:
            manager = await db_conn.users.find_one(
                {"email": user_info.manager_email},
                {"_id": 0, "id": 1}
            )
            if manager:
                manager_id = manager["id"]
        
        new_user = {
            "id": user_id,
            "external_id": user_info.external_id,
            "email": user_info.email,
            "full_name": user_info.name,
            "sso_provider": provider,
            "enterprise_id": enterprise_id,
            "manager_id": manager_id,
            "department": user_info.department,
            "job_title": user_info.job_title,
            "created_at": datetime.now(timezone.utc),
            "last_login": datetime.now(timezone.utc),
            "subscription_status": "active",  # Enterprise users are always active
            "email_verified": True  # SSO users are pre-verified
        }
        
        await db_conn.users.insert_one(new_user)
        
        # Assign default employee role
        await db_conn.user_roles.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "role": "employee",
            "created_at": datetime.now(timezone.utc)
        })
        
        return new_user
        
    except Exception as e:
        logger.error(f"Error creating SSO user: {str(e)}")
        raise HTTPException(500, "Failed to process SSO authentication")


# ==================== MICROSOFT ENTRA ID (AZURE AD) ====================

@router.get("/microsoft/login")
async def microsoft_sso_login(enterprise_id: str = ""):
    """Initiate Microsoft Entra ID SSO login"""
    
    config = get_microsoft_config()
    
    if not config['client_id']:
        raise HTTPException(500, "Microsoft SSO is not configured")
    
    # Build authorization URL using configured URL
    auth_url = config['authorize_url']
    
    params = {
        'client_id': config['client_id'],
        'response_type': 'code',
        'redirect_uri': config['redirect_uri'],
        'response_mode': 'query',
        'scope': 'openid profile email User.Read',
        'state': enterprise_id or 'login',  # Pass enterprise_id in state, or 'login' for regular login
    }
    
    authorization_url = f"{auth_url}?{urlencode(params)}"
    
    return RedirectResponse(authorization_url)


@router.get("/microsoft/callback")
async def microsoft_sso_callback(code: str, state: str):
    """Handle Microsoft Entra ID SSO callback"""
    from urllib.parse import quote
    
    config = get_microsoft_config()
    enterprise_id = state if state != 'login' else None
    frontend_url = get_frontend_url()
    
    def redirect_with_error(error_message: str):
        """Redirect to SSO success page with error message for better UX"""
        encoded_error = quote(error_message)
        return RedirectResponse(f"{frontend_url}/contentry/auth/sso-success?error={encoded_error}")
    
    try:
        # Exchange code for token using configured URL
        token_url = config['token_url']
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                token_url,
                data={
                    'client_id': config['client_id'],
                    'client_secret': config['client_secret'],
                    'code': code,
                    'redirect_uri': config['redirect_uri'],
                    'grant_type': 'authorization_code',
                }
            )
            
            if token_response.status_code != 200:
                logger.error(f"Microsoft token error: {token_response.text}")
                return redirect_with_error("Failed to authenticate with Microsoft. Please try again.")
            
            token_data = token_response.json()
            access_token = token_data['access_token']
            
            # Get user info from Microsoft Graph
            graph_response = await client.get(
                'https://graph.microsoft.com/v1.0/me',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if graph_response.status_code != 200:
                logger.error(f"Microsoft Graph error: {graph_response.text}")
                return redirect_with_error("Failed to retrieve your profile from Microsoft. Please try again.")
            
            user_data = graph_response.json()
            
            # Get manager info (optional)
            manager_email = None
            try:
                manager_response = await client.get(
                    'https://graph.microsoft.com/v1.0/me/manager',
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                if manager_response.status_code == 200:
                    manager_data = manager_response.json()
                    manager_email = manager_data.get('mail') or manager_data.get('userPrincipalName')
            except httpx.HTTPError as e:
                logger.debug(f"Manager info not available: {e}")  # Manager info is optional
            
            # Create SSO user info
            user_email = user_data.get('mail') or user_data.get('userPrincipalName')
            if not user_email:
                logger.error("Microsoft user has no email address")
                return redirect_with_error("Your Microsoft account doesn't have an email address configured. Please contact your IT administrator.")
            
            sso_user = SSOUserInfo(
                external_id=user_data['id'],
                email=user_email,
                name=user_data.get('displayName', ''),
                manager_email=manager_email,
                department=user_data.get('department'),
                job_title=user_data.get('jobTitle')
            )
            
            # Get or create user
            user = await get_or_create_sso_user(sso_user, 'microsoft', enterprise_id)
            
            # Redirect to frontend with user info
            redirect_url = f"{frontend_url}/contentry/auth/sso-success?user_id={user['id']}&email={user['email']}"
            return RedirectResponse(redirect_url)
            
    except HTTPException as he:
        logger.error(f"Microsoft SSO HTTP error: {str(he)}")
        return redirect_with_error(str(he.detail))
    except Exception as e:
        logger.error(f"Microsoft SSO callback error: {str(e)}")
        return redirect_with_error("An unexpected error occurred during authentication. Please try again.")


# ==================== OKTA ====================

@router.get("/okta/login")
async def okta_sso_login(enterprise_id: str):
    """Initiate Okta SSO login"""
    
    auth_url = f"https://{OKTA_DOMAIN}/oauth2/v1/authorize"
    
    params = {
        'client_id': OKTA_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': OKTA_REDIRECT_URI,
        'scope': 'openid profile email',
        'state': enterprise_id,
    }
    
    authorization_url = f"{auth_url}?{urlencode(params)}"
    
    return RedirectResponse(authorization_url)


@router.get("/okta/callback")
async def okta_sso_callback(code: str, state: str):
    """Handle Okta SSO callback"""
    
    enterprise_id = state
    
    try:
        # Exchange code for token
        token_url = f"https://{OKTA_DOMAIN}/oauth2/v1/token"
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                token_url,
                data={
                    'client_id': OKTA_CLIENT_ID,
                    'client_secret': OKTA_CLIENT_SECRET,
                    'code': code,
                    'redirect_uri': OKTA_REDIRECT_URI,
                    'grant_type': 'authorization_code',
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if token_response.status_code != 200:
                logger.error(f"Okta token error: {token_response.text}")
                raise HTTPException(400, "Failed to get access token")
            
            token_data = token_response.json()
            access_token = token_data['access_token']
            
            # Get user info from Okta
            userinfo_response = await client.get(
                f"https://{OKTA_DOMAIN}/oauth2/v1/userinfo",
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if userinfo_response.status_code != 200:
                logger.error(f"Okta userinfo error: {userinfo_response.text}")
                raise HTTPException(400, "Failed to get user info")
            
            user_data = userinfo_response.json()
            
            # Create SSO user info
            sso_user = SSOUserInfo(
                external_id=user_data['sub'],
                email=user_data['email'],
                name=user_data.get('name', user_data.get('preferred_username', '')),
                department=user_data.get('department'),
                job_title=user_data.get('title')
            )
            
            # Get or create user
            user = await get_or_create_sso_user(sso_user, 'okta', enterprise_id)
            
            # Redirect to frontend with user info
            frontend_url = get_frontend_url()
            redirect_url = f"{frontend_url}/contentry/auth/sso-success?user_id={user['id']}&email={user['email']}"
            return RedirectResponse(redirect_url)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Okta SSO callback error: {str(e)}")
        raise HTTPException(500, "SSO authentication failed")


@router.get("/providers")
async def get_sso_providers():
    """Get list of configured SSO providers"""
    providers = []
    
    ms_config = get_microsoft_config()
    okta_config = get_okta_config()
    
    if ms_config['client_id'] and ms_config['client_id'] != 'your-microsoft-client-id':
        providers.append({
            'name': 'Microsoft',
            'id': 'microsoft',
            'login_url': '/api/sso/microsoft/login'
        })
    
    if okta_config['client_id'] and okta_config['client_id'] != 'your-okta-client-id':
        providers.append({
            'name': 'Okta',
            'id': 'okta',
            'login_url': '/api/sso/okta/login'
        })
    
    return {"providers": providers}


# ==================== AUTH CALLBACK ROUTER ====================
# This router handles OAuth callbacks at /api/auth/callback/*
# to match common OAuth redirect URI patterns

auth_callback_router = APIRouter(prefix="/auth/callback", tags=["Auth Callbacks"])

@auth_callback_router.get("/microsoft")
async def microsoft_auth_callback(code: str, state: str = "login"):
    """Handle Microsoft OAuth callback at /api/auth/callback/microsoft"""
    return await microsoft_sso_callback(code, state)
