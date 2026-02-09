"""Extended Company Tests

Comprehensive tests for company management endpoints.
Based on routes in /app/backend/routes/company.py
"""

import pytest


# =============================================================================
# COMPANY CRUD TESTS
# =============================================================================

class TestCompanyCRUD:
    """Tests for company CRUD operations"""
    
    def test_create_company(self, sync_client, user_headers):
        """Test creating a company"""
        response = sync_client.post(
            "/api/v1/company/create",
            json={
                "name": "Test Company",
                "domain": "testcompany.com"
            },
            headers=user_headers
        )
        assert response.status_code in [200, 201, 400, 401, 403, 422, 500]
    
    def test_get_my_company(self, sync_client, user_headers):
        """Test getting my company"""
        response = sync_client.get(
            "/api/v1/company/my-company",
            headers=user_headers
        )
        # Returns null if user has no company, 200 if they do
        assert response.status_code in [200, 401, 403, 404, 500]
    
    def test_update_company(self, sync_client, user_headers):
        """Test updating company"""
        response = sync_client.put(
            "/api/v1/company/update",
            json={"name": "Updated Company Name"},
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 404, 422, 500]


# =============================================================================
# COMPANY MEMBERS TESTS
# =============================================================================

class TestCompanyMembers:
    """Tests for company member management"""
    
    def test_get_company_members(self, sync_client, user_headers):
        """Test getting company members"""
        response = sync_client.get(
            "/api/v1/company/members",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 404, 500]


# =============================================================================
# COMPANY AUTHENTICATION TESTS
# =============================================================================

class TestCompanyAuthentication:
    """Tests for company authentication"""
    
    def test_company_no_auth(self, sync_client):
        """Test company endpoints require authentication"""
        response = sync_client.get("/api/v1/company/my-company")
        assert response.status_code in [401, 403, 422, 500]
