"""
Authentication routes
Handles user signup, login, email verification, and password reset

Migration Status: PHASE 2 - Using Depends(get_db) dependency injection pattern

Security Update (ARCH-022): JWT tokens now stored in HttpOnly cookies
- Prevents XSS attacks from stealing tokens
- Cookies automatically sent with requests
- Secure flag ensures HTTPS-only transmission

RBAC Protected: Phase 5.1c Week 8
Some endpoints are public (login, signup), others require authentication
"""
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Request, Header, Depends, Response
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
import logging
import os
import shutil
from datetime import datetime, timezone, timedelta
from models.schemas import User, UserSignup, UserLogin, Subscription
from email_service import send_verification_email
from security_utils import secure_compare

# Import database dependency injection
from services.database import get_db
# RBAC decorator
from services.authorization_decorator import require_permission


# =============================================================================
# HTTPONLY COOKIE CONFIGURATION (ARCH-022)
# =============================================================================
# Security settings for JWT cookie storage
COOKIE_NAME = "access_token"
COOKIE_MAX_AGE = 86400  # 24 hours in seconds
COOKIE_PATH = "/"
# In production, should be True (requires HTTPS)
COOKIE_SECURE = os.environ.get("ENVIRONMENT", "development").lower() == "production"
# Strict prevents CSRF in most cases; Lax allows GET navigations
COOKIE_SAMESITE = "lax"  # Use "strict" for maximum security, "lax" for usability


def set_auth_cookies(response: Response, access_token: str, refresh_token: str = None):
    """
    Set HttpOnly authentication cookies on the response.
    
    Security features (ARCH-022):
    - HttpOnly: Prevents JavaScript access (XSS protection)
    - Secure: Only sent over HTTPS (in production)
    - SameSite: Prevents CSRF attacks
    
    Args:
        response: FastAPI Response object
        access_token: JWT access token
        refresh_token: Optional refresh token
    """
    # Set access token cookie
    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        httponly=True,  # Cannot be accessed by JavaScript
        secure=COOKIE_SECURE,  # HTTPS only in production
        samesite=COOKIE_SAMESITE,
        max_age=COOKIE_MAX_AGE,
        path=COOKIE_PATH,
    )
    
    # Set refresh token cookie (longer lived)
    if refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,
            max_age=COOKIE_MAX_AGE * 7,  # 7 days
            path=COOKIE_PATH,
        )


def clear_auth_cookies(response: Response):
    """
    Clear all authentication cookies on logout.
    
    Args:
        response: FastAPI Response object
    """
    response.delete_cookie(key=COOKIE_NAME, path=COOKIE_PATH)
    response.delete_cookie(key="refresh_token", path=COOKIE_PATH)
    response.delete_cookie(key="session_token", path=COOKIE_PATH)


def get_token_from_request(request: Request) -> str:
    """
    Extract JWT token from request.
    
    Priority order:
    1. HttpOnly cookie (most secure, preferred)
    2. Authorization header (for API clients/mobile apps)
    
    Args:
        request: FastAPI Request object
        
    Returns:
        JWT token string or None
    """
    # Try cookie first (most secure)
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token
    
    # Fall back to Authorization header for API clients
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "")
    
    return None

# Import security constants
MAX_LOGIN_ATTEMPTS = 5  # Default fallback

