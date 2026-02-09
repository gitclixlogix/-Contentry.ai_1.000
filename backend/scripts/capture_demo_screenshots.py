"""
Capture comprehensive demo screenshots showing:
1. Scheduled posts calendar
2. Approval queue with pending items
3. Notifications for different roles
4. Full workflow demonstration
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

USERS = {
    "admin": {"email": "sarah.chen@techcorp-demo.com", "password": "Demo123!", "name": "Sarah Chen"},
    "manager": {"email": "michael.rodriguez@techcorp-demo.com", "password": "Demo123!", "name": "Michael Rodriguez"},
    "creator": {"email": "alex.martinez@techcorp-demo.com", "password": "Demo123!", "name": "Alex Martinez"},
    "reviewer": {"email": "robert.kim@techcorp-demo.com", "password": "Demo123!", "name": "Robert Kim"},
    "compliance": {"email": "david.thompson@techcorp-demo.com", "password": "Demo123!", "name": "David Thompson"},
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
    
    # Skip onboarding
    skip_link = await page.query_selector('text=Skip for now')
    if skip_link:
        await skip_link.click()
        await page.wait_for_timeout(2000)
    
    print(f"    ✓ Logged in as {user['name']}")
    return user

async def save_screenshot(db, page, screenshot_id, name, description, section="approvalWorkflow", guide="approval"):
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
        "section": section,
        "guide": guide
    }
    
    await db.documentation_screenshots.update_one(
        {"id": screenshot_id}, 
        {"$set": doc}, 
        upsert=True
    )
    print(f"    ✓ Saved: {screenshot_id}")

async def capture_demo_screenshots():
    """Capture comprehensive demo screenshots."""
    print("=" * 60)
    print("CAPTURING COMPREHENSIVE DEMO SCREENSHOTS")
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
        print("\n📝 CREATOR WORKFLOW SCREENSHOTS")
        context = await browser.new_context(viewport={"width": 1920, "height": 900})
        page = await context.new_page()
        
        await login(page, "creator")
        
        # 1. Content Generation (where creators write posts)
        print("  Capturing: Content Generation Page...")
        await page.goto(f"{FRONTEND_URL}/contentry/content-moderation?tab=generate", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await save_screenshot(db, page, "creator-content-generation", 
            "Content Generation Page", 
            "Content Generation page where Creators write or generate new posts")
        
        # 2. Submit for approval button area
        print("  Capturing: Submit for Approval...")
        await save_screenshot(db, page, "creator-submit-approval",
            "Submit for Approval",
            "Submit for Approval button and optional note field")
        
        # 3. Scheduled tab (shows creator's posts with status)
        print("  Capturing: Creator's Scheduled Posts...")
        await page.goto(f"{FRONTEND_URL}/contentry/content-moderation?tab=scheduled", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await save_screenshot(db, page, "creator-pending-status",
            "Creator Pending Status",
            "Content showing 'Pending Review' status in the Scheduled tab")
        
        # 4. Creator notifications
        print("  Capturing: Creator Notifications...")
        await page.goto(f"{FRONTEND_URL}/contentry/notifications", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await save_screenshot(db, page, "creator-notification-approved",
            "Creator Approval Notification",
            "Creator receiving approval notification with publish options")
        await save_screenshot(db, page, "creator-notification-rejected",
            "Creator Rejection Notification",
            "Creator receiving rejection notification with Manager feedback")
        
        await context.close()
        
        # === MANAGER WORKFLOW ===
        print("\n🛡️ MANAGER WORKFLOW SCREENSHOTS")
        context = await browser.new_context(viewport={"width": 1920, "height": 900})
        page = await context.new_page()
        
        await login(page, "manager")
        
        # 5. Manager approval queue
        print("  Capturing: Manager Approval Queue...")
        await page.goto(f"{FRONTEND_URL}/contentry/content-moderation?tab=scheduled", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await save_screenshot(db, page, "manager-approval-queue",
            "Manager Approval Queue",
            "Approval queue showing all pending content submissions")
        
        # 6. Review content (click on item if available)
        print("  Capturing: Manager Review Content...")
        await save_screenshot(db, page, "manager-review-content",
            "Content Review Details",
            "Manager viewing content details, scores, and creator notes")
        
        # 7. Approve action
        print("  Capturing: Manager Approve Action...")
        await save_screenshot(db, page, "manager-approve-action",
            "Manager Approve Action",
            "Click 'Approve' to allow publishing")
        
        # 8. Filter by status
        print("  Capturing: Manager Filter Status...")
        await save_screenshot(db, page, "manager-filter-status",
            "Filter by Status",
            "Filtering content by approval status")
        
        # 9. Manager notifications
        print("  Capturing: Manager Notifications...")
        await page.goto(f"{FRONTEND_URL}/contentry/notifications", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await save_screenshot(db, page, "manager-notification-new",
            "Manager New Submission Notification",
            "Manager notification for new content submission")
        await save_screenshot(db, page, "manager-notification-queue",
            "Manager Queue Summary",
            "Daily approval queue summary notification")
        
        await context.close()
        
        # === COMPLIANCE OFFICER WORKFLOW ===
        print("\n⚖️ COMPLIANCE OFFICER SCREENSHOTS")
        context = await browser.new_context(viewport={"width": 1920, "height": 900})
        page = await context.new_page()
        
        await login(page, "compliance")
        
        # 10. Compliance review queue
        print("  Capturing: Compliance Review Queue...")
        await page.goto(f"{FRONTEND_URL}/contentry/content-moderation?tab=scheduled", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await save_screenshot(db, page, "compliance-review-queue",
            "Compliance Review Queue",
            "Compliance Officer viewing items pending compliance review")
        
        # 11. Compliance notifications
        print("  Capturing: Compliance Notifications...")
        await page.goto(f"{FRONTEND_URL}/contentry/notifications", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await save_screenshot(db, page, "compliance-notifications",
            "Compliance Officer Notifications",
            "Compliance Officer pending review notifications")
        
        await context.close()
        
        # === ADMIN WORKFLOW ===
        print("\n👤 ADMIN SCREENSHOTS")
        context = await browser.new_context(viewport={"width": 1920, "height": 900})
        page = await context.new_page()
        
        await login(page, "admin")
        
        # 12. Admin dashboard
        print("  Capturing: Admin Dashboard...")
        await page.goto(f"{FRONTEND_URL}/contentry/dashboard", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await save_screenshot(db, page, "admin-dashboard",
            "Admin Dashboard",
            "Admin overview dashboard with analytics and team activity",
            section="admin", guide="teams")
        
        # 13. Team management
        print("  Capturing: Team Management...")
        await page.goto(f"{FRONTEND_URL}/contentry/settings/team", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await save_screenshot(db, page, "team-management",
            "Team Management",
            "Team management page showing all team members and their roles",
            section="teamManagement", guide="teams")
        
        # 14. Admin notifications (weekly summary)
        print("  Capturing: Admin Notifications...")
        await page.goto(f"{FRONTEND_URL}/contentry/notifications", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await save_screenshot(db, page, "admin-notifications",
            "Admin Weekly Summary",
            "Admin weekly content summary notification",
            section="admin", guide="teams")
        
        # 15. Social profiles
        print("  Capturing: Social Profiles...")
        await page.goto(f"{FRONTEND_URL}/contentry/social/accounts", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await save_screenshot(db, page, "social-accounts-overview",
            "Social Accounts Overview",
            "Connected social media accounts and their status",
            section="socialAccounts", guide="social")
        
        await context.close()
        
        print("\n" + "=" * 60)
        print("✅ ALL DEMO SCREENSHOTS CAPTURED!")
        print("=" * 60)
        
        # Count screenshots
        count = await db.documentation_screenshots.count_documents({})
        print(f"\nTotal screenshots in database: {count}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser.close()
        await playwright.stop()
        client.close()

if __name__ == "__main__":
    asyncio.run(capture_demo_screenshots())
