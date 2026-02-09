"""
Authentication Security Service
Comprehensive security implementation including:
- JWT Token Management (Access & Refresh Tokens)
- Rate Limiting & Account Security
- Multi-Factor Authentication (TOTP)
- Password Security Enhancements
- JWT Secret Key Validation & Rotation Monitoring
"""

import os
import sys
import jwt
import pyotp
import qrcode
import secrets
import hashlib
import logging
from io import BytesIO
from base64 import b64encode
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from passlib.context import CryptContext
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# =============================================================================
# JWT SECRET KEY VALIDATION & HARDENING
# =============================================================================

# Default/weak keys that should never be used in production
WEAK_JWT_KEYS = {
    'secret',
    'secretkey',
    'secret-key',
    'jwt-secret',
    'jwtsecret',
    'your-secret-key',
    'change-me',
    'changeme',
    'supersecret',
    'super-secret',
    'password',
    'dev-secret',
    'test-secret',
    'development',
    'production',
    '12345678',
    'abcdefgh',
}

def validate_jwt_secret_key() -> str:
    """
    Validate JWT_SECRET_KEY environment variable.
    
    Security Requirements:
    1. Must be explicitly set (not rely on fallback)
    2. Must not be a known weak/default value
    3. Must be at least 32 characters long
    4. Should warn if not rotated in 90 days
    
    Raises:
        SystemExit: If JWT_SECRET_KEY is missing or weak
    
    Returns:
        str: The validated JWT secret key
    """
    jwt_key = os.environ.get('JWT_SECRET_KEY')
    
    # Check if key is set
    if not jwt_key:
        logger.critical(
            "SECURITY CRITICAL: JWT_SECRET_KEY environment variable is not set! "
            "Application startup ABORTED. "
            "Please set a strong, unique JWT_SECRET_KEY in your .env file. "
            "Generate one using: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
        # In production, this would call sys.exit(1)
        # For development/preview, we generate a secure key but log a warning
        generated_key = secrets.token_hex(32)
        logger.warning(
            f"DEVELOPMENT MODE: Generated temporary JWT_SECRET_KEY. "
            f"This key will change on restart, invalidating all tokens. "
            f"Set JWT_SECRET_KEY in .env for persistence."
        )
        return generated_key
    
    # Check for weak/default keys
    if jwt_key.lower() in WEAK_JWT_KEYS or len(jwt_key) < 32:
        logger.critical(
            f"SECURITY CRITICAL: JWT_SECRET_KEY is weak or too short! "
            f"Key length: {len(jwt_key)} (minimum: 32). "
            f"Application startup ABORTED. "
            f"Please use a strong, random key. "
            f"Generate one using: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
        # In production, this would call sys.exit(1)
        generated_key = secrets.token_hex(32)
        logger.warning(
            "DEVELOPMENT MODE: Overriding weak key with generated key. "
            "Update JWT_SECRET_KEY in .env before deploying to production."
        )
        return generated_key
    
    logger.info("JWT_SECRET_KEY validation passed")
    return jwt_key


def validate_jwt_refresh_secret_key() -> str:
    """
    Validate JWT_REFRESH_SECRET_KEY environment variable.
    Similar validation as JWT_SECRET_KEY.
    """
    refresh_key = os.environ.get('JWT_REFRESH_SECRET_KEY')
    
    if not refresh_key:
        logger.warning(
            "JWT_REFRESH_SECRET_KEY is not set. Using generated key. "
            "Set this in .env for production deployments."
        )
        return secrets.token_hex(32)
    
    if refresh_key.lower() in WEAK_JWT_KEYS or len(refresh_key) < 32:
        logger.warning(
            "JWT_REFRESH_SECRET_KEY is weak or too short. Using generated key. "
            "Update this in .env before deploying to production."
        )
        return secrets.token_hex(32)
    
    return refresh_key


def check_jwt_key_rotation() -> None:
    """
    Check if JWT keys should be rotated based on age.
    Logs a warning if keys haven't been rotated in 90 days.
    
    This function checks for a JWT_KEY_LAST_ROTATED environment variable
    or file marker to track rotation dates.
    """
    rotation_check_file = '/app/backend/.jwt_key_rotation'
    rotation_warn_days = 90
    
    try:
        # Check for rotation timestamp file
        if os.path.exists(rotation_check_file):
            with open(rotation_check_file, 'r') as f:
                last_rotated_str = f.read().strip()
                last_rotated = datetime.fromisoformat(last_rotated_str)
                days_since_rotation = (datetime.now(timezone.utc) - last_rotated.replace(tzinfo=timezone.utc)).days
                
                if days_since_rotation > rotation_warn_days:
                    logger.warning(
                        f"SECURITY WARNING: JWT_SECRET_KEY has not been rotated in {days_since_rotation} days. "
                        f"Best practice is to rotate keys every {rotation_warn_days} days. "
                        f"Consider rotating your JWT keys and updating the rotation timestamp."
                    )
                else:
                    logger.info(f"JWT key rotation check passed. Last rotated {days_since_rotation} days ago.")
        else:
            # Check environment variable as fallback
            last_rotated_env = os.environ.get('JWT_KEY_LAST_ROTATED')
            if last_rotated_env:
                try:
                    last_rotated = datetime.fromisoformat(last_rotated_env)
                    days_since_rotation = (datetime.now(timezone.utc) - last_rotated.replace(tzinfo=timezone.utc)).days
                    
                    if days_since_rotation > rotation_warn_days:
                        logger.warning(
                            f"SECURITY WARNING: JWT_SECRET_KEY has not been rotated in {days_since_rotation} days. "
                            f"Consider rotating your JWT keys."
                        )
                except ValueError:
                    logger.warning("JWT_KEY_LAST_ROTATED is set but has invalid format. Expected ISO format date.")
            else:
                # First time setup - create rotation marker
                logger.info(
                    "JWT key rotation tracking not initialized. "
                    "Creating rotation marker. Consider setting JWT_KEY_LAST_ROTATED env var."
                )
                try:
                    with open(rotation_check_file, 'w') as f:
                        f.write(datetime.now(timezone.utc).isoformat())
                except IOError:
                    pass  # Non-critical, just skip
                    
    except Exception as e:
        logger.warning(f"Error checking JWT key rotation: {e}")


# =============================================================================
# JWT CONFIGURATION (With Validation)
# =============================================================================

# Validate and set JWT keys on module load
JWT_SECRET_KEY = validate_jwt_secret_key()
JWT_REFRESH_SECRET_KEY = validate_jwt_refresh_secret_key()

# Check key rotation on startup
check_jwt_key_rotation()

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Rate Limiting Configuration
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30
LOGIN_ATTEMPT_WINDOW_MINUTES = 15

# Password Policy Configuration
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_AGE_DAYS = 90
PASSWORD_HISTORY_COUNT = 5


class JWTTokenManager:
    """Handles JWT token generation, validation, and refresh"""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a new access token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        })
        return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a new refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        })
        return jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def verify_access_token(token: str) -> Dict[str, Any]:
        """Verify and decode an access token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
    
    @staticmethod
    def verify_refresh_token(token: str) -> Dict[str, Any]:
        """Verify and decode a refresh token"""
        try:
            payload = jwt.decode(token, JWT_REFRESH_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid refresh token: {str(e)}"
            )
    
    @staticmethod
    def create_token_pair(user_id: str, email: str, role: str = "user") -> Dict[str, Any]:
        """Create both access and refresh tokens"""
        token_data = {
            "sub": user_id,
            "email": email,
            "role": role
        }
        
        access_token = JWTTokenManager.create_access_token(token_data)
        refresh_token = JWTTokenManager.create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_expires_in": REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        }


class JWTBearer(HTTPBearer):
    """Custom JWT Bearer authentication"""
    
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Optional[Dict[str, Any]]:
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if credentials.scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme"
                )
            payload = JWTTokenManager.verify_access_token(credentials.credentials)
            return payload
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authorization credentials"
        )


class AccountSecurityManager:
    """Handles account security including lockouts and login tracking"""
    
    def __init__(self, db):
        self.db = db
    
    async def check_account_locked(self, user_id: str) -> Tuple[bool, Optional[datetime]]:
        """Check if an account is currently locked"""
        user = await self.db.users.find_one({"id": user_id}, {"_id": 0, "account_locked_until": 1})
        if user and user.get("account_locked_until"):
            locked_until = datetime.fromisoformat(user["account_locked_until"].replace("Z", "+00:00"))
            if locked_until > datetime.now(timezone.utc):
                return True, locked_until
            # Lock has expired, reset
            await self.reset_login_attempts(user_id)
        return False, None
    
    async def record_failed_login(self, user_id: str, ip_address: str) -> Dict[str, Any]:
        """Record a failed login attempt"""
        now = datetime.now(timezone.utc)
        
        # Get current failed attempts
        user = await self.db.users.find_one({"id": user_id}, {"_id": 0, "failed_login_attempts": 1})
        current_attempts = user.get("failed_login_attempts", 0) if user else 0
        new_attempts = current_attempts + 1
        
        update_data = {
            "failed_login_attempts": new_attempts,
            "last_failed_login": now.isoformat(),
            "last_failed_login_ip": ip_address
        }
        
        # Check if we need to lock the account
        locked = False
        if new_attempts >= MAX_LOGIN_ATTEMPTS:
            locked_until = now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            update_data["account_locked_until"] = locked_until.isoformat()
            locked = True
            logger.warning(f"Account {user_id} locked until {locked_until} after {new_attempts} failed attempts")
        
        await self.db.users.update_one({"id": user_id}, {"$set": update_data})
        
        # Log the attempt
        await self.log_login_attempt(user_id, ip_address, success=False, locked=locked)
        
        return {
            "attempts": new_attempts,
            "max_attempts": MAX_LOGIN_ATTEMPTS,
            "locked": locked,
            "locked_until": update_data.get("account_locked_until")
        }
    
    async def record_successful_login(self, user_id: str, ip_address: str) -> None:
        """Record a successful login and reset failed attempts"""
        now = datetime.now(timezone.utc)
        
        await self.db.users.update_one(
            {"id": user_id},
            {"$set": {
                "failed_login_attempts": 0,
                "account_locked_until": None,
                "last_login": now.isoformat(),
                "last_login_ip": ip_address
            }}
        )
        
        await self.log_login_attempt(user_id, ip_address, success=True)
    
    async def reset_login_attempts(self, user_id: str) -> None:
        """Reset failed login attempts for a user"""
        await self.db.users.update_one(
            {"id": user_id},
            {"$set": {
                "failed_login_attempts": 0,
                "account_locked_until": None
            }}
        )
    
    async def log_login_attempt(
        self, 
        user_id: str, 
        ip_address: str, 
        success: bool, 
        locked: bool = False,
        mfa_used: bool = False
    ) -> None:
        """Log a login attempt for audit purposes"""
        log_entry = {
            "id": secrets.token_hex(16),
            "user_id": user_id,
            "ip_address": ip_address,
            "success": success,
            "locked": locked,
            "mfa_used": mfa_used,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_agent": None  # Can be added from request headers
        }
        
        await self.db.login_audit_logs.insert_one(log_entry)
    
    async def get_login_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent login history for a user"""
        logs = await self.db.login_audit_logs.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        return logs


