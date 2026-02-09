"""
Authorization Decorator Service (ARCH-005)

Implements @require_permission decorator for consistent RBAC enforcement across all routes.

Features:
- Permission-based access control
- Enterprise-scoped permissions
- Super admin bypass
- Audit logging of authorization decisions
- 403 Forbidden responses for unauthorized access

Usage:
    from services.authorization_decorator import require_permission
    
    @router.post("/content/analyze")
    @require_permission("content.create")
    async def analyze_content(request: Request):
        # Only users with "content.create" permission can access
        pass

Issues Addressed:
- ARCH-005: Inconsistent RBAC Enforcement Across Routes
- ISS-051: Demo login fake token verification
- ISS-052: Super admin client-side verification
"""

import logging
from functools import wraps
from typing import Optional, List, Union, Callable
from datetime import datetime, timezone
from fastapi import HTTPException, Request, Header
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


# =============================================================================
# ENDPOINT PERMISSION MAPPING
# =============================================================================

# Maps route patterns to required permissions
# Used for documentation and automated permission checking
ENDPOINT_PERMISSIONS = {
    # Content Routes
    "POST /api/content/analyze": "content.create",
    "POST /api/content/analyze/async": "content.create",
    "POST /api/content/generate": "content.create",
    "POST /api/content/generate/async": "content.create",
    "POST /api/content/rewrite": "content.edit_own",
    "POST /api/content/generate-image": "content.create",
    "GET /api/content/history": "content.view_own",
    "DELETE /api/content/history/{id}": "content.delete_own",
    
    # Policy Routes
    "GET /api/policies": "policies.view",
    "POST /api/policies": "policies.create",
    "PUT /api/policies/{id}": "policies.edit",
    "DELETE /api/policies/{id}": "policies.delete",
    "POST /api/policies/bulk-create": "policies.create",
    
    # Strategic Profiles Routes
    "GET /api/strategic-profiles": "profiles.view",
    "POST /api/strategic-profiles": "profiles.create",
    "PUT /api/strategic-profiles/{id}": "profiles.edit",
    "DELETE /api/strategic-profiles/{id}": "profiles.delete",
    
    # Team Routes
    "GET /api/team/members": "team.view_members",
    "POST /api/team/invite": "team.invite_members",
    "DELETE /api/team/member/{id}": "team.remove_members",
    "PUT /api/team/member/{id}/role": "team.assign_roles",
    
    # Analytics Routes
    "GET /api/analytics/overview": "analytics.view_own",
    "GET /api/analytics/team": "analytics.view_team",
    "GET /api/analytics/enterprise": "analytics.view_enterprise",
    "GET /api/analytics/export": "analytics.export",
    
    # Social Routes
    "GET /api/socials": "social.view",
    "POST /api/socials/connect": "social.manage",
    "DELETE /api/socials/{id}": "social.manage",
    "POST /api/posts": "content.publish",
    "GET /api/posts": "content.view_own",
    "DELETE /api/posts/{id}": "content.delete_own",
    
    # Approval Workflow Routes
    "GET /api/approval/pending": "content.approve",
    "POST /api/approval/{id}/approve": "content.approve",
    "POST /api/approval/{id}/reject": "content.approve",
    
    # Subscription Routes
    "GET /api/subscriptions/current": "settings.view",
    "POST /api/subscriptions/upgrade": "settings.edit_billing",
    "POST /api/subscriptions/cancel": "settings.edit_billing",
    
    # Knowledge Base Routes
    "GET /api/user-knowledge/documents": "knowledge.view",
    "POST /api/user-knowledge/upload": "knowledge.upload",
    "DELETE /api/user-knowledge/documents/{id}": "knowledge.delete",
    
    # Projects Routes
    "GET /api/projects": "content.view_own",
    "POST /api/projects": "content.create",
    "PUT /api/projects/{id}": "content.edit_own",
    "DELETE /api/projects/{id}": "content.delete_own",
    
    # Roles Routes (Admin)
    "GET /api/roles": "roles.view",
    "POST /api/roles": "roles.create",
    "PUT /api/roles/{id}": "roles.edit",
    "DELETE /api/roles/{id}": "roles.delete",
    
    # Enterprise Admin Routes
    "GET /api/enterprises/settings": "settings.view",
    "PUT /api/enterprises/settings": "settings.edit_integrations",
    "GET /api/enterprises/users": "team.view_members",
    
    # Super Admin Routes (require super_admin role check)
    "GET /api/superadmin/*": "superadmin.access",
    "POST /api/superadmin/*": "superadmin.access",
    "PUT /api/superadmin/*": "superadmin.access",
    "DELETE /api/superadmin/*": "superadmin.access",
}


