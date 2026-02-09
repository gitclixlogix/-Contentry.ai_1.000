"""
Posts Management Routes
Handles post CRUD, scheduling, publishing, reanalysis, and social media import

RBAC Protected: Phase 5.1b Week 6
All endpoints require appropriate content.* permissions
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Header, Depends, Request, Query
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import logging
import uuid
from models.schemas import Post, PostCreate, Notification, ContentAnalyze
from routes.content import analyze_content
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db
# Import RBAC decorator
from services.authorization_decorator import require_permission

router = APIRouter(tags=["posts"])
logger = logging.getLogger(__name__)

# Will be set by server.py
db = None
calculate_scores = None

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    """Set database instance"""
    global db
    db = database

def set_calculate_scores(func):
    """Set calculate_scores function"""
    global calculate_scores
    calculate_scores = func


@router.post("/posts")
@require_permission("content.create")
async def create_post(request: Request, post_data: PostCreate, user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Create a new post with content analysis"""
    # Analyze content first
    analysis = await analyze_content(ContentAnalyze(content=post_data.content, user_id=user_id))
    
    # Determine scheduled time (accept both scheduled_at and post_time)
    scheduled_time = post_data.scheduled_at or post_data.post_time
    
    # Determine post status based on scheduling or explicit status
    if post_data.status:
        post_status = post_data.status
    elif scheduled_time:
        post_status = "scheduled"
    else:
        post_status = "draft"
    
    # Extract cultural sensitivity score
    cultural_score = None
    if "cultural_analysis" in analysis and "overall_score" in analysis["cultural_analysis"]:
        cultural_score = float(analysis["cultural_analysis"]["overall_score"])
    
    # Extract accuracy score
    accuracy_score = None
    if "accuracy_analysis" in analysis and "accuracy_score" in analysis["accuracy_analysis"]:
        accuracy_score = float(analysis["accuracy_analysis"]["accuracy_score"])
    
    # Extract compliance analysis
    compliance_data = analysis.get("compliance_analysis", {})
    severity = compliance_data.get("severity", "none")
    violation_type = compliance_data.get("violation_type", "none")
    consequences = compliance_data.get("consequences", "none")
    
    # Calculate compliance and overall scores
    flagged_status = analysis.get("flagged_status", "good_coverage")
    scores = calculate_scores(flagged_status, cultural_score, severity, accuracy_score)
    
    post = Post(
        user_id=user_id,
        title=post_data.title,
        content=post_data.content,
        platforms=post_data.platforms,
        status=post_status,
        post_time=scheduled_time,
        flagged_status=flagged_status,
        moderation_summary=analysis.get("summary", ""),
        cultural_sensitivity_score=cultural_score,
        compliance_score=scores["compliance_score"],
        overall_score=scores["overall_score"],
        violation_severity=severity,
        violation_type=violation_type,
        potential_consequences=consequences,
        workspace_type=post_data.workspace_type or "personal",
        enterprise_id=post_data.enterprise_id
    )
    
    post_dict = post.model_dump()
    await db_conn.posts.insert_one(post_dict)
    
    # Create notification
    if post_status == "scheduled":
        notification_msg = f"Your post '{post.title}' has been scheduled for {post_data.scheduled_at}. Status: {post.flagged_status}"
    else:
        notification_msg = f"Your post '{post.title}' has been analyzed. Status: {post.flagged_status}"
    
    notification = Notification(
        user_id=user_id,
        type="alert",
        message=notification_msg
    )
    await db_conn.notifications.insert_one(notification.model_dump())
    
    return post.model_dump()


