"""
Multi-Tenant Middleware (ARCH-009)

Provides database-level tenant isolation by automatically injecting tenant_id
(enterprise_id) into the request context for all authenticated requests.

Features:
- Extracts user_id from request header
- Looks up user's enterprise_id from database
- Injects tenant context into request state
- Supports both enterprise and personal users

Usage:
    # In request handlers, access tenant context via:
    enterprise_id = request.state.enterprise_id  # or None for personal users
    user_id = request.state.user_id
"""

import logging
from typing import Optional, Tuple
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time

logger = logging.getLogger(__name__)

# Cache for user -> enterprise_id mapping (TTL: 5 minutes)
_tenant_cache: dict = {}
_cache_ttl_seconds = 300


def _get_cached_enterprise_id(user_id: str) -> Optional[Tuple[Optional[str], float]]:
    """Get cached enterprise_id for user if not expired"""
    if user_id in _tenant_cache:
        enterprise_id, cached_at = _tenant_cache[user_id]
        if time.time() - cached_at < _cache_ttl_seconds:
            return enterprise_id, cached_at
        # Cache expired, remove it
        del _tenant_cache[user_id]
    return None


def _cache_enterprise_id(user_id: str, enterprise_id: Optional[str]) -> None:
    """Cache enterprise_id for user"""
    _tenant_cache[user_id] = (enterprise_id, time.time())


def clear_tenant_cache(user_id: Optional[str] = None) -> None:
    """Clear tenant cache for a specific user or all users"""
    global _tenant_cache
    if user_id:
        _tenant_cache.pop(user_id, None)
    else:
        _tenant_cache = {}


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically inject tenant context into requests.
    
    Extracts user_id from X-User-ID header, looks up enterprise_id,
    and makes both available via request.state.
    
    For personal users (no enterprise), enterprise_id will be None.
    """
    
    def __init__(self, app: ASGIApp, db=None):
        super().__init__(app)
        self.db = db
        
    def set_db(self, db):
        """Set database instance (called from server.py)"""
        self.db = db
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and inject tenant context.
        
        Sets on request.state:
        - user_id: The authenticated user's ID (or None)
        - enterprise_id: The user's enterprise/tenant ID (or None for personal users)
        - is_enterprise_user: Boolean indicating if user belongs to enterprise
        """
        # Initialize default state
        request.state.user_id = None
        request.state.enterprise_id = None
        request.state.is_enterprise_user = False
        
        # Skip tenant injection for certain paths
        skip_paths = [
            "/api/health",
            "/api/auth/login",
            "/api/auth/signup",
            "/api/auth/refresh",
            "/api/auth/forgot-password",
            "/api/auth/reset-password",
            "/api/auth/verify",
            "/api/oauth",
            "/api/sso",
            "/docs",
            "/openapi.json",
            "/api/webhooks",
            "/api/subscriptions/webhook",
        ]
        
        path = request.url.path
        if any(path.startswith(skip_path) for skip_path in skip_paths):
            return await call_next(request)
        
        # Extract user_id from header
        user_id = request.headers.get("X-User-ID")
        
        if user_id:
            request.state.user_id = user_id
            
            # Check cache first
            cached = _get_cached_enterprise_id(user_id)
            if cached is not None:
                enterprise_id, _ = cached
                request.state.enterprise_id = enterprise_id
                request.state.is_enterprise_user = enterprise_id is not None
                logger.debug(f"Tenant context (cached): user={user_id}, enterprise={enterprise_id}")
            elif self.db is not None:
                # Look up enterprise_id from database
                try:
                    user = await self.db.users.find_one(
                        {"id": user_id},
                        {"_id": 0, "enterprise_id": 1}
                    )
                    if user:
                        enterprise_id = user.get("enterprise_id")
                        request.state.enterprise_id = enterprise_id
                        request.state.is_enterprise_user = enterprise_id is not None
                        # Cache the result
                        _cache_enterprise_id(user_id, enterprise_id)
                        logger.debug(f"Tenant context: user={user_id}, enterprise={enterprise_id}")
                except Exception as e:
                    logger.warning(f"Error looking up tenant context: {e}")
        
        response = await call_next(request)
        return response