# Permissions that any authenticated user has by default
DEFAULT_USER_PERMISSIONS = {
    "content.create",
    "content.view_own",
    "content.edit_own",
    "content.delete_own",
    "analytics.view_own",
    "profiles.view",
    "profiles.create",      # Added for strategic profiles
    "profiles.edit",        # Added for strategic profiles
    "knowledge.view",
    "knowledge.upload",
    "knowledge.delete",     # Added for knowledge base management
    "settings.view",
    "policies.view",        # Added as per review request
    "policies.create",      # Added as per review request  
    "team.view_members",    # Added as per review request
    "team.invite_members",  # Added for team invite functionality
    "projects.view",        # Added for projects access (ARCH-005 Phase 5.1b)
    "projects.create",      # Added for projects creation
    "notifications.view",   # Added for notifications (ARCH-005 Phase 5.1b)
    "notifications.manage", # Added for notification settings
    "social.view",          # Added for social accounts view
    "documentation.view",   # Added for documentation access
    "roles.view",           # Added for viewing roles and permissions
    "scheduler.view",       # Added for viewing scheduled content
    "scheduler.manage",     # Added for managing scheduled prompts and posts
}


# Super admin permissions - full access
SUPER_ADMIN_PERMISSIONS = {"*"}


# =============================================================================
# PERMISSION SERVICE FUNCTIONS
# =============================================================================

async def get_user_context(
    request: Request,
    user_id: Optional[str] = None,
    db: Optional[AsyncIOMotorDatabase] = None
) -> dict:
    """
    Extract user context from request for permission checking.
    
    Returns dict with user_id, enterprise_id, is_super_admin
    """
    # Try to get user_id from various sources
    uid = user_id
    if not uid:
        uid = request.headers.get("X-User-ID")
    if not uid:
        # Try to get from Authorization header or cookies (Bearer token)
        import jwt
        import os
        token = None
        
        # First try cookie (most secure, used by frontend)
        cookie_name = os.environ.get("COOKIE_NAME", "access_token")
        token = request.cookies.get(cookie_name)
        
        # Fall back to Authorization header for API clients
        if not token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
        
        if token:
            try:
                secret = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-in-production")
                payload = jwt.decode(token, secret, algorithms=["HS256"])
                uid = payload.get("sub")
                logger.debug(f"Extracted user_id from JWT: {uid}")
            except jwt.ExpiredSignatureError:
                logger.debug("JWT token expired")
            except jwt.InvalidTokenError as e:
                logger.debug(f"Invalid JWT token: {e}")
            except Exception as e:
                logger.debug(f"JWT extraction failed: {e}")
    
    if not uid:
        return {
            "user_id": None,
            "enterprise_id": None,
            "is_super_admin": False,
            "permissions": set()
        }
    
    # Get database connection
    if db is None:
        from services.database import get_legacy_db
        db = get_legacy_db()
    
    if db is None:
        logger.warning("Database not available for permission check")
        return {
            "user_id": uid,
            "enterprise_id": None,
            "is_super_admin": False,
            "permissions": DEFAULT_USER_PERMISSIONS
        }
    
    # Fetch user from database
    user = await db.users.find_one({"id": uid}, {"_id": 0})
    
    if not user:
        return {
            "user_id": uid,
            "enterprise_id": None,
            "is_super_admin": False,
            "permissions": DEFAULT_USER_PERMISSIONS
        }
    
    enterprise_id = user.get("enterprise_id")
    is_super_admin = user.get("is_super_admin", False) or user.get("role") == "super_admin"
    
    # Super admin has all permissions
    if is_super_admin:
        return {
            "user_id": uid,
            "enterprise_id": enterprise_id,
            "is_super_admin": True,
            "permissions": SUPER_ADMIN_PERMISSIONS
        }
    
    # Get permissions from permission service
    try:
        from services.permission_service import PermissionService
        perm_service = PermissionService()
        permissions = await perm_service.get_user_permissions(uid, enterprise_id or "default")
    except Exception as e:
        logger.warning(f"Failed to get permissions from service: {e}")
        permissions = DEFAULT_USER_PERMISSIONS
    
    return {
        "user_id": uid,
        "enterprise_id": enterprise_id,
        "is_super_admin": False,
        "permissions": permissions
    }


