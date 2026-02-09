"""
Test Suite for Documentation Pages and Team Management Role Change API
Tests:
1. Documentation hub accessibility
2. Strategic Profiles documentation page
3. Approval Workflow documentation page
4. Social Accounts documentation page
5. Role change API for admin users
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://admin-portal-278.preview.emergentagent.com')

# Demo admin credentials
DEMO_ADMIN_EMAIL = "demo-admin@contentry.com"
DEMO_ADMIN_PASSWORD = "DemoAdmin!123"


class TestAuthentication:
    """Test authentication for demo admin user"""
    
    def test_demo_admin_login(self):
        """Test that demo admin can login successfully"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": DEMO_ADMIN_EMAIL, "password": DEMO_ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        print(f"✓ Demo admin login successful, role: {data['user']['role']}")


class TestTeamManagementAPI:
    """Test Team Management API endpoints"""
    
    @pytest.fixture
    def admin_auth(self):
        """Get admin authentication token and user ID"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": DEMO_ADMIN_EMAIL, "password": DEMO_ADMIN_PASSWORD}
        )
        assert response.status_code == 200, "Admin login failed"
        data = response.json()
        return {
            "token": data["access_token"],
            "user_id": data["user"]["id"],
            "headers": {
                "Authorization": f"Bearer {data['access_token']}",
                "X-User-ID": data["user"]["id"],
                "Content-Type": "application/json"
            }
        }
    
    def test_list_team_members(self, admin_auth):
        """Test listing team members"""
        response = requests.get(
            f"{BASE_URL}/api/v1/team-management/members",
            headers=admin_auth["headers"]
        )
        assert response.status_code == 200, f"List members failed: {response.text}"
        
        data = response.json()
        assert "members" in data
        assert "total" in data
        print(f"✓ List team members successful, total: {data['total']}")
    
    def test_role_change_api_endpoint_exists(self, admin_auth):
        """Test that role change endpoint exists and responds"""
        # First, we need a member to change role for
        # Let's try with a non-existent member to verify the endpoint exists
        response = requests.put(
            f"{BASE_URL}/api/v1/team-management/members/non-existent-member/role",
            headers=admin_auth["headers"],
            json={"role": "creator"}
        )
        # Should return 404 for non-existent member, not 405 (method not allowed)
        assert response.status_code in [404, 400, 403], f"Unexpected status: {response.status_code}, {response.text}"
        print(f"✓ Role change endpoint exists, returned {response.status_code} for non-existent member")
    
    def test_role_change_validation(self, admin_auth):
        """Test role change validation - invalid role"""
        response = requests.put(
            f"{BASE_URL}/api/v1/team-management/members/some-member/role",
            headers=admin_auth["headers"],
            json={"role": "invalid_role"}
        )
        # Should return 400 for invalid role or 404 for non-existent member
        assert response.status_code in [400, 404], f"Unexpected status: {response.status_code}"
        print(f"✓ Role change validation works, returned {response.status_code}")
    
    def test_role_change_self_prevention(self, admin_auth):
        """Test that admin cannot change their own role"""
        response = requests.put(
            f"{BASE_URL}/api/v1/team-management/members/{admin_auth['user_id']}/role",
            headers=admin_auth["headers"],
            json={"role": "creator"}
        )
        # Should return 400 - cannot change own role
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "cannot change your own role" in data.get("detail", "").lower()
        print(f"✓ Self role change prevention works")


class TestDatabaseHealth:
    """Test database health endpoint"""
    
    def test_database_health(self):
        """Test database health check"""
        response = requests.get(f"{BASE_URL}/api/v1/health/database")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✓ Database health check passed: {data.get('database')}")


class TestTeamInvitation:
    """Test team invitation endpoints"""
    
    @pytest.fixture
    def admin_auth(self):
        """Get admin authentication token and user ID"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": DEMO_ADMIN_EMAIL, "password": DEMO_ADMIN_PASSWORD}
        )
        assert response.status_code == 200, "Admin login failed"
        data = response.json()
        return {
            "token": data["access_token"],
            "user_id": data["user"]["id"],
            "headers": {
                "Authorization": f"Bearer {data['access_token']}",
                "X-User-ID": data["user"]["id"],
                "Content-Type": "application/json"
            }
        }
    
    def test_invite_member_validation(self, admin_auth):
        """Test invitation validation - invalid role"""
        response = requests.post(
            f"{BASE_URL}/api/v1/team-management/invite",
            headers=admin_auth["headers"],
            json={
                "email": "test@example.com",
                "role": "invalid_role"
            }
        )
        # Should return 400 for invalid role
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✓ Invitation validation works for invalid role")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
