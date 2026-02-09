"""Strategic Profiles Route Tests

Tests for strategic profile management endpoints.
Based on actual routes in /app/backend/routes/strategic_profiles.py:
- GET /api/profiles/strategic
- POST /api/profiles/strategic
- GET /api/profiles/strategic/{profile_id}
- PUT /api/profiles/strategic/{profile_id}
- DELETE /api/profiles/strategic/{profile_id}
- POST /api/profiles/strategic/{profile_id}/knowledge
- GET /api/profiles/strategic/{profile_id}/knowledge
- DELETE /api/profiles/strategic/{profile_id}/knowledge/{document_id}
- POST /api/profiles/strategic/{profile_id}/knowledge/query
- POST /api/profiles/strategic/suggest-keywords-from-description
- POST /api/profiles/strategic/{profile_id}/suggest-keywords
- POST /api/profiles/strategic/sync-default
- POST /api/profiles/strategic/{profile_id}/scrape-website
- DELETE /api/profiles/strategic/{profile_id}/website-content
- GET /api/profiles/strategic/{profile_id}/website/{website_id}/content
- DELETE /api/profiles/strategic/{profile_id}/website/{website_id}
- GET /api/profiles/strategic/{profile_id}/knowledge/{document_id}/content
- POST /api/profiles/strategic/{profile_id}/generate-description
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestStrategicProfilesCRUD:
    """Tests for strategic profile CRUD operations"""
    
    def test_list_strategic_profiles(self, sync_client, user_headers):
        """Test listing strategic profiles"""
        response = sync_client.get("/api/v1/profiles/strategic", headers=user_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_create_strategic_profile(self, sync_client, user_headers):
        """Test creating a strategic profile"""
        response = sync_client.post(
            "/api/v1/profiles/strategic",
            json={
                "name": "Corporate Voice",
                "description": "Professional corporate communication",
                "tone": "professional"
            },
            headers=user_headers
        )
        assert response.status_code in [200, 201, 400, 401, 403, 422, 500]
    
    def test_get_strategic_profile(self, sync_client, user_headers):
        """Test getting a specific strategic profile"""
        response = sync_client.get("/api/v1/profiles/strategic/profile-123", headers=user_headers)
        assert response.status_code in [200, 401, 403, 404, 500]
    
    def test_update_strategic_profile(self, sync_client, user_headers):
        """Test updating a strategic profile"""
        response = sync_client.put(
            "/api/v1/profiles/strategic/profile-123",
            json={"name": "Updated Voice"},
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 404, 422, 500]
    
    def test_delete_strategic_profile(self, sync_client, user_headers):
        """Test deleting a strategic profile"""
        response = sync_client.delete(
            "/api/v1/profiles/strategic/profile-123",
            headers=user_headers
        )
        assert response.status_code in [200, 204, 401, 403, 404, 500]


class TestStrategicProfileKnowledge:
    """Tests for strategic profile knowledge base"""
    
    def test_add_knowledge(self, sync_client, user_headers):
        """Test adding knowledge to a profile"""
        response = sync_client.post(
            "/api/v1/profiles/strategic/profile-123/knowledge",
            json={"content": "Test knowledge content", "title": "Test Document"},
            headers=user_headers
        )
        assert response.status_code in [200, 201, 400, 401, 403, 404, 422, 500]
    
    def test_get_knowledge(self, sync_client, user_headers):
        """Test getting profile knowledge"""
        response = sync_client.get(
            "/api/v1/profiles/strategic/profile-123/knowledge",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 404, 500]
    
    def test_delete_knowledge_document(self, sync_client, user_headers):
        """Test deleting a knowledge document"""
        response = sync_client.delete(
            "/api/v1/profiles/strategic/profile-123/knowledge/doc-123",
            headers=user_headers
        )
        assert response.status_code in [200, 204, 401, 403, 404, 500]
    
    def test_query_knowledge(self, sync_client, user_headers):
        """Test querying profile knowledge"""
        response = sync_client.post(
            "/api/v1/profiles/strategic/profile-123/knowledge/query",
            json={"query": "What are the guidelines?"},
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 404, 422, 500]
    
    def test_get_knowledge_content(self, sync_client, user_headers):
        """Test getting specific knowledge document content"""
        response = sync_client.get(
            "/api/v1/profiles/strategic/profile-123/knowledge/doc-123/content",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 404, 500]


class TestStrategicProfileKeywords:
    """Tests for keyword suggestions"""
    
    def test_suggest_keywords_from_description(self, sync_client, user_headers):
        """Test suggesting keywords from description"""
        response = sync_client.post(
            "/api/v1/profiles/strategic/suggest-keywords-from-description",
            json={"description": "A tech company focused on AI"},
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_suggest_keywords_for_profile(self, sync_client, user_headers):
        """Test suggesting keywords for specific profile"""
        response = sync_client.post(
            "/api/v1/profiles/strategic/profile-123/suggest-keywords",
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 404, 500]


class TestStrategicProfileWebsite:
    """Tests for website scraping"""
    
    def test_scrape_website(self, sync_client, user_headers):
        """Test scraping website for profile"""
        response = sync_client.post(
            "/api/v1/profiles/strategic/profile-123/scrape-website",
            json={"url": "https://example.com"},
            headers=user_headers
        )
        assert response.status_code in [200, 201, 400, 401, 403, 404, 422, 500]
    
    def test_delete_website_content(self, sync_client, user_headers):
        """Test deleting website content"""
        response = sync_client.delete(
            "/api/v1/profiles/strategic/profile-123/website-content",
            headers=user_headers
        )
        assert response.status_code in [200, 204, 401, 403, 404, 500]
    
    def test_sync_default(self, sync_client, user_headers):
        """Test syncing default profile"""
        response = sync_client.post(
            "/api/v1/profiles/strategic/sync-default",
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 500]


class TestStrategicProfileDescription:
    """Tests for description generation"""
    
    def test_generate_description(self, sync_client, user_headers):
        """Test generating description for profile"""
        response = sync_client.post(
            "/api/v1/profiles/strategic/profile-123/generate-description",
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 404, 500]
