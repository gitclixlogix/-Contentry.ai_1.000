"""
Roles Module - Shared Helpers
=============================
Shared helper functions and Pydantic models for roles management.
"""

import os
import logging
from typing import List, Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient

from services.permission_service import permission_service

logger = logging.getLogger(__name__)

# Database connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "contentry_db")


# ==================== PYDANTIC MODELS ====================

class CreateRoleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Role name")
    description: str = Field("", max_length=500, description="Role description")
    permissions: List[str] = Field(default_factory=list, description="List of permission keys")
    color: str = Field("#8B5CF6", description="Role color for UI display")
    icon: str = Field("user", description="Icon identifier")


class UpdateRoleRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: Optional[List[str]] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class AssignRoleRequest(BaseModel):
    user_id: str = Field(..., description="User ID to assign role to")
    valid_until: Optional[str] = Field(None, description="Optional expiry date (ISO format)")


class PermissionCheckRequest(BaseModel):
    permissions: List[str] = Field(..., description="List of permissions to check")


class DuplicateRoleRequest(BaseModel):
    new_name: str = Field(..., min_length=1, max_length=100, description="Name for the new role")
    new_description: Optional[str] = Field(None, max_length=500, description="Description for the new role")


# ==================== HELPER FUNCTIONS ====================

def get_db_connection():
    """Get database connection."""
    client = AsyncIOMotorClient(MONGO_URL)
    return client[DB_NAME]


async def get_user_and_enterprise(x_user_id: str):
    """Get user details and verify enterprise access."""
    db = get_db_connection()
    
    user = await db.users.find_one({"id": x_user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    enterprise_id = user.get("enterprise_id")
    if not enterprise_id:
        raise HTTPException(status_code=403, detail="User not part of an enterprise")
    
    return user, enterprise_id


async def check_user_permission(user_id: str, enterprise_id: str, permission: str):
    """Check if user has a specific permission, raise 403 if not."""
    has_permission = await permission_service.check_permission(user_id, enterprise_id, permission)
    
    # Fallback: check legacy role for admin access
    if not has_permission:
        db = get_db_connection()
        user = await db.users.find_one({"id": user_id}, {"role": 1, "enterprise_role": 1, "_id": 0})
        if user:
            role = user.get("enterprise_role") or user.get("role", "user")
            if role in ["admin", "enterprise_admin"]:
                has_permission = True
    
    if not has_permission:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "permission_denied",
                "missing_permission": permission,
                "message": "You don't have permission to perform this action"
            }
        )


async def check_admin_access(user: dict):
    """Check if user has admin role."""
    user_role = user.get("enterprise_role") or user.get("role", "user")
    if user_role not in ["admin", "enterprise_admin"]:
        raise HTTPException(status_code=403, detail="Only administrators can perform this action")
