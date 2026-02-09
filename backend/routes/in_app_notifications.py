"""
In-App Notifications Routes
Handles user notifications for approval workflow, team updates, etc.

Security Update (ARCH-005 Phase 5.1b):
- Added @require_permission decorators for RBAC enforcement
"""

import os
import logging
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Header, Depends, Request
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db

# ARCH-005: Authorization decorator
from services.authorization_decorator import require_permission

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/in-app-notifications", tags=["in-app-notifications"])

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "contentry_db")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


# ==================== PYDANTIC MODELS ====================

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    message: str
    related_post_id: Optional[str] = None
    from_user_id: Optional[str] = None
    from_user_name: Optional[str] = None
    metadata: dict = {}
    read: bool
    created_at: str


# ==================== API ENDPOINTS ====================

@router.get("")
@require_permission("notifications.view")
async def get_notifications(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    limit: int = 50,
    unread_only: bool = False,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get user's notifications.
    Returns most recent notifications first.
    
    Security (ARCH-005): Requires notifications.view permission.
    """
    query = {"user_id": user_id}
    
    if unread_only:
        query["read"] = False
    
    notifications = await db_conn.notifications.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Enrich with sender info
    for notif in notifications:
        if notif.get("from_user_id"):
            sender = await db_conn.users.find_one(
                {"id": notif["from_user_id"]},
                {"_id": 0, "full_name": 1}
            )
            notif["from_user_name"] = sender.get("full_name", "Unknown") if sender else "Unknown"
    
    return {
        "notifications": notifications,
        "total": len(notifications)
    }


@router.get("/unread-count")
@require_permission("notifications.view")
async def get_unread_count(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get the count of unread notifications.
    
    Security (ARCH-005): Requires notifications.view permission.
    """
    count = await db_conn.notifications.count_documents({
        "user_id": user_id,
        "read": False
    })
    
    return {"unread_count": count}


@router.put("/{notification_id}/read")
@require_permission("notifications.manage")
async def mark_as_read(
    notification_id: str,
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Mark a specific notification as read.
    
    Security (ARCH-005): Requires notifications.manage permission.
    """
    result = await db_conn.notifications.update_one(
        {"id": notification_id, "user_id": user_id},
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}


@router.put("/read-all")
@require_permission("notifications.manage")
async def mark_all_as_read(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Mark all notifications as read.
    
    Security (ARCH-005): Requires notifications.manage permission.
    """
    now = datetime.now(timezone.utc).isoformat()
    
    result = await db_conn.notifications.update_many(
        {"user_id": user_id, "read": False},
        {"$set": {"read": True, "read_at": now}}
    )
    
    return {
        "message": "All notifications marked as read",
        "count": result.modified_count
    }


@router.delete("/{notification_id}")
@require_permission("notifications.manage")
async def delete_notification(
    notification_id: str,
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Delete a specific notification.
    
    Security (ARCH-005): Requires notifications.manage permission.
    """
    result = await db_conn.notifications.delete_one({
        "id": notification_id,
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification deleted"}


@router.delete("/clear-all")
@require_permission("notifications.manage")
async def clear_all_notifications(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Clear all notifications for the user.
    
    Security (ARCH-005): Requires notifications.manage permission.
    """
    result = await db_conn.notifications.delete_many({"user_id": user_id})
    
    return {
        "message": "All notifications cleared",
        "count": result.deleted_count
    }


# ==================== NOTIFICATION TYPE INFO ====================

@router.get("/types")
@require_permission("notifications.view")
async def get_notification_types(request: Request):
    """
    Get information about notification types.
    
    Security (ARCH-005): Requires notifications.view permission.
    """
    return {
        "types": {
            "approval_submitted": {
                "label": "Post Submitted",
                "description": "A team member submitted a post for approval",
                "icon": "FaFileAlt",
                "color": "orange"
            },
            "post_approved": {
                "label": "Post Approved",
                "description": "Your post has been approved",
                "icon": "FaCheckCircle",
                "color": "green"
            },
            "post_rejected": {
                "label": "Post Needs Revision",
                "description": "Your post requires changes",
                "icon": "FaExclamationTriangle",
                "color": "red"
            },
            "invitation_accepted": {
                "label": "Invitation Accepted",
                "description": "Someone accepted your team invitation",
                "icon": "FaUserPlus",
                "color": "blue"
            },
            "role_changed": {
                "label": "Role Updated",
                "description": "Your role has been changed",
                "icon": "FaUserCog",
                "color": "purple"
            },
            "post_published": {
                "label": "Post Published",
                "description": "Your post has been published",
                "icon": "FaRocket",
                "color": "green"
            },
            "post_scheduled": {
                "label": "Post Scheduled",
                "description": "Your post has been scheduled",
                "icon": "FaClock",
                "color": "blue"
            }
        }
    }
