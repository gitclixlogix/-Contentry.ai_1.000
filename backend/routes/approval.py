"""
Content Approval Workflow Routes
Handles post submission, approval, rejection, and status management.

RBAC Protected: Phase 5.1b Week 6
All endpoints require appropriate content.* or approval.* permissions
"""

import os
import logging
from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Header, Depends, Request
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db
# Import RBAC decorator
from services.authorization_decorator import require_permission
# Import email service for notifications
from email_service import send_approval_request_email, send_approval_result_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/approval", tags=["content-approval"])

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "contentry_db")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Content Status Constants
class ContentStatus:
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"

# User Roles
class UserRole:
    USER = "user"  # Legacy - full access (existing users)
    CREATOR = "creator"  # Can create, submit for approval
    MANAGER = "manager"  # Can approve, reject, publish
    ADMIN = "admin"  # Full access
    ENTERPRISE_ADMIN = "enterprise_admin"  # Enterprise admin - full access

# Roles that can approve content
APPROVER_ROLES = [UserRole.MANAGER, UserRole.ADMIN, UserRole.USER, UserRole.ENTERPRISE_ADMIN]

# Roles that need approval
NEEDS_APPROVAL_ROLES = [UserRole.CREATOR]


# ==================== PYDANTIC MODELS ====================

class SubmitForApprovalRequest(BaseModel):
    post_id: str


class ApprovalActionRequest(BaseModel):
    comment: Optional[str] = None


class RejectionRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=1000, description="Reason for rejection")


# ==================== HELPER FUNCTIONS ====================

async def get_user_role(user_id: str) -> str:
    """Get the role of a user."""
    user = await db.users.find_one({"id": user_id}, {"role": 1, "enterprise_role": 1})
    if not user:
        return UserRole.USER
    # Enterprise role takes precedence if set
    return user.get("enterprise_role") or user.get("role", UserRole.USER)


async def can_approve(user_id: str) -> bool:
    """Check if user can approve content."""
    role = await get_user_role(user_id)
    return role in APPROVER_ROLES


async def needs_approval(user_id: str) -> bool:
    """Check if user's content needs approval."""
    role = await get_user_role(user_id)
    return role in NEEDS_APPROVAL_ROLES


async def get_team_managers(user_id: str, db_conn: AsyncIOMotorDatabase = Depends(get_db)) -> List[Dict]:
    """
    Get the designated manager(s) for approval workflow.
    
    Priority:
    1. If user has a designated manager (reports_to), return only that manager
    2. Otherwise, fall back to all managers in the enterprise
    """
    user = await db_conn.users.find_one(
        {"id": user_id}, 
        {"enterprise_id": 1, "reports_to": 1}
    )
    
    if not user:
        return []
    
    # Check if user has a designated manager
    if user.get("reports_to"):
        manager = await db_conn.users.find_one(
            {"id": user["reports_to"]},
            {"_id": 0, "id": 1, "full_name": 1, "email": 1}
        )
        if manager:
            logger.info(f"Routing approval to designated manager: {manager.get('full_name')}")
            return [manager]
    
    # Fall back to all managers in the enterprise
    if not user.get("enterprise_id"):
        # If no enterprise, get all managers/admins
        managers = await db_conn.users.find(
            {"$or": [
                {"role": {"$in": [UserRole.MANAGER, UserRole.ADMIN]}},
                {"enterprise_role": {"$in": [UserRole.MANAGER, UserRole.ADMIN]}}
            ]},
            {"_id": 0, "id": 1, "full_name": 1, "email": 1}
        ).to_list(100)
    else:
        # Get managers in the same enterprise
        managers = await db_conn.users.find(
            {
                "enterprise_id": user["enterprise_id"],
                "$or": [
                    {"role": {"$in": [UserRole.MANAGER, UserRole.ADMIN]}},
                    {"enterprise_role": {"$in": [UserRole.MANAGER, UserRole.ADMIN]}}
                ]
            },
            {"_id": 0, "id": 1, "full_name": 1, "email": 1}
        ).to_list(100)
    
    return managers


