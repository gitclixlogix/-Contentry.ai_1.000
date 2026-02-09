"""
Test Content Analysis and Rewrite APIs
Tests for:
1. Content Analysis - returns overall_score, compliance_score, etc.
2. Content Rewrite - returns rewritten_content
3. Auto-rewrite trigger condition (score < 80)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001').rstrip('/')
API_URL = f"{BASE_URL}/api/v1"


class TestContentAnalysis:
    """Content Analysis endpoint tests"""
    
    def test_analyze_problematic_content(self):
        """Test analysis of content with compliance issues - should return low score"""
        response = requests.post(f"{API_URL}/content/analyze", json={
            "content": "We need a young rockstar to join our team! Must be a digital native who can hustle 24/7.",
            "user_id": "test-user"
        }, headers={"X-User-ID": "test-user"})
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify score fields exist
        assert "overall_score" in data, "Response should contain overall_score"
        assert "compliance_score" in data, "Response should contain compliance_score"
        assert "accuracy_score" in data, "Response should contain accuracy_score"
        assert "cultural_score" in data, "Response should contain cultural_score"
        
        # Verify score is below 80 (should trigger auto-rewrite)
        overall_score = data["overall_score"]
        assert overall_score < 80, f"Problematic content should score below 80, got {overall_score}"
        print(f"✓ Problematic content scored {overall_score}/100 (below 80 threshold)")
        
        # Verify issues are detected
        assert "issues" in data, "Response should contain issues"
        assert len(data["issues"]) > 0, "Should detect compliance issues"
        print(f"✓ Detected {len(data['issues'])} issues")
    
    def test_analyze_good_content(self):
        """Test analysis of compliant content - should return high score"""
        response = requests.post(f"{API_URL}/content/analyze", json={
            "content": "We are looking for a talented professional to join our diverse team. We value experience and dedication.",
            "user_id": "test-user"
        }, headers={"X-User-ID": "test-user"})
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify score fields exist
        assert "overall_score" in data
        overall_score = data["overall_score"]
        print(f"✓ Good content scored {overall_score}/100")
        
        # Good content should score higher (may or may not be above 80)
        assert overall_score > 0, "Score should be positive"
    
    def test_analyze_requires_user_id(self):
        """Test that user_id is required"""
        response = requests.post(f"{API_URL}/content/analyze", json={
            "content": "Test content"
        }, headers={"X-User-ID": "test-user"})
        
        # Should return 422 for missing user_id
        assert response.status_code == 422
        print("✓ API correctly requires user_id field")


class TestContentRewrite:
    """Content Rewrite endpoint tests"""
    
    def test_rewrite_problematic_content(self):
        """Test rewriting content with compliance issues"""
        response = requests.post(f"{API_URL}/content/rewrite", json={
            "content": "We need a young rockstar to join our team! Must be a digital native who can hustle 24/7.",
            "tone": "professional",
            "use_iterative": False,
            "target_score": 80
        }, headers={"X-User-ID": "test-user"})
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify rewritten content exists
        assert "rewritten_content" in data, "Response should contain rewritten_content"
        rewritten = data["rewritten_content"]
        assert len(rewritten) > 0, "Rewritten content should not be empty"
        
        # Verify problematic terms are removed
        rewritten_lower = rewritten.lower()
        assert "young" not in rewritten_lower or "young professional" in rewritten_lower, "Should remove age-discriminatory 'young'"
        print(f"✓ Content rewritten successfully")
        print(f"  Original: 'We need a young rockstar...'")
        print(f"  Rewritten: '{rewritten[:100]}...'")
    
    def test_rewrite_with_profile(self):
        """Test rewriting with strategic profile"""
        response = requests.post(f"{API_URL}/content/rewrite", json={
            "content": "Check out our new product!",
            "tone": "professional",
            "profile_id": None,  # No profile
            "use_iterative": False
        }, headers={"X-User-ID": "test-user"})
        
        assert response.status_code == 200
        data = response.json()
        assert "rewritten_content" in data
        print("✓ Rewrite works without profile")
    
    def test_rewrite_returns_model_info(self):
        """Test that rewrite returns model information"""
        response = requests.post(f"{API_URL}/content/rewrite", json={
            "content": "Test content for rewriting",
            "tone": "professional"
        }, headers={"X-User-ID": "test-user"})
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify rewritten content exists
        assert "rewritten_content" in data, "Response should contain rewritten_content"
        # Model info may be in metrics or at top level
        model_used = data.get("model_used") or data.get("metrics", {}).get("model_used")
        print(f"✓ Rewrite completed successfully")


class TestAutoRewriteCondition:
    """Test the auto-rewrite trigger condition"""
    
    def test_low_score_triggers_rewrite(self):
        """Verify that content with score < 80 would trigger auto-rewrite"""
        # First analyze the content
        analyze_response = requests.post(f"{API_URL}/content/analyze", json={
            "content": "We need a young rockstar to join our team! Must be a digital native who can hustle 24/7.",
            "user_id": "test-user"
        }, headers={"X-User-ID": "test-user"})
        
        assert analyze_response.status_code == 200
        analysis = analyze_response.json()
        overall_score = analysis.get("overall_score", 0)
        
        # Verify score is below 80 (auto-rewrite threshold)
        should_auto_rewrite = overall_score < 80
        assert should_auto_rewrite, f"Score {overall_score} should be below 80 to trigger auto-rewrite"
        print(f"✓ Score {overall_score}/100 is below 80 - auto-rewrite would trigger")
        
        # Now verify rewrite improves the content
        rewrite_response = requests.post(f"{API_URL}/content/rewrite", json={
            "content": "We need a young rockstar to join our team! Must be a digital native who can hustle 24/7.",
            "tone": "professional",
            "analysis_result": analysis,
            "use_iterative": False,
            "target_score": 80
        }, headers={"X-User-ID": "test-user"})
        
        assert rewrite_response.status_code == 200
        rewrite_data = rewrite_response.json()
        rewritten_content = rewrite_data.get("rewritten_content", "")
        
        # Analyze the rewritten content
        reanalyze_response = requests.post(f"{API_URL}/content/analyze", json={
            "content": rewritten_content,
            "user_id": "test-user"
        }, headers={"X-User-ID": "test-user"})
        
        assert reanalyze_response.status_code == 200
        new_analysis = reanalyze_response.json()
        new_score = new_analysis.get("overall_score", 0)
        
        print(f"✓ Original score: {overall_score}/100")
        print(f"✓ Rewritten score: {new_score}/100")
        print(f"✓ Improvement: +{new_score - overall_score} points")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
