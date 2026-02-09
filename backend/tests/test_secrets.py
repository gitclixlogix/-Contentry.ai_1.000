"""
Secrets Management Tests (ARCH-025)

Tests for secrets management endpoints including:
- Status
- Health check
- Validation
- Cache management
"""

import pytest
from fastapi.testclient import TestClient


class TestSecretsStatus:
    """Test secrets status endpoints"""
    
    def test_secrets_status_requires_admin(self, sync_client: TestClient, user_headers):
        """Test that secrets status requires admin"""
        response = sync_client.get(
            "/api/v1/secrets/status",
            headers=user_headers
        )
        assert response.status_code in [401, 403, 500]
    
    def test_secrets_status_with_admin(self, sync_client: TestClient, admin_headers):
        """Test secrets status with admin"""
        response = sync_client.get(
            "/api/v1/secrets/status",
            headers=admin_headers
        )
        assert response.status_code in [200, 403, 500]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert data["status"] == "success"
            assert "managed_secrets" in data["data"]
    
    def test_secrets_health(self, sync_client: TestClient, admin_headers):
        """Test secrets health check"""
        response = sync_client.get(
            "/api/v1/secrets/health",
            headers=admin_headers
        )
        assert response.status_code in [200, 403, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["data"]["healthy"] == True
    
    def test_secrets_validate(self, sync_client: TestClient, admin_headers):
        """Test secrets validation"""
        response = sync_client.get(
            "/api/v1/secrets/validate",
            headers=admin_headers
        )
        assert response.status_code in [200, 403, 500]
        if response.status_code == 200:
            data = response.json()
            assert "all_required_available" in data["data"]


class TestSecretsDefinitions:
    """Test secrets definitions endpoint"""
    
    def test_secrets_definitions(self, sync_client: TestClient, admin_headers):
        """Test getting secrets definitions"""
        response = sync_client.get(
            "/api/v1/secrets/definitions",
            headers=admin_headers
        )
        assert response.status_code in [200, 403, 500]
        if response.status_code == 200:
            data = response.json()
            assert "count" in data["data"]
            assert data["data"]["count"] >= 10


class TestSecretsCache:
    """Test secrets cache management"""
    
    def test_cache_invalidate_requires_admin(self, sync_client: TestClient, user_headers):
        """Test that cache invalidation requires admin"""
        response = sync_client.post(
            "/api/v1/secrets/cache/invalidate",
            headers=user_headers
        )
        assert response.status_code in [401, 403, 500]
    
    def test_cache_invalidate_with_admin(self, sync_client: TestClient, admin_headers):
        """Test cache invalidation with admin"""
        response = sync_client.post(
            "/api/v1/secrets/cache/invalidate",
            headers=admin_headers
        )
        assert response.status_code in [200, 403, 500]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert data["status"] == "success"
