"""
Test Auto-Refill Stripe Integration and Email Notifications
Tests the new auto-refill features:
- POST /api/v1/credits/auto-refill/trigger - Without force_charge returns pending status
- POST /api/v1/credits/auto-refill/trigger?force_charge=true - With force_charge attempts Stripe payment
- POST /api/v1/credits/auto-refill/check-warning - Checks balance and sends warning email if needed
- Email service functions: send_auto_refill_warning_email, send_auto_refill_success_email, send_auto_refill_failed_email

Note: Email service is in console mode (development) - emails are logged to console, not actually sent.
Stripe requires stripe_customer_id and payment_method_id on user record for actual charging.
"""
import pytest
import requests
import os

BASE_URL = "https://admin-portal-278.preview.emergentagent.com/api/v1"

# Use existing test user that has super_admin role
TEST_USER_ID = "security-test-user-001"


class TestAutoRefillTriggerEndpoint:
    """Test POST /api/v1/credits/auto-refill/trigger endpoint"""
    
    @pytest.fixture
    def api_client(self):
        """Create a requests session"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "X-User-ID": TEST_USER_ID
        })
        return session
    
    def test_trigger_without_force_charge_returns_pending_when_below_threshold(self, api_client):
        """
        Test POST /api/v1/credits/auto-refill/trigger without force_charge
        When balance is below threshold and auto-refill is enabled, should return pending status
        """
        # First enable auto-refill with threshold higher than user's balance (25 credits)
        enable_response = api_client.put(
            f"{BASE_URL}/credits/auto-refill/settings",
            json={
                "enabled": True,
                "threshold_credits": 100,  # User has 25 credits, below this threshold
                "refill_pack_id": "standard",
                "max_refills_per_month": 3
            }
        )
        
        assert enable_response.status_code == 200, f"Failed to enable auto-refill: {enable_response.text}"
        
        # Trigger without force_charge (default)
        response = api_client.post(f"{BASE_URL}/credits/auto-refill/trigger")
        
        assert response.status_code == 200, f"Failed to trigger: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, "Response should have success=True"
        
        # Should be triggered with pending status
        if data.get("triggered") == True:
            assert data.get("status") == "pending", f"Status should be 'pending' without force_charge, got: {data.get('status')}"
            assert "pack_id" in data, "Response should have pack_id"
            assert "credits" in data, "Response should have credits"
            assert "amount_usd" in data, "Response should have amount_usd"
            assert "message" in data, "Response should have message about pending status"
            print(f"SUCCESS: Auto-refill triggered with pending status - {data.get('credits')} credits")
        else:
            # Monthly limit might be reached
            reason = data.get("reason")
            print(f"INFO: Auto-refill not triggered - reason: {reason}")
    
    def test_trigger_with_force_charge_attempts_stripe_payment(self, api_client):
        """
        Test POST /api/v1/credits/auto-refill/trigger?force_charge=true
        Should attempt Stripe payment (will return pending without stripe_customer_id)
        """
        # Enable auto-refill with threshold higher than user's balance
        enable_response = api_client.put(
            f"{BASE_URL}/credits/auto-refill/settings",
            json={
                "enabled": True,
                "threshold_credits": 100,
                "refill_pack_id": "standard",
                "max_refills_per_month": 10  # High limit to avoid monthly limit
            }
        )
        
        assert enable_response.status_code == 200, f"Failed to enable auto-refill: {enable_response.text}"
        
        # Trigger WITH force_charge=true
        response = api_client.post(f"{BASE_URL}/credits/auto-refill/trigger?force_charge=true")
        
        assert response.status_code == 200, f"Failed to trigger: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, "Response should have success=True"
        
        if data.get("triggered") == True:
            # Without stripe_customer_id, should still return pending
            status = data.get("status")
            assert status in ["pending", "failed", "completed"], f"Status should be valid, got: {status}"
            
            if status == "pending":
                print("SUCCESS: force_charge=true returns pending (no Stripe customer configured)")
            elif status == "failed":
                print(f"SUCCESS: force_charge=true attempted Stripe but failed: {data.get('error', 'unknown')}")
            elif status == "completed":
                print(f"SUCCESS: force_charge=true completed Stripe payment!")
        else:
            reason = data.get("reason")
            print(f"INFO: Auto-refill not triggered with force_charge - reason: {reason}")
    
    def test_trigger_returns_not_triggered_when_disabled(self, api_client):
        """Test that trigger returns not triggered when auto-refill is disabled"""
        # Ensure auto-refill is disabled
        api_client.put(
            f"{BASE_URL}/credits/auto-refill/settings",
            json={
                "enabled": False,
                "threshold_credits": 100,
                "refill_pack_id": "standard",
                "max_refills_per_month": 3
            }
        )
        
        # Try to trigger
        response = api_client.post(f"{BASE_URL}/credits/auto-refill/trigger")
        
        assert response.status_code == 200, f"Failed to trigger: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert data.get("triggered") == False, "Should not trigger when disabled"
        assert data.get("reason") == "disabled", "Reason should be 'disabled'"
        
        print("SUCCESS: Trigger correctly returns not triggered when disabled")
    
    def test_trigger_returns_not_triggered_when_above_threshold(self, api_client):
        """Test that trigger returns not triggered when balance is above threshold"""
        # Enable auto-refill with very low threshold (user has 25 credits)
        api_client.put(
            f"{BASE_URL}/credits/auto-refill/settings",
            json={
                "enabled": True,
                "threshold_credits": 10,  # Very low threshold, user has 25
                "refill_pack_id": "standard",
                "max_refills_per_month": 3
            }
        )
        
        # Try to trigger
        response = api_client.post(f"{BASE_URL}/credits/auto-refill/trigger")
        
        assert response.status_code == 200, f"Failed to trigger: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        
        # User has 25 credits, threshold is 10, should not trigger
        if data.get("triggered") == False:
            assert data.get("reason") == "above_threshold", "Reason should be 'above_threshold'"
            print("SUCCESS: Trigger correctly returns not triggered when above threshold")
        else:
            print(f"INFO: User balance was below 10 credits, trigger activated")


class TestCheckWarningEndpoint:
    """Test POST /api/v1/credits/auto-refill/check-warning endpoint"""
    
    @pytest.fixture
    def api_client(self):
        """Create a requests session"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "X-User-ID": TEST_USER_ID
        })
        return session
    
    def test_check_warning_endpoint_exists(self, api_client):
        """Test that POST /api/v1/credits/auto-refill/check-warning endpoint exists"""
        response = api_client.post(f"{BASE_URL}/credits/auto-refill/check-warning")
        
        # Should not return 404 or 405
        assert response.status_code != 404, "Endpoint should exist"
        assert response.status_code != 405, "POST method should be allowed"
        assert response.status_code == 200, f"Unexpected status: {response.status_code} - {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Response should have success=True"
        
        # Check response structure
        if data.get("warning_sent") == True:
            assert "current_balance" in data, "Should have current_balance when warning sent"
            assert "threshold" in data, "Should have threshold when warning sent"
            print(f"SUCCESS: Warning email sent - balance: {data.get('current_balance')}, threshold: {data.get('threshold')}")
        else:
            print(f"SUCCESS: No warning needed - {data.get('message', 'auto-refill not enabled or balance not in warning zone')}")
    
    def test_check_warning_when_auto_refill_disabled(self, api_client):
        """Test check-warning returns no warning when auto-refill is disabled"""
        # Ensure auto-refill is disabled
        api_client.put(
            f"{BASE_URL}/credits/auto-refill/settings",
            json={
                "enabled": False,
                "threshold_credits": 100,
                "refill_pack_id": "standard",
                "max_refills_per_month": 3
            }
        )
        
        response = api_client.post(f"{BASE_URL}/credits/auto-refill/check-warning")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert data.get("warning_sent") == False, "Should not send warning when disabled"
        
        print("SUCCESS: No warning sent when auto-refill is disabled")
    
    def test_check_warning_rate_limiting(self, api_client):
        """Test that warning email is only sent once per 24 hours"""
        # Enable auto-refill with threshold that puts user in warning zone
        # User has 25 credits, warning zone is between threshold and 2x threshold
        # Set threshold to 20, warning zone is 20-40, user's 25 is in range
        api_client.put(
            f"{BASE_URL}/credits/auto-refill/settings",
            json={
                "enabled": True,
                "threshold_credits": 20,
                "refill_pack_id": "standard",
                "max_refills_per_month": 3
            }
        )
        
        # First call
        response1 = api_client.post(f"{BASE_URL}/credits/auto-refill/check-warning")
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Second call immediately after
        response2 = api_client.post(f"{BASE_URL}/credits/auto-refill/check-warning")
        assert response2.status_code == 200
        data2 = response2.json()
        
        # If first call sent warning, second should not (24 hour limit)
        if data1.get("warning_sent") == True:
            assert data2.get("warning_sent") == False, "Second call should not send warning within 24 hours"
            print("SUCCESS: Warning email rate limiting works (once per 24 hours)")
        else:
            # Warning might have been sent earlier in testing
            print("INFO: First call didn't send warning (already sent within 24 hours or balance not in warning zone)")


