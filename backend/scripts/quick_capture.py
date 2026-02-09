"""
Quick script to capture a few screenshots at a time.
"""
import asyncio
import os
import sys
import base64
from datetime import datetime, timezone

sys.path.insert(0, '/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from playwright.async_api import async_playwright

# Set Playwright browsers path
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "contentry_db")
FRONTEND_URL = "http://localhost:3000"

# Screenshots to capture
SCREENSHOTS = [
    {
        "id": "creator-content-generation",
        "name": "Creator Content Generation",
        "description": "Content Generation page where Creators write or generate new posts",
        "path": "/contentry/content-moderation?tab=generate",
        "section": "creatorWorkflow",
        "guide": "approval"
    },
    {
        "id": "manager-approval-queue",
        "name": "Manager Approval Queue", 
        "description": "Approval queue showing all pending content submissions",
        "path": "/contentry/content-moderation?tab=scheduled",
        "section": "managerWorkflow",
        "guide": "approval"
    },
]

async def capture_screenshots():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    
    context = await browser.new_context(viewport={"width": 1920, "height": 900})
    page = await context.new_page()
    
    try:
        # Login
        print("Logging in...")
        await page.goto(f"{FRONTEND_URL}/contentry/auth/login", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        
        email_input = await page.query_selector('input[type="email"]')
        if email_input:
            await email_input.fill("demo-admin@contentry.com")
        
        password_input = await page.query_selector('input[type="password"]')
        if password_input:
            await password_input.fill("DemoAdmin!123")
        
        await page.wait_for_timeout(500)
        
        login_btn = await page.query_selector('button[type="submit"]')
        if login_btn:
            await login_btn.click()
            await page.wait_for_timeout(5000)
        
        print(f"Current URL after login: {page.url}")
        
        # Skip onboarding if shown
        skip_link = await page.query_selector('text=Skip for now')
        if skip_link:
            await skip_link.click()
            await page.wait_for_timeout(2000)
        
        # Capture each screenshot
        for config in SCREENSHOTS:
            print(f"Capturing: {config['id']}...")
            
            target_url = f"{FRONTEND_URL}{config['path']}"
            await page.goto(target_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            
            # Capture screenshot
            screenshot_bytes = await page.screenshot(type="png", full_page=False)
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Store in MongoDB
            doc = {
                "id": config["id"],
                "name": config["name"],
                "description": config["description"],
                "path": config["path"],
                "section": config["section"],
                "guide": config["guide"],
                "image_data": screenshot_base64,
                "content_type": "image/png",
                "captured_at": datetime.now(timezone.utc),
                "url": target_url
            }
            
            await db.documentation_screenshots.update_one(
                {"id": config["id"]},
                {"$set": doc},
                upsert=True
            )
            
            print(f"  ✓ Captured and saved: {config['id']}")
        
        print("\nDone!")
        
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
