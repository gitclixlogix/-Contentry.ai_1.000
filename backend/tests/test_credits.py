"""
Credit System API Tests for Contentry.ai
Tests credit balance, packs, plans, consumption, and history endpoints.

Based on Pricing Strategy v3.0:
- Free: 25 credits/month
- Creator: 750 credits/month ($19/mo)
- Pro: 1,500 credits/month ($49/mo)
- Team: 5,000 credits/month ($249/mo)
- Business: 15,000 credits/month ($499/mo)

Credit Packs:
- Starter: 100 credits / $6
- Standard: 500 credits / $22.50
- Growth: 1000 credits / $40
- Scale: 5000 credits / $175
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://admin-portal-278.preview.emergentagent.com')
if BASE_URL and not BASE_URL.startswith('http'):
    BASE_URL = f"https://{BASE_URL}"
BASE_URL = BASE_URL.rstrip('/')

# Test credentials
TEST_USER_EMAIL = "alex.martinez@techcorp-demo.com"
TEST_USER_PASSWORD = "DemoCreator!123"


@pytest.fixture(scope="module")
def api_session():
    """Create a session with authentication"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Login to get auth cookies
    login_response = session.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    )
    
    if login_response.status_code == 200:
        data = login_response.json()
        user_id = data.get("user", {}).get("id")
        if user_id:
            session.headers.update({"X-User-ID": user_id})
    
    return session


class TestCreditPacks:
    """Test credit pack endpoints (public)"""
    
    def test_get_credit_packs_returns_all_packs(self):
        """Test 2: GET /credits/packs - Returns all 4 credit packs"""
        response = requests.get(f"{BASE_URL}/api/v1/credits/packs")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert "packs" in data["data"]
        
        packs = data["data"]["packs"]
        assert len(packs) == 4, f"Expected 4 packs, got {len(packs)}"
    
    def test_credit_packs_have_correct_prices(self):
        """Test 2: Verify credit pack prices match v3.0 pricing"""
        response = requests.get(f"{BASE_URL}/api/v1/credits/packs?currency=USD")
        
        assert response.status_code == 200
        data = response.json()
        packs = {p["id"]: p for p in data["data"]["packs"]}
        
        # Verify Starter Pack: 100 credits / $6
        assert packs["starter"]["credits"] == 100
        assert packs["starter"]["price"] == 6.0
        assert packs["starter"]["price_usd"] == 6.0
        
        # Verify Standard Pack: 500 credits / $22.50
        assert packs["standard"]["credits"] == 500
        assert packs["standard"]["price"] == 22.5
        assert packs["standard"]["price_usd"] == 22.5
        
        # Verify Growth Pack: 1000 credits / $40
        assert packs["growth"]["credits"] == 1000
        assert packs["growth"]["price"] == 40.0
        assert packs["growth"]["price_usd"] == 40.0
        
        # Verify Scale Pack: 5000 credits / $175
        assert packs["scale"]["credits"] == 5000
        assert packs["scale"]["price"] == 175.0
        assert packs["scale"]["price_usd"] == 175.0
    
    def test_credit_packs_have_savings_percent(self):
        """Verify credit packs show correct savings percentages"""
        response = requests.get(f"{BASE_URL}/api/v1/credits/packs")
        
        assert response.status_code == 200
        packs = {p["id"]: p for p in response.json()["data"]["packs"]}
        
        assert packs["starter"]["savings_percent"] == 0
        assert packs["standard"]["savings_percent"] == 10
        assert packs["growth"]["savings_percent"] == 20
        assert packs["scale"]["savings_percent"] == 30


class TestCreditPlans:
    """Test subscription plan endpoints"""
    
    def test_get_plans_returns_all_tiers(self):
        """Test 3: GET /credits/plans - Returns all plan tiers"""
        response = requests.get(f"{BASE_URL}/api/v1/credits/plans")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert "plans" in data["data"]
        
        plans = data["data"]["plans"]
        plan_ids = [p["id"] for p in plans]
        
        # Verify all tiers exist
        expected_tiers = ["free", "creator", "pro", "team", "business", "enterprise"]
        for tier in expected_tiers:
            assert tier in plan_ids, f"Missing plan tier: {tier}"
    
    def test_plans_have_correct_credit_allowances(self):
        """Test 3: Verify plan credit allowances match v3.0 pricing"""
        response = requests.get(f"{BASE_URL}/api/v1/credits/plans")
        
        assert response.status_code == 200
        plans = {p["id"]: p for p in response.json()["data"]["plans"]}
        
        # Verify credit allowances
        assert plans["free"]["monthly_credits"] == 25
        assert plans["creator"]["monthly_credits"] == 750
        assert plans["pro"]["monthly_credits"] == 1500
        assert plans["team"]["monthly_credits"] == 5000
        assert plans["business"]["monthly_credits"] == 15000
        assert plans["enterprise"]["monthly_credits"] == -1  # Custom
    
    def test_plans_have_overage_rates(self):
        """Verify plans have correct overage rates"""
        response = requests.get(f"{BASE_URL}/api/v1/credits/plans")
        
        assert response.status_code == 200
        plans = {p["id"]: p for p in response.json()["data"]["plans"]}
        
        assert plans["free"]["overage_rate"] == 0.06
        assert plans["creator"]["overage_rate"] == 0.05
        assert plans["pro"]["overage_rate"] == 0.04
        assert plans["team"]["overage_rate"] == 0.035
        assert plans["business"]["overage_rate"] == 0.03
        assert plans["enterprise"]["overage_rate"] == 0.025