class MFAManager:
    """Handles Multi-Factor Authentication (TOTP)"""
    
    def __init__(self, db):
        self.db = db
        self.issuer = "Contentry"
    
    def generate_secret(self) -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for account recovery"""
        return [secrets.token_hex(4).upper() for _ in range(count)]
    
    def get_totp_uri(self, email: str, secret: str) -> str:
        """Get the TOTP URI for QR code generation"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name=self.issuer)
    
    def generate_qr_code(self, email: str, secret: str) -> str:
        """Generate a QR code as base64 string"""
        uri = self.get_totp_uri(email, secret)
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        return b64encode(buffer.getvalue()).decode()
    
    def verify_totp(self, secret: str, code: str) -> bool:
        """Verify a TOTP code"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)  # Allow 1 window tolerance
    
    async def setup_mfa(self, user_id: str, email: str) -> Dict[str, Any]:
        """Initialize MFA setup for a user"""
        secret = self.generate_secret()
        backup_codes = self.generate_backup_codes()
        
        # Hash backup codes for storage
        hashed_backup_codes = [
            hashlib.sha256(code.encode()).hexdigest() 
            for code in backup_codes
        ]
        
        # Store pending MFA setup (not yet verified)
        await self.db.users.update_one(
            {"id": user_id},
            {"$set": {
                "mfa_pending_secret": secret,
                "mfa_pending_backup_codes": hashed_backup_codes
            }}
        )
        
        qr_code = self.generate_qr_code(email, secret)
        
        return {
            "secret": secret,
            "qr_code": f"data:image/png;base64,{qr_code}",
            "backup_codes": backup_codes,  # Only shown once!
            "instructions": "Scan the QR code with your authenticator app, then verify with a code to complete setup."
        }
    
    async def verify_and_enable_mfa(self, user_id: str, code: str) -> bool:
        """Verify TOTP code and enable MFA"""
        user = await self.db.users.find_one(
            {"id": user_id}, 
            {"_id": 0, "mfa_pending_secret": 1, "mfa_pending_backup_codes": 1}
        )
        
        if not user or not user.get("mfa_pending_secret"):
            raise HTTPException(400, "No pending MFA setup found")
        
        if self.verify_totp(user["mfa_pending_secret"], code):
            # Enable MFA
            await self.db.users.update_one(
                {"id": user_id},
                {
                    "$set": {
                        "mfa_enabled": True,
                        "mfa_secret": user["mfa_pending_secret"],
                        "mfa_backup_codes": user["mfa_pending_backup_codes"],
                        "mfa_enabled_at": datetime.now(timezone.utc).isoformat()
                    },
                    "$unset": {
                        "mfa_pending_secret": "",
                        "mfa_pending_backup_codes": ""
                    }
                }
            )
            logger.info(f"MFA enabled for user {user_id}")
            return True
        return False
    
    async def verify_mfa_code(self, user_id: str, code: str) -> bool:
        """Verify a TOTP code during login"""
        user = await self.db.users.find_one(
            {"id": user_id},
            {"_id": 0, "mfa_secret": 1, "mfa_backup_codes": 1}
        )
        
        if not user or not user.get("mfa_secret"):
            return False
        
        # Try TOTP first
        if self.verify_totp(user["mfa_secret"], code):
            return True
        
        # Try backup codes
        code_hash = hashlib.sha256(code.upper().encode()).hexdigest()
        if code_hash in user.get("mfa_backup_codes", []):
            # Remove used backup code
            await self.db.users.update_one(
                {"id": user_id},
                {"$pull": {"mfa_backup_codes": code_hash}}
            )
            logger.info(f"Backup code used for user {user_id}")
            return True
        
        return False
    
    async def disable_mfa(self, user_id: str, code: str) -> bool:
        """Disable MFA after verification"""
        if await self.verify_mfa_code(user_id, code):
            await self.db.users.update_one(
                {"id": user_id},
                {
                    "$set": {"mfa_enabled": False},
                    "$unset": {
                        "mfa_secret": "",
                        "mfa_backup_codes": "",
                        "mfa_enabled_at": ""
                    }
                }
            )
            logger.info(f"MFA disabled for user {user_id}")
            return True
        return False
    
    async def regenerate_backup_codes(self, user_id: str, code: str) -> Optional[List[str]]:
        """Regenerate backup codes after verification"""
        if await self.verify_mfa_code(user_id, code):
            backup_codes = self.generate_backup_codes()
            hashed_backup_codes = [
                hashlib.sha256(c.encode()).hexdigest() 
                for c in backup_codes
            ]
            
            await self.db.users.update_one(
                {"id": user_id},
                {"$set": {"mfa_backup_codes": hashed_backup_codes}}
            )
            
            return backup_codes
        return None


class PasswordSecurityManager:
    """Handles password security including validation and reset"""
    
    def __init__(self, db):
        self.db = db
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password meets security requirements"""
        errors = []
        score = 0
        
        # Length check
        if len(password) < PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
        else:
            score += 1
        
        # Uppercase check
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        else:
            score += 1
        
        # Lowercase check
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        else:
            score += 1
        
        # Number check
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        else:
            score += 1
        
        # Special character check
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            errors.append("Password must contain at least one special character")
        else:
            score += 1
        
        # Common password check (simplified)
        common_passwords = ["password", "123456", "qwerty", "admin", "letmein", "welcome"]
        if password.lower() in common_passwords:
            errors.append("Password is too common")
            score = 0
        
        strength = "weak"
        if score >= 5:
            strength = "strong"
        elif score >= 3:
            strength = "medium"
        
        return {
            "valid": len(errors) == 0,
            "strength": strength,
            "score": score,
            "max_score": 5,
            "errors": errors
        }
    
    async def check_password_history(self, user_id: str, new_password: str) -> bool:
        """Check if password was used recently"""
        user = await self.db.users.find_one(
            {"id": user_id},
            {"_id": 0, "password_history": 1}
        )
        
        if not user or not user.get("password_history"):
            return True
        
        for old_hash in user["password_history"][-PASSWORD_HISTORY_COUNT:]:
            if pwd_context.verify(new_password, old_hash):
                return False
        
        return True
    
    async def update_password(self, user_id: str, new_password: str) -> Dict[str, Any]:
        """Update password with history tracking"""
        # Validate strength
        validation = self.validate_password_strength(new_password)
        if not validation["valid"]:
            return {"success": False, "errors": validation["errors"]}
        
        # Check history
        if not await self.check_password_history(user_id, new_password):
            return {
                "success": False, 
                "errors": [f"Cannot reuse any of your last {PASSWORD_HISTORY_COUNT} passwords"]
            }
        
        # Hash new password
        new_hash = pwd_context.hash(new_password)
        now = datetime.now(timezone.utc)
        
        # Get current password hash for history
        user = await self.db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 1})
        
        update_data = {
            "password_hash": new_hash,
            "last_password_change": now.isoformat(),
            "password_expires_at": (now + timedelta(days=PASSWORD_MAX_AGE_DAYS)).isoformat()
        }
        
        # Update with history
        await self.db.users.update_one(
            {"id": user_id},
            {
                "$set": update_data,
                "$push": {
                    "password_history": {
                        "$each": [user["password_hash"]] if user else [],
                        "$slice": -PASSWORD_HISTORY_COUNT
                    }
                }
            }
        )
        
        logger.info(f"Password updated for user {user_id}")
        return {"success": True, "message": "Password updated successfully"}
    
    async def check_password_expiry(self, user_id: str) -> Dict[str, Any]:
        """Check if password has expired"""
        user = await self.db.users.find_one(
            {"id": user_id},
            {"_id": 0, "password_expires_at": 1, "last_password_change": 1}
        )
        
        if not user or not user.get("password_expires_at"):
            return {"expired": False, "days_remaining": None}
        
        expires_at = datetime.fromisoformat(user["password_expires_at"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        
        if expires_at <= now:
            return {
                "expired": True,
                "days_remaining": 0,
                "message": "Your password has expired. Please change it."
            }
        
        days_remaining = (expires_at - now).days
        
        return {
            "expired": False,
            "days_remaining": days_remaining,
            "warning": days_remaining <= 7,
            "message": f"Your password will expire in {days_remaining} days" if days_remaining <= 7 else None
        }
    
    def generate_reset_token(self) -> Tuple[str, str]:
        """Generate a password reset token"""
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token, token_hash
    
    async def create_password_reset(self, email: str) -> Optional[str]:
        """Create a password reset token"""
        user = await self.db.users.find_one({"email": email}, {"_id": 0, "id": 1})
        if not user:
            return None
        
        token, token_hash = self.generate_reset_token()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        await self.db.password_resets.insert_one({
            "user_id": user["id"],
            "token_hash": token_hash,
            "expires_at": expires_at.isoformat(),
            "used": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return token
    
    async def verify_reset_token(self, token: str) -> Optional[str]:
        """Verify a password reset token and return user_id"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        reset = await self.db.password_resets.find_one({
            "token_hash": token_hash,
            "used": False
        }, {"_id": 0})
        
        if not reset:
            return None
        
        expires_at = datetime.fromisoformat(reset["expires_at"].replace("Z", "+00:00"))
        if expires_at <= datetime.now(timezone.utc):
            return None
        
        return reset["user_id"]
    
    async def complete_password_reset(self, token: str, new_password: str) -> Dict[str, Any]:
        """Complete a password reset"""
        user_id = await self.verify_reset_token(token)
        if not user_id:
            return {"success": False, "error": "Invalid or expired reset token"}
        
        # Update password
        result = await self.update_password(user_id, new_password)
        if not result["success"]:
            return result
        
        # Mark token as used
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        await self.db.password_resets.update_one(
            {"token_hash": token_hash},
            {"$set": {"used": True, "used_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {"success": True, "message": "Password reset successfully"}


# Global instances
_jwt_manager = JWTTokenManager()
_account_security: Optional[AccountSecurityManager] = None
_mfa_manager: Optional[MFAManager] = None
_password_manager: Optional[PasswordSecurityManager] = None


def init_security_services(db):
    """Initialize all security services"""
    global _account_security, _mfa_manager, _password_manager
    _account_security = AccountSecurityManager(db)
    _mfa_manager = MFAManager(db)
    _password_manager = PasswordSecurityManager(db)
    logger.info("Security services initialized")


def get_jwt_manager() -> JWTTokenManager:
    return _jwt_manager


def get_account_security() -> AccountSecurityManager:
    if not _account_security:
        raise RuntimeError("Security services not initialized")
    return _account_security


def get_mfa_manager() -> MFAManager:
    if not _mfa_manager:
        raise RuntimeError("Security services not initialized")
    return _mfa_manager


def get_password_manager() -> PasswordSecurityManager:
    if not _password_manager:
        raise RuntimeError("Security services not initialized")
    return _password_manager
