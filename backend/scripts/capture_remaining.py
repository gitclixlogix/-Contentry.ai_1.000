"""
Capture remaining approval workflow screenshots.
"""
import asyncio
import os
import sys
import base64
from datetime import datetime, timezone

sys.path.insert(0, '/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from playwright.async_api import async_playwright

os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "contentry_db")
FRONTEND_URL = "http://localhost:3000"

# Additional screenshots with page-specific preparations
SCREENSHOTS = [
    # Creator submit for approval
    {"id": "creator-submit-approval", "path": "/contentry/content-moderation?tab=generate",
     "name": "Submit for Approval", "description": "Submit for Approval button and optional note field"},
    {"id": "creator-writing-content", "path": "/contentry/content-moderation?tab=generate",
     "name": "Creator Writing Content", "description": "Creator writing content with platform and tone selection"},
    # Manager actions
    {"id": "manager-review-content", "path": "/contentry/content-moderation?tab=scheduled",
     "name": "Manager Review Content", "description": "Manager viewing content details"},
    {"id": "manager-approve-action", "path": "/contentry/content-moderation?tab=scheduled",
     "name": "Manager Approve Action", "description": "Approve action button"},
    {"id": "manager-reject-feedback", "path": "/contentry/content-moderation?tab=scheduled",
     "name": "Manager Reject Feedback", "description": "Rejection dialog with feedback"},
    {"id": "manager-filter-status", "path": "/contentry/content-moderation?tab=scheduled",
     "name": "Filter by Status", "description": "Filtering content by approval status"},
    # Notifications - remaining
    {"id": "creator-notification-rejected", "path": "/contentry/notifications",
     "name": "Rejection Notification", "description": "Creator receiving rejection notification"},
    {"id": "manager-notification-queue", "path": "/contentry/notifications",
     "name": "Queue Summary", "description": "Daily approval queue summary notification"},
]

async def capture_screenshots():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
    context = await browser.new_context(viewport={"width": 1920, "height": 900})
    page = await context.new_page()
    
    try:
        # Login
        print("Logging in...")
        await page.goto(f"{FRONTEND_URL}/contentry/auth/login", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        
        await page.fill('input[type="email"]', "demo-admin@contentry.com")
        await page.fill('input[type="password"]', "DemoAdmin!123")
        await page.wait_for_timeout(500)
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(5000)
        
        print(f"Logged in, current URL: {page.url}")
        
        # Skip onboarding if shown
        skip_link = await page.query_selector('text=Skip for now')
        if skip_link:
            await skip_link.click()
            await page.wait_for_timeout(2000)
        
        # Capture screenshots
        for config in SCREENSHOTS:
            print(f"Capturing: {config['id']}...")
            
            await page.goto(f"{FRONTEND_URL}{config['path']}", wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            
            screenshot_bytes = await page.screenshot(type="png", full_page=False)
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            doc = {
                "id": config["id"],
                "name": config["name"],
                "description": config["description"],
                "path": config["path"],
                "section": "approvalWorkflow",
                "guide": "approval",
                "image_data": screenshot_base64,
                "content_type": "image/png",
                "captured_at": datetime.now(timezone.utc),
                "url": f"{FRONTEND_URL}{config['path']}"
            }
            
            await db.documentation_screenshots.update_one({"id": config["id"]}, {"$set": doc}, upsert=True)
            print(f"  ✓ {config['id']}")
        
        print("\n=== All remaining screenshots captured! ===")
        
        # List all screenshots in DB
        count = await db.documentation_screenshots.count_documents({})
        print(f"\nTotal screenshots in database: {count}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await context.close()
        await browser.close()
        await playwright.stop()
        client.close()

if __name__ == "__main__":
    asyncio.run(capture_screenshots())
