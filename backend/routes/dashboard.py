"""
Dashboard Analytics Routes
Provides comprehensive dashboard data with drill-down support, role-based widgets,
and date filtering capabilities.

Security Update (ARCH-005 Phase 5.1b):
- Added @require_permission decorators for RBAC enforcement
"""
from fastapi import APIRouter, HTTPException, Header, Query, Depends, Request
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db

# ARCH-005: Authorization decorator
from services.authorization_decorator import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'contentry_db')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


def parse_date_range(date_range: str, custom_start: Optional[str] = None, custom_end: Optional[str] = None):
    """Parse date range filter into start and end dates."""
    now = datetime.now(timezone.utc)
    
    if date_range == "this_week":
        # Start of current week (Monday)
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif date_range == "this_month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif date_range == "this_quarter":
        quarter = (now.month - 1) // 3
        start = now.replace(month=quarter * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif date_range == "last_30_days":
        start = now - timedelta(days=30)
        end = now
    elif date_range == "last_90_days":
        start = now - timedelta(days=90)
        end = now
    elif date_range == "custom" and custom_start and custom_end:
        start = datetime.fromisoformat(custom_start.replace('Z', '+00:00'))
        end = datetime.fromisoformat(custom_end.replace('Z', '+00:00'))
    else:
        # Default to last 30 days
        start = now - timedelta(days=30)
        end = now
    
    return start, end


@router.get("/stats")
@require_permission("analytics.view_own")
async def get_dashboard_stats(
    request: Request,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get personal dashboard statistics for a user.
    
    Security (ARCH-005): Requires analytics.view_own permission.
    """
    try:
        if not x_user_id:
            raise HTTPException(401, "User ID required")
        
        # Get user info
        user = await db_conn.users.find_one({"id": x_user_id}, {"_id": 0})
        if not user:
            raise HTTPException(404, "User not found")
        
        # Get basic stats for the user
        posts = await db_conn.posts.find({"user_id": x_user_id}, {"_id": 0}).to_list(10000)
        
        # Calculate basic statistics
        total_posts = len(posts)
        approved_posts = len([p for p in posts if p.get("status") in ["approved", "published"]])
        pending_posts = len([p for p in posts if p.get("status") in ["draft", "pending", "pending_approval"]])
        flagged_posts = len([p for p in posts if p.get("status") == "flagged"])
        
        # Get content analyses for score calculations
        analyses = await db_conn.content_analyses.find(
            {"user_id": x_user_id},
            {"_id": 0}
        ).to_list(10000)
        
        # Calculate average scores
        overall_scores = []
        for analysis in analyses:
            result = analysis.get("analysis_result", {})
            if result.get("overall_score"):
                overall_scores.append(result["overall_score"])
        
        avg_overall_score = round(sum(overall_scores) / len(overall_scores), 1) if overall_scores else 0
        
        return {
            "stats": {
                "total_posts": total_posts,
                "approved_posts": approved_posts,
                "pending_posts": pending_posts,
                "flagged_posts": flagged_posts,
                "avg_overall_score": avg_overall_score
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard stats error: {str(e)}")
        raise HTTPException(500, f"Failed to get dashboard stats: {str(e)}")


@router.get("/overview")
@require_permission("analytics.view_own")
async def get_dashboard_overview(
    request: Request,
    x_user_id: Optional[str] = Header(None),
    date_range: str = Query("last_30_days", description="Date range filter"),
    custom_start: Optional[str] = Query(None, description="Custom start date (ISO format)"),
    custom_end: Optional[str] = Query(None, description="Custom end date (ISO format)"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get comprehensive dashboard overview with drill-down data.
    All stats include IDs for drill-down navigation.
    
    Security (ARCH-005): Requires analytics.view_own permission.
    """
    try:
        if not x_user_id:
            raise HTTPException(401, "User ID required")
        
        # Get user info
        user = await db_conn.users.find_one({"id": x_user_id}, {"_id": 0})
        if not user:
            raise HTTPException(404, "User not found")
        
        start_date, end_date = parse_date_range(date_range, custom_start, custom_end)
        
        # Build date filter for MongoDB
        date_filter = {
            "$gte": start_date.isoformat(),
            "$lte": end_date.isoformat()
        }
        
        # Get posts with date filter
        posts_query = {"user_id": x_user_id}
        posts = await db_conn.posts.find(posts_query, {"_id": 0}).to_list(10000)
        
        # Filter by date in Python (more flexible with different date formats)
        filtered_posts = []
        for post in posts:
            created_at = post.get("created_at")
            if created_at:
                if isinstance(created_at, str):
                    try:
                        post_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        if start_date <= post_date <= end_date:
                            filtered_posts.append(post)
                    except (ValueError, TypeError):
                        filtered_posts.append(post)  # Include if date parse fails
                elif isinstance(created_at, datetime):
                    if start_date <= created_at <= end_date:
                        filtered_posts.append(post)
        
        # Calculate stats with post IDs for drill-down
        total_posts = len(filtered_posts)
        
        approved_posts = [p for p in filtered_posts if p.get("status") in ["approved", "published"]]
        pending_posts = [p for p in filtered_posts if p.get("status") in ["draft", "pending", "pending_approval"]]
        flagged_posts = [p for p in filtered_posts if p.get("status") == "flagged"]
        revision_posts = [p for p in filtered_posts if p.get("status") == "revisions_requested"]
        
        # Get content analyses for score calculations
        analyses = await db_conn.content_analyses.find(
            {"user_id": x_user_id},
            {"_id": 0}
        ).to_list(10000)
        
        # Calculate average scores
        compliance_scores = []
        cultural_scores = []
        accuracy_scores = []
        overall_scores = []
        
        for analysis in analyses:
            result = analysis.get("analysis_result", {})
            
            if result.get("compliance_score"):
                compliance_scores.append(result["compliance_score"])
            if result.get("cultural_score"):
                cultural_scores.append(result["cultural_score"])
            if result.get("accuracy_score"):
                accuracy_scores.append(result["accuracy_score"])
            if result.get("overall_score"):
                overall_scores.append(result["overall_score"])
        
        avg_compliance = round(sum(compliance_scores) / len(compliance_scores), 1) if compliance_scores else 0
        avg_cultural = round(sum(cultural_scores) / len(cultural_scores), 1) if cultural_scores else 0
        avg_accuracy = round(sum(accuracy_scores) / len(accuracy_scores), 1) if accuracy_scores else 0
        avg_overall = round(sum(overall_scores) / len(overall_scores), 1) if overall_scores else 0
        
        return {
            "date_range": {
                "filter": date_range,
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "stats": {
                "total_posts": {
                    "value": total_posts,
                    "post_ids": [p.get("id") for p in filtered_posts],
                    "drill_down_url": "/contentry/content-moderation?tab=posts"
                },
                "approved": {
                    "value": len(approved_posts),
                    "post_ids": [p.get("id") for p in approved_posts],
                    "drill_down_url": "/contentry/content-moderation?tab=posts&status=published"
                },
                "pending": {
                    "value": len(pending_posts),
                    "post_ids": [p.get("id") for p in pending_posts],
                    "drill_down_url": "/contentry/content-moderation?tab=posts&status=pending_approval"
                },
                "flagged": {
                    "value": len(flagged_posts),
                    "post_ids": [p.get("id") for p in flagged_posts],
                    "drill_down_url": "/contentry/content-moderation?tab=posts&status=flagged"
                },
                "revisions_requested": {
                    "value": len(revision_posts),
                    "post_ids": [p.get("id") for p in revision_posts],
                    "drill_down_url": "/contentry/content-moderation?tab=posts&status=revisions_requested"
                }
            },
            "scores": {
                "overall": {
                    "value": avg_overall,
                    "drill_down_url": "/contentry/analytics?view=overall"
                },
                "compliance": {
                    "value": avg_compliance,
                    "drill_down_url": "/contentry/analytics?view=compliance"
                },
                "cultural": {
                    "value": avg_cultural,
                    "drill_down_url": "/contentry/analytics?view=cultural"
                },
                "accuracy": {
                    "value": avg_accuracy,
                    "drill_down_url": "/contentry/analytics?view=accuracy"
                }
            },
            "total_analyses": len(analyses),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard overview error: {str(e)}")
        raise HTTPException(500, f"Failed to get dashboard overview: {str(e)}")


@router.get("/team-performance")
@require_permission("team.view_members")
async def get_team_performance(
    request: Request,
    x_user_id: Optional[str] = Header(None),
    date_range: str = Query("last_30_days", description="Date range filter"),
    custom_start: Optional[str] = Query(None),
    custom_end: Optional[str] = Query(None),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get team performance analytics for managers/admins.
    Returns content volume and compliance scores by team member.
    
    Security (ARCH-005): Requires team.view_members permission.
    """
    try:
        if not x_user_id:
            raise HTTPException(401, "User ID required")
        
        # Get user to check permissions
        user = await db_conn.users.find_one({"id": x_user_id}, {"_id": 0})
        if not user:
            raise HTTPException(404, "User not found")
        
        # Check if user has manager/admin role
        user_role = user.get("role", "").lower()
        enterprise_role = user.get("enterprise_role", "").lower()
        
        is_manager = any(role in ["admin", "manager", "enterprise_admin", "enterprise_manager"] 
                        for role in [user_role, enterprise_role])
        
        if not is_manager:
            raise HTTPException(403, "Manager or admin role required")
        
        start_date, end_date = parse_date_range(date_range, custom_start, custom_end)
        
        # Get enterprise ID if user belongs to one
        enterprise_id = user.get("enterprise_id")
        
        # Build query for team members
        if enterprise_id:
            team_query = {"enterprise_id": enterprise_id}
        else:
            # For non-enterprise, just show user's own data
            team_query = {"id": x_user_id}
        
        team_members = await db_conn.users.find(team_query, {"_id": 0, "id": 1, "full_name": 1, "email": 1}).to_list(1000)
        
        team_performance = []
        
        for member in team_members:
            member_id = member.get("id")
            member_name = member.get("full_name") or member.get("email", "Unknown").split("@")[0]
            
            # Get posts for this member
            posts = await db_conn.posts.find({"user_id": member_id}, {"_id": 0}).to_list(10000)
            
            # Filter by date
            filtered_posts = []
            for post in posts:
                created_at = post.get("created_at")
                if created_at:
                    try:
                        if isinstance(created_at, str):
                            post_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            post_date = created_at
                        if start_date <= post_date <= end_date:
                            filtered_posts.append(post)
                    except:
                        filtered_posts.append(post)
            
            # Get analyses for compliance scores
            analyses = await db_conn.content_analyses.find(
                {"user_id": member_id},
                {"_id": 0}
            ).to_list(10000)
            
            compliance_scores = []
            for analysis in analyses:
                result = analysis.get("analysis_result", {})
                score = result.get("overall_score") or result.get("compliance_score")
                if score:
                    compliance_scores.append(score)
            
            avg_score = round(sum(compliance_scores) / len(compliance_scores), 1) if compliance_scores else 0
            
            team_performance.append({
                "user_id": member_id,
                "name": member_name,
                "content_volume": len(filtered_posts),
                "avg_compliance_score": avg_score,
                "drill_down_url": f"/contentry/content-moderation?tab=posts&user_id={member_id}"
            })
        
        # Sort by content volume (descending)
        team_performance.sort(key=lambda x: x["content_volume"], reverse=True)
        
        return {
            "date_range": {
                "filter": date_range,
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "team_performance": team_performance,
            "charts": {
                "content_volume": {
                    "labels": [m["name"] for m in team_performance[:10]],
                    "data": [m["content_volume"] for m in team_performance[:10]]
                },
                "compliance_scores": {
                    "labels": [m["name"] for m in team_performance[:10]],
                    "data": [m["avg_compliance_score"] for m in team_performance[:10]]
                }
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Team performance error: {str(e)}")
        raise HTTPException(500, f"Failed to get team performance: {str(e)}")


@router.get("/content-strategy")
@require_permission("analytics.view_own")
async def get_content_strategy_insights(
    request: Request,
    x_user_id: Optional[str] = Header(None),
    date_range: str = Query("last_30_days", description="Date range filter"),
    custom_start: Optional[str] = Query(None),
    custom_end: Optional[str] = Query(None),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get content strategy insights - posts by platform and strategic profile.
    
    Security (ARCH-005): Requires analytics.view_own permission.
    """
    try:
        if not x_user_id:
            raise HTTPException(401, "User ID required")
        
        user = await db_conn.users.find_one({"id": x_user_id}, {"_id": 0})
        if not user:
            raise HTTPException(404, "User not found")
        
        start_date, end_date = parse_date_range(date_range, custom_start, custom_end)
        
        # Determine query scope (enterprise or personal)
        enterprise_id = user.get("enterprise_id")
        user_role = user.get("role", "").lower()
        enterprise_role = user.get("enterprise_role", "").lower()
        
        is_manager = any(role in ["admin", "manager", "enterprise_admin", "enterprise_manager"] 
                        for role in [user_role, enterprise_role])
        
        if is_manager and enterprise_id:
            # Get all enterprise users
            enterprise_users = await db_conn.users.find(
                {"enterprise_id": enterprise_id},
                {"_id": 0, "id": 1}
            ).to_list(1000)
            user_ids = [u["id"] for u in enterprise_users]
            posts_query = {"user_id": {"$in": user_ids}}
        else:
            posts_query = {"user_id": x_user_id}
        
        # Get posts
        posts = await db_conn.posts.find(posts_query, {"_id": 0}).to_list(10000)
        
        # Filter by date
        filtered_posts = []
        for post in posts:
            created_at = post.get("created_at")
            if created_at:
                try:
                    if isinstance(created_at, str):
                        post_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        post_date = created_at
                    if start_date <= post_date <= end_date:
                        filtered_posts.append(post)
                except:
                    filtered_posts.append(post)
        
        # Count posts by platform
        platform_counts = {}
        for post in filtered_posts:
            platforms = post.get("platforms", [])
            if isinstance(platforms, list):
                for platform in platforms:
                    platform_lower = platform.lower() if platform else "unspecified"
                    platform_counts[platform_lower] = platform_counts.get(platform_lower, 0) + 1
            elif platforms:
                platform_lower = platforms.lower()
                platform_counts[platform_lower] = platform_counts.get(platform_lower, 0) + 1
            else:
                platform_counts["unspecified"] = platform_counts.get("unspecified", 0) + 1
        
        # Count posts by strategic profile
        profile_counts = {}
        for post in filtered_posts:
            profile_id = post.get("profile_id") or post.get("strategic_profile_id")
            if profile_id:
                # Get profile name
                profile = await db_conn.strategic_profiles.find_one(
                    {"id": profile_id},
                    {"_id": 0, "name": 1}
                )
                profile_name = profile.get("name", "Unknown") if profile else "Unknown"
            else:
                profile_name = "No Profile"
            profile_counts[profile_name] = profile_counts.get(profile_name, 0) + 1
        
        return {
            "date_range": {
                "filter": date_range,
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "posts_by_platform": {
                "data": [
                    {
                        "platform": k.title(),
                        "count": v,
                        "drill_down_url": f"/contentry/content-moderation?tab=posts&platform={k}"
                    }
                    for k, v in sorted(platform_counts.items(), key=lambda x: x[1], reverse=True)
                ],
                "chart": {
                    "labels": [k.title() for k in platform_counts.keys()],
                    "data": list(platform_counts.values())
                }
            },
            "posts_by_profile": {
                "data": [
                    {
                        "profile": k,
                        "count": v,
                        "drill_down_url": f"/contentry/content-moderation?tab=posts&profile={k}"
                    }
                    for k, v in sorted(profile_counts.items(), key=lambda x: x[1], reverse=True)
                ],
                "chart": {
                    "labels": list(profile_counts.keys()),
                    "data": list(profile_counts.values())
                }
            },
            "total_posts": len(filtered_posts),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content strategy error: {str(e)}")
        raise HTTPException(500, f"Failed to get content strategy insights: {str(e)}")


@router.get("/approval-kpis")
@require_permission("analytics.view_own")
async def get_approval_workflow_kpis(
    request: Request,
    x_user_id: Optional[str] = Header(None),
    date_range: str = Query("last_30_days", description="Date range filter"),
    custom_start: Optional[str] = Query(None),
    custom_end: Optional[str] = Query(None),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get approval workflow KPIs - average time to approval and rejection rate.
    
    Security (ARCH-005): Requires analytics.view_own permission.
    """
    try:
        if not x_user_id:
            raise HTTPException(401, "User ID required")
        
        user = await db_conn.users.find_one({"id": x_user_id}, {"_id": 0})
        if not user:
            raise HTTPException(404, "User not found")
        
        start_date, end_date = parse_date_range(date_range, custom_start, custom_end)
        
        # Get approval history
        approval_history = await db_conn.approval_history.find({}, {"_id": 0}).to_list(10000)
        
        # Filter by date
        filtered_approvals = []
        for approval in approval_history:
            action_date = approval.get("action_date") or approval.get("created_at")
            if action_date:
                try:
                    if isinstance(action_date, str):
                        approval_date = datetime.fromisoformat(action_date.replace('Z', '+00:00'))
                    else:
                        approval_date = action_date
                    if start_date <= approval_date <= end_date:
                        filtered_approvals.append(approval)
                except:
                    filtered_approvals.append(approval)
        
        # Calculate KPIs
        approval_times = []
        approved_count = 0
        rejected_count = 0
        total_reviewed = 0
        
        for approval in filtered_approvals:
            action = approval.get("action", "").lower()
            
            if action in ["approved", "approve"]:
                approved_count += 1
                total_reviewed += 1
                
                # Calculate time to approval
                submitted_at = approval.get("submitted_at")
                approved_at = approval.get("action_date") or approval.get("approved_at")
                
                if submitted_at and approved_at:
                    try:
                        if isinstance(submitted_at, str):
                            submitted = datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
                        else:
                            submitted = submitted_at
                        
                        if isinstance(approved_at, str):
                            approved = datetime.fromisoformat(approved_at.replace('Z', '+00:00'))
                        else:
                            approved = approved_at
                        
                        time_diff = (approved - submitted).total_seconds() / 3600  # Hours
                        if time_diff >= 0:
                            approval_times.append(time_diff)
                    except:
                        pass
            
            elif action in ["rejected", "reject", "request_changes", "revisions_requested"]:
                rejected_count += 1
                total_reviewed += 1
        
        avg_approval_time = round(sum(approval_times) / len(approval_times), 1) if approval_times else 0
        rejection_rate = round((rejected_count / total_reviewed * 100), 1) if total_reviewed > 0 else 0
        
        # Format time nicely
        if avg_approval_time < 1:
            avg_approval_time_formatted = f"{int(avg_approval_time * 60)} minutes"
        elif avg_approval_time < 24:
            avg_approval_time_formatted = f"{avg_approval_time:.1f} hours"
        else:
            avg_approval_time_formatted = f"{avg_approval_time / 24:.1f} days"
        
        return {
            "date_range": {
                "filter": date_range,
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "kpis": {
                "avg_time_to_approval": {
                    "value": avg_approval_time,
                    "formatted": avg_approval_time_formatted,
                    "unit": "hours",
                    "drill_down_url": "/contentry/content-moderation?tab=posts&status=approved"
                },
                "rejection_rate": {
                    "value": rejection_rate,
                    "formatted": f"{rejection_rate}%",
                    "drill_down_url": "/contentry/content-moderation?tab=posts&status=revisions_requested"
                },
                "total_approved": {
                    "value": approved_count,
                    "drill_down_url": "/contentry/content-moderation?tab=posts&status=approved"
                },
                "total_rejected": {
                    "value": rejected_count,
                    "drill_down_url": "/contentry/content-moderation?tab=posts&status=revisions_requested"
                },
                "total_reviewed": {
                    "value": total_reviewed
                }
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approval KPIs error: {str(e)}")
        raise HTTPException(500, f"Failed to get approval KPIs: {str(e)}")


@router.get("/my-action-items")
@require_permission("content.view_own")
async def get_my_action_items(
    request: Request,
    x_user_id: Optional[str] = Header(None),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get action items for creator role - posts with revisions requested.
    
    Security (ARCH-005): Requires content.view_own permission.
    """
    try:
        if not x_user_id:
            raise HTTPException(401, "User ID required")
        
        user = await db_conn.users.find_one({"id": x_user_id}, {"_id": 0})
        if not user:
            raise HTTPException(404, "User not found")
        
        # Get posts with revisions requested status
        action_items = await db_conn.posts.find(
            {
                "user_id": x_user_id,
                "status": {"$in": ["revisions_requested", "changes_requested", "rejected"]}
            },
            {"_id": 0}
        ).sort("updated_at", -1).to_list(100)
        
        formatted_items = []
        for item in action_items:
            formatted_items.append({
                "id": item.get("id"),
                "title": item.get("title") or item.get("content", "")[:50] + "...",
                "content_preview": item.get("content", "")[:100] + "..." if len(item.get("content", "")) > 100 else item.get("content", ""),
                "status": item.get("status"),
                "feedback": item.get("rejection_reason") or item.get("feedback") or item.get("revision_notes"),
                "requested_by": item.get("reviewer_name") or item.get("approved_by"),
                "requested_at": item.get("updated_at") or item.get("created_at"),
                "drill_down_url": f"/contentry/content-moderation?tab=posts&post_id={item.get('id')}"
            })
        
        return {
            "action_items": formatted_items,
            "total_count": len(formatted_items),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"My action items error: {str(e)}")
        raise HTTPException(500, f"Failed to get action items: {str(e)}")


@router.get("/my-top-posts")
@require_permission("content.view_own")
async def get_my_top_posts(
    request: Request,
    x_user_id: Optional[str] = Header(None),
    limit: int = Query(3, description="Number of top posts to return"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get user's top performing posts by compliance/engagement score.
    
    Security (ARCH-005): Requires content.view_own permission.
    """
    try:
        if not x_user_id:
            raise HTTPException(401, "User ID required")
        
        user = await db_conn.users.find_one({"id": x_user_id}, {"_id": 0})
        if not user:
            raise HTTPException(404, "User not found")
        
        # Get user's posts with their analysis scores
        posts = await db_conn.posts.find(
            {"user_id": x_user_id},
            {"_id": 0}
        ).to_list(1000)
        
        posts_with_scores = []
        for post in posts:
            post_id = post.get("id")
            
            # Get the analysis for this post
            analysis = await db_conn.content_analyses.find_one(
                {"post_id": post_id},
                {"_id": 0}
            )
            
            score = 0
            if analysis:
                result = analysis.get("analysis_result", {})
                score = result.get("overall_score") or result.get("compliance_score") or 0
            
            posts_with_scores.append({
                "id": post_id,
                "title": post.get("title") or post.get("content", "")[:50] + "...",
                "content_preview": post.get("content", "")[:100],
                "score": score,
                "status": post.get("status"),
                "platforms": post.get("platforms", []),
                "created_at": post.get("created_at"),
                "drill_down_url": f"/contentry/content-moderation?tab=posts&post_id={post_id}"
            })
        
        # Sort by score and get top N
        posts_with_scores.sort(key=lambda x: x["score"], reverse=True)
        top_posts = posts_with_scores[:limit]
        
        return {
            "top_posts": top_posts,
            "total_posts": len(posts_with_scores),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"My top posts error: {str(e)}")
        raise HTTPException(500, f"Failed to get top posts: {str(e)}")


@router.get("/export/{widget_type}")
@require_permission("analytics.view_own")
async def export_dashboard_data(
    request: Request,
    widget_type: str,
    x_user_id: Optional[str] = Header(None),
    date_range: str = Query("last_30_days"),
    custom_start: Optional[str] = Query(None),
    custom_end: Optional[str] = Query(None),
    format: str = Query("csv", description="Export format: csv or json"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Export dashboard widget data as CSV or JSON.
    widget_type options: overview, team-performance, content-strategy, approval-kpis, action-items, top-posts
    """
    try:
        if not x_user_id:
            raise HTTPException(401, "User ID required")
        
        # Get data based on widget type
        if widget_type == "overview":
            data = await get_dashboard_overview(x_user_id, date_range, custom_start, custom_end)
        elif widget_type == "team-performance":
            data = await get_team_performance(x_user_id, date_range, custom_start, custom_end)
        elif widget_type == "content-strategy":
            data = await get_content_strategy_insights(x_user_id, date_range, custom_start, custom_end)
        elif widget_type == "approval-kpis":
            data = await get_approval_workflow_kpis(x_user_id, date_range, custom_start, custom_end)
        elif widget_type == "action-items":
            data = await get_my_action_items(x_user_id)
        elif widget_type == "top-posts":
            data = await get_my_top_posts(x_user_id, limit=10)
        else:
            raise HTTPException(400, f"Unknown widget type: {widget_type}")
        
        if format == "json":
            return data
        
        # Convert to CSV format
        import csv
        import io
        
        output = io.StringIO()
        
        if widget_type == "team-performance":
            writer = csv.writer(output)
            writer.writerow(["Name", "Content Volume", "Avg Compliance Score"])
            for member in data.get("team_performance", []):
                writer.writerow([
                    member.get("name"),
                    member.get("content_volume"),
                    member.get("avg_compliance_score")
                ])
        
        elif widget_type == "content-strategy":
            writer = csv.writer(output)
            writer.writerow(["Category", "Platform/Profile", "Count"])
            for item in data.get("posts_by_platform", {}).get("data", []):
                writer.writerow(["Platform", item.get("platform"), item.get("count")])
            for item in data.get("posts_by_profile", {}).get("data", []):
                writer.writerow(["Profile", item.get("profile"), item.get("count")])
        
        elif widget_type == "approval-kpis":
            writer = csv.writer(output)
            writer.writerow(["KPI", "Value"])
            kpis = data.get("kpis", {})
            writer.writerow(["Avg Time to Approval", kpis.get("avg_time_to_approval", {}).get("formatted")])
            writer.writerow(["Rejection Rate", kpis.get("rejection_rate", {}).get("formatted")])
            writer.writerow(["Total Approved", kpis.get("total_approved", {}).get("value")])
            writer.writerow(["Total Rejected", kpis.get("total_rejected", {}).get("value")])
        
        elif widget_type == "action-items":
            writer = csv.writer(output)
            writer.writerow(["Title", "Status", "Feedback", "Requested By", "Requested At"])
            for item in data.get("action_items", []):
                writer.writerow([
                    item.get("title"),
                    item.get("status"),
                    item.get("feedback"),
                    item.get("requested_by"),
                    item.get("requested_at")
                ])
        
        elif widget_type == "top-posts":
            writer = csv.writer(output)
            writer.writerow(["Title", "Score", "Status", "Platforms", "Created At"])
            for post in data.get("top_posts", []):
                writer.writerow([
                    post.get("title"),
                    post.get("score"),
                    post.get("status"),
                    ", ".join(post.get("platforms", [])),
                    post.get("created_at")
                ])
        
        else:
            writer = csv.writer(output)
            writer.writerow(["Stat", "Value"])
            stats = data.get("stats", {})
            for key, value in stats.items():
                if isinstance(value, dict):
                    writer.writerow([key, value.get("value")])
                else:
                    writer.writerow([key, value])
        
        csv_content = output.getvalue()
        
        return {
            "data": csv_content,
            "filename": f"dashboard_{widget_type}_{date_range}.csv",
            "content_type": "text/csv"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        raise HTTPException(500, f"Failed to export data: {str(e)}")