async def check_permission(
    user_id: str,
    permission: str,
    enterprise_id: Optional[str] = None,
    db: Optional[AsyncIOMotorDatabase] = None
) -> bool:
    """
    Check if a user has a specific permission.
    
    Args:
        user_id: User ID to check
        permission: Permission string (e.g., "content.create")
        enterprise_id: Optional enterprise context
        db: Database connection
    
    Returns:
        True if user has permission, False otherwise
    """
    if db is None:
        from services.database import get_legacy_db
        db = get_legacy_db()
    
    if db is None:
        logger.warning("Database not available for permission check")
        # Fail open for basic permissions, closed for sensitive ones
        return permission in DEFAULT_USER_PERMISSIONS
    
    # Check if user is super admin
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "is_super_admin": 1, "role": 1, "enterprise_id": 1})
    
    if not user:
        return False
    
    is_super_admin = user.get("is_super_admin", False) or user.get("role") == "super_admin"
    if is_super_admin:
        return True
    
    # Use enterprise_id from user if not provided
    ent_id = enterprise_id or user.get("enterprise_id") or "default"
    
    # Get user permissions
    try:
        from services.permission_service import PermissionService
        perm_service = PermissionService()
        permissions = await perm_service.get_user_permissions(user_id, ent_id)
        
        # Check for wildcard permission
        if "*" in permissions:
            return True
        
        return permission in permissions
    except Exception as e:
        logger.warning(f"Permission check failed: {e}")
        return permission in DEFAULT_USER_PERMISSIONS