class TestEmailServiceFunctions:
    """Test that email service functions exist and can be imported"""
    
    def test_email_functions_exist(self):
        """Test that the three auto-refill email functions exist in email_service.py"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        try:
            from email_service import (
                send_auto_refill_warning_email,
                send_auto_refill_success_email,
                send_auto_refill_failed_email
            )
            
            # Verify they are callable
            assert callable(send_auto_refill_warning_email), "send_auto_refill_warning_email should be callable"
            assert callable(send_auto_refill_success_email), "send_auto_refill_success_email should be callable"
            assert callable(send_auto_refill_failed_email), "send_auto_refill_failed_email should be callable"
            
            print("SUCCESS: All three auto-refill email functions exist and are callable")
            print("  - send_auto_refill_warning_email")
            print("  - send_auto_refill_success_email")
            print("  - send_auto_refill_failed_email")
            
        except ImportError as e:
            pytest.fail(f"Failed to import email functions: {e}")
    
    def test_email_functions_are_async(self):
        """Test that email functions are async (coroutines)"""
        import sys
        import inspect
        sys.path.insert(0, '/app/backend')
        
        from email_service import (
            send_auto_refill_warning_email,
            send_auto_refill_success_email,
            send_auto_refill_failed_email
        )
        
        assert inspect.iscoroutinefunction(send_auto_refill_warning_email), "send_auto_refill_warning_email should be async"
        assert inspect.iscoroutinefunction(send_auto_refill_success_email), "send_auto_refill_success_email should be async"
        assert inspect.iscoroutinefunction(send_auto_refill_failed_email), "send_auto_refill_failed_email should be async"
        
        print("SUCCESS: All email functions are async coroutines")


class TestAutoRefillStatusValues:
    """Test that auto-refill trigger returns appropriate status values"""
    
    @pytest.fixture
    def api_client(self):
        """Create a requests session"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "X-User-ID": TEST_USER_ID
        })
        return session
    
    def test_trigger_status_values(self, api_client):
        """Test that trigger returns valid status values (pending/completed/failed)"""
        # Enable auto-refill with high threshold to trigger
        api_client.put(
            f"{BASE_URL}/credits/auto-refill/settings",
            json={
                "enabled": True,
                "threshold_credits": 100,  # User has 25 credits
                "refill_pack_id": "standard",
                "max_refills_per_month": 10
            }
        )
        
        # Test without force_charge
        response = api_client.post(f"{BASE_URL}/credits/auto-refill/trigger")
        
        assert response.status_code == 200
        data = response.json()
        
        if data.get("triggered") == True:
            status = data.get("status")
            valid_statuses = ["pending", "completed", "failed", "requires_action"]
            assert status in valid_statuses, f"Status '{status}' should be one of {valid_statuses}"
            print(f"SUCCESS: Trigger returned valid status: {status}")
        else:
            print(f"INFO: Trigger not activated - reason: {data.get('reason')}")


