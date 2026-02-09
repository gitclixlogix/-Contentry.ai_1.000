"""
Tenant Isolation Service (ARCH-009)

Provides comprehensive multi-tenant data isolation capabilities.
Ensures enterprise data is properly separated at the database level.

Features:
- Tenant-aware database operations
- Query interceptors for automatic tenant filtering
- Data validation to prevent cross-tenant access
- Audit logging for tenant operations
"""

import logging
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timezone
from functools import wraps
from fastapi import Request, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

logger = logging.getLogger(__name__)

# =============================================================================
# COLLECTION CONFIGURATION
# =============================================================================

# Collections that require tenant (enterprise_id) isolation
TENANT_ISOLATED_COLLECTIONS = [
    "posts",
    "content_analyses",
    "policies",
    "scheduled_prompts",
    "generated_content",
    "strategic_profiles",
    "projects",
    "project_content",
    "conversation_memory",
    "analysis_feedback",
    "media_analyses",
    "team_invitations",
    "approval_workflows",
    "pending_approvals",
    "custom_roles",
    "social_profiles",
    "social_posts",
    "draft_posts",
    "knowledge_entries",
    "user_knowledge",
    "dashboard_configs",
    "notifications",
    "in_app_notifications",
]

# Collections that should NOT have tenant filtering (global collections)
GLOBAL_COLLECTIONS = [
    "users",
    "enterprises",
    "subscriptions",
    "payment_transactions",
    "credit_grants",
    "webhook_events",
    "idempotency_records",
    "rate_limit_records",
    "authorization_logs",
    "system_settings",
    "feature_flags",
    "circuit_breaker_states",
    "changelog_entries",
    "migrations",
]

# Collections where user_id is the primary filter (personal data)
USER_SCOPED_COLLECTIONS = [
    "user_preferences",
    "user_sessions",
    "password_reset_tokens",
    "verification_tokens",
    "oauth_tokens",
]


# =============================================================================
# TENANT ISOLATION SERVICE
# =============================================================================

