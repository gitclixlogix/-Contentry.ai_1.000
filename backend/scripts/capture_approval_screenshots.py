"""
Script to capture documentation screenshots for the Approval Workflow Guide.
Run this script to populate the screenshot database with actual screenshots.
"""

import asyncio
import os
import sys
import logging

# Add backend to path
sys.path.insert(0, '/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Screenshots to capture for the Approval Workflow documentation
APPROVAL_SCREENSHOTS = [
    # Creator Workflow
    "creator-content-generation",
    "creator-writing-content", 
    "creator-analysis-scores",
    "creator-submit-approval",
    "creator-pending-status",
    # Manager Workflow
    "manager-approval-queue",
    "manager-review-content",
    "manager-approve-action",
    "manager-reject-feedback",
    "manager-filter-status",
    # Notifications
    "creator-notification-approved",
    "creator-notification-rejected",
    "manager-notification-new",
    "manager-notification-queue",
]

async def capture_screenshots():
    """Capture all approval workflow screenshots."""
    from services.documentation.screenshot_service import ScreenshotService, SCREENSHOT_CONFIG
    
    # Connect to MongoDB
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "contentry_db")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Create screenshot service
    service = ScreenshotService(db)
    
    results = {"success": [], "failed": []}
    
    logger.info(f"Starting capture of {len(APPROVAL_SCREENSHOTS)} screenshots...")
    
    for page_id in APPROVAL_SCREENSHOTS:
        if page_id not in SCREENSHOT_CONFIG:
            logger.warning(f"Unknown page_id: {page_id}, skipping")
            results["failed"].append(page_id)
            continue
            
        logger.info(f"Capturing: {page_id}")
        try:
            result = await service.capture_screenshot(page_id)
            if result:
                results["success"].append(page_id)
                logger.info(f"  ✓ Success: {page_id}")
            else:
                results["failed"].append(page_id)
                logger.error(f"  ✗ Failed: {page_id}")
        except Exception as e:
            results["failed"].append(page_id)
            logger.error(f"  ✗ Error capturing {page_id}: {e}")
    
    # Close browser
    await service.close()
    
    logger.info(f"\n=== Capture Complete ===")
    logger.info(f"Success: {len(results['success'])}")
    logger.info(f"Failed: {len(results['failed'])}")
    
    if results["failed"]:
        logger.info(f"Failed screenshots: {', '.join(results['failed'])}")
    
    return results

if __name__ == "__main__":
    asyncio.run(capture_screenshots())