async def create_notification(
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    related_post_id: Optional[str] = None,
    from_user_id: Optional[str] = None,
    metadata: Optional[Dict] = None
,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create an in-app notification."""
    notification = {
        "id": str(uuid4()),
        "user_id": user_id,
        "type": notification_type,
        "title": title,
        "message": message,
        "related_post_id": related_post_id,
        "from_user_id": from_user_id,
        "metadata": metadata or {},
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db_conn.notifications.insert_one(notification)
    logger.info(f"Created notification for user {user_id}: {notification_type}")
    return notification


# ==================== API ENDPOINTS ====================

@router.get("/status-info")
@require_permission("settings.view")
async def get_status_info(request: Request):
    """Get information about content statuses and roles."""
    return {
        "statuses": {
            "draft": {"label": "Draft", "color": "gray", "description": "Content being worked on"},
            "pending_approval": {"label": "Pending Approval", "color": "orange", "description": "Awaiting manager review"},
            "approved": {"label": "Approved", "color": "green", "description": "Ready to schedule or publish"},
            "rejected": {"label": "Needs Revision", "color": "red", "description": "Returned with feedback"},
            "scheduled": {"label": "Scheduled", "color": "blue", "description": "Scheduled for publication"},
            "published": {"label": "Published", "color": "purple", "description": "Published to social media"}
        },
        "roles": {
            "user": {"label": "User", "can_publish": True, "needs_approval": False},
            "creator": {"label": "Creator", "can_publish": False, "needs_approval": True},
            "manager": {"label": "Manager", "can_publish": True, "needs_approval": False, "can_approve": True},
            "admin": {"label": "Admin", "can_publish": True, "needs_approval": False, "can_approve": True}
        }
    }


@router.get("/user-permissions")
@require_permission("settings.view")
async def get_user_permissions(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID")
):
    """Get the current user's role and permissions."""
    role = await get_user_role(user_id)
    can_approve_content = await can_approve(user_id)
    requires_approval = await needs_approval(user_id)
    
    return {
        "user_id": user_id,
        "role": role,
        "permissions": {
            "can_publish_directly": not requires_approval,
            "needs_approval": requires_approval,
            "can_approve_others": can_approve_content,
            "can_reject_others": can_approve_content,
            "can_view_pending": can_approve_content
        }
    }


@router.post("/submit/{post_id}")
@require_permission("content.edit_own")
async def submit_for_approval(
    request: Request,
    post_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Submit a post for approval.
    Changes status from DRAFT to PENDING_APPROVAL.
    """
    # Get the post
    post = await db_conn.posts.find_one({"id": post_id, "user_id": user_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    current_status = post.get("status", ContentStatus.DRAFT)
    
    # Can only submit drafts or rejected posts
    if current_status not in [ContentStatus.DRAFT, ContentStatus.REJECTED]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot submit post with status '{current_status}'. Only drafts or rejected posts can be submitted."
        )
    
    # Update post status
    now = datetime.now(timezone.utc).isoformat()
    await db_conn.posts.update_one(
        {"id": post_id},
        {"$set": {
            "status": ContentStatus.PENDING_APPROVAL,
            "submitted_at": now,
            "submitted_by": user_id,
            "updated_at": now,
            "rejection_reason": None,  # Clear any previous rejection
            "rejected_by": None,
            "rejected_at": None
        }}
    )
    
    # Get submitter info
    submitter = await db_conn.users.find_one({"id": user_id}, {"full_name": 1, "email": 1})
    submitter_name = submitter.get("full_name", "A team member") if submitter else "A team member"
    
    # Notify all managers (via in-app notifications and email)
    managers = await get_team_managers(user_id, db_conn)
    post_title = post.get("title", post.get("content", "")[:50] + "...")
    post_content = post.get("content", "")
    
    for manager in managers:
        # In-app notification
        await create_notification(
            user_id=manager["id"],
            notification_type="approval_submitted",
            title="New Post Awaiting Approval",
            message=f"{submitter_name} has submitted a post for your review: \"{post_title}\"",
            related_post_id=post_id,
            from_user_id=user_id,
            metadata={"post_title": post_title, "submitter_name": submitter_name},
            db_conn=db_conn
        )
        
        # Email notification to manager
        try:
            approval_link = f"https://admin-portal-278.preview.emergentagent.com/contentry/content-moderation?tab=approvals&post={post_id}"
            await send_approval_request_email(
                manager_email=manager.get("email", ""),
                manager_name=manager.get("full_name", "Manager"),
                submitter_name=submitter_name,
                post_title=post_title,
                post_content=post_content,
                approval_link=approval_link
            )
            logger.info(f"Approval request email sent to {manager.get('email')}")
        except Exception as email_error:
            logger.warning(f"Failed to send approval email to {manager.get('email')}: {email_error}")
    
    logger.info(f"Post {post_id} submitted for approval by user {user_id}")
    
    return {
        "message": "Post submitted for approval",
        "post_id": post_id,
        "status": ContentStatus.PENDING_APPROVAL,
        "notified_managers": len(managers)
    }


@router.get("/pending")
@require_permission("content.approve")
async def get_pending_approvals(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get all posts pending approval.
    Only accessible by managers/admins.
    """
    if not await can_approve(user_id):
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to view pending approvals"
        )
    
    # Get user's enterprise to filter by team
    user = await db_conn.users.find_one({"id": user_id}, {"enterprise_id": 1})
    
    # Build query
    query = {"status": ContentStatus.PENDING_APPROVAL}
    
    # If user is in an enterprise, only show posts from team members
    if user and user.get("enterprise_id"):
        team_members = await db_conn.users.find(
            {"enterprise_id": user["enterprise_id"]},
            {"id": 1}
        ).to_list(1000)
        team_member_ids = [m["id"] for m in team_members]
        query["user_id"] = {"$in": team_member_ids}
    
    # Get pending posts
    posts = await db_conn.posts.find(query, {"_id": 0}).sort("submitted_at", -1).to_list(100)
    
    # Enrich with submitter info
    for post in posts:
        submitter = await db_conn.users.find_one(
            {"id": post.get("user_id")},
            {"_id": 0, "full_name": 1, "email": 1}
        )
        post["submitter"] = submitter or {"full_name": "Unknown", "email": ""}
    
    return {
        "posts": posts,
        "total": len(posts)
    }


@router.get("/approved")
@require_permission("content.approve")
async def get_approved_posts(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get all approved posts ready to be scheduled/published.
    Accessible by managers/admins.
    """
    if not await can_approve(user_id):
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to view approved posts"
        )
    
    posts = await db_conn.posts.find(
        {"status": ContentStatus.APPROVED},
        {"_id": 0}
    ).sort("approved_at", -1).to_list(100)
    
    # Enrich with creator info
    for post in posts:
        creator = await db_conn.users.find_one(
            {"id": post.get("user_id")},
            {"_id": 0, "full_name": 1, "email": 1}
        )
        post["creator"] = creator or {"full_name": "Unknown", "email": ""}
    
    return {
        "posts": posts,
        "total": len(posts)
    }


@router.post("/{post_id}/approve")
@require_permission("content.approve")
async def approve_post(
    request: Request,
    post_id: str,
    approval_request: ApprovalActionRequest = None,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Approve a post.
    Changes status from PENDING_APPROVAL to APPROVED.
    """
    if not await can_approve(user_id):
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to approve posts"
        )
    
    # Get the post
    post = await db_conn.posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.get("status") != ContentStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=400, 
            detail="Only posts with 'pending_approval' status can be approved"
        )
    
    # Get approver info
    approver = await db_conn.users.find_one({"id": user_id}, {"full_name": 1})
    approver_name = approver.get("full_name", "A manager") if approver else "A manager"
    
    # Update post status
    now = datetime.now(timezone.utc).isoformat()
    await db_conn.posts.update_one(
        {"id": post_id},
        {"$set": {
            "status": ContentStatus.APPROVED,
            "approved_at": now,
            "approved_by": user_id,
            "approval_comment": approval_request.comment if approval_request else None,
            "updated_at": now
        }}
    )
    
    # Notify the creator (in-app)
    post_title = post.get("title", post.get("content", "")[:50] + "...")
    
    await create_notification(
        user_id=post["user_id"],
        notification_type="post_approved",
        title="Post Approved!",
        message=f"{approver_name} has approved your post: \"{post_title}\"",
        related_post_id=post_id,
        from_user_id=user_id,
        metadata={"post_title": post_title, "approver_name": approver_name}
    )
    
    # Email notification to creator
    try:
        creator = await db_conn.users.find_one({"id": post["user_id"]}, {"_id": 0, "email": 1, "full_name": 1})
        if creator and creator.get("email"):
            await send_approval_result_email(
                creator_email=creator["email"],
                creator_name=creator.get("full_name", "User"),
                post_title=post_title,
                approved=True,
                reviewer_name=approver_name,
                feedback=approval_request.comment if approval_request else None
            )
            logger.info(f"Approval email sent to creator {creator['email']}")
    except Exception as email_error:
        logger.warning(f"Failed to send approval email: {email_error}")
    
    logger.info(f"Post {post_id} approved by user {user_id}")
    
    return {
        "message": "Post approved successfully",
        "post_id": post_id,
        "status": ContentStatus.APPROVED
    }


