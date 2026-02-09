#!/usr/bin/env python3
"""
Debug Background Job System
"""

import requests
import time
import json

def debug_job_system():
    base_url = "http://localhost:8001/api"
    user_id = "test-async-user"
    
    print("🔍 Debugging Background Job System...")
    
    # Test 1: Create a simple async content analysis job
    print("\n1. Creating async content analysis job...")
    
    url = f"{base_url}/content/analyze/async"
    payload = {
        "content": "Test content for debugging",
        "language": "en",
        "user_id": user_id
    }
    
    response = requests.post(url, json=payload)
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        data = response.json()
        job_id = data.get('job_id')
        
        if job_id:
            print(f"\n2. Polling job {job_id}...")
            
            # Poll a few times
            for i in range(5):
                time.sleep(2)
                
                # Check job status
                status_url = f"{base_url}/jobs/{job_id}"
                status_response = requests.get(status_url, params={"user_id": user_id})
                
                print(f"Poll {i+1}:")
                print(f"  Status code: {status_response.status_code}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"  Status: {status_data.get('status')}")
                    print(f"  Full response: {json.dumps(status_data, indent=2)}")
                    
                    if status_data.get('status') == 'completed':
                        print(f"\n3. Getting job result...")
                        
                        # Get result
                        result_url = f"{base_url}/jobs/{job_id}/result"
                        result_response = requests.get(result_url, params={"user_id": user_id})
                        
                        print(f"Result status code: {result_response.status_code}")
                        if result_response.status_code == 200:
                            result_data = result_response.json()
                            print(f"Result data: {json.dumps(result_data, indent=2)}")
                        else:
                            print(f"Result error: {result_response.text}")
                        break
                    elif status_data.get('status') == 'failed':
                        print(f"  Error: {status_data.get('error')}")
                        break
                else:
                    print(f"  Error: {status_response.text}")
    
    # Test 2: List all jobs
    print(f"\n4. Listing all jobs for user {user_id}...")
    
    jobs_url = f"{base_url}/jobs"
    jobs_response = requests.get(jobs_url, params={"user_id": user_id})
    
    print(f"Jobs list status: {jobs_response.status_code}")
    if jobs_response.status_code == 200:
        jobs_data = jobs_response.json()
        print(f"Jobs data: {json.dumps(jobs_data, indent=2)}")
    else:
        print(f"Jobs error: {jobs_response.text}")

if __name__ == "__main__":
    debug_job_system()