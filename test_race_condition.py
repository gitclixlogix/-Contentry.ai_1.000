#!/usr/bin/env python3
"""
Test for race conditions in image generation that could explain the bug.
"""

import requests
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def test_race_condition_detailed():
    """Test race conditions with detailed error reporting"""
    
    base_url = "http://localhost:8001/api"
    
    # Login first
    login_response = requests.post(f"{base_url}/auth/login", json={
        "email": "demo@test.com",
        "password": "password123"
    })
    user_id = login_response.json().get('user_id') or login_response.json().get('user', {}).get('id')
    
    print(f"🔍 Testing Race Conditions in Image Generation")
    print(f"User ID: {user_id}")
    
    def make_image_request(request_id, delay=0):
        """Make a single image generation request"""
        if delay > 0:
            time.sleep(delay)
            
        try:
            start_time = time.time()
            response = requests.post(f"{base_url}/content/generate-image",
                json={
                    "prompt": f"Test image {request_id} - professional business graphic",
                    "style": "simple",
                    "prefer_quality": False
                },
                headers={"X-User-ID": user_id, "Content-Type": "application/json"},
                timeout=30
            )
            end_time = time.time()
            
            result = {
                'id': request_id,
                'status_code': response.status_code,
                'duration': end_time - start_time,
                'success': False,
                'has_image': False,
                'error': None
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result['success'] = data.get('success', False)
                    result['has_image'] = bool(data.get('image_base64'))
                    result['provider'] = data.get('provider')
                    result['model'] = data.get('model')
                    if not result['success']:
                        result['error'] = data.get('error', 'Unknown error')
                except Exception as e:
                    result['error'] = f"JSON parse error: {str(e)}"
            else:
                result['error'] = f"HTTP {response.status_code}: {response.text[:200]}"
                
            return result
            
        except Exception as e:
            return {
                'id': request_id,
                'status_code': 0,
                'duration': 0,
                'success': False,
                'has_image': False,
                'error': f"Request exception: {str(e)}"
            }
    
    # Test 1: Sequential requests (should work)
    print(f"\n--- Test 1: Sequential Requests ---")
    sequential_results = []
    for i in range(3):
        result = make_image_request(f"seq_{i}")
        sequential_results.append(result)
        print(f"Request seq_{i}: Status={result['status_code']}, Success={result['success']}, Duration={result['duration']:.2f}s")
        time.sleep(1)  # 1 second delay between requests
    
    # Test 2: Concurrent requests (might fail)
    print(f"\n--- Test 2: Concurrent Requests ---")
    concurrent_results = []
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(make_image_request, f"conc_{i}") for i in range(3)]
        
        for future in as_completed(futures):
            result = future.result()
            concurrent_results.append(result)
    
    # Sort by ID for consistent output
    concurrent_results.sort(key=lambda x: x['id'])
    
    for result in concurrent_results:
        status = "✅" if result['success'] and result['has_image'] else "❌"
        print(f"{status} Request {result['id']}: Status={result['status_code']}, Success={result['success']}, Duration={result['duration']:.2f}s")
        if result['error']:
            print(f"   Error: {result['error']}")
    
    # Test 3: Rapid sequential requests (simulate user clicking quickly)
    print(f"\n--- Test 3: Rapid Sequential Requests (User Clicking Quickly) ---")
    rapid_results = []
    
    for i in range(3):
        result = make_image_request(f"rapid_{i}")
        rapid_results.append(result)
        print(f"Request rapid_{i}: Status={result['status_code']}, Success={result['success']}, Duration={result['duration']:.2f}s")
        if result['error']:
            print(f"   Error: {result['error']}")
        time.sleep(0.1)  # Very short delay (100ms) - simulates rapid clicking
    
    # Test 4: Test the exact scenario - content generation followed immediately by image generation
    print(f"\n--- Test 4: Content + Image Generation (Frontend Flow) ---")
    
    # First generate content
    content_start = time.time()
    content_response = requests.post(f"{base_url}/content/generate", json={
        "prompt": "Announce our new AI content moderation tool",
        "tone": "professional",
        "user_id": user_id,
        "platforms": ["facebook"],
        "language": "en",
        "hashtag_count": 3
    })
    content_end = time.time()
    
    print(f"Content generation: Status={content_response.status_code}, Duration={content_end - content_start:.2f}s")
    
    if content_response.status_code == 200:
        content_data = content_response.json()
        generated_content = content_data.get('generated_content', '')
        print(f"Generated content: {generated_content[:100]}...")
        
        # Immediately generate image (like frontend does)
        image_prompt = f"Create a professional social media image that visually represents this content: {generated_content[:300]}"
        
        image_start = time.time()
        image_result = make_image_request("content_flow", 0)
        image_end = time.time()
        
        status = "✅" if image_result['success'] and image_result['has_image'] else "❌"
        print(f"{status} Image generation: Status={image_result['status_code']}, Success={image_result['success']}, Duration={image_result['duration']:.2f}s")
        if image_result['error']:
            print(f"   Error: {image_result['error']}")
    
    # Analysis
    print(f"\n" + "="*60)
    print(f"RACE CONDITION ANALYSIS")
    print(f"="*60)
    
    sequential_success = sum(1 for r in sequential_results if r['success'] and r['has_image'])
    concurrent_success = sum(1 for r in concurrent_results if r['success'] and r['has_image'])
    rapid_success = sum(1 for r in rapid_results if r['success'] and r['has_image'])
    
    print(f"Sequential requests: {sequential_success}/3 successful")
    print(f"Concurrent requests: {concurrent_success}/3 successful")
    print(f"Rapid requests: {rapid_success}/3 successful")
    
    if sequential_success == 3 and concurrent_success < 3:
        print(f"\n🔍 RACE CONDITION DETECTED!")
        print(f"   - Sequential requests work fine")
        print(f"   - Concurrent requests fail")
        print(f"   - This explains why initial generation fails but regeneration works")
        print(f"   - Users click 'Generate' → fails due to race condition")
        print(f"   - Users click 'Regenerate' → works because it's a single request")
        
        return True
    elif rapid_success < 3:
        print(f"\n🔍 RAPID CLICKING ISSUE DETECTED!")
        print(f"   - Rapid successive requests fail")
        print(f"   - This could happen if users click the generate button multiple times")
        
        return True
    else:
        print(f"\n✅ No race condition detected in this test")
        return False

