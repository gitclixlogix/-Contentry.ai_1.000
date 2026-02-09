"""
Test Suite for Subscription Checkout and Location-Based Pricing
Tests:
- POST /api/v1/subscriptions/checkout - Subscription checkout with Stripe
- GET /api/v1/payments/plans - Location-based pricing with country codes
- Free plan activation
- Demo user login flow
"""
import pytest
import requests
import os

BASE_URL = "http://localhost:8001/api/v1"

# Demo user credentials
DEMO_EMAIL = "user@demo.com"
DEMO_PASSWORD = "DemoUser!123"


class TestDemoUserLogin:
    """Test demo user login flow"""
    
    def test_create_demo_user(self):
        """Create demo user if not exists"""
        response = requests.post(
            f"{BASE_URL}/auth/create-demo-user",
            json={
                "id": "demo-user-id",
                "email": DEMO_EMAIL,
                "name": "Demo User",
                "role": "user"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "user" in data or "message" in data
        print(f"✓ Demo user creation: {data.get('message', 'created')}")
    
    def test_demo_user_login(self):
        """Login with demo user credentials"""
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == DEMO_EMAIL
        print(f"✓ Demo user login successful: {data['user']['email']}")
        return data["user"]


class TestLocationBasedPricing:
    """Test GET /api/v1/payments/plans with location-based pricing"""
    
    def test_plans_default_usd(self):
        """Get plans without country code - should return USD"""
        response = requests.get(f"{BASE_URL}/payments/plans")
        assert response.status_code == 200
        data = response.json()
        
        assert "plans" in data
        assert "currency" in data
        assert data["currency"] == "usd"
        assert data["currency_symbol"] == "$"
        
        # Verify plans structure
        plans = data["plans"]
        assert len(plans) > 0
        
        # Check plan structure
        for plan in plans:
            assert "id" in plan
            assert "name" in plan
            assert "credits" in plan
            assert "monthly_price" in plan
            assert "annual_price" in plan
            assert "currency" in plan
        
        print(f"✓ Default USD pricing: {len(plans)} plans returned")
    
    def test_plans_us_country_code(self):
        """Get plans with US country code - should return USD"""
        response = requests.get(f"{BASE_URL}/payments/plans?country_code=US")
        assert response.status_code == 200
        data = response.json()
        
        assert data["currency"] == "usd"
        assert data["currency_symbol"] == "$"
        print(f"✓ US country code returns USD pricing")
    
    def test_plans_gb_country_code(self):
        """Get plans with GB country code - should return GBP"""
        response = requests.get(f"{BASE_URL}/payments/plans?country_code=GB")
        assert response.status_code == 200
        data = response.json()
        
        assert data["currency"] == "gbp"
        assert data["currency_symbol"] == "£"
        
        # Verify GBP prices are different from USD
        plans = data["plans"]
        starter_plan = next((p for p in plans if p["id"] == "starter"), None)
        if starter_plan:
            assert starter_plan["monthly_price"] == 7.99  # GBP price
            print(f"✓ GB country code returns GBP pricing: £{starter_plan['monthly_price']}/mo")
    
    def test_plans_de_country_code(self):
        """Get plans with DE country code - should return EUR"""
        response = requests.get(f"{BASE_URL}/payments/plans?country_code=DE")
        assert response.status_code == 200
        data = response.json()
        
        assert data["currency"] == "eur"
        assert data["currency_symbol"] == "€"
        
        plans = data["plans"]
        starter_plan = next((p for p in plans if p["id"] == "starter"), None)
        if starter_plan:
            assert starter_plan["monthly_price"] == 9.49  # EUR price
            print(f"✓ DE country code returns EUR pricing: €{starter_plan['monthly_price']}/mo")
    
    def test_plans_no_country_code(self):
        """Get plans with NO country code - should return NOK"""
        response = requests.get(f"{BASE_URL}/payments/plans?country_code=NO")
        assert response.status_code == 200
        data = response.json()
        
        assert data["currency"] == "nok"
        assert data["currency_symbol"] == "kr"
        
        plans = data["plans"]
        starter_plan = next((p for p in plans if p["id"] == "starter"), None)
        if starter_plan:
            assert starter_plan["monthly_price"] == 109.00  # NOK price
            print(f"✓ NO country code returns NOK pricing: kr{starter_plan['monthly_price']}/mo")
    
    def test_plans_unknown_country_defaults_usd(self):
        """Get plans with unknown country code - should default to USD"""
        response = requests.get(f"{BASE_URL}/payments/plans?country_code=XX")
        assert response.status_code == 200
        data = response.json()
        
        assert data["currency"] == "usd"
        print(f"✓ Unknown country code defaults to USD")
    
    def test_plans_currency_override(self):
        """Test currency parameter overrides country code"""
        response = requests.get(f"{BASE_URL}/payments/plans?country_code=US&currency=eur")
        assert response.status_code == 200
        data = response.json()
        
        # Currency parameter should take precedence
        assert data["currency"] == "eur"
        print(f"✓ Currency parameter overrides country code")


class TestSubscriptionCheckout:
    """Test POST /api/v1/subscriptions/checkout"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup demo user for checkout tests"""
        # Create demo user
        requests.post(
            f"{BASE_URL}/auth/create-demo-user",
            json={
                "id": "demo-user-id",
                "email": DEMO_EMAIL,
                "name": "Demo User",
                "role": "user"
            }
        )
        
        # Login to get user info
        login_response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD
        })
        if login_response.status_code == 200:
            self.user = login_response.json().get("user", {})
            self.user_id = self.user.get("id", "demo-user-id")
        else:
            self.user_id = "demo-user-id"
    
    def test_checkout_free_plan(self):
        """Free plan should activate directly without Stripe"""
        response = requests.post(
            f"{BASE_URL}/subscriptions/checkout",
            json={
                "package_id": "free",
                "billing_cycle": "monthly",
                "origin_url": "https://test.example.com",
                "user_id": self.user_id
            },
            headers={"X-User-ID": self.user_id}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Free plan returns success without checkout URL
        assert data.get("success") == True or "redirect" in data
        assert "message" in data or "redirect" in data
        print(f"✓ Free plan activation: {data.get('message', 'activated')}")
    
    def test_checkout_starter_plan_returns_stripe_url(self):
        """Starter plan checkout should return Stripe URL"""
        response = requests.post(
            f"{BASE_URL}/subscriptions/checkout",
            json={
                "package_id": "starter",
                "billing_cycle": "monthly",
                "origin_url": "https://test.example.com",
                "user_id": self.user_id
            },
            headers={"X-User-ID": self.user_id}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return url and session_id (not nested in data.data)
        assert "url" in data, f"Expected 'url' in response, got: {data.keys()}"
        assert "session_id" in data, f"Expected 'session_id' in response, got: {data.keys()}"
        
        # URL should be Stripe checkout URL
        assert "stripe.com" in data["url"] or "checkout.stripe.com" in data["url"]
        assert data["session_id"].startswith("cs_")
        
        print(f"✓ Starter plan checkout URL: {data['url'][:50]}...")
        print(f"✓ Session ID: {data['session_id']}")
    
    def test_checkout_creator_plan_monthly(self):
        """Creator plan monthly checkout"""
        response = requests.post(
            f"{BASE_URL}/subscriptions/checkout",
            json={
                "package_id": "creator",
                "billing_cycle": "monthly",
                "origin_url": "https://test.example.com",
                "user_id": self.user_id
            },
            headers={"X-User-ID": self.user_id}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "url" in data
        assert "session_id" in data
        assert "stripe.com" in data["url"]
        print(f"✓ Creator plan monthly checkout successful")
    
    def test_checkout_creator_plan_annual(self):
        """Creator plan annual checkout"""
        response = requests.post(
            f"{BASE_URL}/subscriptions/checkout",
            json={
                "package_id": "creator",
                "billing_cycle": "annual",
                "origin_url": "https://test.example.com",
                "user_id": self.user_id
            },
            headers={"X-User-ID": self.user_id}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "url" in data
        assert "session_id" in data
        print(f"✓ Creator plan annual checkout successful")
    
    def test_checkout_pro_plan(self):
        """Pro plan checkout"""
        response = requests.post(
            f"{BASE_URL}/subscriptions/checkout",
            json={
                "package_id": "pro",
                "billing_cycle": "monthly",
                "origin_url": "https://test.example.com",
                "user_id": self.user_id
            },
            headers={"X-User-ID": self.user_id}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "url" in data
        assert "session_id" in data
        print(f"✓ Pro plan checkout successful")
    
    def test_checkout_invalid_package(self):
        """Invalid package should return 400"""
        response = requests.post(
            f"{BASE_URL}/subscriptions/checkout",
            json={
                "package_id": "invalid_plan",
                "billing_cycle": "monthly",
                "origin_url": "https://test.example.com",
                "user_id": self.user_id
            },
            headers={"X-User-ID": self.user_id}
        )
        assert response.status_code == 400
        print(f"✓ Invalid package returns 400")
    
    def test_checkout_enterprise_requires_sales(self):
        """Enterprise plan should require contacting sales"""
        response = requests.post(
            f"{BASE_URL}/subscriptions/checkout",
            json={
                "package_id": "enterprise",
                "billing_cycle": "monthly",
                "origin_url": "https://test.example.com",
                "user_id": self.user_id
            },
            headers={"X-User-ID": self.user_id}
        )
        # Enterprise should return 400 with contact sales message
        assert response.status_code == 400
        print(f"✓ Enterprise plan requires contacting sales")


class TestSubscriptionPackages:
    """Test GET /api/v1/subscriptions/packages endpoint"""
    
    def test_get_packages(self):
        """Get subscription packages"""
        response = requests.get(f"{BASE_URL}/subscriptions/packages")
        assert response.status_code == 200
        data = response.json()
        
        assert "packages" in data
        packages = data["packages"]
        
        # Verify expected packages exist
        expected_packages = ["free", "starter", "creator", "pro"]
        for pkg_id in expected_packages:
            assert pkg_id in packages, f"Missing package: {pkg_id}"
        
        # Verify package structure
        for pkg_id, pkg in packages.items():
            assert "name" in pkg
            assert "credits_monthly" in pkg or "credits" in pkg
        
        print(f"✓ Subscription packages: {list(packages.keys())}")


class TestResponseFormat:
    """Test that checkout response format matches frontend expectations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup demo user"""
        requests.post(
            f"{BASE_URL}/auth/create-demo-user",
            json={
                "id": "demo-user-id",
                "email": DEMO_EMAIL,
                "name": "Demo User",
                "role": "user"
            }
        )
        login_response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD
        })
        if login_response.status_code == 200:
            self.user_id = login_response.json().get("user", {}).get("id", "demo-user-id")
        else:
            self.user_id = "demo-user-id"
    
    def test_checkout_response_format(self):
        """
        Verify checkout response format matches frontend expectations.
        Frontend expects: response.data.url (not response.data.data.checkout_url)
        """
        response = requests.post(
            f"{BASE_URL}/subscriptions/checkout",
            json={
                "package_id": "starter",
                "billing_cycle": "monthly",
                "origin_url": "https://test.example.com",
                "user_id": self.user_id
            },
            headers={"X-User-ID": self.user_id}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Frontend code: const checkoutUrl = response.data?.url || response.data?.data?.checkout_url;
        # Backend should return { url: "...", session_id: "..." }
        
        # Verify direct access to url (not nested)
        assert "url" in data, "Response should have 'url' at top level"
        assert "session_id" in data, "Response should have 'session_id' at top level"
        
        # Verify NOT nested in data.data
        assert "data" not in data or "checkout_url" not in data.get("data", {}), \
            "Response should NOT have nested data.data.checkout_url format"
        
        print(f"✓ Response format correct: {{url, session_id}}")
    
    def test_plans_response_format(self):
        """
        Verify plans response format matches frontend expectations.
        Frontend expects: response.data.plans (array of plan objects)
        """
        response = requests.get(f"{BASE_URL}/payments/plans")
        assert response.status_code == 200
        data = response.json()
        
        # Frontend code: if (response.data?.plans) { ... }
        assert "plans" in data, "Response should have 'plans' array"
        assert isinstance(data["plans"], list), "plans should be an array"
        
        # Verify plan object structure
        if len(data["plans"]) > 0:
            plan = data["plans"][0]
            required_fields = ["id", "name", "credits", "monthly_price", "annual_price", "currency"]
            for field in required_fields:
                assert field in plan, f"Plan should have '{field}' field"
        
        print(f"✓ Plans response format correct: {{plans: [...]}}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
