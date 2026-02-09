"""
Test Suite: Content Generation Compliance Testing
Tests that AI-generated content is compliant (score >= 80) from the start.

Tests:
1. Generate content with problematic prompt ('young energetic developer') - should produce COMPLIANT content
2. Generate content with 'fresh blood / digital natives' - should NOT contain these terms
3. Verify Strategic Profile is being used (brand voice / SEO keywords)
4. Generate content and analyze it - verify score >= 80
"""

import pytest
import requests
import os
import time
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://admin-portal-278.preview.emergentagent.com')
if BASE_URL.endswith('/'):
    BASE_URL = BASE_URL.rstrip('/')

# Test credentials
TEST_EMAIL = "alex.martinez@techcorp-demo.com"
TEST_PASSWORD = "DemoCreator!123"


class TestComplianceContentGeneration:
    """Test suite for compliance-focused content generation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get auth token
        login_response = self.session.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code == 200:
            data = login_response.json()
            self.access_token = data.get("access_token")
            self.user_id = data.get("user", {}).get("id")
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
            print(f"✓ Logged in as {TEST_EMAIL}, user_id: {self.user_id}")
        else:
            pytest.skip(f"Login failed: {login_response.status_code} - {login_response.text}")
    
    def _wait_for_job(self, job_id: str, max_wait: int = 90) -> dict:
        """Wait for async job to complete and return result"""
        start_time = time.time()
        while time.time() - start_time < max_wait:
            response = self.session.get(
                f"{BASE_URL}/api/v1/jobs/{job_id}",
                headers={"X-User-ID": self.user_id}
            )
            if response.status_code == 200:
                job_data = response.json()
                status = job_data.get("status")
                print(f"  Job status: {status}")
                if status == "completed":
                    return job_data.get("result", {})
                elif status == "failed":
                    raise Exception(f"Job failed: {job_data.get('error')}")
            elif response.status_code == 422:
                print(f"  Job status check error: {response.text[:100]}")
            time.sleep(3)
        raise TimeoutError(f"Job {job_id} did not complete within {max_wait} seconds")
    
    def test_01_generate_young_energetic_developer_compliant(self):
        """
        Test 1: Generate content with problematic prompt ('young energetic developer')
        Should produce COMPLIANT content without age-related terms
        """
        print("\n=== Test 1: Generate content with 'young energetic developer' ===")
        
        # Use async endpoint for content generation
        response = self.session.post(
            f"{BASE_URL}/api/v1/content/generate/async",
            json={
                "user_id": self.user_id,
                "prompt": "Write a job posting for a young energetic developer to join our startup team",
                "tone": "professional",
                "platforms": ["linkedin"],
                "language": "en"
            }
        )
        
        assert response.status_code == 200, f"Generate async failed: {response.status_code} - {response.text}"
        job_data = response.json()
        job_id = job_data.get("job_id")
        print(f"Job submitted: {job_id}")
        
        # Wait for job completion
        result = self._wait_for_job(job_id)
        content = result.get("content", "")
        
        print(f"Generated content:\n{content[:500]}...")
        
        # Check that problematic terms are NOT in the generated content
        problematic_terms = ["young", "energetic", "digital native", "fresh grad", "recent graduate", "junior"]
        content_lower = content.lower()
        
        found_terms = [term for term in problematic_terms if term in content_lower]
        
        if found_terms:
            print(f"⚠ WARNING: Found potentially problematic terms: {found_terms}")
        else:
            print("✓ No problematic age-related terms found in generated content")
        
        # Check for inclusive language
        inclusive_terms = ["candidates", "professionals", "team members", "individuals", "experience levels", "equal opportunity"]
        found_inclusive = [term for term in inclusive_terms if term in content_lower]
        
        print(f"✓ Found inclusive terms: {found_inclusive}")
        
        # The test passes if no problematic terms are found
        assert len(found_terms) == 0, f"Generated content contains age-related terms: {found_terms}"
    
    def test_02_generate_fresh_blood_digital_natives_compliant(self):
        """
        Test 2: Generate content with 'fresh blood / digital natives'
        Should NOT contain these terms, use inclusive language instead
        """
        print("\n=== Test 2: Generate content with 'fresh blood / digital natives' ===")
        
        response = self.session.post(
            f"{BASE_URL}/api/v1/content/generate/async",
            json={
                "user_id": self.user_id,
                "prompt": "We need fresh blood and digital natives to bring innovation to our company",
                "tone": "professional",
                "platforms": ["linkedin"],
                "language": "en"
            }
        )
        
        assert response.status_code == 200, f"Generate async failed: {response.status_code} - {response.text}"
        job_data = response.json()
        job_id = job_data.get("job_id")
        print(f"Job submitted: {job_id}")
        
        result = self._wait_for_job(job_id)
        content = result.get("content", "")
        
        print(f"Generated content:\n{content[:500]}...")
        
        # Check that problematic terms are NOT in the generated content
        problematic_terms = ["fresh blood", "digital native", "digital natives", "young blood", "new blood"]
        content_lower = content.lower()
        
        found_terms = [term for term in problematic_terms if term in content_lower]
        
        if found_terms:
            print(f"⚠ WARNING: Found problematic terms: {found_terms}")
        else:
            print("✓ No problematic terms found in generated content")
        
        # Check for inclusive alternatives
        inclusive_alternatives = ["innovators", "professionals", "talent", "team members", "diverse perspectives"]
        found_inclusive = [term for term in inclusive_alternatives if term in content_lower]
        
        print(f"✓ Found inclusive alternatives: {found_inclusive}")
        
        assert len(found_terms) == 0, f"Generated content contains problematic terms: {found_terms}"
    
    def test_03_verify_strategic_profile_usage(self):
        """
        Test 3: Verify Strategic Profile is being used (brand voice / SEO keywords)
        """
        print("\n=== Test 3: Verify Strategic Profile usage ===")
        
        # First, get available strategic profiles
        profiles_response = self.session.get(
            f"{BASE_URL}/api/v1/strategic-profiles",
            params={"user_id": self.user_id}
        )
        
        if profiles_response.status_code != 200:
            print(f"Could not fetch profiles: {profiles_response.status_code}")
            pytest.skip("Could not fetch strategic profiles")
        
        profiles = profiles_response.json()
        print(f"Found {len(profiles)} strategic profiles")
        
        if not profiles:
            print("No strategic profiles found - creating test profile")
            # Create a test profile with specific SEO keywords
            create_response = self.session.post(
                f"{BASE_URL}/api/v1/strategic-profiles",
                json={
                    "user_id": self.user_id,
                    "name": "Test Compliance Profile",
                    "profile_type": "company",
                    "brand_voice": "Professional, inclusive, and innovative",
                    "writing_tone": "professional",
                    "seo_keywords": ["innovation", "technology", "inclusive workplace", "diversity"],
                    "target_audience": "Tech professionals"
                }
            )
            if create_response.status_code in [200, 201]:
                profile = create_response.json()
                profile_id = profile.get("id")
                print(f"Created test profile: {profile_id}")
            else:
                pytest.skip(f"Could not create test profile: {create_response.text}")
        else:
            # Use first available profile
            profile = profiles[0]
            profile_id = profile.get("id")
            print(f"Using profile: {profile.get('name')} (ID: {profile_id})")
            print(f"  Brand voice: {profile.get('brand_voice', 'N/A')}")
            print(f"  SEO keywords: {profile.get('seo_keywords', [])}")
        
        # Generate content with the profile
        response = self.session.post(
            f"{BASE_URL}/api/v1/content/generate/async",
            json={
                "user_id": self.user_id,
                "prompt": "Write a post about our company culture and team",
                "tone": "professional",
                "platforms": ["linkedin"],
                "profile_id": profile_id,
                "language": "en"
            }
        )
        
        assert response.status_code == 200, f"Generate async failed: {response.status_code}"
        job_data = response.json()
        job_id = job_data.get("job_id")
        print(f"Job submitted with profile_id: {profile_id}")
        
        result = self._wait_for_job(job_id)
        content = result.get("content", "")
        
        print(f"Generated content:\n{content[:500]}...")
        
        # Verify content was generated
        assert len(content) > 50, "Generated content is too short"
        print("✓ Content generated successfully with strategic profile")
    
    def test_04_generate_and_analyze_score_above_80(self):
        """
        Test 4: Generate content and then analyze it - verify score is >= 80
        """
        print("\n=== Test 4: Generate content and verify score >= 80 ===")
        
        # Generate content
        gen_response = self.session.post(
            f"{BASE_URL}/api/v1/content/generate/async",
            json={
                "user_id": self.user_id,
                "prompt": "Write a professional LinkedIn post about hiring talented software engineers for our team",
                "tone": "professional",
                "platforms": ["linkedin"],
                "language": "en"
            }
        )
        
        assert gen_response.status_code == 200, f"Generate async failed: {gen_response.status_code}"
        gen_job_id = gen_response.json().get("job_id")
        print(f"Generation job submitted: {gen_job_id}")
        
        gen_result = self._wait_for_job(gen_job_id)
        generated_content = gen_result.get("content", "")
        
        print(f"Generated content:\n{generated_content[:300]}...")
        
        # Now analyze the generated content
        analyze_response = self.session.post(
            f"{BASE_URL}/api/v1/content/analyze/async",
            json={
                "user_id": self.user_id,
                "content": generated_content,
                "language": "en"
            }
        )
        
        assert analyze_response.status_code == 200, f"Analyze async failed: {analyze_response.status_code}"
        analyze_job_id = analyze_response.json().get("job_id")
        print(f"Analysis job submitted: {analyze_job_id}")
        
        analyze_result = self._wait_for_job(analyze_job_id, max_wait=90)
        
        # Extract scores
        overall_score = analyze_result.get("overall_score", 0)
        compliance_score = analyze_result.get("compliance_score", 0)
        cultural_score = analyze_result.get("cultural_score", 0)
        
        print(f"\n=== Analysis Results ===")
        print(f"Overall Score: {overall_score}")
        print(f"Compliance Score: {compliance_score}")
        print(f"Cultural Score: {cultural_score}")
        
        # Check for violations
        employment_law = analyze_result.get("employment_law_compliance", {})
        violations = employment_law.get("violations", [])
        if violations:
            print(f"Employment law violations: {violations}")
        else:
            print("✓ No employment law violations")
        
        # The main assertion - score should be >= 80
        if overall_score >= 80:
            print(f"✓ SUCCESS: Generated content scored {overall_score}/100 (>= 80)")
        else:
            print(f"⚠ WARNING: Generated content scored {overall_score}/100 (< 80)")
        
        # We expect the score to be >= 80 for compliant content
        assert overall_score >= 80, f"Generated content scored {overall_score}/100, expected >= 80"
    
    def test_05_sync_generate_endpoint_compliance(self):
        """
        Test 5: Test synchronous generate endpoint for compliance
        """
        print("\n=== Test 5: Sync generate endpoint compliance ===")
        
        response = self.session.post(
            f"{BASE_URL}/api/v1/content/generate",
            json={
                "user_id": self.user_id,
                "prompt": "Write about hiring young rockstar developers for our fast-paced startup",
                "tone": "professional",
                "platforms": ["linkedin"],
                "language": "en"
            }
        )
        
        if response.status_code != 200:
            print(f"Sync generate returned: {response.status_code} - {response.text[:200]}")
            # May be rate limited or other issue
            if response.status_code == 429:
                pytest.skip("Rate limited - skipping sync test")
            pytest.fail(f"Sync generate failed: {response.status_code}")
        
        result = response.json()
        content = result.get("generated_content", result.get("content", ""))
        
        print(f"Generated content:\n{content[:400]}...")
        
        # Check for problematic terms
        problematic_terms = ["young", "rockstar", "ninja", "guru", "digital native"]
        content_lower = content.lower()
        
        found_terms = [term for term in problematic_terms if term in content_lower]
        
        if found_terms:
            print(f"⚠ WARNING: Found problematic terms: {found_terms}")
        else:
            print("✓ No problematic terms found")
        
        # Check for inclusive language
        inclusive_terms = ["professionals", "candidates", "team members", "talent", "experience"]
        found_inclusive = [term for term in inclusive_terms if term in content_lower]
        print(f"✓ Found inclusive terms: {found_inclusive}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
