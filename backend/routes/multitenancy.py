"""
Multi-Tenancy Administration Routes (ARCH-009, ARCH-008)

Provides API endpoints for:
- Migration management (run, status, rollback)
- Schema validation
- Tenant isolation status
- Data integrity checks

All endpoints require super_admin role.
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Header
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db

# Import RBAC decorator
from services.authorization_decorator import require_permission

# Import tenant services
from services.tenant_isolation_service import (
    get_tenant_service,
    TENANT_ISOLATED_COLLECTIONS,
    GLOBAL_COLLECTIONS,
)
from services.schema_validation_service import get_schema_service
from services.migration_service import get_migration_service

# Import tenant context
from middleware.tenant import get_tenant_context, TenantContext

router = APIRouter(prefix="/multitenancy", tags=["multitenancy"])
logger = logging.getLogger(__name__)


# =============================================================================
# MIGRATION ENDPOINTS
# =============================================================================

@router.get("/migrations/status")
@require_permission("system.manage")
async def get_migration_status(
    request: Request,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get current migration status.
    
    Returns information about applied and pending migrations.
    Requires super_admin role.
    """
    try:
        migration_service = get_migration_service()
        migration_service.set_db(db_conn)
        status = await migration_service.get_migration_status()
        return {
            "status": "success",
            "data": status
        }
    except Exception as e:
        logger.error(f"Error getting migration status: {e}")
        raise HTTPException(500, f"Failed to get migration status: {str(e)}")


