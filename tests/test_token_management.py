"""
Token Management API Tests for Super Admin
Tests all token tracking, alerts, and cost analysis endpoints.

Endpoints tested:
- GET /api/v1/superadmin/tokens/realtime - Real-time token stats
- GET /api/v1/superadmin/tokens/usage/summary - Usage summary with trend data
- GET /api/v1/superadmin/tokens/usage/by-agent - Breakdown by agent type
- GET /api/v1/superadmin/tokens/usage/by-model - Breakdown by model
- GET /api/v1/superadmin/tokens/usage/top-users - Top users by token consumption
- GET /api/v1/superadmin/tokens/alerts - Get alerts list
- GET /api/v1/superadmin/tokens/alerts/config - Get alert configuration
- PUT /api/v1/superadmin/tokens/alerts/config - Update alert thresholds
- POST /api/v1/superadmin/tokens/alerts/acknowledge - Acknowledge alert
- GET /api/v1/superadmin/tokens/cost/comparison - API vs credit cost comparison
- GET /api/v1/superadmin/tokens/cost/projection - Monthly cost projection
- GET /api/v1/superadmin/tokens/recommendations - Optimization recommendations
- Access control tests - Non-super-admin users should get 403
"""

import pytest
import requests
import os

# Use the public URL for testing
BASE_URL = os.environ.get('FRONTEND_URL', 'https://admin-portal-278.preview.emergentagent.com')

# Test credentials
SUPER_ADMIN_USER_ID = "security-test-user-001"
SUPER_ADMIN_EMAIL = "test@security.com"
REGULAR_USER_ID = "demo-user-001"


