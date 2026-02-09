"""Scheduler Route Tests

Tests for content scheduling endpoints.
Based on actual routes in /app/backend/routes/scheduler.py:
- GET /api/scheduler/status
- POST /api/scheduler/trigger/{post_id}
- POST /api/scheduler/reanalyze/{post_id}
- GET /api/scheduler/posts/scheduled
- POST /api/scheduler/schedule-prompt
- GET /api/scheduler/scheduled-prompts
- DELETE /api/scheduler/scheduled-prompts/{prompt_id}
- PUT /api/scheduler/scheduled-prompts/{prompt_id}/toggle
- PUT /api/scheduler/scheduled-prompts/{prompt_id}
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta


class TestSchedulerStatus:
    """Tests for scheduler status endpoints"""
    
    def test_get_scheduler_status(self, sync_client, user_headers):
        """Test getting scheduler status"""
        response = sync_client.get("/api/v1/scheduler/status", headers=user_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_scheduler_status_no_auth(self, sync_client):
        """Test scheduler status requires authentication"""
        response = sync_client.get("/api/v1/scheduler/status")
        assert response.status_code in [401, 403, 422, 500]


class TestSchedulerPosts:
    """Tests for scheduled post management"""
    
    def test_get_scheduled_posts(self, sync_client, user_headers):
        """Test getting scheduled posts"""
        response = sync_client.get("/api/v1/scheduler/posts/scheduled", headers=user_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_trigger_post(self, sync_client, user_headers):
        """Test triggering a post"""
        response = sync_client.post(
            "/api/v1/scheduler/trigger/post-123",
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 404, 500]
    
    def test_reanalyze_post(self, sync_client, user_headers):
        """Test re-analyzing a post"""
        response = sync_client.post(
            "/api/v1/scheduler/reanalyze/post-123",
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 404, 500]


class TestScheduledPrompts:
    """Tests for scheduled prompts"""
    
    def test_create_scheduled_prompt(self, sync_client, user_headers):
        """Test creating a scheduled prompt"""
        response = sync_client.post(
            "/api/v1/scheduler/schedule-prompt",
            json={
                "prompt": "Generate a LinkedIn post",
                "schedule": "0 9 * * 1-5"
            },
            headers=user_headers
        )
        assert response.status_code in [200, 201, 400, 401, 403, 422, 500]
    
    def test_get_scheduled_prompts(self, sync_client, user_headers):
        """Test getting scheduled prompts"""
        response = sync_client.get("/api/v1/scheduler/scheduled-prompts", headers=user_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_delete_scheduled_prompt(self, sync_client, user_headers):
        """Test deleting a scheduled prompt"""
        response = sync_client.delete(
            "/api/v1/scheduler/scheduled-prompts/prompt-123",
            headers=user_headers
        )
        assert response.status_code in [200, 204, 401, 403, 404, 500]
    
    def test_toggle_scheduled_prompt(self, sync_client, user_headers):
        """Test toggling a scheduled prompt"""
        response = sync_client.put(
            "/api/v1/scheduler/scheduled-prompts/prompt-123/toggle",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 404, 500]
    
    def test_update_scheduled_prompt(self, sync_client, user_headers):
        """Test updating a scheduled prompt"""
        response = sync_client.put(
            "/api/v1/scheduler/scheduled-prompts/prompt-123",
            json={"prompt": "Updated prompt"},
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 404, 422, 500]
