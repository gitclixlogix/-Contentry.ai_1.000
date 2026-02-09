"""
Observability Routes (ARCH-006, ARCH-016)

Provides API endpoints for monitoring, metrics, and SLO tracking.

Endpoints:
- GET /api/observability/metrics - Current system metrics
- GET /api/observability/slos - SLO compliance status
- GET /api/observability/slos/{name} - Specific SLO status
- GET /api/observability/health - Health check with metrics
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

# Import observability services
from services.tracing_service import get_metrics_collector
from services.slo_service import get_slo_service
from middleware.correlation import get_correlation_id

router = APIRouter(prefix="/observability", tags=["observability"])
logger = logging.getLogger(__name__)


# =============================================================================
# METRICS ENDPOINTS
# =============================================================================

@router.get("/metrics")
@require_permission("system.manage")
async def get_metrics(
    request: Request,
    operation: Optional[str] = None,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get current system metrics.
    
    Args:
        operation: Optional operation name to filter metrics
        
    Returns:
        dict: Current metrics for all or specific operations
        
    Requires super_admin role.
    """
    try:
        metrics = get_metrics_collector()
        
        if operation:
            stats = metrics.get_stats(operation)
            return {
                "status": "success",
                "data": {
                    "operation": operation,
                    "metrics": stats,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
        else:
            all_stats = metrics.get_all_stats()
            return {
                "status": "success",
                "data": {
                    "operations": all_stats,
                    "operation_count": len(all_stats),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(500, f"Failed to get metrics: {str(e)}")


@router.post("/metrics/reset")
@require_permission("system.manage")
async def reset_metrics(
    request: Request,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Reset all metrics.
    
    USE WITH CAUTION: This clears all collected metrics data.
    
    Requires super_admin role.
    """
    try:
        metrics = get_metrics_collector()
        metrics.reset()
        
        return {
            "status": "success",
            "message": "All metrics have been reset",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error resetting metrics: {e}")
        raise HTTPException(500, f"Failed to reset metrics: {str(e)}")


# =============================================================================
# SLO ENDPOINTS
# =============================================================================

@router.get("/slos")
@require_permission("system.manage")
async def get_all_slos(
    request: Request,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get SLO compliance status for all defined SLOs.
    
    Returns:
        dict: Overall SLO status and individual SLO compliance
        
    Requires super_admin role.
    """
    try:
        slo_service = get_slo_service()
        slo_service.set_db(db_conn)
        
        status = slo_service.check_all_slos()
        
        return {
            "status": "success",
            "data": status
        }
    except Exception as e:
        logger.error(f"Error getting SLO status: {e}")
        raise HTTPException(500, f"Failed to get SLO status: {str(e)}")


@router.get("/slos/definitions")
@require_permission("system.manage")
async def get_slo_definitions(
    request: Request,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get all SLO definitions.
    
    Returns:
        list: All defined SLOs with their configuration
        
    Requires super_admin role.
    """
    try:
        slo_service = get_slo_service()
        
        definitions = [
            {
                "name": slo.name,
                "operation": slo.operation,
                "type": slo.slo_type.value,
                "target": slo.target,
                "threshold": slo.threshold,
                "unit": slo.unit,
                "description": slo.description,
                "critical": slo.critical,
            }
            for slo in slo_service.get_all_slos()
        ]
        
        return {
            "status": "success",
            "data": {
                "slo_count": len(definitions),
                "definitions": definitions
            }
        }
    except Exception as e:
        logger.error(f"Error getting SLO definitions: {e}")
        raise HTTPException(500, f"Failed to get SLO definitions: {str(e)}")


@router.post("/slos/snapshot")
@require_permission("system.manage")
async def record_slo_snapshot(
    request: Request,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Record current SLO status snapshot to database.
    
    This is typically called by a scheduled job, but can be
    triggered manually for immediate recording.
    
    Requires super_admin role.
    """
    try:
        slo_service = get_slo_service()
        slo_service.set_db(db_conn)
        
        await slo_service.record_slo_snapshot()
        
        return {
            "status": "success",
            "message": "SLO snapshot recorded",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error recording SLO snapshot: {e}")
        raise HTTPException(500, f"Failed to record SLO snapshot: {str(e)}")


@router.get("/slos/{slo_name}")
@require_permission("system.manage")
async def get_slo_status(
    request: Request,
    slo_name: str,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get compliance status for a specific SLO.
    
    Args:
        slo_name: Name of the SLO to check
        
    Returns:
        dict: SLO compliance details
        
    Requires super_admin role.
    """
    try:
        slo_service = get_slo_service()
        slo_service.set_db(db_conn)
        
        status = slo_service.check_slo_compliance(slo_name)
        
        if "error" in status:
            raise HTTPException(404, status["error"])
        
        return {
            "status": "success",
            "data": status
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting SLO status: {e}")
        raise HTTPException(500, f"Failed to get SLO status: {str(e)}")


@router.get("/slos/{slo_name}/history")
@require_permission("system.manage")
async def get_slo_history(
    request: Request,
    slo_name: str,
    hours: int = 24,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get historical data for a specific SLO.
    
    Args:
        slo_name: Name of the SLO
        hours: Number of hours of history (default: 24)
        
    Returns:
        list: Historical SLO snapshots
        
    Requires super_admin role.
    """
    try:
        slo_service = get_slo_service()
        slo_service.set_db(db_conn)
        
        # Verify SLO exists
        slo = slo_service.get_slo(slo_name)
        if not slo:
            raise HTTPException(404, f"SLO '{slo_name}' not found")
        
        history = await slo_service.get_slo_history(slo_name, hours)
        
        return {
            "status": "success",
            "data": {
                "slo_name": slo_name,
                "hours": hours,
                "snapshots": history
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting SLO history: {e}")
        raise HTTPException(500, f"Failed to get SLO history: {str(e)}")


# =============================================================================
# HEALTH ENDPOINTS
# =============================================================================

@router.get("/health")
async def observability_health(
    request: Request,
):
    """
    Health check endpoint with basic observability metrics.
    
    This endpoint is public and doesn't require authentication.
    It's designed for load balancer health checks.
    """
    try:
        correlation_id = get_correlation_id(request)
        metrics = get_metrics_collector()
        
        # Get API request metrics
        api_stats = metrics.get_stats("api_request")
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id,
            "metrics_summary": {
                "total_requests": api_stats.get("total_requests", 0),
                "success_rate": api_stats.get("success_rate_percent"),
                "p95_latency_ms": api_stats.get("latency_p95_ms"),
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/trace-info")
async def get_trace_info(
    request: Request,
):
    """
    Get current request trace information.
    
    Useful for debugging and verifying correlation ID propagation.
    """
    return {
        "correlation_id": get_correlation_id(request),
        "user_id": getattr(request.state, "user_id", None),
        "enterprise_id": getattr(request.state, "enterprise_id", None),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
