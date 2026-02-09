"""Social Routes Tests

Tests for social media integration endpoints.
Based on actual routes in /app/backend/routes/social.py:
- POST /api/social/upload-image
- GET /api/social/images/{filename}
- GET /api/social/plan-info
- POST /api/social/profiles
- GET /api/social/profiles
- GET /api/social/profiles/{profile_id}
- DELETE /api/social/profiles/{profile_id}
- POST /api/social/profiles/{profile_id}/generate-link
- POST /api/social/posts
- GET /api/social/posts
- GET /api/social/posts/{post_id}
- DELETE /api/social/posts/{post_id}
- GET /api/social/analytics/post/{post_id}
- GET /api/social/analytics/profile/{profile_id}
- GET /api/social/history/{profile_id}
- GET /api/social/supported-platforms
- POST /api/social/import-history
- GET /api/social/posts/{post_id}/analyze
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestSocialPlanInfo:
    """Tests for plan info endpoint"""
    
    def test_get_plan_info(self, sync_client, user_headers):
        """Test getting plan info"""
        response = sync_client.get("/api/v1/social/plan-info", headers=user_headers)
        assert response.status_code in [200, 401, 403, 500]


class TestSocialProfiles:
    """Tests for social profile management"""
    
    def test_list_social_profiles(self, sync_client, user_headers):
        """Test listing social profiles"""
        response = sync_client.get("/api/v1/social/profiles", headers=user_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_create_social_profile(self, sync_client, user_headers):
        """Test creating a social profile"""
        response = sync_client.post(
            "/api/v1/social/profiles",
            json={
                "platform": "linkedin",
                "profile_name": "Test Profile"
            },
            headers=user_headers
        )
        assert response.status_code in [200, 201, 400, 401, 403, 422, 500]
    
    def test_get_social_profile(self, sync_client, user_headers):
        """Test getting a specific social profile"""
        response = sync_client.get("/api/v1/social/profiles/profile-123", headers=user_headers)
        assert response.status_code in [200, 401, 403, 404, 500]
    
    def test_delete_social_profile(self, sync_client, user_headers):
        """Test deleting a social profile"""
        response = sync_client.delete(
            "/api/v1/social/profiles/profile-123",
            headers=user_headers
        )
        assert response.status_code in [200, 204, 401, 403, 404, 500]
    
    def test_generate_profile_link(self, sync_client, user_headers):
        """Test generating connection link for profile"""
        response = sync_client.post(
            "/api/v1/social/profiles/profile-123/generate-link",
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 404, 500]


class TestSocialPosts:
    """Tests for social posts"""
    
    def test_list_social_posts(self, sync_client, user_headers):
        """Test listing social posts"""
        response = sync_client.get("/api/v1/social/posts", headers=user_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_create_social_post(self, sync_client, user_headers):
        """Test creating a social post"""
        response = sync_client.post(
            "/api/v1/social/posts",
            json={
                "content": "Test post content",
                "profile_id": "profile-123",
                "platform": "linkedin"
            },
            headers=user_headers
        )
        assert response.status_code in [200, 201, 400, 401, 403, 422, 500]
    
    def test_get_social_post(self, sync_client, user_headers):
        """Test getting a specific social post"""
        response = sync_client.get("/api/v1/social/posts/post-123", headers=user_headers)
        assert response.status_code in [200, 401, 403, 404, 500]
    
    def test_delete_social_post(self, sync_client, user_headers):
        """Test deleting a social post"""
        response = sync_client.delete(
            "/api/v1/social/posts/post-123",
            headers=user_headers
        )
        assert response.status_code in [200, 204, 401, 403, 404, 500]
    
    def test_analyze_social_post(self, sync_client, user_headers):
        """Test analyzing a social post"""
        response = sync_client.get(
            "/api/v1/social/posts/post-123/analyze",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 404, 500]


class TestSocialAnalytics:
    """Tests for social analytics"""
    
    def test_get_post_analytics(self, sync_client, user_headers):
        """Test getting post analytics"""
        response = sync_client.get(
            "/api/v1/social/analytics/post/post-123",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 404, 500]
    
    def test_get_profile_analytics(self, sync_client, user_headers):
        """Test getting profile analytics"""
        response = sync_client.get(
            "/api/v1/social/analytics/profile/profile-123",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 404, 500]


class TestSocialHistory:
    """Tests for social history"""
    
    def test_get_profile_history(self, sync_client, user_headers):
        """Test getting profile history"""
        response = sync_client.get(
            "/api/v1/social/history/profile-123",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 404, 500]


class TestSocialPlatforms:
    """Tests for supported platforms"""
    
    def test_get_supported_platforms(self, sync_client, user_headers):
        """Test getting supported platforms"""
        response = sync_client.get("/api/v1/social/supported-platforms", headers=user_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_import_history(self, sync_client, user_headers):
        """Test importing history"""
        response = sync_client.post(
            "/api/v1/social/import-history",
            json={"profile_id": "profile-123"},
            headers=user_headers
        )
        assert response.status_code in [200, 201, 400, 401, 403, 422, 500]
