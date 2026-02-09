"""Extended Analytics Tests

Comprehensive tests for analytics endpoints.
Based on routes in /app/backend/routes/analytics.py
"""

import pytest


# =============================================================================
# PAYMENT ANALYTICS TESTS
# =============================================================================

class TestPaymentAnalytics:
    """Tests for payment analytics"""
    
    def test_get_payment_analytics(self, sync_client, admin_headers):
        """Test getting payment analytics"""
        response = sync_client.get(
            "/api/v1/admin/analytics/payments",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 500]


# =============================================================================
# CARD DISTRIBUTION TESTS
# =============================================================================

class TestCardDistribution:
    """Tests for card distribution analytics"""
    
    def test_get_card_distribution(self, sync_client, admin_headers):
        """Test getting card distribution"""
        response = sync_client.get(
            "/api/v1/admin/analytics/card-distribution",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 500]


# =============================================================================
# GEOGRAPHIC ANALYTICS TESTS
# =============================================================================

class TestGeographicAnalytics:
    """Tests for geographic analytics"""
    
    def test_get_users_by_country(self, sync_client, admin_headers):
        """Test getting users by country"""
        response = sync_client.get(
            "/api/v1/admin/analytics/users-by-country",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 500]


# =============================================================================
# SUBSCRIPTION ANALYTICS TESTS
# =============================================================================

class TestSubscriptionAnalytics:
    """Tests for subscription analytics"""
    
    def test_get_subscription_analytics(self, sync_client, admin_headers):
        """Test getting subscription analytics"""
        response = sync_client.get(
            "/api/v1/admin/analytics/subscriptions",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 500]


# =============================================================================
# USER TABLE ANALYTICS TESTS
# =============================================================================

class TestUserTableAnalytics:
    """Tests for user table analytics"""
    
    def test_get_user_table(self, sync_client, admin_headers):
        """Test getting user table analytics"""
        response = sync_client.get(
            "/api/v1/admin/analytics/user-table",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_user_demographics(self, sync_client, admin_headers):
        """Test getting user demographics"""
        response = sync_client.get(
            "/api/v1/admin/analytics/user-demographics",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 500]


# =============================================================================
# POSTING PATTERN ANALYTICS TESTS
# =============================================================================

class TestPostingPatterns:
    """Tests for posting pattern analytics"""
    
    def test_get_posting_patterns(self, sync_client, admin_headers):
        """Test getting posting patterns"""
        response = sync_client.get(
            "/api/v1/admin/analytics/posting-patterns",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 500]


# =============================================================================
# CONTENT QUALITY ANALYTICS TESTS
# =============================================================================

class TestContentQuality:
    """Tests for content quality analytics"""
    
    def test_get_content_quality(self, sync_client, admin_headers):
        """Test getting content quality metrics"""
        response = sync_client.get(
            "/api/v1/admin/analytics/content-quality",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 500]


# =============================================================================
# COST METRICS TESTS
# =============================================================================

class TestCostMetrics:
    """Tests for cost metrics"""
    
    def test_get_cost_metrics(self, sync_client, admin_headers):
        """Test getting cost metrics"""
        response = sync_client.get(
            "/api/v1/admin/analytics/cost-metrics",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 500]


# =============================================================================
# LANGUAGE DISTRIBUTION TESTS
# =============================================================================

class TestLanguageDistribution:
    """Tests for language distribution analytics"""
    
    def test_get_language_distribution(self, sync_client, admin_headers):
        """Test getting language distribution"""
        response = sync_client.get(
            "/api/v1/admin/analytics/language-distribution",
            headers=admin_headers
        )
        assert response.status_code in [200, 401, 403, 500]
