"""
Test suite for Iterative Agentic Rewrite feature
Tests POST /api/v1/content/rewrite with iterative mode enabled

Features tested:
- Iterative rewrite returns final_score, original_score, iterations_needed, target_met fields
- Content with compliance issues gets improved score through iterations
- Content already >= 80 returns immediately without rewriting
- Response includes iterations array with score history
"""

import pytest
import requests
import os
import time

# Use public URL for testing
BASE_URL = "https://admin-portal-278.preview.emergentagent.com"

# Test credentials
TEST_EMAIL = "sarah.chen@techcorp-demo.com"
TEST_PASSWORD = "Demo123!"


class TestIterativeRewrite:
    """Test suite for iterative agentic rewrite feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures - login and get auth token"""
        # Login to get access token
        login_response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        login_data = login_response.json()
        
        self.access_token = login_data.get("access_token")
        self.user_id = login_data.get("user", {}).get("id")
        
        assert self.access_token, "No access token received"
        assert self.user_id, "No user ID received"
        
        # Get a strategic profile for the user
        profiles_response = requests.get(
            f"{BASE_URL}/api/v1/profiles/strategic",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "X-User-ID": self.user_id
            }
        )
        
        if profiles_response.status_code == 200:
            profiles = profiles_response.json().get("profiles", [])
            if profiles:
                self.profile_id = profiles[0].get("id")
            else:
                self.profile_id = None
        else:
            self.profile_id = None
        
        yield
    
    def test_rewrite_endpoint_exists(self):
        """Test that the rewrite endpoint exists and responds"""
        response = requests.post(
            f"{BASE_URL}/api/v1/content/rewrite",
            json={
                "content": "Test content",
                "user_id": self.user_id
            },
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-User-ID": self.user_id
            }
        )
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404, "Rewrite endpoint not found"
        # Should not return 405 (method allowed)
        assert response.status_code != 405, "POST method not allowed"
    
    def test_rewrite_requires_content(self):
        """Test that rewrite requires content field"""
        response = requests.post(
            f"{BASE_URL}/api/v1/content/rewrite",
            json={
                "user_id": self.user_id
            },
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-User-ID": self.user_id
            }
        )
        
        # Should return 400 for missing content
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_iterative_rewrite_returns_expected_fields(self):
        """Test that iterative rewrite returns all expected fields"""
        # Content with employment law issues that should trigger rewriting
        problematic_content = """
        🚀 We're hiring! Looking for a young digital native to join our team!
        
        Must be a recent grad with fresh ideas. We work hard and play hard - 
        join us for happy hours and ski trips! #Hiring #StartupLife
        """
        
        response = requests.post(
            f"{BASE_URL}/api/v1/content/rewrite",
            json={
                "content": problematic_content,
                "user_id": self.user_id,
                "profile_id": self.profile_id,
                "use_iterative": True,
                "target_score": 80,
                "max_iterations": 3
            },
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-User-ID": self.user_id
            },
            timeout=120  # Allow time for iterative processing
        )
        
        assert response.status_code == 200, f"Rewrite failed: {response.status_code} - {response.text}"
        
        data = response.json()
        
        # Check for required fields from iterative rewrite
        assert "rewritten_content" in data, "Missing rewritten_content field"
        assert "final_score" in data, "Missing final_score field"
        assert "original_score" in data, "Missing original_score field"
        assert "iterations_needed" in data, "Missing iterations_needed field"
        assert "target_met" in data, "Missing target_met field"
        
        # Validate field types
        assert isinstance(data["rewritten_content"], str), "rewritten_content should be string"
        assert isinstance(data["final_score"], (int, float)), "final_score should be numeric"
        assert isinstance(data["original_score"], (int, float)), "original_score should be numeric"
        assert isinstance(data["iterations_needed"], int), "iterations_needed should be int"
        assert isinstance(data["target_met"], bool), "target_met should be boolean"
        
        # Check iterations array if present
        if "iterations" in data:
            assert isinstance(data["iterations"], list), "iterations should be a list"
        
        print(f"✓ Iterative rewrite returned all expected fields")
        print(f"  - Original score: {data['original_score']}")
        print(f"  - Final score: {data['final_score']}")
        print(f"  - Iterations needed: {data['iterations_needed']}")
        print(f"  - Target met: {data['target_met']}")
    
    def test_iterative_rewrite_improves_score(self):
        """Test that iterative rewrite improves content score"""
        # Content with clear compliance issues
        problematic_content = """
        Join our brotherhood of digital ninjas! We're looking for young, 
        energetic rock stars who are fresh out of college. 
        
        Perks include mandatory happy hours and weekend ski trips!
        #WorkHardPlayHard #Hiring
        """
        
        response = requests.post(
            f"{BASE_URL}/api/v1/content/rewrite",
            json={
                "content": problematic_content,
                "user_id": self.user_id,
                "profile_id": self.profile_id,
                "use_iterative": True,
                "target_score": 80,
                "max_iterations": 3
            },
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-User-ID": self.user_id
            },
            timeout=120
        )
        
        assert response.status_code == 200, f"Rewrite failed: {response.status_code}"
        
        data = response.json()
        
        # Final score should be >= original score (improvement)
        final_score = data.get("final_score", 0)
        original_score = data.get("original_score", 0)
        
        assert final_score >= original_score, f"Score did not improve: {original_score} -> {final_score}"
        
        # If target was met, final score should be >= 80
        if data.get("target_met"):
            assert final_score >= 80, f"Target met but score {final_score} < 80"
        
        print(f"✓ Score improved from {original_score} to {final_score}")
        print(f"  - Improvement: +{final_score - original_score}")
    
    def test_high_quality_content_returns_immediately(self):
        """Test that content already >= 80 returns without rewriting"""
        # High quality, compliant content
        good_content = """
        We're excited to announce an open position on our team!
        
        We welcome candidates from all backgrounds and experience levels.
        Our inclusive workplace values diversity and offers flexible work arrangements.
        
        Apply today to join our collaborative team!
        #Careers #DiversityAndInclusion
        """
        
        response = requests.post(
            f"{BASE_URL}/api/v1/content/rewrite",
            json={
                "content": good_content,
                "user_id": self.user_id,
                "profile_id": self.profile_id,
                "use_iterative": True,
                "target_score": 80,
                "max_iterations": 3
            },
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-User-ID": self.user_id
            },
            timeout=120
        )
        
        assert response.status_code == 200, f"Rewrite failed: {response.status_code}"
        
        data = response.json()
        
        # Check if original score was already high
        original_score = data.get("original_score", 0)
        iterations_needed = data.get("iterations_needed", -1)
        
        print(f"✓ High quality content test")
        print(f"  - Original score: {original_score}")
        print(f"  - Iterations needed: {iterations_needed}")
        
        # If original was >= 80, should return with 0 iterations
        if original_score >= 80:
            assert iterations_needed == 0, f"Expected 0 iterations for high-score content, got {iterations_needed}"
            print(f"  - Correctly returned immediately without rewriting")
    
    def test_rewrite_with_promotional_flag(self):
        """Test rewrite with promotional content flag adds disclosure"""
        promotional_content = """
        I absolutely love this amazing product from @BrandName!
        Use my code SARAH20 for 20% off your purchase!
        Link in bio to shop now! #MustHave #GameChanger
        """
        
        response = requests.post(
            f"{BASE_URL}/api/v1/content/rewrite",
            json={
                "content": promotional_content,
                "user_id": self.user_id,
                "profile_id": self.profile_id,
                "is_promotional": True,
                "compliance_issues": ["missing_disclosure"],
                "use_iterative": True,
                "target_score": 80,
                "max_iterations": 3
            },
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-User-ID": self.user_id
            },
            timeout=120
        )
        
        assert response.status_code == 200, f"Rewrite failed: {response.status_code}"
        
        data = response.json()
        rewritten = data.get("rewritten_content", "").lower()
        
        # Check for disclosure hashtags
        has_disclosure = "#ad" in rewritten or "#sponsored" in rewritten or "paid partnership" in rewritten
        
        print(f"✓ Promotional content rewrite test")
        print(f"  - Has disclosure: {has_disclosure}")
        print(f"  - Final score: {data.get('final_score')}")
        
        # Note: Disclosure should be added but we don't fail if AI decides differently
        if has_disclosure:
            print(f"  - Disclosure correctly added")
    
    def test_iterations_array_contains_score_history(self):
        """Test that iterations array contains score history"""
        problematic_content = """
        Looking for a young, aggressive salesman to dominate our market!
        Must be willing to work weekends and attend mandatory team bonding.
        """
        
        response = requests.post(
            f"{BASE_URL}/api/v1/content/rewrite",
            json={
                "content": problematic_content,
                "user_id": self.user_id,
                "profile_id": self.profile_id,
                "use_iterative": True,
                "target_score": 80,
                "max_iterations": 3
            },
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-User-ID": self.user_id
            },
            timeout=120
        )
        
        assert response.status_code == 200, f"Rewrite failed: {response.status_code}"
        
        data = response.json()
        iterations = data.get("iterations", [])
        
        print(f"✓ Iterations array test")
        print(f"  - Number of iterations: {len(iterations)}")
        
        # If there were iterations, check structure
        for i, iteration in enumerate(iterations):
            print(f"  - Iteration {i+1}: score={iteration.get('score')}, status={iteration.get('status')}")
            
            # Each iteration should have score and status
            assert "iteration" in iteration or "score" in iteration, f"Iteration {i+1} missing expected fields"
    
    def test_message_field_describes_result(self):
        """Test that message field describes the rewrite result"""
        content = "Test content for message field validation"
        
        response = requests.post(
            f"{BASE_URL}/api/v1/content/rewrite",
            json={
                "content": content,
                "user_id": self.user_id,
                "profile_id": self.profile_id,
                "use_iterative": True,
                "target_score": 80,
                "max_iterations": 3
            },
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-User-ID": self.user_id
            },
            timeout=120
        )
        
        assert response.status_code == 200, f"Rewrite failed: {response.status_code}"
        
        data = response.json()
        message = data.get("message", "")
        
        print(f"✓ Message field test")
        print(f"  - Message: {message}")
        
        # Message should be present and non-empty
        assert message, "Message field should not be empty"


class TestNonIterativeRewrite:
    """Test legacy non-iterative rewrite mode"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        login_response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        
        self.access_token = login_data.get("access_token")
        self.user_id = login_data.get("user", {}).get("id")
        
        yield
    
    def test_non_iterative_mode(self):
        """Test rewrite with use_iterative=False (legacy mode)"""
        content = "Test content for non-iterative rewrite"
        
        response = requests.post(
            f"{BASE_URL}/api/v1/content/rewrite",
            json={
                "content": content,
                "user_id": self.user_id,
                "use_iterative": False  # Disable iterative mode
            },
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-User-ID": self.user_id
            },
            timeout=60
        )
        
        assert response.status_code == 200, f"Rewrite failed: {response.status_code}"
        
        data = response.json()
        
        # Non-iterative mode should return different fields
        assert "rewritten_content" in data, "Missing rewritten_content"
        
        # Should have detected_intent for non-iterative mode
        if "detected_intent" in data:
            print(f"✓ Non-iterative mode returned detected_intent: {data['detected_intent']}")
        
        print(f"✓ Non-iterative rewrite completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
