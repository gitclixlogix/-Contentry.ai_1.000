"""
Test Auto-Refill Feature for Credits
Tests the auto-refill API endpoints for credit management.

Endpoints tested:
- GET /api/v1/credits/auto-refill/settings - Get user's auto-refill configuration
- PUT /api/v1/credits/auto-refill/settings - Update auto-refill settings
- GET /api/v1/credits/auto-refill/history - Get auto-refill transaction history
- POST /api/v1/credits/auto-refill/trigger - Manually trigger auto-refill check
- GET /api/v1/credits/auto-refill/packs - Get available credit packs
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://admin-portal-278.preview.emergentagent.com')
if not BASE_URL.endswith('/api/v1'):
    BASE_URL = f"{BASE_URL.rstrip('/')}/api/v1"

# Demo user credentials - Admin has settings.edit permission
ADMIN_USER = {
    "email": "sarah.chen@techcorp-demo.com",
    "password": "Demo123!",
    "name": "Sarah Chen"
}

# Creator user for testing
CREATOR_USER = {
    "email": "alex.martinez@techcorp-demo.com",
    "password": "Demo123!",
    "name": "Alex Martinez"
}


class TestAutoRefillPacks:
    """Test auto-refill packs endpoint (no auth required)"""
    
    @pytest.fixture
    def api_client(self):
        """Create a requests session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session
    
    def test_get_auto_refill_packs(self, api_client):
        """Test GET /credits/auto-refill/packs - returns available credit packs"""
        response = api_client.get(f"{BASE_URL}/credits/auto-refill/packs")
        
        assert response.status_code == 200, f"Failed to get packs: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, "Response should have success=True"
        assert "data" in data, "Response should contain data"
        assert "packs" in data["data"], "Data should contain packs"
        
        packs = data["data"]["packs"]
        assert len(packs) == 4, f"Should have 4 packs, got {len(packs)}"
        
        # Verify pack structure
        pack_ids = [p["id"] for p in packs]
        assert "starter" in pack_ids, "Should have starter pack"
        assert "standard" in pack_ids, "Should have standard pack"
        assert "growth" in pack_ids, "Should have growth pack"
        assert "scale" in pack_ids, "Should have scale pack"
        
        # Verify pack details
        for pack in packs:
            assert "id" in pack, "Pack should have id"
            assert "name" in pack, "Pack should have name"
            assert "credits" in pack, "Pack should have credits"
            assert "price_usd" in pack, "Pack should have price_usd"
            assert "per_credit_rate" in pack, "Pack should have per_credit_rate"
            assert "savings_percent" in pack, "Pack should have savings_percent"
        
        print(f"SUCCESS: Got {len(packs)} credit packs")
        for pack in packs:
            print(f"  - {pack['name']}: {pack['credits']} credits @ ${pack['price_usd']}")


