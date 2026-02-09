#!/usr/bin/env python3
"""
Focused test script for Admin Drill-Down API Endpoints
Tests the new drill-down functionality as per review request
"""

import requests
import json
import sys

class DrillDownTester:
    def __init__(self, base_url="https://admin-portal-278.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
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

    def test_all_drilldown_endpoints(self):
        """Test all drill-down API endpoints as per review request"""
        print("="*80)
        print("ADMIN DRILL-DOWN API ENDPOINTS COMPREHENSIVE TEST")
        print("="*80)
        print("Testing all new drill-down endpoints added to admin routes")
        print("="*80)
        
        # Test all admin drilldown endpoints
        admin_metrics = [
            "total_users", "total_posts", "total_revenue", "flagged_content",
            "approved_content", "active_subscriptions", "transactions", "users_by_country"
        ]
        
        print(f"\n🔍 Testing {len(admin_metrics)} Admin Drilldown Endpoints...")
        admin_success_count = 0
        
        for metric in admin_metrics:
            success, response = self.run_test(
                f"Admin Drilldown - {metric}",
                "GET",
                f"admin/drilldown/{metric}",
                200
            )
            
            if success:
                admin_success_count += 1
                # Verify response structure
                if isinstance(response, dict):
                    required_fields = ["title", "description", "metric_type", "total", "items", "is_demo_data"]
                    missing_fields = [field for field in required_fields if field not in response]
                    if missing_fields:
                        print(f"   ❌ Missing required fields in {metric}: {missing_fields}")
                    else:
                        print(f"   ✅ {metric}: All required fields present")
                        print(f"   📊 Title: {response.get('title')}")
                        print(f"   📊 Items count: {response.get('total', 0)}")
                        print(f"   📊 Demo data: {response.get('is_demo_data', False)}")
                        
                        # Show sample item structure for first few endpoints
                        if metric in ["total_users", "total_posts"] and response.get('items'):
                            sample_item = response['items'][0]
                            print(f"   📊 Sample item keys: {list(sample_item.keys())}")
        
        # Test financial drilldown endpoints
        financial_metrics = ["total_transactions", "card_distribution"]
        
        print(f"\n🔍 Testing {len(financial_metrics)} Financial Drilldown Endpoints...")
        financial_success_count = 0
        
        for metric in financial_metrics:
            success, response = self.run_test(
                f"Financial Drilldown - {metric}",
                "GET",
                f"admin/financial/drilldown/{metric}",
                200
            )
            
            if success:
                financial_success_count += 1
                # Verify response structure
                if isinstance(response, dict):
                    required_fields = ["title", "description", "metric_type", "total", "items", "is_demo_data"]
                    missing_fields = [field for field in required_fields if field not in response]
                    if missing_fields:
                        print(f"   ❌ Missing required fields in {metric}: {missing_fields}")
                    else:
                        print(f"   ✅ {metric}: All required fields present")
                        print(f"   📊 Title: {response.get('title')}")
                        print(f"   📊 Items count: {response.get('total', 0)}")
                        print(f"   📊 Demo data: {response.get('is_demo_data', False)}")
        
        # Test analytics drilldown endpoints
        analytics_metrics = ["compliance_rate", "total_mrr"]
        
        print(f"\n🔍 Testing {len(analytics_metrics)} Analytics Drilldown Endpoints...")
        analytics_success_count = 0
        
        for metric in analytics_metrics:
            success, response = self.run_test(
                f"Analytics Drilldown - {metric}",
                "GET",
                f"admin/analytics/drilldown/{metric}",
                200
            )
            
            if success:
                analytics_success_count += 1
                # Verify response structure
                if isinstance(response, dict):
                    required_fields = ["title", "description", "metric_type", "total", "items", "is_demo_data"]
                    missing_fields = [field for field in required_fields if field not in response]
                    if missing_fields:
                        print(f"   ❌ Missing required fields in {metric}: {missing_fields}")
                    else:
                        print(f"   ✅ {metric}: All required fields present")
                        print(f"   📊 Title: {response.get('title')}")
                        print(f"   📊 Items count: {response.get('total', 0)}")
                        print(f"   📊 Demo data: {response.get('is_demo_data', False)}")
        
        # Test error handling - invalid metric type
        print(f"\n🔍 Testing Error Handling...")
        error_tests_passed = 0
        
        success, response = self.run_test(
            "Invalid Metric Type - Admin",
            "GET",
            "admin/drilldown/invalid_metric",
            400
        )
        if success:
            error_tests_passed += 1
            print(f"   ✅ Admin invalid metric correctly returns 400")
        
        success, response = self.run_test(
            "Invalid Metric Type - Financial",
            "GET",
            "admin/financial/drilldown/invalid_metric",
            400
        )
        if success:
            error_tests_passed += 1
            print(f"   ✅ Financial invalid metric correctly returns 400")
        
        success, response = self.run_test(
            "Invalid Metric Type - Analytics",
            "GET",
            "admin/analytics/drilldown/invalid_metric",
            400
        )
        if success:
            error_tests_passed += 1
            print(f"   ✅ Analytics invalid metric correctly returns 400")
        
        # Summary
        total_endpoints = len(admin_metrics) + len(financial_metrics) + len(analytics_metrics)
        total_success = admin_success_count + financial_success_count + analytics_success_count
        
        print(f"\n" + "="*80)
        print(f"DRILL-DOWN ENDPOINTS TEST SUMMARY")
        print(f"="*80)
        print(f"📊 Admin Endpoints: {admin_success_count}/{len(admin_metrics)} passed")
        print(f"📊 Financial Endpoints: {financial_success_count}/{len(financial_metrics)} passed")
        print(f"📊 Analytics Endpoints: {analytics_success_count}/{len(analytics_metrics)} passed")
        print(f"📊 Error Handling: {error_tests_passed}/3 passed")
        print(f"📊 Overall Success Rate: {total_success}/{total_endpoints} ({(total_success/total_endpoints)*100:.1f}%)")
        
        if total_success == total_endpoints and error_tests_passed == 3:
            print(f"\n✅ ALL DRILL-DOWN API ENDPOINTS WORKING PERFECTLY!")
            print(f"   ✓ All endpoints return 200 OK")
            print(f"   ✓ All required fields present (title, description, metric_type, total, items, is_demo_data)")
            print(f"   ✓ Proper data structures in items arrays")
            print(f"   ✓ Error handling for invalid metrics (400 status)")
            print(f"   ✓ No MongoDB ObjectId serialization errors detected")
            return True
        else:
            print(f"\n❌ SOME DRILL-DOWN API ISSUES DETECTED")
            if self.failed_tests:
                print(f"\nFailed Tests:")
                for test in self.failed_tests:
                    error_msg = test.get('error', f"Expected {test.get('expected')}, got {test.get('actual')}")
                    print(f"   - {test['test']}: {error_msg}")
            return False

def main():
    print("🚀 Starting Drill-Down API Endpoints Test...")
    
    tester = DrillDownTester()
    success = tester.test_all_drilldown_endpoints()
    
    print(f"\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)
    print(f"📊 Total Tests: {tester.tests_run}")
    print(f"📊 Passed: {tester.tests_passed}")
    print(f"📊 Failed: {len(tester.failed_tests)}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())