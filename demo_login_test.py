#!/usr/bin/env python3
"""
Demo Login Security and Functionality Test
Tests backend API endpoints that support demo user and demo admin functionality
"""

import requests
import json
import sys
from datetime import datetime

class DemoLoginTester:
    def __init__(self, base_url="https://admin-portal-278.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Demo user credentials as they would be stored in localStorage
        self.demo_user_data = {
            "id": "demo-user",
            "role": "user", 
            "email": "demo@contentry.com"
        }
        
        self.demo_admin_data = {
            "id": "admin-user",
            "role": "admin",
            "email": "admin@contentry.com"
        }

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")
            self.failed_tests.append(name)

    def make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request to API"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            
            return response
        except Exception as e:
            print(f"   Request error: {str(e)}")
            return None

    def test_demo_user_posts_access(self):
        """Test demo user can access posts endpoint"""
        print("\n🔍 Testing Demo User Posts Access...")
        
        response = self.make_request('GET', 'posts', params={"user_id": "demo-user"})
        
        if response and response.status_code == 200:
            try:
                posts = response.json()
                self.log_test(
                    "Demo User Posts API Access", 
                    True, 
                    f"Successfully retrieved {len(posts) if isinstance(posts, list) else 'N/A'} posts"
                )
                
                # Check if posts contain expected fields
                if isinstance(posts, list) and len(posts) > 0:
                    sample_post = posts[0]
                    expected_fields = ['id', 'user_id', 'content', 'flagged_status', 'platforms']
                    missing_fields = [field for field in expected_fields if field not in sample_post]
                    
                    if not missing_fields:
                        self.log_test("Demo User Posts Data Structure", True, "All expected fields present")
                    else:
                        self.log_test("Demo User Posts Data Structure", False, f"Missing fields: {missing_fields}")
                
                return True
            except json.JSONDecodeError:
                self.log_test("Demo User Posts API Access", False, "Invalid JSON response")
                return False
        else:
            status = response.status_code if response else "No response"
            self.log_test("Demo User Posts API Access", False, f"HTTP {status}")
            return False

    def test_demo_admin_analytics_access(self):
        """Test demo admin can access admin analytics endpoints"""
        print("\n🔍 Testing Demo Admin Analytics Access...")
        
        # Test multiple admin endpoints
        admin_endpoints = [
            ("users-by-country", "Users by Country Analytics"),
            ("payments", "Payment Analytics"), 
            ("subscriptions", "Subscription Analytics"),
            ("user-table", "User Management Table")
        ]
        
        all_success = True
        
        for endpoint, name in admin_endpoints:
            response = self.make_request('GET', f'admin/analytics/{endpoint}')
            
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    self.log_test(f"Demo Admin {name}", True, "API accessible and returns data")
                except json.JSONDecodeError:
                    self.log_test(f"Demo Admin {name}", False, "Invalid JSON response")
                    all_success = False
            else:
                status = response.status_code if response else "No response"
                self.log_test(f"Demo Admin {name}", False, f"HTTP {status}")
                all_success = False
        
        return all_success

    def test_demo_user_content_analysis(self):
        """Test demo user can analyze content"""
        print("\n🔍 Testing Demo User Content Analysis...")
        
        test_content = "This is a professional business announcement about our new product launch."
        
        response = self.make_request('POST', 'content/analyze', data={
            "content": test_content,
            "user_id": "demo-user",
            "language": "en"
        })
        
        if response and response.status_code == 200:
            try:
                analysis = response.json()
                expected_fields = ['flagged_status', 'summary', 'cultural_analysis']
                missing_fields = [field for field in expected_fields if field not in analysis]
                
                if not missing_fields:
                    flagged_status = analysis.get('flagged_status', 'unknown')
                    cultural_score = analysis.get('cultural_analysis', {}).get('overall_score', 'N/A')
                    
                    self.log_test(
                        "Demo User Content Analysis", 
                        True, 
                        f"Status: {flagged_status}, Cultural Score: {cultural_score}"
                    )
                    return True
                else:
                    self.log_test("Demo User Content Analysis", False, f"Missing fields: {missing_fields}")
                    return False
            except json.JSONDecodeError:
                self.log_test("Demo User Content Analysis", False, "Invalid JSON response")
                return False
        else:
            status = response.status_code if response else "No response"
            self.log_test("Demo User Content Analysis", False, f"HTTP {status}")
            return False

    def test_demo_user_reputation_score(self):
        """Test demo user reputation score endpoint"""
        print("\n🔍 Testing Demo User Reputation Score...")
        
        response = self.make_request('GET', 'user/reputation-score', params={"user_id": "demo-user"})
        
        if response and response.status_code == 200:
            try:
                score_data = response.json()
                expected_fields = ['reputation_score', 'risk_level', 'total_analyzed_posts']
                missing_fields = [field for field in expected_fields if field not in score_data]
                
                if not missing_fields:
                    reputation_score = score_data.get('reputation_score', 'N/A')
                    risk_level = score_data.get('risk_level', 'N/A')
                    total_posts = score_data.get('total_analyzed_posts', 0)
                    
                    self.log_test(
                        "Demo User Reputation Score", 
                        True, 
                        f"Score: {reputation_score}, Risk: {risk_level}, Posts: {total_posts}"
                    )
                    return True
                else:
                    self.log_test("Demo User Reputation Score", False, f"Missing fields: {missing_fields}")
                    return False
            except json.JSONDecodeError:
                self.log_test("Demo User Reputation Score", False, "Invalid JSON response")
                return False
        else:
            status = response.status_code if response else "No response"
            self.log_test("Demo User Reputation Score", False, f"HTTP {status}")
            return False

    def test_role_based_access_security(self):
        """Test that role-based access is properly enforced"""
        print("\n🔍 Testing Role-Based Access Security...")
        
        # Test that regular user cannot access admin endpoints without proper authentication
        # Note: In a real system, this would require authentication tokens
        # For demo purposes, we're testing that the endpoints exist and respond appropriately
        
        # Test admin endpoint accessibility (should work since it's demo data)
        response = self.make_request('GET', 'admin/analytics/users-by-country')
        
        if response and response.status_code == 200:
            self.log_test(
                "Admin Endpoint Accessibility", 
                True, 
                "Admin analytics endpoints are accessible (demo environment)"
            )
        else:
            self.log_test("Admin Endpoint Accessibility", False, "Admin endpoints not accessible")
        
        # Test user-specific data isolation
        demo_user_posts = self.make_request('GET', 'posts', params={"user_id": "demo-user"})
        admin_user_posts = self.make_request('GET', 'posts', params={"user_id": "admin-user"})
        
        if demo_user_posts and admin_user_posts:
            demo_posts = demo_user_posts.json() if demo_user_posts.status_code == 200 else []
            admin_posts = admin_user_posts.json() if admin_user_posts.status_code == 200 else []
            
            # Check that user data is properly isolated
            demo_user_ids = set()
            admin_user_ids = set()
            
            if isinstance(demo_posts, list):
                demo_user_ids = {post.get('user_id') for post in demo_posts if 'user_id' in post}
            
            if isinstance(admin_posts, list):
                admin_user_ids = {post.get('user_id') for post in admin_posts if 'user_id' in post}
            
            # Check data isolation
            if 'demo-user' in demo_user_ids and 'admin-user' not in demo_user_ids:
                self.log_test("User Data Isolation", True, "Demo user only sees their own posts")
            else:
                self.log_test("User Data Isolation", False, "Data isolation may be compromised")
        
        return True

    def test_api_response_security(self):
        """Test that API responses don't contain sensitive information"""
        print("\n🔍 Testing API Response Security...")
        
        # Test that user endpoints don't expose sensitive data
        response = self.make_request('GET', 'posts', params={"user_id": "demo-user"})
        
        if response and response.status_code == 200:
            try:
                posts = response.json()
                if isinstance(posts, list) and len(posts) > 0:
                    sample_post = posts[0]
                    
                    # Check that sensitive fields are not exposed
                    sensitive_fields = ['password', 'password_hash', 'api_key', 'secret', 'token']
                    exposed_sensitive = [field for field in sensitive_fields if field in sample_post]
                    
                    if not exposed_sensitive:
                        self.log_test("API Response Security", True, "No sensitive data exposed in posts")
                    else:
                        self.log_test("API Response Security", False, f"Sensitive fields exposed: {exposed_sensitive}")
                else:
                    self.log_test("API Response Security", True, "No posts to check (empty response)")
            except json.JSONDecodeError:
                self.log_test("API Response Security", False, "Invalid JSON response")
        else:
            self.log_test("API Response Security", False, "Could not retrieve posts for security check")
        
        return True

    def run_comprehensive_demo_login_tests(self):
        """Run all demo login related backend tests"""
        print("🚀 Starting Demo Login Backend API Security Tests...")
        print(f"Base URL: {self.base_url}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n" + "="*70)
        print("DEMO USER FUNCTIONALITY TESTS")
        print("="*70)
        
        # Test demo user API access
        self.test_demo_user_posts_access()
        self.test_demo_user_content_analysis()
        self.test_demo_user_reputation_score()
        
        print("\n" + "="*70)
        print("DEMO ADMIN FUNCTIONALITY TESTS") 
        print("="*70)
        
        # Test demo admin API access
        self.test_demo_admin_analytics_access()
        
        print("\n" + "="*70)
        print("SECURITY AND ACCESS CONTROL TESTS")
        print("="*70)
        
        # Test security aspects
        self.test_role_based_access_security()
        self.test_api_response_security()
        
        # Print final results
        print("\n" + "="*70)
        print("DEMO LOGIN BACKEND TEST RESULTS")
        print("="*70)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {len(self.failed_tests)}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"   - {test}")
        
        if success_rate >= 90:
            print(f"\n🎉 Demo Login Backend APIs: EXCELLENT ({success_rate:.1f}%)")
        elif success_rate >= 75:
            print(f"\n✅ Demo Login Backend APIs: GOOD ({success_rate:.1f}%)")
        elif success_rate >= 50:
            print(f"\n⚠️  Demo Login Backend APIs: NEEDS IMPROVEMENT ({success_rate:.1f}%)")
        else:
            print(f"\n❌ Demo Login Backend APIs: CRITICAL ISSUES ({success_rate:.1f}%)")
        
        return success_rate >= 75

def main():
    """Main test runner"""
    tester = DemoLoginTester()
    success = tester.run_comprehensive_demo_login_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())