"""
Documentation Screenshot Service

Captures screenshots of application pages for dynamic documentation.
Uses Playwright for headless browser automation.
Stores screenshots in MongoDB with metadata.
"""

import asyncio
import base64
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Browser, Page

# Set Playwright browsers path
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'

logger = logging.getLogger(__name__)

# Screenshot configuration for each documentation page
SCREENSHOT_CONFIG = {
    "login": {
        "id": "login",
        "name": "Login Page",
        "description": "The login screen with email/password and SSO options",
        "path": "/contentry/auth/login",
        "requires_auth": False,
        "section": "getting-started",
        "guide": "user"
    },
    "dashboard": {
        "id": "dashboard",
        "name": "User Dashboard",
        "description": "Main dashboard showing assessment scores, posting activity, and compliance overview",
        "path": "/contentry/dashboard",
        "requires_auth": True,
        "section": "overview",
        "guide": "user"
    },
    "content-analyze": {
        "id": "content-analyze",
        "name": "Analyze Content",
        "description": "Content analysis interface for compliance and cultural sensitivity checking",
        "path": "/contentry/content-moderation",
        "requires_auth": True,
        "section": "analyzeContent",
        "guide": "user"
    },
    "content-generate": {
        "id": "content-generate",
        "name": "Content Generation",
        "description": "AI-powered content generation with platform selection and tone options",
        "path": "/contentry/content-moderation?tab=generate",
        "requires_auth": True,
        "section": "contentCreation",
        "guide": "user"
    },
    "scheduled-posts": {
        "id": "scheduled-posts",
        "name": "Scheduled Posts",
        "description": "View and manage scheduled content and approval queue",
        "path": "/contentry/content-moderation?tab=scheduled",
        "requires_auth": True,
        "section": "contentCreation",
        "guide": "user"
    },
    "all-posts": {
        "id": "all-posts",
        "name": "All Posts",
        "description": "Complete history of all generated and published posts",
        "path": "/contentry/content-moderation?tab=posts",
        "requires_auth": True,
        "section": "contentCreation",
        "guide": "user"
    },
    "settings": {
        "id": "settings",
        "name": "Account Settings",
        "description": "User profile and account configuration",
        "path": "/contentry/settings",
        "requires_auth": True,
        "section": "gettingStarted",
        "guide": "user"
    },
    "strategic-profiles": {
        "id": "strategic-profiles",
        "name": "Strategic Profiles",
        "description": "Brand profiles with knowledge bases for AI content generation",
        "path": "/contentry/settings/social",
        "requires_auth": True,
        "section": "strategicProfiles",
        "guide": "user"
    },
    "admin-analytics": {
        "id": "admin-analytics",
        "name": "Admin Analytics",
        "description": "Platform-wide analytics dashboard for administrators",
        "path": "/contentry/admin",
        "requires_auth": True,
        "section": "analytics",
        "guide": "admin"
    },
    "advanced-analytics": {
        "id": "advanced-analytics",
        "name": "Advanced Analytics",
        "description": "Detailed analytics with drill-down capabilities",
        "path": "/contentry/analytics",
        "requires_auth": True,
        "section": "analytics",
        "guide": "admin"
    },
    "financial-analytics": {
        "id": "financial-analytics",
        "name": "Financial Analytics",
        "description": "Revenue tracking and subscription metrics",
        "path": "/contentry/admin/financial",
        "requires_auth": True,
        "section": "financials",
        "guide": "admin"
    },
    "user-management": {
        "id": "user-management",
        "name": "User Management",
        "description": "Admin interface for managing platform users",
        "path": "/contentry/admin/users",
        "requires_auth": True,
        "section": "userManagement",
        "guide": "admin"
    },
    "enterprise-dashboard": {
        "id": "enterprise-dashboard",
        "name": "Enterprise Dashboard",
        "description": "Enterprise admin view with team analytics",
        "path": "/contentry/enterprise/dashboard",
        "requires_auth": True,
        "section": "gettingStarted",
        "guide": "enterprise"
    },
    "enterprise-team": {
        "id": "enterprise-team",
        "name": "Team Management",
        "description": "Manage enterprise team members and roles",
        "path": "/contentry/enterprise/team",
        "requires_auth": True,
        "section": "teamManagement",
        "guide": "enterprise"
    },
    "knowledge-base": {
        "id": "knowledge-base",
        "name": "Knowledge Base",
        "description": "Upload and manage company documents for AI training",
        "path": "/contentry/enterprise/knowledge",
        "requires_auth": True,
        "section": "knowledgeBase",
        "guide": "enterprise"
    },
    "projects-hub": {
        "id": "projects-hub",
        "name": "Projects Hub",
        "description": "Unified workspace for organizing and managing content by project",
        "path": "/contentry/projects",
        "requires_auth": True,
        "section": "projectsHub",
        "guide": "user"
    },
    "project-dashboard": {
        "id": "project-dashboard",
        "name": "Project Dashboard",
        "description": "Individual project view with content linking and quick actions",
        "path": "/contentry/projects",
        "requires_auth": True,
        "section": "projectsHub",
        "guide": "user",
        "note": "Will navigate to first project dashboard"
    },
    "documentation-hub": {
        "id": "documentation-hub",
        "name": "Documentation Hub",
        "description": "Self-updating help documentation with screenshots and guides",
        "path": "/contentry/documentation",
        "requires_auth": True,
        "section": "help",
        "guide": "user"
    },
    # Team & Roles Management Screenshots
    "team-management": {
        "id": "team-management",
        "name": "Team Management",
        "description": "Manage team members, invite collaborators, and assign roles",
        "path": "/contentry/settings/team",
        "requires_auth": True,
        "section": "teamManagement",
        "guide": "teams"
    },
    "roles-management": {
        "id": "roles-management",
        "name": "Role Management",
        "description": "Create, edit, and manage custom roles with granular permissions",
        "path": "/contentry/settings/roles",
        "requires_auth": True,
        "section": "rolesPermissions",
        "guide": "teams"
    },
    "role-permissions": {
        "id": "role-permissions",
        "name": "Role Permissions",
        "description": "Configure granular permissions for each role",
        "path": "/contentry/settings/roles",
        "requires_auth": True,
        "section": "rolesPermissions",
        "guide": "teams",
        "note": "Focuses on the permissions editing modal"
    },
    "invite-member": {
        "id": "invite-member",
        "name": "Invite Team Member",
        "description": "Send invitation to new team members with role selection",
        "path": "/contentry/settings/team",
        "requires_auth": True,
        "section": "teamManagement",
        "guide": "teams",
        "note": "Shows the invitation modal"
    },
    "approval-queue": {
        "id": "approval-queue",
        "name": "Content Approval Queue",
        "description": "Review and approve content submitted by team members",
        "path": "/contentry/content-moderation?tab=scheduled",
        "requires_auth": True,
        "section": "approvalWorkflow",
        "guide": "teams"
    },
    "role-audit-log": {
        "id": "role-audit-log",
        "name": "Role Audit Log",
        "description": "Track changes to roles and permissions over time",
        "path": "/contentry/settings/roles/audit",
        "requires_auth": True,
        "section": "rolesPermissions",
        "guide": "teams"
    },
    # Creator Workflow Screenshots
    "creator-content-generation": {
        "id": "creator-content-generation",
        "name": "Creator Content Generation",
        "description": "Content Generation page where Creators write or generate new posts",
        "path": "/contentry/content-moderation?tab=generate",
        "requires_auth": True,
        "section": "creatorWorkflow",
        "guide": "approval",
        "role": "creator"
    },
    "creator-writing-content": {
        "id": "creator-writing-content",
        "name": "Creator Writing Content",
        "description": "Creator writing content with platform and tone selection",
        "path": "/contentry/content-moderation?tab=generate",
        "requires_auth": True,
        "section": "creatorWorkflow",
        "guide": "approval",
        "role": "creator"
    },
    "creator-analysis-scores": {
        "id": "creator-analysis-scores",
        "name": "Creator Analysis Scores",
        "description": "AI analysis showing Cultural Fit, Brand Alignment, and Compliance scores",
        "path": "/contentry/content-moderation?tab=analyze",
        "requires_auth": True,
        "section": "creatorWorkflow",
        "guide": "approval",
        "role": "creator"
    },
    "creator-submit-approval": {
        "id": "creator-submit-approval",
        "name": "Submit for Approval",
        "description": "Submit for Approval button and optional note field",
        "path": "/contentry/content-moderation?tab=generate",
        "requires_auth": True,
        "section": "creatorWorkflow",
        "guide": "approval",
        "role": "creator"
    },
    "creator-pending-status": {
        "id": "creator-pending-status",
        "name": "Creator Pending Status",
        "description": "Content showing 'Pending Review' status in the Scheduled tab",
        "path": "/contentry/content-moderation?tab=scheduled",
        "requires_auth": True,
        "section": "creatorWorkflow",
        "guide": "approval",
        "role": "creator"
    },
    # Manager Workflow Screenshots
    "manager-approval-queue": {
        "id": "manager-approval-queue",
        "name": "Manager Approval Queue",
        "description": "Approval queue showing all pending content submissions",
        "path": "/contentry/content-moderation?tab=scheduled",
        "requires_auth": True,
        "section": "managerWorkflow",
        "guide": "approval",
        "role": "manager"
    },
    "manager-review-content": {
        "id": "manager-review-content",
        "name": "Manager Review Content",
        "description": "Manager viewing content details, scores, and creator notes",
        "path": "/contentry/content-moderation?tab=scheduled",
        "requires_auth": True,
        "section": "managerWorkflow",
        "guide": "approval",
        "role": "manager"
    },
    "manager-approve-action": {
        "id": "manager-approve-action",
        "name": "Manager Approve Action",
        "description": "Click 'Approve' to allow publishing",
        "path": "/contentry/content-moderation?tab=scheduled",
        "requires_auth": True,
        "section": "managerWorkflow",
        "guide": "approval",
        "role": "manager"
    },
    "manager-reject-feedback": {
        "id": "manager-reject-feedback",
        "name": "Manager Reject with Feedback",
        "description": "Rejection dialog with feedback field",
        "path": "/contentry/content-moderation?tab=scheduled",
        "requires_auth": True,
        "section": "managerWorkflow",
        "guide": "approval",
        "role": "manager"
    },
    "manager-filter-status": {
        "id": "manager-filter-status",
        "name": "Manager Filter Status",
        "description": "Filtering content by approval status",
        "path": "/contentry/content-moderation?tab=scheduled",
        "requires_auth": True,
        "section": "managerWorkflow",
        "guide": "approval",
        "role": "manager"
    },
    # Notification Screenshots
    "creator-notification-approved": {
        "id": "creator-notification-approved",
        "name": "Creator Approval Notification",
        "description": "Creator receiving approval notification with publish options",
        "path": "/contentry/notifications",
        "requires_auth": True,
        "section": "notifications",
        "guide": "approval",
        "role": "creator"
    },
    "creator-notification-rejected": {
        "id": "creator-notification-rejected",
        "name": "Creator Rejection Notification",
        "description": "Creator receiving rejection notification with Manager feedback",
        "path": "/contentry/notifications",
        "requires_auth": True,
        "section": "notifications",
        "guide": "approval",
        "role": "creator"
    },
    "manager-notification-new": {
        "id": "manager-notification-new",
        "name": "Manager New Submission Notification",
        "description": "Manager notification for new content submission",
        "path": "/contentry/notifications",
        "requires_auth": True,
        "section": "notifications",
        "guide": "approval",
        "role": "manager"
    },
    "manager-notification-queue": {
        "id": "manager-notification-queue",
        "name": "Manager Queue Summary Notification",
        "description": "Daily approval queue summary notification",
        "path": "/contentry/notifications",
        "requires_auth": True,
        "section": "notifications",
        "guide": "approval",
        "role": "manager"
    }
}


