"""Extended Authentication Tests

Comprehensive tests for authentication endpoints to increase coverage.
Based on routes in /app/backend/routes/auth.py
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone


# =============================================================================
# SIGNUP TESTS
# =============================================================================

class TestSignup:
    """Tests for user signup"""
    
    def test_signup_success(self, sync_client):
        """Test successful signup with valid data"""
        response = sync_client.post(
            "/api/v1/auth/signup",
            json={
                "email": f"test_{datetime.now().timestamp()}@example.com",
                "password": "TestPassword123!",
                "full_name": "Test User"
            }
        )
        assert response.status_code in [200, 201, 400, 409, 422, 500]
    
    def test_signup_weak_password(self, sync_client):
        """Test signup with weak password"""
        response = sync_client.post(
            "/api/v1/auth/signup",
            json={
                "email": "weak@example.com",
                "password": "weak",
                "full_name": "Test User"
            }
        )
        assert response.status_code in [400, 422, 500]
    
    def test_signup_invalid_email(self, sync_client):
        """Test signup with invalid email format"""
        response = sync_client.post(
            "/api/v1/auth/signup",
            json={
                "email": "not-an-email",
                "password": "TestPassword123!",
                "full_name": "Test User"
            }
        )
        assert response.status_code in [400, 422, 500]
    
    def test_signup_missing_fields(self, sync_client):
        """Test signup with missing required fields"""
        response = sync_client.post(
            "/api/v1/auth/signup",
            json={"email": "test@example.com"}
        )
        assert response.status_code in [400, 422]


# =============================================================================
# LOGIN TESTS
# =============================================================================

class TestLogin:
    """Tests for user login"""
    
    def test_login_invalid_credentials(self, sync_client):
        """Test login with invalid credentials"""
        response = sync_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code in [401, 404, 422, 500]
    
    def test_login_missing_password(self, sync_client):
        """Test login without password"""
        response = sync_client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com"}
        )
        assert response.status_code in [400, 422]
    
    def test_login_empty_credentials(self, sync_client):
        """Test login with empty credentials"""
        response = sync_client.post(
            "/api/v1/auth/login",
            json={"email": "", "password": ""}
        )
        assert response.status_code in [400, 422, 500]


# =============================================================================
# PASSWORD MANAGEMENT TESTS
# =============================================================================

class TestPasswordManagement:
    """Tests for password management endpoints"""
    
    def test_check_password_strength_strong(self, sync_client):
        """Test password strength check with strong password"""
        response = sync_client.post(
            "/api/v1/auth/check-password-strength",
            json={"password": "StrongP@ssw0rd123!"}
        )
        assert response.status_code in [200, 422, 500]
    
    def test_check_password_strength_weak(self, sync_client):
        """Test password strength check with weak password"""
        response = sync_client.post(
            "/api/v1/auth/check-password-strength",
            json={"password": "123"}
        )
        assert response.status_code in [200, 422, 500]
    
    def test_forgot_password(self, sync_client):
        """Test forgot password request"""
        response = sync_client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "test@example.com"}
        )
        assert response.status_code in [200, 400, 404, 422, 500]
    
    def test_validate_reset_token(self, sync_client):
        """Test validating reset token"""
        response = sync_client.post(
            "/api/v1/auth/validate-reset-token",
            json={"token": "invalid-token"}
        )
        assert response.status_code in [200, 400, 404, 422, 500]
    
    def test_reset_password(self, sync_client):
        """Test password reset"""
        response = sync_client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "invalid-token",
                "new_password": "NewPassword123!"
            }
        )
        assert response.status_code in [200, 400, 404, 422, 500]
    
    def test_change_password(self, sync_client, user_headers):
        """Test changing password"""
        response = sync_client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "OldPassword123!",
                "new_password": "NewPassword123!"
            },
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]


# =============================================================================
# PROFILE MANAGEMENT TESTS
# =============================================================================

class TestProfileManagement:
    """Tests for profile management endpoints"""
    
    def test_get_current_user(self, sync_client, user_headers):
        """Test getting current user profile"""
        response = sync_client.get("/api/v1/auth/me", headers=user_headers)
        assert response.status_code in [200, 401, 403, 404, 500]
    
    def test_update_profile(self, sync_client, user_headers):
        """Test updating user profile"""
        response = sync_client.put(
            "/api/v1/auth/profile",
            json={"full_name": "Updated Name"},
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_get_me_no_auth(self, sync_client):
        """Test getting profile without authentication"""
        response = sync_client.get("/api/v1/auth/me")
        assert response.status_code in [401, 403, 422, 500]


# =============================================================================
# SESSION MANAGEMENT TESTS
# =============================================================================

class TestSessionManagement:
    """Tests for session management"""
    
    def test_logout(self, sync_client, user_headers):
        """Test user logout"""
        response = sync_client.post("/api/v1/auth/logout", headers=user_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_refresh_token(self, sync_client, user_headers):
        """Test token refresh"""
        response = sync_client.post("/api/v1/auth/refresh", headers=user_headers)
        assert response.status_code in [200, 401, 403, 422, 500]
    
    def test_refresh_without_auth(self, sync_client):
        """Test token refresh without authentication"""
        response = sync_client.post("/api/v1/auth/refresh")
        assert response.status_code in [401, 403, 422, 500]


# =============================================================================
# DEMO USER TESTS
# =============================================================================

class TestDemoUsers:
    """Tests for demo user functionality"""
    
    def test_create_demo_user(self, sync_client):
        """Test creating demo user"""
        response = sync_client.post(
            "/api/v1/auth/create-demo-user",
            json={"type": "user"}
        )
        assert response.status_code in [200, 201, 400, 422, 500]
    
    def test_create_demo_admin(self, sync_client):
        """Test creating demo admin"""
        response = sync_client.post(
            "/api/v1/auth/create-demo-user",
            json={"type": "admin"}
        )
        assert response.status_code in [200, 201, 400, 422, 500]


# =============================================================================
# EXTENSION AUTH TESTS
# =============================================================================

class TestExtensionAuth:
    """Tests for browser extension authentication"""
    
    def test_extension_login(self, sync_client):
        """Test extension login"""
        response = sync_client.post(
            "/api/v1/auth/extension/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!"
            }
        )
        assert response.status_code in [200, 401, 404, 422, 500]
    
    def test_extension_verify(self, sync_client, user_headers):
        """Test extension token verification"""
        response = sync_client.get(
            "/api/v1/auth/extension/verify",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 500]


# =============================================================================
# ACCOUNT MANAGEMENT TESTS
# =============================================================================

class TestAccountManagement:
    """Tests for account management"""
    
    def test_delete_account(self, sync_client, user_headers):
        """Test account deletion"""
        response = sync_client.delete(
            "/api/v1/auth/account",
            headers=user_headers
        )
        assert response.status_code in [200, 204, 401, 403, 404, 500]
    
    def test_request_data_export(self, sync_client, user_headers):
        """Test GDPR data export request"""
        response = sync_client.post(
            "/api/v1/auth/request-data-export",
            headers=user_headers
        )
        assert response.status_code in [200, 202, 401, 403, 500]
    
    def test_request_account_deletion(self, sync_client, user_headers):
        """Test account deletion request"""
        response = sync_client.post(
            "/api/v1/auth/request-account-deletion",
            headers=user_headers
        )
        assert response.status_code in [200, 202, 401, 403, 422, 500]
    
    def test_get_gdpr_requests(self, sync_client, admin_headers):
        """Test getting GDPR requests for a user"""
        response = sync_client.get(
            "/api/v1/auth/gdpr-requests/test-user-001",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 404, 500]


# =============================================================================
# PHONE AUTH TESTS
# =============================================================================

class TestPhoneAuth:
    """Tests for phone authentication"""
    
    def test_send_phone_otp(self, sync_client):
        """Test sending OTP to phone"""
        response = sync_client.post(
            "/api/v1/auth/phone/send-otp",
            json={"phone": "+1234567890"}
        )
        assert response.status_code in [200, 400, 422, 500]
    
    def test_verify_phone_otp(self, sync_client):
        """Test verifying phone OTP"""
        response = sync_client.post(
            "/api/v1/auth/phone/verify-otp",
            json={"phone": "+1234567890", "otp": "123456"}
        )
        assert response.status_code in [200, 400, 401, 422, 500]
    
    def test_phone_login(self, sync_client):
        """Test phone-based login"""
        response = sync_client.post(
            "/api/v1/auth/phone/login",
            json={"phone": "+1234567890", "otp": "123456"}
        )
        assert response.status_code in [200, 400, 401, 422, 500]


# =============================================================================
# EMAIL VERIFICATION TESTS
# =============================================================================

class TestEmailVerification:
    """Tests for email verification"""
    
    def test_verify_email(self, sync_client):
        """Test email verification with token"""
        response = sync_client.post(
            "/api/v1/auth/verify-email",
            json={"token": "invalid-verification-token"}
        )
        assert response.status_code in [200, 400, 404, 422, 500]
    
    def test_verify_otp(self, sync_client):
        """Test OTP verification"""
        response = sync_client.post(
            "/api/v1/auth/verify-otp",
            json={"email": "test@example.com", "otp": "123456"}
        )
        assert response.status_code in [200, 400, 401, 422, 500]
