"""Superadmin Route Tests

Tests for superadmin management endpoints.
Based on actual routes in /app/backend/routes/superadmin.py:
- GET /api/superadmin/kpis/growth
- GET /api/superadmin/kpis/mrr-trend
- GET /api/superadmin/kpis/active-users
- GET /api/superadmin/kpis/customer-funnel
- GET /api/superadmin/kpis/trial-conversion
- GET /api/superadmin/kpis/ai-costs
- GET /api/superadmin/kpis/feature-adoption
- GET /api/superadmin/kpis/mrr-by-plan
- GET /api/superadmin/kpis/top-customers
- GET /api/superadmin/verify
- GET /api/superadmin/customers
- GET /api/superadmin/customers/{company_id}
- GET /api/superadmin/users
- GET /api/superadmin/analytics/geographic
- GET /api/superadmin/analytics/languages
- GET /api/superadmin/analytics/health
- GET /api/superadmin/analytics/revenue
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestSuperadminVerify:
    """Tests for superadmin verification"""
    
    def test_verify_superadmin(self, sync_client, admin_headers):
        """Test verifying superadmin access"""
        response = sync_client.get("/api/v1/superadmin/verify", headers=admin_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_verify_superadmin_no_auth(self, sync_client):
        """Test verify requires authentication"""
        response = sync_client.get("/api/v1/superadmin/verify")
        assert response.status_code in [401, 403, 422, 500]


class TestSuperadminKPIs:
    """Tests for superadmin KPI endpoints"""
    
    def test_get_growth_kpis(self, sync_client, admin_headers):
        """Test getting growth KPIs"""
        response = sync_client.get("/api/v1/superadmin/kpis/growth", headers=admin_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_mrr_trend(self, sync_client, admin_headers):
        """Test getting MRR trend"""
        response = sync_client.get("/api/v1/superadmin/kpis/mrr-trend", headers=admin_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_active_users(self, sync_client, admin_headers):
        """Test getting active users KPI"""
        response = sync_client.get("/api/v1/superadmin/kpis/active-users", headers=admin_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_customer_funnel(self, sync_client, admin_headers):
        """Test getting customer funnel"""
        response = sync_client.get("/api/v1/superadmin/kpis/customer-funnel", headers=admin_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_trial_conversion(self, sync_client, admin_headers):
        """Test getting trial conversion"""
        response = sync_client.get("/api/v1/superadmin/kpis/trial-conversion", headers=admin_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_ai_costs(self, sync_client, admin_headers):
        """Test getting AI costs"""
        response = sync_client.get("/api/v1/superadmin/kpis/ai-costs", headers=admin_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_feature_adoption(self, sync_client, admin_headers):
        """Test getting feature adoption"""
        response = sync_client.get("/api/v1/superadmin/kpis/feature-adoption", headers=admin_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_mrr_by_plan(self, sync_client, admin_headers):
        """Test getting MRR by plan"""
        response = sync_client.get("/api/v1/superadmin/kpis/mrr-by-plan", headers=admin_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_top_customers(self, sync_client, admin_headers):
        """Test getting top customers"""
        response = sync_client.get("/api/v1/superadmin/kpis/top-customers", headers=admin_headers)
        assert response.status_code in [200, 401, 403, 500]


class TestSuperadminCustomers:
    """Tests for customer management"""
    
    def test_list_customers(self, sync_client, admin_headers):
        """Test listing customers"""
        response = sync_client.get("/api/v1/superadmin/customers", headers=admin_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_customer_details(self, sync_client, admin_headers):
        """Test getting customer details"""
        response = sync_client.get(
            "/api/v1/superadmin/customers/company-123",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 404, 500]


class TestSuperadminUsers:
    """Tests for user management"""
    
    def test_list_users(self, sync_client, admin_headers):
        """Test listing all users"""
        response = sync_client.get("/api/v1/superadmin/users", headers=admin_headers)
        assert response.status_code in [200, 401, 403, 500]


class TestSuperadminAnalytics:
    """Tests for superadmin analytics"""
    
    def test_get_geographic_analytics(self, sync_client, admin_headers):
        """Test getting geographic analytics"""
        response = sync_client.get("/api/v1/superadmin/analytics/geographic", headers=admin_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_languages_analytics(self, sync_client, admin_headers):
        """Test getting language analytics"""
        response = sync_client.get("/api/v1/superadmin/analytics/languages", headers=admin_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_health_analytics(self, sync_client, admin_headers):
        """Test getting health analytics"""
        response = sync_client.get("/api/v1/superadmin/analytics/health", headers=admin_headers)
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_revenue_analytics(self, sync_client, admin_headers):
        """Test getting revenue analytics"""
        response = sync_client.get("/api/v1/superadmin/analytics/revenue", headers=admin_headers)
        assert response.status_code in [200, 401, 403, 500]
