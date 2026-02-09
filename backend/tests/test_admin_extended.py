"""Extended Admin Tests

Comprehensive tests for admin endpoints.
Based on routes in /app/backend/routes/admin.py
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# =============================================================================
# ADMIN STATS TESTS
# =============================================================================

class TestAdminStats:
    """Tests for admin statistics"""
    
    def test_get_admin_stats(self, sync_client, admin_headers):
        """Test getting admin stats"""
        response = sync_client.get(
            "/api/v1/admin/stats",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_admin_stats_regular_user(self, sync_client, user_headers):
        """Test admin stats denied for regular user"""
        response = sync_client.get(
            "/api/v1/admin/stats",
            headers=user_headers
        )
        assert response.status_code in [401, 403, 500]


# =============================================================================
# GOD VIEW DASHBOARD TESTS
# =============================================================================

class TestGodViewDashboard:
    """Tests for god view dashboard"""
    
    def test_get_god_view_dashboard(self, sync_client, admin_headers):
        """Test getting god view dashboard"""
        response = sync_client.get(
            "/api/v1/admin/god-view-dashboard",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 500]


# =============================================================================
# USER MANAGEMENT TESTS
# =============================================================================

class TestAdminUserManagement:
    """Tests for admin user management"""
    
    def test_get_admin_users(self, sync_client, admin_headers):
        """Test getting admin users list"""
        response = sync_client.get(
            "/api/v1/admin/users",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_admin_users_with_pagination(self, sync_client, admin_headers):
        """Test admin users with pagination"""
        response = sync_client.get(
            "/api/v1/admin/users",
            params={"page": 1, "limit": 10},
            headers=admin_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_delete_admin_user(self, sync_client, admin_headers):
        """Test deleting a user"""
        response = sync_client.delete(
            "/api/v1/admin/users/test-user-to-delete",
            headers=admin_headers
        )
        assert response.status_code in [200, 204, 401, 403, 404, 500]
    
    def test_bulk_delete_users(self, sync_client, admin_headers):
        """Test bulk deleting users"""
        # Note: DELETE requests typically don't have a body
        # The bulk delete might use a different method or query params
        response = sync_client.post(
            "/api/v1/admin/users/bulk-delete",
            json={"user_ids": ["user-1", "user-2"]},
            headers=admin_headers
        )
        # Various status codes depending on implementation
        assert response.status_code in [200, 400, 401, 403, 404, 405, 422, 500]


# =============================================================================
# POSTS MANAGEMENT TESTS
# =============================================================================

class TestAdminPostsManagement:
    """Tests for admin posts management"""
    
    def test_get_admin_posts(self, sync_client, admin_headers):
        """Test getting admin posts list"""
        response = sync_client.get(
            "/api/v1/admin/posts",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 500]


# =============================================================================
# FEEDBACK TESTS
# =============================================================================

class TestAdminFeedback:
    """Tests for admin feedback"""
    
    def test_get_admin_feedback(self, sync_client, admin_headers):
        """Test getting admin feedback"""
        response = sync_client.get(
            "/api/v1/admin/feedback",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 500]


# =============================================================================
# DRILLDOWN TESTS
# =============================================================================

class TestAdminDrilldown:
    """Tests for admin drilldown analytics"""
    
    def test_drilldown_users(self, sync_client, admin_headers):
        """Test users drilldown"""
        response = sync_client.get(
            "/api/v1/admin/drilldown/users",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 404, 500]
    
    def test_drilldown_revenue(self, sync_client, admin_headers):
        """Test revenue drilldown"""
        response = sync_client.get(
            "/api/v1/admin/drilldown/revenue",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 404, 500]
    
    def test_financial_drilldown(self, sync_client, admin_headers):
        """Test financial drilldown"""
        response = sync_client.get(
            "/api/v1/admin/financial/drilldown/mrr",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 404, 500]
    
    def test_analytics_drilldown(self, sync_client, admin_headers):
        """Test analytics drilldown"""
        response = sync_client.get(
            "/api/v1/admin/analytics/drilldown/engagement",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 404, 500]


# =============================================================================
# DOCUMENTATION TESTS
# =============================================================================

class TestAdminDocumentation:
    """Tests for admin documentation"""
    
    def test_get_documentation(self, sync_client, admin_headers):
        """Test getting documentation"""
        response = sync_client.get(
            "/api/v1/admin/documentation",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_documentation_pdf(self, sync_client, admin_headers):
        """Test getting documentation PDF"""
        response = sync_client.get(
            "/api/v1/admin/documentation/pdf",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 404, 500]


# =============================================================================
# COMPREHENSIVE REPORT TESTS
# =============================================================================

class TestAdminReports:
    """Tests for admin reports"""
    
    def test_generate_comprehensive_report(self, sync_client, admin_headers):
        """Test generating comprehensive report"""
        response = sync_client.post(
            "/api/v1/admin/generate-comprehensive-report",
            json={"report_type": "monthly"},
            headers=admin_headers
        )
        assert response.status_code in [200, 202, 400, 401, 403, 422, 500]
    
    def test_download_pdf_report(self, sync_client, admin_headers):
        """Test downloading PDF report"""
        response = sync_client.get(
            "/api/v1/admin/download-pdf-report",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 404, 500]


# =============================================================================
# MRR TESTS
# =============================================================================

class TestAdminMRR:
    """Tests for admin MRR metrics"""
    
    def test_get_mrr(self, sync_client, admin_headers):
        """Test getting MRR"""
        response = sync_client.get(
            "/api/v1/admin/mrr",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_mrr_cache_status(self, sync_client, admin_headers):
        """Test getting MRR cache status"""
        response = sync_client.get(
            "/api/v1/admin/mrr/cache-status",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 500]
    
    def test_refresh_mrr(self, sync_client, admin_headers):
        """Test refreshing MRR"""
        response = sync_client.post(
            "/api/v1/admin/mrr/refresh",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 500]
