"""
Secrets Management Routes (ARCH-010)

Provides API endpoints for secrets management status and administration.

NOTE: These endpoints only provide status information and do NOT expose
actual secret values for security reasons.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db

# Import RBAC decorator
from services.authorization_decorator import require_permission

# Import secrets manager
from services.secrets_manager_service import (
    get_secrets_manager,
    MANAGED_SECRETS,
    mask_secret,
)

router = APIRouter(prefix="/secrets", tags=["secrets"])
logger = logging.getLogger(__name__)


# =============================================================================
# STATUS ENDPOINTS
# =============================================================================

@router.get("/status")
@require_permission("system.manage")
async def get_secrets_status(
    request: Request,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get the current status of the secrets manager.
    
    Returns information about:
    - AWS availability
    - Cache status
    - Statistics
    - Managed secrets list
    
    NOTE: Does not expose actual secret values.
    
    Requires super_admin role.
    """
    try:
        secrets_manager = get_secrets_manager()
        status = secrets_manager.get_status()
        
        return {
            "status": "success",
            "data": status
        }
    except Exception as e:
        logger.error(f"Error getting secrets status: {e}")
        raise HTTPException(500, f"Failed to get secrets status: {str(e)}")


@router.get("/health")
@require_permission("system.manage")
async def secrets_health_check(
    request: Request,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Perform a health check on the secrets manager.
    
    Verifies that all required secrets are available.
    
    Requires super_admin role.
    """
    try:
        secrets_manager = get_secrets_manager()
        health = secrets_manager.health_check()
        
        return {
            "status": "success",
            "data": health
        }
    except Exception as e:
        logger.error(f"Error checking secrets health: {e}")
        raise HTTPException(500, f"Failed to check secrets health: {str(e)}")


@router.get("/validate")
@require_permission("system.manage")
async def validate_secrets_configuration(
    request: Request,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Validate the secrets configuration.
    
    Checks each configured secret and reports its status.
    
    NOTE: Does not expose actual secret values.
    
    Requires super_admin role.
    """
    try:
        secrets_manager = get_secrets_manager()
        validation = secrets_manager.validate_configuration()
        
        return {
            "status": "success",
            "data": validation
        }
    except Exception as e:
        logger.error(f"Error validating secrets: {e}")
        raise HTTPException(500, f"Failed to validate secrets: {str(e)}")


# =============================================================================
# CACHE MANAGEMENT
# =============================================================================

@router.post("/cache/invalidate")
@require_permission("system.manage")
async def invalidate_secrets_cache(
    request: Request,
    secret_name: Optional[str] = None,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Invalidate the secrets cache.
    
    Args:
        secret_name: Optional specific secret to invalidate.
                     If not provided, invalidates all cached secrets.
    
    Requires super_admin role.
    """
    try:
        secrets_manager = get_secrets_manager()
        secrets_manager.invalidate_cache(secret_name)
        
        return {
            "status": "success",
            "message": f"Cache invalidated for {'all secrets' if not secret_name else secret_name}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(500, f"Failed to invalidate cache: {str(e)}")


@router.post("/cache/refresh/{secret_name}")
@require_permission("system.manage")
async def refresh_secret(
    request: Request,
    secret_name: str,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Force refresh a specific secret from the source.
    
    This invalidates the cache and fetches a fresh value.
    
    NOTE: Does not expose the actual secret value.
    
    Requires super_admin role.
    """
    try:
        if secret_name not in MANAGED_SECRETS:
            raise HTTPException(404, f"Unknown secret: {secret_name}")
        
        secrets_manager = get_secrets_manager()
        value = secrets_manager.refresh_secret(secret_name)
        
        return {
            "status": "success",
            "data": {
                "secret_name": secret_name,
                "available": value is not None,
                "masked_preview": mask_secret(value) if value else None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing secret: {e}")
        raise HTTPException(500, f"Failed to refresh secret: {str(e)}")


# =============================================================================
# AUDIT LOG
# =============================================================================

@router.get("/audit-log")
@require_permission("system.manage")
async def get_secrets_audit_log(
    request: Request,
    limit: int = 100,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get the secrets access audit log.
    
    Returns recent secret access events (cached in memory).
    
    Args:
        limit: Maximum number of entries to return (default: 100, max: 500)
    
    Requires super_admin role.
    """
    try:
        secrets_manager = get_secrets_manager()
        actual_limit = min(limit, 500)
        audit_log = secrets_manager.get_audit_log(actual_limit)
        
        return {
            "status": "success",
            "data": {
                "entries": audit_log,
                "count": len(audit_log),
                "limit": actual_limit
            }
        }
    except Exception as e:
        logger.error(f"Error getting audit log: {e}")
        raise HTTPException(500, f"Failed to get audit log: {str(e)}")


# =============================================================================
# DEFINITIONS
# =============================================================================

@router.get("/definitions")
@require_permission("system.manage")
async def get_secret_definitions(
    request: Request,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get all secret definitions.
    
    Returns the configuration for all managed secrets
    (without exposing actual values).
    
    Requires super_admin role.
    """
    try:
        definitions = [
            {
                "name": config.name,
                "aws_secret_name": config.aws_secret_name,
                "env_var_name": config.env_var_name,
                "required": config.required,
                "rotatable": config.rotatable,
                "description": config.description,
            }
            for config in MANAGED_SECRETS.values()
        ]
        
        return {
            "status": "success",
            "data": {
                "count": len(definitions),
                "definitions": definitions
            }
        }
    except Exception as e:
        logger.error(f"Error getting definitions: {e}")
        raise HTTPException(500, f"Failed to get definitions: {str(e)}")


# =============================================================================
# ROTATION WEBHOOK
# =============================================================================

@router.post("/rotation/webhook")
async def handle_rotation_webhook(
    request: Request,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Handle secret rotation webhooks from AWS.
    
    This endpoint should be called by AWS Lambda or SNS
    when a secret is rotated.
    
    Expected payload:
    {
        "secret_name": "contentry/openai/api-key",
        "version_id": "abc123",
        "event_type": "rotation"
    }
    
    NOTE: In production, this should be secured with
    AWS IAM authentication or a webhook secret.
    """
    try:
        body = await request.json()
        
        secret_name = body.get("secret_name")
        version_id = body.get("version_id")
        event_type = body.get("event_type")
        
        if not secret_name or not version_id:
            raise HTTPException(400, "Missing secret_name or version_id")
        
        if event_type != "rotation":
            return {
                "status": "ignored",
                "message": f"Event type '{event_type}' not handled"
            }
        
        # Find the internal secret name from AWS name
        internal_name = None
        for name, config in MANAGED_SECRETS.items():
            if config.aws_secret_name == secret_name:
                internal_name = name
                break
        
        if not internal_name:
            logger.warning(f"Unknown AWS secret name in rotation webhook: {secret_name}")
            return {
                "status": "ignored",
                "message": f"Unknown secret: {secret_name}"
            }
        
        # Handle the rotation
        secrets_manager = get_secrets_manager()
        secrets_manager.handle_rotation_event(internal_name, version_id)
        
        return {
            "status": "success",
            "message": f"Rotation handled for {internal_name}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling rotation webhook: {e}")
        raise HTTPException(500, f"Failed to handle rotation: {str(e)}")
