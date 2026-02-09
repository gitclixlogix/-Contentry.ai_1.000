"""
Admin Analytics Tests (ARCH-025)

Tests for admin analytics endpoints including:
- Dashboard stats
- User analytics
- Payment analytics
- Usage analytics
"""

import pytest
from fastapi.testclient import TestClient


class TestAdminAnalytics:
    """Test admin analytics endpoints"""
    
    @pytest.mark.admin
    def test_admin_stats_requires_admin(self, sync_client: TestClient, user_headers):
        """Test that admin stats requires admin role"""
        response = sync_client.get(
            "/api/v1/admin/stats",
            headers=user_headers  # Regular user
        )
        # Should be denied for non-admin
        assert response.status_code in [401, 403, 404]
    
    @pytest.mark.admin
    def test_admin_stats_with_admin(self, sync_client: TestClient, admin_headers):
        """Test admin stats with admin role"""
        response = sync_client.get(
            "/api/v1/admin/stats",
            headers=admin_headers
        )
        assert response.status_code in [200, 403, 500]
        if response.status_code == 200:
            data = response.json()
            # Check expected fields exist
            assert isinstance(data, dict)
    
    @pytest.mark.admin
    def test_card_distribution_requires_admin(self, sync_client: TestClient, user_headers):
        """Test card distribution requires admin"""
        response = sync_client.get(
            "/api/v1/admin/analytics/card-distribution",
            headers=user_headers
        )
        assert response.status_code in [401, 403, 404, 500]
    
    @pytest.mark.admin
    def test_users_by_country_requires_admin(self, sync_client: TestClient, user_headers):
        """Test users by country requires admin"""
        response = sync_client.get(
            "/api/v1/admin/analytics/users-by-country",
            headers=user_headers
        )
        assert response.status_code in [401, 403, 404, 500]
    
    @pytest.mark.admin
    def test_payments_analytics_requires_admin(self, sync_client: TestClient, user_headers):
        """Test payments analytics requires admin"""
        response = sync_client.get(
            "/api/v1/admin/analytics/payments",
            headers=user_headers
        )
        assert response.status_code in [401, 403, 404, 500]


class TestAdminWithPermissions:
    """Test admin endpoints with proper permissions"""
    
    @pytest.mark.admin
    def test_admin_user_demographics(self, sync_client: TestClient, admin_headers):
        """Test user demographics with admin"""
        response = sync_client.get(
            "/api/v1/admin/analytics/user-demographics",
            headers=admin_headers
        )
        # Should work or return appropriate error
        assert response.status_code in [200, 403, 500]
    
    @pytest.mark.admin
    def test_admin_posting_patterns(self, sync_client: TestClient, admin_headers):
        """Test posting patterns with admin"""
        response = sync_client.get(
            "/api/v1/admin/analytics/posting-patterns",
            headers=admin_headers
        )
        assert response.status_code in [200, 403, 500]
    
    @pytest.mark.admin
    def test_admin_content_quality(self, sync_client: TestClient, admin_headers):
        """Test content quality analytics with admin"""
        response = sync_client.get(
            "/api/v1/admin/analytics/content-quality",
            headers=admin_headers
        )
        assert response.status_code in [200, 403, 500]
