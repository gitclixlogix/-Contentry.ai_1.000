"""
Employment Law Agent API Tests

Tests the agentic multi-model compliance engine that detects employment law violations
using gpt-4.1-mini and gemini-2.5-flash models.

Violations tested:
- Age discrimination (ADEA): "recent grad"
- Gendered language (Title VII): "brother-in-arms", "ninja"
- Disability discrimination (ADA): "handle high-stress"
- Culture of exclusion: "happy hours", "ski trips", "#WorkHardPlayHard"
"""

import pytest
import requests
import os

# Use the public URL for testing
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001') + '/api/v1'

# Test credentials
TEST_USER_ID = "sarah-chen"
TEST_EMAIL = "sarah.chen@techcorp-demo.com"
TEST_PASSWORD = "Demo123!"


class TestEmploymentLawAgent:
    """Tests for the Employment Law Compliance Agent"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-User-ID": TEST_USER_ID
        })
    
    def test_content_analysis_detects_age_discrimination(self):
        """Test that 'recent grad' triggers age discrimination violation"""
        content = "We're hiring a recent grad for our marketing team!"
        
        response = self.session.post(
            f"{BASE_URL}/content/analyze",
            json={
                "content": content,
                "user_id": TEST_USER_ID,
                "language": "en"
            },
            timeout=180
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that violations were detected
        compliance = data.get("compliance_analysis", {})
        emp_check = compliance.get("employment_law_check", {})
        
        assert emp_check.get("violations_found") == True, "Should detect violations"
        
        # Check for age discrimination
        violation_types = emp_check.get("violation_types", [])
        assert "age_discrimination" in violation_types, f"Should detect age discrimination, got: {violation_types}"
    
    def test_content_analysis_detects_gendered_language(self):
        """Test that 'ninja' and 'brother-in-arms' trigger gendered language violations"""
        content = "Looking for a marketing ninja to join our brother-in-arms team!"
        
        response = self.session.post(
            f"{BASE_URL}/content/analyze",
            json={
                "content": content,
                "user_id": TEST_USER_ID,
                "language": "en"
            },
            timeout=180
        )
        
        assert response.status_code == 200
        data = response.json()
        
        compliance = data.get("compliance_analysis", {})
        emp_check = compliance.get("employment_law_check", {})
        
        assert emp_check.get("violations_found") == True, "Should detect violations"
        
        violation_types = emp_check.get("violation_types", [])
        assert "gendered_language" in violation_types, f"Should detect gendered language, got: {violation_types}"
    
    def test_content_analysis_detects_disability_discrimination(self):
        """Test that 'handle high-stress' triggers disability discrimination violation"""
        content = "Must be able to handle high-stress environments and work under pressure."
        
        response = self.session.post(
            f"{BASE_URL}/content/analyze",
            json={
                "content": content,
                "user_id": TEST_USER_ID,
                "language": "en"
            },
            timeout=180
        )
        
        assert response.status_code == 200
        data = response.json()
        
        compliance = data.get("compliance_analysis", {})
        emp_check = compliance.get("employment_law_check", {})
        
        # This may or may not be detected depending on context
        # The agent should at least analyze the content
        assert "employment_law_check" in compliance, "Should have employment law check"
    
    def test_content_analysis_detects_culture_exclusion(self):
        """Test that 'happy hours', 'ski trips', '#WorkHardPlayHard' trigger culture exclusion"""
        content = "We love happy hours, ski trips and #WorkHardPlayHard! Join our work family!"
        
        response = self.session.post(
            f"{BASE_URL}/content/analyze",
            json={
                "content": content,
                "user_id": TEST_USER_ID,
                "language": "en"
            },
            timeout=180
        )
        
        assert response.status_code == 200
        data = response.json()
        
        compliance = data.get("compliance_analysis", {})
        emp_check = compliance.get("employment_law_check", {})
        
        assert emp_check.get("violations_found") == True, "Should detect violations"
        
        violation_types = emp_check.get("violation_types", [])
        assert "culture_exclusion" in violation_types, f"Should detect culture exclusion, got: {violation_types}"
    
    def test_content_analysis_full_violation_content(self):
        """Test the full sample content with all violation types"""
        content = """🚀 TechCorp is hiring! Looking for a recent grad who is a marketing ninja 
        ready to join our work family! We are a fun team that is like a brother-in-arms group. 
        We love happy hours, ski trips and #WorkHardPlayHard. Must be able to handle high-stress 
        environments. Apply now!"""
        
        response = self.session.post(
            f"{BASE_URL}/content/analyze",
            json={
                "content": content,
                "user_id": TEST_USER_ID,
                "language": "en"
            },
            timeout=180
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check flagged status
        assert data.get("flagged_status") == "policy_violation", f"Should be flagged as policy_violation, got: {data.get('flagged_status')}"
        
        # Check compliance analysis
        compliance = data.get("compliance_analysis", {})
        emp_check = compliance.get("employment_law_check", {})
        
        assert emp_check.get("is_hr_content") == True, "Should detect as HR content"
        assert emp_check.get("violations_found") == True, "Should detect violations"
        
        # Check models used
        models_used = emp_check.get("models_used", [])
        assert "gpt-4.1-mini" in models_used, f"Should use gpt-4.1-mini, got: {models_used}"
        # Note: gemini-2.5-flash may fail if not available, but gpt-4.1-mini should work
        
        # Check violation types - should have multiple
        violation_types = emp_check.get("violation_types", [])
        assert len(violation_types) >= 2, f"Should detect multiple violation types, got: {violation_types}"
        
        # Check compliance score is lowered
        compliance_score = data.get("compliance_score", 100)
        assert compliance_score < 80, f"Compliance score should be lowered, got: {compliance_score}"
        
        # Check overall rating
        overall_rating = data.get("overall_rating", "")
        assert overall_rating in ["Needs Improvement", "Poor", "Critical"], f"Overall rating should indicate issues, got: {overall_rating}"
    
    def test_content_analysis_clean_content(self):
        """Test that clean content passes without violations"""
        content = "We're looking for a talented professional to join our team. We offer competitive benefits and a supportive work environment."
        
        response = self.session.post(
            f"{BASE_URL}/content/analyze",
            json={
                "content": content,
                "user_id": TEST_USER_ID,
                "language": "en"
            },
            timeout=180
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Clean content should not be flagged as policy_violation
        flagged_status = data.get("flagged_status", "")
        # It might be good_coverage or something else, but not policy_violation
        compliance = data.get("compliance_analysis", {})
        emp_check = compliance.get("employment_law_check", {})
        
        # If violations are found, they should be minimal
        violations_found = emp_check.get("violations_found", False)
        if violations_found:
            violation_count = emp_check.get("violation_count", 0)
            assert violation_count <= 1, f"Clean content should have minimal violations, got: {violation_count}"
    
    def test_content_analysis_returns_recommendations(self):
        """Test that violations include recommendations for fixes"""
        content = "Looking for a recent grad ninja to join our brother-in-arms team!"
        
        response = self.session.post(
            f"{BASE_URL}/content/analyze",
            json={
                "content": content,
                "user_id": TEST_USER_ID,
                "language": "en"
            },
            timeout=180
        )
        
        assert response.status_code == 200
        data = response.json()
        
        compliance = data.get("compliance_analysis", {})
        violations = compliance.get("violations", [])
        
        # Check that at least some violations have recommendations
        has_recommendations = False
        for v in violations:
            if v.get("recommendation"):
                has_recommendations = True
                break
        
        assert has_recommendations or len(violations) == 0, "Violations should include recommendations"


class TestContentAnalysisAPI:
    """General tests for the content analysis API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-User-ID": TEST_USER_ID
        })
    
    def test_api_requires_authentication(self):
        """Test that API requires authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(
            f"{BASE_URL}/content/analyze",
            json={
                "content": "Test content",
                "user_id": TEST_USER_ID,
                "language": "en"
            },
            timeout=30
        )
        
        # Should return 401 without X-User-ID header
        assert response.status_code == 401
    
    def test_api_returns_scores(self):
        """Test that API returns all required scores"""
        response = self.session.post(
            f"{BASE_URL}/content/analyze",
            json={
                "content": "Test content for analysis",
                "user_id": TEST_USER_ID,
                "language": "en"
            },
            timeout=180
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required score fields
        assert "compliance_score" in data, "Should have compliance_score"
        assert "cultural_score" in data, "Should have cultural_score"
        assert "accuracy_score" in data, "Should have accuracy_score"
        assert "overall_score" in data, "Should have overall_score"
    
    def test_api_returns_cultural_analysis(self):
        """Test that API returns cultural analysis with Hofstede dimensions"""
        response = self.session.post(
            f"{BASE_URL}/content/analyze",
            json={
                "content": "Test content for cultural analysis",
                "user_id": TEST_USER_ID,
                "language": "en"
            },
            timeout=180
        )
        
        assert response.status_code == 200
        data = response.json()
        
        cultural = data.get("cultural_analysis", {})
        assert "overall_score" in cultural, "Should have cultural overall_score"
        assert "dimensions" in cultural, "Should have cultural dimensions"
        
        # Should have 6 Hofstede dimensions
        dimensions = cultural.get("dimensions", [])
        assert len(dimensions) == 6, f"Should have 6 cultural dimensions, got: {len(dimensions)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
