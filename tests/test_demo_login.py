"""
Test TechCorp Demo Login Functionality
Tests the demo user login for all 4 roles: Admin, Manager, Creator, Reviewer
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://admin-portal-278.preview.emergentagent.com')
if not BASE_URL.endswith('/api/v1'):
    BASE_URL = f"{BASE_URL.rstrip('/')}/api/v1"

# Demo user credentials
DEMO_USERS = {
    "admin": {
        "email": "sarah.chen@techcorp-demo.com",
        "password": "Demo123!",
        "name": "Sarah Chen",
        "role": "admin"
    },
    "manager": {
        "email": "michael.rodriguez@techcorp-demo.com",
        "password": "Demo123!",
        "name": "Michael Rodriguez",
        "role": "manager"
    },
    "creator": {
        "email": "alex.martinez@techcorp-demo.com",
        "password": "Demo123!",
        "name": "Alex Martinez",
        "role": "creator"
    },
    "reviewer": {
        "email": "robert.kim@techcorp-demo.com",
        "password": "Demo123!",
        "name": "Robert Kim",
        "role": "reviewer"
    }
}


class TestDemoLogin:
    """Test demo user login functionality"""
    
    @pytest.fixture
    def api_client(self):
        """Create a requests session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session
    
    def test_admin_login(self, api_client):
        """Test Admin (Sarah Chen) login"""
        user = DEMO_USERS["admin"]
        response = api_client.post(f"{BASE_URL}/auth/login", json={
            "email": user["email"],
            "password": user["password"]
        })
        
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Login response should have success=True"
        assert "user" in data, "Login response should contain user data"
        assert data["user"]["email"] == user["email"], "User email should match"
        assert data["user"]["full_name"] == user["name"], f"User name should be {user['name']}"
        print(f"SUCCESS: Admin login - {user['name']}")
    
    def test_manager_login(self, api_client):
        """Test Manager (Michael Rodriguez) login"""
        user = DEMO_USERS["manager"]
        response = api_client.post(f"{BASE_URL}/auth/login", json={
            "email": user["email"],
            "password": user["password"]
        })
        
        assert response.status_code == 200, f"Manager login failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Login response should have success=True"
        assert "user" in data, "Login response should contain user data"
        assert data["user"]["email"] == user["email"], "User email should match"
        assert data["user"]["full_name"] == user["name"], f"User name should be {user['name']}"
        print(f"SUCCESS: Manager login - {user['name']}")
    
    def test_creator_login(self, api_client):
        """Test Creator (Alex Martinez) login"""
        user = DEMO_USERS["creator"]
        response = api_client.post(f"{BASE_URL}/auth/login", json={
            "email": user["email"],
            "password": user["password"]
        })
        
        assert response.status_code == 200, f"Creator login failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Login response should have success=True"
        assert "user" in data, "Login response should contain user data"
        assert data["user"]["email"] == user["email"], "User email should match"
        assert data["user"]["full_name"] == user["name"], f"User name should be {user['name']}"
        print(f"SUCCESS: Creator login - {user['name']}")
    
    def test_reviewer_login(self, api_client):
        """Test Reviewer (Robert Kim) login"""
        user = DEMO_USERS["reviewer"]
        response = api_client.post(f"{BASE_URL}/auth/login", json={
            "email": user["email"],
            "password": user["password"]
        })
        
        assert response.status_code == 200, f"Reviewer login failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Login response should have success=True"
        assert "user" in data, "Login response should contain user data"
        assert data["user"]["email"] == user["email"], "User email should match"
        assert data["user"]["full_name"] == user["name"], f"User name should be {user['name']}"
        print(f"SUCCESS: Reviewer login - {user['name']}")
    
    def test_invalid_password(self, api_client):
        """Test login with invalid password"""
        response = api_client.post(f"{BASE_URL}/auth/login", json={
            "email": "sarah.chen@techcorp-demo.com",
            "password": "WrongPassword123!"
        })
        
        assert response.status_code in [401, 400], f"Invalid password should return 401 or 400, got {response.status_code}"
        print("SUCCESS: Invalid password correctly rejected")
    
    def test_invalid_email(self, api_client):
        """Test login with non-existent email"""
        response = api_client.post(f"{BASE_URL}/auth/login", json={
            "email": "nonexistent@techcorp-demo.com",
            "password": "Demo123!"
        })
        
        assert response.status_code in [401, 400, 404], f"Invalid email should return 401/400/404, got {response.status_code}"
        print("SUCCESS: Invalid email correctly rejected")


class TestDemoUserData:
    """Test demo user data in database"""
    
    @pytest.fixture
    def api_client(self):
        """Create a requests session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session
    
    def test_admin_has_correct_role(self, api_client):
        """Verify admin user has correct role after login"""
        user = DEMO_USERS["admin"]
        response = api_client.post(f"{BASE_URL}/auth/login", json={
            "email": user["email"],
            "password": user["password"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "admin", f"Admin should have role 'admin', got {data['user'].get('role')}"
        print(f"SUCCESS: Admin has correct role")
    
    def test_manager_has_correct_role(self, api_client):
        """Verify manager user has correct role after login"""
        user = DEMO_USERS["manager"]
        response = api_client.post(f"{BASE_URL}/auth/login", json={
            "email": user["email"],
            "password": user["password"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "manager", f"Manager should have role 'manager', got {data['user'].get('role')}"
        print(f"SUCCESS: Manager has correct role")
    
    def test_creator_has_correct_role(self, api_client):
        """Verify creator user has correct role after login"""
        user = DEMO_USERS["creator"]
        response = api_client.post(f"{BASE_URL}/auth/login", json={
            "email": user["email"],
            "password": user["password"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "creator", f"Creator should have role 'creator', got {data['user'].get('role')}"
        print(f"SUCCESS: Creator has correct role")
    
    def test_reviewer_has_correct_role(self, api_client):
        """Verify reviewer user has correct role after login"""
        user = DEMO_USERS["reviewer"]
        response = api_client.post(f"{BASE_URL}/auth/login", json={
            "email": user["email"],
            "password": user["password"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "reviewer", f"Reviewer should have role 'reviewer', got {data['user'].get('role')}"
        print(f"SUCCESS: Reviewer has correct role")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
