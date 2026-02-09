"""
Notification Routes
API endpoints for SMS and Email notifications

Security Update (ARCH-005 Phase 5.1b):
- Added @require_permission decorators for RBAC enforcement
"""

from fastapi import APIRouter, HTTPException, Header, Depends, Request
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import logging
from security_utils import secure_compare
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db

# ARCH-005: Authorization decorator
from services.authorization_decorator import require_permission

router = APIRouter(prefix="/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)

# Database will be set by server.py
db = None

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    """Set database instance"""
    global db
    db = database


# ==================== REQUEST MODELS ====================

class SendSMSRequest(BaseModel):
    phone: str
    message: str

class SendOTPRequest(BaseModel):
    phone: str

class VerifyOTPRequest(BaseModel):
    phone: str
    code: str

class SendEmailRequest(BaseModel):
    to_email: EmailStr
    subject: str
    message: str
    template: Optional[str] = None


# ==================== CONFIGURATION ====================

@router.get("/config-status")
@require_permission("notifications.view")
async def get_notification_config_status(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get notification service configuration status.
    
    Security (ARCH-005): Requires notifications.view permission.
    """
    from services.notification_service import notification_service
    return notification_service.get_configuration_status()


# ==================== SMS ENDPOINTS ====================

@router.post("/sms/send")
@require_permission("notifications.manage")
async def send_sms(request: Request, data: SendSMSRequest, user_id: str = Header(None, alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Send SMS message.
    
    Security (ARCH-005): Requires notifications.manage permission.
    """
    from services.notification_service import notification_service
    
    result = await notification_service.send_sms(data.phone, data.message)
    
    if result.get("success"):
        return result
    else:
        raise HTTPException(500, result.get("error", "Failed to send SMS"))


@router.post("/sms/send-otp")
@require_permission("notifications.manage")
async def send_otp(request: Request, data: SendOTPRequest, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Send OTP verification code via SMS.
    
    Security (ARCH-005): Requires notifications.manage permission.
    """
    from services.notification_service import notification_service
    
    result = await notification_service.send_verification_via_twilio_verify(data.phone)
    
    if result.get("success"):
        return {
            "message": "OTP sent successfully",
            "is_mocked": result.get("is_mocked", False),
            "otp_for_testing": result.get("otp_for_testing")  # Only in mock mode
        }
    else:
        raise HTTPException(500, result.get("error", "Failed to send OTP"))


@router.post("/sms/verify-otp")
@require_permission("notifications.manage")
async def verify_otp(request: Request, data: VerifyOTPRequest, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Verify OTP code.
    
    Security (ARCH-005): Requires notifications.manage permission.
    """
    from services.notification_service import notification_service
    
    # First try Twilio Verify service
    result = await notification_service.verify_otp_via_twilio_verify(data.phone, data.code)
    
    if result.get("success"):
        return {"verified": True, "message": "OTP verified successfully"}
    
    # If Twilio Verify not configured, check manual OTP
    if "not configured" in result.get("error", ""):
        # Check manual OTP from database
        otp_record = await db_conn.phone_otps.find_one({"phone": data.phone})
        
        if not otp_record:
            raise HTTPException(400, "No OTP found for this phone number")
        
        from datetime import datetime, timezone
        expiry = otp_record.get("expiry")
        if expiry and datetime.now(timezone.utc) > expiry:
            await db_conn.phone_otps.delete_one({"phone": data.phone})
            raise HTTPException(400, "OTP has expired")
        
        # Use constant-time comparison to prevent timing attacks
        if not secure_compare(otp_record.get("otp", ""), data.code):
            raise HTTPException(400, "Invalid OTP")
        
        # Delete used OTP
        await db_conn.phone_otps.delete_one({"phone": data.phone})
        
        return {"verified": True, "message": "OTP verified successfully"}
    
    raise HTTPException(400, result.get("error", "OTP verification failed"))


# ==================== EMAIL ENDPOINTS ====================

@router.post("/email/send")
@require_permission("notifications.manage")
async def send_email(request: Request, data: SendEmailRequest, user_id: str = Header(None, alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Send custom email.
    
    Security (ARCH-005): Requires notifications.manage permission.
    """
    from services.notification_service import notification_service
    
    # Build simple HTML content
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="padding: 30px; background: #f5f5f5;">
            {data.message}
        </div>
    </body>
    </html>
    """
    
    result = await notification_service.send_email(
        to_email=data.to_email,
        subject=data.subject,
        html_content=html_content,
        text_content=data.message
    )
    
    if result.get("success"):
        return result
    else:
        raise HTTPException(500, result.get("error", "Failed to send email"))


@router.post("/email/verification")
@require_permission("notifications.manage")
async def send_verification_email(
    request: Request,
    email: EmailStr,
    user_name: str,
    verification_token: str,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Send email verification link.
    
    Security (ARCH-005): Requires notifications.manage permission.
    """
    from services.notification_service import notification_service
    
    result = await notification_service.send_verification_email(
        email=email,
        verification_token=verification_token,
        user_name=user_name
    )
    
    if result.get("success"):
        return {"message": "Verification email sent", **result}
    else:
        raise HTTPException(500, result.get("error", "Failed to send verification email"))


@router.post("/email/welcome")
@require_permission("notifications.manage")
async def send_welcome_email(request: Request, email: EmailStr, user_name: str, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Send welcome email.
    
    Security (ARCH-005): Requires notifications.manage permission.
    """
    from services.notification_service import notification_service
    
    result = await notification_service.send_welcome_email(email=email, user_name=user_name)
    
    if result.get("success"):
        return {"message": "Welcome email sent", **result}
    else:
        raise HTTPException(500, result.get("error", "Failed to send welcome email"))


@router.post("/email/password-reset")
@require_permission("notifications.manage")
async def send_password_reset_email(
    request: Request,
    email: EmailStr,
    user_name: str,
    reset_token: str,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Send password reset link.
    
    Security (ARCH-005): Requires notifications.manage permission.
    """
    from services.notification_service import notification_service
    
    result = await notification_service.send_password_reset_email(
        email=email,
        reset_token=reset_token,
        user_name=user_name
    )
    
    if result.get("success"):
        return {"message": "Password reset email sent", **result}
    else:
        raise HTTPException(500, result.get("error", "Failed to send password reset email"))


# ==================== NOTIFICATION HISTORY ====================

@router.get("/history")
@require_permission("notifications.view")
async def get_notification_history(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    limit: int = 50,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get user's notification history.
    
    Security (ARCH-005): Requires notifications.view permission.
    """
    try:
        notifications = await db_conn.notifications.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return {"notifications": notifications, "total": len(notifications)}
    except Exception as e:
        logger.error(f"Error fetching notification history: {str(e)}")
        raise HTTPException(500, "Failed to fetch notification history")


@router.put("/mark-read/{notification_id}")
@require_permission("notifications.manage")
async def mark_notification_read(
    request: Request,
    notification_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Mark notification as read.
    
    Security (ARCH-005): Requires notifications.manage permission.
    """
    try:
        result = await db_conn.notifications.update_one(
            {"id": notification_id, "user_id": user_id},
            {"$set": {"read": True, "read_at": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(404, "Notification not found")
        
        return {"message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification: {str(e)}")
        raise HTTPException(500, "Failed to update notification")


@router.delete("/{notification_id}")
@require_permission("notifications.manage")
async def delete_notification(
    request: Request,
    notification_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a notification"""
    try:
        result = await db_conn.notifications.delete_one(
            {"id": notification_id, "user_id": user_id}
        )
        
        if result.deleted_count == 0:
            raise HTTPException(404, "Notification not found")
        
        return {"message": "Notification deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification: {str(e)}")
        raise HTTPException(500, "Failed to delete notification")
