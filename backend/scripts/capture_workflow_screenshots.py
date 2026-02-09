"""
Capture approval workflow screenshots with proper demo data.
Each screenshot shows a specific step in the workflow.
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

# Demo user credentials
USERS = {
    "admin": {"email": "sarah.chen@techcorp-demo.com", "password": "Demo123!", "name": "Sarah Chen"},
    "manager": {"email": "michael.rodriguez@techcorp-demo.com", "password": "Demo123!", "name": "Michael Rodriguez"},
    "creator": {"email": "alex.martinez@techcorp-demo.com", "password": "Demo123!", "name": "Alex Martinez"},
    "reviewer": {"email": "robert.kim@techcorp-demo.com", "password": "Demo123!", "name": "Robert Kim"},
}

async def login(page, role):
    """Login as a specific role."""
    user = USERS[role]
    print(f"  Logging in as {user['name']} ({role})...")
    
    await page.goto(f"{FRONTEND_URL}/contentry/auth/login", wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    
    # Accept cookies
    accept_btn = await page.query_selector('button:has-text("Accept All")')
    if accept_btn:
        await accept_btn.click()
        await page.wait_for_timeout(500)
    
    # Fill credentials
    await page.fill('input[type="email"]', user["email"])
    await page.fill('input[type="password"]', user["password"])
    await page.wait_for_timeout(300)
    await page.click('button:has-text("Log in")')
    await page.wait_for_timeout(4000)
    
    # Skip onboarding if shown
    skip_link = await page.query_selector('text=Skip for now')
    if skip_link:
        await skip_link.click()
        await page.wait_for_timeout(2000)
    
    print(f"    ✓ Logged in as {user['name']}")
    return user

async def save_screenshot(db, page, screenshot_id, name, description):
    """Capture and save a screenshot to MongoDB."""
    screenshot_bytes = await page.screenshot(type="png", full_page=False)
    screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
    
    doc = {
        "id": screenshot_id,
        "name": name,
        "description": description,
        "image_data": screenshot_base64,
        "content_type": "image/png",
        "captured_at": datetime.now(timezone.utc),
        "url": page.url,
        "section": "approvalWorkflow",
        "guide": "approval"
    }
    
    await db.documentation_screenshots.update_one(
        {"id": screenshot_id}, 
        {"$set": doc}, 
        upsert=True
    )
    print(f"    ✓ Saved: {screenshot_id}")

async def capture_all_screenshots():
    """Capture all approval workflow screenshots."""
    print("=" * 60)
    print("CAPTURING APPROVAL WORKFLOW SCREENSHOTS")
    print("=" * 60)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    
    try:
        # === CREATOR WORKFLOW ===
        print("\n📝 CREATOR WORKFLOW")
        context = await browser.new_context(viewport={"width": 1920, "height": 900})
        page = await context.new_page()
        
        user = await login(page, "creator")
        
        # 1. Content Generation page
        print("  Capturing: Creator Content Generation...")
        await page.goto(f"{FRONTEND_URL}/contentry/content-moderation?tab=generate", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await save_screenshot(db, page, "creator-content-generation", 
            "Content Generation Page", 
            "Content Generation page where Creators write or generate new posts")
        
        # 2. Analysis scores
        print("  Capturing: Creator Analysis Scores...")
        await page.goto(f"{FRONTEND_URL}/contentry/content-moderation?tab=analyze", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await save_screenshot(db, page, "creator-analysis-scores",
            "Content Analysis Scores",
            "AI analysis showing Cultural Fit, Brand Alignment, and Compliance scores")
        
        # 3. Scheduled/Pending tab (Creator's view of their pending content)
        print("  Capturing: Creator Pending Status...")
        await page.goto(f"{FRONTEND_URL}/contentry/content-moderation?tab=scheduled", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await save_screenshot(db, page, "creator-pending-status",
            "Pending Content Status",
            "Content showing 'Pending Review' status in the Scheduled tab")
        
        # 4. Notifications (Creator view)
        print("  Capturing: Creator Notifications...")
        await page.goto(f"{FRONTEND_URL}/contentry/notifications", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await save_screenshot(db, page, "creator-notification-approved",
            "Creator Approval Notification",
            "Creator receiving approval notification with publish options")
        
        await context.close()
        
        # === MANAGER WORKFLOW ===
        print("\n🛡️ MANAGER WORKFLOW")
        context = await browser.new_context(viewport={"width": 1920, "height": 900})
        page = await context.new_page()
        
        user = await login(page, "manager")
        
        # 5. Approval Queue (Manager's view)
        print("  Capturing: Manager Approval Queue...")
        await page.goto(f"{FRONTEND_URL}/contentry/content-moderation?tab=scheduled", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await save_screenshot(db, page, "manager-approval-queue",
            "Manager Approval Queue",
            "Approval queue showing all pending content submissions")
        
        # 6. Review Content Details
        print("  Capturing: Manager Review Content...")
        # Click on a pending item if available
        pending_item = await page.query_selector('[data-status="pending"], .pending-item')
        if pending_item:
            await pending_item.click()
            await page.wait_for_timeout(1500)
        await save_screenshot(db, page, "manager-review-content",
            "Content Review Details",
            "Manager viewing content details, scores, and creator notes")
        
        # 7. Notifications (Manager view)
        print("  Capturing: Manager Notifications...")
        await page.goto(f"{FRONTEND_URL}/contentry/notifications", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await save_screenshot(db, page, "manager-notification-new",
            "Manager New Submission Notification",
            "Manager notification for new content submission")
        
        await context.close()
        
        # === ADMIN WORKFLOW ===
        print("\n👤 ADMIN WORKFLOW")
        context = await browser.new_context(viewport={"width": 1920, "height": 900})
        page = await context.new_page()
        
        user = await login(page, "admin")
        
        # 8. Admin Dashboard
        print("  Capturing: Admin Dashboard...")
        await page.goto(f"{FRONTEND_URL}/contentry/dashboard", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await save_screenshot(db, page, "admin-dashboard",
            "Admin Dashboard",
            "Admin overview dashboard with analytics and team activity")
        
        # 9. Team Management
        print("  Capturing: Team Management...")
        await page.goto(f"{FRONTEND_URL}/contentry/settings/team", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await save_screenshot(db, page, "team-management",
            "Team Management",
            "Team management page showing all team members and their roles")
        
        await context.close()
        
        print("\n" + "=" * 60)
        print("✅ ALL SCREENSHOTS CAPTURED SUCCESSFULLY!")
        print("=" * 60)
        
        # Count screenshots
        count = await db.documentation_screenshots.count_documents({"guide": "approval"})
        print(f"\nTotal approval workflow screenshots: {count}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser.close()
        await playwright.stop()
        client.close()

if __name__ == "__main__":
    asyncio.run(capture_all_screenshots())
