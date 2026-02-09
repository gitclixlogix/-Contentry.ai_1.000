"""
Authentication Security Routes
Endpoints for JWT tokens, MFA, rate limiting, and password security

RBAC Protected: Phase 5.1c Week 8
Auth-related endpoints - some protected, some public for auth flows
"""

from fastapi import APIRouter, HTTPException, Header, Request, Depends, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import Optional
import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db
# RBAC decorator
from services.authorization_decorator import require_permission

from services.auth_security import (
    JWTTokenManager,
    JWTBearer,
    get_account_security,
    get_mfa_manager,
    get_password_manager,
    get_jwt_manager,
    init_security_services,
    MAX_LOGIN_ATTEMPTS
)

router = APIRouter(prefix="/auth/security", tags=["auth-security"])
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

db = None


# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    global db
    db = database
    init_security_services(database)


# ============================================
# JWT Token Endpoints
# ============================================

@router.post("/token/refresh")
async def refresh_access_token(data: dict):
    """
    Refresh access token using refresh token
    
    Body: {"refresh_token": "..."}
    """
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(400, "Refresh token is required")
    
    try:
        # Verify refresh token
        payload = JWTTokenManager.verify_refresh_token(refresh_token)
        
        # Create new access token
        new_access_token = JWTTokenManager.create_access_token({
            "sub": payload["sub"],
            "email": payload["email"],
            "role": payload.get("role", "user")
        })
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(500, "Failed to refresh token")


@router.post("/token/verify")
async def verify_token(data: dict):
    """
    Verify if an access token is valid
    
    Body: {"access_token": "..."}
    """
    access_token = data.get("access_token")
    if not access_token:
        raise HTTPException(400, "Access token is required")
    
    try:
        payload = JWTTokenManager.verify_access_token(access_token)
        return {
            "valid": True,
            "user_id": payload["sub"],
            "email": payload["email"],
            "role": payload.get("role"),
            "expires_at": datetime.fromtimestamp(payload["exp"], tz=timezone.utc).isoformat()
        }
    except HTTPException as e:
        return {
            "valid": False,
            "error": e.detail
        }


