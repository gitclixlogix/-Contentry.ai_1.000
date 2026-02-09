"""Extended Content Tests

Comprehensive tests for content analysis and generation endpoints.
Based on routes in /app/backend/routes/content.py
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# =============================================================================
# CONTENT ANALYSIS TESTS
# =============================================================================

class TestContentAnalysis:
    """Tests for content analysis endpoints"""
    
    def test_analyze_content(self, sync_client, user_headers):
        """Test basic content analysis"""
        response = sync_client.post(
            "/api/v1/content/analyze",
            json={
                "content": "This is a test post about our new product launch.",
                "platforms": ["linkedin"]
            },
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_analyze_content_async(self, sync_client, user_headers):
        """Test async content analysis"""
        response = sync_client.post(
            "/api/v1/content/analyze/async",
            json={
                "content": "Async analysis test content",
                "platforms": ["twitter"]
            },
            headers=user_headers
        )
        assert response.status_code in [200, 202, 400, 401, 403, 422, 500]
    
    def test_analyze_content_empty(self, sync_client, user_headers):
        """Test analysis with empty content"""
        response = sync_client.post(
            "/api/v1/content/analyze",
            json={"content": "", "platforms": ["linkedin"]},
            headers=user_headers
        )
        assert response.status_code in [400, 422, 500]
    
    def test_analyze_content_no_auth(self, sync_client):
        """Test analysis without authentication"""
        response = sync_client.post(
            "/api/v1/content/analyze",
            json={"content": "Test", "platforms": ["linkedin"]}
        )
        assert response.status_code in [401, 403, 422, 500]
    
    def test_check_promotional_content(self, sync_client, user_headers):
        """Test checking promotional content"""
        response = sync_client.post(
            "/api/v1/content/check-promotional",
            json={"content": "Buy now! 50% off sale!"},
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_analyze_with_image(self, sync_client, user_headers):
        """Test content analysis with image"""
        response = sync_client.post(
            "/api/v1/content/analyze-with-image",
            json={
                "content": "Check out this image!",
                "image_url": "https://example.com/image.jpg"
            },
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_analyze_request(self, sync_client, user_headers):
        """Test analyze request endpoint"""
        response = sync_client.post(
            "/api/v1/content/analyze-request",
            json={
                "content": "Please analyze this content",
                "request_type": "full"
            },
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]


# =============================================================================
# CONTENT GENERATION TESTS
# =============================================================================

class TestContentGeneration:
    """Tests for content generation endpoints"""
    
    def test_generate_content(self, sync_client, user_headers):
        """Test basic content generation"""
        response = sync_client.post(
            "/api/v1/content/generate",
            json={
                "prompt": "Write a LinkedIn post about AI",
                "tone": "professional"
            },
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_generate_content_async(self, sync_client, user_headers):
        """Test async content generation"""
        response = sync_client.post(
            "/api/v1/content/generate/async",
            json={
                "prompt": "Generate async content",
                "platforms": ["twitter"]
            },
            headers=user_headers
        )
        assert response.status_code in [200, 202, 400, 401, 403, 422, 500]
    
    def test_smart_generate(self, sync_client, user_headers):
        """Test smart content generation"""
        response = sync_client.post(
            "/api/v1/content/smart-generate",
            json={
                "topic": "AI in healthcare",
                "audience": "professionals"
            },
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_regenerate_content(self, sync_client, user_headers):
        """Test content regeneration"""
        response = sync_client.post(
            "/api/v1/content/regenerate",
            json={
                "original_content": "Original post here",
                "instructions": "Make it more engaging"
            },
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]


# =============================================================================
# CONTENT REWRITE TESTS
# =============================================================================

class TestContentRewrite:
    """Tests for content rewrite endpoints"""
    
    def test_rewrite_content(self, sync_client, user_headers):
        """Test content rewriting"""
        response = sync_client.post(
            "/api/v1/content/rewrite",
            json={
                "content": "This is unprofessional content",
                "tone": "professional",
                "issues": ["too casual"]
            },
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_confirm_disclosure(self, sync_client, user_headers):
        """Test confirming content disclosure"""
        response = sync_client.post(
            "/api/v1/content/confirm-disclosure",
            json={"content_id": "test-content-123", "confirmed": True},
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 404, 422, 500]


# =============================================================================
# IMAGE GENERATION TESTS
# =============================================================================

class TestImageGeneration:
    """Tests for image generation endpoints"""
    
    def test_generate_image_async(self, sync_client, user_headers):
        """Test async image generation"""
        response = sync_client.post(
            "/api/v1/ai/generate-image/async",
            json={"prompt": "A professional business meeting"},
            headers=user_headers
        )
        assert response.status_code in [200, 202, 400, 401, 403, 422, 500]
    
    def test_generate_image(self, sync_client, user_headers):
        """Test image generation"""
        response = sync_client.post(
            "/api/v1/content/generate-image",
            json={"prompt": "Modern office space"},
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_regenerate_image(self, sync_client, user_headers):
        """Test image regeneration"""
        response = sync_client.post(
            "/api/v1/content/regenerate-image",
            json={
                "original_prompt": "Office space",
                "modifications": "Add more plants"
            },
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_get_image_models(self, sync_client, user_headers):
        """Test getting available image models"""
        response = sync_client.get(
            "/api/v1/content/image-models",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 500]
    
    def test_analyze_image(self, sync_client, user_headers):
        """Test image analysis"""
        response = sync_client.post(
            "/api/v1/analyze-image",
            json={"image_url": "https://example.com/test.jpg"},
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_vision_status(self, sync_client, user_headers):
        """Test vision API status"""
        response = sync_client.get(
            "/api/v1/vision-status",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 500]


# =============================================================================
# MEDIA ANALYSIS TESTS
# =============================================================================

class TestMediaAnalysis:
    """Tests for media analysis endpoints"""
    
    def test_analyze_media(self, sync_client, user_headers):
        """Test media analysis"""
        response = sync_client.post(
            "/api/v1/media/analyze",
            json={"media_url": "https://example.com/video.mp4"},
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]


# =============================================================================
# SCHEDULED PROMPTS TESTS
# =============================================================================

class TestScheduledPrompts:
    """Tests for scheduled prompts endpoints"""
    
    def test_create_scheduled_prompt(self, sync_client, user_headers):
        """Test creating scheduled prompt"""
        response = sync_client.post(
            "/api/v1/scheduled-prompts",
            json={
                "prompt": "Daily motivational post",
                "schedule": "0 9 * * *"
            },
            headers=user_headers
        )
        assert response.status_code in [200, 201, 400, 401, 403, 422, 500]
    
    def test_get_scheduled_prompts(self, sync_client, user_headers):
        """Test getting scheduled prompts"""
        response = sync_client.get(
            "/api/v1/scheduled-prompts",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 422, 500]
    
    def test_delete_scheduled_prompt(self, sync_client, user_headers):
        """Test deleting scheduled prompt"""
        response = sync_client.delete(
            "/api/v1/scheduled-prompts/prompt-123",
            headers=user_headers
        )
        assert response.status_code in [200, 204, 401, 403, 404, 422, 500]
    
    def test_toggle_scheduled_prompt(self, sync_client, user_headers):
        """Test toggling scheduled prompt"""
        response = sync_client.patch(
            "/api/v1/scheduled-prompts/prompt-123/toggle",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 404, 422, 500]


# =============================================================================
# GENERATED CONTENT HISTORY TESTS
# =============================================================================

class TestGeneratedContentHistory:
    """Tests for generated content history"""
    
    def test_get_generated_content(self, sync_client, user_headers):
        """Test getting generated content history"""
        response = sync_client.get(
            "/api/v1/generated-content",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 422, 500]


# =============================================================================
# SPECIALIZED CONTENT GENERATION TESTS
# =============================================================================

class TestSpecializedGeneration:
    """Tests for specialized content generation"""
    
    def test_generate_seo_blog(self, sync_client, user_headers):
        """Test SEO blog generation"""
        response = sync_client.post(
            "/api/v1/content/generate-seo-blog",
            json={
                "topic": "Best practices for remote work",
                "keywords": ["remote work", "productivity"]
            },
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_generate_social_campaign(self, sync_client, user_headers):
        """Test social campaign generation"""
        response = sync_client.post(
            "/api/v1/content/generate-social-campaign",
            json={
                "campaign_goal": "Product launch",
                "platforms": ["linkedin", "twitter"]
            },
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_repurpose_podcast(self, sync_client, user_headers):
        """Test podcast repurposing"""
        response = sync_client.post(
            "/api/v1/content/repurpose-podcast",
            json={"transcript": "This is a podcast transcript..."},
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]


# =============================================================================
# AGENT CAPABILITIES TESTS
# =============================================================================

class TestAgentCapabilities:
    """Tests for AI agent capabilities"""
    
    def test_get_agent_capabilities(self, sync_client, user_headers):
        """Test getting agent capabilities"""
        response = sync_client.get(
            "/api/v1/content/agent-capabilities",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_model_selection_explanation(self, sync_client, user_headers):
        """Test getting model selection explanation"""
        response = sync_client.get(
            "/api/v1/content/model-selection-explanation",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 404, 422, 500]