class TestTokenManagementAccessControl:
    """Test access control - Super Admin only"""
    
    def test_realtime_stats_requires_super_admin(self):
        """Regular user should get 403 on realtime stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/realtime",
            headers={"x-user-id": REGULAR_USER_ID, "Content-Type": "application/json"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Regular user correctly denied access to realtime stats (403)")
    
    def test_usage_summary_requires_super_admin(self):
        """Regular user should get 403 on usage summary endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/usage/summary",
            headers={"x-user-id": REGULAR_USER_ID, "Content-Type": "application/json"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Regular user correctly denied access to usage summary (403)")
    
    def test_alerts_requires_super_admin(self):
        """Regular user should get 403 on alerts endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/alerts",
            headers={"x-user-id": REGULAR_USER_ID, "Content-Type": "application/json"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Regular user correctly denied access to alerts (403)")
    
    def test_no_user_id_returns_401(self):
        """Request without user ID should get 401"""
        response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/realtime",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print(f"✓ Request without user ID correctly returns 401")


class TestRealtimeStats:
    """Test GET /api/v1/superadmin/tokens/realtime"""
    
    def test_realtime_stats_success(self):
        """Super admin can access realtime stats"""
        response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/realtime",
            headers={"x-user-id": SUPER_ADMIN_USER_ID, "Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, f"Expected success=True, got {data}"
        assert "data" in data, "Response should contain 'data' field"
        
        stats = data["data"]
        # Verify structure
        assert "today" in stats, "Should have 'today' stats"
        assert "last_hour" in stats, "Should have 'last_hour' stats"
        assert "tokens_per_minute" in stats, "Should have 'tokens_per_minute'"
        assert "requests_per_minute" in stats, "Should have 'requests_per_minute'"
        assert "projection" in stats, "Should have 'projection' data"
        
        # Verify today stats structure
        today = stats["today"]
        assert "total_tokens" in today, "today should have total_tokens"
        assert "api_cost_usd" in today, "today should have api_cost_usd"
        assert "request_count" in today, "today should have request_count"
        
        print(f"✓ Realtime stats returned successfully")
        print(f"  - Today's tokens: {today.get('total_tokens', 0)}")
        print(f"  - Today's cost: ${today.get('api_cost_usd', 0)}")
        print(f"  - Tokens/min: {stats.get('tokens_per_minute', 0)}")


class TestUsageSummary:
    """Test GET /api/v1/superadmin/tokens/usage/summary"""
    
    def test_usage_summary_default(self):
        """Get usage summary with default parameters"""
        response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/usage/summary",
            headers={"x-user-id": SUPER_ADMIN_USER_ID, "Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "data" in data
        
        summary = data["data"]
        assert "period" in summary, "Should have period info"
        assert "totals" in summary, "Should have totals"
        assert "trend_data" in summary, "Should have trend_data"
        
        totals = summary["totals"]
        assert "total_tokens" in totals
        assert "total_api_cost_usd" in totals
        assert "total_requests" in totals
        
        print(f"✓ Usage summary returned successfully")
        print(f"  - Total tokens: {totals.get('total_tokens', 0)}")
        print(f"  - Total cost: ${totals.get('total_api_cost_usd', 0)}")
    
    def test_usage_summary_with_days_param(self):
        """Get usage summary with custom days parameter"""
        response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/usage/summary?days=7",
            headers={"x-user-id": SUPER_ADMIN_USER_ID, "Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Usage summary with days=7 returned successfully")
    
    def test_usage_summary_with_group_by(self):
        """Get usage summary with hourly grouping"""
        response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/usage/summary?days=7&group_by=hourly",
            headers={"x-user-id": SUPER_ADMIN_USER_ID, "Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Usage summary with hourly grouping returned successfully")


class TestUsageByAgent:
    """Test GET /api/v1/superadmin/tokens/usage/by-agent"""
    
    def test_usage_by_agent(self):
        """Get token usage breakdown by agent type"""
        response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/usage/by-agent",
            headers={"x-user-id": SUPER_ADMIN_USER_ID, "Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "data" in data
        
        # Data should be a list (may be empty if no usage yet)
        assert isinstance(data["data"], list), "Data should be a list"
        
        # If there's data, verify structure
        if len(data["data"]) > 0:
            agent = data["data"][0]
            assert "agent_type" in agent
            assert "total_tokens" in agent
            assert "api_cost_usd" in agent
            assert "request_count" in agent
            print(f"✓ Usage by agent returned {len(data['data'])} agent types")
            for a in data["data"][:3]:
                print(f"  - {a.get('agent_type')}: {a.get('total_tokens')} tokens")
        else:
            print(f"✓ Usage by agent returned empty list (no usage data yet)")


class TestUsageByModel:
    """Test GET /api/v1/superadmin/tokens/usage/by-model"""
    
    def test_usage_by_model(self):
        """Get token usage breakdown by model"""
        response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/usage/by-model",
            headers={"x-user-id": SUPER_ADMIN_USER_ID, "Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "data" in data
        assert isinstance(data["data"], list)
        
        if len(data["data"]) > 0:
            model = data["data"][0]
            assert "model" in model
            assert "provider" in model
            assert "total_tokens" in model
            assert "api_cost_usd" in model
            print(f"✓ Usage by model returned {len(data['data'])} models")
            for m in data["data"][:3]:
                print(f"  - {m.get('model')} ({m.get('provider')}): ${m.get('api_cost_usd')}")
        else:
            print(f"✓ Usage by model returned empty list (no usage data yet)")


class TestTopUsers:
    """Test GET /api/v1/superadmin/tokens/usage/top-users"""
    
    def test_top_users(self):
        """Get top users by token consumption"""
        response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/usage/top-users",
            headers={"x-user-id": SUPER_ADMIN_USER_ID, "Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "data" in data
        assert isinstance(data["data"], list)
        
        if len(data["data"]) > 0:
            user = data["data"][0]
            assert "user_id" in user
            assert "total_tokens" in user
            assert "api_cost_usd" in user
            print(f"✓ Top users returned {len(data['data'])} users")
        else:
            print(f"✓ Top users returned empty list (no usage data yet)")
    
    def test_top_users_with_limit(self):
        """Get top users with custom limit"""
        response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/usage/top-users?limit=5",
            headers={"x-user-id": SUPER_ADMIN_USER_ID, "Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert len(data["data"]) <= 5, "Should return at most 5 users"
        print(f"✓ Top users with limit=5 returned successfully")


class TestAlerts:
    """Test alerts endpoints"""
    
    def test_get_alerts(self):
        """Get alerts list"""
        response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/alerts",
            headers={"x-user-id": SUPER_ADMIN_USER_ID, "Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "data" in data
        assert "count" in data
        assert isinstance(data["data"], list)
        
        print(f"✓ Alerts returned {data.get('count', 0)} alerts")
    
    def test_get_alerts_with_severity_filter(self):
        """Get alerts filtered by severity"""
        response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/alerts?severity=warning",
            headers={"x-user-id": SUPER_ADMIN_USER_ID, "Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Alerts with severity=warning returned successfully")
    
    def test_get_alerts_include_acknowledged(self):
        """Get alerts including acknowledged ones"""
        response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/alerts?include_acknowledged=true",
            headers={"x-user-id": SUPER_ADMIN_USER_ID, "Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Alerts with include_acknowledged=true returned successfully")


class TestAlertConfig:
    """Test alert configuration endpoints"""
    
    def test_get_alert_config(self):
        """Get current alert configuration"""
        response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/alerts/config",
            headers={"x-user-id": SUPER_ADMIN_USER_ID, "Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "data" in data
        
        config = data["data"]
        assert "enabled" in config
        assert "email_notifications" in config
        assert "thresholds" in config
        
        thresholds = config["thresholds"]
        assert "daily_tokens" in thresholds
        assert "daily_cost_usd" in thresholds
        assert "monthly_budget_usd" in thresholds
        
        print(f"✓ Alert config returned successfully")
        print(f"  - Enabled: {config.get('enabled')}")
        print(f"  - Daily token limit: {thresholds.get('daily_tokens')}")
        print(f"  - Monthly budget: ${thresholds.get('monthly_budget_usd')}")
    
    def test_update_alert_config(self):
        """Update alert configuration"""
        # First get current config
        get_response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/alerts/config",
            headers={"x-user-id": SUPER_ADMIN_USER_ID, "Content-Type": "application/json"}
        )
        original_config = get_response.json()["data"]
        
        # Update with new values
        update_data = {
            "notification_cooldown_minutes": 120
        }
        
        response = requests.put(
            f"{BASE_URL}/api/v1/superadmin/tokens/alerts/config",
            headers={"x-user-id": SUPER_ADMIN_USER_ID, "Content-Type": "application/json"},
            json=update_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        
        # Verify update
        updated_config = data["data"]
        assert updated_config.get("notification_cooldown_minutes") == 120
        
        # Restore original value
        restore_data = {
            "notification_cooldown_minutes": original_config.get("notification_cooldown_minutes", 60)
        }
        requests.put(
            f"{BASE_URL}/api/v1/superadmin/tokens/alerts/config",
            headers={"x-user-id": SUPER_ADMIN_USER_ID, "Content-Type": "application/json"},
            json=restore_data
        )
        
        print(f"✓ Alert config updated and restored successfully")


class TestAlertAcknowledge:
    """Test alert acknowledgment"""
    
    def test_acknowledge_nonexistent_alert(self):
        """Acknowledging non-existent alert should return 404"""
        response = requests.post(
            f"{BASE_URL}/api/v1/superadmin/tokens/alerts/acknowledge",
            headers={"x-user-id": SUPER_ADMIN_USER_ID, "Content-Type": "application/json"},
            json={"alert_id": "nonexistent-alert-id-12345"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print(f"✓ Acknowledging non-existent alert correctly returns 404")


class TestCostComparison:
    """Test GET /api/v1/superadmin/tokens/cost/comparison"""
    
    def test_cost_comparison(self):
        """Get cost comparison between API costs and credit revenue"""
        response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/cost/comparison",
            headers={"x-user-id": SUPER_ADMIN_USER_ID, "Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "data" in data
        
        comparison = data["data"]
        assert "period_days" in comparison
        assert "totals" in comparison
        
        totals = comparison["totals"]
        assert "api_cost_usd" in totals
        assert "credit_cost" in totals
        assert "credit_revenue_usd" in totals
        assert "margin_usd" in totals
        assert "margin_percent" in totals
        
        print(f"✓ Cost comparison returned successfully")
        print(f"  - API Cost: ${totals.get('api_cost_usd')}")
        print(f"  - Credit Revenue: ${totals.get('credit_revenue_usd')}")
        print(f"  - Margin: ${totals.get('margin_usd')} ({totals.get('margin_percent')}%)")


class TestCostProjection:
    """Test GET /api/v1/superadmin/tokens/cost/projection"""
    
    def test_cost_projection(self):
        """Get monthly cost projection"""
        response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/cost/projection",
            headers={"x-user-id": SUPER_ADMIN_USER_ID, "Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "data" in data
        
        projection = data["data"]
        assert "current_cost_usd" in projection
        assert "projected_cost_usd" in projection
        assert "days_elapsed" in projection
        assert "days_remaining" in projection
        assert "daily_avg_cost_usd" in projection
        
        print(f"✓ Cost projection returned successfully")
        print(f"  - Current MTD: ${projection.get('current_cost_usd')}")
        print(f"  - Projected: ${projection.get('projected_cost_usd')}")
        print(f"  - Daily avg: ${projection.get('daily_avg_cost_usd')}")


class TestRecommendations:
    """Test GET /api/v1/superadmin/tokens/recommendations"""
    
    def test_recommendations(self):
        """Get optimization recommendations"""
        response = requests.get(
            f"{BASE_URL}/api/v1/superadmin/tokens/recommendations",
            headers={"x-user-id": SUPER_ADMIN_USER_ID, "Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "data" in data
        assert isinstance(data["data"], list)
        
        # Should always have at least one recommendation
        assert len(data["data"]) >= 1, "Should have at least one recommendation"
        
        rec = data["data"][0]
        assert "type" in rec
        assert "priority" in rec
        assert "title" in rec
        assert "description" in rec
        
        print(f"✓ Recommendations returned {len(data['data'])} items")
        for r in data["data"][:3]:
            print(f"  - [{r.get('priority')}] {r.get('title')}")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