class TestCreditBalance:
    """Test credit balance endpoint (authenticated)"""
    
    def test_get_balance_returns_user_credits(self, api_session):
        """Test 1: GET /credits/balance - Returns correct balance and plan info"""
        response = api_session.get(f"{BASE_URL}/api/v1/credits/balance")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        
        balance_data = data["data"]
        
        # Verify required fields
        assert "user_id" in balance_data
        assert "plan" in balance_data
        assert "plan_name" in balance_data
        assert "credits_balance" in balance_data
        assert "credits_used_this_month" in balance_data
        assert "monthly_allowance" in balance_data
        assert "features" in balance_data
        assert "limits" in balance_data
    
    def test_balance_has_billing_cycle_info(self, api_session):
        """Verify balance includes billing cycle dates"""
        response = api_session.get(f"{BASE_URL}/api/v1/credits/balance")
        
        assert response.status_code == 200
        balance_data = response.json()["data"]
        
        assert "billing_cycle_start" in balance_data
        assert "billing_cycle_end" in balance_data
        assert "overage_rate" in balance_data
    
    def test_balance_requires_authentication(self):
        """Verify balance endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/v1/credits/balance")
        
        # Should fail without auth
        assert response.status_code in [401, 403, 422]


class TestCreditConsumption:
    """Test credit consumption endpoint"""
    
    def test_consume_credits_deducts_balance(self, api_session):
        """Test 4: POST /credits/consume - Correctly deducts credits"""
        # Get initial balance
        balance_before = api_session.get(f"{BASE_URL}/api/v1/credits/balance").json()["data"]["credits_balance"]
        
        # Consume credits (quick_analysis = 2 credits)
        response = api_session.post(
            f"{BASE_URL}/api/v1/credits/consume",
            json={"action": "quick_analysis", "quantity": 1}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["credits_consumed"] == 2
        assert data["data"]["balance_before"] == balance_before
        assert data["data"]["balance_after"] == balance_before - 2
    
    def test_consume_credits_logs_transaction(self, api_session):
        """Test 4: Verify consumption creates transaction record"""
        response = api_session.post(
            f"{BASE_URL}/api/v1/credits/consume",
            json={"action": "export_to_pdf", "quantity": 1}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "transaction" in data["data"]
        transaction = data["data"]["transaction"]
        
        assert transaction["action"] == "export_to_pdf"
        assert transaction["credits_consumed"] == 1
        assert "created_at" in transaction
    
    def test_consume_invalid_action_fails(self, api_session):
        """Verify invalid action returns error"""
        response = api_session.post(
            f"{BASE_URL}/api/v1/credits/consume",
            json={"action": "invalid_action", "quantity": 1}
        )
        
        assert response.status_code == 400


class TestCreditHistory:
    """Test credit history endpoint"""
    
    def test_get_history_returns_transactions(self, api_session):
        """Test 5: GET /credits/history - Returns transaction history"""
        response = api_session.get(f"{BASE_URL}/api/v1/credits/history")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert "transactions" in data["data"]
        assert "count" in data["data"]
        
        # Should have at least one transaction from previous tests
        assert len(data["data"]["transactions"]) > 0
    
    def test_history_transactions_have_required_fields(self, api_session):
        """Verify transaction records have all required fields"""
        response = api_session.get(f"{BASE_URL}/api/v1/credits/history")
        
        assert response.status_code == 200
        transactions = response.json()["data"]["transactions"]
        
        if len(transactions) > 0:
            tx = transactions[0]
            assert "user_id" in tx
            assert "action" in tx
            assert "credits_consumed" in tx
            assert "balance_before" in tx
            assert "balance_after" in tx
            assert "created_at" in tx
    
    def test_history_supports_pagination(self, api_session):
        """Verify history supports limit and skip parameters"""
        response = api_session.get(f"{BASE_URL}/api/v1/credits/history?limit=5&skip=0")
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        assert data["limit"] == 5
        assert data["skip"] == 0


class TestCreditCosts:
    """Test credit costs endpoint (public)"""
    
    def test_get_costs_returns_all_actions(self):
        """Verify costs endpoint returns all action costs"""
        response = requests.get(f"{BASE_URL}/api/v1/credits/costs")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "costs" in data["data"]
        assert "categorized" in data["data"]
        
        costs = data["data"]["costs"]
        
        # Verify key action costs
        assert costs["content_analysis"] == 5
        assert costs["quick_analysis"] == 2
        assert costs["content_generation"] == 10
        assert costs["image_generation"] == 20
        assert costs["approval_workflow"] == 0  # Free action
    
    def test_costs_are_categorized(self):
        """Verify costs are properly categorized"""
        response = requests.get(f"{BASE_URL}/api/v1/credits/costs")
        
        assert response.status_code == 200
        categorized = response.json()["data"]["categorized"]
        
        expected_categories = [
            "core_content",
            "image_media",
            "voice_audio",
            "sentiment_analysis",
            "publishing",
            "advanced",
            "free_actions"
        ]
        
        for category in expected_categories:
            assert category in categorized, f"Missing category: {category}"


class TestCreditCheck:
    """Test credit check endpoint"""
    
    def test_check_credits_available(self, api_session):
        """Verify check endpoint returns availability info"""
        response = api_session.get(f"{BASE_URL}/api/v1/credits/check/content_analysis?quantity=1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "has_enough" in data["data"]
        assert "credits_required" in data["data"]
        assert "credits_available" in data["data"]
        assert data["data"]["credits_required"] == 5  # content_analysis cost


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
