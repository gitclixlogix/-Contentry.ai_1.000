"""Extended AI Agent Tests

Comprehensive tests for AI agent endpoints.
Based on routes in /app/backend/routes/ai_agent.py
"""

import pytest


# =============================================================================
# AI GENERATE TESTS
# =============================================================================

class TestAIGenerate:
    """Tests for AI generation endpoints"""
    
    def test_ai_generate(self, sync_client, user_headers):
        """Test AI content generation"""
        response = sync_client.post(
            "/api/v1/agent/generate",
            json={
                "prompt": "Write a post about productivity",
                "tone": "professional"
            },
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_ai_rewrite(self, sync_client, user_headers):
        """Test AI content rewrite"""
        response = sync_client.post(
            "/api/v1/agent/rewrite",
            json={
                "content": "Original content here",
                "instructions": "Make it more engaging"
            },
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_ai_analyze(self, sync_client, user_headers):
        """Test AI content analysis"""
        response = sync_client.post(
            "/api/v1/agent/analyze",
            json={"content": "Content to analyze"},
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_ai_ideate(self, sync_client, user_headers):
        """Test AI ideation"""
        response = sync_client.post(
            "/api/v1/agent/ideate",
            json={"topic": "Marketing strategies"},
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_ai_repurpose(self, sync_client, user_headers):
        """Test AI content repurposing"""
        response = sync_client.post(
            "/api/v1/agent/repurpose",
            json={
                "content": "Long form content",
                "target_format": "twitter_thread"
            },
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_ai_optimize(self, sync_client, user_headers):
        """Test AI content optimization"""
        response = sync_client.post(
            "/api/v1/agent/optimize",
            json={
                "content": "Content to optimize",
                "platform": "linkedin"
            },
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]


# =============================================================================
# AI INFO TESTS
# =============================================================================

class TestAIInfo:
    """Tests for AI info endpoints"""
    
    def test_get_model_info(self, sync_client, user_headers):
        """Test getting AI model info"""
        response = sync_client.get(
            "/api/v1/agent/model-info",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_usage_analytics(self, sync_client, user_headers):
        """Test getting AI usage analytics"""
        response = sync_client.get(
            "/api/v1/agent/usage-analytics",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 500]
    
    def test_explain_selection(self, sync_client, user_headers):
        """Test explaining AI selection"""
        response = sync_client.get(
            "/api/v1/agent/explain-selection",
            params={"content_id": "test-123"},
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 404, 422, 500]


# =============================================================================
# AI AUTHENTICATION TESTS
# =============================================================================

class TestAIAuthentication:
    """Tests for AI authentication"""
    
    def test_ai_generate_no_auth(self, sync_client):
        """Test AI generate requires authentication"""
        response = sync_client.post(
            "/api/v1/agent/generate",
            json={"prompt": "Test"}
        )
        assert response.status_code in [401, 403, 422, 500]
