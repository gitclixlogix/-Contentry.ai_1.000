"""
Workflow GIF Recording Service

Records multi-step user workflows as animated GIFs for documentation.
Uses Playwright for browser automation and captures frames to create GIFs.

Key workflows:
1. Role Assignment - Changing a team member's role
2. Content Rewriting - Analyzing and rewriting content
"""

import asyncio
import base64
import io
import logging
import os
import tempfile
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from PIL import Image

# Set Playwright browsers path
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'

logger = logging.getLogger(__name__)

# Workflow definitions
WORKFLOW_CONFIG = {
    "role-assignment": {
        "id": "role-assignment",
        "name": "Assigning a Manager Role",
        "description": "Shows how to change a team member's role from Creator to Manager",
        "duration_seconds": 8,
        "steps": [
            {"action": "navigate", "path": "/contentry/enterprise/settings/team", "wait": 2000},
            {"action": "screenshot", "label": "Team Management page"},
            {"action": "hover", "selector": "select", "wait": 500},
            {"action": "screenshot", "label": "Hovering over role dropdown"},
            {"action": "click", "selector": "select", "wait": 500},
            {"action": "screenshot", "label": "Dropdown opened"},
            {"action": "select", "selector": "select", "value": "manager", "wait": 1000},
            {"action": "screenshot", "label": "Role changed to Manager"},
            {"action": "wait", "duration": 1500},
            {"action": "screenshot", "label": "Change confirmed"},
        ],
        "section": "team-management",
        "guide": "admin"
    },
    "content-rewriting": {
        "id": "content-rewriting",
        "name": "Rewriting Content",
        "description": "Shows how to analyze content and use AI to rewrite it",
        "duration_seconds": 10,
        "steps": [
            {"action": "navigate", "path": "/contentry/content-moderation", "wait": 2000},
            {"action": "screenshot", "label": "Analyze Content tab"},
            {"action": "type", "selector": "textarea", "text": "Check out this product! It's amazing!", "wait": 500},
            {"action": "screenshot", "label": "Content entered"},
            {"action": "click", "selector": "button:has-text('Analyze')", "wait": 3000},
            {"action": "screenshot", "label": "Content analyzed"},
            {"action": "scroll", "y": 300, "wait": 500},
            {"action": "screenshot", "label": "Viewing results"},
            {"action": "click", "selector": "button:has-text('Rewrite')", "wait": 3000},
            {"action": "screenshot", "label": "Content rewritten"},
        ],
        "section": "content-analysis",
        "guide": "user"
    }
}


