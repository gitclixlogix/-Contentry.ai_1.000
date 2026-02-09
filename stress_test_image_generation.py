#!/usr/bin/env python3
"""
Stress test for image generation to verify retry logic and fallback mechanisms
"""

import requests
import time
import concurrent.futures
import json
from datetime import datetime

class ImageGenerationStressTest:
    def __init__(self, base_url="http://localhost:8001/api"):
        self.base_url = base_url
        self.user_id = None
        
    def login(self):
        """Login and get user ID"""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={
                "email": "demo@test.com",
                "password": "password123"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.user_id = data.get('user_id') or data.get('user', {}).get('id')
            print(f"✅ Logged in successfully - User ID: {self.user_id}")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False
    
    def make_image_request(self, request_id, provider=None):
        """Make a single image generation request"""
        start_time = time.time()
        
        payload = {
            "prompt": f"Stress test image #{request_id} - professional AI technology visualization with modern design elements",
            "style": "creative",
            "prefer_quality": False
        }
        
        if provider:
            payload["provider"] = provider
        
        try:
            response = requests.post(
                f"{self.base_url}/content/generate-image",
                json=payload,
                headers={"X-User-ID": self.user_id, "Content-Type": "application/json"},
                timeout=90  # Longer timeout for stress test
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            success = response.status_code == 200
            result = response.json() if response.content else {}
            
            return {
                "request_id": request_id,
                "success": success,
                "status_code": response.status_code,
                "duration": duration,
                "has_image": bool(result.get('image_base64')) if success else False,
                "provider": result.get('provider', 'N/A') if success else None,
                "model": result.get('model', 'N/A') if success else None,
                "justification": result.get('justification', 'N/A') if success else None,
                "error": result.get('error', response.text[:100]) if not success else None,
                "fallback_detected": 'fallback' in result.get('justification', '').lower() if success else False
            }
            
        except Exception as e:
            end_time = time.time()
            return {
                "request_id": request_id,
                "success": False,
                "status_code": 0,
                "duration": end_time - start_time,
                "has_image": False,
                "provider": None,
                "model": None,
                "justification": None,
                "error": str(e),
                "fallback_detected": False
            }
    
    def run_concurrent_stress_test(self, num_requests=10, max_workers=10):
        """Run high-concurrency stress test"""
        print(f"\n🔥 Running stress test with {num_requests} concurrent requests...")
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.make_image_request, i+1) for i in range(num_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Sort results by request_id
        results.sort(key=lambda x: x['request_id'])
        
        # Analyze results
        successful_requests = sum(1 for r in results if r['success'] and r['has_image'])
        failed_requests = num_requests - successful_requests
        fallback_count = sum(1 for r in results if r.get('fallback_detected', False))
        
        print(f"\n📊 Stress Test Results:")
        print(f"   Total Duration: {total_duration:.2f}s")
        print(f"   ✅ Successful: {successful_requests}/{num_requests} ({(successful_requests/num_requests)*100:.1f}%)")
        print(f"   ❌ Failed: {failed_requests}/{num_requests}")
        print(f"   🔄 Fallbacks Detected: {fallback_count}")
        
        # Provider analysis
        provider_counts = {}
        for result in results:
            if result['success'] and result['provider']:
                provider_counts[result['provider']] = provider_counts.get(result['provider'], 0) + 1
        
        if provider_counts:
            print(f"\n   📊 Provider Distribution:")
            for provider, count in provider_counts.items():
                percentage = (count / successful_requests) * 100 if successful_requests > 0 else 0
                print(f"      {provider}: {count}/{successful_requests} ({percentage:.1f}%)")
        
        # Duration analysis
        successful_durations = [r['duration'] for r in results if r['success']]
        if successful_durations:
            avg_duration = sum(successful_durations) / len(successful_durations)
            min_duration = min(successful_durations)
            max_duration = max(successful_durations)
            print(f"\n   ⏱️  Duration Analysis (successful requests):")
            print(f"      Average: {avg_duration:.2f}s")
            print(f"      Min: {min_duration:.2f}s")
            print(f"      Max: {max_duration:.2f}s")
        
        # Show failures
        failed_results = [r for r in results if not r['success']]
        if failed_results:
            print(f"\n   ❌ Failed Requests:")
            for result in failed_results[:5]:  # Show first 5 failures
                print(f"      Request #{result['request_id']}: {result['error'][:80]}...")
        
        # Show fallbacks
        fallback_results = [r for r in results if r.get('fallback_detected', False)]
        if fallback_results:
            print(f"\n   🔄 Fallback Details:")
            for result in fallback_results:
                print(f"      Request #{result['request_id']}: {result['justification'][:80]}...")
        
        return successful_requests, failed_requests, fallback_count, results
    
    def test_provider_specific_fallback(self):
        """Test fallback by forcing Gemini provider under stress"""
        print(f"\n🔍 Testing Gemini provider under stress (potential fallback scenario)...")
        
        # Make multiple rapid Gemini requests to potentially trigger rate limits
        gemini_results = []
        for i in range(5):
            print(f"   Making Gemini request #{i+1}...")
            result = self.make_image_request(f"gemini-{i+1}", provider="gemini")
            gemini_results.append(result)
            
            if result['success']:
                provider_used = result['provider']
                fallback = result['fallback_detected']
                print(f"      ✅ Success - Provider: {provider_used}, Fallback: {fallback}")
            else:
                print(f"      ❌ Failed - {result['error'][:50]}...")
            
            # Small delay between requests
            time.sleep(0.5)
        
        # Analyze Gemini results
        gemini_success = sum(1 for r in gemini_results if r['success'])
        gemini_fallbacks = sum(1 for r in gemini_results if r.get('fallback_detected', False))
        
        print(f"\n   📊 Gemini Stress Results:")
        print(f"      Success Rate: {gemini_success}/5 ({(gemini_success/5)*100:.1f}%)")
        print(f"      Fallbacks: {gemini_fallbacks}/5")
        
        return gemini_success, gemini_fallbacks, gemini_results

def main():
    print("🚀 Starting Image Generation Stress Test...")
    
    tester = ImageGenerationStressTest()
    
    if not tester.login():
        return False
    
    # Test 1: High concurrency stress test
    success_10, failed_10, fallback_10, results_10 = tester.run_concurrent_stress_test(10, 10)
    
    # Test 2: Even higher concurrency
    print(f"\n" + "="*60)
    success_15, failed_15, fallback_15, results_15 = tester.run_concurrent_stress_test(15, 15)
    
    # Test 3: Provider-specific fallback test
    print(f"\n" + "="*60)
    gemini_success, gemini_fallbacks, gemini_results = tester.test_provider_specific_fallback()
    
    # Overall assessment
    print(f"\n" + "="*80)
    print(f"STRESS TEST SUMMARY")
    print(f"="*80)
    
    total_requests = 10 + 15 + 5
    total_success = success_10 + success_15 + gemini_success
    total_fallbacks = fallback_10 + fallback_15 + gemini_fallbacks
    
    print(f"\n📊 Overall Results:")
    print(f"   Total Requests: {total_requests}")
    print(f"   Total Successful: {total_success} ({(total_success/total_requests)*100:.1f}%)")
    print(f"   Total Fallbacks: {total_fallbacks}")
    
    print(f"\n🔍 Retry Logic Assessment:")
    if total_success >= total_requests * 0.8:  # 80% success rate
        print(f"   ✅ EXCELLENT - Retry logic working effectively under stress")
    elif total_success >= total_requests * 0.6:  # 60% success rate
        print(f"   ⚠️  GOOD - Some issues under extreme load, but generally stable")
    else:
        print(f"   ❌ NEEDS IMPROVEMENT - Significant failures under stress")
    
    print(f"\n🔄 Fallback Mechanism Assessment:")
    if total_fallbacks > 0:
        print(f"   ✅ WORKING - Fallback mechanism triggered {total_fallbacks} times")
    else:
        print(f"   ℹ️  NOT TRIGGERED - Primary provider (Gemini) handled all requests successfully")
    
    return total_success >= total_requests * 0.7

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)