class ScreenshotService:
    """Service for capturing and managing documentation screenshots."""
    
    def __init__(self, db, base_url: str = None):
        self.db = db
        self.base_url = base_url or os.environ.get(
            "FRONTEND_URL", 
            "https://admin-portal-278.preview.emergentagent.com"
        )
        self.browser: Optional[Browser] = None
        self.demo_credentials = {
            "email": "demo-admin@contentry.com",
            "password": "DemoAdmin!123"
        }
    
    async def _get_browser(self):
        """Get or create browser instance."""
        if self.browser is None:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
        return self.browser
    
    async def _login(self, page: Page, retries: int = 2) -> bool:
        """Login to the application using demo credentials with retry logic."""
        for attempt in range(retries + 1):
            try:
                login_url = f"{self.base_url}/contentry/auth/login"
                await page.goto(login_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)
                
                # Fill login form
                email_input = await page.query_selector('input[type="email"]')
                if email_input:
                    await email_input.fill(self.demo_credentials["email"])
                    
                password_input = await page.query_selector('input[type="password"]')
                if password_input:
                    await password_input.fill(self.demo_credentials["password"])
                
                await page.wait_for_timeout(500)
                
                # Click login button - use type="submit" to handle translated text
                login_btn = await page.query_selector('button[type="submit"]')
                if login_btn:
                    await login_btn.click()
                    await page.wait_for_timeout(6000)
                    
                    # Check if login was successful by looking for dashboard elements
                    dashboard_check = await page.query_selector('[class*="dashboard"], [class*="sidebar"]')
                    if dashboard_check or "dashboard" in page.url.lower():
                        return True
                    
                    # If not on dashboard, try again
                    if attempt < retries:
                        logger.warning(f"Login attempt {attempt + 1} failed, retrying...")
                        continue
                    
                return False
            except Exception as e:
                logger.error(f"Login attempt {attempt + 1} failed: {e}")
                if attempt < retries:
                    await page.wait_for_timeout(2000)
                    continue
                return False
        return False
    
    async def _prepare_page_for_screenshot(self, page: Page, page_id: str, config: Dict) -> None:
        """Prepare the page for optimal screenshot capture with UI interactions."""
        try:
            # Wait for page to fully load
            await page.wait_for_load_state("networkidle", timeout=15000)
        except:
            pass  # Continue even if networkidle times out
        
        # Page-specific preparations
        if page_id == "team-management":
            # Click on Settings menu if collapsed, then Team
            settings_btn = await page.query_selector('a[href*="settings"]')
            if settings_btn:
                await settings_btn.click()
                await page.wait_for_timeout(1000)
            # Ensure we're on team tab and table is visible
            await page.wait_for_selector('[data-testid="team-members-table"], table', timeout=5000)
            
        elif page_id == "invite-member":
            # Open the invite modal
            invite_btn = await page.query_selector('[data-testid="invite-member-btn"], button:has-text("Invite")')
            if invite_btn:
                await invite_btn.click()
                await page.wait_for_timeout(1000)
                
        elif page_id == "roles-management" or page_id == "role-permissions":
            # Expand a role card to show permissions
            role_card = await page.query_selector('[data-testid="role-card"], .role-card')
            if role_card:
                await role_card.click()
                await page.wait_for_timeout(500)
                
        elif page_id == "admin-analytics" or page_id == "advanced-analytics":
            # Wait for charts to render
            await page.wait_for_timeout(2000)
            # Click on a tab to show data
            tabs = await page.query_selector_all('[role="tab"]')
            if len(tabs) > 0:
                await tabs[0].click()
                await page.wait_for_timeout(1000)
                
        elif page_id == "strategic-profiles":
            # Scroll to show the profile form
            await page.evaluate("window.scrollTo(0, 200)")
            await page.wait_for_timeout(500)
            
        elif page_id == "content-analyze":
            # Click analyze tab if not already selected
            analyze_tab = await page.query_selector('[data-testid="analyze-tab"], button:has-text("Analyze")')
            if analyze_tab:
                await analyze_tab.click()
                await page.wait_for_timeout(500)
                
        elif page_id == "content-generate":
            # Ensure generate tab is selected
            generate_tab = await page.query_selector('[data-testid="generate-tab"], button:has-text("Generate")')
            if generate_tab:
                await generate_tab.click()
                await page.wait_for_timeout(500)
                
        elif page_id == "documentation-hub":
            # Scroll to show all guide cards
            await page.evaluate("window.scrollTo(0, 150)")
            await page.wait_for_timeout(500)
            
        elif page_id == "projects-hub":
            # Wait for project cards to load
            await page.wait_for_selector('[data-testid="project-card"], .project-card', timeout=5000)
            
        # Highlight active sidebar item
        current_path = config.get('path', '')
        sidebar_link = await page.query_selector(f'aside a[href*="{current_path.split("?")[0]}"]')
        if sidebar_link:
            await page.evaluate("""(el) => {
                el.style.backgroundColor = 'rgba(66, 153, 225, 0.2)';
                el.style.borderLeft = '3px solid #4299E1';
            }""", sidebar_link)
        
        # Hide any toast notifications that might be showing
        await page.evaluate("""() => {
            document.querySelectorAll('[data-sonner-toast], .toast, .chakra-toast').forEach(el => {
                el.style.display = 'none';
            });
        }""")
        
        # Final wait for any animations
        await page.wait_for_timeout(500)

    async def capture_screenshot(self, page_id: str) -> Optional[Dict]:
        """Capture a screenshot of a specific page with enhanced UI preparation."""
        if page_id not in SCREENSHOT_CONFIG:
            logger.error(f"Unknown page_id: {page_id}")
            return None
        
        config = SCREENSHOT_CONFIG[page_id]
        browser = await self._get_browser()
        context = await browser.new_context(
            viewport={"width": 1920, "height": 900}
        )
        page = await context.new_page()
        
        try:
            # Login if required
            if config["requires_auth"]:
                logged_in = await self._login(page)
                if not logged_in:
                    logger.error(f"Failed to login for screenshot: {page_id}")
                    await context.close()
                    return None
            
            # Navigate to target page
            target_url = f"{self.base_url}{config['path']}"
            await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)  # Initial wait for dynamic content
            
            # Prepare page for optimal screenshot (UI interactions, highlighting, etc.)
            await self._prepare_page_for_screenshot(page, page_id, config)
            
            # Capture screenshot
            screenshot_bytes = await page.screenshot(
                type="png",
                full_page=False
            )
            
            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Create screenshot document
            screenshot_doc = {
                "id": page_id,
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
            
            # Store in MongoDB
            await self.db.documentation_screenshots.update_one(
                {"id": page_id},
                {"$set": screenshot_doc},
                upsert=True
            )
            
            logger.info(f"Screenshot captured: {page_id}")
            return screenshot_doc
            
        except Exception as e:
            logger.error(f"Screenshot capture failed for {page_id}: {e}")
            return None
        finally:
            await context.close()
    
    async def capture_all_screenshots(self) -> Dict:
        """Capture screenshots for all configured pages."""
        results = {
            "success": [],
            "failed": [],
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None
        }
        
        for page_id in SCREENSHOT_CONFIG.keys():
            try:
                result = await self.capture_screenshot(page_id)
                if result:
                    results["success"].append(page_id)
                else:
                    results["failed"].append(page_id)
            except Exception as e:
                logger.error(f"Failed to capture {page_id}: {e}")
                results["failed"].append(page_id)
        
        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Store refresh status
        await self.db.documentation_meta.update_one(
            {"type": "screenshot_refresh"},
            {"$set": {
                "last_refresh": datetime.now(timezone.utc),
                "results": results
            }},
            upsert=True
        )
        
        return results
    
    async def get_screenshot(self, page_id: str) -> Optional[Dict]:
        """Get a screenshot from the database."""
        doc = await self.db.documentation_screenshots.find_one(
            {"id": page_id},
            {"_id": 0}
        )
        return doc
    
    async def get_all_screenshots(self) -> List[Dict]:
        """Get all screenshots from the database."""
        cursor = self.db.documentation_screenshots.find(
            {},
            {"_id": 0, "image_data": 0}  # Exclude image data for listing
        )
        return await cursor.to_list(length=100)
    
    async def get_screenshots_by_guide(self, guide: str) -> List[Dict]:
        """Get screenshots for a specific guide (admin, enterprise, user)."""
        cursor = self.db.documentation_screenshots.find(
            {"guide": guide},
            {"_id": 0}
        )
        return await cursor.to_list(length=50)
    
    async def get_last_refresh_status(self) -> Optional[Dict]:
        """Get the status of the last screenshot refresh."""
        doc = await self.db.documentation_meta.find_one(
            {"type": "screenshot_refresh"},
            {"_id": 0}
        )
        return doc
    
    async def close(self):
        """Close browser instance."""
        if self.browser:
            await self.browser.close()
            self.browser = None


# Singleton instance
_screenshot_service: Optional[ScreenshotService] = None

def get_screenshot_service(db) -> ScreenshotService:
    """Get or create screenshot service instance."""
    global _screenshot_service
    if _screenshot_service is None:
        _screenshot_service = ScreenshotService(db)
    return _screenshot_service
