"""
User Routes
Handles user-specific endpoints including dashboard analytics

RBAC Protected: Phase 5.1b Week 6
All endpoints require appropriate analytics.* permissions
"""

from fastapi import APIRouter, HTTPException, Header, Depends, Request
from typing import Optional
from datetime import datetime, timezone, timedelta
import logging
from collections import Counter
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db
# Import RBAC decorator
from services.authorization_decorator import require_permission

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)

# Will be set by server.py
db = None

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    """Set database instance"""
    global db
    db = database


@router.get("/{user_id}")
@require_permission("settings.view")
async def get_user(
    request: Request,
    user_id: str,
    x_user_id: Optional[str] = Header(None),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get user by ID"""
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
        if not user:
            raise HTTPException(404, "User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(500, str(e))


@router.get("/{user_id}/dashboard-analytics")
@require_permission("analytics.view_own")
async def get_user_dashboard_analytics(
    request: Request,
    user_id: str,
    x_user_id: Optional[str] = Header(None),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get comprehensive dashboard analytics for a specific user.
    Returns aggregated data for posts, analyses, and trends.
    """
    try:
        # Verify user exists
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(404, "User not found")
        
        # Get user's posts
        posts = await db_conn.posts.find(
            {"user_id": user_id},
            {"_id": 0}
        ).to_list(1000)
        
        # Calculate post stats
        total_posts = len(posts)
        approved = len([p for p in posts if p.get("status") in ["approved", "published"]])
        flagged = len([p for p in posts if p.get("status") == "flagged"])
        pending = len([p for p in posts if p.get("status") in ["draft", "pending"]])
        
        # Get user's content analyses
        analyses = await db_conn.content_analyses.find(
            {"user_id": user_id},
            {"_id": 0}
        ).to_list(1000)
        
        # Aggregate cultural violations
        cultural_violations = {}
        compliance_violations = {}
        
        for analysis in analyses:
            result = analysis.get("analysis_result", {})
            
            # Cultural data
            cultural = result.get("cultural_analysis", {})
            dimensions = cultural.get("dimensions", [])
            for dim in dimensions:
                if dim.get("score", 100) < 70:
                    dimension_name = dim.get("dimension", "Unknown")
                    cultural_violations[dimension_name] = cultural_violations.get(dimension_name, 0) + 1
            
            # Compliance data
            compliance = result.get("compliance_analysis", {})
            violation_type = compliance.get("violation_type")
            if violation_type and violation_type != "none":
                compliance_violations[violation_type] = compliance_violations.get(violation_type, 0) + 1
        
        # Calculate posting trends (last 6 months)
        now = datetime.now(timezone.utc)
        months = []
        month_posts = []
        
        for i in range(5, -1, -1):
            month_start = (now - timedelta(days=30*i)).replace(day=1)
            month_name = month_start.strftime("%b")
            months.append(month_name)
            
            # Count posts in this month
            count = 0
            for post in posts:
                created_at = post.get("created_at")
                if created_at:
                    if isinstance(created_at, str):
                        try:
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        except (ValueError, TypeError) as e:
                            logging.debug(f"Skipping post with invalid date: {e}")
                            continue
                    if created_at.year == month_start.year and created_at.month == month_start.month:
                        count += 1
            month_posts.append(count)
        
        # Top 5 cultural violations
        top_cultural = sorted(
            cultural_violations.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "user_id": user_id,
            "stats": {
                "total_posts": total_posts,
                "approved": approved,
                "pending": pending,
                "flagged": flagged
            },
            "posting_trend": {
                "months": months,
                "post_counts": month_posts
            },
            "cultural_violations": {
                "total": sum(cultural_violations.values()),
                "by_dimension": dict(top_cultural)
            },
            "compliance_violations": {
                "total": sum(compliance_violations.values()),
                "by_type": compliance_violations
            },
            "total_analyses": len(analyses),
            "generated_at": now.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard analytics error: {str(e)}")
        raise HTTPException(500, f"Failed to get dashboard analytics: {str(e)}")



@router.get("/{user_id}/score-analytics")
@require_permission("analytics.view_own")
async def get_user_score_analytics(
    request: Request,
    user_id: str,
    x_user_id: Optional[str] = Header(None),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get score analytics for user dashboard.
    Returns: Average scores over time, pillar breakdown, top/bottom posts.
    """
    try:
        # Verify user exists
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(404, "User not found")
        
        # Get user's content analyses
        analyses = await db_conn.content_analyses.find(
            {"user_id": user_id},
            {"_id": 0}
        ).to_list(1000)
        
        # Calculate daily average scores for line chart
        daily_scores = {}
        pillar_scores = {"compliance": [], "cultural": [], "accuracy": []}
        post_scores = []
        
        for analysis in analyses:
            result = analysis.get("analysis_result", {})
            created_at = analysis.get("created_at")
            
            # Parse date
            if created_at:
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except (ValueError, TypeError):
                        continue
                
                date_key = created_at.strftime("%Y-%m-%d")
                
                # Get overall score
                overall_score = result.get("overall_score", 0)
                if overall_score > 0:
                    if date_key not in daily_scores:
                        daily_scores[date_key] = []
                    daily_scores[date_key].append(overall_score)
                    
                    # Store for top/bottom calculation
                    post_scores.append({
                        "id": analysis.get("id"),
                        "content": analysis.get("content", "")[:100] + "..." if len(analysis.get("content", "")) > 100 else analysis.get("content", ""),
                        "overall_score": overall_score,
                        "created_at": created_at.isoformat()
                    })
                
                # Get pillar scores
                compliance = result.get("compliance_analysis", {})
                cultural = result.get("cultural_analysis", {})
                
                compliance_score = compliance.get("score", 0)
                cultural_score = cultural.get("overall_score", 0)
                accuracy_score = result.get("accuracy_score", result.get("overall_score", 0))
                
                if compliance_score > 0:
                    pillar_scores["compliance"].append(compliance_score)
                if cultural_score > 0:
                    pillar_scores["cultural"].append(cultural_score)
                if accuracy_score > 0:
                    pillar_scores["accuracy"].append(accuracy_score)
        
        # Build score trend for last 30 days
        score_trend = {"dates": [], "scores": []}
        for i in range(29, -1, -1):
            date = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
            score_trend["dates"].append(date[-5:])  # Just MM-DD
            if date in daily_scores:
                avg = sum(daily_scores[date]) / len(daily_scores[date])
                score_trend["scores"].append(round(avg, 1))
            else:
                score_trend["scores"].append(None)  # No data for this day
        
        # Calculate pillar averages
        pillar_breakdown = {
            "compliance": round(sum(pillar_scores["compliance"]) / len(pillar_scores["compliance"]), 1) if pillar_scores["compliance"] else 0,
            "cultural": round(sum(pillar_scores["cultural"]) / len(pillar_scores["cultural"]), 1) if pillar_scores["cultural"] else 0,
            "accuracy": round(sum(pillar_scores["accuracy"]) / len(pillar_scores["accuracy"]), 1) if pillar_scores["accuracy"] else 0
        }
        
        # Sort posts by score
        sorted_posts = sorted(post_scores, key=lambda x: x["overall_score"], reverse=True)
        top_posts = sorted_posts[:5]
        bottom_posts = sorted_posts[-5:][::-1] if len(sorted_posts) >= 5 else sorted_posts[::-1]
        
        # Calculate overall average
        all_scores = [p["overall_score"] for p in post_scores if p["overall_score"] > 0]
        overall_avg = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0
        
        return {
            "user_id": user_id,
            "overall_average": overall_avg,
            "total_analyses": len(analyses),
            "score_trend": score_trend,
            "pillar_breakdown": pillar_breakdown,
            "top_posts": top_posts,
            "bottom_posts": bottom_posts,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Score analytics error: {str(e)}")
        raise HTTPException(500, f"Failed to get score analytics: {str(e)}")
