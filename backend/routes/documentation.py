"""
Documentation API Routes

Provides endpoints for managing documentation screenshots, workflow GIFs, and changelog.

RBAC Protected: Phase 5.1c Week 8
All endpoints require appropriate documentation.* permissions
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Header, Depends, Request
from pydantic import BaseModel

from services.documentation.screenshot_service import (
    get_screenshot_service,
    SCREENSHOT_CONFIG
)
from services.documentation.screenshot_scheduler import (
    get_screenshot_scheduler,
    start_screenshot_scheduler
)
from services.documentation.workflow_gif_service import (
    get_workflow_service,
    WORKFLOW_CONFIG
)
from services.documentation.changelog_service import (
    get_changelog_service,
    MONITORED_PAGES
)
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db
# RBAC decorator
from services.authorization_decorator import require_permission

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/documentation", tags=["documentation"])

# Database reference
db = None

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    """Set the database reference."""
    global db
    db = database


class RefreshResponse(BaseModel):
    message: str
    task_id: Optional[str] = None
    status: str


class ScreenshotMetadata(BaseModel):
    id: str
    name: str
    description: str
    path: str
    section: str
    guide: str
    captured_at: Optional[str] = None
    url: Optional[str] = None


# Background task tracking
_refresh_tasks = {}


async def _background_refresh_all():
    """Background task to refresh all screenshots."""
    service = get_screenshot_service(db)
    try:
        results = await service.capture_all_screenshots()
        logger.info(f"Screenshot refresh complete: {len(results['success'])} success, {len(results['failed'])} failed")
    except Exception as e:
        logger.error(f"Screenshot refresh failed: {e}")


async def _background_refresh_single(page_id: str):
    """Background task to refresh a single screenshot."""
    service = get_screenshot_service(db)
    try:
        result = await service.capture_screenshot(page_id)
        if result:
            logger.info(f"Screenshot refreshed: {page_id}")
        else:
            logger.error(f"Screenshot refresh failed: {page_id}")
    except Exception as e:
        logger.error(f"Screenshot refresh failed for {page_id}: {e}")


@router.get("/screenshots")
@require_permission("documentation.view")
async def list_screenshots(request: Request):
    """
    List all available documentation screenshots.
    Returns metadata without image data.
    """
    service = get_screenshot_service(db)
    screenshots = await service.get_all_screenshots()
    
    # Add config info for any missing screenshots
    all_pages = []
    captured_ids = {s["id"] for s in screenshots}
    
    for page_id, config in SCREENSHOT_CONFIG.items():
        if page_id in captured_ids:
            # Find the captured screenshot
            captured = next(s for s in screenshots if s["id"] == page_id)
            all_pages.append({
                **captured,
                "status": "captured",
                "captured_at": captured.get("captured_at", "").isoformat() if captured.get("captured_at") else None
            })
        else:
            all_pages.append({
                "id": page_id,
                "name": config["name"],
                "description": config["description"],
                "path": config["path"],
                "section": config["section"],
                "guide": config["guide"],
                "status": "pending",
                "captured_at": None
            })
    
    return {
        "screenshots": all_pages,
        "total": len(all_pages),
        "captured": len(captured_ids)
    }


@router.get("/screenshots/status")
@require_permission("documentation.view")
async def get_refresh_status(request: Request):
    """
    Get the status of the last screenshot refresh operation.
    """
    service = get_screenshot_service(db)
    status = await service.get_last_refresh_status()
    
    if not status:
        return {
            "status": "never_run",
            "last_refresh": None,
            "results": None
        }
    
    return {
        "status": "completed",
        "last_refresh": status.get("last_refresh", "").isoformat() if status.get("last_refresh") else None,
        "results": status.get("results")
    }


@router.get("/screenshots/{page_id}")
async def get_screenshot(request: Request, page_id: str):
    """
    Get a specific screenshot by page ID.
    Returns full screenshot data including base64 image.
    Public endpoint - no authentication required for viewing documentation.
    """
    if page_id not in SCREENSHOT_CONFIG:
        raise HTTPException(status_code=404, detail=f"Unknown page: {page_id}")
    
    service = get_screenshot_service(db)
    screenshot = await service.get_screenshot(page_id)
    
    if not screenshot:
        # Return config without image if not yet captured
        config = SCREENSHOT_CONFIG[page_id]
        return {
            "id": page_id,
            "name": config["name"],
            "description": config["description"],
            "path": config["path"],
            "section": config["section"],
            "guide": config["guide"],
            "status": "not_captured",
            "image_data": None,
            "captured_at": None
        }
    
    return {
        **screenshot,
        "status": "captured",
        "captured_at": screenshot.get("captured_at", "").isoformat() if screenshot.get("captured_at") else None
    }


@router.get("/screenshots/guide/{guide}")
@require_permission("documentation.view")
async def get_screenshots_by_guide(request: Request, guide: str):
    """
    Get all screenshots for a specific guide (admin, enterprise, user, about).
    """
    if guide not in ["admin", "enterprise", "user", "about"]:
        raise HTTPException(status_code=400, detail="Invalid guide type")
    
    service = get_screenshot_service(db)
    screenshots = await service.get_screenshots_by_guide(guide)
    
    # Also get pending screenshots for this guide
    guide_configs = [
        {**config, "id": pid, "status": "pending", "captured_at": None}
        for pid, config in SCREENSHOT_CONFIG.items()
        if config["guide"] == guide
    ]
    
    captured_ids = {s["id"] for s in screenshots}
    result = []
    
    for config in guide_configs:
        if config["id"] in captured_ids:
            captured = next(s for s in screenshots if s["id"] == config["id"])
            result.append({
                **captured,
                "status": "captured"
            })
        else:
            result.append(config)
    
    return {"screenshots": result, "guide": guide}


@router.post("/screenshots/refresh")
@require_permission("documentation.manage")
async def refresh_all_screenshots(request: Request, background_tasks: BackgroundTasks):
    """
    Trigger a refresh of all documentation screenshots.
    Runs in background to avoid timeout.
    """
    background_tasks.add_task(_background_refresh_all)
    
    return RefreshResponse(
        message="Screenshot refresh started",
        status="in_progress"
    )


@router.post("/screenshots/refresh/{page_id}")
@require_permission("documentation.manage")
async def refresh_screenshot(request: Request, page_id: str, background_tasks: BackgroundTasks):
    """
    Refresh a specific screenshot.
    """
    if page_id not in SCREENSHOT_CONFIG:
        raise HTTPException(status_code=404, detail=f"Unknown page: {page_id}")
    
    background_tasks.add_task(_background_refresh_single, page_id)
    
    return RefreshResponse(
        message=f"Screenshot refresh started for {page_id}",
        status="in_progress"
    )


@router.get("/config")
@require_permission("documentation.view")
async def get_documentation_config(request: Request):
    """
    Get the documentation configuration including all page definitions.
    """
    return {
        "pages": [
            {
                "id": page_id,
                **config
            }
            for page_id, config in SCREENSHOT_CONFIG.items()
        ],
        "guides": ["about", "admin", "enterprise", "user"]
    }



@router.get("/scheduler/status")
@require_permission("documentation.view")
async def get_scheduler_status(request: Request):
    """
    Get the status of the background screenshot scheduler.
    """
    scheduler = get_screenshot_scheduler(db)
    return await scheduler.get_status()


@router.get("/scheduler/health")
@require_permission("documentation.view")
async def get_screenshot_health(request: Request):
    """
    Get health status of documentation screenshots.
    Shows missing, stale, and fresh screenshots.
    """
    scheduler = get_screenshot_scheduler(db)
    return await scheduler.get_screenshot_health()


@router.post("/scheduler/trigger")
@require_permission("documentation.manage")
async def trigger_scheduler_refresh(request: Request, background_tasks: BackgroundTasks):
    """
    Manually trigger an immediate screenshot refresh via the scheduler.
    """
    scheduler = get_screenshot_scheduler(db)
    
    if not scheduler.is_running:
        # Initialize if not running
        await scheduler.initialize()
    
    background_tasks.add_task(scheduler.trigger_refresh_now)
    
    return RefreshResponse(
        message="Screenshot refresh triggered via scheduler",
        status="in_progress"
    )



# ============================================================================
# WORKFLOW GIF ENDPOINTS
# ============================================================================

@router.get("/workflows")
@require_permission("documentation.view")
async def get_all_workflows(request: Request):
    """
    Get all available workflows (recorded and unrecorded).
    """
    service = get_workflow_service(db)
    workflows = await service.get_all_workflows()
    
    return {
        "workflows": workflows,
        "total": len(workflows),
        "configured": len(WORKFLOW_CONFIG)
    }


@router.get("/workflows/{workflow_id}")
@require_permission("documentation.view")
async def get_workflow(request: Request, workflow_id: str):
    """
    Get a specific workflow GIF by ID.
    Returns the base64-encoded GIF data.
    """
    service = get_workflow_service(db)
    workflow = await service.get_workflow(workflow_id)
    
    if not workflow:
        # Check if workflow is configured but not recorded
        if workflow_id in WORKFLOW_CONFIG:
            config = WORKFLOW_CONFIG[workflow_id]
            return {
                "id": workflow_id,
                "name": config["name"],
                "description": config["description"],
                "section": config["section"],
                "guide": config["guide"],
                "status": "not_recorded",
                "message": "Workflow configured but not yet recorded. Use POST /workflows/{workflow_id}/record to capture."
            }
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    
    return workflow


@router.post("/workflows/{workflow_id}/record")
@require_permission("documentation.manage")
async def record_workflow(request: Request, workflow_id: str, background_tasks: BackgroundTasks):
    """
    Record a specific workflow as an animated GIF.
    This process runs in the background and may take 10-15 seconds.
    """
    if workflow_id not in WORKFLOW_CONFIG:
        raise HTTPException(status_code=404, detail=f"Unknown workflow: {workflow_id}")
    
    service = get_workflow_service(db)
    
    # Record in background
    async def _record():
        await service.initialize()
        result = await service.record_workflow(workflow_id)
        await service.cleanup()
        logger.info(f"Workflow recording completed: {workflow_id} - {result}")
    
    background_tasks.add_task(_record)
    
    config = WORKFLOW_CONFIG[workflow_id]
    return RefreshResponse(
        message=f"Recording workflow: {config['name']}. This may take up to 15 seconds.",
        task_id=workflow_id,
        status="recording"
    )


@router.post("/workflows/record-all")
@require_permission("documentation.manage")
async def record_all_workflows(request: Request, background_tasks: BackgroundTasks):
    """
    Record all configured workflows as animated GIFs.
    """
    service = get_workflow_service(db)
    
    async def _record_all():
        await service.initialize()
        results = await service.record_all_workflows()
        await service.cleanup()
        logger.info(f"All workflow recordings completed: {results}")
    
    background_tasks.add_task(_record_all)
    
    return RefreshResponse(
        message=f"Recording all {len(WORKFLOW_CONFIG)} workflows. This may take a few minutes.",
        status="recording"
    )



# ============================================================================
# CHANGELOG / "WHAT'S NEW" ENDPOINTS
# ============================================================================

@router.get("/changelog")
async def get_changelog(request: Request, limit: int = 50, page: int = 1):
    """
    Get the changelog / "What's New" entries.
    Public endpoint - no authentication required for viewing documentation.
    
    Entries are sorted by detection date (newest first) and include:
    - Description of the change (AI-generated)
    - Screenshot of the changed page
    - Timestamp of when the change was detected
    """
    service = get_changelog_service(db)
    return await service.get_changelog(limit=limit, page=page)


@router.get("/changelog/recent")
async def get_recent_changes(request: Request, days: int = 30):
    """
    Get recent changelog entries from the last N days.
    Public endpoint - no authentication required.
    Does not include screenshot data for faster loading.
    """
    service = get_changelog_service(db)
    entries = await service.get_recent_changes(days=days)
    return {"entries": entries, "days": days, "count": len(entries)}


@router.get("/changelog/monitored-pages")
@require_permission("documentation.view")
async def get_monitored_pages(request: Request):
    """
    Get the list of pages being monitored for changes.
    """
    return {
        "pages": MONITORED_PAGES,
        "total": len(MONITORED_PAGES)
    }


@router.get("/changelog/entry/{entry_id}")
@require_permission("documentation.view")
async def get_changelog_entry(request: Request, entry_id: str, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get a specific changelog entry by ID.
    Includes the full screenshot data.
    """
    entry = await db_conn.documentation_changelog.find_one(
        {"id": entry_id},
        {"_id": 0}
    )
    
    if not entry:
        raise HTTPException(status_code=404, detail=f"Changelog entry not found: {entry_id}")
    
    return entry


@router.post("/changelog/scan")
@require_permission("documentation.manage")
async def trigger_changelog_scan(request: Request, background_tasks: BackgroundTasks):
    """
    Trigger a scan for UI changes.
    
    The scan compares current screenshots against baselines and creates
    changelog entries for any significant changes detected.
    AI is used to generate user-friendly descriptions of the changes.
    """
    service = get_changelog_service(db)
    
    async def _scan():
        try:
            result = await service.scan_for_changes()
            logger.info(f"Changelog scan result: {result}")
        except Exception as e:
            logger.error(f"Changelog scan failed: {e}")
    
    background_tasks.add_task(_scan)
    
    return RefreshResponse(
        message="Changelog scan started. Comparing current UI against baselines...",
        status="scanning"
    )