@router.post("/migrations/run")
@require_permission("system.manage")
async def run_migrations(
    request: Request,
    dry_run: bool = False,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Run all pending migrations.
    
    Args:
        dry_run: If true, only report what would be done without executing
        
    Requires super_admin role.
    """
    try:
        migration_service = get_migration_service()
        migration_service.set_db(db_conn)
        result = await migration_service.run_migrations(dry_run=dry_run)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        raise HTTPException(500, f"Failed to run migrations: {str(e)}")


@router.post("/migrations/rollback/{version}")
@require_permission("system.manage")
async def rollback_migration(
    request: Request,
    version: str,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Rollback a specific migration.
    
    Args:
        version: Version of the migration to rollback
        
    Requires super_admin role.
    """
    try:
        migration_service = get_migration_service()
        migration_service.set_db(db_conn)
        result = await migration_service.rollback_migration(version)
        
        if not result.get("success"):
            raise HTTPException(400, result.get("error", "Rollback failed"))
        
        return {
            "status": "success",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rolling back migration: {e}")
        raise HTTPException(500, f"Failed to rollback migration: {str(e)}")


# =============================================================================
# SCHEMA VALIDATION ENDPOINTS
# =============================================================================

@router.get("/schema/status")
@require_permission("system.manage")
async def get_schema_status(
    request: Request,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get schema validation status for all collections.
    
    Returns information about which collections have schema validation enabled.
    Requires super_admin role.
    """
    try:
        schema_service = get_schema_service()
        schema_service.set_db(db_conn)
        
        # Get list of collections
        collections = await db_conn.list_collection_names()
        
        status = {
            "total_collections": len(collections),
            "tenant_isolated": [],
            "global": [],
            "other": []
        }
        
        for collection in collections:
            schema = await schema_service.get_collection_schema(collection)
            collection_info = {
                "name": collection,
                "has_schema": schema is not None,
                "schema": schema
            }
            
            if collection in TENANT_ISOLATED_COLLECTIONS:
                status["tenant_isolated"].append(collection_info)
            elif collection in GLOBAL_COLLECTIONS:
                status["global"].append(collection_info)
            else:
                status["other"].append(collection_info)
        
        return {
            "status": "success",
            "data": status
        }
    except Exception as e:
        logger.error(f"Error getting schema status: {e}")
        raise HTTPException(500, f"Failed to get schema status: {str(e)}")


@router.post("/schema/apply")
@require_permission("system.manage")
async def apply_schemas(
    request: Request,
    validation_level: str = "moderate",
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Apply schema validation to all configured collections.
    
    Args:
        validation_level: "strict" or "moderate" (default: moderate)
        
    Requires super_admin role.
    """
    try:
        if validation_level not in ["strict", "moderate"]:
            raise HTTPException(400, "validation_level must be 'strict' or 'moderate'")
        
        schema_service = get_schema_service()
        schema_service.set_db(db_conn)
        results = await schema_service.apply_all_schemas(validation_level)
        
        successful = [k for k, v in results.items() if v]
        failed = [k for k, v in results.items() if not v]
        
        return {
            "status": "success",
            "data": {
                "validation_level": validation_level,
                "successful_count": len(successful),
                "failed_count": len(failed),
                "successful": successful,
                "failed": failed
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying schemas: {e}")
        raise HTTPException(500, f"Failed to apply schemas: {str(e)}")


# =============================================================================
# TENANT ISOLATION ENDPOINTS
# =============================================================================

@router.get("/tenant/status")
@require_permission("system.manage")
async def get_tenant_status(
    request: Request,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get tenant isolation status and statistics.
    
    Returns:
    - Collection configuration
    - Documents missing enterprise_id
    - Tenant statistics
    
    Requires super_admin role.
    """
    try:
        tenant_service = get_tenant_service()
        tenant_service.set_db(db_conn)
        
        status = {
            "configuration": {
                "tenant_isolated_collections": TENANT_ISOLATED_COLLECTIONS,
                "global_collections": GLOBAL_COLLECTIONS,
            },
            "statistics": {},
            "missing_enterprise_id": {}
        }
        
        # Check each tenant-isolated collection
        for collection_name in TENANT_ISOLATED_COLLECTIONS:
            try:
                collection = db_conn[collection_name]
                
                # Total documents
                total = await collection.count_documents({})
                
                # Documents with enterprise_id
                with_enterprise = await collection.count_documents({
                    "enterprise_id": {"$exists": True, "$ne": None}
                })
                
                # Documents missing enterprise_id
                missing = await collection.count_documents({
                    "$or": [
                        {"enterprise_id": {"$exists": False}},
                        {"enterprise_id": None}
                    ]
                })
                
                status["statistics"][collection_name] = {
                    "total_documents": total,
                    "with_enterprise_id": with_enterprise,
                    "missing_enterprise_id": missing,
                    "isolation_percentage": round((with_enterprise / total * 100) if total > 0 else 100, 1)
                }
                
                if missing > 0:
                    status["missing_enterprise_id"][collection_name] = missing
                    
            except Exception as e:
                logger.warning(f"Error checking collection {collection_name}: {e}")
                status["statistics"][collection_name] = {"error": str(e)}
        
        return {
            "status": "success",
            "data": status
        }
    except Exception as e:
        logger.error(f"Error getting tenant status: {e}")
        raise HTTPException(500, f"Failed to get tenant status: {str(e)}")


@router.post("/tenant/backfill")
@require_permission("system.manage")
async def backfill_enterprise_ids(
    request: Request,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Backfill enterprise_id on documents missing the field.
    
    Looks up each document's user_id and sets enterprise_id based on
    the user's enterprise membership.
    
    Requires super_admin role.
    """
    try:
        schema_service = get_schema_service()
        schema_service.set_db(db_conn)
        
        results = await schema_service.ensure_tenant_fields()
        
        total_updated = sum(v for v in results.values() if isinstance(v, int) and v > 0)
        errors = {k: v for k, v in results.items() if v == -1}
        
        return {
            "status": "success",
            "data": {
                "total_updated": total_updated,
                "collections": results,
                "errors": errors
            }
        }
    except Exception as e:
        logger.error(f"Error backfilling enterprise IDs: {e}")
        raise HTTPException(500, f"Failed to backfill enterprise IDs: {str(e)}")


@router.get("/tenant/context")
async def get_current_tenant_context(
    request: Request,
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Get the current request's tenant context.
    
    Useful for debugging and verifying tenant isolation is working.
    Available to all authenticated users.
    """
    return {
        "status": "success",
        "data": {
            "user_id": tenant.user_id,
            "enterprise_id": tenant.enterprise_id,
            "is_enterprise_user": tenant.is_enterprise_user,
            "tenant_filter": tenant.get_tenant_filter(),
            "enterprise_filter": tenant.get_enterprise_filter()
        }
    }


# =============================================================================
# DATA INTEGRITY ENDPOINTS
# =============================================================================

@router.get("/integrity/check")
@require_permission("system.manage")
async def check_data_integrity(
    request: Request,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Run data integrity checks on tenant-isolated collections.
    
    Checks for:
    - Documents with invalid user_id references
    - Documents with invalid enterprise_id references
    - Orphaned documents
    
    Requires super_admin role.
    """
    try:
        issues = []
        
        # Get valid user IDs and enterprise IDs
        valid_user_ids = set()
        valid_enterprise_ids = set()
        
        async for user in db_conn.users.find({}, {"_id": 0, "id": 1}):
            valid_user_ids.add(user["id"])
        
        async for enterprise in db_conn.enterprises.find({}, {"_id": 0, "id": 1}):
            valid_enterprise_ids.add(enterprise["id"])
        
        # Check each tenant-isolated collection
        for collection_name in TENANT_ISOLATED_COLLECTIONS[:5]:  # Limit for performance
            try:
                collection = db_conn[collection_name]
                
                # Sample documents with invalid user_id
                invalid_users = await collection.find(
                    {
                        "user_id": {"$exists": True, "$nin": list(valid_user_ids)}
                    },
                    {"_id": 0, "id": 1, "user_id": 1}
                ).limit(10).to_list(10)
                
                if invalid_users:
                    issues.append({
                        "collection": collection_name,
                        "issue_type": "invalid_user_id",
                        "count": len(invalid_users),
                        "sample_ids": [d.get("id") for d in invalid_users]
                    })
                
                # Sample documents with invalid enterprise_id
                invalid_enterprises = await collection.find(
                    {
                        "enterprise_id": {"$exists": True, "$ne": None, "$nin": list(valid_enterprise_ids)}
                    },
                    {"_id": 0, "id": 1, "enterprise_id": 1}
                ).limit(10).to_list(10)
                
                if invalid_enterprises:
                    issues.append({
                        "collection": collection_name,
                        "issue_type": "invalid_enterprise_id",
                        "count": len(invalid_enterprises),
                        "sample_ids": [d.get("id") for d in invalid_enterprises]
                    })
                    
            except Exception as e:
                logger.warning(f"Error checking collection {collection_name}: {e}")
        
        return {
            "status": "success",
            "data": {
                "issues_found": len(issues),
                "issues": issues,
                "valid_user_count": len(valid_user_ids),
                "valid_enterprise_count": len(valid_enterprise_ids),
                "collections_checked": min(5, len(TENANT_ISOLATED_COLLECTIONS))
            }
        }
    except Exception as e:
        logger.error(f"Error checking data integrity: {e}")
        raise HTTPException(500, f"Failed to check data integrity: {str(e)}")


@router.get("/tenant/audit-logs")
@require_permission("system.manage")
async def get_tenant_audit_logs(
    request: Request,
    limit: int = 50,
    enterprise_id: Optional[str] = None,
    operation: Optional[str] = None,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get tenant audit logs.
    
    Args:
        limit: Maximum number of logs to return (default: 50, max: 200)
        enterprise_id: Filter by enterprise ID
        operation: Filter by operation type
        
    Requires super_admin role.
    """
    try:
        # Build query
        query = {}
        if enterprise_id:
            query["enterprise_id"] = enterprise_id
        if operation:
            query["operation"] = operation
        
        # Limit to max 200
        actual_limit = min(limit, 200)
        
        logs = await db_conn.tenant_audit_logs.find(
            query,
            {"_id": 0}
        ).sort("timestamp", -1).limit(actual_limit).to_list(actual_limit)
        
        return {
            "status": "success",
            "data": {
                "logs": logs,
                "count": len(logs),
                "limit": actual_limit
            }
        }
    except Exception as e:
        logger.error(f"Error getting tenant audit logs: {e}")
        raise HTTPException(500, f"Failed to get audit logs: {str(e)}")
