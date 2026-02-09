#!/usr/bin/env python3
"""
Image Generation Fix Test
Testing the image generation fix by directly calling the backend API as specified in review request.

Test Steps:
1. Create an image generation job using the async endpoint
2. Poll for job completion
3. Verify the result structure contains `images[0].data` with base64 data

Endpoint: POST http://localhost:8001/api/v1/ai/generate-image/async
Headers: Content-Type: application/json, X-User-ID: demo-user-id
Body: JSON with prompt, style, model, user_id

Expected Result:
- Job completes successfully
- Result contains `images` array with at least one entry
- Each image entry has `data` (base64 string), `type`, and `mime_type`

Why: The frontend fix expects `result.images[0].data` but we need to confirm the backend is returning this format correctly.
"""

import requests
import json
import time
import sys

class ImageGenerationTester:
    def __init__(self):
        self.base_url = "http://localhost:8001/api/v1"
        self.user_id = "demo-user-id"
        self.headers = {
            "Content-Type": "application/json",
            "X-User-ID": self.user_id
        }
        
    def test_image_generation_fix(self):
        """Test the image generation fix as specified in the review request"""
        print("=" * 80)
        print("IMAGE GENERATION FIX TEST")
        print("=" * 80)
        print("Testing the backend API to verify it returns images[0].data format")
        print("This confirms the frontend fix can properly access the image data")
        print("=" * 80)
        
        # Step 1: Create an image generation job using the async endpoint
        print("\n🔍 Step 1: Creating image generation job...")
        
        payload = {
            "prompt": "A professional infographic about sustainable shipping",
            "style": "creative",
            "model": "gpt-image-1",
            "user_id": self.user_id
        }
        
        print(f"📝 Endpoint: POST {self.base_url}/ai/generate-image/async")
        print(f"📝 Headers: {self.headers}")
        print(f"📝 Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(
                f"{self.base_url}/ai/generate-image/async",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code not in [200, 202]:
                print(f"❌ Failed to create image generation job")
                print(f"📊 Response: {response.text}")
                return False
                
            response_data = response.json()
            job_id = response_data.get("job_id")
            
            if not job_id:
                print(f"❌ No job_id in response")
                print(f"📊 Response: {response_data}")
                return False
                
            print(f"✅ Image generation job created successfully")
            print(f"📊 Job ID: {job_id}")
            
        except Exception as e:
            print(f"❌ Error creating image generation job: {str(e)}")
            return False
        
        # Step 2: Poll for job completion
        print(f"\n🔍 Step 2: Polling for job completion...")
        
        max_wait_time = 120  # 2 minutes for image generation
        check_interval = 5   # Check every 5 seconds
        elapsed_time = 0
        
        job_completed = False
        final_result = None
        
        while elapsed_time < max_wait_time:
            try:
                job_response = requests.get(
                    f"{self.base_url}/jobs/{job_id}",
                    headers={"X-User-ID": self.user_id},
                    timeout=10
                )
                
                if job_response.status_code != 200:
                    print(f"⚠️  Failed to get job status: {job_response.status_code}")
                    time.sleep(check_interval)
                    elapsed_time += check_interval
                    continue
                
                job_data = job_response.json()
                status = job_data.get("status", "unknown")
                progress = job_data.get("progress", {})
                
                print(f"📊 Job status after {elapsed_time}s: {status}")
                if progress:
                    current_step = progress.get("current_step", "")
                    percentage = progress.get("percentage", 0)
                    print(f"📊 Progress: {current_step} ({percentage}%)")
                
                if status == "completed":
                    job_completed = True
                    final_result = job_data.get("result", {})
                    print(f"✅ Job completed successfully!")
                    break
                elif status == "failed":
                    error_msg = job_data.get("error", "Unknown error")
                    print(f"❌ Job failed: {error_msg}")
                    return False
                elif status in ["running", "pending"]:
                    print(f"⏳ Job still {status}...")
                else:
                    print(f"⚠️  Unknown job status: {status}")
                
            except Exception as e:
                print(f"⚠️  Error checking job status: {str(e)}")
            
            time.sleep(check_interval)
            elapsed_time += check_interval
        
        if not job_completed:
            print(f"⚠️  Job did not complete within {max_wait_time} seconds")
            print(f"📊 Final status check...")
            
            # One final check
            try:
                job_response = requests.get(
                    f"{self.base_url}/jobs/{job_id}",
                    headers={"X-User-ID": self.user_id},
                    timeout=10
                )
                
                if job_response.status_code == 200:
                    job_data = job_response.json()
                    status = job_data.get("status", "unknown")
                    print(f"📊 Final job status: {status}")
                    
                    if status == "completed":
                        final_result = job_data.get("result", {})
                        job_completed = True
                        print(f"✅ Job completed on final check!")
                    else:
                        print(f"❌ Job did not complete: {status}")
                        return False
                else:
                    print(f"❌ Failed to get final job status: {job_response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error in final status check: {str(e)}")
                return False
        
        # Step 3: Verify the result structure contains `images[0].data` with base64 data
        print(f"\n🔍 Step 3: Verifying result structure...")
        
        if not final_result:
            print(f"❌ No result data available")
            return False
        
        print(f"📊 Result keys: {list(final_result.keys())}")
        
        # Check for images array
        images = final_result.get("images")
        if not images:
            print(f"❌ No 'images' array in result")
            print(f"📊 Result structure: {json.dumps(final_result, indent=2)[:500]}...")
            return False
        
        if not isinstance(images, list):
            print(f"❌ 'images' is not an array: {type(images)}")
            return False
        
        if len(images) == 0:
            print(f"❌ 'images' array is empty")
            return False
        
        print(f"✅ Found 'images' array with {len(images)} entries")
        
        # Check first image entry
        first_image = images[0]
        if not isinstance(first_image, dict):
            print(f"❌ First image entry is not a dict: {type(first_image)}")
            return False
        
        print(f"📊 First image keys: {list(first_image.keys())}")
        
        # Check for required fields
        required_fields = ["data", "type", "mime_type"]
        missing_fields = []
        
        for field in required_fields:
            if field not in first_image:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required fields in first image: {missing_fields}")
            print(f"📊 Available fields: {list(first_image.keys())}")
            return False
        
        # Check data field (base64 string)
        image_data = first_image.get("data")
        if not image_data:
            print(f"❌ 'data' field is empty")
            return False
        
        if not isinstance(image_data, str):
            print(f"❌ 'data' field is not a string: {type(image_data)}")
            return False
        
        # Basic base64 validation (should be a long string)
        if len(image_data) < 100:
            print(f"❌ 'data' field too short to be base64 image: {len(image_data)} chars")
            return False
        
        print(f"✅ Found 'data' field with {len(image_data)} characters")
        print(f"✅ Image type: {first_image.get('type')}")
        print(f"✅ MIME type: {first_image.get('mime_type')}")
        
        # Verify base64 format (basic check)
        try:
            import base64
            # Try to decode a small portion to verify it's valid base64
            base64.b64decode(image_data[:100])
            print(f"✅ Data appears to be valid base64 format")
        except Exception as e:
            print(f"⚠️  Data may not be valid base64: {str(e)}")
        
        print(f"\n" + "=" * 80)
        print(f"IMAGE GENERATION FIX TEST SUMMARY")
        print(f"=" * 80)
        print(f"✅ Job creation: SUCCESS")
        print(f"✅ Job completion: SUCCESS")
        print(f"✅ Result structure: SUCCESS")
        print(f"✅ images[0].data: PRESENT ({len(image_data)} chars)")
        print(f"✅ images[0].type: {first_image.get('type')}")
        print(f"✅ images[0].mime_type: {first_image.get('mime_type')}")
        print(f"")
        print(f"🎉 IMAGE GENERATION FIX VERIFICATION: PASSED")
        print(f"")
        print(f"The backend correctly returns the expected data structure:")
        print(f"- result.images[0].data contains base64 image data")
        print(f"- result.images[0].type contains image type")
        print(f"- result.images[0].mime_type contains MIME type")
        print(f"")
        print(f"The frontend fix should now be able to properly access:")
        print(f"const imageData = result?.images?.[0]?.data || result?.image_base64;")
        print(f"const mimeType = result?.images?.[0]?.mime_type || result?.mime_type || 'image/png';")
        print(f"=" * 80)
        
        return True

def main():
    """Main test execution"""
    tester = ImageGenerationTester()
    
    print("Starting Image Generation Fix Test...")
    print("This test verifies the backend API returns the correct data structure")
    print("that the frontend fix expects to receive.\n")
    
    success = tester.test_image_generation_fix()
    
    if success:
        print("\n🎉 All tests passed! Image generation fix is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Test failed! Image generation fix needs attention.")
        sys.exit(1)

if __name__ == "__main__":
    main()