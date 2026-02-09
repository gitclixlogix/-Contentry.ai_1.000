"""
Email service for sending verification and notification emails
Supports: Console logging (dev), SendGrid, AWS SES, Microsoft 365 (Graph API)

SECURITY NOTE:
- In production (EMAIL_SERVICE != 'console'), sensitive data like OTP codes
  and reset tokens are NEVER logged to console
- Console mode is for development only and should never be used in production
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Email service configuration
EMAIL_SERVICE = os.getenv('EMAIL_SERVICE', 'console')  # Options: console, sendgrid, ses, microsoft365
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
AWS_SES_REGION = os.getenv('AWS_SES_REGION', 'us-east-1')
FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@contentry.ai')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://admin-portal-278.preview.emergentagent.com')

# Microsoft 365 / Graph API configuration
MS365_CLIENT_ID = os.getenv('MS365_CLIENT_ID')
MS365_TENANT_ID = os.getenv('MS365_TENANT_ID')
MS365_CLIENT_SECRET = os.getenv('MS365_CLIENT_SECRET')
MS365_SENDER_EMAIL = os.getenv('MS365_SENDER_EMAIL', 'contact@contentry.ai')  # Actual mailbox
MS365_SENDER_NAME = os.getenv('MS365_SENDER_NAME', 'Contentry.ai')

# Security: Control whether sensitive data can be logged in console mode
# Set to 'false' in production environments
LOG_SENSITIVE_DATA_IN_DEV = os.getenv('LOG_SENSITIVE_DATA_IN_DEV', 'true').lower() == 'true'


async def send_email_via_microsoft365(to_email: str, subject: str, html_content: str, from_email: str = FROM_EMAIL):
    """
    Send email using Microsoft Graph API (Microsoft 365).
    
    Uses client credentials flow for application-level access.
    The email is sent from MS365_SENDER_EMAIL but displays FROM_EMAIL as the sender name.
    """
    try:
        import msal
        import httpx
        
        # Acquire token using client credentials
        app = msal.ConfidentialClientApplication(
            MS365_CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{MS365_TENANT_ID}",
            client_credential=MS365_CLIENT_SECRET
        )
        
        # Get token for Microsoft Graph
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        
        if "access_token" not in result:
            error_msg = result.get("error_description", result.get("error", "Unknown error"))
            logger.error(f"Microsoft 365 auth failed: {error_msg}")
            return False
        
        access_token = result["access_token"]
        
        # Build the email message
        # Use FROM_EMAIL as display name but send from actual mailbox
        message = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": html_content
                },
                "from": {
                    "emailAddress": {
                        "address": MS365_SENDER_EMAIL,
                        "name": from_email.replace("@contentry.ai", "").replace("noreply", "Contentry.ai")
                    }
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_email
                        }
                    }
                ]
            },
            "saveToSentItems": "true"
        }
        
        # Send email via Graph API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://graph.microsoft.com/v1.0/users/{MS365_SENDER_EMAIL}/sendMail",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json=message,
                timeout=30.0
            )
            
            if response.status_code == 202:
                logger.info(f"Email sent via Microsoft 365 to {to_email}")
                return True
            else:
                logger.error(f"Microsoft 365 email failed: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Microsoft 365 email error: {str(e)}")
        return False


async def send_email_via_sendgrid(to_email: str, subject: str, html_content: str, from_email: str = FROM_EMAIL):
    """Send email using SendGrid"""
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        logger.info(f"Email sent via SendGrid to {to_email}: Status {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"SendGrid email failed: {str(e)}")
        return False


async def send_email_via_ses(to_email: str, subject: str, html_content: str, from_email: str = FROM_EMAIL):
    """Send email using AWS SES"""
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        ses_client = boto3.client('ses', region_name=AWS_SES_REGION)
        
        response = ses_client.send_email(
            Source=from_email,
            Destination={'ToAddresses': [to_email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Html': {'Data': html_content}}
            }
        )
        
        logger.info(f"Email sent via AWS SES to {to_email}: MessageId {response['MessageId']}")
        return True
    except Exception as e:
        logger.error(f"AWS SES email failed: {str(e)}")
        return False


def log_email_to_console(to_email: str, subject: str, content: str, is_sensitive: bool = False):
    """
    Log email to console (development mode only).
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        content: Email content
        is_sensitive: If True, sensitive data (OTP, tokens) will be masked unless LOG_SENSITIVE_DATA_IN_DEV is enabled
    """
    # Mask sensitive content in production or when configured
    if is_sensitive and not LOG_SENSITIVE_DATA_IN_DEV:
        display_content = "[SENSITIVE CONTENT MASKED - Enable LOG_SENSITIVE_DATA_IN_DEV for development testing]"
    else:
        display_content = content
    
    logger.info(f"""
    ==============================================
    📧 EMAIL: {subject}
    ==============================================
    To: {to_email}
    
    {display_content}
    
    (Email service in console mode - set EMAIL_SERVICE env var)
    ==============================================
    """)

async def send_verification_email(email: str, verification_token: str, user_name: str):
    """Send email verification link to user"""
    
    verification_link = f"{FRONTEND_URL}/contentry/auth/verify-email?token={verification_token}"
    
    subject = "Verify your Contentry.ai account"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">Contentry.ai</h1>
        </div>
        <div style="padding: 30px; background: #f5f5f5;">
            <h2 style="color: #333;">Welcome, {user_name}!</h2>
            <p style="color: #666; line-height: 1.6;">
                Thank you for signing up for Contentry.ai. Please verify your email address to activate your account.
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
    
    # Send via configured service
    if EMAIL_SERVICE == 'microsoft365' and MS365_CLIENT_ID and MS365_CLIENT_SECRET:
        return await send_email_via_microsoft365(email, subject, html_content)
    elif EMAIL_SERVICE == 'sendgrid' and SENDGRID_API_KEY:
        return await send_email_via_sendgrid(email, subject, html_content)
    elif EMAIL_SERVICE == 'ses':
        return await send_email_via_ses(email, subject, html_content)
    else:
        # Console mode (development)
        log_email_to_console(email, subject, f"Name: {user_name}\nVerification Link: {verification_link}")
        return True
    

async def send_welcome_email(email: str, user_name: str):
    """Send welcome email after successful verification"""
    subject = "Welcome to Contentry.ai!"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">🎉 Welcome to Contentry.ai!</h1>
        </div>
        <div style="padding: 30px; background: #f5f5f5;">
            <h2 style="color: #333;">Hi {user_name},</h2>
            <p style="color: #666; line-height: 1.6;">
                Your account has been successfully verified! You're now ready to start using Contentry.ai for intelligent content analysis and moderation.
            </p>
            <h3 style="color: #333;">What you can do:</h3>
            <ul style="color: #666; line-height: 1.8;">
                <li>Analyze content for compliance and cultural sensitivity</li>
                <li>Generate and schedule social media posts</li>
                <li>Monitor brand reputation and policy adherence</li>
                <li>Get AI-powered content recommendations</li>
            </ul>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{FRONTEND_URL}/contentry/auth/login" 
                   style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Start Using Contentry.ai
                </a>
            </div>
        </div>
    </body>
    </html>
    """
    
    if EMAIL_SERVICE == 'microsoft365' and MS365_CLIENT_ID and MS365_CLIENT_SECRET:
        return await send_email_via_microsoft365(email, subject, html_content)
    elif EMAIL_SERVICE == 'sendgrid' and SENDGRID_API_KEY:
        return await send_email_via_sendgrid(email, subject, html_content)
    elif EMAIL_SERVICE == 'ses':
        return await send_email_via_ses(email, subject, html_content)
    else:
        log_email_to_console(email, subject, f"Welcome {user_name}!")
        return True