def test_resource_contention():
    """Test if there's resource contention in the image generation service"""
    
    base_url = "http://localhost:8001/api"
    
    # Login
    login_response = requests.post(f"{base_url}/auth/login", json={
        "email": "demo@test.com",
        "password": "password123"
    })
    user_id = login_response.json().get('user_id') or login_response.json().get('user', {}).get('id')
    
    print(f"\n🔍 Testing Resource Contention")
    
    # Test with different users (simulate multiple users using the system)
    def make_request_as_user(user_id, request_id):
        try:
            response = requests.post(f"{base_url}/content/generate-image",
                json={
                    "prompt": f"Test image for user {user_id} request {request_id}",
                    "style": "simple",
                    "prefer_quality": False
                },
                headers={"X-User-ID": user_id, "Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('success', False) and bool(data.get('image_base64'))
            return False
        except:
            return False
    
    # Simulate multiple users making requests simultaneously
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i in range(5):
            # Use the same user ID for all requests to test resource contention
            future = executor.submit(make_request_as_user, user_id, i)
            futures.append(future)
        
        results = [future.result() for future in as_completed(futures)]
    
    success_count = sum(results)
    print(f"Multi-user simulation: {success_count}/5 requests successful")
    
    if success_count < 5:
        print(f"⚠️  Resource contention detected - some requests failed")
        return True
    else:
        print(f"✅ No resource contention detected")
        return False

if __name__ == "__main__":
    race_condition_found = test_race_condition_detailed()
    resource_contention_found = test_resource_contention()
    
    print(f"\n" + "="*80)
    print(f"FINAL DIAGNOSIS")
    print(f"="*80)
    
    if race_condition_found or resource_contention_found:
        print(f"🔍 ROOT CAUSE IDENTIFIED:")
        
        if race_condition_found:
            print(f"   ✅ Race condition in concurrent image generation requests")
            print(f"   ✅ This explains the user's experience:")
            print(f"      - Initial generation fails (due to race condition)")
            print(f"      - Regeneration works (single request, no race condition)")
        
        if resource_contention_found:
            print(f"   ✅ Resource contention under load")
        
        print(f"\n💡 RECOMMENDED FIXES:")
        print(f"   1. Add request queuing/throttling in image generation service")
        print(f"   2. Implement proper concurrency control")
        print(f"   3. Add retry logic in frontend for failed image generation")
        print(f"   4. Consider using a job queue for image generation")
        
    else:
        print(f"❓ No clear race condition detected in testing")
        print(f"   The issue might be:")
        print(f"   - Environment-specific (production vs development)")
        print(f"   - Load-related (happens under higher load)")
        print(f"   - Network-related (user's connection)")
        print(f"   - Browser-specific (JavaScript errors)")