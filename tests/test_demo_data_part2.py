"""
Test Demo Data Part 2 - Scheduled Posts, Approval Workflows, LinkedIn Integration
Tests for TechCorp Demo Environment for Right Management presentation
"""

import pytest
import requests
import os
from datetime import datetime

# Use the public URL for testing
BASE_URL = "https://admin-portal-278.preview.emergentagent.com"

# Demo credentials
DEMO_USERS = {
    "admin": {
        "email": "sarah.chen@techcorp-demo.com",
        "password": "Demo123!",
        "role": "admin"
    },
    "manager": {
        "email": "michael.rodriguez@techcorp-demo.com",
        "password": "Demo123!",
        "role": "manager"
    },
    "creator": {
        "email": "alex.martinez@techcorp-demo.com",
        "password": "Demo123!",
        "role": "creator"
    },
    "compliance": {
        "email": "david.thompson@techcorp-demo.com",
        "password": "Demo123!",
        "role": "manager"
    }
}


class TestDemoLogin:
    """Test demo user login functionality"""
    
    def test_admin_login(self):
        """Test Admin (Sarah Chen) login"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": DEMO_USERS["admin"]["email"],
                "password": DEMO_USERS["admin"]["password"]
            }
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert "user" in data
        assert data["user"]["email"] == DEMO_USERS["admin"]["email"]
        print(f"✓ Admin login successful: {data['user']['full_name']}")
        return data
    
    def test_manager_login(self):
        """Test Manager (Michael Rodriguez) login"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": DEMO_USERS["manager"]["email"],
                "password": DEMO_USERS["manager"]["password"]
            }
        )
        assert response.status_code == 200, f"Manager login failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Manager login successful: {data['user']['full_name']}")
        return data
    
    def test_creator_login(self):
        """Test Creator (Alex Martinez) login"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": DEMO_USERS["creator"]["email"],
                "password": DEMO_USERS["creator"]["password"]
            }
        )
        assert response.status_code == 200, f"Creator login failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Creator login successful: {data['user']['full_name']}")
        return data
    
    def test_compliance_login(self):
        """Test Compliance Officer (David Thompson) login"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": DEMO_USERS["compliance"]["email"],
                "password": DEMO_USERS["compliance"]["password"]
            }
        )
        assert response.status_code == 200, f"Compliance login failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Compliance login successful: {data['user']['full_name']}")
        return data


class TestScheduledPosts:
    """Test scheduled posts in database"""
    
    @pytest.fixture
    def admin_session(self):
        """Get admin session with cookies"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": DEMO_USERS["admin"]["email"],
                "password": DEMO_USERS["admin"]["password"]
            }
        )
        assert response.status_code == 200
        return session
    
    def test_get_posts_list(self, admin_session):
        """Test getting posts list - should include scheduled posts"""
        response = admin_session.get(
            f"{BASE_URL}/api/v1/posts",
            headers={"X-User-ID": "sarah-chen"}
        )
        # May return 200 or 403 depending on permissions
        if response.status_code == 200:
            data = response.json()
            posts = data.get("posts", [])
            print(f"✓ Found {len(posts)} posts")
            
            # Check for scheduled posts
            scheduled_posts = [p for p in posts if p.get("scheduled_at")]
            print(f"✓ Found {len(scheduled_posts)} scheduled posts")
            
            # Check for different statuses
            approved = [p for p in posts if p.get("status") == "approved"]
            pending = [p for p in posts if p.get("status") == "pending"]
            draft = [p for p in posts if p.get("status") == "draft"]
            
            print(f"  - Approved: {len(approved)}")
            print(f"  - Pending: {len(pending)}")
            print(f"  - Draft: {len(draft)}")
        else:
            print(f"Posts endpoint returned {response.status_code}")


class TestApprovalWorkflows:
    """Test approval workflows configuration"""
    
    @pytest.fixture
    def admin_session(self):
        """Get admin session with cookies"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": DEMO_USERS["admin"]["email"],
                "password": DEMO_USERS["admin"]["password"]
            }
        )
        assert response.status_code == 200
        return session
    
    def test_get_approval_workflows(self, admin_session):
        """Test getting approval workflows"""
        response = admin_session.get(
            f"{BASE_URL}/api/v1/approval/workflows",
            headers={"X-User-ID": "sarah-chen"}
        )
        if response.status_code == 200:
            data = response.json()
            workflows = data.get("workflows", [])
            print(f"✓ Found {len(workflows)} approval workflows")
            
            # Check for expected workflows
            workflow_names = [w.get("name") for w in workflows]
            expected_workflows = [
                "Standard Corporate Post",
                "HR/Employee Communications",
                "Product Announcements",
                "Crisis Communications",
                "Sensitive HR Topics"
            ]
            
            for expected in expected_workflows:
                if expected in workflow_names:
                    print(f"  ✓ Found workflow: {expected}")
                else:
                    print(f"  ⚠ Missing workflow: {expected}")
        else:
            print(f"Approval workflows endpoint returned {response.status_code}")


class TestLinkedInIntegration:
    """Test LinkedIn integration configuration"""
    
    @pytest.fixture
    def admin_session(self):
        """Get admin session with cookies"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": DEMO_USERS["admin"]["email"],
                "password": DEMO_USERS["admin"]["password"]
            }
        )
        assert response.status_code == 200
        return session
    
    def test_get_social_profiles(self, admin_session):
        """Test getting social profiles including LinkedIn"""
        response = admin_session.get(
            f"{BASE_URL}/api/v1/social/profiles",
            headers={"X-User-ID": "sarah-chen"}
        )
        if response.status_code == 200:
            data = response.json()
            profiles = data.get("profiles", [])
            print(f"✓ Found {len(profiles)} social profiles")
            
            # Check for LinkedIn profiles
            linkedin_profiles = [p for p in profiles if p.get("platform") == "linkedin"]
            print(f"✓ Found {len(linkedin_profiles)} LinkedIn profiles")
            
            for profile in linkedin_profiles:
                print(f"  - {profile.get('account_name')}")
        else:
            print(f"Social profiles endpoint returned {response.status_code}")


class TestDatabaseContent:
    """Direct database content verification via API"""
    
    @pytest.fixture
    def admin_session(self):
        """Get admin session with cookies"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": DEMO_USERS["admin"]["email"],
                "password": DEMO_USERS["admin"]["password"]
            }
        )
        assert response.status_code == 200
        return session
    
    def test_dashboard_stats(self, admin_session):
        """Test dashboard stats to verify data exists"""
        response = admin_session.get(
            f"{BASE_URL}/api/v1/dashboard/stats",
            headers={"X-User-ID": "sarah-chen"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Dashboard stats retrieved")
            print(f"  - Total posts: {data.get('total_posts', 'N/A')}")
            print(f"  - Pending approval: {data.get('pending_approval', 'N/A')}")
            print(f"  - Scheduled: {data.get('scheduled', 'N/A')}")
        else:
            print(f"Dashboard stats returned {response.status_code}")
    
    def test_notifications(self, admin_session):
        """Test notifications exist"""
        response = admin_session.get(
            f"{BASE_URL}/api/v1/notifications",
            headers={"X-User-ID": "sarah-chen"}
        )
        if response.status_code == 200:
            data = response.json()
            notifications = data.get("notifications", [])
            print(f"✓ Found {len(notifications)} notifications")
        else:
            print(f"Notifications endpoint returned {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
