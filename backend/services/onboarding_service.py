"""
Onboarding Service
==================
Handles user onboarding flow, progress tracking, and wizard state management.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "contentry_db")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


class OnboardingService:
    """
    Service for managing user onboarding wizard.
    """
    
    # Wizard steps
    STEPS = [
        "welcome",
        "website",
        "document", 
        "analyze",
        "complete"
    ]
    
    async def get_onboarding_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get the current onboarding status for a user.
        Returns whether onboarding is complete and current progress.
        """
        user = await db.users.find_one(
            {"id": user_id},
            {"_id": 0, "has_completed_onboarding": 1, "onboarding_progress": 1, "enterprise_id": 1}
        )
        
        if not user:
            return {
                "has_completed_onboarding": False,
                "should_show_wizard": True,
                "current_step": "welcome",
                "step_index": 0,
                "data": {}
            }
        
        # Enterprise users skip onboarding
        if user.get("enterprise_id"):
            return {
                "has_completed_onboarding": True,
                "should_show_wizard": False,
                "current_step": "complete",
                "step_index": 4,
                "data": {},
                "reason": "enterprise_user"
            }
        
        has_completed = user.get("has_completed_onboarding", False)
        progress = user.get("onboarding_progress", {})
        
        return {
            "has_completed_onboarding": has_completed,
            "should_show_wizard": not has_completed,
            "current_step": progress.get("current_step", "welcome"),
            "step_index": self.STEPS.index(progress.get("current_step", "welcome")),
            "data": progress.get("data", {}),
            "profile_id": progress.get("profile_id")
        }
    
    async def save_progress(
        self,
        user_id: str,
        current_step: str,
        data: Dict[str, Any] = None,
        profile_id: str = None
    ) -> Dict[str, Any]:
        """
        Save the user's onboarding progress.
        """
        if current_step not in self.STEPS:
            raise ValueError(f"Invalid step: {current_step}")
        
        progress = {
            "current_step": current_step,
            "data": data or {},
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if profile_id:
            progress["profile_id"] = profile_id
        
        await db.users.update_one(
            {"id": user_id},
            {
                "$set": {
                    "onboarding_progress": progress
                }
            }
        )
        
        return {
            "success": True,
            "current_step": current_step,
            "step_index": self.STEPS.index(current_step),
            "data": data
        }
    
    async def complete_onboarding(self, user_id: str) -> Dict[str, Any]:
        """
        Mark the user's onboarding as complete.
        """
        await db.users.update_one(
            {"id": user_id},
            {
                "$set": {
                    "has_completed_onboarding": True,
                    "onboarding_completed_at": datetime.now(timezone.utc).isoformat(),
                    "onboarding_progress.current_step": "complete"
                }
            }
        )
        
        logger.info(f"User {user_id} completed onboarding")
        
        return {
            "success": True,
            "has_completed_onboarding": True,
            "message": "Onboarding completed successfully"
        }
    
    async def skip_onboarding(self, user_id: str) -> Dict[str, Any]:
        """
        Allow user to skip onboarding.
        """
        await db.users.update_one(
            {"id": user_id},
            {
                "$set": {
                    "has_completed_onboarding": True,
                    "onboarding_skipped": True,
                    "onboarding_skipped_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        logger.info(f"User {user_id} skipped onboarding")
        
        return {
            "success": True,
            "has_completed_onboarding": True,
            "skipped": True,
            "message": "Onboarding skipped"
        }
    
    async def create_default_profile(
        self,
        user_id: str,
        website_url: str = None,
        website_content: str = None
    ) -> Dict[str, Any]:
        """
        Create a default strategic profile for the user during onboarding.
        """
        profile_id = f"profile_{uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        
        profile = {
            "id": profile_id,
            "user_id": user_id,
            "name": "My First Profile",
            "description": "Your default brand profile created during onboarding",
            "tone": "professional",
            "style_guidelines": "",
            "target_audience": "",
            "brand_voice": "",
            "key_messages": [],
            "prohibited_words": [],
            "reference_websites": [],
            "created_at": now,
            "updated_at": now,
            "is_default": True,
            "created_via": "onboarding"
        }
        
        # Add website if provided
        if website_url:
            profile["reference_websites"] = [{
                "url": website_url,
                "content": website_content,
                "scraped_at": now if website_content else None
            }]
        
        await db.strategic_profiles.insert_one(profile)
        profile.pop("_id", None)
        
        # Save profile ID to onboarding progress
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"onboarding_progress.profile_id": profile_id}}
        )
        
        logger.info(f"Created default profile {profile_id} for user {user_id}")
        
        return profile
    
    async def get_or_create_onboarding_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the user's onboarding profile, or create one if it doesn't exist.
        """
        # Check if user has an onboarding profile
        user = await db.users.find_one(
            {"id": user_id},
            {"_id": 0, "onboarding_progress": 1}
        )
        
        profile_id = user.get("onboarding_progress", {}).get("profile_id") if user else None
        
        if profile_id:
            profile = await db.strategic_profiles.find_one(
                {"id": profile_id},
                {"_id": 0}
            )
            if profile:
                return profile
        
        # Create a new default profile
        return await self.create_default_profile(user_id)


# Singleton instance
onboarding_service = OnboardingService()