class WorkflowGifService:
    """
    Service for recording and storing workflow GIFs.
    """
    
    def __init__(self, db):
        self.db = db
        self.browser = None
        self.context = None
        self.base_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
        self.frame_delay = 560  # milliseconds between frames (~1.8 fps) - slower for readability
        self.gif_quality = 90  # Higher quality for clarity
        
    async def initialize(self):
        """Initialize Playwright browser."""
        from playwright.async_api import async_playwright
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        logger.info("Workflow GIF service initialized")
        
    async def cleanup(self):
        """Cleanup browser resources."""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        logger.info("Workflow GIF service cleaned up")
    
    async def _login(self, page, email: str = "demo@test.com", password: str = "password123"):
        """Login to the application."""
        try:
            await page.goto(f"{self.base_url}/contentry/auth/login")
            await page.wait_for_load_state('networkidle')
            
            await page.fill('input[type="email"]', email)
            await page.fill('input[type="password"]', password)
            await page.click('button:has-text("Log in")')
            
            await page.wait_for_timeout(3000)
            await page.wait_for_load_state('networkidle')
            
            logger.info("Login successful for workflow recording")
            return True
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    async def _capture_frame(self, page) -> Image.Image:
        """Capture a single frame as PIL Image."""
        screenshot_bytes = await page.screenshot(type='png')
        return Image.open(io.BytesIO(screenshot_bytes))
    
    async def _execute_workflow_steps(self, page, steps: List[Dict]) -> List[Image.Image]:
        """Execute workflow steps and capture frames."""
        frames = []
        
        for step in steps:
            action = step.get("action")
            
            try:
                if action == "navigate":
                    path = step.get("path", "/")
                    await page.goto(f"{self.base_url}{path}")
                    await page.wait_for_load_state('networkidle')
                    
                elif action == "click":
                    selector = step.get("selector")
                    if selector:
                        element = await page.query_selector(selector)
                        if element:
                            await element.click()
                        else:
                            # Try with text content
                            await page.click(selector, timeout=5000)
                    
                elif action == "hover":
                    selector = step.get("selector")
                    if selector:
                        await page.hover(selector)
                    
                elif action == "type":
                    selector = step.get("selector")
                    text = step.get("text", "")
                    if selector:
                        await page.fill(selector, text)
                    
                elif action == "select":
                    selector = step.get("selector")
                    value = step.get("value")
                    if selector and value:
                        await page.select_option(selector, value)
                    
                elif action == "scroll":
                    y = step.get("y", 300)
                    await page.evaluate(f"window.scrollBy(0, {y})")
                    
                elif action == "wait":
                    duration = step.get("duration", 1000)
                    await page.wait_for_timeout(duration)
                
                elif action == "screenshot":
                    pass  # Will capture below
                
                # Wait after action
                wait_time = step.get("wait", 500)
                await page.wait_for_timeout(wait_time)
                
                # Capture frame after each step
                frame = await self._capture_frame(page)
                frames.append(frame)
                
                # Add extra frames for the screenshot action to show the state longer
                if action == "screenshot":
                    for _ in range(3):  # Hold this frame longer
                        frames.append(frame.copy())
                
            except Exception as e:
                logger.warning(f"Step failed ({action}): {e}")
                # Still capture a frame even if action failed
                try:
                    frame = await self._capture_frame(page)
                    frames.append(frame)
                except:
                    pass
        
        return frames
    
    def _frames_to_gif(self, frames: List[Image.Image], duration: int = 400) -> bytes:
        """Convert frames to animated GIF."""
        if not frames:
            return b''
        
        # Resize frames for reasonable file size while maintaining clarity
        target_width = 800
        resized_frames = []
        
        for frame in frames:
            # Calculate proportional height
            aspect_ratio = frame.height / frame.width
            target_height = int(target_width * aspect_ratio)
            
            # High-quality resize
            resized = frame.resize(
                (target_width, target_height), 
                Image.Resampling.LANCZOS
            )
            
            # Convert to palette mode for GIF
            resized = resized.convert('P', palette=Image.ADAPTIVE, colors=256)
            resized_frames.append(resized)
        
        # Create GIF
        output = io.BytesIO()
        resized_frames[0].save(
            output,
            format='GIF',
            save_all=True,
            append_images=resized_frames[1:],
            duration=duration,
            loop=0,  # Loop forever
            optimize=False  # Don't optimize to maintain quality
        )
        
        return output.getvalue()
    
    async def record_workflow(self, workflow_id: str) -> Dict:
        """
        Record a workflow as an animated GIF.
        
        Args:
            workflow_id: ID of the workflow to record
            
        Returns:
            Dict with workflow info and base64-encoded GIF
        """
        if workflow_id not in WORKFLOW_CONFIG:
            return {"error": f"Unknown workflow: {workflow_id}"}
        
        config = WORKFLOW_CONFIG[workflow_id]
        logger.info(f"Recording workflow: {config['name']}")
        
        if not self.browser:
            await self.initialize()
        
        context = None
        page = None
        
        try:
            # Create new browser context
            context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 720}
            )
            page = await context.new_page()
            
            # Login
            if not await self._login(page):
                return {"error": "Failed to login"}
            
            # Execute workflow steps and capture frames
            frames = await self._execute_workflow_steps(page, config["steps"])
            
            if not frames:
                return {"error": "No frames captured"}
            
            # Convert to GIF
            gif_data = self._frames_to_gif(frames, self.frame_delay)
            gif_base64 = base64.b64encode(gif_data).decode('utf-8')
            
            # Store in database
            workflow_doc = {
                "id": workflow_id,
                "name": config["name"],
                "description": config["description"],
                "section": config["section"],
                "guide": config["guide"],
                "gif_data": gif_base64,
                "content_type": "image/gif",
                "frame_count": len(frames),
                "duration_seconds": len(frames) * self.frame_delay / 1000,
                "file_size_bytes": len(gif_data),
                "captured_at": datetime.now(timezone.utc),
                "status": "captured"
            }
            
            await self.db.documentation_workflows.update_one(
                {"id": workflow_id},
                {"$set": workflow_doc},
                upsert=True
            )
            
            logger.info(f"Workflow recorded: {workflow_id} ({len(frames)} frames, {len(gif_data)} bytes)")
            
            return {
                "id": workflow_id,
                "name": config["name"],
                "description": config["description"],
                "frame_count": len(frames),
                "duration_seconds": len(frames) * self.frame_delay / 1000,
                "file_size_bytes": len(gif_data),
                "status": "captured"
            }
            
        except Exception as e:
            logger.error(f"Failed to record workflow {workflow_id}: {e}")
            return {"error": str(e)}
            
        finally:
            if page:
                await page.close()
            if context:
                await context.close()
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """Get a recorded workflow GIF."""
        workflow = await self.db.documentation_workflows.find_one(
            {"id": workflow_id},
            {"_id": 0}
        )
        return workflow
    
    async def get_all_workflows(self) -> List[Dict]:
        """Get all available workflows (with or without recordings)."""
        workflows = []
        
        for workflow_id, config in WORKFLOW_CONFIG.items():
            recorded = await self.db.documentation_workflows.find_one(
                {"id": workflow_id},
                {"_id": 0, "gif_data": 0}  # Exclude large gif_data
            )
            
            if recorded:
                workflows.append(recorded)
            else:
                workflows.append({
                    "id": workflow_id,
                    "name": config["name"],
                    "description": config["description"],
                    "section": config["section"],
                    "guide": config["guide"],
                    "status": "not_recorded"
                })
        
        return workflows
    
    async def record_all_workflows(self) -> Dict:
        """Record all configured workflows."""
        results = {"success": [], "failed": []}
        
        for workflow_id in WORKFLOW_CONFIG:
            result = await self.record_workflow(workflow_id)
            
            if "error" in result:
                results["failed"].append({
                    "id": workflow_id,
                    "error": result["error"]
                })
            else:
                results["success"].append(result)
        
        return results


# Singleton instance
_workflow_service: Optional[WorkflowGifService] = None


def get_workflow_service(db) -> WorkflowGifService:
    """Get or create the singleton workflow service instance."""
    global _workflow_service
    if _workflow_service is None:
        _workflow_service = WorkflowGifService(db)
    return _workflow_service
