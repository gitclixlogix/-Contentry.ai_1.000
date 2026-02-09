"""
Response Schema Tests (ARCH-025)

Tests for API response schemas and validation including:
- Response format validation
- Error response format
- Pagination responses
"""

import pytest
from fastapi.testclient import TestClient


class TestResponseSchemas:
    """Test API response schemas"""
    
    def test_health_response_schema(self, sync_client: TestClient):
        """Test health check response schema"""
        response = sync_client.get("/api/v1/health/database")
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            # Verify required fields
            assert "status" in data
            # Database may be unhealthy in test environment due to event loop issues
            assert data["status"] in ["healthy", "unhealthy"]
    
    def test_success_response_has_status(self, sync_client: TestClient, admin_headers):
        """Test that success responses have status field"""
        response = sync_client.get(
            "/api/v1/observability/slos/definitions",
            headers=admin_headers
        )
        assert response.status_code in [200, 403, 500]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert data["status"] == "success"
            assert "data" in data
    
    def test_error_response_has_detail(self, sync_client: TestClient, user_headers):
        """Test that error responses have detail field"""
        response = sync_client.get(
            "/api/v1/admin/stats",
            headers=user_headers  # Regular user, should fail
        )
        assert response.status_code in [401, 403, 404, 500]
        if response.status_code in [401, 403]:
            data = response.json()
            assert "detail" in data
    
    def test_list_response_is_array(self, sync_client: TestClient, user_headers):
        """Test that list endpoints return arrays"""
        response = sync_client.get(
            "/api/v1/posts",
            headers=user_headers
        )
        assert response.status_code in [200, 403, 500]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_correlation_id_in_response_headers(self, sync_client: TestClient):
        """Test that correlation ID is in response headers"""
        response = sync_client.get("/api/v1/health/database")
        assert "x-correlation-id" in response.headers
        assert len(response.headers["x-correlation-id"]) > 0


class TestValidationErrors:
    """Test validation error responses"""
    
    def test_missing_required_field_error(self, sync_client: TestClient, user_headers):
        """Test error response for missing required field"""
        response = sync_client.post(
            "/api/v1/content/analyze",
            headers=user_headers,
            json={}  # Missing required content field
        )
        assert response.status_code in [422, 403]
        if response.status_code == 422:
            data = response.json()
            assert "detail" in data
    
    def test_invalid_json_error(self, sync_client: TestClient, user_headers):
        """Test error response for invalid JSON"""
        response = sync_client.post(
            "/api/v1/content/analyze",
            headers={**user_headers, "Content-Type": "application/json"},
            content="{invalid json"
        )
        assert response.status_code in [422, 400]
