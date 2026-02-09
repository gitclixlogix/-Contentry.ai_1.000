"""
Roles Management Module
=======================
Refactored roles module with separate files for:
- permissions: Permission listing and checking endpoints
- crud: Role CRUD operations
- assignments: Role assignment to users
- audit: Audit log viewing and export

This module combines all sub-routers into a single router.
"""

from fastapi import APIRouter

from .permissions import router as permissions_router
from .crud import router as crud_router
from .assignments import router as assignments_router
from .audit import router as audit_router

# Create main router
router = APIRouter(prefix="/roles", tags=["roles"])

# Include all sub-routers
# Note: Order matters for FastAPI route matching
# Static routes (permissions, audit) must come before dynamic routes ({role_id})
router.include_router(permissions_router)  # /permissions, /permissions/check, etc.
router.include_router(audit_router)        # /audit, /audit/export, /audit/statistics
router.include_router(crud_router, prefix="")  # "", /{role_id}, /feature-status, etc.
router.include_router(assignments_router, prefix="")  # /{role_id}/assignments, /users/{user_id}/roles
