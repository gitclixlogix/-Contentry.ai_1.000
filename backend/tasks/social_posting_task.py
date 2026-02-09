"""
Social Media Posting Background Task

Posts content to social media platforms via Ayrshare API.
This is the async version of the /api/social/posts endpoint.
"""

import logging
import os
import httpx
from typing import Dict, Any, Callable, Coroutine, List
from datetime import datetime, timezone
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorDatabase

from services.job_queue_service import Job, JobProgress

logger = logging.getLogger(__name__)

# Ayrshare API configuration
AYRSHARE_BASE_URL = "https://app.ayrshare.com/api"

SUPPORTED_PLATFORMS = [
    "twitter", "facebook", "instagram", "linkedin", 
    "tiktok", "pinterest", "youtube", "threads", 
    "bluesky", "reddit", "gmb"
]


def get_ayrshare_headers(profile_key: str = None) -> Dict[str, str]:
    """Get Ayrshare API headers."""
    api_key = os.getenv("AYRSHARE_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    if profile_key:
        headers["Profile-Key"] = profile_key
    return headers


async def social_posting_handler(
    job: Job,
    db: AsyncIOMotorDatabase,
    progress_callback: Callable[[JobProgress], Coroutine]
) -> Dict[str, Any]:
    """
    Execute social media posting task.
    
    Args:
        job: Job containing input data
        db: Database connection
        progress_callback: Callback to report progress
        
    Returns:
        Posting result dictionary
    """
    input_data = job.input_data
    user_id = job.user_id
    
    # Extract parameters
    content = input_data.get("content", "")
    platforms = input_data.get("platforms", [])
    profile_id = input_data.get("profile_id")
    media_urls = input_data.get("media_urls", [])
    schedule_date = input_data.get("schedule_date")
    
    if not content:
        raise ValueError("Content is required")
    
    if not platforms:
        raise ValueError("At least one platform is required")
    
    # Validate platforms
    invalid_platforms = [p for p in platforms if p not in SUPPORTED_PLATFORMS]
    if invalid_platforms:
        raise ValueError(f"Unsupported platforms: {', '.join(invalid_platforms)}")
    
    # Step 1: Get profile
    await progress_callback(JobProgress(
        current_step="Loading profile",
        total_steps=4,
        current_step_num=1,
        percentage=10,
        message="Loading social media profile..."
    ))
    
    profile = None
    if profile_id:
        profile = await db.social_profiles.find_one(
            {"id": profile_id, "user_id": user_id}
        )
        if not profile:
            raise ValueError("Profile not found")
    else:
        profile = await db.social_profiles.find_one({"user_id": user_id})
        if not profile:
            raise ValueError("No social profile found. Please create a profile first.")
    
    # Step 2: Validate content for platforms
    await progress_callback(JobProgress(
        current_step="Validating content",
        total_steps=4,
        current_step_num=2,
        percentage=25,
        message="Validating content for selected platforms..."
    ))
    
    # Platform character limits
    platform_limits = {
        "twitter": 280,
        "threads": 500,
        "linkedin": 3000,
        "facebook": 63206,
        "instagram": 2200,
        "tiktok": 2200,
        "pinterest": 500,
        "youtube": 5000,
    }
    
    warnings = []
    for platform in platforms:
        limit = platform_limits.get(platform)
        if limit and len(content) > limit:
            warnings.append(f"{platform}: Content exceeds {limit} character limit")
    
    # Step 3: Post to Ayrshare
    await progress_callback(JobProgress(
        current_step="Posting content",
        total_steps=4,
        current_step_num=3,
        percentage=50,
        message="Publishing to social media platforms..."
    ))
    
    # Build Ayrshare payload
    payload = {
        "post": content,
        "platforms": platforms
    }
    
    if media_urls:
        payload["mediaUrls"] = media_urls
    
    if schedule_date:
        payload["scheduleDate"] = schedule_date
    
    # Get profile key
    profile_key = profile.get("profile_key") if profile.get("is_ayrshare_profile") else None
    
    # Make API request
    async with httpx.AsyncClient() as http_client:
        response = await http_client.post(
            f"{AYRSHARE_BASE_URL}/post",
            headers=get_ayrshare_headers(profile_key),
            json=payload,
            timeout=60.0
        )
    
    data = response.json()
    logger.info(f"Ayrshare response for job {job.job_id}: {data}")
    
    # Check for plan-related errors
    if data.get("code") == 169 or data.get("action") == "Paid Plan Required":
        raise ValueError(
            "Ayrshare Premium or Business Plan required to post. "
            "Please upgrade at https://www.ayrshare.com/pricing"
        )
    
    # Check for platform linking errors
    errors = data.get("errors", [])
    not_linked = [e.get("platform") for e in errors if e.get("code") == 156]
    if not_linked:
        raise ValueError(
            f"Platforms not linked: {', '.join(not_linked)}. "
            "Please link your social accounts in the Ayrshare dashboard."
        )
    
    # Check for other errors
    if data.get("status") == "error" or (errors and len(errors) > 0):
        error_messages = [e.get("message", "Unknown error") for e in errors]
        raise ValueError(f"Posting failed: {'; '.join(error_messages)}")
    
    # Step 4: Save post record
    await progress_callback(JobProgress(
        current_step="Saving record",
        total_steps=4,
        current_step_num=4,
        percentage=90,
        message="Saving post record..."
    ))
    
    post_doc = {
        "id": str(uuid4()),
        "job_id": job.job_id,
        "user_id": user_id,
        "profile_id": profile["id"],
        "ayrshare_id": data.get("id"),
        "content": content,
        "platforms": platforms,
        "media_urls": media_urls,
        "schedule_date": schedule_date,
        "status": "scheduled" if schedule_date else data.get("status", "success"),
        "post_ids": data.get("postIds", []),
        "errors": errors,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.social_posts.insert_one(post_doc)
    
    result = {
        "post_id": post_doc["id"],
        "ayrshare_id": data.get("id"),
        "status": post_doc["status"],
        "platforms": platforms,
        "post_ids": data.get("postIds", []),
        "errors": errors,
        "warnings": warnings,
        "posted_at": datetime.now(timezone.utc).isoformat(),
        "job_id": job.job_id
    }
    
    logger.info(f"Social posting completed for job {job.job_id}: {result['status']}")
    
    return result
