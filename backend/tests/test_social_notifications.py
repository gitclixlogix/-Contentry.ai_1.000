#!/usr/bin/env python3
"""
Test Social Media Integration and Notification Services
As requested in the review request
"""

import requests
import json
import sys
from datetime import datetime

class SocialNotificationTester:
    def __init__(self, base_url="http://localhost:8001/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.user_id = "test-user-123"

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        
        # Set default headers
        if headers is None:
            headers = {}
        
        # Add content type for JSON requests
        if method in ['POST', 'PUT', 'PATCH'] and data:
            headers['Content-Type'] = 'application/json'
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json() if response.content else {}
                    if response_data:
                        # Print key information from response
                        if 'is_mocked' in response_data:
                            print(f"   📊 Mock Mode: {response_data['is_mocked']}")
                        if 'message' in response_data:
                            print(f"   📊 Message: {response_data['message']}")
                        if 'otp_for_testing' in response_data:
                            print(f"   📊 Test OTP: {response_data['otp_for_testing']}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                self.failed_tests.append({
                    "test": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:200]
                })
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "test": name,
                "error": str(e)
            })
            return False, {}

    def test_social_media_endpoints(self):
        """Test Social Media API endpoints"""
        print("\n" + "="*60)
        print("SOCIAL MEDIA API ENDPOINTS TESTING")
        print("="*60)
        
        # Test 1: Social Media Configuration Status
        print("\n1. Testing Social Media Configuration Status...")
        success, response = self.run_test(
            "Social Media Config Status",
            "GET",
            "social/config-status",
            200
        )
        
        if success:
            print(f"   📊 Configuration Status Retrieved:")
            for platform, config in response.items():
                if isinstance(config, dict):
                    print(f"      - {platform.title()}: {'✓' if config.get('configured') else '✗'} configured")
        
        # Test 2: Twitter Auth URL
        print("\n2. Testing Twitter Auth URL...")
        self.run_test(
            "Twitter Auth URL",
            "GET",
            "social/twitter/auth",
            200,
            headers={"X-User-ID": self.user_id}
        )
        
        # Test 3: LinkedIn Auth URL
        print("\n3. Testing LinkedIn Auth URL...")
        self.run_test(
            "LinkedIn Auth URL",
            "GET",
            "social/linkedin/auth",
            200,
            headers={"X-User-ID": self.user_id}
        )
        
        # Test 4: Twitter Post
        print("\n4. Testing Twitter Post...")
        self.run_test(
            "Twitter Post",
            "POST",
            "social/twitter/post",
            200,
            data={"content": "Test tweet"},
            headers={"X-User-ID": self.user_id}
        )
        
        # Test 5: LinkedIn Post
        print("\n5. Testing LinkedIn Post...")
        self.run_test(
            "LinkedIn Post",
            "POST",
            "social/linkedin/post",
            200,
            data={"content": "Test LinkedIn post"},
            headers={"X-User-ID": self.user_id}
        )

    def test_notification_endpoints(self):
        """Test Notification Service endpoints"""
        print("\n" + "="*60)
        print("NOTIFICATION SERVICE ENDPOINTS TESTING")
        print("="*60)
        
        # Test 1: Notification Configuration Status
        print("\n1. Testing Notification Configuration Status...")
        success, response = self.run_test(
            "Notification Config Status",
            "GET",
            "notifications/config-status",
            200
        )
        
        if success:
            print(f"   📊 Notification Services Status:")
            if 'sms' in response:
                sms_config = response['sms']
                print(f"      - SMS ({sms_config.get('provider', 'unknown')}): {'✓' if sms_config.get('configured') else '✗'} configured")
            if 'email' in response:
                email_config = response['email']
                print(f"      - Email ({email_config.get('provider', 'unknown')}): {'✓' if email_config.get('configured') else '✗'} configured")
        
        # Test 2: Send SMS OTP
        print("\n2. Testing SMS OTP Send...")
        success, response = self.run_test(
            "Send SMS OTP",
            "POST",
            "notifications/sms/send-otp",
            200,
            data={"phone": "+1234567890"}
        )
        
        # Test 3: Send SMS Message
        print("\n3. Testing SMS Message Send...")
        self.run_test(
            "Send SMS Message",
            "POST",
            "notifications/sms/send",
            200,
            data={"phone": "+1234567890", "message": "Test message"}
        )
        
        # Test 4: Send Email
        print("\n4. Testing Email Send...")
        self.run_test(
            "Send Email",
            "POST",
            "notifications/email/send",
            200,
            data={
                "to_email": "test@example.com",
                "subject": "Test",
                "message": "Test email"
            }
        )

    def test_scheduler_endpoints(self):
        """Test existing scheduler endpoints"""
        print("\n" + "="*60)
        print("SCHEDULER ENDPOINTS TESTING")
        print("="*60)
        
        # Test 1: Get Scheduler Status
        print("\n1. Testing Scheduler Status...")
        self.run_test(
            "Get Scheduler Status",
            "GET",
            "scheduler/status",
            200
        )
        
        # Test 2: Get Scheduled Posts
        print("\n2. Testing Scheduled Posts...")
        self.run_test(
            "Get Scheduled Posts",
            "GET",
            "scheduler/posts/scheduled",
            200,
            headers={"X-User-ID": self.user_id}
        )

    def run_all_tests(self):
        """Run all social media and notification tests"""
        print("🚀 STARTING SOCIAL MEDIA & NOTIFICATION SERVICES TESTING")
        print(f"Base URL: {self.base_url}")
        print(f"Test User ID: {self.user_id}")
        print("="*80)
        
        # Run test suites
        self.test_social_media_endpoints()
        self.test_notification_endpoints()
        self.test_scheduler_endpoints()
        
        # Print results
        print("\n" + "="*80)
        print("TEST RESULTS SUMMARY")
        print("="*80)
        print(f"📊 Total Tests Run: {self.tests_run}")
        print(f"📊 Tests Passed: {self.tests_passed}")
        print(f"📊 Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📊 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test.get('test', 'Unknown Test')}")
                if 'error' in test:
                    print(f"      Error: {test['error']}")
                else:
                    print(f"      Expected: {test.get('expected')}, Got: {test.get('actual')}")
                    if test.get('response'):
                        print(f"      Response: {test['response'][:100]}...")
        else:
            print("\n✅ ALL TESTS PASSED!")
        
        print("\n" + "="*80)
        print("TESTING COMPLETE")
        print("="*80)
        
        return self.tests_passed == self.tests_run


def main():
    """Main test execution"""
    print("Social Media Integration & Notification Services Test Suite")
    print("Testing newly implemented endpoints as per review request")
    print("="*80)
    
    tester = SocialNotificationTester()
    success = tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())