# Create router
router = APIRouter(prefix="/auth", tags=["auth"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =============================================================================
# BACKWARD COMPATIBILITY LAYER (DEPRECATED)
# =============================================================================
# The following global db and set_db() pattern is deprecated.
# It remains for backward compatibility during migration.
# New code should use: db: AsyncIOMotorDatabase = Depends(get_db)

db = None


def set_db(database):
    """
    DEPRECATED: Set the database instance for this router.
    
    This function is kept for backward compatibility during the migration
    to dependency injection. New endpoints should use Depends(get_db).
    """
    global db
    db = database

# =============================================================================


def validate_password_strength(password: str) -> dict:
    """
    Validate password strength requirements.
    Returns dict with 'valid' boolean and 'errors' list.
    Requirements: 8+ chars, 1 uppercase, 1 lowercase, 1 number, 1 symbol
    """
    import re
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', password):
        errors.append("Password must contain at least one special character (!@#$%^&*...)")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "requirements": {
            "min_length": len(password) >= 8,
            "has_uppercase": bool(re.search(r'[A-Z]', password)),
            "has_lowercase": bool(re.search(r'[a-z]', password)),
            "has_number": bool(re.search(r'\d', password)),
            "has_symbol": bool(re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', password))
        }
    }


@router.post("/signup")
async def signup(user_data: UserSignup, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Register a new user"""
    # Validate password strength
    password_check = validate_password_strength(user_data.password)
    if not password_check["valid"]:
        raise HTTPException(400, detail={
            "message": "Password does not meet security requirements",
            "errors": password_check["errors"],
            "requirements": password_check["requirements"]
        })
    
    # Check if user exists
    existing = await db_conn.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(400, "User already exists")
    
    # Hash password
    password_hash = pwd_context.hash(user_data.password)
    
    # Check if email domain belongs to an enterprise
    enterprise_id = None
    enterprise_role = None
    email_verified = False
    verification_token = None
    
    if "@" in user_data.email:
        domain = user_data.email.split("@")[1].lower()
        enterprise = await db_conn.enterprises.find_one(
            {"domains": domain, "is_active": True},
            {"_id": 0}
        )
        
        if enterprise:
            enterprise_id = enterprise["id"]
            enterprise_role = "enterprise_user"
            # Enterprise users need email verification
            verification_token = str(uuid.uuid4())
            email_verified = False
    
    # Create user
    # Enterprise users skip onboarding wizard
    skip_onboarding = enterprise_id is not None
    
    user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        phone=user_data.phone,
        password_hash=password_hash,
        dob=user_data.dob,
        enterprise_id=enterprise_id,
        enterprise_role=enterprise_role,
        email_verified=email_verified,
        verification_token=verification_token,
        has_completed_onboarding=skip_onboarding
    )
    
    user_dict = user.model_dump()
    await db_conn.users.insert_one(user_dict)
    
    # Create free subscription
    subscription = Subscription(
        user_id=user.id,
        plan="free",
        price=0.0,
        credits=100000
    )
    await db_conn.subscriptions.insert_one(subscription.model_dump())
    
    # Send verification email if enterprise user
    if enterprise_id and verification_token:
        try:
            await send_verification_email(
                email=user.email,
                verification_token=verification_token,
                user_name=user.full_name
            )
            logging.info(f"Verification email sent to {user.email}")
        except Exception as e:
            logging.error(f"Failed to send verification email: {str(e)}")
    
    response = {"message": "User created successfully", "user_id": user.id}
    
    # Add enterprise info if applicable
    if enterprise_id:
        response["enterprise"] = {
            "id": enterprise_id,
            "name": enterprise.get("name"),
            "requires_verification": True
        }
        response["message"] = "User created. Please check your email to verify your account and access enterprise features."
    
    return response


@router.post("/check-password-strength")
async def check_password_strength(data: dict):
    """
    Check password strength without creating an account.
    Used for real-time frontend validation.
    """
    password = data.get("password", "")
    result = validate_password_strength(password)
    return result


@router.post("/login")
async def login(credentials: UserLogin, request: Request = None, response: Response = None, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Login user and return user info with JWT tokens.
    
    Security (ARCH-022): JWT tokens are now set as HttpOnly cookies
    - access_token: HttpOnly cookie (24h expiry)
    - refresh_token: HttpOnly cookie (7 day expiry)
    - Tokens still returned in response body for backward compatibility
    """
    from services.auth_security import (
        JWTTokenManager, 
        get_account_security, 
        get_password_manager
    )
    
    logging.info(f"Login attempt for email: {credentials.email}")
    
    # Get client IP
    client_ip = "unknown"
    if request:
        client_ip = request.client.host if request.client else "unknown"
    
    # Find user
    user = await db_conn.users.find_one({"email": credentials.email})
    if not user:
        logging.info(f"User not found: {credentials.email}")
        raise HTTPException(401, "Invalid credentials")
    
    logging.info(f"User found: {user.get('id')}")
    
    # Check if user has password_hash (some legacy users might not)
    if not user.get("password_hash"):
        logging.warning(f"User {user.get('id')} has no password_hash")
        raise HTTPException(401, "Invalid credentials")
    
    logging.info("User has password_hash")
    
    user_id = user["id"]
    
    # Check if account is locked
    try:
        account_security = get_account_security()
        is_locked, locked_until = await account_security.check_account_locked(user_id)
        
        if is_locked:
            raise HTTPException(
                status_code=423,
                detail={
                    "error": "Account locked",
                    "message": "Too many failed login attempts. Please try again later.",
                    "locked_until": locked_until.isoformat() if locked_until else None
                }
            )
    except RuntimeError:
        # Security services not initialized - skip check
        account_security = None
    
    # Verify password
    try:
        password_valid = pwd_context.verify(credentials.password, user["password_hash"])
        logging.info(f"Password verification result for {credentials.email}: {password_valid}")
    except Exception as e:
        logging.error(f"Password verification error: {str(e)}")
        password_valid = False
    
    if not password_valid:
        # Record failed login
        if account_security:
            attempt_result = await account_security.record_failed_login(user_id, client_ip)
            remaining = MAX_LOGIN_ATTEMPTS - attempt_result["attempts"]
            
            if attempt_result["locked"]:
                raise HTTPException(
                    status_code=423,
                    detail={
                        "error": "Account locked",
                        "message": "Too many failed login attempts. Account has been locked.",
                        "locked_until": attempt_result["locked_until"]
                    }
                )
            
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Invalid credentials",
                    "attempts_remaining": remaining
                }
            )
        raise HTTPException(401, "Invalid credentials")
    
    # Check if MFA is enabled
    mfa_enabled = user.get("mfa_enabled", False)
    
    if mfa_enabled:
        # Return MFA required response - user needs to verify with /auth/security/mfa/verify
        return {
            "success": False,
            "mfa_required": True,
            "user_id": user_id,
            "message": "MFA verification required. Please provide your authenticator code."
        }
    
    # Record successful login
    if account_security:
        await account_security.record_successful_login(user_id, client_ip)
    
    # Check password expiry
    password_warning = None
    try:
        password_manager = get_password_manager()
        password_status = await password_manager.check_password_expiry(user_id)
        if password_status.get("expired"):
            return {
                "success": False,
                "password_expired": True,
                "user_id": user_id,
                "message": "Your password has expired. Please reset it."
            }
        if password_status.get("warning"):
            password_warning = password_status.get("message")
    except RuntimeError:
        pass
    
    # Check if user must change temporary password (new team members)
    if user.get("must_change_password"):
        return {
            "success": False,
            "must_change_password": True,
            "user_id": user_id,
            "email": user["email"],
            "full_name": user.get("full_name", ""),
            "message": "You must change your temporary password before continuing."
        }
    
    # Generate JWT tokens
    access_token = None
    refresh_token = None
    tokens = {}
    try:
        tokens = JWTTokenManager.create_token_pair(
            user_id=user_id,
            email=user["email"],
            role=user.get("role", "user")
        )
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
    except Exception as e:
        logging.error(f"Token generation error: {str(e)}")
    
    # Fetch enterprise name from enterprises collection if user has enterprise_id
    enterprise_name = user.get("enterprise_name")
    enterprise_id = user.get("enterprise_id")
    enterprise_role = user.get("enterprise_role")
    
    if enterprise_id and not enterprise_name:
        # Look up enterprise name from enterprises collection
        enterprise = await db_conn.enterprises.find_one(
            {"id": enterprise_id},
            {"_id": 0, "name": 1}
        )
        if enterprise:
            enterprise_name = enterprise.get("name")
            logging.info(f"Fetched enterprise_name '{enterprise_name}' for user {user_id}")
    
    # Determine if user is enterprise admin
    # Check both enterprise_role values: 'admin' and 'enterprise_admin'
    is_enterprise_admin = enterprise_role in ["admin", "enterprise_admin"] if enterprise_role else False
    
    # Build response data
    response_data = {
        "success": True,
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "phone": user.get("phone"),
            "role": user.get("role", "user"),
            "subscription_status": user.get("subscription_status", "active"),
            "subscription_plan": user.get("subscription_plan"),
            "profile_picture": user.get("profile_picture"),
            "company_name": user.get("company_name"),
            "job_title": user.get("job_title"),
            "country": user.get("country"),
            "default_tone": user.get("default_tone", "professional"),
            "default_homepage": user.get("default_homepage"),
            "enterprise_id": enterprise_id,
            "enterprise_name": enterprise_name,
            "enterprise_role": enterprise_role,
            "is_enterprise_admin": is_enterprise_admin,
            "mfa_enabled": mfa_enabled,
            "last_login": user.get("last_login")
        },
        # Include tokens in response body for backward compatibility
        # Frontend should migrate to using HttpOnly cookies
        **tokens
    }
    
    if password_warning:
        response_data["password_warning"] = password_warning
    
    # Create JSON response with HttpOnly cookies (ARCH-022)
    json_response = JSONResponse(content=response_data)
    
    # Set HttpOnly cookies for JWT tokens
    if access_token:
        set_auth_cookies(json_response, access_token, refresh_token)
        logging.info(f"HttpOnly cookies set for user {user_id}")
    
    return json_response


