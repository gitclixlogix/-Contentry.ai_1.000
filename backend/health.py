"""
Health Check Endpoints for Load Balancer and Monitoring
Provides liveness, readiness, and detailed health status
"""

from fastapi import APIRouter, Depends
from datetime import datetime, timezone
import psutil
import os
from motor.motor_asyncio import AsyncIOMotorDatabase
from services.database import get_db
from middleware.api_cache import get_cache_stats

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Basic health check for load balancer.
    Returns 200 if the service is running.
    """
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes liveness probe.
    Returns 200 if the process is alive.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_check(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Kubernetes readiness probe.
    Returns 200 if the service can accept traffic.
    Checks database connectivity.
    """
    try:
        # Check MongoDB connection
        await db.command("ping")
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "not_ready", "database": "disconnected", "error": str(e)}, 503


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Detailed health check for monitoring dashboards.
    Returns comprehensive system status.
    """
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Database check
    db_status = "connected"
    db_latency_ms = None
    try:
        start = datetime.now(timezone.utc)
        await db.command("ping")
        db_latency_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Process info
    process = psutil.Process()
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "uptime_seconds": (datetime.now(timezone.utc) - datetime.fromtimestamp(process.create_time(), timezone.utc)).total_seconds(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
        },
        "process": {
            "pid": process.pid,
            "memory_mb": round(process.memory_info().rss / (1024**2), 2),
            "threads": process.num_threads(),
            "open_files": len(process.open_files()),
            "connections": len(process.connections()),
        },
        "database": {
            "status": db_status,
            "latency_ms": round(db_latency_ms, 2) if db_latency_ms else None,
        },
        "cache": get_cache_stats(),
        "dependencies": {
            "mongodb": db_status == "connected",
            "redis": get_cache_stats().get("status") == "connected",
        }
    }