# =============================================================================
# TENANT CONTEXT DEPENDENCY
# =============================================================================

class TenantContext:
    """
    Tenant context object available via dependency injection.
    
    Usage in routes:
        from middleware.tenant import get_tenant_context, TenantContext
        
        @router.get("/items")
        async def get_items(tenant: TenantContext = Depends(get_tenant_context)):
            if tenant.enterprise_id:
                # Enterprise user - filter by tenant
                query = {"enterprise_id": tenant.enterprise_id}
            else:
                # Personal user - filter by user only
                query = {"user_id": tenant.user_id}
    """
    
    def __init__(self, user_id: Optional[str], enterprise_id: Optional[str]):
        self.user_id = user_id
        self.enterprise_id = enterprise_id
        self.is_enterprise_user = enterprise_id is not None
    
    def get_tenant_filter(self, include_user: bool = True) -> dict:
        """
        Get the appropriate filter for database queries.
        
        Args:
            include_user: If True, includes user_id in filter for enterprise users
            
        Returns:
            dict: MongoDB query filter
        """
        if self.enterprise_id:
            if include_user and self.user_id:
                return {"enterprise_id": self.enterprise_id, "user_id": self.user_id}
            return {"enterprise_id": self.enterprise_id}
        elif self.user_id:
            return {"user_id": self.user_id}
        return {}
    
    def get_enterprise_filter(self) -> dict:
        """
        Get filter for enterprise-wide queries (no user filter).
        Used for queries that should return all data within an enterprise.
        
        Returns:
            dict: MongoDB query filter for enterprise-wide access
        """
        if self.enterprise_id:
            return {"enterprise_id": self.enterprise_id}
        elif self.user_id:
            # Personal users see only their own data
            return {"user_id": self.user_id}
        return {}
    
    def add_tenant_to_document(self, document: dict) -> dict:
        """
        Add tenant fields to a document before insertion.
        
        Args:
            document: The document to modify
            
        Returns:
            dict: Document with tenant fields added
        """
        if self.enterprise_id:
            document["enterprise_id"] = self.enterprise_id
        if self.user_id:
            document["user_id"] = self.user_id
        return document


async def get_tenant_context(request: Request) -> TenantContext:
    """
    FastAPI dependency to get tenant context.
    
    Usage:
        @router.get("/items")
        async def get_items(
            tenant: TenantContext = Depends(get_tenant_context),
            db_conn: AsyncIOMotorDatabase = Depends(get_db)
        ):
            query = tenant.get_tenant_filter()
            items = await db_conn.items.find(query, {"_id": 0}).to_list(100)
            return items
    """
    user_id = getattr(request.state, "user_id", None)
    enterprise_id = getattr(request.state, "enterprise_id", None)
    return TenantContext(user_id, enterprise_id)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def build_tenant_query(
    request: Request,
    base_query: dict = None,
    include_user: bool = True,
    enterprise_wide: bool = False
) -> dict:
    """
    Build a tenant-aware query from request context.
    
    Args:
        request: FastAPI Request object
        base_query: Additional query filters to merge
        include_user: Include user_id filter for enterprise users
        enterprise_wide: If True, don't filter by user_id (for admin views)
        
    Returns:
        dict: Complete MongoDB query with tenant filters
    """
    query = base_query.copy() if base_query else {}
    
    enterprise_id = getattr(request.state, "enterprise_id", None)
    user_id = getattr(request.state, "user_id", None)
    
    if enterprise_id:
        query["enterprise_id"] = enterprise_id
        if include_user and not enterprise_wide and user_id:
            query["user_id"] = user_id
    elif user_id:
        query["user_id"] = user_id
    
    return query


def ensure_tenant_fields(request: Request, document: dict) -> dict:
    """
    Ensure tenant fields are present in a document.
    
    Args:
        request: FastAPI Request object
        document: Document to be inserted
        
    Returns:
        dict: Document with tenant fields ensured
    """
    enterprise_id = getattr(request.state, "enterprise_id", None)
    user_id = getattr(request.state, "user_id", None)
    
    if enterprise_id and "enterprise_id" not in document:
        document["enterprise_id"] = enterprise_id
    if user_id and "user_id" not in document:
        document["user_id"] = user_id
    
    return document
