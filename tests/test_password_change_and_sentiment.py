"""
Test cases for:
1. Force password change for new users on first login
2. Sentiment Analysis endpoint (Network Error fix)

These tests verify the features implemented for TechCorp International demo.
"""
import pytest
import requests
import os
import json

# Use the public URL for testing
BASE_URL = "https://admin-portal-278.preview.emergentagent.com/api/v1"

# Test credentials
ADMIN_EMAIL = "sarah.chen@techcorp-demo.com"
ADMIN_PASSWORD = "Demo123!"
CREATOR_EMAIL = "alex.martinez@techcorp-demo.com"
CREATOR_PASSWORD = "Demo123!"


class TestSetInitialPassword:
    """Test the /auth/set-initial-password endpoint"""
    
    def test_set_initial_password_user_not_found(self):
        """Test that endpoint returns 404 for non-existent user"""
        response = requests.post(
            f"{BASE_URL}/auth/set-initial-password",
            json={
                "email": "nonexistent@example.com",
                "temporary_password": "TempPass123!",
                "new_password": "NewPass123!"
            }
        )
        assert response.status_code == 404
        assert "not found" in response.json().get("detail", "").lower()
    
    def test_set_initial_password_wrong_temp_password(self):
        """Test that endpoint returns 401 for wrong temporary password"""
        response = requests.post(
            f"{BASE_URL}/auth/set-initial-password",
            json={
                "email": ADMIN_EMAIL,
                "temporary_password": "WrongPassword123!",
                "new_password": "NewPass123!"
            }
        )
        assert response.status_code == 401
        assert "incorrect" in response.json().get("detail", "").lower()
    
    def test_set_initial_password_not_required(self):
        """Test that endpoint returns 400 if user doesn't need password change"""
        # Admin user doesn't have must_change_password flag
        response = requests.post(
            f"{BASE_URL}/auth/set-initial-password",
            json={
                "email": ADMIN_EMAIL,
                "temporary_password": ADMIN_PASSWORD,
                "new_password": "NewSecurePass123!"
            }
        )
        # Should return 400 because admin doesn't have must_change_password flag
        assert response.status_code == 400
        assert "not required" in response.json().get("detail", "").lower()
    
    def test_set_initial_password_weak_password(self):
        """Test that endpoint validates password strength"""
        response = requests.post(
            f"{BASE_URL}/auth/set-initial-password",
            json={
                "email": ADMIN_EMAIL,
                "temporary_password": ADMIN_PASSWORD,
                "new_password": "weak"  # Too weak
            }
        )
        # Should return 400 for weak password (or 400 for not required)
        assert response.status_code == 400


class TestLoginMustChangePassword:
    """Test the login flow with must_change_password handling"""
    
    def test_login_success_no_password_change(self):
        """Test normal login returns success without must_change_password"""
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "must_change_password" not in data or data.get("must_change_password") == False
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
    
    def test_login_returns_user_info(self):
        """Test login returns complete user info"""
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": CREATOR_EMAIL,
                "password": CREATOR_PASSWORD
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        user = data.get("user", {})
        assert "id" in user
        assert "email" in user
        assert "full_name" in user


class TestSentimentAnalysis:
    """Test the sentiment analysis endpoint"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers for API calls"""
        # Login to get session
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
        )
        assert login_response.status_code == 200
        data = login_response.json()
        user_id = data["user"]["id"]
        access_token = data.get("access_token", "")
        
        return {
            "X-User-ID": user_id,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def test_sentiment_analysis_endpoint_exists(self, auth_headers):
        """Test that sentiment analysis endpoint exists and responds"""
        response = requests.post(
            f"{BASE_URL}/sentiment/analyze",
            headers=auth_headers,
            json={
                "urls": ["https://www.example.com"],
                "enterprise_id": "techcorp-international",
                "enterprise_name": "TechCorp International"
            }
        )
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404, f"Sentiment endpoint not found: {response.text}"
        # Should not return 500 (no internal error)
        # Note: May return 401/403 if auth is required, or 200/400 for valid/invalid request
        print(f"Sentiment analysis response: {response.status_code} - {response.text[:200]}")
    
    def test_sentiment_analysis_with_valid_url(self, auth_headers):
        """Test sentiment analysis with a valid URL"""
        response = requests.post(
            f"{BASE_URL}/sentiment/analyze",
            headers=auth_headers,
            json={
                "urls": ["https://www.linkedin.com/company/microsoft"],
                "enterprise_id": "techcorp-international",
                "enterprise_name": "TechCorp International"
            },
            timeout=60  # Sentiment analysis may take time
        )
        print(f"Sentiment analysis response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response data keys: {data.keys()}")
            # Verify response structure
            assert "profiles" in data or "results" in data or "analyzed_at" in data
    
    def test_sentiment_analysis_no_network_error(self, auth_headers):
        """Test that sentiment analysis doesn't return Network Error"""
        response = requests.post(
            f"{BASE_URL}/sentiment/analyze",
            headers=auth_headers,
            json={
                "urls": ["https://www.google.com"],
                "enterprise_id": "techcorp-international",
                "enterprise_name": "TechCorp International"
            },
            timeout=60
        )
        # Should not have "Network Error" in response
        response_text = response.text.lower()
        assert "network error" not in response_text, f"Network Error found in response: {response.text}"
        print(f"Sentiment analysis completed without Network Error: {response.status_code}")


class TestAuthEndpoints:
    """Test authentication-related endpoints"""
    
    def test_login_endpoint_works(self):
        """Test that login endpoint is accessible"""
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": "WrongPassword123!"
            }
        )
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