@router.get("/posts")
@require_permission("content.view_own")
async def get_posts(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    workspace: str = Query("personal", description="Workspace type: personal or enterprise"),
    enterprise_id: str = Query(None, description="Enterprise ID for company workspace"),
    limit: int = 50,
    skip: int = 0,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all posts for a user with pagination, filtered by workspace context"""
    # Cap limit at 100 to prevent memory issues
    actual_limit = min(limit, 100)
    
    # Build query based on workspace type
    if workspace == "enterprise" and enterprise_id:
        # In company workspace, show posts that are:
        # 1. Created by any user in the enterprise AND marked as company posts
        # 2. OR posts with enterprise_id set
        query = {
            "$or": [
                {"enterprise_id": enterprise_id, "workspace_type": "enterprise"},
                {"enterprise_id": enterprise_id},  # Also include posts with enterprise_id but without workspace_type
            ]
        }
    else:
        # In personal workspace, show only personal posts by this user
        # Match both user_id and author_id fields for compatibility
        query = {
            "$or": [
                {"user_id": user_id},
                {"author_id": user_id}
            ],
            "$and": [
                {"$or": [
                    {"workspace_type": {"$exists": False}},  # Legacy posts without workspace
                    {"workspace_type": "personal"},
                    {"workspace_type": None},
                    {"enterprise_id": {"$exists": False}},  # No enterprise_id means personal
                    {"enterprise_id": None}
                ]}
            ]
        }
    
    posts = await db_conn.posts.find(
        query, 
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(actual_limit).to_list(actual_limit)
    return posts


@router.get("/posts/{post_id}")
@require_permission("content.view_own")
async def get_post(request: Request, post_id: str, user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Get a specific post"""
    post = await db_conn.posts.find_one({"id": post_id, "user_id": user_id}, {"_id": 0})
    if not post:
        raise HTTPException(404, "Post not found")
    return post


@router.put("/posts/{post_id}")
@require_permission("content.edit_own")
async def update_post(request: Request, post_id: str, update_data: dict, user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Update an existing post - supports both full and partial updates"""
    
    # Check if post exists
    existing_post = await db_conn.posts.find_one({"id": post_id, "user_id": user_id})
    if not existing_post:
        raise HTTPException(404, "Post not found")
    
    # Build update fields
    update_fields = {}
    
    # Check if content is being updated - if so, reanalyze
    if 'content' in update_data and update_data['content'] != existing_post.get('content'):
        # Analyze the updated content
        analysis = await analyze_content(ContentAnalyze(content=update_data['content'], user_id=user_id))
        
        # Extract scores
        cultural_score = None
        if "cultural_analysis" in analysis and "overall_score" in analysis["cultural_analysis"]:
            cultural_score = float(analysis["cultural_analysis"]["overall_score"])
        
        accuracy_score = None
        if "accuracy_analysis" in analysis and "accuracy_score" in analysis["accuracy_analysis"]:
            accuracy_score = float(analysis["accuracy_analysis"]["accuracy_score"])
        
        compliance_data = analysis.get("compliance_analysis", {})
        severity = compliance_data.get("severity", "none")
        flagged_status = analysis.get("flagged_status", "good_coverage")
        scores = calculate_scores(flagged_status, cultural_score, severity, accuracy_score)
        
        update_fields.update({
            "content": update_data['content'],
            "flagged_status": flagged_status,
            "moderation_summary": analysis.get("summary", ""),
            "cultural_sensitivity_score": cultural_score,
            "compliance_score": scores["compliance_score"],
            "overall_score": scores["overall_score"],
            "violation_severity": severity,
        })
    
    # Handle other fields
    simple_fields = ['title', 'platforms', 'post_time', 'status', 'reanalyze_before_post']
    for field in simple_fields:
        if field in update_data:
            update_fields[field] = update_data[field]
    
    if update_fields:
        update_fields['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        await db_conn.posts.update_one(
            {"id": post_id, "user_id": user_id},
            {"$set": update_fields}
        )
    
    return {"message": "Post updated successfully", "post_id": post_id}


@router.delete("/posts/{post_id}")
@require_permission("content.delete_own")
async def delete_post(request: Request, post_id: str, user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Delete a post"""
    result = await db_conn.posts.delete_one({"id": post_id, "user_id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(404, "Post not found")
    
    return {"message": "Post deleted successfully"}


@router.get("/posts/scheduled/all")
@require_permission("content.view_own")
async def get_scheduled_posts(request: Request, user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Get all scheduled posts for a user"""
    posts = await db_conn.posts.find(
        {"user_id": user_id, "status": "scheduled"},
        {"_id": 0}
    ).sort("post_time", 1).to_list(1000)
    
    return {"scheduled_posts": posts}


@router.post("/posts/{post_id}/publish")
@require_permission("social.publish")
async def publish_post(request: Request, post_id: str, user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Manually publish a post"""
    post = await db_conn.posts.find_one({"id": post_id, "user_id": user_id})
    if not post:
        raise HTTPException(404, "Post not found")
    
    # Update post status
    await db_conn.posts.update_one(
        {"id": post_id},
        {
            "$set": {
                "status": "published",
                "published_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Create notification
    notification = Notification(
        user_id=post["user_id"],
        type="alert",
        message=f"Your scheduled post '{post['title']}' has been published!"
    )
    await db_conn.notifications.insert_one(notification.model_dump())
    
    return {"message": "Post published successfully", "post_id": post_id}


@router.post("/posts/{post_id}/reanalyze")
@require_permission("content.analyze")
async def reanalyze_post(request: Request, post_id: str, user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Reanalyze a post's content"""
    post = await db_conn.posts.find_one({"id": post_id, "user_id": user_id})
    if not post:
        raise HTTPException(404, "Post not found")
    
    # Reanalyze content
    analysis = await analyze_content(ContentAnalyze(content=post["content"], user_id=user_id))
    
    # Extract new scores
    cultural_score = None
    if "cultural_analysis" in analysis and "overall_score" in analysis["cultural_analysis"]:
        cultural_score = float(analysis["cultural_analysis"]["overall_score"])
    
    accuracy_score = None
    if "accuracy_analysis" in analysis and "accuracy_score" in analysis["accuracy_analysis"]:
        accuracy_score = float(analysis["accuracy_analysis"]["accuracy_score"])
    
    compliance_data = analysis.get("compliance_analysis", {})
    severity = compliance_data.get("severity", "none")
    flagged_status = analysis.get("flagged_status", "good_coverage")
    scores = calculate_scores(flagged_status, cultural_score, severity, accuracy_score)
    
    # Update post with new analysis
    update_data = {
        "flagged_status": flagged_status,
        "moderation_summary": analysis.get("summary", ""),
        "cultural_sensitivity_score": cultural_score,
        "compliance_score": scores["compliance_score"],
        "overall_score": scores["overall_score"],
        "violation_severity": severity,
        "reanalyzed_at": datetime.now(timezone.utc)
    }
    
    await db_conn.posts.update_one(
        {"id": post_id},
        {"$set": update_data}
    )
    
    return {
        "message": "Post reanalyzed successfully",
        "post_id": post_id,
        "new_analysis": {
            "flagged_status": flagged_status,
            "compliance_score": scores["compliance_score"],
            "overall_score": scores["overall_score"]
        }
    }


@router.post("/posts/reanalyze-all")
@require_permission("content.analyze")
async def reanalyze_all_posts(request: Request, user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Reanalyze all user's posts"""
    posts = await db_conn.posts.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    
    reanalyzed_count = 0
    for post in posts:
        try:
            # Reanalyze content
            analysis = await analyze_content(ContentAnalyze(content=post["content"], user_id=user_id))
            
            # Extract scores
            cultural_score = None
            if "cultural_analysis" in analysis and "overall_score" in analysis["cultural_analysis"]:
                cultural_score = float(analysis["cultural_analysis"]["overall_score"])
            
            accuracy_score = None
            if "accuracy_analysis" in analysis and "accuracy_score" in analysis["accuracy_analysis"]:
                accuracy_score = float(analysis["accuracy_analysis"]["accuracy_score"])
            
            compliance_data = analysis.get("compliance_analysis", {})
            severity = compliance_data.get("severity", "none")
            flagged_status = analysis.get("flagged_status", "good_coverage")
            scores = calculate_scores(flagged_status, cultural_score, severity, accuracy_score)
            
            # Update post
            await db_conn.posts.update_one(
                {"id": post["id"]},
                {
                    "$set": {
                        "flagged_status": flagged_status,
                        "moderation_summary": analysis.get("summary", ""),
                        "cultural_sensitivity_score": cultural_score,
                        "compliance_score": scores["compliance_score"],
                        "overall_score": scores["overall_score"],
                        "violation_severity": severity,
                        "reanalyzed_at": datetime.now(timezone.utc)
                    }
                }
            )
            reanalyzed_count += 1
        except Exception as e:
            logger.error(f"Error reanalyzing post {post['id']}: {str(e)}")
    
    return {
        "message": f"Reanalyzed {reanalyzed_count} out of {len(posts)} posts",
        "total_posts": len(posts),
        "reanalyzed": reanalyzed_count
    }


@router.post("/posts/{post_id}/feedback")
@require_permission("content.view_own")
async def save_analysis_feedback(request: Request, post_id: str, feedback_data: dict, user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Save user feedback on analysis accuracy"""
    post = await db_conn.posts.find_one({"id": post_id, "user_id": user_id})
    if not post:
        raise HTTPException(404, "Post not found")
    
    feedback = {
        "id": str(uuid.uuid4()),
        "post_id": post_id,
        "user_id": user_id,
        "user_correction": feedback_data.get("correction", ""),
        "disagreement_reason": feedback_data.get("reason", ""),
        "created_at": datetime.now(timezone.utc)
    }
    
    await db_conn.analysis_feedback.insert_one(feedback)
    
    return {"message": "Feedback saved successfully", "feedback_id": feedback["id"]}


@router.post("/posts/generate-user-report")
@require_permission("analytics.view_own")
async def generate_user_report(request: Request, user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Generate comprehensive analytics report for user"""
    # Get all user posts
    posts = await db_conn.posts.find({"user_id": user_id}, {"_id": 0}).to_list(10000)
    
    if not posts:
        return {
            "message": "No posts found for this user",
            "total_posts": 0
        }
    
    # Calculate statistics
    total_posts = len(posts)
    flagged_posts = [p for p in posts if p.get("flagged_status") != "good_coverage"]
    
    # Score averages
    cultural_scores = [p.get("cultural_sensitivity_score", 0) for p in posts if p.get("cultural_sensitivity_score")]
    compliance_scores = [p.get("compliance_score", 0) for p in posts if p.get("compliance_score")]
    overall_scores = [p.get("overall_score", 0) for p in posts if p.get("overall_score")]
    
    avg_cultural = sum(cultural_scores) / len(cultural_scores) if cultural_scores else 0
    avg_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0
    avg_overall = sum(overall_scores) / len(overall_scores) if overall_scores else 0
    
    # Severity distribution
    severity_dist = {
        "critical": 0,
        "severe": 0,
        "high": 0,
        "moderate": 0,
        "none": 0
    }
    for post in posts:
        severity = post.get("violation_severity", "none")
        if severity in severity_dist:
            severity_dist[severity] += 1
    
    # Platform distribution
    platform_dist = {}
    for post in posts:
        for platform in post.get("platforms", []):
            platform_dist[platform] = platform_dist.get(platform, 0) + 1
    
    report = {
        "user_id": user_id,
        "generated_at": datetime.now(timezone.utc),
        "summary": {
            "total_posts": total_posts,
            "flagged_posts": len(flagged_posts),
            "compliance_rate": round((total_posts - len(flagged_posts)) / total_posts * 100, 1) if total_posts > 0 else 100
        },
        "average_scores": {
            "cultural_sensitivity": round(avg_cultural, 1),
            "compliance": round(avg_compliance, 1),
            "overall": round(avg_overall, 1)
        },
        "severity_distribution": severity_dist,
        "platform_distribution": platform_dist,
        "recommendations": []
    }
    
    # Add recommendations based on analysis
    if avg_compliance < 70:
        report["recommendations"].append("Consider reviewing company policies before posting")
    if avg_cultural < 70:
        report["recommendations"].append("Increase awareness of cultural sensitivity in content")
    if len(flagged_posts) > total_posts * 0.2:
        report["recommendations"].append("High percentage of flagged content - consider content training")
    
    return report
