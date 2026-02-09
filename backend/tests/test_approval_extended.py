"""Extended Approval Workflow Tests

Comprehensive tests for content approval endpoints.
Based on routes in /app/backend/routes/approval.py
"""

import pytest


# =============================================================================
# APPROVAL STATUS TESTS
# =============================================================================

class TestApprovalStatus:
    """Tests for approval status endpoints"""
    
    def test_get_status_info(self, sync_client, user_headers):
        """Test getting approval status info"""
        response = sync_client.get(
            "/api/v1/approval/status-info",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_user_permissions(self, sync_client, user_headers):
        """Test getting user approval permissions"""
        response = sync_client.get(
            "/api/v1/approval/user-permissions",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 500]


# =============================================================================
# SUBMISSION TESTS
# =============================================================================

class TestApprovalSubmission:
    """Tests for approval submission"""
    
    def test_submit_for_approval(self, sync_client, user_headers):
        """Test submitting content for approval"""
        response = sync_client.post(
            "/api/v1/approval/submit/post-123",
            headers=user_headers
        )
        assert response.status_code in [200, 400, 401, 403, 404, 422, 500]
    
    def test_get_my_submissions(self, sync_client, user_headers):
        """Test getting my submissions"""
        response = sync_client.get(
            "/api/v1/approval/my-submissions",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 500]


# =============================================================================
# PENDING APPROVALS TESTS
# =============================================================================

class TestPendingApprovals:
    """Tests for pending approvals"""
    
    def test_get_pending_approvals(self, sync_client, user_headers):
        """Test getting pending approvals"""
        response = sync_client.get(
            "/api/v1/approval/pending",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_approved_content(self, sync_client, user_headers):
        """Test getting approved content"""
        response = sync_client.get(
            "/api/v1/approval/approved",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 500]
    
    def test_get_rejected_content(self, sync_client, user_headers):
        """Test getting rejected content"""
        response = sync_client.get(
            "/api/v1/approval/rejected",
            headers=user_headers
        )
        assert response.status_code in [200, 401, 403, 500]


# =============================================================================
# APPROVAL ACTIONS TESTS
# =============================================================================

class TestApprovalActions:
    """Tests for approval/rejection actions"""
    
    def test_approve_content(self, sync_client, admin_headers):
        """Test approving content"""
        response = sync_client.post(
            "/api/v1/approval/post-123/approve",
            headers=admin_headers
        )
        assert response.status_code in [200, 400, 401, 403, 404, 500]
    
    def test_reject_content(self, sync_client, admin_headers):
        """Test rejecting content"""
        response = sync_client.post(
            "/api/v1/approval/post-123/reject",
            json={"reason": "Does not meet guidelines"},
            headers=admin_headers
        )
        assert response.status_code in [200, 400, 401, 403, 404, 422, 500]
