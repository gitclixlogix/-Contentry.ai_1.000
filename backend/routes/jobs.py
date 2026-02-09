"""
Background Jobs API

Provides REST endpoints and WebSocket support for job management.
This enables async processing of long-running operations with real-time updates.

RBAC Protected: Phase 5.1c Week 7
All endpoints require appropriate settings.* or admin.* permissions

Endpoints:
- GET /jobs - List user's jobs
- GET /jobs/{job_id} - Get job status
- GET /jobs/{job_id}/result - Get job result
- DELETE /jobs/{job_id} - Cancel a job
- WS /ws/jobs/{job_id} - Real-time job updates
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, Query, Header, Request
from typing import Optional, List
from datetime import datetime, timezone
import logging
import asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase

from services.database import get_db
from services.job_queue_service import (
    get_job_queue_service,
    JobStatus,
    TaskType,
    Job
)
# RBAC decorator
from services.authorization_decorator import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


# ==================== REST Endpoints ====================

@router.get("")
@require_permission("settings.view")
async def list_jobs(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum jobs to return"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    List jobs for the current user.
    
    Args:
        user_id: Current user ID
        task_type: Optional filter by task type
        status: Optional filter by status
        limit: Maximum number of jobs to return
        
    Returns:
        List of jobs with their current status
    """
    job_service = get_job_queue_service()
    job_service.set_db(db_conn)
    
    # Convert string to enum if provided
    task_type_enum = TaskType(task_type) if task_type else None
    status_enum = JobStatus(status) if status else None
    
    jobs = await job_service.get_user_jobs(
        user_id=user_id,
        task_type=task_type_enum,
        status=status_enum,
        limit=limit
    )
    
    return {
        "jobs": [job.to_dict() for job in jobs],
        "count": len(jobs)
    }