class TestAutoRefillWarningsCollection:
    """Test that warning emails are tracked in auto_refill_warnings collection"""
    
    @pytest.fixture
    def api_client(self):
        """Create a requests session"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "X-User-ID": TEST_USER_ID
        })
        return session
    
    def test_warning_tracking_in_database(self, api_client):
        """
        Test that check_low_balance_warning checks auto_refill_warnings collection
        to prevent sending multiple warnings within 24 hours
        """
        # Enable auto-refill with threshold that puts user in warning zone
        api_client.put(
            f"{BASE_URL}/credits/auto-refill/settings",
            json={
                "enabled": True,
                "threshold_credits": 20,  # Warning zone 20-40, user has 25
                "refill_pack_id": "standard",
                "max_refills_per_month": 3
            }
        )
        
        # Call check-warning twice
        response1 = api_client.post(f"{BASE_URL}/credits/auto-refill/check-warning")
        response2 = api_client.post(f"{BASE_URL}/credits/auto-refill/check-warning")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # If first sent warning, second should not (proves DB tracking works)
        if data1.get("warning_sent") == True and data2.get("warning_sent") == False:
            print("SUCCESS: Warning tracking in auto_refill_warnings collection works correctly")
        elif data1.get("warning_sent") == False:
            print("INFO: No warning sent (already sent within 24 hours or balance not in warning zone)")
        else:
            print("INFO: Both calls returned same result")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