@router.post("/token/revoke")
@require_permission("settings.view")
async def revoke_token(
    request: Request,
    data: dict,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """
    Revoke/invalidate tokens (logout)
    
    Note: For true token revocation, implement a token blacklist
    """
    # In a production system, you'd add the token to a blacklist
    # For now, we just acknowledge the request
    return {
        "message": "Token revoked successfully",
        "note": "Please discard the tokens on client side"
    }


# ============================================
# MFA Endpoints
# ============================================

@router.post("/mfa/setup")
@require_permission("settings.edit_integrations")
async def setup_mfa(request: Request, x_user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Initialize MFA setup - returns QR code and backup codes
    """
    try:
        mfa_manager = get_mfa_manager()
        
        # Get user email
        user = await db_conn.users.find_one({"id": x_user_id}, {"_id": 0, "email": 1, "mfa_enabled": 1})
        if not user:
            raise HTTPException(404, "User not found")
        
        if user.get("mfa_enabled"):
            raise HTTPException(400, "MFA is already enabled. Disable it first to reconfigure.")
        
        result = await mfa_manager.setup_mfa(x_user_id, user["email"])
        
        return {
            "success": True,
            "qr_code": result["qr_code"],
            "secret": result["secret"],
            "backup_codes": result["backup_codes"],
            "message": "Scan the QR code with your authenticator app, then call /mfa/verify to complete setup"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA setup error: {str(e)}")
        raise HTTPException(500, "Failed to setup MFA")


@router.post("/mfa/verify-setup")
@require_permission("settings.edit_integrations")
async def verify_mfa_setup(
    request: Request,
    data: dict,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """
    Complete MFA setup by verifying a TOTP code
    
    Body: {"code": "123456"}
    """
    code = data.get("code")
    if not code:
        raise HTTPException(400, "Verification code is required")
    
    try:
        mfa_manager = get_mfa_manager()
        
        if await mfa_manager.verify_and_enable_mfa(x_user_id, code):
            return {
                "success": True,
                "message": "MFA enabled successfully"
            }
        else:
            raise HTTPException(400, "Invalid verification code")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA verify setup error: {str(e)}")
        raise HTTPException(500, "Failed to verify MFA setup")


@router.post("/mfa/verify")
async def verify_mfa_code(data: dict, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Verify MFA code during login
    
    Body: {"user_id": "...", "code": "123456"}
    """
    user_id = data.get("user_id")
    code = data.get("code")
    
    if not user_id or not code:
        raise HTTPException(400, "User ID and code are required")
    
    try:
        mfa_manager = get_mfa_manager()
        
        if await mfa_manager.verify_mfa_code(user_id, code):
            # Generate tokens after successful MFA
            user = await db_conn.users.find_one({"id": user_id}, {"_id": 0, "email": 1, "role": 1})
            tokens = JWTTokenManager.create_token_pair(
                user_id, 
                user["email"], 
                user.get("role", "user")
            )
            
            # Record successful login with MFA
            account_security = get_account_security()
            await account_security.record_successful_login(user_id, "MFA-verified")
            
            return {
                "success": True,
                "message": "MFA verification successful",
                **tokens
            }
        else:
            raise HTTPException(401, "Invalid MFA code")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA verify error: {str(e)}")
        raise HTTPException(500, "Failed to verify MFA code")


@router.post("/mfa/disable")
@require_permission("settings.edit_integrations")
async def disable_mfa(
    request: Request,
    data: dict,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """
    Disable MFA after verification
    
    Body: {"code": "123456"}
    """
    code = data.get("code")
    if not code:
        raise HTTPException(400, "Verification code is required")
    
    try:
        mfa_manager = get_mfa_manager()
        
        if await mfa_manager.disable_mfa(x_user_id, code):
            return {
                "success": True,
                "message": "MFA disabled successfully"
            }
        else:
            raise HTTPException(400, "Invalid verification code")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA disable error: {str(e)}")
        raise HTTPException(500, "Failed to disable MFA")


@router.post("/mfa/backup-codes/regenerate")
@require_permission("settings.edit_integrations")
async def regenerate_backup_codes(
    request: Request,
    data: dict,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """
    Regenerate backup codes after verification
    
    Body: {"code": "123456"}
    """
    code = data.get("code")
    if not code:
        raise HTTPException(400, "Verification code is required")
    
    try:
        mfa_manager = get_mfa_manager()
        new_codes = await mfa_manager.regenerate_backup_codes(x_user_id, code)
        
        if new_codes:
            return {
                "success": True,
                "backup_codes": new_codes,
                "message": "New backup codes generated. Save these securely - they won't be shown again!"
            }
        else:
            raise HTTPException(400, "Invalid verification code")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backup codes regenerate error: {str(e)}")
        raise HTTPException(500, "Failed to regenerate backup codes")


@router.get("/mfa/status")
@require_permission("settings.view")
async def get_mfa_status(request: Request, x_user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Get MFA status for current user"""
    try:
        user = await db_conn.users.find_one(
            {"id": x_user_id},
            {"_id": 0, "mfa_enabled": 1, "mfa_enabled_at": 1, "mfa_backup_codes": 1}
        )
        
        if not user:
            raise HTTPException(404, "User not found")
        
        backup_codes_remaining = len(user.get("mfa_backup_codes", [])) if user.get("mfa_enabled") else 0
        
        return {
            "mfa_enabled": user.get("mfa_enabled", False),
            "enabled_at": user.get("mfa_enabled_at"),
            "backup_codes_remaining": backup_codes_remaining
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA status error: {str(e)}")
        raise HTTPException(500, "Failed to get MFA status")


# ============================================
# Password Security Endpoints
# ============================================

@router.post("/password/validate")
async def validate_password_strength(data: dict):
    """
    Validate password strength without saving
    
    Body: {"password": "..."}
    """
    from services.auth_security import PasswordSecurityManager
    
    password = data.get("password")
    if not password:
        raise HTTPException(400, "Password is required")
    
    return PasswordSecurityManager.validate_password_strength(password)


@router.post("/password/change")
@require_permission("settings.view")
async def change_password(
    request: Request,
    data: dict,
    x_user_id: str = Header(..., alias="X-User-ID")
,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Change password for authenticated user
    
    Body: {"current_password": "...", "new_password": "..."}
    """
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    
    if not current_password or not new_password:
        raise HTTPException(400, "Current and new passwords are required")
    
    try:
        # Verify current password
        user = await db_conn.users.find_one({"id": x_user_id}, {"_id": 0, "password_hash": 1})
        if not user or not pwd_context.verify(current_password, user["password_hash"]):
            raise HTTPException(401, "Current password is incorrect")
        
        # Update password
        password_manager = get_password_manager()
        result = await password_manager.update_password(x_user_id, new_password)
        
        if not result["success"]:
            raise HTTPException(400, result["errors"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        raise HTTPException(500, "Failed to change password")


@router.post("/password/reset/request")
@limiter.limit("3/minute")
async def request_password_reset(request: Request, data: dict):
    """
    Request a password reset email
    
    Body: {"email": "..."}
    """
    email = data.get("email")
    if not email:
        raise HTTPException(400, "Email is required")
    
    try:
        password_manager = get_password_manager()
        token = await password_manager.create_password_reset(email)
        
        # Always return success to prevent email enumeration
        # In production, send the email with the token
        if token:
            # TODO: Send email with reset link containing token
            logger.info(f"Password reset requested for {email}")
            # For development, return the token (remove in production!)
            return {
                "message": "If an account exists with this email, a reset link has been sent",
                "dev_token": token  # REMOVE IN PRODUCTION
            }
        
        return {
            "message": "If an account exists with this email, a reset link has been sent"
        }
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        return {
            "message": "If an account exists with this email, a reset link has been sent"
        }


@router.post("/password/reset/verify")
async def verify_reset_token(data: dict):
    """
    Verify a password reset token is valid
    
    Body: {"token": "..."}
    """
    token = data.get("token")
    if not token:
        raise HTTPException(400, "Token is required")
    
    try:
        password_manager = get_password_manager()
        user_id = await password_manager.verify_reset_token(token)
        
        if user_id:
            return {"valid": True}
        else:
            return {"valid": False, "error": "Invalid or expired token"}
    except Exception as e:
        logger.error(f"Reset token verify error: {str(e)}")
        return {"valid": False, "error": "Verification failed"}


@router.post("/password/reset/complete")
async def complete_password_reset(data: dict):
    """
    Complete password reset with token
    
    Body: {"token": "...", "new_password": "..."}
    """
    token = data.get("token")
    new_password = data.get("new_password")
    
    if not token or not new_password:
        raise HTTPException(400, "Token and new password are required")
    
    try:
        password_manager = get_password_manager()
        result = await password_manager.complete_password_reset(token, new_password)
        
        if not result["success"]:
            raise HTTPException(400, result.get("error") or result.get("errors"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset complete error: {str(e)}")
        raise HTTPException(500, "Failed to complete password reset")


@router.get("/password/expiry")
@require_permission("settings.view")
async def check_password_expiry(request: Request, x_user_id: str = Header(..., alias="X-User-ID")):
    """Check if user's password has expired or is expiring soon"""
    try:
        password_manager = get_password_manager()
        return await password_manager.check_password_expiry(x_user_id)
    except Exception as e:
        logger.error(f"Password expiry check error: {str(e)}")
        raise HTTPException(500, "Failed to check password expiry")


# ============================================
# Account Security Endpoints
# ============================================

@router.get("/account/status")
@require_permission("settings.view")
async def get_account_security_status(request: Request, x_user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Get comprehensive security status for account"""
    try:
        account_security = get_account_security()
        password_manager = get_password_manager()
        
        # Get user data
        user = await db_conn.users.find_one(
            {"id": x_user_id},
            {
                "_id": 0,
                "failed_login_attempts": 1,
                "account_locked_until": 1,
                "last_login": 1,
                "last_login_ip": 1,
                "mfa_enabled": 1
            }
        )
        
        if not user:
            raise HTTPException(404, "User not found")
        
        # Check lock status
        is_locked, locked_until = await account_security.check_account_locked(x_user_id)
        
        # Check password expiry
        password_status = await password_manager.check_password_expiry(x_user_id)
        
        return {
            "account_locked": is_locked,
            "locked_until": locked_until.isoformat() if locked_until else None,
            "failed_login_attempts": user.get("failed_login_attempts", 0),
            "max_login_attempts": MAX_LOGIN_ATTEMPTS,
            "last_login": user.get("last_login"),
            "last_login_ip": user.get("last_login_ip"),
            "mfa_enabled": user.get("mfa_enabled", False),
            "password_status": password_status
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Account status error: {str(e)}")
        raise HTTPException(500, "Failed to get account status")


@router.get("/account/login-history")
@require_permission("settings.view")
async def get_login_history(
    request: Request,
    x_user_id: str = Header(..., alias="X-User-ID"),
    limit: int = 20
):
    """Get recent login history"""
    try:
        account_security = get_account_security()
        history = await account_security.get_login_history(x_user_id, limit)
        
        return {
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Login history error: {str(e)}")
        raise HTTPException(500, "Failed to get login history")


@router.post("/account/unlock")
@require_permission("admin.manage")
async def admin_unlock_account(
    request: Request,
    data: dict,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Admin endpoint to unlock a locked account"""
    target_user_id = data.get("user_id")
    if not target_user_id:
        raise HTTPException(400, "User ID is required")
    
    try:
        # Check if requester is admin
        requester = await db_conn.users.find_one({"id": x_user_id}, {"_id": 0, "role": 1})
        if not requester or requester.get("role") not in ["admin", "enterprise_admin"]:
            raise HTTPException(403, "Admin access required")
        
        account_security = get_account_security()
        await account_security.reset_login_attempts(target_user_id)
        
        return {
            "success": True,
            "message": f"Account {target_user_id} unlocked successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Account unlock error: {str(e)}")
        raise HTTPException(500, "Failed to unlock account")


# Export limiter for use in main app
def get_limiter():
    return limiter
