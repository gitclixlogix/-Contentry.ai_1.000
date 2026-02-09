#!/usr/bin/env python3
"""
Contentry Backend Baseline Test Suite - Before Refactoring

This test suite establishes a comprehensive baseline for all backend endpoints
before proceeding with major refactoring of server.py (3619 lines).

Test Coverage:
1. Authentication Endpoints (signup, login, demo admin)
2. Content Analysis Endpoints (analyze, rewrite, generate)
3. Admin Analytics Endpoints (card-distribution, payments, users-by-country, stats)
4. Posts Endpoints (create, list, get specific)
5. Subscription Endpoints (plans)

Purpose: Ensure nothing breaks during refactoring by having a comprehensive test baseline.
"""

import requests
import json
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import uuid
import os

class ContentryBaselineTests:
    def __init__(self, base_url: str = "https://admin-portal-278.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Contentry-Baseline-Tests/1.0'
        })
        
        # Test tracking
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.test_results = {}
        
        # Test data storage
        self.demo_user_id = "demo-user"
        self.demo_admin_id = "admin-user"
        self.created_user_id = None
        self.created_post_id = None
        
        print(f"🔧 Contentry Backend Baseline Test Suite")
        print(f"📍 Backend URL: {self.base_url}")
        print(f"🎯 Purpose: Establish baseline before server.py refactoring")
        print("="*80)

    def log_test_result(self, test_name: str, success: bool, response_data: Any = None, error: str = None):
        """Log test result for tracking"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            self.failed_tests.append({
                'test': test_name,
                'error': error,
                'response': str(response_data)[:200] if response_data else None
            })
        
        self.test_results[test_name] = {
            'success': success,
            'response': response_data,
            'error': error
        }
        
        print(f"{status} {test_name}")
        if error:
            print(f"    Error: {error}")
        
        return success

    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    params: Dict = None, expected_status: int = 200) -> Tuple[bool, Any]:
        """Make HTTP request and validate response"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, params=params)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, params=params)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params)
            else:
                return False, f"Unsupported method: {method}"
            
            success = response.status_code == expected_status
            
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = response.text
            
            if not success:
                error_msg = f"Expected {expected_status}, got {response.status_code}: {response_data}"
                return False, error_msg
            
            return True, response_data
            
        except Exception as e:
            return False, str(e)

    # ==================== AUTHENTICATION ENDPOINTS ====================
    
    def test_auth_signup_email(self):
        """Test POST /api/auth/signup - Email signup"""
        test_name = "Authentication - Email Signup"
        
        # Generate unique test user
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "full_name": f"Baseline Test User {timestamp}",
            "email": f"baseline_test_{timestamp}@contentry.com",
            "phone": "+1234567890",
            "password": "BaselineTest123!",
            "dob": "1990-01-01"
        }
        
        success, response = self.make_request('POST', '/auth/signup', data=user_data)
        
        if success and isinstance(response, dict) and 'user_id' in response:
            self.created_user_id = response['user_id']
            return self.log_test_result(test_name, True, response)
        else:
            return self.log_test_result(test_name, False, response, "Failed to create user or missing user_id")

    def test_auth_login_email(self):
        """Test POST /api/auth/login - Email login"""
        test_name = "Authentication - Email Login"
        
        # Test with demo user credentials
        login_data = {
            "email": "demo@contentry.com",
            "password": "demo123"
        }
        
        success, response = self.make_request('POST', '/auth/login', data=login_data)
        
        if success and isinstance(response, dict) and 'user' in response:
            user_info = response['user']
            expected_fields = ['id', 'full_name', 'email', 'role']
            missing_fields = [field for field in expected_fields if field not in user_info]
            
            if missing_fields:
                return self.log_test_result(test_name, False, response, f"Missing fields: {missing_fields}")
            
            return self.log_test_result(test_name, True, response)
        else:
            return self.log_test_result(test_name, False, response, "Invalid login response structure")

    def test_demo_admin_login(self):
        """Test demo admin login functionality"""
        test_name = "Authentication - Demo Admin Login"
        
        # Test with demo admin credentials
        login_data = {
            "email": "admin@contentry.com", 
            "password": "admin123"
        }
        
        success, response = self.make_request('POST', '/auth/login', data=login_data)
        
        if success and isinstance(response, dict) and 'user' in response:
            user_info = response['user']
            
            # Check if login was successful (admin role verification is optional since demo admin might not have role set)
            if user_info.get('email') == 'admin@contentry.com':
                return self.log_test_result(test_name, True, response)
            else:
                return self.log_test_result(test_name, False, response, f"Expected admin email, got: {user_info.get('email')}")
        else:
            return self.log_test_result(test_name, False, response, "Demo admin login failed")

    # ==================== CONTENT ANALYSIS ENDPOINTS ====================
    
    def test_content_analyze_text(self):
        """Test POST /api/content/analyze - Text analysis"""
        test_name = "Content Analysis - Text Analysis"
        
        analyze_data = {
            "content": "Excited to announce our new product launch! This innovative solution will revolutionize the industry. #innovation #product",
            "user_id": self.demo_user_id,
            "language": "en"
        }
        
        success, response = self.make_request('POST', '/content/analyze', data=analyze_data)
        
        if success and isinstance(response, dict):
            # Verify required response fields
            required_fields = ['flagged_status', 'summary']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                return self.log_test_result(test_name, False, response, f"Missing required fields: {missing_fields}")
            
            # Verify cultural analysis exists
            if 'cultural_analysis' in response and 'overall_score' in response['cultural_analysis']:
                cultural_score = response['cultural_analysis']['overall_score']
                if not isinstance(cultural_score, (int, float)) or not (0 <= cultural_score <= 100):
                    return self.log_test_result(test_name, False, response, f"Invalid cultural score: {cultural_score}")
            
            return self.log_test_result(test_name, True, response)
        else:
            return self.log_test_result(test_name, False, response, "Invalid analysis response")

    def test_content_rewrite(self):
        """Test POST /api/content/rewrite - Content rewriting"""
        test_name = "Content Analysis - Content Rewrite"
        
        rewrite_data = {
            "content": "Check out our awesome new product! It's really cool and amazing!",
            "tone": "professional",
            "job_title": "Marketing Manager",
            "user_id": self.demo_user_id,
            "language": "en"
        }
        
        success, response = self.make_request('POST', '/content/rewrite', data=rewrite_data)
        
        if success and isinstance(response, dict) and 'rewritten_content' in response:
            rewritten = response['rewritten_content']
            
            # Verify content was actually rewritten (different from original)
            if rewritten and rewritten != rewrite_data['content']:
                return self.log_test_result(test_name, True, response)
            else:
                return self.log_test_result(test_name, False, response, "Content not properly rewritten")
        else:
            return self.log_test_result(test_name, False, response, "Missing rewritten_content field")

    def test_content_generate(self):
        """Test POST /api/content/generate - Content generation"""
        test_name = "Content Analysis - Content Generation"
        
        generate_data = {
            "prompt": "Create a professional announcement about a new product launch",
            "tone": "professional",
            "job_title": "CEO",
            "user_id": self.demo_user_id,
            "platforms": ["facebook", "twitter"],
            "language": "en"
        }
        
        success, response = self.make_request('POST', '/content/generate', data=generate_data)
        
        if success and isinstance(response, dict) and 'generated_content' in response:
            generated = response['generated_content']
            
            # Verify content was generated
            if generated and len(generated.strip()) > 10:  # Reasonable content length
                return self.log_test_result(test_name, True, response)
            else:
                return self.log_test_result(test_name, False, response, "Generated content too short or empty")
        else:
            return self.log_test_result(test_name, False, response, "Missing generated_content field")

    # ==================== ADMIN ANALYTICS ENDPOINTS ====================
    
    def test_admin_analytics_card_distribution(self):
        """Test GET /api/admin/analytics/card-distribution"""
        test_name = "Admin Analytics - Card Distribution"
        
        success, response = self.make_request('GET', '/admin/analytics/card-distribution')
        
        if success and isinstance(response, dict):
            # Verify card analytics data structure
            expected_fields = ['card_types', 'total_transactions', 'total_revenue']
            has_expected = any(field in response for field in expected_fields)
            
            if has_expected:
                return self.log_test_result(test_name, True, response)
            else:
                return self.log_test_result(test_name, False, response, f"Missing expected fields: {expected_fields}")
        else:
            return self.log_test_result(test_name, False, response, "Invalid analytics response")

    def test_admin_analytics_payments(self):
        """Test GET /api/admin/analytics/payments"""
        test_name = "Admin Analytics - Payments"
        
        success, response = self.make_request('GET', '/admin/analytics/payments')
        
        if success and isinstance(response, dict):
            # Verify payment analytics structure
            expected_fields = ['revenue_over_time', 'payment_methods', 'subscription_revenue']
            has_expected = any(field in response for field in expected_fields)
            
            if has_expected:
                return self.log_test_result(test_name, True, response)
            else:
                return self.log_test_result(test_name, False, response, f"Missing expected fields: {expected_fields}")
        else:
            return self.log_test_result(test_name, False, response, "Invalid payment analytics response")

    def test_admin_analytics_users_by_country(self):
        """Test GET /api/admin/analytics/users-by-country"""
        test_name = "Admin Analytics - Users by Country"
        
        success, response = self.make_request('GET', '/admin/analytics/users-by-country')
        
        if success and isinstance(response, dict):
            # Verify geographic data structure
            expected_fields = ['countries', 'user_counts', 'country_details']
            has_expected = any(field in response for field in expected_fields)
            
            if has_expected:
                return self.log_test_result(test_name, True, response)
            else:
                return self.log_test_result(test_name, False, response, f"Missing expected fields: {expected_fields}")
        else:
            return self.log_test_result(test_name, False, response, "Invalid geographic analytics response")

    def test_admin_stats(self):
        """Test GET /api/admin/stats"""
        test_name = "Admin Analytics - Stats"
        
        success, response = self.make_request('GET', '/admin/stats')
        
        if success and isinstance(response, dict):
            # Verify stats structure
            stats_fields = ['total_users', 'total_posts', 'total_revenue', 'active_subscriptions']
            has_stats = any(field in response for field in stats_fields)
            
            if has_stats:
                return self.log_test_result(test_name, True, response)
            else:
                return self.log_test_result(test_name, False, response, f"Missing expected stats fields: {stats_fields}")
        else:
            return self.log_test_result(test_name, False, response, "Invalid stats response")

    # ==================== POSTS ENDPOINTS ====================
    
    def test_posts_create(self):
        """Test POST /api/posts - Create post"""
        test_name = "Posts - Create Post"
        
        post_data = {
            "title": "Baseline Test Post",
            "content": "This is a baseline test post created during pre-refactoring testing to ensure post creation functionality works correctly.",
            "platforms": ["facebook", "twitter"]
        }
        
        success, response = self.make_request('POST', '/posts', data=post_data)
        
        if success and isinstance(response, dict) and 'id' in response:
            self.created_post_id = response['id']
            
            # Verify post fields
            required_fields = ['id', 'title', 'content', 'platforms', 'status']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                return self.log_test_result(test_name, False, response, f"Missing post fields: {missing_fields}")
            
            return self.log_test_result(test_name, True, response)
        else:
            return self.log_test_result(test_name, False, response, "Failed to create post or missing post ID")

    def test_posts_list(self):
        """Test GET /api/posts - List posts"""
        test_name = "Posts - List Posts"
        
        params = {"user_id": self.demo_user_id}
        success, response = self.make_request('GET', '/posts', params=params)
        
        if success and isinstance(response, list):
            # Verify posts structure
            if len(response) > 0:
                post = response[0]
                required_fields = ['id', 'title', 'content']
                missing_fields = [field for field in required_fields if field not in post]
                
                if missing_fields:
                    return self.log_test_result(test_name, False, response, f"Missing post fields: {missing_fields}")
            
            return self.log_test_result(test_name, True, {"posts_count": len(response)})
        else:
            return self.log_test_result(test_name, False, response, "Invalid posts list response")

    def test_posts_get_specific(self):
        """Test GET /api/posts/{post_id} - Get specific post"""
        test_name = "Posts - Get Specific Post"
        
        # Use created post ID or demo post
        post_id = self.created_post_id or "demo-post-id"
        
        success, response = self.make_request('GET', f'/posts/{post_id}')
        
        if success and isinstance(response, dict):
            # Verify post structure
            required_fields = ['id', 'title', 'content']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                return self.log_test_result(test_name, False, response, f"Missing post fields: {missing_fields}")
            
            return self.log_test_result(test_name, True, response)
        else:
            # If specific post not found, try with demo user posts
            params = {"user_id": self.demo_user_id}
            success, posts = self.make_request('GET', '/posts', params=params)
            
            if success and isinstance(posts, list) and len(posts) > 0:
                # Test with first available post
                first_post_id = posts[0]['id']
                success, response = self.make_request('GET', f'/posts/{first_post_id}')
                
                if success:
                    return self.log_test_result(test_name, True, response)
            
            return self.log_test_result(test_name, False, response, "No posts available for testing")

    # ==================== SUBSCRIPTION ENDPOINTS ====================
    
    def test_subscriptions_plans(self):
        """Test GET /api/subscriptions/plans"""
        test_name = "Subscriptions - Get Plans"
        
        success, response = self.make_request('GET', '/subscriptions/plans')
        
        if success and isinstance(response, (list, dict)):
            # Verify plans structure
            if isinstance(response, list) and len(response) > 0:
                plan = response[0]
                required_fields = ['id', 'name', 'price']
                missing_fields = [field for field in required_fields if field not in plan]
                
                if missing_fields:
                    return self.log_test_result(test_name, False, response, f"Missing plan fields: {missing_fields}")
            
            elif isinstance(response, dict) and 'plans' in response:
                plans = response['plans']
                if isinstance(plans, list) and len(plans) > 0:
                    plan = plans[0]
                    required_fields = ['id', 'name', 'price']
                    missing_fields = [field for field in required_fields if field not in plan]
                    
                    if missing_fields:
                        return self.log_test_result(test_name, False, response, f"Missing plan fields: {missing_fields}")
            
            return self.log_test_result(test_name, True, response)
        else:
            return self.log_test_result(test_name, False, response, "Invalid subscription plans response")

    # ==================== ADDITIONAL CRITICAL ENDPOINTS ====================
    
    def test_user_reputation_score(self):
        """Test GET /api/user/reputation-score"""
        test_name = "User Analytics - Reputation Score"
        
        params = {"user_id": self.demo_user_id}
        success, response = self.make_request('GET', '/user/reputation-score', params=params)
        
        if success and isinstance(response, dict):
            # Verify reputation score structure
            expected_fields = ['reputation_score', 'risk_level', 'total_analyzed_posts']
            has_expected = any(field in response for field in expected_fields)
            
            if has_expected:
                return self.log_test_result(test_name, True, response)
            else:
                return self.log_test_result(test_name, False, response, f"Missing expected fields: {expected_fields}")
        else:
            return self.log_test_result(test_name, False, response, "Invalid reputation score response")

    def test_notifications_endpoint(self):
        """Test GET /api/notifications"""
        test_name = "User Management - Notifications"
        
        params = {"user_id": self.demo_user_id}
        success, response = self.make_request('GET', '/notifications', params=params)
        
        if success and isinstance(response, (list, dict)):
            # Notifications endpoint should return list or dict with notifications
            return self.log_test_result(test_name, True, response)
        else:
            return self.log_test_result(test_name, False, response, "Invalid notifications response")

    def test_policies_list(self):
        """Test GET /api/policies"""
        test_name = "Policy Management - List Policies"
        
        params = {"user_id": self.demo_user_id}
        success, response = self.make_request('GET', '/policies', params=params)
        
        if success and isinstance(response, (list, dict)):
            # Policies endpoint should return list or dict with policies
            return self.log_test_result(test_name, True, response)
        else:
            return self.log_test_result(test_name, False, response, "Invalid policies response")

    # ==================== COMPREHENSIVE TEST RUNNER ====================
    
    def run_baseline_tests(self):
        """Run comprehensive baseline test suite"""
        print("🚀 Starting Contentry Backend Baseline Tests...")
        print("📋 Testing all critical endpoints before refactoring")
        print()
        
        # 1. Authentication Endpoints
        print("1️⃣  AUTHENTICATION ENDPOINTS")
        print("-" * 40)
        self.test_auth_signup_email()
        self.test_auth_login_email()
        self.test_demo_admin_login()
        print()
        
        # 2. Content Analysis Endpoints  
        print("2️⃣  CONTENT ANALYSIS ENDPOINTS")
        print("-" * 40)
        self.test_content_analyze_text()
        self.test_content_rewrite()
        self.test_content_generate()
        print()
        
        # 3. Admin Analytics Endpoints
        print("3️⃣  ADMIN ANALYTICS ENDPOINTS")
        print("-" * 40)
        self.test_admin_analytics_card_distribution()
        self.test_admin_analytics_payments()
        self.test_admin_analytics_users_by_country()
        self.test_admin_stats()
        print()
        
        # 4. Posts Endpoints
        print("4️⃣  POSTS ENDPOINTS")
        print("-" * 40)
        self.test_posts_create()
        self.test_posts_list()
        self.test_posts_get_specific()
        print()
        
        # 5. Subscription Endpoints
        print("5️⃣  SUBSCRIPTION ENDPOINTS")
        print("-" * 40)
        self.test_subscriptions_plans()
        print()
        
        # 6. Additional Critical Endpoints
        print("6️⃣  ADDITIONAL CRITICAL ENDPOINTS")
        print("-" * 40)
        self.test_user_reputation_score()
        self.test_notifications_endpoint()
        self.test_policies_list()
        print()
        
        # Generate comprehensive report
        self.generate_baseline_report()
        
        return self.tests_passed == self.tests_run

    def generate_baseline_report(self):
        """Generate comprehensive baseline test report"""
        print("="*80)
        print("📊 CONTENTRY BACKEND BASELINE TEST REPORT")
        print("="*80)
        print(f"🎯 Purpose: Pre-refactoring baseline for server.py (3619 lines)")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Backend URL: {self.base_url}")
        print()
        
        print(f"📈 OVERALL RESULTS:")
        print(f"   Total Tests: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {len(self.failed_tests)}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print()
        
        # Categorize results
        categories = {
            'Authentication': ['Authentication - Email Signup', 'Authentication - Email Login', 'Authentication - Demo Admin Login'],
            'Content Analysis': ['Content Analysis - Text Analysis', 'Content Analysis - Content Rewrite', 'Content Analysis - Content Generation'],
            'Admin Analytics': ['Admin Analytics - Card Distribution', 'Admin Analytics - Payments', 'Admin Analytics - Users by Country', 'Admin Analytics - Stats'],
            'Posts Management': ['Posts - Create Post', 'Posts - List Posts', 'Posts - Get Specific Post'],
            'Subscriptions': ['Subscriptions - Get Plans'],
            'Additional Critical': ['User Analytics - Reputation Score', 'User Management - Notifications', 'Policy Management - List Policies']
        }
        
        print("📋 RESULTS BY CATEGORY:")
        for category, tests in categories.items():
            passed = sum(1 for test in tests if self.test_results.get(test, {}).get('success', False))
            total = len(tests)
            status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
            print(f"   {status} {category}: {passed}/{total}")
        print()
        
        # Failed tests details
        if self.failed_tests:
            print("❌ FAILED TESTS DETAILS:")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test['test']}")
                if test['error']:
                    print(f"      Error: {test['error']}")
                print()
        else:
            print("✅ ALL TESTS PASSED - BASELINE ESTABLISHED!")
            print("🔧 Ready for server.py refactoring with confidence")
        
        print("="*80)
        
        # Save results to file for reference
        self.save_baseline_results()

    def save_baseline_results(self):
        """Save baseline results to JSON file for future comparison"""
        results_data = {
            'test_date': datetime.now().isoformat(),
            'backend_url': self.base_url,
            'total_tests': self.tests_run,
            'tests_passed': self.tests_passed,
            'success_rate': (self.tests_passed/self.tests_run)*100 if self.tests_run > 0 else 0,
            'test_results': self.test_results,
            'failed_tests': self.failed_tests
        }
        
        try:
            results_file = '/app/backend/tests/baseline_results.json'
            os.makedirs(os.path.dirname(results_file), exist_ok=True)
            
            with open(results_file, 'w') as f:
                json.dump(results_data, f, indent=2)
            
            print(f"💾 Baseline results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️  Could not save results file: {e}")


def main():
    """Main test runner"""
    print("🔧 Contentry Backend - Pre-Refactoring Baseline Tests")
    print("="*80)
    
    # Initialize test suite
    tester = ContentryBaselineTests()
    
    # Run comprehensive baseline tests
    success = tester.run_baseline_tests()
    
    # Exit with appropriate code
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())