async def log_authorization_decision(
    user_id: str,
    permission: str,
    granted: bool,
    endpoint: str,
    reason: Optional[str] = None,
    db: Optional[AsyncIOMotorDatabase] = None
):
    """
    Log authorization decision for audit trail.
    """
    try:
        if db is None:
            from services.database import get_legacy_db
            db = get_legacy_db()
        
        if db is None:
            return
        
        log_entry = {
            "user_id": user_id,
            "permission": permission,
            "granted": granted,
            "endpoint": endpoint,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await db.authorization_logs.insert_one(log_entry)
        
        if not granted:
            logger.warning(f"Authorization denied: user={user_id}, permission={permission}, endpoint={endpoint}")
        
    except Exception as e:
        logger.error(f"Failed to log authorization: {e}")


# =============================================================================
# REQUIRE_PERMISSION DECORATOR
# =============================================================================

def require_permission(
    permission: Union[str, List[str]],
    any_of: bool = False,
    log_access: bool = True
):
    """
    Decorator to enforce permission checks on route handlers.
    
    Args:
        permission: Required permission(s). Can be a single string or list.
        any_of: If True, user needs ANY of the permissions. If False, ALL are required.
        log_access: Whether to log authorization decisions.
    
    Usage:
        @router.post("/content/analyze")
        @require_permission("content.create")
        async def analyze_content(request: Request):
            pass
        
        @router.delete("/policies/{id}")
        @require_permission(["policies.delete", "admin.manage"])
        async def delete_policy(policy_id: str):
            pass
    
    Raises:
        HTTPException 401: If user is not authenticated
        HTTPException 403: If user lacks required permission
    """
    permissions = [permission] if isinstance(permission, str) else permission
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find Request object in args or kwargs
            request = None
            
            # First check kwargs for common Request parameter names
            for param_name in ["request", "request_obj", "req"]:
                if param_name in kwargs:
                    candidate = kwargs[param_name]
                    if hasattr(candidate, 'url') and hasattr(candidate, 'method'):
                        request = candidate
                        break
            
            # If not found in kwargs, check args
            if not request:
                for arg in args:
                    if hasattr(arg, 'url') and hasattr(arg, 'method'):
                        request = arg
                        break
            
            # Get user context
            user_id = kwargs.get("user_id") or kwargs.get("x_user_id")
            db = kwargs.get("db") or kwargs.get("db_conn")
            
            # For internal calls (no request), try to get user_id from first argument
            # This handles cases like analyze_content(ContentAnalyze(user_id=...))
            if not user_id and not request and args:
                first_arg = args[0]
                if hasattr(first_arg, 'user_id'):
                    user_id = first_arg.user_id
                    logger.debug(f"Extracted user_id from first argument: {user_id}")
            
            # Debug logging (remove after fixing)
            # import traceback
            # logger.warning(f"require_permission: kwargs keys = {list(kwargs.keys())}")
            # logger.warning(f"require_permission: user_id from kwargs = {user_id}")
            # logger.warning(f"require_permission: request = {request}")
            # logger.warning(f"require_permission: call stack = {''.join(traceback.format_stack()[-5:-1])}")
            
            if request:
                user_context = await get_user_context(request, user_id, db)
            else:
                user_context = {
                    "user_id": user_id,
                    "enterprise_id": None,
                    "is_super_admin": False,
                    "permissions": DEFAULT_USER_PERMISSIONS
                }
            
            uid = user_context["user_id"]
            
            # Check if user is authenticated
            if not uid:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": "authentication_required",
                        "message": "You must be logged in to access this resource"
                    }
                )
            
            # Super admin bypasses all permission checks
            if user_context["is_super_admin"]:
                if log_access:
                    await log_authorization_decision(
                        uid, 
                        permissions[0], 
                        True, 
                        request.url.path if request else "unknown",
                        "super_admin_bypass"
                    )
                return await func(*args, **kwargs)
            
            # Check permissions
            user_permissions = user_context["permissions"]
            
            # Handle wildcard permission
            if "*" in user_permissions:
                if log_access:
                    await log_authorization_decision(
                        uid,
                        permissions[0],
                        True,
                        request.url.path if request else "unknown",
                        "wildcard_permission"
                    )
                return await func(*args, **kwargs)
            
            # Check required permissions
            if any_of:
                has_permission = any(p in user_permissions for p in permissions)
            else:
                has_permission = all(p in user_permissions for p in permissions)
            
            endpoint_path = request.url.path if request else "unknown"
            
            if not has_permission:
                if log_access:
                    await log_authorization_decision(
                        uid,
                        ", ".join(permissions),
                        False,
                        endpoint_path,
                        f"missing_permissions: {permissions}"
                    )
                
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "permission_denied",
                        "message": "You do not have permission to access this resource",
                        "required_permissions": permissions,
                        "any_of": any_of
                    }
                )
            
            # Permission granted
            if log_access:
                await log_authorization_decision(
                    uid,
                    permissions[0],
                    True,
                    endpoint_path
                )
            
            return await func(*args, **kwargs)
        
        # Store permission info on function for documentation
        wrapper._required_permissions = permissions
        wrapper._any_of = any_of
        
        return wrapper
    
    return decorator


