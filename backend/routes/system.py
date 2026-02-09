"""
Circuit Breaker and Feature Flags API Routes (ARCH-003, ARCH-018)

Provides endpoints for:
- Monitoring circuit breaker status
- Managing feature flags
- Health checks with service status

RBAC Protected: Phase 5.1c Week 8
All endpoints require appropriate admin.* or settings.* permissions
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Request
from typing import Optional
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase

from services.database import get_db
from services.circuit_breaker_service import (
    get_all_circuits_status,
    get_circuit_status,
    reset_circuit,
    trip_circuit,
    CircuitOpenError,
    ServiceUnavailableError
)
from services.feature_flags_service import (
    get_feature_flags_service,
    is_feature_enabled,
    set_feature_flag,
    get_all_feature_flags,
    FeatureFlag
)
# RBAC decorator
from services.authorization_decorator import require_permission

router = APIRouter(prefix="/system", tags=["system"])


# ============================================================
# Circuit Breaker Endpoints
# ============================================================

@router.get("/circuits")
@require_permission("admin.view")
async def get_circuits_status(request: Request):
    """
    Get status of all circuit breakers.
    
    Returns:
        Circuit breaker states, metrics, and summary
    """
    return get_all_circuits_status()


@router.get("/circuits/{service_name}")
@require_permission("admin.view")
async def get_service_circuit_status(request: Request, service_name: str):
    """
    Get status of a specific circuit breaker.
    
    Args:
        service_name: Name of the service (openai, stripe, etc.)
    """
    status = get_circuit_status(service_name)
    if status.get("state") == "not_initialized":
        raise HTTPException(status_code=404, detail=f"Circuit breaker '{service_name}' not found")
    return status


@router.post("/circuits/{service_name}/reset")
@require_permission("admin.manage")
async def reset_service_circuit(
    request: Request,
    service_name: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Manually reset a circuit breaker to closed state.
    Requires admin privileges.
    
    Args:
        service_name: Name of the service to reset
    """
    # Ensure circuit exists before trying to reset it
    from services.circuit_breaker_service import get_or_create_circuit
    await get_or_create_circuit(service_name)
    
    success = await reset_circuit(service_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Circuit breaker '{service_name}' not found")
    
    return {
        "success": True,
        "message": f"Circuit breaker '{service_name}' reset to CLOSED",
        "status": get_circuit_status(service_name)
    }


@router.post("/circuits/{service_name}/trip")
@require_permission("admin.manage")
async def trip_service_circuit(
    request: Request,
    service_name: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Manually trip (open) a circuit breaker.
    Useful for maintenance or known outages.
    
    Args:
        service_name: Name of the service to trip
    """
    # Ensure circuit exists before trying to trip it
    from services.circuit_breaker_service import get_or_create_circuit
    await get_or_create_circuit(service_name)
    
    success = await trip_circuit(service_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Circuit breaker '{service_name}' not found")
    
    return {
        "success": True,
        "message": f"Circuit breaker '{service_name}' tripped to OPEN",
        "status": get_circuit_status(service_name)
    }


# ============================================================
# Feature Flags Endpoints
# ============================================================

@router.get("/features")
@require_permission("admin.view")
async def get_features(request: Request):
    """
    Get all feature flags and their current states.
    """
    return {
        "features": get_all_feature_flags(),
        "categories": ["AI", "Social", "Payments", "Media", "System", "Beta"]
    }


@router.get("/features/{feature_name}")
@require_permission("admin.view")
async def get_feature_status(
    request: Request,
    feature_name: str,
    user_id: Optional[str] = None
):
    """
    Check if a specific feature is enabled.
    
    Args:
        feature_name: Name of the feature
        user_id: Optional user ID for user-specific checks
    """
    try:
        flag = FeatureFlag(feature_name)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown feature: {feature_name}. Valid features: {[f.value for f in FeatureFlag]}"
        )
    
    enabled = await is_feature_enabled(flag, user_id)
    
    return {
        "feature": feature_name,
        "enabled": enabled,
        "user_id": user_id
    }


class SetFeatureRequest(BaseModel):
    enabled: bool
    reason: Optional[str] = None


@router.put("/features/{feature_name}")
@require_permission("admin.manage")
async def update_feature_flag(
    http_request: Request,
    feature_name: str,
    request: SetFeatureRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Enable or disable a feature flag.
    Requires admin privileges.
    
    Args:
        feature_name: Name of the feature
        enabled: Whether to enable or disable
        reason: Reason for the change
    """
    try:
        flag = FeatureFlag(feature_name)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown feature: {feature_name}"
        )
    
    success = await set_feature_flag(flag, request.enabled, request.reason, x_user_id)
    
    return {
        "success": success,
        "feature": feature_name,
        "enabled": request.enabled,
        "reason": request.reason
    }


# ============================================================
# Health Check with Service Status
# ============================================================

@router.get("/health")
@require_permission("admin.view")
async def system_health(request: Request):
    """
    Comprehensive system health check including all external services.
    """
    circuits_status = get_all_circuits_status()
    features = get_all_feature_flags()
    
    # Determine overall health
    degraded = circuits_status["summary"]["degraded"]
    open_services = circuits_status["summary"]["open_services"]
    
    # Calculate feature availability
    disabled_features = [f for f, data in features.items() if not data["enabled"]]
    
    # Overall status
    if len(open_services) >= 3:
        status = "critical"
    elif degraded:
        status = "degraded"
    else:
        status = "healthy"
    
    return {
        "status": status,
        "circuits": {
            "summary": circuits_status["summary"],
            "open_services": open_services
        },
        "features": {
            "total": len(features),
            "enabled": len(features) - len(disabled_features),
            "disabled": disabled_features
        },
        "message": _get_health_message(status, open_services, disabled_features)
    }


def _get_health_message(status: str, open_services: list, disabled_features: list) -> str:
    """Generate health status message"""
    if status == "healthy":
        return "All systems operational"
    elif status == "degraded":
        issues = []
        if open_services:
            issues.append(f"Services experiencing issues: {', '.join(open_services)}")
        if disabled_features:
            issues.append(f"Features disabled: {', '.join(disabled_features[:3])}")
        return "; ".join(issues)
    else:  # critical
        return f"Multiple services down: {', '.join(open_services)}. Some functionality unavailable."


# ============================================================
# Service Availability Check for Frontend
# ============================================================

@router.get("/availability")
@require_permission("settings.view")
async def check_service_availability(request: Request):
    """
    Quick availability check for frontend to determine which features to show.
    Returns a simple map of feature -> available status.
    """
    features = get_all_feature_flags()
    circuits_status = get_all_circuits_status()
    
    availability = {}
    for feature_name, feature_data in features.items():
        # Feature is available if enabled AND all dependent circuits are not open
        available = feature_data["enabled"]
        
        if available and feature_data.get("dependent_circuits"):
            for circuit in feature_data["dependent_circuits"]:
                circuit_info = circuits_status["circuits"].get(circuit, {})
                if circuit_info.get("state") == "open":
                    available = False
                    break
        
        availability[feature_name] = {
            "available": available,
            "reason": None if available else "Service temporarily unavailable"
        }
    
    return {
        "availability": availability,
        "degraded": circuits_status["summary"]["degraded"]
    }