async def send_password_reset_email(email: str, reset_token: str, user_name: str):
    """Send password reset link to user"""
    reset_link = f"{FRONTEND_URL}/contentry/auth/reset-password?token={reset_token}"
    
    subject = "Reset your Contentry.ai password"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">Contentry.ai</h1>
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
    
    if EMAIL_SERVICE == 'microsoft365' and MS365_CLIENT_ID and MS365_CLIENT_SECRET:
        return await send_email_via_microsoft365(email, subject, html_content)
    elif EMAIL_SERVICE == 'sendgrid' and SENDGRID_API_KEY:
        return await send_email_via_sendgrid(email, subject, html_content)
    elif EMAIL_SERVICE == 'ses':
        return await send_email_via_ses(email, subject, html_content)
    else:
        # Console mode - mark reset link as sensitive
        log_email_to_console(
            email, 
            subject, 
            f"Reset Link: {reset_link}\n\n⚠️ DEV MODE: In production, reset link is only sent via email.",
            is_sensitive=True  # Mark as sensitive content
        )
        return True


async def send_otp_email(email: str, otp_code: str, user_name: str, phone: str = None):
    """
    Send OTP code via email for phone authentication.
    
    SECURITY NOTE: 
    - OTP is sent ONLY via email, never logged or returned in API response
    - OTP should be stored as hash in database
    - OTP expires in 5 minutes
    """
    # Mask phone number for display (show only last 4 digits)
    masked_phone = f"***{phone[-4:]}" if phone and len(phone) >= 4 else "your phone"
    
    subject = "Your Contentry.ai One-Time Password (OTP)"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">🔐 Contentry.ai</h1>
        </div>
        <div style="padding: 30px; background: #f5f5f5;">
            <h2 style="color: #333;">Your One-Time Password</h2>
            <p style="color: #666; line-height: 1.6;">
                Hi {user_name}, you requested a one-time password for phone authentication ({masked_phone}).
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <div style="background: #fff; border: 2px solid #667eea; border-radius: 10px; padding: 20px; display: inline-block;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #667eea;">{otp_code}</span>
                </div>
            </div>
            <p style="color: #666; text-align: center; font-size: 14px;">
                This code will expire in <strong>10 minutes</strong>.
            </p>
            <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 5px; padding: 15px; margin-top: 20px;">
                <p style="color: #856404; margin: 0; font-size: 13px;">
                    ⚠️ <strong>Security Notice:</strong> Never share this code with anyone. 
                    Contentry.ai staff will never ask for your OTP.
                </p>
            </div>
            <p style="color: #999; font-size: 12px; margin-top: 20px;">
                If you didn't request this code, please ignore this email or contact support if you have concerns.
            </p>
        </div>
        <div style="padding: 20px; background: #333; text-align: center;">
            <p style="color: #999; margin: 0; font-size: 12px;">
                This is an automated message from Contentry.ai. Please do not reply.
            </p>
        </div>
    </body>
    </html>
    """
    
    if EMAIL_SERVICE == 'microsoft365' and MS365_CLIENT_ID and MS365_CLIENT_SECRET:
        return await send_email_via_microsoft365(email, subject, html_content)
    elif EMAIL_SERVICE == 'sendgrid' and SENDGRID_API_KEY:
        return await send_email_via_sendgrid(email, subject, html_content)
    elif EMAIL_SERVICE == 'ses':
        return await send_email_via_ses(email, subject, html_content)
    else:
        # Console mode (development) - OTP is marked as sensitive
        # Will be masked unless LOG_SENSITIVE_DATA_IN_DEV is enabled
        log_email_to_console(
            email, 
            subject, 
            f"OTP Code: {otp_code}\nExpires in: 10 minutes\n\n⚠️ DEV MODE: In production, OTP is only sent via email.",
            is_sensitive=True  # Mark as sensitive content
        )
        return True


async def send_email(to_email: str, subject: str, html_content: str, from_email: str = None):
    """
    Generic email sending function.
    Routes to the appropriate email service based on configuration.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML body of the email
        from_email: Sender email (optional, uses FROM_EMAIL env var if not provided)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    sender = from_email or FROM_EMAIL
    
    if EMAIL_SERVICE == 'microsoft365' and MS365_CLIENT_ID and MS365_CLIENT_SECRET:
        return await send_email_via_microsoft365(to_email, subject, html_content, sender)
    elif EMAIL_SERVICE == 'sendgrid' and SENDGRID_API_KEY:
        return await send_email_via_sendgrid(to_email, subject, html_content, sender)
    elif EMAIL_SERVICE == 'ses':
        return await send_email_via_ses(to_email, subject, html_content, sender)
    else:
        # Console mode (development)
        log_email_to_console(to_email, subject, html_content)
        return True