@router.get("/{job_id}")
@require_permission("settings.view")
async def get_job_status(
    request: Request,
    job_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get the current status of a job.
    
    Args:
        job_id: Job identifier
        user_id: Current user ID
        
    Returns:
        Job status, progress, and metadata
    """
    job_service = get_job_queue_service()
    job_service.set_db(db_conn)
    
    job = await job_service.get_job(job_id, user_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job.to_dict()


@router.get("/{job_id}/result")
@require_permission("settings.view")
async def get_job_result(
    request: Request,
    job_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get the result of a completed job.
    
    Args:
        job_id: Job identifier
        user_id: Current user ID
        
    Returns:
        Job result data if completed, or current status if not
    """
    job_service = get_job_queue_service()
    job_service.set_db(db_conn)
    
    job = await job_service.get_job(job_id, user_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status == JobStatus.COMPLETED:
        return {
            "job_id": job_id,
            "status": job.status.value,
            "result": job.result,
            "completed_at": job.completed_at
        }
    elif job.status == JobStatus.FAILED:
        return {
            "job_id": job_id,
            "status": job.status.value,
            "error": job.error,
            "error_details": job.error_details,
            "completed_at": job.completed_at
        }
    else:
        return {
            "job_id": job_id,
            "status": job.status.value,
            "progress": {
                "current_step": job.progress.current_step,
                "total_steps": job.progress.total_steps,
                "current_step_num": job.progress.current_step_num,
                "percentage": job.progress.percentage,
                "message": job.progress.message
            } if job.progress else None,
            "message": "Job is still processing"
        }


@router.delete("/{job_id}")
@require_permission("settings.view")
async def cancel_job(
    request: Request,
    job_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Cancel a running job.
    
    Args:
        job_id: Job identifier
        user_id: Current user ID
        
    Returns:
        Cancellation confirmation
    """
    job_service = get_job_queue_service()
    job_service.set_db(db_conn)
    
    success = await job_service.cancel_job(job_id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=400, 
            detail="Unable to cancel job. It may be already completed, failed, or cancelled."
        )
    
    return {
        "job_id": job_id,
        "status": "cancelled",
        "message": "Job has been cancelled"
    }


# ==================== WebSocket Endpoint ====================

@router.websocket("/ws/{job_id}")
async def job_websocket(
    websocket: WebSocket,
    job_id: str,
    user_id: Optional[str] = None,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    WebSocket endpoint for real-time job status updates.
    
    Connect to receive real-time updates as the job progresses.
    The connection will automatically close when the job completes or fails.
    
    Message format (sent from server):
    {
        "type": "status_update" | "progress_update" | "connected" | "error",
        "job_id": "...",
        "status": "pending" | "processing" | "completed" | "failed" | "cancelled",
        "progress": {
            "current_step": "...",
            "total_steps": 5,
            "current_step_num": 2,
            "percentage": 40,
            "message": "..."
        },
        "result": {...},  // Only on completion
        "error": "..."    // Only on failure
    }
    """
    # Accept the connection
    await websocket.accept()
    
    job_service = get_job_queue_service()
    job_service.set_db(db_conn)
    
    try:
        # Verify job exists and user has access
        job = await job_service.get_job(job_id, user_id)
        
        if not job:
            await websocket.send_json({
                "type": "error",
                "message": "Job not found",
                "job_id": job_id
            })
            await websocket.close()
            return
        
        # Send initial status
        await websocket.send_json({
            "type": "connected",
            "job_id": job_id,
            "status": job.status.value,
            "progress": {
                "current_step": job.progress.current_step,
                "total_steps": job.progress.total_steps,
                "current_step_num": job.progress.current_step_num,
                "percentage": job.progress.percentage,
                "message": job.progress.message
            } if job.progress else None,
            "message": "Connected to job status stream"
        })
        
        # If job is already complete, send result and close
        if job.status == JobStatus.COMPLETED:
            await websocket.send_json({
                "type": "status_update",
                "job_id": job_id,
                "status": "completed",
                "result": job.result
            })
            await websocket.close()
            return
        elif job.status in [JobStatus.FAILED, JobStatus.CANCELLED]:
            await websocket.send_json({
                "type": "status_update",
                "job_id": job_id,
                "status": job.status.value,
                "error": job.error
            })
            await websocket.close()
            return
        
        # Register for updates
        job_service.register_websocket(job_id, websocket)
        
        # Keep connection alive and handle client messages
        try:
            while True:
                # Wait for client messages (ping/pong, etc.)
                try:
                    data = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=30.0  # 30 second timeout
                    )
                    
                    # Handle ping
                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    
                    # Handle status request
                    elif data.get("type") == "get_status":
                        job = await job_service.get_job(job_id, user_id)
                        if job:
                            await websocket.send_json({
                                "type": "status_update",
                                "job_id": job_id,
                                "status": job.status.value,
                                "progress": {
                                    "current_step": job.progress.current_step,
                                    "total_steps": job.progress.total_steps,
                                    "current_step_num": job.progress.current_step_num,
                                    "percentage": job.progress.percentage,
                                    "message": job.progress.message
                                } if job.progress else None,
                                "result": job.result if job.status == JobStatus.COMPLETED else None,
                                "error": job.error if job.status == JobStatus.FAILED else None
                            })
                            
                            # Close if job is done
                            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                                await websocket.close()
                                return
                                
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await websocket.send_json({"type": "ping"})
                    
                    # Check job status
                    job = await job_service.get_job(job_id, user_id)
                    if job and job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                        # Send final status and close
                        await websocket.send_json({
                            "type": "status_update",
                            "job_id": job_id,
                            "status": job.status.value,
                            "result": job.result if job.status == JobStatus.COMPLETED else None,
                            "error": job.error if job.status == JobStatus.FAILED else None
                        })
                        await websocket.close()
                        return
                        
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for job {job_id}")
            
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
                "job_id": job_id
            })
        except Exception:
            pass
            
    finally:
        # Unregister websocket
        job_service.unregister_websocket(job_id, websocket)


# ==================== Admin/Cleanup Endpoints ====================

@router.post("/cleanup")
@require_permission("admin.manage")
async def cleanup_old_jobs(
    request: Request,
    retention_days: int = Query(7, ge=1, le=30, description="Days to retain jobs"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Clean up old completed/failed jobs.
    
    Args:
        retention_days: Number of days to retain jobs (default: 7)
        
    Returns:
        Cleanup result
    """
    job_service = get_job_queue_service()
    job_service.set_db(db_conn)
    
    await job_service.cleanup_old_jobs(retention_days)
    
    return {
        "message": f"Cleaned up jobs older than {retention_days} days",
        "retention_days": retention_days
    }


@router.get("/stats")
@require_permission("settings.view")
async def get_job_stats(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get job statistics for the current user.
    
    Returns:
        Statistics about user's jobs by status and type
    """
    # Aggregate job counts by status
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": {"status": "$status", "task_type": "$task_type"},
            "count": {"$sum": 1}
        }}
    ]
    
    results = await db_conn.background_jobs.aggregate(pipeline).to_list(100)
    
    # Organize results
    by_status = {}
    by_type = {}
    
    for r in results:
        status = r["_id"]["status"]
        task_type = r["_id"]["task_type"]
        count = r["count"]
        
        by_status[status] = by_status.get(status, 0) + count
        by_type[task_type] = by_type.get(task_type, 0) + count
    
    total = sum(by_status.values())
    
    return {
        "total_jobs": total,
        "by_status": by_status,
        "by_type": by_type
    }
