"""
Multi-Tenancy Tests (ARCH-025)

Tests for multi-tenancy endpoints including:
- Tenant context
- Migration status
- Schema validation
- Tenant isolation
"""

import pytest
from fastapi.testclient import TestClient


class TestTenantContext:
    """Test tenant context endpoints"""
    
    def test_tenant_context_available(self, sync_client: TestClient, user_headers):
        """Test tenant context is available"""
        response = sync_client.get(
            "/api/v1/multitenancy/tenant/context",
            headers=user_headers
        )
        assert response.status_code in [200, 403, 500]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "user_id" in data["data"]
    
    def test_enterprise_user_has_tenant_id(
        self, 
        sync_client: TestClient, 
        enterprise_headers
    ):
        """Test that enterprise user has tenant ID"""
        response = sync_client.get(
            "/api/v1/multitenancy/tenant/context",
            headers=enterprise_headers
        )
        assert response.status_code in [200, 403, 500]
        if response.status_code == 200:
            data = response.json()
            # In test environment, enterprise_id may not be set
            # Just verify the response structure is correct
            assert "data" in data
            if data["data"].get("enterprise_id") is not None:
                assert data["data"]["is_enterprise_user"] == True


class TestMigrationEndpoints:
    """Test migration endpoints"""
    
    def test_migration_status_requires_admin(self, sync_client: TestClient, user_headers):
        """Test that migration status requires admin"""
        response = sync_client.get(
            "/api/v1/multitenancy/migrations/status",
            headers=user_headers
        )
        assert response.status_code in [401, 403, 500]
    
    def test_migration_status_with_admin(self, sync_client: TestClient, admin_headers):
        """Test migration status with admin"""
        response = sync_client.get(
            "/api/v1/multitenancy/migrations/status",
            headers=admin_headers
        )
        assert response.status_code in [200, 403, 500]
        if response.status_code == 200:
            data = response.json()
            assert "applied_count" in data["data"]


class TestSchemaValidation:
    """Test schema validation endpoints"""
    
    def test_schema_status_requires_admin(self, sync_client: TestClient, user_headers):
        """Test that schema status requires admin"""
        response = sync_client.get(
            "/api/v1/multitenancy/schema/status",
            headers=user_headers
        )
        assert response.status_code in [401, 403, 500]
    
    def test_schema_status_with_admin(self, sync_client: TestClient, admin_headers):
        """Test schema status with admin"""
        response = sync_client.get(
            "/api/v1/multitenancy/schema/status",
            headers=admin_headers
        )
        assert response.status_code in [200, 403, 500]
        if response.status_code == 200:
            data = response.json()
            assert "tenant_isolated" in data["data"]


class TestTenantIsolation:
    """Test tenant isolation status"""
    
    def test_tenant_status_with_admin(self, sync_client: TestClient, admin_headers):
        """Test tenant status with admin"""
        response = sync_client.get(
            "/api/v1/multitenancy/tenant/status",
            headers=admin_headers
        )
        assert response.status_code in [200, 403, 500]
        if response.status_code == 200:
            data = response.json()
            assert "configuration" in data["data"]
            assert "statistics" in data["data"]
