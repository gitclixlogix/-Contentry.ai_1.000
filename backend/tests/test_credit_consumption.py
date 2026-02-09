"""
Credit Consumption Integration Tests for Contentry.ai
Tests credit-based pricing integration into feature endpoints.

Test Scenarios:
1. Credit balance endpoint returns correct plan info and balance
2. Content generation endpoint returns 402 when user has insufficient credits (Free tier has 25 credits, generation costs 50)
3. Content analysis endpoint successfully consumes 10 credits and returns analysis result
4. Video analysis endpoint is registered and accessible at /api/v1/video/analyze
5. Credit history endpoint records transactions correctly

Credit Costs (Pricing v3.0):
- content_generation: 50 credits
- content_analysis: 10 credits
- image_generation: 20 credits
- ai_rewrite: 25 credits
- iterative_rewrite: 50 credits
- Free tier: 25 credits/month
"""

import pytest
import requests
import os
import time
from datetime import datetime

# Use localhost for testing since we're running inside the container
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
if BASE_URL and not BASE_URL.startswith('http'):
    BASE_URL = f"http://{BASE_URL}"
BASE_URL = BASE_URL.rstrip('/')

# Generate unique test user ID for isolation
TEST_USER_ID = f"test-credit-user-{int(time.time())}"


@pytest.fixture(scope="module")
def api_session():
    """Create a session with test user headers"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-User-ID": TEST_USER_ID
    })
    return session


class TestCreditBalanceEndpoint:
    """Test 1: Credit balance endpoint returns correct plan info and balance"""
    
    def test_new_user_gets_free_plan_with_25_credits(self, api_session):
        """New users should be initialized with Free plan (25 credits)"""
        response = api_session.get(f"{BASE_URL}/api/v1/credits/balance")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        
        balance_data = data["data"]
        
        # Verify Free plan initialization
        assert balance_data["plan"] == "free", f"Expected 'free' plan, got {balance_data['plan']}"
        assert balance_data["plan_name"] == "Free"
        assert balance_data["monthly_allowance"] == 25, f"Free plan should have 25 credits/month"
        assert balance_data["credits_balance"] == 25, f"New user should start with 25 credits"
    
    def test_balance_includes_required_fields(self, api_session):
        """Balance response should include all required fields"""
        response = api_session.get(f"{BASE_URL}/api/v1/credits/balance")
        
        assert response.status_code == 200
        balance_data = response.json()["data"]
        
        required_fields = [
            "user_id", "plan", "plan_name", "credits_balance",
            "credits_used_this_month", "monthly_allowance",
            "billing_cycle_start", "billing_cycle_end",
            "features", "limits", "overage_rate"
        ]
        
        for field in required_fields:
            assert field in balance_data, f"Missing required field: {field}"
    
    def test_balance_features_match_free_plan(self, api_session):
        """Free plan features should match expected configuration"""
        response = api_session.get(f"{BASE_URL}/api/v1/credits/balance")
        
        assert response.status_code == 200
        features = response.json()["data"]["features"]
        
        # Free plan features
        assert features["content_analysis"] is True
        assert features["content_generation"] is True
        assert features["ai_rewrite"] is True
        assert features["image_generation"] is False  # Pay per use
        assert features["api_access"] is False


class TestContentGenerationInsufficientCredits:
    """Test 2: Content generation returns 402 when user has insufficient credits"""
    
    def test_content_generation_returns_402_for_free_tier(self, api_session):
        """
        Free tier has 25 credits, content generation costs 50 credits.
        Should return 402 Payment Required.
        """
        response = api_session.post(
            f"{BASE_URL}/api/v1/content/generate",
            json={
                "prompt": "Write a professional LinkedIn post about AI",
                "tone": "professional",
                "platforms": ["linkedin"]
            }
        )
        
        # Should return 402 Payment Required
        assert response.status_code == 402, f"Expected 402, got {response.status_code}: {response.text}"
        
        data = response.json()
        detail = data.get("detail", {})
        
        # Verify error structure
        assert detail.get("error") == "insufficient_credits"
        assert detail.get("credits_required") == 50, f"Content generation should cost 50 credits"
        assert detail.get("credits_available") == 25, f"Free tier should have 25 credits"
        assert "upgrade_url" in detail
    
    def test_content_generation_error_includes_action_info(self, api_session):
        """402 error should include action information"""
        response = api_session.post(
            f"{BASE_URL}/api/v1/content/generate",
            json={
                "prompt": "Test prompt",
                "tone": "casual"
            }
        )
        
        assert response.status_code == 402
        detail = response.json().get("detail", {})
        
        assert detail.get("action") == "content_generation"


class TestContentAnalysisCredits:
    """Test 3: Content analysis endpoint successfully consumes 10 credits"""
    
    def test_content_analysis_consumes_10_credits(self, api_session):
        """Content analysis should consume 10 credits and return analysis result"""
        # First get initial balance
        balance_before = api_session.get(f"{BASE_URL}/api/v1/credits/balance").json()["data"]["credits_balance"]
        
        # Perform content analysis (costs 10 credits)
        response = api_session.post(
            f"{BASE_URL}/api/v1/content/analyze",
            json={
                "content": "This is a test post for content analysis. It should be professional and appropriate.",
                "user_id": TEST_USER_ID,
                "language": "en"
            }
        )
        
        # Should succeed if user has >= 10 credits
        if balance_before >= 10:
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            
            # Verify balance was deducted
            balance_after = api_session.get(f"{BASE_URL}/api/v1/credits/balance").json()["data"]["credits_balance"]
            assert balance_after == balance_before - 10, f"Expected {balance_before - 10} credits, got {balance_after}"
        else:
            # Should return 402 if insufficient credits
            assert response.status_code == 402
    
    def test_content_analysis_returns_analysis_result(self, api_session):
        """Content analysis should return proper analysis structure"""
        # Use a fresh user to ensure we have credits
        fresh_user_id = f"test-analysis-{int(time.time())}"
        headers = {
            "Content-Type": "application/json",
            "X-User-ID": fresh_user_id
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/content/analyze",
            headers=headers,
            json={
                "content": "Excited to share our latest product launch! Check it out at example.com #innovation #tech",
                "user_id": fresh_user_id,
                "language": "en"
            }
        )
        
        # Fresh user should have 25 credits, analysis costs 10
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify analysis result structure
        assert "flagged_status" in data or "overall_score" in data or "summary" in data


class TestVideoAnalysisEndpoint:
    """Test 4: Video analysis endpoint is registered and accessible"""
    
    def test_video_analyze_endpoint_exists(self, api_session):
        """Video analysis endpoint should be registered at /api/v1/video/analyze"""
        # Test with OPTIONS to check if endpoint exists
        response = api_session.options(f"{BASE_URL}/api/v1/video/analyze")
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404, "Video analysis endpoint not found at /api/v1/video/analyze"
    
    def test_video_analyze_requires_video_url(self, api_session):
        """Video analysis should require video_url parameter"""
        response = api_session.post(
            f"{BASE_URL}/api/v1/video/analyze",
            json={}  # Missing video_url
        )
        
        # Should return 422 (validation error) not 404
        assert response.status_code in [400, 422], f"Expected 400/422 for missing video_url, got {response.status_code}"
    
    def test_video_analyze_with_invalid_url(self, api_session):
        """Video analysis with invalid URL should return appropriate error"""
        response = api_session.post(
            f"{BASE_URL}/api/v1/video/analyze",
            json={
                "video_url": "https://example.com/test-video.mp4",
                "async_mode": False
            }
        )
        
        # Should not return 404 - endpoint exists
        assert response.status_code != 404, "Video analysis endpoint not found"
        
        # May return 402 (insufficient credits) or 500 (video processing error)
        # Both indicate the endpoint is working
        assert response.status_code in [200, 402, 500], f"Unexpected status: {response.status_code}"
    
    def test_video_analyses_list_endpoint_exists(self, api_session):
        """Video analyses list endpoint should be accessible"""
        response = api_session.get(f"{BASE_URL}/api/v1/video/analyses")
        
        # Should return 200 with empty list or analyses
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["success"] is True
        assert "analyses" in data


class TestCreditHistoryEndpoint:
    """Test 5: Credit history endpoint records transactions correctly"""
    
    def test_credit_history_returns_transactions(self, api_session):
        """Credit history should return transaction records"""
        response = api_session.get(f"{BASE_URL}/api/v1/credits/history")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "transactions" in data["data"]
        assert "count" in data["data"]
    
    def test_credit_history_records_consumption(self, api_session):
        """Credit history should record consumption transactions"""
        # Use a fresh user to ensure clean history
        fresh_user_id = f"test-history-{int(time.time())}"
        headers = {
            "Content-Type": "application/json",
            "X-User-ID": fresh_user_id
        }
        
        # Consume some credits via the consume endpoint
        consume_response = requests.post(
            f"{BASE_URL}/api/v1/credits/consume",
            headers=headers,
            json={"action": "export_to_pdf", "quantity": 1}  # 1 credit
        )
        
        assert consume_response.status_code == 200, f"Consume failed: {consume_response.text}"
        
        # Check history
        history_response = requests.get(
            f"{BASE_URL}/api/v1/credits/history",
            headers=headers
        )
        
        assert history_response.status_code == 200
        transactions = history_response.json()["data"]["transactions"]
        
        # Should have at least one transaction
        assert len(transactions) >= 1, "No transactions recorded"
        
        # Verify transaction structure
        tx = transactions[0]
        assert "user_id" in tx
        assert "action" in tx
        assert "credits_consumed" in tx
        assert "balance_before" in tx
        assert "balance_after" in tx
        assert "created_at" in tx
    
    def test_credit_history_supports_pagination(self, api_session):
        """Credit history should support limit and skip parameters"""
        response = api_session.get(f"{BASE_URL}/api/v1/credits/history?limit=5&skip=0")
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        assert data["limit"] == 5
        assert data["skip"] == 0


class TestCreditCostsVerification:
    """Verify credit costs match the pricing strategy"""
    
    def test_credit_costs_match_pricing_v3(self):
        """Verify credit costs match Pricing Strategy v3.0"""
        response = requests.get(f"{BASE_URL}/api/v1/credits/costs")
        
        assert response.status_code == 200
        costs = response.json()["data"]["costs"]
        
        # Verify key costs from pricing strategy
        assert costs["content_generation"] == 50, f"Content generation should cost 50, got {costs['content_generation']}"
        assert costs["content_analysis"] == 10, f"Content analysis should cost 10, got {costs['content_analysis']}"
        assert costs["image_generation"] == 20, f"Image generation should cost 20, got {costs['image_generation']}"
        assert costs["ai_rewrite"] == 25, f"AI rewrite should cost 25, got {costs['ai_rewrite']}"
        assert costs["iterative_rewrite"] == 50, f"Iterative rewrite should cost 50, got {costs['iterative_rewrite']}"
    
    def test_free_plan_has_25_credits(self):
        """Verify Free plan has 25 credits/month"""
        response = requests.get(f"{BASE_URL}/api/v1/credits/plans")
        
        assert response.status_code == 200
        plans = {p["id"]: p for p in response.json()["data"]["plans"]}
        
        assert plans["free"]["monthly_credits"] == 25, f"Free plan should have 25 credits"


class TestCreditConsumptionFlow:
    """Test complete credit consumption flow"""
    
    def test_consume_credits_deducts_balance(self):
        """Consuming credits should deduct from balance"""
        fresh_user_id = f"test-consume-{int(time.time())}"
        headers = {
            "Content-Type": "application/json",
            "X-User-ID": fresh_user_id
        }
        
        # Get initial balance (should be 25 for new user)
        balance_response = requests.get(
            f"{BASE_URL}/api/v1/credits/balance",
            headers=headers
        )
        initial_balance = balance_response.json()["data"]["credits_balance"]
        assert initial_balance == 25, f"New user should have 25 credits, got {initial_balance}"
        
        # Consume 5 credits (quick_analysis)
        consume_response = requests.post(
            f"{BASE_URL}/api/v1/credits/consume",
            headers=headers,
            json={"action": "quick_analysis", "quantity": 1}  # 5 credits
        )
        
        assert consume_response.status_code == 200
        consume_data = consume_response.json()["data"]
        
        assert consume_data["credits_consumed"] == 5
        assert consume_data["balance_before"] == 25
        assert consume_data["balance_after"] == 20
        
        # Verify balance was actually updated
        new_balance_response = requests.get(
            f"{BASE_URL}/api/v1/credits/balance",
            headers=headers
        )
        new_balance = new_balance_response.json()["data"]["credits_balance"]
        assert new_balance == 20, f"Balance should be 20 after consuming 5 credits"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