class TestAutoRefillSettings:
    """Test auto-refill settings endpoints (requires auth)"""
    
    @pytest.fixture
    def api_client(self):
        """Create a requests session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session
    
    @pytest.fixture
    def admin_auth(self, api_client):
        """Login as admin and get user ID"""
        response = api_client.post(f"{BASE_URL}/auth/login", json={
            "email": ADMIN_USER["email"],
            "password": ADMIN_USER["password"]
        })
        
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.text}")
        
        data = response.json()
        user_id = data.get("user", {}).get("id")
        if not user_id:
            pytest.skip("Could not get user ID from login response")
        
        return user_id
    
    @pytest.fixture
    def creator_auth(self, api_client):
        """Login as creator and get user ID"""
        response = api_client.post(f"{BASE_URL}/auth/login", json={
            "email": CREATOR_USER["email"],
            "password": CREATOR_USER["password"]
        })
        
        if response.status_code != 200:
            pytest.skip(f"Creator login failed: {response.text}")
        
        data = response.json()
        user_id = data.get("user", {}).get("id")
        if not user_id:
            pytest.skip("Could not get user ID from login response")
        
        return user_id
    
    def test_get_auto_refill_settings_default(self, api_client, admin_auth):
        """Test GET /credits/auto-refill/settings - returns default settings for new user"""
        response = api_client.get(
            f"{BASE_URL}/credits/auto-refill/settings",
            headers={"X-User-ID": admin_auth}
        )
        
        assert response.status_code == 200, f"Failed to get settings: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, "Response should have success=True"
        assert "data" in data, "Response should contain data"
        
        settings = data["data"]
        assert "enabled" in settings, "Settings should have enabled field"
        assert "threshold_credits" in settings, "Settings should have threshold_credits"
        assert "refill_pack_id" in settings, "Settings should have refill_pack_id"
        assert "max_refills_per_month" in settings, "Settings should have max_refills_per_month"
        assert "pack_details" in settings, "Settings should have pack_details"
        
        # Default values
        assert settings["threshold_credits"] == 100, "Default threshold should be 100"
        assert settings["refill_pack_id"] == "standard", "Default pack should be standard"
        assert settings["max_refills_per_month"] == 3, "Default max refills should be 3"
        
        print(f"SUCCESS: Got auto-refill settings - enabled={settings['enabled']}")
    
    def test_update_auto_refill_settings_enable(self, api_client, admin_auth):
        """Test PUT /credits/auto-refill/settings - enable auto-refill"""
        payload = {
            "enabled": True,
            "threshold_credits": 200,
            "refill_pack_id": "growth",
            "max_refills_per_month": 5
        }
        
        response = api_client.put(
            f"{BASE_URL}/credits/auto-refill/settings",
            headers={"X-User-ID": admin_auth},
            json=payload
        )
        
        assert response.status_code == 200, f"Failed to update settings: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, "Response should have success=True"
        assert "data" in data, "Response should contain data"
        
        settings = data["data"]
        assert settings["enabled"] == True, "Auto-refill should be enabled"
        assert settings["threshold_credits"] == 200, "Threshold should be 200"
        assert settings["refill_pack_id"] == "growth", "Pack should be growth"
        assert settings["max_refills_per_month"] == 5, "Max refills should be 5"
        
        print(f"SUCCESS: Enabled auto-refill with threshold={settings['threshold_credits']}")
    
    def test_update_auto_refill_settings_disable(self, api_client, admin_auth):
        """Test PUT /credits/auto-refill/settings - disable auto-refill"""
        payload = {
            "enabled": False,
            "threshold_credits": 100,
            "refill_pack_id": "standard",
            "max_refills_per_month": 3
        }
        
        response = api_client.put(
            f"{BASE_URL}/credits/auto-refill/settings",
            headers={"X-User-ID": admin_auth},
            json=payload
        )
        
        assert response.status_code == 200, f"Failed to update settings: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, "Response should have success=True"
        settings = data["data"]
        assert settings["enabled"] == False, "Auto-refill should be disabled"
        
        print("SUCCESS: Disabled auto-refill")
    
    def test_update_auto_refill_invalid_pack(self, api_client, admin_auth):
        """Test PUT /credits/auto-refill/settings - invalid pack ID returns error"""
        payload = {
            "enabled": True,
            "threshold_credits": 100,
            "refill_pack_id": "invalid_pack",
            "max_refills_per_month": 3
        }
        
        response = api_client.put(
            f"{BASE_URL}/credits/auto-refill/settings",
            headers={"X-User-ID": admin_auth},
            json=payload
        )
        
        assert response.status_code == 400, f"Should return 400 for invalid pack: {response.text}"
        print("SUCCESS: Invalid pack ID correctly rejected")
    
    def test_update_auto_refill_threshold_validation(self, api_client, admin_auth):
        """Test PUT /credits/auto-refill/settings - threshold validation"""
        # Test threshold too low
        payload = {
            "enabled": True,
            "threshold_credits": 5,  # Below minimum of 10
            "refill_pack_id": "standard",
            "max_refills_per_month": 3
        }
        
        response = api_client.put(
            f"{BASE_URL}/credits/auto-refill/settings",
            headers={"X-User-ID": admin_auth},
            json=payload
        )
        
        assert response.status_code == 400, f"Should return 400 for threshold < 10: {response.text}"
        print("SUCCESS: Low threshold correctly rejected")
    
    def test_update_auto_refill_max_refills_validation(self, api_client, admin_auth):
        """Test PUT /credits/auto-refill/settings - max refills validation"""
        # Test max refills too high
        payload = {
            "enabled": True,
            "threshold_credits": 100,
            "refill_pack_id": "standard",
            "max_refills_per_month": 15  # Above maximum of 10
        }
        
        response = api_client.put(
            f"{BASE_URL}/credits/auto-refill/settings",
            headers={"X-User-ID": admin_auth},
            json=payload
        )
        
        assert response.status_code == 400, f"Should return 400 for max_refills > 10: {response.text}"
        print("SUCCESS: High max_refills correctly rejected")


class TestAutoRefillHistory:
    """Test auto-refill history endpoint"""
    
    @pytest.fixture
    def api_client(self):
        """Create a requests session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session
    
    @pytest.fixture
    def admin_auth(self, api_client):
        """Login as admin and get user ID"""
        response = api_client.post(f"{BASE_URL}/auth/login", json={
            "email": ADMIN_USER["email"],
            "password": ADMIN_USER["password"]
        })
        
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.text}")
        
        data = response.json()
        user_id = data.get("user", {}).get("id")
        if not user_id:
            pytest.skip("Could not get user ID from login response")
        
        return user_id
    
    def test_get_auto_refill_history(self, api_client, admin_auth):
        """Test GET /credits/auto-refill/history - returns history"""
        response = api_client.get(
            f"{BASE_URL}/credits/auto-refill/history",
            headers={"X-User-ID": admin_auth}
        )
        
        assert response.status_code == 200, f"Failed to get history: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, "Response should have success=True"
        assert "data" in data, "Response should contain data"
        assert "history" in data["data"], "Data should contain history"
        assert "count" in data["data"], "Data should contain count"
        
        history = data["data"]["history"]
        assert isinstance(history, list), "History should be a list"
        
        print(f"SUCCESS: Got auto-refill history with {len(history)} records")


