"""
Role-Based Access Control (RBAC) for Enterprise Features
Handles permissions for manager, employee, and admin roles

Migration Status: PHASE 2 - Using Depends(get_db) dependency injection pattern
"""

from typing import List, Optional, Set
from fastapi import HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

# Import database dependency injection
from services.database import get_db

logger = logging.getLogger(__name__)

# =============================================================================
# BACKWARD COMPATIBILITY LAYER (DEPRECATED)
# =============================================================================
# The following global db and set_db() pattern is deprecated.
# It remains for backward compatibility during migration.
# New code should use: db: AsyncIOMotorDatabase = Depends(get_db)

db = None


# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    """Set database instance"""
    global db
    db = database


# Role Definitions
ROLES = {
    'admin': {
        'permissions': [
            'view_all_analytics',
            'manage_users',
            'manage_roles',
            'manage_enterprise',
            'view_team_analytics',
            'manage_policies'
        ]
    },
    'manager': {
        'permissions': [
            'view_team_analytics',
            'view_team_posts',
            'manage_team_content',
            'view_subordinates'
        ]
    },
    'employee': {
        'permissions': [
            'view_own_analytics',
            'create_content',
            'view_own_posts'
        ]
    }
}


async def get_user_roles(user_id: str) -> List[str]:
    """Get all roles for a user"""
    try:
        roles = await db.user_roles.find(
            {"user_id": user_id},
            {"_id": 0, "role": 1}
        ).to_list(10)
        
        return [r['role'] for r in roles]
    except Exception as e:
        logger.error(f"Error getting user roles: {str(e)}")
        return []


async def get_user_permissions(user_id: str) -> Set[str]:
    """Get all permissions for a user based on their roles"""
    roles = await get_user_roles(user_id)
    
    permissions = set()
    for role in roles:
        if role in ROLES:
            permissions.update(ROLES[role]['permissions'])
    
    return permissions


async def has_permission(user_id: str, permission: str) -> bool:
    """Check if user has a specific permission"""
    permissions = await get_user_permissions(user_id)
    return permission in permissions


async def require_permission(user_id: str, permission: str):
    """Raise exception if user doesn't have permission"""
    if not await has_permission(user_id, permission):
        raise HTTPException(403, f"Permission denied: {permission} required")


async def assign_role(user_id: str, role: str) -> bool:
    """Assign a role to a user"""
    if role not in ROLES:
        raise HTTPException(400, f"Invalid role: {role}")
    
    try:
        # Check if role already exists
        existing = await db.user_roles.find_one({
            "user_id": user_id,
            "role": role
        })
        
        if existing:
            return True  # Already has role
        
        # Import here to avoid circular dependency
        from datetime import datetime, timezone
        import uuid
        
        # Assign role
        await db.user_roles.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "role": role,
            "created_at": datetime.now(timezone.utc)
        })
        
        logger.info(f"Assigned role {role} to user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error assigning role: {str(e)}")
        return False


async def remove_role(user_id: str, role: str) -> bool:
    """Remove a role from a user"""
    try:
        result = await db.user_roles.delete_one({
            "user_id": user_id,
            "role": role
        })
        
        if result.deleted_count > 0:
            logger.info(f"Removed role {role} from user {user_id}")
            return True
        return False
        
    except Exception as e:
        logger.error(f"Error removing role: {str(e)}")
        return False


async def is_manager(user_id: str) -> bool:
    """Check if user has manager role"""
    roles = await get_user_roles(user_id)
    return 'manager' in roles or 'admin' in roles


async def get_subordinate_ids(manager_id: str, include_self: bool = False) -> List[str]:
    """
    Get all subordinate user IDs for a manager (recursive)
    Returns flat list of all direct and indirect reports
    """
    subordinate_ids = []
    
    if include_self:
        subordinate_ids.append(manager_id)
    
    async def get_direct_reports(manager_id: str):
        """Recursively get all subordinates"""
        direct_reports = await db.users.find(
            {"manager_id": manager_id},
            {"_id": 0, "id": 1}
        ).to_list(1000)
        
        for report in direct_reports:
            user_id = report['id']
            if user_id not in subordinate_ids:
                subordinate_ids.append(user_id)
                # Recursively get their reports
                await get_direct_reports(user_id)
    
    await get_direct_reports(manager_id)
    
    return subordinate_ids


async def get_team_member_ids(user_id: str) -> List[str]:
    """
    Get all team member IDs that a user can access
    - If manager: returns all subordinates + self
    - If admin: returns all enterprise users
    - If employee: returns only self
    """
    try:
        # Get user info
        user = await db.users.find_one(
            {"id": user_id},
            {"_id": 0, "enterprise_id": 1}
        )
        
        if not user:
            return [user_id]
        
        # Check if admin
        roles = await get_user_roles(user_id)
        if 'admin' in roles:
            # Admin can see all users in their enterprise
            if user.get('enterprise_id'):
                all_users = await db.users.find(
                    {"enterprise_id": user['enterprise_id']},
                    {"_id": 0, "id": 1}
                ).to_list(10000)
                return [u['id'] for u in all_users]
            return [user_id]
        
        # Check if manager
        if 'manager' in roles:
            # Get all subordinates + self
            return await get_subordinate_ids(user_id, include_self=True)
        
        # Employee - only self
        return [user_id]
        
    except Exception as e:
        logger.error(f"Error getting team member IDs: {str(e)}")
        return [user_id]


async def can_access_user_data(requester_id: str, target_user_id: str) -> bool:
    """Check if requester can access target user's data"""
    if requester_id == target_user_id:
        return True
    
    # Get accessible user IDs for requester
    accessible_ids = await get_team_member_ids(requester_id)
    return target_user_id in accessible_ids


async def filter_by_team_access(user_id: str, user_ids: List[str]) -> List[str]:
    """Filter a list of user IDs to only those accessible by the user"""
    accessible_ids = await get_team_member_ids(user_id)
    return [uid for uid in user_ids if uid in accessible_ids]