class TenantIsolationService:
    """
    Service for enforcing multi-tenant data isolation.
    
    Provides methods for:
    - Building tenant-aware queries
    - Validating tenant access
    - Adding tenant context to documents
    - Audit logging
    """
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db
        self._audit_enabled = True
    
    def set_db(self, db: AsyncIOMotorDatabase):
        """Set database instance"""
        self.db = db
    
    def is_tenant_isolated_collection(self, collection_name: str) -> bool:
        """Check if a collection requires tenant isolation"""
        return collection_name in TENANT_ISOLATED_COLLECTIONS
    
    def is_global_collection(self, collection_name: str) -> bool:
        """Check if a collection is global (no tenant filtering)"""
        return collection_name in GLOBAL_COLLECTIONS
    
    def build_tenant_query(
        self,
        collection_name: str,
        enterprise_id: Optional[str],
        user_id: Optional[str],
        base_query: dict = None,
        include_user_filter: bool = True,
        enterprise_wide: bool = False
    ) -> dict:
        """
        Build a tenant-aware query for a collection.
        
        Args:
            collection_name: Name of the MongoDB collection
            enterprise_id: The tenant/enterprise ID
            user_id: The user ID
            base_query: Additional query filters
            include_user_filter: Whether to include user_id in filter
            enterprise_wide: If True, don't filter by user_id (for team views)
            
        Returns:
            dict: MongoDB query with appropriate tenant filters
        """
        query = base_query.copy() if base_query else {}
        
        # Global collections don't need tenant filtering
        if self.is_global_collection(collection_name):
            return query
        
        # User-scoped collections filter by user_id only
        if collection_name in USER_SCOPED_COLLECTIONS:
            if user_id:
                query["user_id"] = user_id
            return query
        
        # Tenant-isolated collections
        if self.is_tenant_isolated_collection(collection_name):
            if enterprise_id:
                query["enterprise_id"] = enterprise_id
                # Also filter by user unless enterprise_wide access
                if include_user_filter and not enterprise_wide and user_id:
                    query["user_id"] = user_id
            elif user_id:
                # Personal user - filter by user_id only
                # Also check for null/missing enterprise_id to prevent data leaks
                query["user_id"] = user_id
                query["$or"] = [
                    {"enterprise_id": {"$exists": False}},
                    {"enterprise_id": None}
                ]
        elif user_id:
            # Unknown collection - default to user filtering
            query["user_id"] = user_id
        
        return query
    
    def prepare_document_for_insert(
        self,
        collection_name: str,
        document: dict,
        enterprise_id: Optional[str],
        user_id: Optional[str]
    ) -> dict:
        """
        Prepare a document for insertion with tenant fields.
        
        Args:
            collection_name: Name of the MongoDB collection
            document: The document to insert
            enterprise_id: The tenant/enterprise ID
            user_id: The user ID
            
        Returns:
            dict: Document with tenant fields added
        """
        # Don't modify global collections
        if self.is_global_collection(collection_name):
            return document
        
        # Add tenant fields for isolated collections
        if self.is_tenant_isolated_collection(collection_name):
            if enterprise_id and "enterprise_id" not in document:
                document["enterprise_id"] = enterprise_id
        
        # Add user_id if not present
        if user_id and "user_id" not in document:
            document["user_id"] = user_id
        
        return document
    
    async def validate_tenant_access(
        self,
        collection_name: str,
        document_id: str,
        enterprise_id: Optional[str],
        user_id: Optional[str],
        id_field: str = "id"
    ) -> bool:
        """
        Validate that a user has access to a specific document.
        
        Args:
            collection_name: Name of the MongoDB collection
            document_id: The document's ID
            enterprise_id: The user's enterprise ID
            user_id: The user's ID
            id_field: Field name for the document ID (default: "id")
            
        Returns:
            bool: True if access is allowed, False otherwise
        """
        if self.db is None:
            logger.warning("Database not set for tenant isolation service")
            return False
        
        collection = self.db[collection_name]
        
        # Build query to check access
        query = {id_field: document_id}
        query = self.build_tenant_query(
            collection_name,
            enterprise_id,
            user_id,
            query,
            include_user_filter=True
        )
        
        document = await collection.find_one(query, {"_id": 0, id_field: 1})
        return document is not None
    
    async def log_tenant_operation(
        self,
        operation: str,
        collection_name: str,
        enterprise_id: Optional[str],
        user_id: Optional[str],
        document_id: Optional[str] = None,
        details: dict = None
    ) -> None:
        """
        Log a tenant-related operation for audit purposes.
        
        Args:
            operation: The operation type (read, write, delete, etc.)
            collection_name: The collection being accessed
            enterprise_id: The tenant ID
            user_id: The user ID
            document_id: Optional document ID
            details: Additional details to log
        """
        if not self._audit_enabled or self.db is None:
            return
        
        try:
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "operation": operation,
                "collection": collection_name,
                "enterprise_id": enterprise_id,
                "user_id": user_id,
                "document_id": document_id,
                "details": details or {}
            }
            await self.db.tenant_audit_logs.insert_one(log_entry)
        except Exception as e:
            logger.warning(f"Failed to log tenant operation: {e}")


# =============================================================================
# TENANT-AWARE DECORATORS
# =============================================================================

def require_tenant_isolation(collection_name: str):
    """
    Decorator to enforce tenant isolation on route handlers.
    
    Usage:
        @router.get("/posts")
        @require_tenant_isolation("posts")
        async def get_posts(request: Request, ...):
            # request.state.tenant_query contains the tenant filter
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request in args or kwargs
            request = kwargs.get('request')
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if not request:
                raise HTTPException(500, "Request object not found")
            
            # Get tenant context
            enterprise_id = getattr(request.state, "enterprise_id", None)
            user_id = getattr(request.state, "user_id", None)
            
            # Build tenant query and attach to request
            service = TenantIsolationService()
            request.state.tenant_query = service.build_tenant_query(
                collection_name,
                enterprise_id,
                user_id
            )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_tenant_service: Optional[TenantIsolationService] = None


def get_tenant_service() -> TenantIsolationService:
    """Get the global tenant isolation service instance"""
    global _tenant_service
    if _tenant_service is None:
        _tenant_service = TenantIsolationService()
    return _tenant_service


def init_tenant_service(db: AsyncIOMotorDatabase) -> TenantIsolationService:
    """Initialize the tenant isolation service with database"""
    global _tenant_service
    _tenant_service = TenantIsolationService(db)
    return _tenant_service