class TestAutoRefillTrigger:
    """Test auto-refill trigger endpoint"""
    
    @pytest.fixture
    def api_client(self):
        """Create a requests session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session
    
    @pytest.fixture
    def admin_auth(self, api_client):
        """Login as admin and get user ID"""
        response = api_client.post(f"{BASE_URL}/auth/login", json={
            "email": ADMIN_USER["email"],
            "password": ADMIN_USER["password"]
        })
        
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.text}")
        
        data = response.json()
        user_id = data.get("user", {}).get("id")
        if not user_id:
            pytest.skip("Could not get user ID from login response")
        
        return user_id
    
    def test_trigger_auto_refill_disabled(self, api_client, admin_auth):
        """Test POST /credits/auto-refill/trigger - when disabled"""
        # First ensure auto-refill is disabled
        api_client.put(
            f"{BASE_URL}/credits/auto-refill/settings",
            headers={"X-User-ID": admin_auth},
            json={
                "enabled": False,
                "threshold_credits": 100,
                "refill_pack_id": "standard",
                "max_refills_per_month": 3
            }
        )
        
        # Try to trigger
        response = api_client.post(
            f"{BASE_URL}/credits/auto-refill/trigger",
            headers={"X-User-ID": admin_auth}
        )
        
        assert response.status_code == 200, f"Failed to trigger: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, "Response should have success=True"
        assert data.get("triggered") == False, "Should not trigger when disabled"
        assert data.get("reason") == "disabled", "Reason should be 'disabled'"
        
        print("SUCCESS: Auto-refill trigger correctly returns not triggered when disabled")
    
    def test_trigger_auto_refill_above_threshold(self, api_client, admin_auth):
        """Test POST /credits/auto-refill/trigger - when above threshold"""
        # Enable auto-refill with low threshold
        api_client.put(
            f"{BASE_URL}/credits/auto-refill/settings",
            headers={"X-User-ID": admin_auth},
            json={
                "enabled": True,
                "threshold_credits": 10,  # Very low threshold
                "refill_pack_id": "standard",
                "max_refills_per_month": 3
            }
        )
        
        # Try to trigger (user likely has more than 10 credits)
        response = api_client.post(
            f"{BASE_URL}/credits/auto-refill/trigger",
            headers={"X-User-ID": admin_auth}
        )
        
        assert response.status_code == 200, f"Failed to trigger: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, "Response should have success=True"
        # If user has > 10 credits, should not trigger
        if data.get("triggered") == False:
            assert data.get("reason") == "above_threshold", "Reason should be 'above_threshold'"
            print("SUCCESS: Auto-refill not triggered - balance above threshold")
        else:
            # If triggered, verify the response structure
            assert "pack_id" in data, "Triggered response should have pack_id"
            assert "credits" in data, "Triggered response should have credits"
            print(f"SUCCESS: Auto-refill triggered for {data.get('credits')} credits")
        
        # Clean up - disable auto-refill
        api_client.put(
            f"{BASE_URL}/credits/auto-refill/settings",
            headers={"X-User-ID": admin_auth},
            json={
                "enabled": False,
                "threshold_credits": 100,
                "refill_pack_id": "standard",
                "max_refills_per_month": 3
            }
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