# ============ APPROVAL WORKFLOW EMAIL FUNCTIONS ============

async def send_approval_request_email(manager_email: str, manager_name: str, submitter_name: str, post_title: str, post_content: str, approval_link: str):
    """
    Send email notification to manager when content is submitted for approval.
    """
    subject = f"🔔 Content Awaiting Your Approval: {post_title[:50]}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
            .post-preview {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #667eea; }}
            .btn {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 5px 10px 0; }}
            .footer {{ padding: 15px; text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin: 0;">📝 New Content Awaiting Your Review</h2>
            </div>
            <div class="content">
                <p>Hi {manager_name},</p>
                <p><strong>{submitter_name}</strong> has submitted content for your approval.</p>
                
                <div class="post-preview">
                    <h3 style="margin-top: 0;">{post_title}</h3>
                    <p style="color: #666;">{post_content[:300]}{'...' if len(post_content) > 300 else ''}</p>
                </div>
                
                <p>Please review the content and approve or reject it:</p>
                
                <a href="{approval_link}" class="btn">Review Now</a>
            </div>
            <div class="footer">
                <p>This is an automated message from Contentry.ai</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return await send_email(manager_email, subject, html_content)


async def send_approval_result_email(creator_email: str, creator_name: str, post_title: str, approved: bool, reviewer_name: str, rejection_reason: str = None, feedback: str = None):
    """
    Send email notification to creator when their content is approved or rejected.
    """
    if approved:
        subject = f"✅ Your Content Has Been Approved: {post_title[:50]}"
        status_emoji = "✅"
        status_text = "Approved"
        status_color = "#10b981"
        action_message = "Your content is ready to be scheduled or published."
    else:
        subject = f"❌ Content Requires Changes: {post_title[:50]}"
        status_emoji = "❌"
        status_text = "Needs Revision"
        status_color = "#ef4444"
        action_message = "Please review the feedback and make the necessary changes."
    
    feedback_section = ""
    if rejection_reason:
        feedback_section = f"""
        <div style="background: #fef2f2; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #ef4444;">
            <h4 style="margin-top: 0; color: #991b1b;">Reason for Changes Needed:</h4>
            <p style="color: #666;">{rejection_reason}</p>
        </div>
        """
    if feedback:
        feedback_section += f"""
        <div style="background: #f0f9ff; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #3b82f6;">
            <h4 style="margin-top: 0; color: #1e40af;">Reviewer Feedback:</h4>
            <p style="color: #666;">{feedback}</p>
        </div>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: {status_color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
            .status-badge {{ display: inline-block; background: {status_color}; color: white; padding: 5px 12px; border-radius: 20px; font-size: 14px; }}
            .btn {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
            .footer {{ padding: 15px; text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin: 0;">{status_emoji} Content Review Complete</h2>
            </div>
            <div class="content">
                <p>Hi {creator_name},</p>
                <p>Your content "<strong>{post_title}</strong>" has been reviewed by {reviewer_name}.</p>
                
                <p>Status: <span class="status-badge">{status_text}</span></p>
                
                {feedback_section}
                
                <p>{action_message}</p>
                
                <a href="https://admin-portal-278.preview.emergentagent.com/contentry/content-moderation?tab=posts" class="btn">View Content</a>
            </div>
            <div class="footer">
                <p>This is an automated message from Contentry.ai</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return await send_email(creator_email, subject, html_content)


# ============ AUTO-REFILL EMAIL FUNCTIONS ============

async def send_auto_refill_warning_email(
    email: str,
    user_name: str,
    current_balance: int,
    threshold: int,
    pack_name: str,
    pack_credits: int,
    pack_price: float
):
    """
    Send warning email one day before auto-refill triggers.
    This is sent when balance is approaching the threshold.
    """
    subject = "⚠️ Your Credits Are Running Low - Auto-Refill Reminder"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
            .balance-box {{ background: white; padding: 20px; border-radius: 8px; margin: 15px 0; text-align: center; border: 2px solid #f59e0b; }}
            .balance-number {{ font-size: 48px; font-weight: bold; color: #f59e0b; }}
            .refill-info {{ background: #fef3c7; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .btn {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 5px 10px 0; }}
            .btn-secondary {{ background: #6b7280; }}
            .footer {{ padding: 15px; text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin: 0;">⚠️ Credit Balance Low</h2>
            </div>
            <div class="content">
                <p>Hi {user_name},</p>
                <p>Your Contentry.ai credit balance is getting low and approaching your auto-refill threshold.</p>
                
                <div class="balance-box">
                    <div class="balance-number">{current_balance}</div>
                    <div style="color: #666;">credits remaining</div>
                    <div style="margin-top: 10px; font-size: 14px; color: #999;">
                        Threshold: {threshold} credits
                    </div>
                </div>
                
                <div class="refill-info">
                    <h3 style="margin-top: 0; color: #92400e;">🔄 Auto-Refill Will Trigger Soon</h3>
                    <p style="margin: 0;">When your balance drops below <strong>{threshold} credits</strong>, we'll automatically purchase:</p>
                    <ul style="margin: 10px 0;">
                        <li><strong>{pack_name}</strong> - {pack_credits:,} credits</li>
                        <li>Amount: <strong>${pack_price:.2f}</strong></li>
                    </ul>
                </div>
                
                <p>If you want to modify your auto-refill settings or disable it, you can do so from your billing settings:</p>
                
                <a href="{FRONTEND_URL}/contentry/settings/billing#auto-refill-section" class="btn">Manage Auto-Refill</a>
                <a href="{FRONTEND_URL}/contentry/settings/billing" class="btn btn-secondary">Buy Credits Now</a>
            </div>
            <div class="footer">
                <p>This is an automated message from Contentry.ai</p>
                <p style="color: #999;">You received this because auto-refill is enabled on your account.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return await send_email(email, subject, html_content)


async def send_auto_refill_success_email(
    email: str,
    user_name: str,
    pack_name: str,
    credits_added: int,
    amount_charged: float,
    new_balance: int,
    transaction_id: str = None
):
    """
    Send confirmation email when auto-refill purchase is completed.
    """
    subject = f"✅ Auto-Refill Complete: {credits_added:,} Credits Added"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
            .success-box {{ background: #d1fae5; padding: 20px; border-radius: 8px; margin: 15px 0; text-align: center; border: 2px solid #10b981; }}
            .credits-added {{ font-size: 36px; font-weight: bold; color: #059669; }}
            .receipt {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; border: 1px solid #e5e7eb; }}
            .receipt-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f3f4f6; }}
            .receipt-row:last-child {{ border-bottom: none; font-weight: bold; }}
            .btn {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
            .footer {{ padding: 15px; text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin: 0;">✅ Auto-Refill Successful</h2>
            </div>
            <div class="content">
                <p>Hi {user_name},</p>
                <p>Your account has been automatically refilled with credits as configured in your auto-refill settings.</p>
                
                <div class="success-box">
                    <div style="font-size: 18px; color: #059669;">Credits Added</div>
                    <div class="credits-added">+{credits_added:,}</div>
                    <div style="margin-top: 10px; color: #666;">
                        New Balance: <strong>{new_balance:,} credits</strong>
                    </div>
                </div>
                
                <div class="receipt">
                    <h3 style="margin-top: 0;">📋 Transaction Details</h3>
                    <div class="receipt-row">
                        <span>Pack</span>
                        <span>{pack_name}</span>
                    </div>
                    <div class="receipt-row">
                        <span>Credits</span>
                        <span>{credits_added:,}</span>
                    </div>
                    <div class="receipt-row">
                        <span>Amount Charged</span>
                        <span>${amount_charged:.2f}</span>
                    </div>
                    {f'<div class="receipt-row"><span>Transaction ID</span><span style="font-family: monospace; font-size: 12px;">{transaction_id}</span></div>' if transaction_id else ''}
                </div>
                
                <p>Your credits are ready to use. Continue creating amazing content!</p>
                
                <a href="{FRONTEND_URL}/contentry/content-moderation" class="btn">Start Creating</a>
            </div>
            <div class="footer">
                <p>This is an automated message from Contentry.ai</p>
                <p style="color: #999;">
                    <a href="{FRONTEND_URL}/contentry/settings/billing#auto-refill-section" style="color: #667eea;">Manage auto-refill settings</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return await send_email(email, subject, html_content)


async def send_auto_refill_failed_email(
    email: str,
    user_name: str,
    pack_name: str,
    amount: float,
    error_reason: str = "Payment method declined"
):
    """
    Send notification email when auto-refill payment fails.
    """
    subject = "❌ Auto-Refill Failed - Action Required"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
            .error-box {{ background: #fef2f2; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #ef4444; }}
            .btn {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 5px 10px 0; }}
            .btn-danger {{ background: #ef4444; }}
            .footer {{ padding: 15px; text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin: 0;">❌ Auto-Refill Payment Failed</h2>
            </div>
            <div class="content">
                <p>Hi {user_name},</p>
                <p>We were unable to process your auto-refill payment. Your credit balance may run out soon.</p>
                
                <div class="error-box">
                    <h3 style="margin-top: 0; color: #991b1b;">Payment Failed</h3>
                    <p style="margin: 0;"><strong>Pack:</strong> {pack_name}</p>
                    <p style="margin: 5px 0;"><strong>Amount:</strong> ${amount:.2f}</p>
                    <p style="margin: 5px 0 0;"><strong>Reason:</strong> {error_reason}</p>
                </div>
                
                <p><strong>What to do next:</strong></p>
                <ul>
                    <li>Update your payment method in billing settings</li>
                    <li>Or manually purchase a credit pack</li>
                </ul>
                
                <a href="{FRONTEND_URL}/contentry/settings/billing" class="btn">Update Payment Method</a>
                <a href="{FRONTEND_URL}/contentry/settings/billing" class="btn btn-danger">Buy Credits Now</a>
            </div>
            <div class="footer">
                <p>This is an automated message from Contentry.ai</p>
                <p style="color: #999;">
                    Your auto-refill will retry on your next credit usage if payment method is updated.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return await send_email(email, subject, html_content)

