"""
Roles Module - Assignment Endpoints
===================================
API endpoints for managing role assignments to users.

Security Update (ARCH-005 Phase 5.1b):
- Added @require_permission decorators for RBAC enforcement
"""

from fastapi import APIRouter, HTTPException, Header, Query, Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from services.role_service import role_service

# Import database dependency injection
from services.database import get_db

# ARCH-005: Authorization decorator
from services.authorization_decorator import require_permission

from .helpers import (
    get_user_and_enterprise, 
    check_user_permission, 
    AssignRoleRequest
)

router = APIRouter(tags=["role-assignments"])


@router.post("/{role_id}/assignments")
@require_permission("roles.assign")
async def assign_role(
    request_obj: Request,
    role_id: str,
    request: AssignRoleRequest,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Assign a role to a user.
    
    Security (ARCH-005): Requires roles.assign permission.
    """
    user, enterprise_id = await get_user_and_enterprise(x_user_id)
    
    # Verify target user is in the same enterprise
    target_user = await db_conn.users.find_one(
        {"id": request.user_id},
        {"enterprise_id": 1, "_id": 0}
    )
    
    if not target_user or target_user.get("enterprise_id") != enterprise_id:
        raise HTTPException(status_code=404, detail="User not found in your enterprise")
    
    try:
        result = await role_service.assign_role(
            user_id=request.user_id,
            enterprise_id=enterprise_id,
            role_id=role_id,
            assigned_by=x_user_id,
            valid_until=request.valid_until
        )
        
        return {
            "message": "Role assigned successfully",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{role_id}/assignments/{user_id}")
@require_permission("roles.assign")
async def remove_role_assignment(
    request: Request,
    role_id: str,
    user_id: str,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Remove a role assignment from a user.
    
    Security (ARCH-005): Requires roles.assign permission.
    """
    user, enterprise_id = await get_user_and_enterprise(x_user_id)
    
    try:
        result = await role_service.remove_role_assignment(
            user_id=user_id,
            enterprise_id=enterprise_id,
            role_id=role_id,
            removed_by=x_user_id
        )
        
        return {
            "message": "Role assignment removed successfully",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{role_id}/users")
@require_permission("team.view_members")
async def get_role_users(
    request: Request,
    role_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get all users who have a specific role.
    
    Security (ARCH-005): Requires team.view_members permission.
    """
    user, enterprise_id = await get_user_and_enterprise(x_user_id)
    
    result = await role_service.get_users_with_role(
        role_id=role_id,
        enterprise_id=enterprise_id,
        page=page,
        limit=limit
    )
    
    return result


@router.get("/users/{user_id}/roles")
@require_permission("roles.view")
async def get_user_roles(
    request: Request,
    user_id: str,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get all roles assigned to a specific user.
    
    Security (ARCH-005): Requires roles.view permission.
    """
    user, enterprise_id = await get_user_and_enterprise(x_user_id)
    
    # Users can view their own roles, or need team.view_members for others
    if user_id != x_user_id:
        await check_user_permission(x_user_id, enterprise_id, "team.view_members")
    
    # Verify target user is in the same enterprise
    target_user = await db_conn.users.find_one(
        {"id": user_id},
        {"enterprise_id": 1, "_id": 0}
    )
    
    if not target_user or target_user.get("enterprise_id") != enterprise_id:
        raise HTTPException(status_code=404, detail="User not found in your enterprise")
    
    result = await role_service.get_user_roles(user_id, enterprise_id)
    
    return result
