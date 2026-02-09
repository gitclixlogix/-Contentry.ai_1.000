"""
Production Notification Service
Handles SMS (Twilio) and Email (SendGrid) notifications
Framework-ready implementation with mock fallback when credentials not configured
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, List
import secrets

logger = logging.getLogger(__name__)

# ==================== TWILIO CONFIGURATION ====================
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')
TWILIO_VERIFY_SERVICE_SID = os.environ.get('TWILIO_VERIFY_SERVICE_SID', '')

# ==================== SENDGRID CONFIGURATION ====================
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@contentry.ai')
FROM_NAME = os.environ.get('FROM_NAME', 'Contentry.ai')

# ==================== APP CONFIGURATION ====================
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
APP_NAME = 'Contentry.ai'


class NotificationService:
    """
    Unified notification service for SMS and Email
    Automatically falls back to mock/console mode when credentials not configured
    """
    
    def __init__(self):
        self.twilio_configured = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER)
        self.sendgrid_configured = bool(SENDGRID_API_KEY)
        self.twilio_verify_configured = bool(TWILIO_VERIFY_SERVICE_SID)
        
        self._twilio_client = None
        self._sendgrid_client = None
        
        if not self.twilio_configured:
            logger.warning("Twilio SMS not configured - using mock mode")
        if not self.sendgrid_configured:
            logger.warning("SendGrid not configured - using console mode for emails")
    
    # ==================== TWILIO CLIENT ====================
    
    def _get_twilio_client(self):
        """Get or create Twilio client"""
        if not self.twilio_configured:
            return None
        
        if self._twilio_client is None:
            try:
                from twilio.rest import Client
                self._twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            except ImportError:
                logger.error("Twilio package not installed. Run: pip install twilio")
                return None
            except Exception as e:
                logger.error(f"Failed to create Twilio client: {str(e)}")
                return None
        
        return self._twilio_client
    
    # ==================== SMS METHODS ====================
    
    async def send_sms(self, to_phone: str, message: str) -> Dict:
        """
        Send SMS message via Twilio
        Falls back to mock mode if Twilio not configured
        """
        if not self.twilio_configured:
            logger.info(f"[MOCK SMS] To: {to_phone}\nMessage: {message}")
            return {
                "success": True,
                "is_mocked": True,
                "message_id": f"mock_sms_{secrets.token_hex(8)}",
                "to": to_phone,
                "note": "SMS service not configured - add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER to .env"
            }
        
        try:
            client = self._get_twilio_client()
            if not client:
                return {"success": False, "error": "Twilio client not available"}
            
            # Send SMS
            sms_message = client.messages.create(
                body=message,
                from_=TWILIO_PHONE_NUMBER,
                to=to_phone
            )
            
            logger.info(f"SMS sent to {to_phone}: SID {sms_message.sid}")
            
            return {
                "success": True,
                "is_mocked": False,
                "message_id": sms_message.sid,
                "to": to_phone,
                "status": sms_message.status
            }
            
        except Exception as e:
            logger.error(f"SMS send error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_otp_sms(self, to_phone: str, otp_code: str) -> Dict:
        """Send OTP code via SMS"""
        message = f"Your {APP_NAME} verification code is: {otp_code}. This code expires in 5 minutes."
        return await self.send_sms(to_phone, message)
    
    async def send_verification_via_twilio_verify(self, to_phone: str, channel: str = "sms") -> Dict:
        """
        Send verification code using Twilio Verify service
        This is more secure than custom OTP as Twilio manages the codes
        """
        if not self.twilio_verify_configured:
            # Fall back to regular SMS with generated OTP
            otp = str(secrets.randbelow(900000) + 100000)  # 6-digit OTP
            result = await self.send_otp_sms(to_phone, otp)
            result["otp_for_testing"] = otp if result.get("is_mocked") else None
            return result
        
        try:
            client = self._get_twilio_client()
            if not client:
                return {"success": False, "error": "Twilio client not available"}
            
            verification = client.verify.v2.services(TWILIO_VERIFY_SERVICE_SID) \
                .verifications.create(to=to_phone, channel=channel)
            
            logger.info(f"Twilio Verify sent to {to_phone}: Status {verification.status}")
            
            return {
                "success": True,
                "is_mocked": False,
                "status": verification.status,
                "to": to_phone,
                "channel": channel
            }
            
        except Exception as e:
            logger.error(f"Twilio Verify error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def verify_otp_via_twilio_verify(self, to_phone: str, code: str) -> Dict:
        """
        Verify OTP code using Twilio Verify service
        """
        if not self.twilio_verify_configured:
            return {
                "success": False,
                "error": "Twilio Verify not configured - use manual OTP verification"
            }
        
        try:
            client = self._get_twilio_client()
            if not client:
                return {"success": False, "error": "Twilio client not available"}
            
            verification_check = client.verify.v2.services(TWILIO_VERIFY_SERVICE_SID) \
                .verification_checks.create(to=to_phone, code=code)
            
            is_valid = verification_check.status == "approved"
            
            return {
                "success": is_valid,
                "status": verification_check.status,
                "is_mocked": False
            }
            
        except Exception as e:
            logger.error(f"Twilio Verify check error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # ==================== EMAIL METHODS ====================
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str = None,
        from_email: str = None,
        from_name: str = None
    ) -> Dict:
        """
        Send email via SendGrid
        Falls back to console logging if SendGrid not configured
        """
        from_email = from_email or FROM_EMAIL
        from_name = from_name or FROM_NAME
        
        if not self.sendgrid_configured:
            logger.info(f"""
            ===============================================
            📧 EMAIL (Mock Mode)
            ===============================================
            To: {to_email}
            From: {from_name} <{from_email}>
            Subject: {subject}
            
            {text_content or 'HTML content - see logs for full email'}
            
            (Configure SENDGRID_API_KEY to enable real emails)
            ===============================================
            """)
            return {
                "success": True,
                "is_mocked": True,
                "to": to_email,
                "subject": subject,
                "note": "Email service not configured - add SENDGRID_API_KEY to .env"
            }
        
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            message = Mail(
                from_email=Email(from_email, from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            if text_content:
                message.add_content(Content("text/plain", text_content))
            
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            
            logger.info(f"Email sent to {to_email}: Status {response.status_code}")
            
            return {
                "success": response.status_code in [200, 201, 202],
                "is_mocked": False,
                "to": to_email,
                "status_code": response.status_code
            }
            
        except ImportError:
            logger.error("SendGrid package not installed. Run: pip install sendgrid")
            return {"success": False, "error": "SendGrid package not installed"}
        except Exception as e:
            logger.error(f"SendGrid email error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_verification_email(self, email: str, verification_token: str, user_name: str) -> Dict:
        """Send email verification link"""
        verification_link = f"{FRONTEND_URL}/contentry/auth/verify-email?token={verification_token}"
        
        subject = f"Verify your {APP_NAME} account"
        html_content = self._get_verification_email_template(user_name, verification_link)
        text_content = f"Hi {user_name}, verify your email: {verification_link}"
        
        return await self.send_email(email, subject, html_content, text_content)
    
    async def send_welcome_email(self, email: str, user_name: str) -> Dict:
        """Send welcome email after verification"""
        subject = f"Welcome to {APP_NAME}!"
        html_content = self._get_welcome_email_template(user_name)
        text_content = f"Welcome to {APP_NAME}, {user_name}! Your account is now active."
        
        return await self.send_email(email, subject, html_content, text_content)
    
    async def send_password_reset_email(self, email: str, reset_token: str, user_name: str) -> Dict:
        """Send password reset link"""
        reset_link = f"{FRONTEND_URL}/contentry/auth/reset-password?token={reset_token}"
        
        subject = f"Reset your {APP_NAME} password"
        html_content = self._get_password_reset_template(user_name, reset_link)
        text_content = f"Hi {user_name}, reset your password: {reset_link}"
        
        return await self.send_email(email, subject, html_content, text_content)
    
    async def send_post_published_notification(self, email: str, user_name: str, post_title: str, platforms: List[str]) -> Dict:
        """Send notification when scheduled post is published"""
        platform_list = ", ".join(platforms)
        
        subject = f"Your post has been published to {platform_list}"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">✅ Post Published!</h1>
            </div>
            <div style="padding: 30px; background: #f5f5f5;">
                <h2 style="color: #333;">Hi {user_name},</h2>
                <p style="color: #666; line-height: 1.6;">
                    Your scheduled post <strong>"{post_title}"</strong> has been successfully published to: <strong>{platform_list}</strong>
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{FRONTEND_URL}/contentry/content-moderation?tab=posts" 
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Your Posts
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(email, subject, html_content)
    
    async def send_post_flagged_notification(self, email: str, user_name: str, post_title: str, reason: str) -> Dict:
        """Send notification when scheduled post is flagged during pre-publish review"""
        subject = f"⚠️ Your scheduled post was flagged"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #f59e0b; padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">⚠️ Post Flagged</h1>
            </div>
            <div style="padding: 30px; background: #f5f5f5;">
                <h2 style="color: #333;">Hi {user_name},</h2>
                <p style="color: #666; line-height: 1.6;">
                    Your scheduled post <strong>"{post_title}"</strong> was flagged during our pre-publish review and was not posted.
                </p>
                <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="color: #856404; margin: 0;"><strong>Reason:</strong> {reason}</p>
                </div>
                <p style="color: #666;">
                    Please review and update your content before rescheduling.
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{FRONTEND_URL}/contentry/content-moderation?tab=posts" 
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Review Post
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(email, subject, html_content)
    
    # ==================== EMAIL TEMPLATES ====================
    
    def _get_verification_email_template(self, user_name: str, verification_link: str) -> str:
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">{APP_NAME}</h1>
            </div>
            <div style="padding: 30px; background: #f5f5f5;">
                <h2 style="color: #333;">Welcome, {user_name}!</h2>
                <p style="color: #666; line-height: 1.6;">
                    Thank you for signing up. Please verify your email address to activate your account.
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_link}" 
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verify Email Address
                    </a>
                </div>
                <p style="color: #999; font-size: 12px;">
                    If you didn't create this account, you can safely ignore this email.
                </p>
                <p style="color: #999; font-size: 12px;">
                    Or copy this link: {verification_link}
                </p>
            </div>
        </body>
        </html>
        """
    
    def _get_welcome_email_template(self, user_name: str) -> str:
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">🎉 Welcome to {APP_NAME}!</h1>
            </div>
            <div style="padding: 30px; background: #f5f5f5;">
                <h2 style="color: #333;">Hi {user_name},</h2>
                <p style="color: #666; line-height: 1.6;">
                    Your account has been successfully verified! You're now ready to start using {APP_NAME}.
                </p>
                <h3 style="color: #333;">What you can do:</h3>
                <ul style="color: #666; line-height: 1.8;">
                    <li>Analyze content for compliance and cultural sensitivity</li>
                    <li>Generate and schedule social media posts</li>
                    <li>Monitor brand reputation and policy adherence</li>
                    <li>Get AI-powered content recommendations</li>
                </ul>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{FRONTEND_URL}/contentry/dashboard" 
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Go to Dashboard
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_password_reset_template(self, user_name: str, reset_link: str) -> str:
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">{APP_NAME}</h1>
            </div>
            <div style="padding: 30px; background: #f5f5f5;">
                <h2 style="color: #333;">Password Reset Request</h2>
                <p style="color: #666; line-height: 1.6;">
                    Hi {user_name}, we received a request to reset your password. Click the button below to create a new password.
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" 
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                <p style="color: #999; font-size: 12px;">
                    This link will expire in 1 hour. If you didn't request this, please ignore this email.
                </p>
                <p style="color: #999; font-size: 12px;">
                    Or copy this link: {reset_link}
                </p>
            </div>
        </body>
        </html>
        """
    
    # ==================== CONFIGURATION STATUS ====================
    
    def get_configuration_status(self) -> Dict:
        """Get current notification service configuration status"""
        return {
            "sms": {
                "provider": "twilio",
                "configured": self.twilio_configured,
                "verify_service": self.twilio_verify_configured,
                "features": ["sms", "otp", "verify"] if self.twilio_configured else ["mock_sms"]
            },
            "email": {
                "provider": "sendgrid",
                "configured": self.sendgrid_configured,
                "from_email": FROM_EMAIL,
                "features": ["transactional", "templates"] if self.sendgrid_configured else ["console_log"]
            }
        }


# Create singleton instance
notification_service = NotificationService()
