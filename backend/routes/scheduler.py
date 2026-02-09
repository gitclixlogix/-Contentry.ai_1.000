"""
Scheduler API Routes
Handles manual triggers and status checks for the post scheduler

Security Update (ARCH-005 Phase 5.1b):
- Added @require_permission decorators for RBAC enforcement
"""

from fastapi import APIRouter, HTTPException, Header, Depends, Request
from typing import Optional
from datetime import datetime, timezone
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db

# ARCH-005: Authorization decorator
from services.authorization_decorator import require_permission

router = APIRouter(prefix="/scheduler", tags=["scheduler"])
logger = logging.getLogger(__name__)

# Will be set by server.py
db = None

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    """Set database instance"""
    global db
    db = database


@router.get("/status")
@require_permission("scheduler.view")
async def get_scheduler_status(request: Request, x_user_id: Optional[str] = Header(None), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get scheduler service status and statistics
    """
    try:
        # Count scheduled posts
        total_scheduled = await db_conn.posts.count_documents({"status": "scheduled"})
        
        # Count due posts
        now = datetime.now(timezone.utc).isoformat()
        due_posts = await db_conn.posts.count_documents({
            "status": "scheduled",
            "post_time": {"$lte": now}
        })
        
        # Get recently published posts (last 24 hours)
        yesterday = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        recently_published = await db_conn.posts.count_documents({
            "status": "published",
            "published_at": {"$gte": yesterday}
        })
        
        # Get next scheduled post
        next_post = await db_conn.posts.find_one(
            {"status": "scheduled"},
            {"_id": 0, "id": 1, "title": 1, "post_time": 1, "platforms": 1},
            sort=[("post_time", 1)]
        )
        
        return {
            "scheduler_active": True,
            "total_scheduled_posts": total_scheduled,
            "due_posts": due_posts,
            "recently_published": recently_published,
            "next_scheduled_post": next_post,
            "check_interval": "120 seconds",
            "features": {
                "pre_publish_reanalysis": True,
                "auto_posting": True,
                "multi_platform": True
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(500, f"Failed to get scheduler status: {str(e)}")


@router.post("/trigger/{post_id}")
@require_permission("social.post")
async def trigger_scheduled_post(
    request: Request,
    post_id: str,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Manually trigger a scheduled post to be published immediately.
    
    Security (ARCH-005): Requires social.post permission.
    """
    try:
        from services.post_scheduler import PostScheduler
        
        # Get the post
        post = await db_conn.posts.find_one({"id": post_id, "user_id": x_user_id}, {"_id": 0})
        
        if not post:
            raise HTTPException(404, "Post not found")
        
        if post.get("status") != "scheduled":
            raise HTTPException(400, f"Post is not scheduled (current status: {post.get('status')})")
        
        # Process the post
        scheduler = PostScheduler()
        result = await scheduler.process_scheduled_post(post)
        
        return {
            "message": "Post triggered for publishing",
            "post_id": post_id,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering post {post_id}: {str(e)}")
        raise HTTPException(500, f"Failed to trigger post: {str(e)}")


@router.post("/reanalyze/{post_id}")
@require_permission("content.analyze")
async def reanalyze_scheduled_post(
    request: Request,
    post_id: str,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Manually trigger reanalysis of a scheduled post without publishing
    """
    try:
        from services.post_scheduler import PostScheduler
        
        # Get the post
        post = await db_conn.posts.find_one({"id": post_id, "user_id": x_user_id}, {"_id": 0})
        
        if not post:
            raise HTTPException(404, "Post not found")
        
        # Reanalyze the post
        scheduler = PostScheduler()
        reanalysis = await scheduler.reanalyze_content(post)
        
        # Update post with reanalysis results
        await db_conn.posts.update_one(
            {"id": post_id},
            {
                "$set": {
                    "pre_publish_reanalysis": reanalysis,
                    "reanalyzed_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return {
            "message": "Post reanalyzed successfully",
            "post_id": post_id,
            "reanalysis": reanalysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reanalyzing post {post_id}: {str(e)}")
        raise HTTPException(500, f"Failed to reanalyze post: {str(e)}")


@router.get("/posts/scheduled")
@require_permission("content.view_own")
async def get_scheduled_posts(
    request: Request,
    x_user_id: str = Header(..., alias="X-User-ID"),
    limit: int = 50,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get all scheduled posts for the user
    """
    try:
        posts = await db_conn.posts.find(
            {"user_id": x_user_id, "status": "scheduled"},
            {"_id": 0}
        ).sort("post_time", 1).limit(limit).to_list(limit)
        
        return {
            "scheduled_posts": posts,
            "total": len(posts)
        }
        
    except Exception as e:
        logger.error(f"Error getting scheduled posts: {str(e)}")
        raise HTTPException(500, f"Failed to get scheduled posts: {str(e)}")


@router.post("/schedule-prompt")
@require_permission("scheduler.manage")
async def schedule_prompt_for_generation(
    request: Request,
    data: dict,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Schedule a prompt for content generation at a specified time.
    
    The system will:
    1. Generate content from the prompt at the scheduled time
    2. If auto_post is True:
       - Run full analysis 5 minutes before posting
       - If score >= 85, auto-post to platforms (unless approval required)
       - If score < 85, save to posts and create notification for user review
    3. If auto_post is False:
       - Generate content and save to "All Posts" for user to review/post manually
    4. In Company Workspace:
       - If user needs approval, content will be submitted for approval before posting
    """
    from uuid import uuid4
    
    try:
        prompt = data.get("prompt")
        schedule_type = data.get("schedule_type", "once")  # once, daily, weekly, monthly
        schedule_time = data.get("schedule_time", "09:00")
        start_date = data.get("start_date")
        schedule_days = data.get("schedule_days", [])
        platforms = data.get("platforms", [])
        auto_post = data.get("auto_post", False)
        tone = data.get("tone", "professional")
        reanalyze_before_post = data.get("reanalyze_before_post", True)
        workspace_type = data.get("workspace_type", "personal")  # personal or enterprise
        enterprise_id = data.get("enterprise_id")
        
        if not prompt:
            raise HTTPException(400, "Prompt is required")
        
        if not start_date:
            raise HTTPException(400, "Start date is required")
        
        # Check if user needs approval (for enterprise workspace)
        needs_approval = False
        if workspace_type == "enterprise" and enterprise_id:
            # Check user's role to determine if they need approval
            user = await db_conn.users.find_one({"id": x_user_id}, {"_id": 0, "role": 1})
            if user and user.get("role") == "creator":
                needs_approval = True
        
        # Calculate next scheduled time
        scheduled_datetime = f"{start_date}T{schedule_time}:00"
        
        # Create scheduled prompt record
        scheduled_prompt = {
            "id": str(uuid4()),
            "user_id": x_user_id,
            "prompt": prompt,
            "tone": tone,
            "platforms": platforms,
            "schedule_type": schedule_type,
            "schedule_time": schedule_time,
            "start_date": start_date,
            "schedule_days": schedule_days,
            "next_run": scheduled_datetime,
            "auto_post": auto_post,
            "reanalyze_before_post": reanalyze_before_post,
            "min_score_for_auto_post": 85,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_run": None,
            "run_count": 0,
            "last_generated_post_id": None,
            "workspace_type": workspace_type,
            "enterprise_id": enterprise_id,
            "needs_approval": needs_approval,  # If true, generated content goes to approval queue
            "approval_status": "pending" if needs_approval else None
        }
        
        await db_conn.scheduled_prompts.insert_one(scheduled_prompt)
        
        # Remove MongoDB _id before returning
        scheduled_prompt.pop("_id", None)
        
        approval_note = ""
        if needs_approval:
            approval_note = " Content will be submitted for manager approval before posting."
        
        return {
            "success": True,
            "message": f"Prompt scheduled for {scheduled_datetime}",
            "scheduled_prompt": scheduled_prompt,
            "auto_post": auto_post,
            "needs_approval": needs_approval,
            "note": "Content will be generated at the scheduled time" + 
                    (". If analysis score >= 85, it will be auto-posted." if auto_post and not needs_approval else ". It will appear in All Posts for your review.") +
                    approval_note
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling prompt: {str(e)}")
        raise HTTPException(500, f"Failed to schedule prompt: {str(e)}")


@router.get("/scheduled-prompts")
@require_permission("scheduler.view")
async def get_scheduled_prompts(
    request: Request,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all scheduled prompts for a user"""
    try:
        prompts = await db_conn.scheduled_prompts.find(
            {"user_id": x_user_id},
            {"_id": 0}
        ).sort("next_run", 1).to_list(100)
        
        return prompts
        
    except Exception as e:
        logger.error(f"Error getting scheduled prompts: {str(e)}")
        raise HTTPException(500, f"Failed to get scheduled prompts: {str(e)}")


@router.delete("/scheduled-prompts/{prompt_id}")
@require_permission("scheduler.manage")
async def delete_scheduled_prompt(
    request: Request,
    prompt_id: str,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a scheduled prompt"""
    try:
        result = await db_conn.scheduled_prompts.delete_one({
            "id": prompt_id,
            "user_id": x_user_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(404, "Scheduled prompt not found")
        
        return {"success": True, "message": "Scheduled prompt deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scheduled prompt: {str(e)}")
        raise HTTPException(500, f"Failed to delete scheduled prompt: {str(e)}")


@router.put("/scheduled-prompts/{prompt_id}/toggle")
@require_permission("scheduler.manage")
async def toggle_scheduled_prompt(
    request: Request,
    prompt_id: str,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Toggle a scheduled prompt active/paused"""
    try:
        prompt = await db_conn.scheduled_prompts.find_one({
            "id": prompt_id,
            "user_id": x_user_id
        })
        
        if not prompt:
            raise HTTPException(404, "Scheduled prompt not found")
        
        new_status = "paused" if prompt.get("status") == "active" else "active"
        
        await db_conn.scheduled_prompts.update_one(
            {"id": prompt_id},
            {"$set": {"status": new_status}}
        )
        
        return {"success": True, "status": new_status}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling scheduled prompt: {str(e)}")
        raise HTTPException(500, f"Failed to toggle scheduled prompt: {str(e)}")


@router.put("/scheduled-prompts/{prompt_id}")
@require_permission("scheduler.manage")
async def update_scheduled_prompt(
    request: Request,
    prompt_id: str,
    update_data: dict,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update a scheduled prompt"""
    try:
        prompt = await db_conn.scheduled_prompts.find_one({
            "id": prompt_id,
            "user_id": x_user_id
        })
        
        if not prompt:
            raise HTTPException(404, "Scheduled prompt not found")
        
        # Build update fields
        update_fields = {}
        allowed_fields = ['prompt', 'schedule_type', 'schedule_time', 'auto_post', 'platforms', 'hashtag_count', 'tone']
        
        for field in allowed_fields:
            if field in update_data:
                update_fields[field] = update_data[field]
        
        if update_fields:
            # Recalculate next_run if schedule changed
            if 'schedule_time' in update_fields or 'schedule_type' in update_fields:
                from datetime import datetime, timezone, timedelta
                schedule_time = update_fields.get('schedule_time', prompt.get('schedule_time', '09:00'))
                hour, minute = map(int, schedule_time.split(':'))
                now = datetime.now(timezone.utc)
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
                update_fields['next_run'] = next_run.isoformat()
            
            update_fields['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            await db_conn.scheduled_prompts.update_one(
                {"id": prompt_id},
                {"$set": update_fields}
            )
        
        return {"success": True, "message": "Scheduled prompt updated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating scheduled prompt: {str(e)}")
        raise HTTPException(500, f"Failed to update scheduled prompt: {str(e)}")