def require_super_admin(func: Callable):
    """
    Decorator to restrict access to super admins only.
    
    Usage:
        @router.get("/superadmin/users")
        @require_super_admin
        async def list_all_users(request: Request):
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Find Request object
        request = kwargs.get("request")
        if not request:
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
        
        user_id = kwargs.get("user_id") or kwargs.get("x_user_id")
        db = kwargs.get("db") or kwargs.get("db_conn")
        
        if request:
            user_context = await get_user_context(request, user_id, db)
        else:
            user_context = {"user_id": user_id, "is_super_admin": False}
        
        uid = user_context.get("user_id")
        
        if not uid:
            raise HTTPException(
                status_code=401,
                detail={"error": "authentication_required", "message": "You must be logged in"}
            )
        
        if not user_context.get("is_super_admin"):
            await log_authorization_decision(
                uid,
                "superadmin.access",
                False,
                request.url.path if request else "unknown",
                "not_super_admin"
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "super_admin_required",
                    "message": "This action requires super admin privileges"
                }
            )
        
        await log_authorization_decision(
            uid,
            "superadmin.access",
            True,
            request.url.path if request else "unknown"
        )
        
        return await func(*args, **kwargs)
    
    wrapper._required_permissions = ["superadmin.access"]
    
    return wrapper


def require_enterprise_admin(func: Callable):
    """
    Decorator to restrict access to enterprise admins.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get("request")
        if not request:
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
        
        user_id = kwargs.get("user_id") or kwargs.get("x_user_id")
        db = kwargs.get("db") or kwargs.get("db_conn")
        
        if request:
            user_context = await get_user_context(request, user_id, db)
        else:
            user_context = {"user_id": user_id, "is_super_admin": False, "permissions": set()}
        
        uid = user_context.get("user_id")
        
        if not uid:
            raise HTTPException(
                status_code=401,
                detail={"error": "authentication_required", "message": "You must be logged in"}
            )
        
        # Super admin can access enterprise admin functions
        if user_context.get("is_super_admin"):
            return await func(*args, **kwargs)
        
        # Check for enterprise admin permissions
        admin_permissions = {"team.remove_members", "settings.edit_billing", "roles.delete"}
        user_permissions = user_context.get("permissions", set())
        
        has_admin_access = bool(admin_permissions & user_permissions) or "*" in user_permissions
        
        if not has_admin_access:
            await log_authorization_decision(
                uid,
                "enterprise_admin.access",
                False,
                request.url.path if request else "unknown",
                "not_enterprise_admin"
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "enterprise_admin_required",
                    "message": "This action requires enterprise admin privileges"
                }
            )
        
        return await func(*args, **kwargs)
    
    wrapper._required_permissions = ["enterprise_admin.access"]
    
    return wrapper


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_endpoint_permission(method: str, path: str) -> Optional[str]:
    """
    Get required permission for an endpoint from the mapping.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Route path
    
    Returns:
        Required permission or None if not mapped
    """
    key = f"{method.upper()} {path}"
    
    # Try exact match first
    if key in ENDPOINT_PERMISSIONS:
        return ENDPOINT_PERMISSIONS[key]
    
    # Try wildcard match
    for pattern, permission in ENDPOINT_PERMISSIONS.items():
        if pattern.endswith("*"):
            base_pattern = pattern[:-1]
            method_pattern, path_pattern = base_pattern.split(" ", 1)
            if method.upper() == method_pattern and path.startswith(path_pattern):
                return permission
    
    return None


async def verify_super_admin_server_side(
    user_id: str,
    db: Optional[AsyncIOMotorDatabase] = None
) -> bool:
    """
    Verify super admin status server-side (ISS-052 fix).
    
    NEVER trust client-side claims of super admin status.
    Always verify against the database.
    """
    if db is None:
        from services.database import get_legacy_db
        db = get_legacy_db()
    
    if db is None:
        return False
    
    user = await db.users.find_one(
        {"id": user_id},
        {"_id": 0, "is_super_admin": 1, "role": 1, "email": 1}
    )
    
    if not user:
        return False
    
    # Check both is_super_admin flag and role
    is_super = user.get("is_super_admin", False) or user.get("role") == "super_admin"
    
    # Additional check: verify email domain for super admin
    # This prevents unauthorized super admin account creation
    email = user.get("email", "")
    allowed_super_admin_domains = ["contentry.com", "emergentlabs.io"]
    email_domain = email.split("@")[-1] if "@" in email else ""
    
    # Super admin must have is_super_admin flag AND be from allowed domain
    # OR be explicitly marked as super_admin role
    if is_super:
        if user.get("role") == "super_admin":
            return True
        if email_domain in allowed_super_admin_domains:
            return True
        
        # Log potential security issue
        logger.warning(f"User {user_id} has is_super_admin=True but email domain {email_domain} not allowed")
        return False
    
    return False