@router.post("/{post_id}/reject")
@require_permission("content.approve")
async def reject_post(
    request: Request,
    post_id: str,
    rejection_request: RejectionRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Reject a post with a reason.
    Changes status from PENDING_APPROVAL to REJECTED.
    """
    if not await can_approve(user_id):
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to reject posts"
        )
    
    # Get the post
    post = await db_conn.posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.get("status") != ContentStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=400, 
            detail="Only posts with 'pending_approval' status can be rejected"
        )
    
    # Get rejector info
    rejector = await db_conn.users.find_one({"id": user_id}, {"full_name": 1})
    rejector_name = rejector.get("full_name", "A manager") if rejector else "A manager"
    
    # Update post status
    now = datetime.now(timezone.utc).isoformat()
    await db_conn.posts.update_one(
        {"id": post_id},
        {"$set": {
            "status": ContentStatus.REJECTED,
            "rejected_at": now,
            "rejected_by": user_id,
            "rejection_reason": rejection_request.reason,
            "updated_at": now
        }}
    )
    
    # Notify the creator (in-app)
    post_title = post.get("title", post.get("content", "")[:50] + "...")
    
    await create_notification(
        user_id=post["user_id"],
        notification_type="post_rejected",
        title="Post Needs Revision",
        message=f"{rejector_name} has requested changes for your post: \"{post_title}\"",
        related_post_id=post_id,
        from_user_id=user_id,
        metadata={
            "post_title": post_title,
            "rejector_name": rejector_name,
            "rejection_reason": rejection_request.reason
        }
    )
    
    # Email notification to creator
    try:
        creator = await db_conn.users.find_one({"id": post["user_id"]}, {"_id": 0, "email": 1, "full_name": 1})
        if creator and creator.get("email"):
            await send_approval_result_email(
                creator_email=creator["email"],
                creator_name=creator.get("full_name", "User"),
                post_title=post_title,
                approved=False,
                reviewer_name=rejector_name,
                rejection_reason=rejection_request.reason
            )
            logger.info(f"Rejection email sent to creator {creator['email']}")
    except Exception as email_error:
        logger.warning(f"Failed to send rejection email: {email_error}")
    
    logger.info(f"Post {post_id} rejected by user {user_id}. Reason: {rejection_request.reason}")
    
    return {
        "message": "Post rejected and sent back to creator",
        "post_id": post_id,
        "status": ContentStatus.REJECTED,
        "rejection_reason": rejection_request.reason
    }


@router.get("/rejected")
@require_permission("content.view_own")
async def get_rejected_posts(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get posts that have been rejected for the current user.
    Shows posts that need revision.
    """
    posts = await db_conn.posts.find(
        {
            "user_id": user_id,
            "status": ContentStatus.REJECTED
        },
        {"_id": 0}
    ).sort("rejected_at", -1).to_list(100)
    
    # Enrich with rejector info
    for post in posts:
        if post.get("rejected_by"):
            rejector = await db_conn.users.find_one(
                {"id": post["rejected_by"]},
                {"_id": 0, "full_name": 1}
            )
            post["rejector"] = rejector or {"full_name": "Unknown"}
    
    return {
        "posts": posts,
        "total": len(posts)
    }


@router.get("/my-submissions")
@require_permission("content.view_own")
async def get_my_submissions(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    status: Optional[str] = None,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get the current user's submitted posts with their statuses.
    """
    query = {"user_id": user_id}
    
    if status:
        query["status"] = status
    else:
        # Exclude drafts by default - show only submitted/processed posts
        query["status"] = {"$in": [
            ContentStatus.PENDING_APPROVAL,
            ContentStatus.APPROVED,
            ContentStatus.REJECTED,
            ContentStatus.SCHEDULED,
            ContentStatus.PUBLISHED
        ]}
    
    posts = await db_conn.posts.find(query, {"_id": 0}).sort("updated_at", -1).to_list(100)
    
    return {
        "posts": posts,
        "total": len(posts)
    }
