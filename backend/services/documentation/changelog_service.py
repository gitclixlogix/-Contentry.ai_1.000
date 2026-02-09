"""
Living Changelog Service

Automatically detects UI changes and generates a self-updating changelog.
Uses AI to describe detected changes in user-friendly language.

Features:
- Compares current UI screenshots against a baseline
- Detects major changes (new pages, new sections)
- Uses Emergent LLM to generate natural descriptions
- Creates timestamped entries for the "What's New" page
"""

import asyncio
import base64
import hashlib
import io
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from PIL import Image
import imagehash  # For perceptual hashing

logger = logging.getLogger(__name__)

# Pages to monitor for changes
MONITORED_PAGES = [
    {"id": "dashboard", "name": "Dashboard", "path": "/contentry"},
    {"id": "admin-dashboard", "name": "Admin Dashboard", "path": "/contentry/admin"},
    {"id": "analytics", "name": "Analytics", "path": "/contentry/analytics"},
    {"id": "content-moderation", "name": "Content Moderation", "path": "/contentry/content-moderation"},
    {"id": "settings", "name": "Settings", "path": "/contentry/settings"},
    {"id": "social-accounts", "name": "Social Accounts", "path": "/contentry/settings/social"},
    {"id": "team-management", "name": "Team Management", "path": "/contentry/enterprise/settings/team"},
    {"id": "documentation-hub", "name": "Documentation Hub", "path": "/contentry/documentation"},
    {"id": "projects-hub", "name": "Projects Hub", "path": "/contentry/projects"},
]

# Change detection thresholds
MAJOR_CHANGE_THRESHOLD = 15  # Hamming distance for perceptual hash (higher = more different)
SIGNIFICANT_CHANGE_THRESHOLD = 10


