"""
Test Approval Workflow for Creator Role
Tests the fixes for:
1. Creator gets 'You must be logged in' error when submitting for approval
2. Creator should be able to schedule posts that require approval in Company Workspace
3. Creator should see all posts waiting for approval or approved in All Posts
"""

import pytest
import requests
import os
import json
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://admin-portal-278.preview.emergentagent.com')
if BASE_URL.endswith('/'):
    BASE_URL = BASE_URL.rstrip('/')

# Test credentials
CREATOR_EMAIL = "alex.martinez@techcorp-demo.com"
CREATOR_PASSWORD = "DemoCreator!123"
CREATOR_USER_ID = "alex-martinez"
ENTERPRISE_ID = "techcorp-international"


class TestApprovalWorkflow:
    """Test approval workflow for Creator role"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-User-ID": CREATOR_USER_ID
        })
    
    def test_01_creator_login(self):
        """Test 1: Verify Creator can login successfully"""
        response = self.session.post(f"{BASE_URL}/api/v1/auth/login", json={
            "email": CREATOR_EMAIL,
            "password": CREATOR_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert data.get("user", {}).get("role") == "creator"
        assert data.get("user", {}).get("enterprise_id") == ENTERPRISE_ID
        print(f"✓ Creator login successful: {data['user']['full_name']}")
    
    def test_02_create_post_no_auth_error(self):
        """Test 2: Creator can create post without 'You must be logged in' error"""
        response = self.session.post(f"{BASE_URL}/api/v1/posts", json={
            "title": "TEST_Approval_Workflow_Post",
            "content": "This is a test post to verify the approval workflow is working correctly.",
            "platforms": ["linkedin"],
            "status": "draft",
            "workspace_type": "enterprise",
            "enterprise_id": ENTERPRISE_ID
        })
        
        # Should NOT get 401 authentication error
        assert response.status_code != 401, f"Got authentication error: {response.text}"
        assert response.status_code == 200, f"Post creation failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert data.get("status") == "draft"
        self.post_id = data["id"]
        print(f"✓ Post created successfully: {self.post_id}")
        return data["id"]
    
    def test_03_submit_for_approval_no_auth_error(self):
        """Test 3: Creator can submit post for approval without 'You must be logged in' error"""
        # First create a post
        create_response = self.session.post(f"{BASE_URL}/api/v1/posts", json={
            "title": "TEST_Submit_For_Approval",
            "content": "Testing submission for approval workflow.",
            "platforms": ["linkedin"],
            "status": "draft",
            "workspace_type": "enterprise",
            "enterprise_id": ENTERPRISE_ID
        })
        assert create_response.status_code == 200
        post_id = create_response.json()["id"]
        
        # Submit for approval
        response = self.session.post(f"{BASE_URL}/api/v1/approval/submit/{post_id}")
        
        # Should NOT get 401 authentication error
        assert response.status_code != 401, f"Got authentication error: {response.text}"
        assert response.status_code == 200, f"Approval submission failed: {response.text}"
        
        data = response.json()
        assert data.get("status") == "pending_approval"
        assert data.get("message") == "Post submitted for approval"
        print(f"✓ Post submitted for approval: {post_id}")
        return post_id
    
    def test_04_verify_pending_approval_status(self):
        """Test 4: Verify post has 'pending_approval' status after submission"""
        # Create and submit a post
        create_response = self.session.post(f"{BASE_URL}/api/v1/posts", json={
            "title": "TEST_Verify_Pending_Status",
            "content": "Testing pending approval status verification.",
            "platforms": ["linkedin"],
            "status": "draft",
            "workspace_type": "enterprise",
            "enterprise_id": ENTERPRISE_ID
        })
        post_id = create_response.json()["id"]
        
        # Submit for approval
        self.session.post(f"{BASE_URL}/api/v1/approval/submit/{post_id}")
        
        # Get posts with pending_approval status
        response = self.session.get(f"{BASE_URL}/api/v1/posts?status=pending_approval")
        assert response.status_code == 200
        
        posts = response.json()
        post_ids = [p["id"] for p in posts]
        assert post_id in post_ids, f"Post {post_id} not found in pending_approval posts"
        
        # Verify the specific post status
        post = next((p for p in posts if p["id"] == post_id), None)
        assert post is not None
        assert post["status"] == "pending_approval"
        print(f"✓ Post status verified as 'pending_approval': {post_id}")
    
    def test_05_schedule_prompt_needs_approval(self):
        """Test 5: Schedule prompt in Company Workspace shows 'needs_approval' for Creator"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = self.session.post(f"{BASE_URL}/api/v1/scheduler/schedule-prompt", json={
            "prompt": "TEST_Create a LinkedIn post about our new product launch",
            "schedule_type": "once",
            "schedule_time": "10:00",
            "start_date": tomorrow,
            "platforms": ["linkedin"],
            "auto_post": True,
            "tone": "professional",
            "workspace_type": "enterprise",
            "enterprise_id": ENTERPRISE_ID
        })
        
        assert response.status_code == 200, f"Schedule prompt failed: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert data.get("needs_approval") == True, "needs_approval should be True for Creator in Company Workspace"
        
        scheduled_prompt = data.get("scheduled_prompt", {})
        assert scheduled_prompt.get("needs_approval") == True
        assert scheduled_prompt.get("workspace_type") == "enterprise"
        assert scheduled_prompt.get("enterprise_id") == ENTERPRISE_ID
        
        # Verify the note mentions approval
        note = data.get("note", "")
        assert "approval" in note.lower(), f"Note should mention approval: {note}"
        
        print(f"✓ Scheduled prompt correctly shows needs_approval=True")
        return scheduled_prompt.get("id")
    
    def test_06_all_posts_shows_pending_approval(self):
        """Test 6: All Posts page shows posts with 'pending_approval' status for Creator"""
        # Get all posts for the user
        response = self.session.get(f"{BASE_URL}/api/v1/posts")
        assert response.status_code == 200
        
        posts = response.json()
        
        # Check if there are any pending_approval posts
        pending_posts = [p for p in posts if p.get("status") == "pending_approval"]
        
        # We should have at least one pending_approval post from previous tests
        assert len(pending_posts) > 0, "No pending_approval posts found in All Posts"
        
        print(f"✓ All Posts shows {len(pending_posts)} posts with 'pending_approval' status")
    
    def test_07_user_permissions_shows_needs_approval(self):
        """Test 7: User permissions endpoint shows Creator needs approval"""
        response = self.session.get(f"{BASE_URL}/api/v1/approval/user-permissions")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("role") == "creator"
        assert data.get("permissions", {}).get("needs_approval") == True
        assert data.get("permissions", {}).get("can_publish_directly") == False
        
        print(f"✓ User permissions correctly show needs_approval=True for Creator")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_posts(self):
        """Clean up TEST_ prefixed posts"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "X-User-ID": CREATOR_USER_ID
        })
        
        # Get all posts
        response = session.get(f"{BASE_URL}/api/v1/posts")
        if response.status_code == 200:
            posts = response.json()
            test_posts = [p for p in posts if p.get("title", "").startswith("TEST_")]
            
            for post in test_posts:
                try:
                    session.delete(f"{BASE_URL}/api/v1/posts/{post['id']}")
                except:
                    pass
            
            print(f"✓ Cleaned up {len(test_posts)} test posts")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
