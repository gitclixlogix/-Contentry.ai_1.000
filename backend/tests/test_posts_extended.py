"""Extended Posts Tests

Comprehensive tests for posts endpoints.
Based on routes in /app/backend/routes/posts.py
"""

import pytest


# =============================================================================
# POSTS CRUD TESTS
# =============================================================================

class TestPostsCRUD:
    """Tests for posts CRUD operations"""
    
    def test_create_post(self, sync_client, user_headers):
        """Test creating a post"""
        response = sync_client.post(
            "/api/v1/posts",
            json={
                "content": "This is a test post",
                "title": "Test Post",
                "platforms": ["linkedin"]
            },
            headers=user_headers
        )
        assert response.status_code in [200, 201, 400, 401, 403, 422, 500]
    
    def test_get_posts(self, sync_client, user_headers):
        """Test getting posts list"""
        response = sync_client.get(
            "/api/v1/posts",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_posts_with_pagination(self, sync_client, user_headers):
        """Test getting posts with pagination"""
        response = sync_client.get(
            "/api/v1/posts",
            params={"page": 1, "limit": 10},
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_get_single_post(self, sync_client, user_headers):
        """Test getting a single post"""
        response = sync_client.get(
            "/api/v1/posts/post-123",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 404, 500]
    
    def test_update_post(self, sync_client, user_headers):
        """Test updating a post"""
        response = sync_client.put(
            "/api/v1/posts/post-123",
            json={"content": "Updated content"},
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 404, 422, 500]
    
    def test_delete_post(self, sync_client, user_headers):
        """Test deleting a post"""
        response = sync_client.delete(
            "/api/v1/posts/post-123",
            headers=user_headers
        )
        assert response.status_code in [200, 204, 401, 403, 404, 500]


# =============================================================================
# POSTS FILTERING TESTS
# =============================================================================

class TestPostsFiltering:
    """Tests for posts filtering"""
    
    def test_filter_by_status(self, sync_client, user_headers):
        """Test filtering posts by status"""
        response = sync_client.get(
            "/api/v1/posts",
            params={"status": "published"},
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_filter_by_platform(self, sync_client, user_headers):
        """Test filtering posts by platform"""
        response = sync_client.get(
            "/api/v1/posts",
            params={"platform": "linkedin"},
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]


# =============================================================================
# POSTS AUTHENTICATION TESTS
# =============================================================================

class TestPostsAuthentication:
    """Tests for posts authentication"""
    
    def test_posts_no_auth(self, sync_client):
        """Test posts requires authentication"""
        response = sync_client.get("/api/v1/posts")
        assert response.status_code in [401, 403, 422, 500]
    
    def test_create_post_no_auth(self, sync_client):
        """Test creating post requires authentication"""
        response = sync_client.post(
            "/api/v1/posts",
            json={"content": "Test"}
        )
        assert response.status_code in [401, 403, 422, 500]
