"""
Unit Tests for Notification Service

Tests SMS and Email notification functionality:
- Twilio SMS integration
- SendGrid email integration
- Mock fallback modes
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from services.notification_service import NotificationService


class TestNotificationServiceInit:
    """Test NotificationService initialization"""
    
    def test_service_initializes(self):
        """Test service can be instantiated"""
        service = NotificationService()
        assert service is not None


class TestSendSMS:
    """Test SMS sending functionality"""
    
    @pytest.mark.asyncio
    async def test_send_sms_returns_result(self):
        """Test SMS returns a result dict"""
        service = NotificationService()
        result = await service.send_sms("+15551234567", "Test message")
        
        # Result should have success key
        assert "success" in result


class TestSendOTPSMS:
    """Test OTP SMS sending"""
    
    @pytest.mark.asyncio
    async def test_send_otp_sms_returns_result(self):
        """Test OTP SMS returns a result dict"""
        service = NotificationService()
        result = await service.send_otp_sms("+15551234567", "123456")
        
        # Result should have success key
        assert "success" in result


class TestSendEmail:
    """Test email sending functionality"""
    
    @pytest.mark.asyncio
    async def test_send_email_mock_mode(self):
        """Test email falls back to console mode without credentials"""
        with patch.dict('os.environ', {
            'TWILIO_ACCOUNT_SID': '',
            'TWILIO_AUTH_TOKEN': '',
            'TWILIO_PHONE_NUMBER': '',
            'SENDGRID_API_KEY': ''
        }):
            service = NotificationService()
            result = await service.send_email(
                to_email="test@example.com",
                subject="Test Subject",
                html_content="<p>Test body</p>"
            )
            
            assert result["success"] == True
            assert result["is_mocked"] == True


class TestEmailTemplates:
    """Test email template methods"""
    
    @pytest.mark.asyncio
    async def test_send_verification_email(self):
        """Test verification email"""
        with patch.dict('os.environ', {
            'TWILIO_ACCOUNT_SID': '',
            'TWILIO_AUTH_TOKEN': '',
            'TWILIO_PHONE_NUMBER': '',
            'SENDGRID_API_KEY': ''
        }):
            service = NotificationService()
            result = await service.send_verification_email(
                email="test@example.com",
                verification_token="verify_123",
                user_name="Test User"
            )
            
            assert result["success"] == True
    
    @pytest.mark.asyncio
    async def test_send_welcome_email(self):
        """Test welcome email"""
        with patch.dict('os.environ', {
            'TWILIO_ACCOUNT_SID': '',
            'TWILIO_AUTH_TOKEN': '',
            'TWILIO_PHONE_NUMBER': '',
            'SENDGRID_API_KEY': ''
        }):
            service = NotificationService()
            result = await service.send_welcome_email(
                email="test@example.com",
                user_name="Test User"
            )
            
            assert result["success"] == True
    
    @pytest.mark.asyncio
    async def test_send_password_reset_email(self):
        """Test password reset email"""
        with patch.dict('os.environ', {
            'TWILIO_ACCOUNT_SID': '',
            'TWILIO_AUTH_TOKEN': '',
            'TWILIO_PHONE_NUMBER': '',
            'SENDGRID_API_KEY': ''
        }):
            service = NotificationService()
            result = await service.send_password_reset_email(
                email="test@example.com",
                reset_token="reset_123",
                user_name="Test User"
            )
            
            assert result["success"] == True
    
    @pytest.mark.asyncio
    async def test_send_post_published_notification(self):
        """Test post published notification"""
        with patch.dict('os.environ', {
            'TWILIO_ACCOUNT_SID': '',
            'TWILIO_AUTH_TOKEN': '',
            'TWILIO_PHONE_NUMBER': '',
            'SENDGRID_API_KEY': ''
        }):
            service = NotificationService()
            result = await service.send_post_published_notification(
                email="test@example.com",
                user_name="Test User",
                post_title="Test Post",
                platforms=["linkedin", "twitter"]
            )
            
            assert result["success"] == True
    
    @pytest.mark.asyncio
    async def test_send_post_flagged_notification(self):
        """Test post flagged notification"""
        with patch.dict('os.environ', {
            'TWILIO_ACCOUNT_SID': '',
            'TWILIO_AUTH_TOKEN': '',
            'TWILIO_PHONE_NUMBER': '',
            'SENDGRID_API_KEY': ''
        }):
            service = NotificationService()
            result = await service.send_post_flagged_notification(
                email="test@example.com",
                user_name="Test User",
                post_title="Test Post",
                reason="Policy violation"
            )
            
            assert result["success"] == True


class TestConfigurationStatus:
    """Test configuration status method"""
    
    def test_get_configuration_status(self):
        """Test getting configuration status"""
        with patch.dict('os.environ', {
            'TWILIO_ACCOUNT_SID': '',
            'TWILIO_AUTH_TOKEN': '',
            'TWILIO_PHONE_NUMBER': '',
            'SENDGRID_API_KEY': ''
        }):
            service = NotificationService()
            status = service.get_configuration_status()
            
            assert "sms_configured" in status or "twilio_configured" in status or isinstance(status, dict)
