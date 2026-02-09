"""
Roles Module - Permission Endpoints
===================================
API endpoints for managing and checking permissions.

Security Update (ARCH-005 Phase 5.1b):
- Added @require_permission decorators for RBAC enforcement
"""

from fastapi import APIRouter, Header, Query, Request, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from services.permission_service import permission_service, PERMISSIONS, ALL_PERMISSIONS
from services.database import get_db
from services.authorization_decorator import require_permission
from .helpers import get_user_and_enterprise, PermissionCheckRequest

router = APIRouter(tags=["permissions"])


@router.get("/permissions")
@require_permission("roles.view")
async def list_permissions(
    request: Request,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get all available permissions grouped by category.
    
    Security (ARCH-005): Requires roles.view permission.
    """
    user, enterprise_id = await get_user_and_enterprise(x_user_id)
    
    # Format permissions for frontend
    categories = []
    for category_key, perms in PERMISSIONS.items():
        category = {
            "key": category_key,
            "name": category_key.replace("_", " ").title(),
            "permissions": []
        }
        for perm_key, perm_info in perms.items():
            category["permissions"].append({
                "key": perm_key,
                **perm_info
            })
        categories.append(category)
    
    return {
        "categories": categories,
        "total": len(ALL_PERMISSIONS)
    }


@router.get("/permissions/check")
@require_permission("roles.view")
async def check_permission(
    request: Request,
    permission: str = Query(..., description="Permission to check"),
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Check if the current user has a specific permission.
    
    Security (ARCH-005): Requires roles.view permission.
    """
    user, enterprise_id = await get_user_and_enterprise(x_user_id)
    
    allowed = await permission_service.check_permission(
        x_user_id, enterprise_id, permission
    )
    
    return {
        "permission": permission,
        "allowed": allowed
    }


@router.post("/permissions/check-bulk")
@require_permission("roles.view")
async def check_permissions_bulk(
    request_obj: Request,
    request: PermissionCheckRequest,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Check multiple permissions at once.
    
    Security (ARCH-005): Requires roles.view permission.
    """
    user, enterprise_id = await get_user_and_enterprise(x_user_id)
    
    results = await permission_service.check_permissions_bulk(
        x_user_id, enterprise_id, request.permissions
    )
    
    return {"results": results}


@router.get("/inheritance-rules")
@require_permission("roles.view")
async def get_inheritance_rules(
    request: Request,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get all permission inheritance rules.
    Shows which permissions automatically grant other permissions.
    
    Security (ARCH-005): Requires roles.view permission.
    """
    from services.permission_service import PERMISSION_INHERITANCE
    
    await get_user_and_enterprise(x_user_id)
    
    # Format inheritance rules for frontend display
    rules = []
    for parent_perm, child_perms in PERMISSION_INHERITANCE.items():
        parent_info = permission_service.get_permission_info(parent_perm)
        rules.append({
            "parent_permission": parent_perm,
            "parent_name": parent_info.get("name", parent_perm) if parent_info else parent_perm,
            "grants_permissions": child_perms,
            "grants_count": len(child_perms)
        })
    
    return {
        "inheritance_rules": rules,
        "total_rules": len(rules)
    }
