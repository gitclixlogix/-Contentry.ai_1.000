"""
Team Analytics Routes
Provides analytics for managers to view their team's performance
Includes proper permission checking and data filtering

Security Update (ARCH-005 Phase 5.1b):
- Added @require_permission decorators for RBAC enforcement
"""

from fastapi import APIRouter, HTTPException, Header, Depends, Request
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import logging
import rbac
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db

# ARCH-005: Authorization decorator
from services.authorization_decorator import require_permission

router = APIRouter(prefix="/team", tags=["team"])
logger = logging.getLogger(__name__)

# Database will be set by server.py
db = None

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    """Set database instance"""
    global db
    db = database
    rbac.set_db(database)


@router.get("/analytics")
@require_permission("team.view_members")
async def get_team_analytics(request: Request, user_id: str = Header(...), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get analytics for manager's team.
    Requires: manager or admin role.
    Returns: aggregated analytics for all subordinates.
    
    Security (ARCH-005): Requires team.view_members permission.
    """
    try:
        # Check permission
        await rbac.require_permission(user_id, 'view_team_analytics')
        
        # Get team member IDs
        team_ids = await rbac.get_team_member_ids(user_id)
        
        if not team_ids:
            return {
                "team_size": 0,
                "message": "No team members found"
            }
        
        # Get posts from team members with projection for only needed fields
        posts = await db_conn.posts.find(
            {"user_id": {"$in": team_ids}},
            {
                "_id": 0,
                "cultural_sensitivity_score": 1,
                "compliance_score": 1,
                "overall_score": 1,
                "flagged_status": 1,
                "violation_severity": 1,
                "user_id": 1,
                "created_at": 1
            }
        ).limit(1000).to_list(1000)
        
        # Calculate team metrics
        total_posts = len(posts)
        
        # Cultural sensitivity scores
        cultural_scores = [
            p.get('cultural_sensitivity_score', 0) 
            for p in posts 
            if p.get('cultural_sensitivity_score')
        ]
        avg_cultural_score = sum(cultural_scores) / len(cultural_scores) if cultural_scores else 0
        
        # Compliance scores
        compliance_scores = [
            p.get('compliance_score', 0) 
            for p in posts 
            if p.get('compliance_score')
        ]
        avg_compliance_score = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0
        
        # Overall scores
        overall_scores = [
            p.get('overall_score', 0) 
            for p in posts 
            if p.get('overall_score')
        ]
        avg_overall_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        
        # Flagged content
        flagged_posts = [p for p in posts if p.get('flagged_status') != 'good_coverage']
        flagged_by_type = {}
        for post in flagged_posts:
            flag_type = post.get('flagged_status', 'unknown')
            flagged_by_type[flag_type] = flagged_by_type.get(flag_type, 0) + 1
        
        # Violation severity distribution
        severity_dist = {
            "critical": 0,
            "severe": 0,
            "high": 0,
            "moderate": 0,
            "none": 0
        }
        for post in posts:
            severity = post.get('violation_severity', 'none')
            if severity in severity_dist:
                severity_dist[severity] += 1
        
        # Posts by team member
        posts_by_member = {}
        for post in posts:
            uid = post['user_id']
            if uid not in posts_by_member:
                posts_by_member[uid] = {
                    "count": 0,
                    "avg_score": 0,
                    "flagged_count": 0
                }
            posts_by_member[uid]["count"] += 1
            if post.get('overall_score'):
                current_avg = posts_by_member[uid]["avg_score"]
                current_count = posts_by_member[uid]["count"]
                posts_by_member[uid]["avg_score"] = (
                    (current_avg * (current_count - 1) + post['overall_score']) / current_count
                )
            if post.get('flagged_status') != 'good_coverage':
                posts_by_member[uid]["flagged_count"] += 1
        
        # Get user details for team members
        team_members = await db_conn.users.find(
            {"id": {"$in": team_ids}},
            {"_id": 0, "id": 1, "full_name": 1, "email": 1, "job_title": 1, "department": 1}
        ).to_list(1000)
        
        # Combine user info with stats
        team_performance = []
        for member in team_members:
            member_stats = posts_by_member.get(member['id'], {
                "count": 0,
                "avg_score": 0,
                "flagged_count": 0
            })
            team_performance.append({
                "user_id": member['id'],
                "name": member.get('full_name', 'Unknown'),
                "email": member['email'],
                "job_title": member.get('job_title'),
                "department": member.get('department'),
                "post_count": member_stats['count'],
                "avg_overall_score": round(member_stats['avg_score'], 1),
                "flagged_count": member_stats['flagged_count'],
                "compliance_rate": round(
                    ((member_stats['count'] - member_stats['flagged_count']) / member_stats['count'] * 100)
                    if member_stats['count'] > 0 else 100, 
                    1
                )
            })
        
        # Sort by post count desc
        team_performance.sort(key=lambda x: x['post_count'], reverse=True)
        
        # Time-based trends (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_posts = [p for p in posts if p.get('created_at', datetime.min.replace(tzinfo=timezone.utc)) > thirty_days_ago]
        
        return {
            "team_size": len(team_ids),
            "manager_id": user_id,
            "total_posts": total_posts,
            "recent_posts_30d": len(recent_posts),
            
            "average_scores": {
                "cultural_sensitivity": round(avg_cultural_score, 1),
                "compliance": round(avg_compliance_score, 1),
                "overall": round(avg_overall_score, 1)
            },
            
            "flagged_content": {
                "total": len(flagged_posts),
                "by_type": flagged_by_type,
                "percentage": round((len(flagged_posts) / total_posts * 100) if total_posts > 0 else 0, 1)
            },
            
            "severity_distribution": severity_dist,
            
            "team_performance": team_performance[:20],  # Top 20 team members
            
            "compliance_rate": round(
                ((total_posts - len(flagged_posts)) / total_posts * 100) if total_posts > 0 else 100,
                1
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team analytics: {str(e)}")
        raise HTTPException(500, "Failed to get team analytics")


@router.get("/members")
@require_permission("team.view_members")
async def get_team_members(request: Request, user_id: str = Header(...), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get list of team members (subordinates).
    Requires: manager or admin role.
    
    Security (ARCH-005): Requires team.view_members permission.
    """
    try:
        # Check permission
        await rbac.require_permission(user_id, 'view_subordinates')
        
        # Get team member IDs
        team_ids = await rbac.get_subordinate_ids(user_id, include_self=False)
        
        if not team_ids:
            return {"team_members": [], "team_size": 0}
        
        # Get user details
        team_members = await db_conn.users.find(
            {"id": {"$in": team_ids}},
            {
                "_id": 0,
                "id": 1,
                "full_name": 1,
                "email": 1,
                "job_title": 1,
                "department": 1,
                "manager_id": 1,
                "created_at": 1,
                "last_login": 1
            }
        ).to_list(1000)
        
        # Build hierarchy info
        for member in team_members:
            # Check if this user is also a manager (has subordinates)
            subordinate_count = await db_conn.users.count_documents({"manager_id": member['id']})
            member['is_manager'] = subordinate_count > 0
            member['direct_reports_count'] = subordinate_count
        
        return {
            "team_members": team_members,
            "team_size": len(team_members)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team members: {str(e)}")
        raise HTTPException(500, "Failed to get team members")


@router.get("/member/{member_id}/posts")
@require_permission("team.view_members")
async def get_member_posts(request: Request, member_id: str, user_id: str = Header(...), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get posts for a specific team member.
    Requires: manager or admin role + member must be in requester's team.
    
    Security (ARCH-005): Requires team.view_members permission.
    """
    try:
        # Check if requester can access this member's data
        can_access = await rbac.can_access_user_data(user_id, member_id)
        if not can_access:
            raise HTTPException(403, "Cannot access this user's data")
        
        # Get member info
        member = await db_conn.users.find_one(
            {"id": member_id},
            {"_id": 0, "id": 1, "full_name": 1, "email": 1, "job_title": 1}
        )
        
        if not member:
            raise HTTPException(404, "Team member not found")
        
        # Get posts
        posts = await db_conn.posts.find(
            {"user_id": member_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        return {
            "member": member,
            "posts": posts,
            "total_posts": len(posts)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting member posts: {str(e)}")
        raise HTTPException(500, "Failed to get member posts")


@router.get("/hierarchy")
@require_permission("team.view_members")
async def get_team_hierarchy(request: Request, user_id: str = Header(...), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get organizational hierarchy starting from the user.
    Shows reporting structure with subordinates.
    
    Security (ARCH-005): Requires team.view_members permission.
    """
    try:
        # Check permission
        await rbac.require_permission(user_id, 'view_subordinates')
        
        async def build_hierarchy(manager_id: str, depth: int = 0, max_depth: int = 5, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
            """Recursively build hierarchy tree"""
            if depth > max_depth:
                return None
            
            # Get manager info
            manager = await db_conn.users.find_one(
                {"id": manager_id},
                {"_id": 0, "id": 1, "full_name": 1, "email": 1, "job_title": 1, "department": 1}
            )
            
            if not manager:
                return None
            
            # Get direct reports
            reports = await db_conn.users.find(
                {"manager_id": manager_id},
                {"_id": 0, "id": 1, "full_name": 1, "email": 1, "job_title": 1}
            ).to_list(100)
            
            # Build hierarchy for each report
            subordinates = []
            for report in reports:
                sub_hierarchy = await build_hierarchy(report['id'], depth + 1, max_depth)
                if sub_hierarchy:
                    subordinates.append(sub_hierarchy)
            
            return {
                "user_id": manager['id'],
                "name": manager.get('full_name', 'Unknown'),
                "email": manager['email'],
                "job_title": manager.get('job_title'),
                "department": manager.get('department'),
                "direct_reports_count": len(reports),
                "subordinates": subordinates,
                "level": depth
            }
        
        hierarchy = await build_hierarchy(user_id)
        
        return {
            "hierarchy": hierarchy,
            "total_levels": max((s.get('level', 0) for s in hierarchy.get('subordinates', [])), default=0) + 1 if hierarchy else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team hierarchy: {str(e)}")
        raise HTTPException(500, "Failed to get team hierarchy")
