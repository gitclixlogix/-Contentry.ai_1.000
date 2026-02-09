"""
Documentation Screenshot Scheduler

Automated background service that periodically refreshes documentation screenshots.
Uses APScheduler for task scheduling and runs independently of the main API server.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from motor.motor_asyncio import AsyncIOMotorClient

from services.documentation.screenshot_service import (
    ScreenshotService,
    SCREENSHOT_CONFIG
)

logger = logging.getLogger(__name__)

# Configuration
SCREENSHOT_REFRESH_INTERVAL_HOURS = int(os.environ.get('SCREENSHOT_REFRESH_HOURS', '24'))
SCREENSHOT_REFRESH_ENABLED = os.environ.get('SCREENSHOT_REFRESH_ENABLED', 'true').lower() == 'true'


class DocumentationScreenshotScheduler:
    """
    Background scheduler for documentation screenshot updates.
    
    Features:
    - Automatic periodic refresh of all documentation screenshots
    - Configurable refresh interval via environment variables
    - Health monitoring and status tracking
    - Graceful error handling with retry logic
    """
    
    def __init__(self, db):
        self.db = db
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.screenshot_service: Optional[ScreenshotService] = None
        self.is_running = False
        self.last_run_status = None
    
    async def initialize(self):
        """Initialize the screenshot service and scheduler."""
        try:
            # Initialize screenshot service
            self.screenshot_service = ScreenshotService(self.db)
            
            # Initialize APScheduler
            self.scheduler = AsyncIOScheduler(
                timezone='UTC',
                job_defaults={
                    'coalesce': True,  # Combine missed runs
                    'max_instances': 1,  # Only one instance at a time
                    'misfire_grace_time': 3600  # Allow 1 hour grace for missed jobs
                }
            )
            
            logger.info("Documentation screenshot scheduler initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize screenshot scheduler: {e}")
            return False
    
    async def _refresh_screenshots_job(self):
        """
        Background job that refreshes all documentation screenshots.
        This runs periodically based on SCREENSHOT_REFRESH_INTERVAL_HOURS.
        """
        job_start = datetime.now(timezone.utc)
        logger.info(f"Starting scheduled screenshot refresh at {job_start.isoformat()}")
        
        try:
            # Update status to "in_progress"
            await self.db.documentation_meta.update_one(
                {"type": "screenshot_scheduler"},
                {
                    "$set": {
                        "status": "in_progress",
                        "current_job_started": job_start
                    }
                },
                upsert=True
            )
            
            # Capture all screenshots
            results = await self.screenshot_service.capture_all_screenshots()
            
            job_end = datetime.now(timezone.utc)
            duration_seconds = (job_end - job_start).total_seconds()
            
            # Update status
            self.last_run_status = {
                "status": "completed",
                "started_at": job_start,
                "completed_at": job_end,
                "duration_seconds": duration_seconds,
                "success_count": len(results.get("success", [])),
                "failed_count": len(results.get("failed", [])),
                "results": results
            }
            
            await self.db.documentation_meta.update_one(
                {"type": "screenshot_scheduler"},
                {
                    "$set": {
                        "status": "completed",
                        "last_successful_run": job_end,
                        "last_run_duration_seconds": duration_seconds,
                        "last_run_results": self.last_run_status
                    }
                },
                upsert=True
            )
            
            logger.info(
                f"Screenshot refresh completed: {len(results.get('success', []))} success, "
                f"{len(results.get('failed', []))} failed in {duration_seconds:.1f}s"
            )
            
        except Exception as e:
            logger.error(f"Screenshot refresh job failed: {e}")
            
            await self.db.documentation_meta.update_one(
                {"type": "screenshot_scheduler"},
                {
                    "$set": {
                        "status": "error",
                        "last_error": str(e),
                        "last_error_at": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
            
            self.last_run_status = {
                "status": "error",
                "error": str(e),
                "started_at": job_start,
                "failed_at": datetime.now(timezone.utc)
            }
    
    def start(self):
        """Start the background scheduler."""
        if not SCREENSHOT_REFRESH_ENABLED:
            logger.info("Screenshot refresh scheduler is disabled via SCREENSHOT_REFRESH_ENABLED=false")
            return False
        
        if self.is_running:
            logger.warning("Screenshot scheduler is already running")
            return True
        
        try:
            # Schedule periodic refresh job
            self.scheduler.add_job(
                self._refresh_screenshots_job,
                trigger=IntervalTrigger(hours=SCREENSHOT_REFRESH_INTERVAL_HOURS),
                id='screenshot_refresh',
                name='Documentation Screenshot Refresh',
                replace_existing=True
            )
            
            # Also schedule a daily refresh at 3 AM UTC (off-peak hours)
            self.scheduler.add_job(
                self._refresh_screenshots_job,
                trigger=CronTrigger(hour=3, minute=0),
                id='screenshot_refresh_daily',
                name='Daily Screenshot Refresh (3 AM UTC)',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            
            logger.info(
                f"Screenshot scheduler started. "
                f"Refresh interval: {SCREENSHOT_REFRESH_INTERVAL_HOURS} hours. "
                f"Daily refresh at 3:00 AM UTC."
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to start screenshot scheduler: {e}")
            return False
    
    def stop(self):
        """Stop the background scheduler."""
        if not self.is_running:
            logger.warning("Screenshot scheduler is not running")
            return
        
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("Screenshot scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping screenshot scheduler: {e}")
    
    async def trigger_refresh_now(self):
        """Manually trigger an immediate screenshot refresh."""
        logger.info("Manual screenshot refresh triggered")
        await self._refresh_screenshots_job()
    
    async def get_status(self) -> dict:
        """Get the current scheduler status."""
        status_doc = await self.db.documentation_meta.find_one(
            {"type": "screenshot_scheduler"},
            {"_id": 0}
        )
        
        next_run = None
        if self.scheduler and self.is_running:
            job = self.scheduler.get_job('screenshot_refresh')
            if job:
                next_run = job.next_run_time.isoformat() if job.next_run_time else None
        
        return {
            "enabled": SCREENSHOT_REFRESH_ENABLED,
            "is_running": self.is_running,
            "refresh_interval_hours": SCREENSHOT_REFRESH_INTERVAL_HOURS,
            "next_scheduled_run": next_run,
            "last_run": status_doc.get("last_run_results") if status_doc else None,
            "status": status_doc.get("status") if status_doc else "never_run"
        }
    
    async def get_screenshot_health(self) -> dict:
        """Get health status of all screenshots."""
        screenshots = await self.db.documentation_screenshots.find(
            {},
            {"_id": 0, "id": 1, "captured_at": 1, "name": 1}
        ).to_list(100)
        
        now = datetime.now(timezone.utc)
        stale_threshold_hours = SCREENSHOT_REFRESH_INTERVAL_HOURS * 2  # 2x interval = stale
        
        health = {
            "total_configured": len(SCREENSHOT_CONFIG),
            "captured": len(screenshots),
            "missing": [],
            "stale": [],
            "fresh": []
        }
        
        captured_ids = {s["id"] for s in screenshots}
        
        for page_id, config in SCREENSHOT_CONFIG.items():
            if page_id not in captured_ids:
                health["missing"].append({
                    "id": page_id,
                    "name": config["name"]
                })
            else:
                screenshot = next(s for s in screenshots if s["id"] == page_id)
                captured_at = screenshot.get("captured_at")
                
                if captured_at:
                    # Handle both timezone-aware and naive datetimes
                    if captured_at.tzinfo is None:
                        from datetime import timezone as tz
                        captured_at = captured_at.replace(tzinfo=tz.utc)
                    
                    age_hours = (now - captured_at).total_seconds() / 3600
                    
                    if age_hours > stale_threshold_hours:
                        health["stale"].append({
                            "id": page_id,
                            "name": screenshot.get("name"),
                            "age_hours": round(age_hours, 1)
                        })
                    else:
                        health["fresh"].append({
                            "id": page_id,
                            "name": screenshot.get("name"),
                            "age_hours": round(age_hours, 1)
                        })
        
        return health


# Singleton instance
_scheduler_instance: Optional[DocumentationScreenshotScheduler] = None


def get_screenshot_scheduler(db) -> DocumentationScreenshotScheduler:
    """Get or create the singleton scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = DocumentationScreenshotScheduler(db)
    return _scheduler_instance


async def start_screenshot_scheduler(db):
    """Initialize and start the screenshot scheduler."""
    scheduler = get_screenshot_scheduler(db)
    await scheduler.initialize()
    scheduler.start()
    return scheduler
