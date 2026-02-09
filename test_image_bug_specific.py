#!/usr/bin/env python3
"""
Specific test to reproduce the image generation bug reported by user.
This test simulates the exact frontend flow: content generation followed by image generation.
"""

import requests
import json
import time

def test_frontend_flow():
    """Test the exact flow that the frontend uses"""
    
    base_url = "http://localhost:8001/api"
    
    # Step 1: Login
    print("🔍 Step 1: Login...")
    login_response = requests.post(f"{base_url}/auth/login", json={
        "email": "demo@test.com",
        "password": "password123"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    user_data = login_response.json()
    user_id = user_data.get('user_id') or user_data.get('user', {}).get('id')
    print(f"✅ Login successful - User ID: {user_id}")
    
    # Step 2: Generate content first (like frontend does)
    print("\n🔍 Step 2: Generate content first...")
    content_response = requests.post(f"{base_url}/content/generate", json={
        "prompt": "Announce our new AI-powered content moderation tool",
        "tone": "professional",
        "user_id": user_id,
        "platforms": ["facebook", "twitter"],
        "language": "en",
        "hashtag_count": 3
    })
    
    if content_response.status_code != 200:
        print(f"❌ Content generation failed: {content_response.status_code}")
        print(f"Response: {content_response.text}")
        return False
    
    content_data = content_response.json()
    generated_content = content_data.get('generated_content', '')
    print(f"✅ Content generated: {generated_content[:100]}...")
    
    # Step 3: Generate image based on the generated content (like frontend does)
    print("\n🔍 Step 3: Generate image based on generated content...")
    
    # This is the exact same logic as the frontend (line 297-298)
    image_prompt = f"Create a professional social media image that visually represents this content: {generated_content[:300]}"
    
    image_response = requests.post(f"{base_url}/content/generate-image", 
        json={
            "prompt": image_prompt,
            "style": "simple",  # Frontend uses 'simple' as default
            "prefer_quality": False
        },
        headers={"X-User-ID": user_id}
    )
    
    print(f"Image generation response status: {image_response.status_code}")
    
    if image_response.status_code != 200:
        print(f"❌ Image generation failed: {image_response.status_code}")
        print(f"Response: {image_response.text}")
        return False
    
    image_data = image_response.json()
    
    if not image_data.get('success'):
        print(f"❌ Image generation not successful: {image_data}")
        return False
    
    if not image_data.get('image_base64'):
        print(f"❌ No image data returned: {image_data}")
        return False
    
    print(f"✅ Image generated successfully!")
    print(f"   Provider: {image_data.get('provider')}")
    print(f"   Model: {image_data.get('model')}")
    print(f"   Style: {image_data.get('detected_style')}")
    print(f"   Image size: {len(image_data.get('image_base64', ''))} characters")
    
    # Step 4: Test the regeneration flow (what works for users)
    print("\n🔍 Step 4: Test image regeneration (what users say works)...")
    
    regen_response = requests.post(f"{base_url}/content/regenerate-image",
        json={
            "original_prompt": image_prompt,
            "feedback": None,
            "style": "simple",
            "prefer_quality": True
        },
        headers={"X-User-ID": user_id}
    )
    
    if regen_response.status_code != 200:
        print(f"❌ Image regeneration failed: {regen_response.status_code}")
        print(f"Response: {regen_response.text}")
        return False
    
    regen_data = regen_response.json()
    
    if regen_data.get('success') and regen_data.get('image_base64'):
        print(f"✅ Image regeneration successful!")
        print(f"   Provider: {regen_data.get('provider')}")
        print(f"   Model: {regen_data.get('model')}")
    else:
        print(f"❌ Image regeneration failed: {regen_data}")
        return False
    
    return True

def test_multiple_attempts():
    """Test multiple attempts to see if there's an intermittent issue"""
    
    print("\n" + "="*60)
    print("TESTING MULTIPLE ATTEMPTS FOR INTERMITTENT ISSUES")
    print("="*60)
    
    success_count = 0
    total_attempts = 5
    
    for i in range(total_attempts):
        print(f"\n--- Attempt {i+1}/{total_attempts} ---")
        
        if test_frontend_flow():
            success_count += 1
            print(f"✅ Attempt {i+1}: SUCCESS")
        else:
            print(f"❌ Attempt {i+1}: FAILED")
        
        # Small delay between attempts
        time.sleep(2)
    
    print(f"\n📊 Results: {success_count}/{total_attempts} attempts successful")
    
    if success_count == total_attempts:
        print("✅ All attempts successful - no intermittent issues detected")
        return True
    elif success_count > 0:
        print("⚠️  Intermittent issues detected - some attempts failed")
        return False
    else:
        print("❌ All attempts failed - consistent issue")
        return False

def test_error_conditions():
    """Test various error conditions that might cause the issue"""
    
    print("\n" + "="*60)
    print("TESTING ERROR CONDITIONS")
    print("="*60)
    
    base_url = "http://localhost:8001/api"
    
    # Login first
    login_response = requests.post(f"{base_url}/auth/login", json={
        "email": "demo@test.com",
        "password": "password123"
    })
    user_id = login_response.json().get('user_id') or login_response.json().get('user', {}).get('id')
    
    # Test 1: Empty prompt
    print("\n🔍 Test 1: Empty image prompt...")
    response = requests.post(f"{base_url}/content/generate-image",
        json={
            "prompt": "",
            "style": "simple",
            "prefer_quality": False
        },
        headers={"X-User-ID": user_id}
    )
    print(f"Empty prompt response: {response.status_code} - {response.text[:100]}")
    
    # Test 2: Invalid style
    print("\n🔍 Test 2: Invalid style...")
    response = requests.post(f"{base_url}/content/generate-image",
        json={
            "prompt": "Test image",
            "style": "invalid_style",
            "prefer_quality": False
        },
        headers={"X-User-ID": user_id}
    )
    print(f"Invalid style response: {response.status_code} - {response.text[:100]}")
    
    # Test 3: Missing user ID
    print("\n🔍 Test 3: Missing user ID...")
    response = requests.post(f"{base_url}/content/generate-image",
        json={
            "prompt": "Test image",
            "style": "simple",
            "prefer_quality": False
        }
    )
    print(f"Missing user ID response: {response.status_code} - {response.text[:100]}")
    
    # Test 4: Very long prompt
    print("\n🔍 Test 4: Very long prompt...")
    long_prompt = "Create an image " * 100  # Very long prompt
    response = requests.post(f"{base_url}/content/generate-image",
        json={
            "prompt": long_prompt,
            "style": "simple",
            "prefer_quality": False
        },
        headers={"X-User-ID": user_id}
    )
    print(f"Long prompt response: {response.status_code} - Success: {response.json().get('success') if response.status_code == 200 else 'N/A'}")

if __name__ == "__main__":
    print("🚀 Testing Image Generation Bug - Frontend Flow Simulation")
    print("="*80)
    
    # Test the exact frontend flow
    print("Testing exact frontend flow...")
    frontend_success = test_frontend_flow()
    
    # Test multiple attempts for intermittent issues
    multiple_success = test_multiple_attempts()
    
    # Test error conditions
    test_error_conditions()
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL ANALYSIS")
    print("="*80)
    
    if frontend_success and multiple_success:
        print("✅ CONCLUSION: Image generation is working correctly")
        print("   The reported bug may be:")
        print("   - A frontend UI issue (not showing generated images)")
        print("   - A network/timeout issue on the user's end")
        print("   - A browser-specific issue")
        print("   - An issue with specific prompts or content")
    elif frontend_success and not multiple_success:
        print("⚠️  CONCLUSION: Intermittent image generation issues detected")
        print("   The bug may be related to:")
        print("   - Race conditions or timing issues")
        print("   - Resource limitations under load")
        print("   - External API rate limiting")
    else:
        print("❌ CONCLUSION: Consistent image generation failure")
        print("   The bug is likely in:")
        print("   - Backend image generation service")
        print("   - API configuration or dependencies")
        print("   - Authentication or authorization issues")