# Phone Login Models
class PhoneLoginRequest(BaseModel):
    phone: str
    password: str

class PhoneSendOTPRequest(BaseModel):
    phone: str

class PhoneVerifyOTPRequest(BaseModel):
    phone: str
    otp: str


@router.post("/phone/send-otp")
async def send_phone_otp(data: PhoneSendOTPRequest, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Send OTP to phone number for login"""
    try:
        import secrets
        
        # Check if user exists with this phone number
        user = await db_conn.users.find_one({"phone": data.phone})
        if not user:
            raise HTTPException(404, "User not found with this phone number")
        
        # Generate 6-digit OTP using cryptographically secure random
        otp = str(secrets.randbelow(900000) + 100000)
        
        # SECURITY: Hash OTP before storing in database
        # Using bcrypt to hash OTP for secure storage
        otp_hash = pwd_context.hash(otp)
        
        # Store hashed OTP in database with expiration (10 minutes as per security requirements)
        otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        await db_conn.phone_otps.update_one(
            {"phone": data.phone},
            {
                "$set": {
                    "otp_hash": otp_hash,  # Store hash, not plain OTP
                    "expiry": otp_expiry,
                    "created_at": datetime.now(timezone.utc),
                    "attempts": 0  # Track verification attempts
                }
            },
            upsert=True
        )
        
        # SECURITY: Send OTP via email only - NEVER log or return in API response
        # OTP is sent to user's registered email, not exposed in logs or response
        try:
            from email_service import send_otp_email
            await send_otp_email(
                email=user.get("email"),
                otp_code=otp,
                user_name=user.get("full_name", "User"),
                phone=data.phone
            )
            logging.info(f"OTP email sent for phone authentication (phone: {data.phone[-4:]})")  # Log only last 4 digits
        except Exception as email_error:
            logging.error(f"Failed to send OTP email: {str(email_error)}")
            # Clean up the OTP record if email fails
            await db_conn.phone_otps.delete_one({"phone": data.phone})
            raise HTTPException(500, "Failed to send OTP. Please try again.")
        
        # SECURITY: Return success message only - NEVER include OTP in response
        return {
            "success": True,
            "message": "OTP sent to your registered email address. Please check your inbox.",
            "expires_in_minutes": 10
        }
        # NOTE: OTP is intentionally NOT logged or returned in response for security
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error sending OTP: {str(e)}")
        raise HTTPException(500, "Failed to send OTP")


@router.post("/phone/verify-otp")
async def verify_phone_otp(data: PhoneVerifyOTPRequest, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Verify OTP and login user"""
    try:
        # Get OTP record
        otp_record = await db_conn.phone_otps.find_one({"phone": data.phone})
        if not otp_record:
            raise HTTPException(404, "OTP not found. Please request a new OTP.")
        
        # Check verification attempts (prevent brute force)
        attempts = otp_record.get("attempts", 0)
        if attempts >= 3:
            await db_conn.phone_otps.delete_one({"phone": data.phone})
            raise HTTPException(429, "Too many failed attempts. Please request a new OTP.")
        
        # Check if OTP expired
        expiry = otp_record["expiry"]
        # Ensure expiry has timezone info
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        
        if datetime.now(timezone.utc) > expiry:
            await db_conn.phone_otps.delete_one({"phone": data.phone})
            raise HTTPException(400, "OTP expired. Please request a new OTP.")
        
        # SECURITY: Verify OTP using bcrypt hash comparison
        # OTP is stored as hash, so we verify against the hash
        otp_hash = otp_record.get("otp_hash")
        if not otp_hash:
            # Legacy fallback for old records (temporary - will be removed)
            if not secure_compare(otp_record.get("otp", ""), data.otp):
                await db_conn.phone_otps.update_one(
                    {"phone": data.phone},
                    {"$inc": {"attempts": 1}}
                )
                raise HTTPException(401, "Invalid OTP")
        else:
            # Secure hash verification
            if not pwd_context.verify(data.otp, otp_hash):
                await db_conn.phone_otps.update_one(
                    {"phone": data.phone},
                    {"$inc": {"attempts": 1}}
                )
                raise HTTPException(401, "Invalid OTP")
        
        # Delete used OTP (one-time use)
        await db_conn.phone_otps.delete_one({"phone": data.phone})
        
        # Get user
        user = await db_conn.users.find_one({"phone": data.phone}, {"_id": 0})
        if not user:
            raise HTTPException(404, "User not found")
        
        return {
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "full_name": user["full_name"],
                "email": user.get("email"),
                "phone": user["phone"],
                "role": user.get("role", "user"),
                "subscription_status": user.get("subscription_status", "active"),
                "subscription_plan": user.get("subscription_plan"),
                "profile_picture": user.get("profile_picture"),
                "company_name": user.get("company_name"),
                "job_title": user.get("job_title"),
                "country": user.get("country"),
                "default_tone": user.get("default_tone", "professional"),
                "default_homepage": user.get("default_homepage"),
                "enterprise_id": user.get("enterprise_id"),
                "enterprise_role": user.get("enterprise_role"),
                "is_enterprise_admin": user.get("enterprise_role") == "admin"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error verifying OTP: {str(e)}")
        raise HTTPException(500, "Failed to verify OTP")


@router.post("/phone/login")
async def phone_login(credentials: PhoneLoginRequest, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Login with phone number and password"""
    try:
        user = await db_conn.users.find_one({"phone": credentials.phone})
        if not user or not pwd_context.verify(credentials.password, user["password_hash"]):
            raise HTTPException(401, "Invalid credentials")
        
        return {
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "full_name": user["full_name"],
                "email": user.get("email"),
                "phone": user["phone"],
                "role": user.get("role", "user"),
                "subscription_status": user.get("subscription_status", "active"),
                "subscription_plan": user.get("subscription_plan"),
                "profile_picture": user.get("profile_picture"),
                "company_name": user.get("company_name"),
                "job_title": user.get("job_title"),
                "country": user.get("country"),
                "default_tone": user.get("default_tone", "professional"),
                "default_homepage": user.get("default_homepage"),
                "enterprise_id": user.get("enterprise_id"),
                "enterprise_role": user.get("enterprise_role"),
                "is_enterprise_admin": user.get("enterprise_role") == "admin"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Phone login error: {str(e)}")
        raise HTTPException(500, "Login failed")


# Password Reset Models
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ValidateResetTokenRequest(BaseModel):
    token: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Send password reset email
    """
    try:
        # Find user by email
        user = await db_conn.users.find_one({"email": request.email}, {"_id": 0})
        
        # Always return success (don't reveal if email exists)
        if not user:
            return {"success": True, "message": "If the email exists, a reset link has been sent"}
        
        # Only allow password reset for non-OAuth users
        if user.get("oauth_provider"):
            raise HTTPException(400, "OAuth users cannot reset password. Please use your OAuth provider to sign in.")
        
        # Generate reset token
        reset_token = str(uuid.uuid4())
        reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Store reset token
        await db_conn.users.update_one(
            {"id": user["id"]},
            {"$set": {
                "password_reset_token": reset_token,
                "password_reset_expires": reset_expires.isoformat()
            }}
        )
        
        # SECURITY: Send password reset email - NEVER log the token
        # The reset token is sent only via email, never exposed in logs or API response
        try:
            from email_service import send_password_reset_email
            email_sent = await send_password_reset_email(
                email=user["email"],
                reset_token=reset_token,
                user_name=user.get("full_name", "User")
            )
            if email_sent:
                logging.info("Password reset email sent to user (email masked)")  # Don't log email
            else:
                logging.warning("Password reset email delivery may have failed")
        except Exception as email_error:
            logging.error(f"Failed to send password reset email: {str(email_error)}")
            # Don't fail the request - token is still valid
        
        # NOTE: Reset token is intentionally NOT logged for security
        # Token is sent only via email to the verified email address
        
        return {"success": True, "message": "If the email exists, a password reset link has been sent to your email address."}
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in forgot password: {str(e)}")
        return {"success": True, "message": "If the email exists, a reset link has been sent"}


@router.post("/validate-reset-token")
async def validate_reset_token(request: ValidateResetTokenRequest, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Validate if reset token is valid and not expired
    """
    try:
        user = await db_conn.users.find_one(
            {"password_reset_token": request.token},
            {"_id": 0}
        )
        
        if not user:
            raise HTTPException(400, "Invalid reset token")
        
        # Check expiry
        if "password_reset_expires" in user:
            expires = datetime.fromisoformat(user["password_reset_expires"])
            if expires < datetime.now(timezone.utc):
                raise HTTPException(400, "Reset token has expired")
        else:
            raise HTTPException(400, "Invalid reset token")
        
        return {"valid": True}
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error validating reset token: {str(e)}")
        raise HTTPException(500, "Failed to validate reset token")


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Reset user password with valid token
    """
    try:
        # Validate token
        user = await db_conn.users.find_one(
            {"password_reset_token": request.token},
            {"_id": 0}
        )
        
        if not user:
            raise HTTPException(400, "Invalid reset token")
        
        # Check expiry
        if "password_reset_expires" in user:
            expires = datetime.fromisoformat(user["password_reset_expires"])
            if expires < datetime.now(timezone.utc):
                raise HTTPException(400, "Reset token has expired")
        else:
            raise HTTPException(400, "Invalid reset token")
        
        # Validate password strength
        if len(request.new_password) < 8:
            raise HTTPException(400, "Password must be at least 8 characters")
        if not any(c.isupper() for c in request.new_password):
            raise HTTPException(400, "Password must contain at least one uppercase letter")
        if not any(c.islower() for c in request.new_password):
            raise HTTPException(400, "Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in request.new_password):
            raise HTTPException(400, "Password must contain at least one number")
        
        # Hash new password
        password_hash = pwd_context.hash(request.new_password)
        
        # Update password and clear reset token
        await db_conn.users.update_one(
            {"id": user["id"]},
            {"$set": {
                "password_hash": password_hash,
                "password_reset_token": None,
                "password_reset_expires": None,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"success": True, "message": "Password reset successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error resetting password: {str(e)}")
        raise HTTPException(500, "Failed to reset password")


# GDPR Compliance Routes

@router.post("/request-data-export")
@require_permission("settings.view")
async def request_data_export(request: Request, user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Request export of all user data (GDPR Right to Access)
    """
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(404, "User not found")
        
        # Collect all user data
        user_data = {
            "personal_info": {
                "id": user.get("id"),
                "email": user.get("email"),
                "full_name": user.get("full_name"),
                "phone": user.get("phone"),
                "role": user.get("role"),
                "created_at": user.get("created_at"),
                "last_login": user.get("last_login"),
            },
            "subscription": user.get("subscription", {}),
            "preferences": user.get("preferences", {}),
        }
        
        # Get user's content history
        posts = await db_conn.posts.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        user_data["content_history"] = posts
        
        # Get payment transactions
        transactions = await db_conn.payment_transactions.find(
            {"user_id": user_id},
            {"_id": 0}
        ).to_list(1000)
        user_data["payment_history"] = transactions
        
        # Log data export request
        await db_conn.gdpr_requests.insert_one({
            "user_id": user_id,
            "request_type": "data_export",
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "status": "completed"
        })
        
        return {
            "success": True,
            "data": user_data,
            "message": "Your personal data has been exported"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error exporting user data: {str(e)}")
        raise HTTPException(500, "Failed to export user data")


@router.post("/request-account-deletion")
@require_permission("settings.view")
async def request_account_deletion(request: Request, confirmation: str, user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Request account deletion (GDPR Right to Erasure)
    User must confirm by typing their email
    """
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(404, "User not found")
        
        # Verify confirmation using constant-time comparison to prevent timing attacks
        if not secure_compare(confirmation, user.get("email", "")):
            raise HTTPException(400, "Confirmation does not match email")
        
        # Log deletion request
        await db_conn.gdpr_requests.insert_one({
            "user_id": user_id,
            "request_type": "account_deletion",
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
            "confirmation": confirmation
        })
        
        # Mark user as deleted (soft delete for legal compliance)
        await db_conn.users.update_one(
            {"id": user_id},
            {"$set": {
                "deleted_at": datetime.now(timezone.utc).isoformat(),
                "deletion_requested": True,
                "email": f"deleted_{user_id}@deleted.com",
                "phone": None,
                "full_name": "Deleted User",
                "oauth_provider": None,
                "oauth_picture": None,
            }}
        )
        
        # Delete sessions
        await db_conn.sessions.delete_many({"user_id": user_id})
        
        return {
            "success": True,
            "message": "Your account has been scheduled for deletion. All personal data will be removed within 30 days."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting account: {str(e)}")
        raise HTTPException(500, "Failed to process deletion request")


@router.get("/gdpr-requests/{user_id}")
@require_permission("settings.view")
async def get_gdpr_requests(request: Request, user_id: str, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get all GDPR requests for a user
    """
    try:
        requests = await db_conn.gdpr_requests.find(
            {"user_id": user_id},
            {"_id": 0}
        ).to_list(100)
        
        return {"requests": requests}
    
    except Exception as e:
        logging.error(f"Error fetching GDPR requests: {str(e)}")
        raise HTTPException(500, "Failed to fetch GDPR requests")


@router.post("/verify-otp")
async def verify_otp(data: dict):
    """Verify OTP (placeholder implementation)"""
    # Placeholder OTP verification
    return {"message": "OTP verified", "verified": True}


@router.post("/verify-email")
async def verify_email(data: dict, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Verify user email with verification token"""
    try:
        token = data.get("token")
        if not token:
            raise HTTPException(400, "Verification token required")
        
        # Find user with this token
        user = await db_conn.users.find_one({"verification_token": token})
        if not user:
            raise HTTPException(404, "Invalid verification token")
        
        # Update user as verified
        await db_conn.users.update_one(
            {"id": user["id"]},
            {"$set": {
                "email_verified": True,
                "verification_token": None
            }}
        )
        
        return {"message": "Email verified successfully", "verified": True}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error verifying email: {str(e)}")
        raise HTTPException(500, "Failed to verify email")


@router.put("/profile")
@require_permission("settings.view")
async def update_profile(request: Request, data: dict, user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Update user profile settings"""
    try:
        if not user_id:
            raise HTTPException(400, "User ID required")
        
        # Get update fields
        update_fields = {}
        allowed_fields = [
            "full_name", "company_name", "job_title", "country",
            "default_tone", "default_homepage", "profile_picture"
        ]
        
        for field in allowed_fields:
            if field in data:
                update_fields[field] = data[field]
        
        if not update_fields:
            raise HTTPException(400, "No valid fields to update")
        
        # Update user
        result = await db_conn.users.update_one(
            {"id": user_id},
            {"$set": update_fields}
        )
        
        if result.matched_count == 0:
            raise HTTPException(404, "User not found")
        
        # Get updated user - exclude sensitive fields
        updated_user = await db_conn.users.find_one(
            {"id": user_id}, 
            {"_id": 0, "password": 0, "password_hash": 0}
        )
        
        return {
            "message": "Profile updated successfully",
            "user": updated_user
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating profile: {str(e)}")


@router.post("/change-password")
@require_permission("settings.view")
async def change_password(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Change user password.
    
    Requires:
    - old_password: Current password for verification
    - new_password: New password to set
    """
    try:
        data = await request.json()
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        
        if not old_password or not new_password:
            raise HTTPException(400, "Both old_password and new_password are required")
        
        if len(new_password) < 8:
            raise HTTPException(400, "New password must be at least 8 characters")
        
        # Get user from database
        user = await db_conn.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(404, "User not found")
        
        # Verify old password
        if not pwd_context.verify(old_password, user.get("password_hash", "")):
            raise HTTPException(401, "Current password is incorrect")
        
        # Hash new password
        new_password_hash = pwd_context.hash(new_password)
        
        # Update password in database
        await db_conn.users.update_one(
            {"id": user_id},
            {"$set": {"password_hash": new_password_hash, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {"success": True, "message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error changing password: {str(e)}")
        raise HTTPException(500, f"Error changing password: {str(e)}")


# Model for initial password setting
class SetInitialPasswordRequest(BaseModel):
    email: EmailStr
    temporary_password: str
    new_password: str


@router.post("/set-initial-password")
async def set_initial_password(
    request: SetInitialPasswordRequest,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Set initial password for new team members.
    
    This endpoint is used when a user logs in for the first time with a 
    temporary password and must change it before continuing.
    
    Requires:
    - email: User's email address
    - temporary_password: The temporary password provided to the user
    - new_password: The new password the user wants to set
    """
    try:
        # Find the user
        user = await db_conn.users.find_one({"email": request.email})
        if not user:
            raise HTTPException(404, "User not found")
        
        # Verify the temporary password
        if not pwd_context.verify(request.temporary_password, user.get("password_hash", "")):
            raise HTTPException(401, "Temporary password is incorrect")
        
        # Check that this user has the must_change_password flag
        if not user.get("must_change_password"):
            raise HTTPException(400, "Password change not required for this user")
        
        # Validate new password strength
        password_check = validate_password_strength(request.new_password)
        if not password_check["valid"]:
            raise HTTPException(400, detail={
                "message": "New password does not meet security requirements",
                "errors": password_check["errors"],
                "requirements": password_check["requirements"]
            })
        
        # Ensure new password is different from temporary password
        if request.new_password == request.temporary_password:
            raise HTTPException(400, "New password must be different from the temporary password")
        
        # Hash the new password
        new_password_hash = pwd_context.hash(request.new_password)
        
        # Update user: set new password and clear the must_change_password flag
        await db_conn.users.update_one(
            {"id": user["id"]},
            {
                "$set": {
                    "password_hash": new_password_hash,
                    "must_change_password": False,
                    "password_changed_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        logging.info(f"Initial password set successfully for user {user['id']}")
        
        return {
            "success": True,
            "message": "Password changed successfully. You can now log in with your new password."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error setting initial password: {str(e)}")
        raise HTTPException(500, f"Failed to set initial password: {str(e)}")


@router.post("/upload-avatar")
@require_permission("settings.view")
async def upload_avatar(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    file: UploadFile = File(...),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Upload user avatar/profile picture"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(400, "File must be an image")
        
        # Create uploads directory if it doesn't exist
        uploads_dir = "/app/uploads/avatars"
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"{user_id}_{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(uploads_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create URL path (relative path for serving through API)
        # Note: The serve endpoint is under /api/v1/uploads/avatars/
        avatar_url = f"/api/v1/uploads/avatars/{unique_filename}"
        
        # Update user record in database
        result = await db_conn.users.update_one(
            {"id": user_id},
            {"$set": {"profile_picture": avatar_url}}
        )
        
        if result.matched_count == 0:
            # Clean up file if user not found
            os.remove(file_path)
            raise HTTPException(404, "User not found")
        
        # Get updated user - exclude sensitive fields
        updated_user = await db_conn.users.find_one(
            {"id": user_id}, 
            {"_id": 0, "password": 0, "password_hash": 0}
        )
        
        return {
            "message": "Avatar uploaded successfully",
            "avatar_url": avatar_url,
            "user": updated_user
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error uploading avatar: {str(e)}")
        raise HTTPException(500, f"Failed to upload avatar: {str(e)}")


@router.post("/create-demo-user")
async def create_demo_user(user_data: dict, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Create or update a demo user in the database with proper password hashing"""
    try:
        user_id = user_data.get("id")
        if not user_id:
            raise HTTPException(400, "User ID required")
        
        # Check if user already exists
        existing_user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        
        # Generate the expected demo password
        role = user_data.get("role", "user")
        demo_password = f"Demo{role.capitalize()}!123"
        password_hash = pwd_context.hash(demo_password)
        
        if existing_user:
            # User already exists - reset password and unlock account for demo purposes
            # This ensures demo logins always work
            
            # Extract subscription plan from user_data
            subscription_data = user_data.get("subscription", {})
            subscription_plan = subscription_data.get("plan", "pro") if isinstance(subscription_data, dict) else "pro"
            
            update_fields = {
                "password_hash": password_hash,
                "failed_login_attempts": 0,
                "account_locked_until": None,
                "role": role,
                "full_name": user_data.get("full_name", existing_user.get("full_name")),
                "subscription_plan": subscription_plan,
                "subscription_status": "active",
                "plan_tier": subscription_plan,  # Also update plan_tier for rate limit service consistency
            }
            
            # Handle enterprise fields based on whether this is an enterprise demo or not
            if user_data.get("enterprise_id"):
                # Enterprise demo user - set enterprise fields
                update_fields["enterprise_id"] = user_data["enterprise_id"]
                update_fields["enterprise_name"] = user_data.get("enterprise_name")
                update_fields["enterprise_role"] = user_data.get("enterprise_role")
            else:
                # Non-enterprise demo user - explicitly clear enterprise fields
                # This fixes users who were previously set up with enterprise access
                update_fields["enterprise_id"] = None
                update_fields["enterprise_name"] = None
                update_fields["enterprise_role"] = None
            
            await db_conn.users.update_one(
                {"id": user_id},
                {"$set": update_fields}
            )
            
            # Also update user_credits collection to sync the plan
            plan_credits_map = {
                "free": {"monthly_credits": 25, "overage_rate": 0.06},
                "creator": {"monthly_credits": 750, "overage_rate": 0.05},
                "pro": {"monthly_credits": 1500, "overage_rate": 0.04},
                "team": {"monthly_credits": 5000, "overage_rate": 0.035},
                "business": {"monthly_credits": 15000, "overage_rate": 0.03},
            }
            plan_info = plan_credits_map.get(subscription_plan, plan_credits_map["pro"])
            
            await db_conn.user_credits.update_one(
                {"user_id": user_id},
                {"$set": {
                    "plan": subscription_plan,
                    "monthly_allowance": plan_info["monthly_credits"],
                    "overage_rate": plan_info["overage_rate"],
                }}
            )
            
            # Get updated user without sensitive data
            updated_user = await db_conn.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
            
            return {
                "message": "Demo user ready",
                "user": updated_user,
                "demo_password": demo_password
            }
        
        # Create new demo user with proper password hash
        new_user = {
            "id": user_id,
            "email": user_data.get("email"),
            "full_name": user_data.get("full_name"),
            "role": user_data.get("role", "user"),
            "password_hash": password_hash,  # Properly hashed password
            "email_verified": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "subscription_status": "active",
            "subscription_plan": user_data.get("subscription", {}).get("plan", "pro"),
            "default_homepage": user_data.get("default_homepage", "/contentry/dashboard"),
            "default_tone": "professional",
            "job_title": "",
            "company_name": "",
            "country": "",
            "profile_picture": None
        }
        
        # Add enterprise fields if applicable
        if user_data.get("enterprise_id"):
            enterprise_id = user_data["enterprise_id"]
            new_user["enterprise_id"] = enterprise_id
            new_user["enterprise_name"] = user_data.get("enterprise_name")
            new_user["enterprise_role"] = user_data.get("enterprise_role")
            
            # Create demo enterprise if it doesn't exist
            existing_enterprise = await db_conn.enterprises.find_one({"id": enterprise_id})
            if not existing_enterprise:
                # Get subscription tier from user data
                subscription_data = user_data.get("subscription", {})
                subscription_tier = subscription_data.get("plan", "enterprise") if isinstance(subscription_data, dict) else "enterprise"
                
                demo_enterprise = {
                    "id": enterprise_id,
                    "name": user_data.get("enterprise_name", "Demo Enterprise"),
                    "domains": ["demo.com", f"{enterprise_id}.demo.com"],
                    "admin_user_id": user_id,
                    "is_active": True,
                    "settings": {
                        "allowed_roles": ["admin", "manager", "creator", "reviewer"],
                        "shared_credits": True
                    },
                    "subscription_tier": subscription_tier,
                    "company_logo": None,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db_conn.enterprises.insert_one(demo_enterprise)
                logging.info(f"Created demo enterprise: {enterprise_id} with tier: {subscription_tier}")
        
        # Insert into database
        await db_conn.users.insert_one(new_user)
        
        # Remove sensitive data for response
        response_user = {k: v for k, v in new_user.items() if k not in ["_id", "password_hash"]}
        
        logging.info(f"Created demo user: {user_id} with role: {role}")
        
        return {
            "message": "Demo user created successfully",
            "user": response_user,
            "demo_password": demo_password  # Return password so frontend can use it for proper login
        }
    
    except Exception as e:
        logging.error(f"Error creating demo user: {str(e)}")
        raise HTTPException(500, f"Failed to create demo user: {str(e)}")


# =====================
# User Self-Service Account Management
# =====================

# ==================== BROWSER EXTENSION AUTH ====================

class ExtensionAuthRequest(BaseModel):
    """Request model for extension authentication"""
    email: str
    password: str

@router.post("/extension/login")
async def extension_login(credentials: ExtensionAuthRequest, request: Request = None, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Login endpoint specifically for the browser extension.
    Returns user data in a format suitable for the extension.
    """
    logging.info(f"Extension login attempt for email: {credentials.email}")
    
    # Find user
    user = await db_conn.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(401, "Invalid credentials")
    
    # Check if user has password_hash
    if not user.get("password_hash"):
        raise HTTPException(401, "Invalid credentials")
    
    # Verify password
    try:
        password_valid = pwd_context.verify(credentials.password, user["password_hash"])
    except Exception as e:
        logging.error(f"Password verification error: {str(e)}")
        password_valid = False
    
    if not password_valid:
        raise HTTPException(401, "Invalid credentials")
    
    # Update last login
    await db_conn.users.update_one(
        {"id": user["id"]},
        {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Return extension-friendly response
    return {
        "success": True,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name", ""),
            "enterprise_id": user.get("enterprise_id"),
            "profile_picture": user.get("profile_picture"),
        }
    }

@router.get("/extension/verify")
async def extension_verify_token(x_user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Verify if the extension's stored user session is still valid.
    """
    user = await db_conn.users.find_one({"id": x_user_id}, {"_id": 0, "id": 1, "email": 1, "full_name": 1})
    if not user:
        raise HTTPException(401, "Invalid session")
    
    return {
        "valid": True,
        "user": user
    }


@router.delete("/account")
@require_permission("settings.view")
async def delete_own_account(request: Request, user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Allow user to delete their own account"""
    try:
        # Find the user
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(404, "User not found")
        
        # Prevent deletion of admin users via this endpoint
        if user.get("role") == "admin":
            raise HTTPException(403, "Admin users cannot delete accounts via this endpoint")
        
        # If user is enterprise admin, check if they're the only admin
        if user.get("enterprise_role") == "enterprise_admin":
            enterprise_id = user.get("enterprise_id")
            admin_count = await db_conn.users.count_documents({
                "enterprise_id": enterprise_id,
                "enterprise_role": "enterprise_admin"
            })
            if admin_count <= 1:
                raise HTTPException(
                    400, 
                    "Cannot delete account: You are the only enterprise admin. Transfer admin rights first."
                )
        
        # Delete user's data
        deleted_posts = await db_conn.posts.delete_many({"user_id": user_id})
        await db_conn.content_analyses.delete_many({"user_id": user_id})
        await db_conn.scheduled_posts.delete_many({"user_id": user_id})
        await db_conn.notifications.delete_many({"user_id": user_id})
        
        # Delete the user
        result = await db_conn.users.delete_one({"id": user_id})
        
        if result.deleted_count == 0:
            raise HTTPException(500, "Failed to delete account")
        
        logging.info(f"User {user_id} ({user.get('email')}) deleted their own account")
        
        return {
            "message": "Account deleted successfully",
            "posts_deleted": deleted_posts.deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting account: {str(e)}")
        raise HTTPException(500, f"Failed to delete account: {str(e)}")


@router.post("/logout")
@require_permission("settings.view")
async def logout(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Logout user and clear authentication cookies.
    
    Security (ARCH-022):
    - Clears HttpOnly access_token cookie
    - Clears HttpOnly refresh_token cookie
    - Clears session_token cookie (for OAuth)
    - Invalidates any server-side session
    """
    # Create response
    response = JSONResponse(content={
        "success": True,
        "message": "Logged out successfully"
    })
    
    # Clear all auth cookies
    clear_auth_cookies(response)
    
    # Try to invalidate server-side session if it exists
    session_token = request.cookies.get("session_token")
    if session_token:
        try:
            await db_conn.sessions.delete_one({"session_token": session_token})
        except Exception as e:
            logging.warning(f"Failed to delete session: {e}")
    
    # Also try to extract and invalidate JWT-based sessions
    access_token = get_token_from_request(request)
    if access_token:
        try:
            # Add to token blacklist (if implemented)
            await db_conn.token_blacklist.insert_one({
                "token": access_token,
                "invalidated_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            })
        except Exception as e:
            logging.debug(f"Token blacklist not available: {e}")
    
    logging.info("User logged out successfully")
    return response


@router.get("/me")
async def get_current_user(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get current authenticated user from HttpOnly cookie.
    
    Security (ARCH-022): Extracts JWT from HttpOnly cookie instead of
    requiring client to send Authorization header.
    
    Note: This endpoint does NOT use @require_permission since it's the
    primary way for the frontend to verify authentication status.
    Authentication is handled internally by verifying the JWT token.
    """
    from services.auth_security import JWTTokenManager
    
    # Get token from cookie or header
    token = get_token_from_request(request)
    
    if not token:
        raise HTTPException(
            status_code=401, 
            detail={
                "error": "not_authenticated",
                "message": "Not authenticated - no token found"
            }
        )
    
    # Verify token
    try:
        payload = JWTTokenManager.verify_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=401, 
                detail={
                    "error": "invalid_token",
                    "message": "Invalid or expired token"
                }
            )
        
        user_id = payload.get("sub") or payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=401, 
                detail={
                    "error": "invalid_payload",
                    "message": "Invalid token payload"
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.warning(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=401, 
            detail={
                "error": "token_verification_failed",
                "message": "Invalid or expired token"
            }
        )
    
    # Get user from database
    user = await db_conn.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    
    if not user:
        raise HTTPException(
            status_code=404, 
            detail={
                "error": "user_not_found",
                "message": "User not found"
            }
        )
    
    # Compute is_enterprise_admin field (same logic as login endpoint)
    enterprise_role = user.get("enterprise_role")
    is_enterprise_admin = enterprise_role in ["admin", "enterprise_admin"] if enterprise_role else False
    user["is_enterprise_admin"] = is_enterprise_admin
    
    # Fetch enterprise_name if user has enterprise_id but no enterprise_name
    enterprise_id = user.get("enterprise_id")
    enterprise_name = user.get("enterprise_name")
    if enterprise_id and not enterprise_name:
        enterprise = await db_conn.enterprises.find_one(
            {"id": enterprise_id},
            {"_id": 0, "name": 1}
        )
        if enterprise:
            user["enterprise_name"] = enterprise.get("name")
    
    return {
        "success": True,
        "user": user
    }


@router.post("/refresh")
async def refresh_token(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Refresh access token using refresh token from HttpOnly cookie.
    
    Security (ARCH-022): 
    - Reads refresh_token from HttpOnly cookie
    - Issues new access_token as HttpOnly cookie
    """
    from services.auth_security import JWTTokenManager
    
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(401, "No refresh token")
    
    try:
        # Verify refresh token
        payload = JWTTokenManager.verify_refresh_token(refresh_token)
        if not payload:
            raise HTTPException(401, "Invalid refresh token")
        
        user_id = payload.get("sub") or payload.get("user_id")
        if not user_id:
            raise HTTPException(401, "Invalid token payload")
        
        # Get user to verify they still exist and get current info
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
        if not user:
            raise HTTPException(401, "User not found")
        
        # Generate new token pair
        tokens = JWTTokenManager.create_token_pair(
            user_id=user_id,
            email=user["email"],
            role=user.get("role", "user")
        )
        
        # Create response with new cookies
        response = JSONResponse(content={
            "success": True,
            "message": "Token refreshed",
            **tokens  # Include in body for backward compatibility
        })
        
        # Set new HttpOnly cookies
        set_auth_cookies(
            response, 
            tokens.get("access_token"), 
            tokens.get("refresh_token")
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Token refresh error: {e}")
        raise HTTPException(401, "Failed to refresh token")
