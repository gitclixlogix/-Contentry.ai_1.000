#!/usr/bin/env python3
"""
Test the exact request format that the frontend sends to identify any mismatch.
"""

import requests
import json

def test_exact_frontend_request():
    """Test with the exact same request format as the frontend"""
    
    base_url = "http://localhost:8001/api"
    
    # Login first
    login_response = requests.post(f"{base_url}/auth/login", json={
        "email": "demo@test.com",
        "password": "password123"
    })
    
    user_data = login_response.json()
    user_id = user_data.get('user_id') or user_data.get('user', {}).get('id')
    print(f"User ID: {user_id}")
    
    # Test the exact request format from frontend (lines 298-304)
    print("\n🔍 Testing exact frontend request format...")
    
    # This is exactly what the frontend sends
    request_data = {
        "prompt": "Create a professional social media image that visually represents this content: Exciting news! We're launching our revolutionary AI-powered content moderation tool that helps businesses maintain brand safety across all social media platforms. This cutting-edge technology ensures your content aligns with your brand values while protecting your reputation. #AI #ContentModeration #BrandSafety",
        "style": "simple",  # Frontend default
        "prefer_quality": False  # Frontend default
    }
    
    headers = {
        "X-User-ID": user_id,
        "Content-Type": "application/json"
    }
    
    print(f"Request URL: {base_url}/content/generate-image")
    print(f"Request headers: {headers}")
    print(f"Request data: {json.dumps(request_data, indent=2)}")
    
    response = requests.post(
        f"{base_url}/content/generate-image",
        json=request_data,
        headers=headers
    )
    
    print(f"\nResponse status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        response_data = response.json()
        print(f"Response data keys: {list(response_data.keys())}")
        print(f"Success field: {response_data.get('success')}")
        print(f"Has image_base64: {'image_base64' in response_data}")
        print(f"Image base64 length: {len(response_data.get('image_base64', ''))}")
        print(f"Provider: {response_data.get('provider')}")
        print(f"Model: {response_data.get('model')}")
        
        # Check if this matches what frontend expects
        frontend_expected_fields = ['success', 'image_base64', 'mime_type', 'model', 'detected_style', 'justification', 'estimated_cost']
        missing_fields = [field for field in frontend_expected_fields if field not in response_data]
        
        if missing_fields:
            print(f"❌ Missing fields that frontend expects: {missing_fields}")
        else:
            print(f"✅ All expected fields present")
            
        # Test the exact condition from frontend (line 306)
        if response_data.get('success'):
            print(f"✅ Frontend condition 'imageResponse.data.success' would be TRUE")
        else:
            print(f"❌ Frontend condition 'imageResponse.data.success' would be FALSE")
            
    else:
        print(f"❌ Request failed: {response.text}")
    
    return response.status_code == 200 and response.json().get('success')

def test_different_styles():
    """Test different image styles to see if any fail"""
    
    base_url = "http://localhost:8001/api"
    
    # Login first
    login_response = requests.post(f"{base_url}/auth/login", json={
        "email": "demo@test.com", 
        "password": "password123"
    })
    user_id = login_response.json().get('user_id') or login_response.json().get('user', {}).get('id')
    
    styles = ['simple', 'creative', 'photorealistic', 'illustration']
    
    print(f"\n🔍 Testing different image styles...")
    
    for style in styles:
        print(f"\n--- Testing style: {style} ---")
        
        response = requests.post(f"{base_url}/content/generate-image", 
            json={
                "prompt": f"Create a {style} social media image about AI technology",
                "style": style,
                "prefer_quality": False
            },
            headers={"X-User-ID": user_id, "Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            success = data.get('success')
            has_image = bool(data.get('image_base64'))
            print(f"   Status: {response.status_code}, Success: {success}, Has Image: {has_image}")
            if success and has_image:
                print(f"   ✅ Style '{style}' works correctly")
            else:
                print(f"   ❌ Style '{style}' failed - Success: {success}, Has Image: {has_image}")
        else:
            print(f"   ❌ Style '{style}' failed with status {response.status_code}")

def test_error_scenarios():
    """Test scenarios that might cause the frontend to show 'generation failed'"""
    
    base_url = "http://localhost:8001/api"
    
    # Login first
    login_response = requests.post(f"{base_url}/auth/login", json={
        "email": "demo@test.com",
        "password": "password123"
    })
    user_id = login_response.json().get('user_id') or login_response.json().get('user', {}).get('id')
    
    print(f"\n🔍 Testing error scenarios...")
    
    # Test 1: Network timeout simulation (very long prompt)
    print(f"\n--- Test 1: Very complex prompt ---")
    complex_prompt = """Create a highly detailed, photorealistic social media image that shows a futuristic AI-powered content moderation dashboard with multiple screens displaying real-time analytics, sentiment analysis graphs, brand safety metrics, compliance scores, cultural sensitivity indicators, automated content filtering in action, with holographic displays showing global social media platforms like Facebook, Twitter, Instagram, LinkedIn, TikTok, with AI neural network visualizations, machine learning algorithms processing data streams, cybersecurity shields protecting brand reputation, diverse team of professionals monitoring the systems, modern office environment with glass walls, city skyline in background, dramatic lighting, professional photography style, ultra-high resolution, award-winning composition"""
    
    response = requests.post(f"{base_url}/content/generate-image",
        json={
            "prompt": complex_prompt,
            "style": "photorealistic", 
            "prefer_quality": True
        },
        headers={"X-User-ID": user_id, "Content-Type": "application/json"},
        timeout=30  # 30 second timeout
    )
    
    print(f"   Complex prompt result: Status {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Success: {data.get('success')}, Has Image: {bool(data.get('image_base64'))}")
    
    # Test 2: Rapid successive requests (race condition test)
    print(f"\n--- Test 2: Rapid successive requests ---")
    import threading
    import time
    
    results = []
    
    def make_request(i):
        try:
            resp = requests.post(f"{base_url}/content/generate-image",
                json={
                    "prompt": f"Simple test image {i}",
                    "style": "simple",
                    "prefer_quality": False
                },
                headers={"X-User-ID": user_id, "Content-Type": "application/json"},
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                results.append({
                    'id': i,
                    'success': data.get('success'),
                    'has_image': bool(data.get('image_base64'))
                })
            else:
                results.append({
                    'id': i,
                    'success': False,
                    'has_image': False,
                    'status': resp.status_code
                })
        except Exception as e:
            results.append({
                'id': i,
                'success': False,
                'has_image': False,
                'error': str(e)
            })
    
    # Start 3 concurrent requests
    threads = []
    for i in range(3):
        t = threading.Thread(target=make_request, args=(i,))
        threads.append(t)
        t.start()
    
    # Wait for all to complete
    for t in threads:
        t.join()
    
    print(f"   Concurrent requests results:")
    for result in results:
        status = "✅" if result.get('success') and result.get('has_image') else "❌"
        print(f"   {status} Request {result['id']}: Success={result.get('success')}, Has Image={result.get('has_image')}")

if __name__ == "__main__":
    print("🔍 Testing Frontend Exact Request Format")
    print("="*60)
    
    # Test exact frontend request
    success = test_exact_frontend_request()
    
    # Test different styles
    test_different_styles()
    
    # Test error scenarios
    test_error_scenarios()
    
    print(f"\n" + "="*60)
    print(f"SUMMARY")
    print(f"="*60)
    
    if success:
        print(f"✅ Frontend request format works correctly")
        print(f"   The issue may be:")
        print(f"   - Frontend JavaScript error handling")
        print(f"   - Browser network issues")
        print(f"   - Timing/race conditions in the UI")
        print(f"   - User-specific content or prompts")
    else:
        print(f"❌ Frontend request format has issues")
        print(f"   The backend may have problems with the exact request format")