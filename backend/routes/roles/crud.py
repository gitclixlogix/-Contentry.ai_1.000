"""
Roles Module - CRUD Endpoints
=============================
API endpoints for creating, reading, updating, and deleting roles.

Security Update (ARCH-005 Phase 5.1b):
- Added @require_permission decorators for RBAC enforcement
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Query, Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from services.permission_service import permission_service
from services.role_service import role_service

# Import database dependency injection
from services.database import get_db

# ARCH-005: Authorization decorator
from services.authorization_decorator import require_permission

from .helpers import (
    get_user_and_enterprise, 
    check_user_permission, 
    CreateRoleRequest,
    UpdateRoleRequest,
    DuplicateRoleRequest
)

router = APIRouter(tags=["roles"])


@router.get("/feature-status")
@require_permission("roles.view")
async def get_feature_status(
    request: Request,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Check if granular permissions feature is enabled for the enterprise.
    
    Security (ARCH-005): Requires roles.view permission.
    """
    user, enterprise_id = await get_user_and_enterprise(x_user_id)
    
    is_enabled = await permission_service.is_feature_enabled(enterprise_id)
    
    return {
        "feature": "granular_permissions",
        "enabled": is_enabled,
        "enterprise_id": enterprise_id
    }


@router.get("/")
@require_permission("roles.view")
async def list_roles(
    request: Request,
    include_system: bool = Query(True, description="Include system roles"),
    include_inactive: bool = Query(False, description="Include inactive roles"),
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    List all roles available to the enterprise.
    
    Security (ARCH-005): Requires roles.view permission.
    """
    user, enterprise_id = await get_user_and_enterprise(x_user_id)
    
    roles = await role_service.get_roles_for_enterprise(
        enterprise_id,
        include_system=include_system,
        include_inactive=include_inactive
    )
    
    return {
        "roles": roles,
        "total": len(roles)
    }


@router.post("/")
@require_permission("roles.create")
async def create_role(
    request_obj: Request,
    request: CreateRoleRequest,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Create a new custom role.
    
    Security (ARCH-005): Requires roles.create permission.
    """
    user, enterprise_id = await get_user_and_enterprise(x_user_id)
    
    # Validate that user has all permissions they're trying to grant
    user_permissions = await permission_service.get_user_permissions(x_user_id, enterprise_id)
    
    # Allow if user has wildcard or all requested permissions
    if "*" not in user_permissions:
        for perm in request.permissions:
            if perm not in user_permissions:
                raise HTTPException(
                    status_code=403,
                    detail=f"Cannot grant permission '{perm}' - you don't have this permission"
                )
    
    try:
        role = await role_service.create_role(
            enterprise_id=enterprise_id,
            name=request.name,
            description=request.description,
            permissions=request.permissions,
            created_by=x_user_id,
            color=request.color,
            icon=request.icon
        )
        
        return {
            "message": "Role created successfully",
            "role": role
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{role_id}")
@require_permission("roles.view")
async def get_role(
    request: Request,
    role_id: str,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get details of a specific role.
    
    Security (ARCH-005): Requires roles.view permission.
    """
    user, enterprise_id = await get_user_and_enterprise(x_user_id)
    
    role = await role_service.get_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Verify access to this role
    if role.get("enterprise_id") and role["enterprise_id"] != enterprise_id:
        if not role.get("is_system_role"):
            raise HTTPException(status_code=404, detail="Role not found")
    
    # Get user count
    user_count = await db_conn.role_assignments.count_documents({
        "role_id": role_id,
        "enterprise_id": enterprise_id
    })
    
    return {
        "role": role,
        "user_count": user_count
    }


@router.put("/{role_id}")
@require_permission("roles.edit")
async def update_role(
    request_obj: Request,
    role_id: str,
    request: UpdateRoleRequest,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Update an existing role.
    
    Security (ARCH-005): Requires roles.edit permission.
    """
    user, enterprise_id = await get_user_and_enterprise(x_user_id)
    
    # Verify role belongs to this enterprise
    role = await role_service.get_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if role.get("enterprise_id") != enterprise_id:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Validate permissions if being updated
    if request.permissions is not None:
        user_permissions = await permission_service.get_user_permissions(x_user_id, enterprise_id)
        if "*" not in user_permissions:
            for perm in request.permissions:
                if perm not in user_permissions:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Cannot grant permission '{perm}' - you don't have this permission"
                    )
    
    try:
        updated_role = await role_service.update_role(
            role_id=role_id,
            updated_by=x_user_id,
            name=request.name,
            description=request.description,
            permissions=request.permissions,
            color=request.color,
            icon=request.icon
        )
        
        return {
            "message": "Role updated successfully",
            "role": updated_role
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{role_id}")
@require_permission("roles.delete")
async def delete_role(
    request: Request,
    role_id: str,
    reassign_to: Optional[str] = Query(None, description="Role ID to reassign users to"),
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Delete a custom role. Optionally reassign users to another role.
    
    Security (ARCH-005): Requires roles.delete permission.
    """
    user, enterprise_id = await get_user_and_enterprise(x_user_id)
    
    # Verify role belongs to this enterprise
    role = await role_service.get_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if role.get("enterprise_id") != enterprise_id:
        raise HTTPException(status_code=404, detail="Role not found")
    
    try:
        result = await role_service.delete_role(
            role_id=role_id,
            deleted_by=x_user_id,
            reassign_to=reassign_to
        )
        
        return {
            "message": "Role deleted successfully",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{role_id}/duplicate")
@require_permission("roles.create")
async def duplicate_role(
    request_obj: Request,
    role_id: str,
    request: DuplicateRoleRequest,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Duplicate an existing role with a new name.
    Can duplicate both system roles and custom roles.
    
    Security (ARCH-005): Requires roles.create permission.
    """
    user, enterprise_id = await get_user_and_enterprise(x_user_id)
    
    try:
        new_role = await role_service.duplicate_role(
            source_role_id=role_id,
            enterprise_id=enterprise_id,
            new_name=request.new_name,
            created_by=x_user_id,
            new_description=request.new_description
        )
        
        return {
            "message": "Role duplicated successfully",
            "role": new_role
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{role_id}/effective-permissions")
@require_permission("roles.view")
async def get_effective_permissions(
    request: Request,
    role_id: str,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get a role with all effective permissions resolved, including inherited ones.
    
    Security (ARCH-005): Requires roles.view permission.
    """
    user, enterprise_id = await get_user_and_enterprise(x_user_id)
    
    try:
        role_with_inheritance = await role_service.get_role_with_inherited_permissions(role_id)
        
        return {
            "role": role_with_inheritance,
            "inheritance_info": {
                "direct_permissions_count": len(role_with_inheritance.get("permissions", [])),
                "inherited_permissions_count": len(role_with_inheritance.get("inherited_permissions", [])),
                "effective_permissions_count": len(role_with_inheritance.get("effective_permissions", []))
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
