"""
Roles Module - Audit Endpoints
==============================
API endpoints for viewing and exporting audit logs.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Query
from fastapi.responses import Response

from services.role_service import role_service
from .helpers import get_user_and_enterprise, check_admin_access

router = APIRouter(tags=["audit"])


@router.get("/audit")
async def get_audit_log(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    action: Optional[str] = Query(None, description="Filter by action type"),
    actor: Optional[str] = Query(None, description="Filter by actor user ID"),
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """
    Get the permission audit log for the enterprise.
    """
    user, enterprise_id = await get_user_and_enterprise(x_user_id)
    await check_admin_access(user)
    
    result = await role_service.get_audit_log(
        enterprise_id=enterprise_id,
        page=page,
        limit=limit,
        action_filter=action,
        actor_filter=actor
    )
    
    return result


@router.get("/audit/export")
async def export_audit_log(
    format: str = Query("json", description="Export format: 'json' or 'csv'"),
    start_date: Optional[str] = Query(None, description="Filter entries after this date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter entries before this date (ISO format)"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    actor: Optional[str] = Query(None, description="Filter by actor user ID"),
    limit: int = Query(10000, ge=1, le=50000, description="Maximum entries to export"),
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """
    Export the permission audit log in JSON or CSV format.
    """
    user, enterprise_id = await get_user_and_enterprise(x_user_id)
    await check_admin_access(user)
    
    # Validate format
    if format not in ["json", "csv"]:
        raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
    
    result = await role_service.export_audit_log(
        enterprise_id=enterprise_id,
        format=format,
        start_date=start_date,
        end_date=end_date,
        action_filter=action,
        actor_filter=actor,
        limit=limit
    )
    
    # Return CSV as downloadable file
    if format == "csv":
        csv_content = result.get("csv_content", "")
        filename = f"audit_log_export_{enterprise_id}_{result['export_timestamp'][:10]}.csv"
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    # Return JSON response
    return result


@router.get("/audit/statistics")
async def get_audit_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """
    Get audit log statistics for the enterprise.
    """
    user, enterprise_id = await get_user_and_enterprise(x_user_id)
    await check_admin_access(user)
    
    result = await role_service.get_audit_statistics(
        enterprise_id=enterprise_id,
        days=days
    )
    
    return result