class ChangelogService:
    """
    Service for detecting UI changes and generating changelog entries.
    """
    
    def __init__(self, db):
        self.db = db
        self.llm_key = os.environ.get('EMERGENT_LLM_KEY')
        
    async def _get_llm_description(self, page_name: str, change_type: str, details: str) -> str:
        """
        Generate a user-friendly description of the change using AI.
        """
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            import uuid
            
            prompt = f"""Page: {page_name}
Change Type: {change_type}
Details: {details}

Rules:
- Keep it to ONE sentence only
- Be specific about what changed
- Use present tense
- Focus on user benefit when possible
- Example format: "A new 'Export' button has been added to the Analytics page."

Generate the description:"""

            # Initialize chat with required session_id and system_message
            chat = LlmChat(
                api_key=self.llm_key,
                session_id=f"changelog_{uuid.uuid4().hex[:8]}",
                system_message="You are a product update writer. Generate a single, clear, user-friendly sentence describing a UI change."
            )
            
            # LlmChat.send_message is async, so await it directly
            response = await chat.send_message(UserMessage(text=prompt))
            
            # The response is a string directly
            return response.strip() if isinstance(response, str) else str(response).strip()
            
        except Exception as e:
            logger.error(f"Failed to generate AI description: {e}")
            # Fallback to template description
            return f"Changes detected on the {page_name} page."
    
    def _compute_image_hash(self, image_data: bytes) -> str:
        """Compute perceptual hash of an image for comparison."""
        try:
            image = Image.open(io.BytesIO(base64.b64decode(image_data)))
            # Use perceptual hash for similarity detection
            phash = imagehash.phash(image)
            return str(phash)
        except Exception as e:
            logger.error(f"Failed to compute image hash: {e}")
            return ""
    
    def _compute_hash_difference(self, hash1: str, hash2: str) -> int:
        """
        Compute the Hamming distance between two perceptual hashes.
        Higher = more different.
        """
        if not hash1 or not hash2:
            return 100  # Treat as very different if hash missing
        
        try:
            h1 = imagehash.hex_to_hash(hash1)
            h2 = imagehash.hex_to_hash(hash2)
            return h1 - h2
        except Exception as e:
            logger.error(f"Failed to compare hashes: {e}")
            return 100
    
    async def _get_baseline(self, page_id: str) -> Optional[Dict]:
        """Get the baseline screenshot for a page."""
        baseline = await self.db.documentation_baselines.find_one(
            {"page_id": page_id},
            {"_id": 0}
        )
        return baseline
    
    async def _update_baseline(self, page_id: str, image_hash: str, captured_at: datetime):
        """Update the baseline for a page."""
        await self.db.documentation_baselines.update_one(
            {"page_id": page_id},
            {
                "$set": {
                    "page_id": page_id,
                    "image_hash": image_hash,
                    "captured_at": captured_at,
                    "updated_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
    
    async def detect_changes(self) -> List[Dict]:
        """
        Compare current screenshots against baselines and detect changes.
        
        Returns:
            List of detected changes with descriptions
        """
        changes = []
        
        for page_config in MONITORED_PAGES:
            page_id = page_config["id"]
            page_name = page_config["name"]
            
            try:
                # Get current screenshot
                current = await self.db.documentation_screenshots.find_one(
                    {"id": page_id},
                    {"_id": 0}
                )
                
                if not current or not current.get("image_data"):
                    continue
                
                # Compute current hash
                current_hash = self._compute_image_hash(current["image_data"])
                current_time = current.get("captured_at", datetime.now(timezone.utc))
                
                # Get baseline
                baseline = await self._get_baseline(page_id)
                
                if not baseline:
                    # First time seeing this page - set as baseline
                    await self._update_baseline(page_id, current_hash, current_time)
                    
                    # Log as new page
                    change = {
                        "type": "new_page",
                        "page_id": page_id,
                        "page_name": page_name,
                        "page_path": page_config["path"],
                        "hash_difference": 100,
                        "detected_at": datetime.now(timezone.utc)
                    }
                    
                    # Generate AI description
                    change["description"] = await self._get_llm_description(
                        page_name,
                        "new_page",
                        "A completely new page has been added to the application"
                    )
                    change["screenshot_data"] = current["image_data"]
                    
                    changes.append(change)
                    continue
                
                # Compare with baseline
                hash_diff = self._compute_hash_difference(baseline.get("image_hash", ""), current_hash)
                
                if hash_diff >= MAJOR_CHANGE_THRESHOLD:
                    # Major change detected
                    change = {
                        "type": "major_change",
                        "page_id": page_id,
                        "page_name": page_name,
                        "page_path": page_config["path"],
                        "hash_difference": hash_diff,
                        "detected_at": datetime.now(timezone.utc)
                    }
                    
                    # Generate AI description
                    change["description"] = await self._get_llm_description(
                        page_name,
                        "major_update",
                        f"Significant UI changes detected (difference score: {hash_diff}). This could include new sections, redesigned components, or major feature additions."
                    )
                    change["screenshot_data"] = current["image_data"]
                    
                    changes.append(change)
                    
                    # Update baseline to new screenshot
                    await self._update_baseline(page_id, current_hash, current_time)
                    
                elif hash_diff >= SIGNIFICANT_CHANGE_THRESHOLD:
                    # Notable change but not major
                    logger.info(f"Significant change detected on {page_name} (diff: {hash_diff}), but below major threshold")
                
            except Exception as e:
                logger.error(f"Error detecting changes for {page_id}: {e}")
        
        return changes
    
    async def add_changelog_entry(self, change: Dict) -> str:
        """
        Add a new entry to the changelog.
        
        Args:
            change: Dict with change details
            
        Returns:
            ID of the created entry
        """
        entry_id = f"change_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{change['page_id']}"
        
        entry = {
            "id": entry_id,
            "type": change.get("type", "update"),
            "page_id": change.get("page_id"),
            "page_name": change.get("page_name"),
            "page_path": change.get("page_path"),
            "description": change.get("description", ""),
            "screenshot_data": change.get("screenshot_data"),
            "hash_difference": change.get("hash_difference", 0),
            "detected_at": change.get("detected_at", datetime.now(timezone.utc)),
            "created_at": datetime.now(timezone.utc)
        }
        
        await self.db.documentation_changelog.insert_one(entry)
        logger.info(f"Changelog entry created: {entry_id}")
        
        return entry_id
    
    async def scan_for_changes(self) -> Dict:
        """
        Perform a full scan for changes and update the changelog.
        
        Returns:
            Summary of detected changes
        """
        logger.info("Starting changelog scan...")
        
        changes = await self.detect_changes()
        
        entries_created = []
        for change in changes:
            entry_id = await self.add_changelog_entry(change)
            entries_created.append({
                "id": entry_id,
                "type": change["type"],
                "page": change["page_name"],
                "description": change["description"]
            })
        
        logger.info(f"Changelog scan complete. {len(entries_created)} new entries.")
        
        return {
            "scanned_pages": len(MONITORED_PAGES),
            "changes_detected": len(changes),
            "entries_created": entries_created
        }
    
    async def get_changelog(self, limit: int = 50, page: int = 1) -> Dict:
        """
        Get changelog entries with pagination.
        
        Args:
            limit: Number of entries per page
            page: Page number (1-indexed)
            
        Returns:
            Dict with entries and pagination info
        """
        skip = (page - 1) * limit
        
        entries = await self.db.documentation_changelog.find(
            {},
            {"_id": 0}
        ).sort("detected_at", -1).skip(skip).limit(limit).to_list(limit)
        
        total = await self.db.documentation_changelog.count_documents({})
        
        return {
            "entries": entries,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    
    async def get_recent_changes(self, days: int = 30) -> List[Dict]:
        """
        Get recent changelog entries within the specified number of days.
        """
        from datetime import timedelta
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        entries = await self.db.documentation_changelog.find(
            {"detected_at": {"$gte": cutoff}},
            {"_id": 0, "screenshot_data": 0}  # Exclude large screenshot data
        ).sort("detected_at", -1).to_list(100)
        
        return entries


# Singleton instance
_changelog_service: Optional[ChangelogService] = None


def get_changelog_service(db) -> ChangelogService:
    """Get or create the singleton changelog service instance."""
    global _changelog_service
    if _changelog_service is None:
        _changelog_service = ChangelogService(db)
    return _changelog_service
