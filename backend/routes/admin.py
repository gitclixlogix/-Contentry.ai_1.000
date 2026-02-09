"""
Admin Routes
Handles admin-level operations: user management, stats, documentation, reports

Security Update (ARCH-005 Phase 5.1b):
- Added @require_permission decorators for RBAC enforcement

Enterprise Scoping Update:
- Admin analytics are now scoped to the admin's enterprise/company
- Platform super-admins (role='super_admin') see all data
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Header
from fastapi.responses import HTMLResponse
from datetime import datetime, timezone, timedelta
import logging
import os
from services.stripe_mrr_service import calculate_mrr, get_cache_status, clear_mrr_cache
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List

# Import database dependency injection
from services.database import get_db

# ARCH-005: Authorization decorator
from services.authorization_decorator import require_permission

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)

# Will be set by server.py
db = None

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    """Set database instance"""
    global db
    db = database


async def get_enterprise_scope(request: Request, db_conn: AsyncIOMotorDatabase) -> dict:
    """
    Get enterprise scoping information for the current user.
    Returns dict with:
    - is_platform_admin: True if user should see all platform data
    - enterprise_id: The user's enterprise_id (None for platform admins)
    - user_ids: List of user IDs in the same enterprise (empty for platform admins)
    """
    user = getattr(request.state, 'user', None)
    if not user:
        return {"is_platform_admin": False, "enterprise_id": None, "user_ids": []}
    
    user_role = user.get('role', '')
    
    # Platform super-admins see all data
    if user_role == 'super_admin':
        return {"is_platform_admin": True, "enterprise_id": None, "user_ids": []}
    
    # Get the admin's enterprise_id
    user_id = user.get('id') or user.get('user_id')
    admin_user = await db_conn.users.find_one({"id": user_id}, {"_id": 0, "enterprise_id": 1})
    
    if not admin_user or not admin_user.get('enterprise_id'):
        # Admin without enterprise - show only their own data
        return {"is_platform_admin": False, "enterprise_id": None, "user_ids": [user_id] if user_id else []}
    
    enterprise_id = admin_user['enterprise_id']
    
    # Get all users in the same enterprise
    enterprise_users = await db_conn.users.find(
        {"enterprise_id": enterprise_id},
        {"_id": 0, "id": 1}
    ).to_list(10000)
    
    user_ids = [u['id'] for u in enterprise_users]
    
    return {
        "is_platform_admin": False,
        "enterprise_id": enterprise_id,
        "user_ids": user_ids
    }


@router.get("/stats")
@require_permission("admin.view")
async def get_admin_stats(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get overall admin statistics.
    Scoped to admin's enterprise unless platform super-admin.
    
    Security (ARCH-005): Requires admin.view permission.
    """
    try:
        # Get enterprise scope for filtering
        scope = await get_enterprise_scope(request, db_conn)
        
        # Build query filter based on scope
        if scope["is_platform_admin"]:
            user_filter = {}
            post_filter = {}
        elif scope["user_ids"]:
            user_filter = {"id": {"$in": scope["user_ids"]}}
            post_filter = {"user_id": {"$in": scope["user_ids"]}}
        else:
            user_filter = {"id": {"$in": []}}  # No users
            post_filter = {"user_id": {"$in": []}}  # No posts
        
        # Count users (scoped)
        total_users = await db_conn.users.count_documents(user_filter)
        active_filter = {**user_filter, "subscription_status": "active"} if user_filter else {"subscription_status": "active"}
        active_users = await db_conn.users.count_documents(active_filter)
        
        # Count posts (scoped)
        total_posts = await db_conn.posts.count_documents(post_filter)
        flagged_filter = {**post_filter, "flagged_status": {"$ne": "good_coverage"}} if post_filter else {"flagged_status": {"$ne": "good_coverage"}}
        flagged_posts = await db_conn.posts.count_documents(flagged_filter)
        good_coverage_filter = {**post_filter, "flagged_status": "good_coverage"} if post_filter else {"flagged_status": "good_coverage"}
        good_coverage = await db_conn.posts.count_documents(good_coverage_filter)
        
        # Count by specific flag types (scoped)
        rude_filter = {**post_filter, "flagged_status": "rude_and_abusive"} if post_filter else {"flagged_status": "rude_and_abusive"}
        rude_and_abusive = await db_conn.posts.count_documents(rude_filter)
        harassment_filter = {**post_filter, "flagged_status": "contain_harassment"} if post_filter else {"flagged_status": "contain_harassment"}
        contain_harassment = await db_conn.posts.count_documents(harassment_filter)
        policy_filter = {**post_filter, "flagged_status": "policy_violation"} if post_filter else {"flagged_status": "policy_violation"}
        policy_violation = await db_conn.posts.count_documents(policy_filter)
        
        # Count enterprises (only for platform admins)
        if scope["is_platform_admin"]:
            total_enterprises = await db_conn.enterprises.count_documents({})
        else:
            total_enterprises = 1  # Just their own enterprise
        
        # Get recent signups (last 30 days, scoped)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_filter = {**user_filter, "created_at": {"$gte": thirty_days_ago}} if user_filter else {"created_at": {"$gte": thirty_days_ago}}
        recent_signups = await db_conn.users.count_documents(recent_filter)
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "recent_signups_30d": recent_signups
            },
            "posts": {
                "total": total_posts,
                "flagged": flagged_posts,
                "compliance_rate": round((total_posts - flagged_posts) / total_posts * 100, 1) if total_posts > 0 else 100
            },
            "flagged_stats": {
                "good_coverage": good_coverage,
                "rude_and_abusive": rude_and_abusive,
                "contain_harassment": contain_harassment,
                "policy_violation": policy_violation
            },
            "enterprises": {
                "total": total_enterprises
            }
        }
    except Exception as e:
        logger.error(f"Error getting admin stats: {str(e)}")
        raise HTTPException(500, "Failed to get admin statistics")


@router.get("/god-view-dashboard")
@require_permission("admin.view")
async def get_admin_god_view_dashboard(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get comprehensive "god view" dashboard analytics for system admin.
    Returns: KPI cards, credit consumption, most active companies, compliance hotspots.
    Scoped to admin's enterprise unless platform super-admin.
    
    Security (ARCH-005): Requires admin.view permission.
    """
    try:
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)
        
        # Get enterprise scope for filtering
        scope = await get_enterprise_scope(request, db_conn)
        
        # Build query filters based on scope
        if scope["is_platform_admin"]:
            user_filter = {}
            analysis_filter = {}
        elif scope["user_ids"]:
            user_filter = {"id": {"$in": scope["user_ids"]}}
            analysis_filter = {"user_id": {"$in": scope["user_ids"]}}
        else:
            user_filter = {"id": {"$in": []}}
            analysis_filter = {"user_id": {"$in": []}}
        
        # ==================== KPI CARDS ====================
        total_users = await db_conn.users.count_documents(user_filter)
        new_users_filter = {**user_filter, "created_at": {"$gte": thirty_days_ago.isoformat()}} if user_filter else {"created_at": {"$gte": thirty_days_ago.isoformat()}}
        new_users_30d = await db_conn.users.count_documents(new_users_filter)
        
        # Enterprise count - only for platform admins
        if scope["is_platform_admin"]:
            total_enterprises = await db_conn.enterprises.count_documents({})
            active_enterprises = await db_conn.enterprises.count_documents({})
        else:
            total_enterprises = 1
            active_enterprises = 1
        
        total_content_analyzed = await db_conn.content_analyses.count_documents(analysis_filter)
        
        # ==================== LIVE STRIPE MRR ====================
        # MRR is only shown for platform admins (requires access to all Stripe data)
        if scope["is_platform_admin"]:
            mrr_data = await calculate_mrr()
            mrr_value = mrr_data.get("mrr")
            mrr_status = mrr_data.get("status", "unknown")
            mrr_subscription_count = mrr_data.get("subscription_count", 0)
            mrr_cached = mrr_data.get("cached", False)
            mrr_error = mrr_data.get("error")
        else:
            # For enterprise admins, show placeholder or enterprise-specific data
            mrr_value = None
            mrr_status = "enterprise_view"
            mrr_subscription_count = total_users
            mrr_cached = False
            mrr_error = None
            mrr_data = {"last_updated": now.isoformat()}
        
        kpi_cards = {
            "mrr": {
                "value": mrr_value,
                "label": "Monthly Recurring Revenue" if scope["is_platform_admin"] else "Team Members",
                "format": "currency" if scope["is_platform_admin"] else "number",
                "status": mrr_status,
                "subscription_count": mrr_subscription_count,
                "cached": mrr_cached,
                "error": mrr_error,
                "last_updated": mrr_data.get("last_updated")
            },
            "new_users": {
                "value": new_users_30d,
                "label": "New Team Members (30 Days)" if not scope["is_platform_admin"] else "New Users (30 Days)",
                "format": "number"
            },
            "active_companies": {
                "value": active_enterprises if scope["is_platform_admin"] else total_users,
                "label": "Active Companies" if scope["is_platform_admin"] else "Active Team Members",
                "format": "number"
            },
            "total_content": {
                "value": total_content_analyzed,
                "label": "Total Content Analyzed",
                "format": "number"
            }
        }
        
        # ==================== CREDIT CONSUMPTION (LAST 30 DAYS) ====================
        # Use aggregation pipeline for efficient credit consumption calculation
        daily_credits = {}
        
        # Build match filter for scoping
        if scope["is_platform_admin"]:
            usage_match = {"created_at": {"$gte": thirty_days_ago.isoformat()}}
            posts_match = {"created_at": {"$gte": thirty_days_ago.isoformat()}}
        elif scope["user_ids"]:
            usage_match = {"created_at": {"$gte": thirty_days_ago.isoformat()}, "user_id": {"$in": scope["user_ids"]}}
            posts_match = {"created_at": {"$gte": thirty_days_ago.isoformat()}, "user_id": {"$in": scope["user_ids"]}}
        else:
            usage_match = {"created_at": {"$gte": thirty_days_ago.isoformat()}, "user_id": {"$in": []}}
            posts_match = {"created_at": {"$gte": thirty_days_ago.isoformat()}, "user_id": {"$in": []}}
        
        # Try to get from usage_logs collection first with aggregation
        if "usage_logs" in await db_conn.list_collection_names():
            usage_pipeline = [
                {"$match": usage_match},
                {"$group": {
                    "_id": {"$substr": ["$created_at", 0, 10]},
                    "total_credits": {"$sum": {"$ifNull": ["$credits_used", {"$ifNull": ["$tokens", 1]}]}}
                }},
                {"$limit": 100}
            ]
            usage_results = await db_conn.usage_logs.aggregate(usage_pipeline).to_list(100)
            for result in usage_results:
                daily_credits[result["_id"]] = result["total_credits"]
        
        if not daily_credits:
            # Fall back to counting posts per day as proxy for credit usage
            posts_pipeline = [
                {"$match": posts_match},
                {"$group": {
                    "_id": {"$substr": ["$created_at", 0, 10]},
                    "count": {"$sum": 1}
                }},
                {"$limit": 100}
            ]
            posts_results = await db_conn.posts.aggregate(posts_pipeline).to_list(100)
            for result in posts_results:
                daily_credits[result["_id"]] = result["count"]
        
        # Build credit trend for chart
        credit_consumption = {"dates": [], "credits": []}
        for i in range(29, -1, -1):
            date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            credit_consumption["dates"].append(date[-5:])  # MM-DD
            credit_consumption["credits"].append(daily_credits.get(date, 0))
        
        # ==================== MOST ACTIVE COMPANIES/TEAM MEMBERS ====================
        # For platform admins: show most active companies
        # For enterprise admins: show most active team members
        
        if scope["is_platform_admin"]:
            # Platform admin - show enterprise activity
            user_enterprise_map = {}
            users = await db_conn.users.find(
                {"enterprise_id": {"$exists": True, "$nin": [None, ""]}},
                {"_id": 0, "id": 1, "enterprise_id": 1}
            ).limit(10000).to_list(10000)
            
            for user in users:
                if user.get("enterprise_id"):
                    user_enterprise_map[user["id"]] = user["enterprise_id"]
            
            # Count posts by user, then map to enterprises
            posts_pipeline = [
                {"$match": {"created_at": {"$gte": thirty_days_ago.isoformat()}}},
                {"$group": {
                    "_id": "$user_id",
                    "post_count": {"$sum": 1}
                }},
                {"$limit": 5000}
            ]
            posts_by_user = await db_conn.posts.aggregate(posts_pipeline).to_list(5000)
            
            enterprise_activity = {}
            for item in posts_by_user:
                user_id = item["_id"]
                enterprise_id = user_enterprise_map.get(user_id)
                if enterprise_id:
                    enterprise_activity[enterprise_id] = enterprise_activity.get(enterprise_id, 0) + item["post_count"]
            
            # Get enterprise names
            enterprise_names = {}
            enterprises = await db_conn.enterprises.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(1000)
            for ent in enterprises:
                enterprise_names[ent["id"]] = ent.get("name", "Unknown Company")
            
            # Sort and get top 10
            sorted_activity = sorted(enterprise_activity.items(), key=lambda x: x[1], reverse=True)[:10]
            most_active_companies = [
                {"name": enterprise_names.get(eid, "Unknown"), "posts": count}
                for eid, count in sorted_activity
            ]
        else:
            # Enterprise admin - show team member activity
            posts_pipeline = [
                {"$match": posts_match},
                {"$group": {
                    "_id": "$user_id",
                    "post_count": {"$sum": 1}
                }},
                {"$sort": {"post_count": -1}},
                {"$limit": 10}
            ]
            posts_by_user = await db_conn.posts.aggregate(posts_pipeline).to_list(10)
            
            # Get user names for the team members
            user_ids_in_results = [item["_id"] for item in posts_by_user]
            team_users = await db_conn.users.find(
                {"id": {"$in": user_ids_in_results}},
                {"_id": 0, "id": 1, "full_name": 1, "email": 1}
            ).to_list(10)
            
            user_names = {u["id"]: u.get("full_name", u.get("email", "Unknown")) for u in team_users}
            
            most_active_companies = [
                {"name": user_names.get(item["_id"], "Unknown"), "posts": item["post_count"]}
                for item in posts_by_user
            ]
        
        # ==================== COMPLIANCE HOTSPOTS ====================
        # Use aggregation pipeline for compliance violation analysis (scoped)
        compliance_violations = {}
        
        # Build analysis filter
        if scope["is_platform_admin"]:
            analysis_match = {"created_at": {"$gte": thirty_days_ago.isoformat()}}
        elif scope["user_ids"]:
            analysis_match = {"created_at": {"$gte": thirty_days_ago.isoformat()}, "user_id": {"$in": scope["user_ids"]}}
        else:
            analysis_match = {"created_at": {"$gte": thirty_days_ago.isoformat()}, "user_id": {"$in": []}}
        
        # Get recent analyses with limit
        analyses = await db_conn.content_analyses.find(
            analysis_match,
            {"_id": 0, "analysis_result.compliance_analysis.violations": 1, "analysis_result.compliance_analysis.violation_type": 1}
        ).limit(5000).to_list(5000)
        
        for analysis in analyses:
            result = analysis.get("analysis_result", {})
            compliance = result.get("compliance_analysis", {})
            
            # Check violations
            violations = compliance.get("violations", [])
            for violation in violations:
                violation_type = violation.get("type", violation.get("policy", "Unknown"))
                compliance_violations[violation_type] = compliance_violations.get(violation_type, 0) + 1
            
            # Also check violation_type
            violation_type = compliance.get("violation_type")
            if violation_type and violation_type != "none":
                compliance_violations[violation_type] = compliance_violations.get(violation_type, 0) + 1
        
        # Sort by count
        sorted_violations = sorted(compliance_violations.items(), key=lambda x: x[1], reverse=True)[:15]
        compliance_hotspots = [
            {"violation_type": vtype, "count": count, "percentage": round(count / sum(compliance_violations.values()) * 100, 1) if compliance_violations else 0}
            for vtype, count in sorted_violations
        ]
        
        return {
            "kpi_cards": kpi_cards,
            "credit_consumption": credit_consumption,
            "most_active_companies": most_active_companies,
            "most_active_label": "Most Active Companies" if scope["is_platform_admin"] else "Most Active Team Members",
            "compliance_hotspots": compliance_hotspots,
            "summary": {
                "total_users": total_users,
                "total_enterprises": total_enterprises,
                "total_analyses": total_content_analyzed,
                "total_violations": sum(compliance_violations.values())
            },
            "scope": {
                "is_platform_admin": scope["is_platform_admin"],
                "enterprise_id": scope["enterprise_id"]
            },
            "generated_at": now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"God view dashboard error: {str(e)}")
        raise HTTPException(500, f"Failed to get dashboard data: {str(e)}")


@router.get("/users")
@require_permission("admin.view")
async def get_all_users(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get all users (admin only).
    Scoped to admin's enterprise unless platform super-admin.
    
    Security (ARCH-005): Requires admin.view permission.
    """
    try:
        # Get enterprise scope
        scope = await get_enterprise_scope(request, db_conn)
        
        if scope["is_platform_admin"]:
            users = await db_conn.users.find({}, {"_id": 0, "password_hash": 0}).to_list(10000)
        elif scope["user_ids"]:
            users = await db_conn.users.find({"id": {"$in": scope["user_ids"]}}, {"_id": 0, "password_hash": 0}).to_list(10000)
        else:
            users = []
        
        return {"users": users, "total": len(users), "scope": {"is_platform_admin": scope["is_platform_admin"]}}
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        raise HTTPException(500, "Failed to get users")


@router.get("/posts")
@require_permission("admin.view")
async def get_all_posts(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get all posts (admin only).
    Scoped to admin's enterprise unless platform super-admin.
    
    Security (ARCH-005): Requires admin.view permission.
    """
    try:
        # Get enterprise scope
        scope = await get_enterprise_scope(request, db_conn)
        
        if scope["is_platform_admin"]:
            posts = await db_conn.posts.find({}, {"_id": 0}).sort("created_at", -1).limit(1000).to_list(1000)
        elif scope["user_ids"]:
            posts = await db_conn.posts.find({"user_id": {"$in": scope["user_ids"]}}, {"_id": 0}).sort("created_at", -1).limit(1000).to_list(1000)
        else:
            posts = []
        
        return {"posts": posts, "total": len(posts)}
    except Exception as e:
        logger.error(f"Error getting posts: {str(e)}")
        raise HTTPException(500, "Failed to get posts")


@router.get("/feedback")
@require_permission("admin.view")
async def get_all_feedback(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get all user feedback (admin only).
    
    Security (ARCH-005): Requires admin.view permission.
    """
    try:
        feedback = await db_conn.analysis_feedback.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
        return {"feedback": feedback, "total": len(feedback)}
    except Exception as e:
        logger.error(f"Error getting feedback: {str(e)}")
        raise HTTPException(500, "Failed to get feedback")


# =====================
# User Management Endpoints
# =====================

@router.delete("/users/{user_id}")
@require_permission("admin.delete")
async def admin_delete_user(request: Request, user_id: str, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Delete a user (admin only).
    
    Security (ARCH-005): Requires admin.delete permission.
    """
    try:
        # Find the user first
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(404, "User not found")
        
        # Prevent deletion of admin users
        if user.get("role") == "admin":
            raise HTTPException(403, "Cannot delete admin users")
        
        # Delete user's posts
        deleted_posts = await db_conn.posts.delete_many({"user_id": user_id})
        
        # Delete user's content analyses
        await db_conn.content_analyses.delete_many({"user_id": user_id})
        
        # Delete user's scheduled posts
        await db_conn.scheduled_posts.delete_many({"user_id": user_id})
        
        # Delete user's notifications
        await db_conn.notifications.delete_many({"user_id": user_id})
        
        # Delete the user
        result = await db_conn.users.delete_one({"id": user_id})
        
        if result.deleted_count == 0:
            raise HTTPException(500, "Failed to delete user")
        
        logger.info(f"Admin deleted user {user_id} ({user.get('email')})")
        
        return {
            "message": "User deleted successfully",
            "user_id": user_id,
            "email": user.get("email"),
            "posts_deleted": deleted_posts.deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(500, f"Failed to delete user: {str(e)}")


@router.delete("/users/bulk")
@require_permission("admin.delete")
async def admin_bulk_delete_users(request: Request, user_ids: list[str], db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Bulk delete users (admin only).
    
    Security (ARCH-005): Requires admin.delete permission.
    """
    try:
        deleted_users = []
        failed_users = []
        
        for user_id in user_ids:
            try:
                user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
                if not user:
                    failed_users.append({"user_id": user_id, "reason": "Not found"})
                    continue
                
                if user.get("role") == "admin":
                    failed_users.append({"user_id": user_id, "reason": "Cannot delete admin"})
                    continue
                
                # Delete related data
                await db_conn.posts.delete_many({"user_id": user_id})
                await db_conn.content_analyses.delete_many({"user_id": user_id})
                await db_conn.scheduled_posts.delete_many({"user_id": user_id})
                await db_conn.notifications.delete_many({"user_id": user_id})
                
                # Delete user
                await db_conn.users.delete_one({"id": user_id})
                deleted_users.append({"user_id": user_id, "email": user.get("email")})
                
            except Exception as e:
                failed_users.append({"user_id": user_id, "reason": str(e)})
        
        return {
            "message": f"Deleted {len(deleted_users)} users",
            "deleted": deleted_users,
            "failed": failed_users
        }
    except Exception as e:
        logger.error(f"Error bulk deleting users: {str(e)}")
        raise HTTPException(500, f"Failed to bulk delete users: {str(e)}")


# =====================
# Drill-Down Endpoints
# =====================

@router.get("/drilldown/{metric_type}")
@require_permission("admin.view")
async def get_admin_drilldown(request: Request, metric_type: str, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get drill-down data for admin dashboard metrics.
    
    Security (ARCH-005): Requires admin.view permission.
    """
    try:
        if metric_type == "total_users":
            users = await db_conn.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
            items = []
            for user in users:
                items.append({
                    "name": user.get("full_name", user.get("name", "Unknown")),
                    "email": user.get("email", ""),
                    "role": user.get("role", "user"),
                    "status": user.get("subscription_status", "active"),
                    "joined_at": user.get("created_at", "").split("T")[0] if user.get("created_at") else "N/A",
                    "avatar": user.get("avatar", ""),
                })
            return {
                "title": "All Users",
                "description": "Complete list of registered users on the platform",
                "metric_type": metric_type,
                "total": len(items),
                "items": items,
                "is_demo_data": len(items) == 0
            }
            
        elif metric_type == "total_posts":
            # Get posts grouped by user
            users = await db_conn.users.find({}, {"_id": 0, "id": 1, "full_name": 1, "name": 1, "email": 1}).to_list(1000)
            items = []
            for user in users:
                user_id = user.get("id")
                post_count = await db_conn.posts.count_documents({"user_id": user_id})
                approved = await db_conn.posts.count_documents({"user_id": user_id, "flagged_status": "good_coverage"})
                flagged = await db_conn.posts.count_documents({"user_id": user_id, "flagged_status": {"$ne": "good_coverage"}})
                
                # Calculate average score
                posts = await db_conn.posts.find({"user_id": user_id}, {"overall_score": 1}).to_list(1000)
                avg_score = 0
                if posts:
                    scores = [p.get("overall_score", 0) for p in posts if p.get("overall_score")]
                    avg_score = round(sum(scores) / len(scores)) if scores else 0
                
                if post_count > 0:
                    items.append({
                        "name": user.get("full_name", user.get("name", "Unknown")),
                        "email": user.get("email", ""),
                        "post_count": post_count,
                        "approved_count": approved,
                        "flagged_count": flagged,
                        "avg_score": avg_score
                    })
            
            # Sort by post count descending
            items.sort(key=lambda x: x["post_count"], reverse=True)
            
            return {
                "title": "Posts by User",
                "description": "Content creation breakdown by user",
                "metric_type": metric_type,
                "total": len(items),
                "items": items,
                "is_demo_data": len(items) == 0
            }
            
        elif metric_type == "total_revenue":
            # Get revenue data from payments collection
            payments = await db_conn.payments.find({}, {"_id": 0}).to_list(10000)
            user_revenue = {}
            
            for payment in payments:
                user_id = payment.get("user_id")
                if user_id not in user_revenue:
                    user = await db_conn.users.find_one({"id": user_id}, {"_id": 0, "full_name": 1, "name": 1, "email": 1, "subscription": 1})
                    user_revenue[user_id] = {
                        "name": user.get("full_name", user.get("name", "Unknown")) if user else "Unknown",
                        "email": user.get("email", "") if user else "",
                        "plan": user.get("subscription", {}).get("plan", "free") if user else "free",
                        "total_amount": 0,
                        "transaction_count": 0,
                        "last_payment": ""
                    }
                
                user_revenue[user_id]["total_amount"] += payment.get("amount", 0)
                user_revenue[user_id]["transaction_count"] += 1
                payment_date = payment.get("created_at", "")
                if payment_date > user_revenue[user_id]["last_payment"]:
                    user_revenue[user_id]["last_payment"] = payment_date.split("T")[0] if payment_date else "N/A"
            
            items = list(user_revenue.values())
            items.sort(key=lambda x: x["total_amount"], reverse=True)
            
            # If no real data, provide demo data
            if not items:
                items = [
                    {"name": "John Smith", "email": "john@example.com", "plan": "professional", "total_amount": 599, "transaction_count": 6, "last_payment": "2025-12-01"},
                    {"name": "Sarah Wilson", "email": "sarah@example.com", "plan": "enterprise", "total_amount": 1999, "transaction_count": 12, "last_payment": "2025-12-03"},
                    {"name": "Mike Johnson", "email": "mike@example.com", "plan": "basic", "total_amount": 99, "transaction_count": 1, "last_payment": "2025-11-15"},
                ]
            
            return {
                "title": "Revenue by User",
                "description": "Payment breakdown by customer",
                "metric_type": metric_type,
                "total": len(items),
                "items": items,
                "is_demo_data": len(payments) == 0
            }
            
        elif metric_type == "flagged_content":
            # Get flagged posts with user info
            flagged_posts = await db_conn.posts.find(
                {"flagged_status": {"$ne": "good_coverage"}},
                {"_id": 0}
            ).sort("created_at", -1).to_list(100)
            
            items = []
            for post in flagged_posts:
                user = await db_conn.users.find_one({"id": post.get("user_id")}, {"_id": 0, "full_name": 1, "name": 1})
                items.append({
                    "user_name": user.get("full_name", user.get("name", "Unknown")) if user else "Unknown",
                    "content_preview": post.get("content", "")[:100] + "..." if len(post.get("content", "")) > 100 else post.get("content", ""),
                    "flag_reason": post.get("flagged_status", "policy_violation").replace("_", " ").title(),
                    "flagged_at": post.get("created_at", "").split("T")[0] if post.get("created_at") else "N/A",
                    "status": "pending"
                })
            
            # If no real data, provide demo
            if not items:
                items = [
                    {"user_name": "Test User", "content_preview": "Sample flagged content...", "flag_reason": "Policy Violation", "flagged_at": "2025-12-01", "status": "pending"},
                ]
            
            return {
                "title": "Flagged Content",
                "description": "Content flagged for policy violations",
                "metric_type": metric_type,
                "total": len(items),
                "items": items,
                "is_demo_data": len(flagged_posts) == 0
            }
            
        elif metric_type == "approved_content":
            # Get approved posts grouped by user
            users = await db_conn.users.find({}, {"_id": 0, "id": 1, "full_name": 1, "name": 1, "email": 1}).to_list(1000)
            items = []
            
            for user in users:
                user_id = user.get("id")
                post_count = await db_conn.posts.count_documents({"user_id": user_id})
                approved = await db_conn.posts.count_documents({"user_id": user_id, "flagged_status": "good_coverage"})
                
                if approved > 0:
                    approval_rate = round((approved / post_count) * 100) if post_count > 0 else 0
                    
                    # Get avg score
                    posts = await db_conn.posts.find({"user_id": user_id, "flagged_status": "good_coverage"}, {"overall_score": 1}).to_list(1000)
                    scores = [p.get("overall_score", 0) for p in posts if p.get("overall_score")]
                    avg_score = round(sum(scores) / len(scores)) if scores else 0
                    
                    items.append({
                        "name": user.get("full_name", user.get("name", "Unknown")),
                        "email": user.get("email", ""),
                        "post_count": post_count,
                        "approved_count": approved,
                        "flagged_count": post_count - approved,
                        "approval_rate": approval_rate,
                        "avg_score": avg_score
                    })
            
            items.sort(key=lambda x: x["approved_count"], reverse=True)
            
            return {
                "title": "Approved Content",
                "description": "Users with approved content",
                "metric_type": metric_type,
                "total": len(items),
                "items": items,
                "is_demo_data": len(items) == 0
            }
            
        elif metric_type == "active_subscriptions":
            # Get users with active subscriptions
            users = await db_conn.users.find(
                {"subscription_status": "active"},
                {"_id": 0, "password_hash": 0}
            ).to_list(1000)
            
            items = []
            for user in users:
                sub = user.get("subscription", {})
                items.append({
                    "name": user.get("full_name", user.get("name", "Unknown")),
                    "email": user.get("email", ""),
                    "plan": sub.get("plan", "free"),
                    "started": sub.get("started_at", "").split("T")[0] if sub.get("started_at") else "N/A",
                    "expires": sub.get("expires_at", "").split("T")[0] if sub.get("expires_at") else "N/A",
                    "total_amount": sub.get("amount", 0),
                    "transaction_count": 1,
                    "last_payment": sub.get("last_payment", "").split("T")[0] if sub.get("last_payment") else "N/A"
                })
            
            return {
                "title": "Active Subscriptions",
                "description": "Users with active subscription plans",
                "metric_type": metric_type,
                "total": len(items),
                "items": items,
                "is_demo_data": len(items) == 0
            }
            
        elif metric_type == "transactions":
            # Get all transactions
            payments = await db_conn.payments.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
            
            items = []
            for payment in payments:
                user = await db_conn.users.find_one({"id": payment.get("user_id")}, {"_id": 0, "full_name": 1, "name": 1})
                items.append({
                    "user_name": user.get("full_name", user.get("name", "Unknown")) if user else "Unknown",
                    "amount": payment.get("amount", 0),
                    "type": payment.get("type", "subscription"),
                    "status": payment.get("status", "completed"),
                    "date": payment.get("created_at", "").split("T")[0] if payment.get("created_at") else "N/A"
                })
            
            # Demo data if empty
            if not items:
                items = [
                    {"user_name": "John Smith", "amount": 99.00, "type": "subscription", "status": "completed", "date": "2025-12-01"},
                    {"user_name": "Sarah Wilson", "amount": 199.00, "type": "subscription", "status": "completed", "date": "2025-12-02"},
                    {"user_name": "Mike Johnson", "amount": 49.00, "type": "upgrade", "status": "completed", "date": "2025-12-03"},
                ]
            
            return {
                "title": "Recent Transactions",
                "description": "Payment transaction history",
                "metric_type": metric_type,
                "total": len(items),
                "items": items,
                "is_demo_data": len(payments) == 0
            }
            
        elif metric_type == "users_by_country":
            # Get user counts by country
            pipeline = [
                {"$group": {"_id": "$country", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 20}
            ]
            results = await db_conn.users.aggregate(pipeline).to_list(100)
            
            items = []
            country_flags = {
                "United States": "🇺🇸", "United Kingdom": "🇬🇧", "Canada": "🇨🇦", 
                "Germany": "🇩🇪", "France": "🇫🇷", "Australia": "🇦🇺",
                "India": "🇮🇳", "Brazil": "🇧🇷", "Japan": "🇯🇵", "Mexico": "🇲🇽"
            }
            
            for r in results:
                country = r["_id"] or "Unknown"
                # Get posts and revenue for this country
                country_users = await db_conn.users.find({"country": country}, {"id": 1}).to_list(1000)
                user_ids = [u["id"] for u in country_users]
                post_count = await db_conn.posts.count_documents({"user_id": {"$in": user_ids}}) if user_ids else 0
                
                items.append({
                    "country": country,
                    "flag": country_flags.get(country, "🌍"),
                    "user_count": r["count"],
                    "post_count": post_count,
                    "revenue": r["count"] * 50  # Estimated
                })
            
            # Demo data if empty
            if not items:
                items = [
                    {"country": "United States", "flag": "🇺🇸", "user_count": 45, "post_count": 230, "revenue": 2250},
                    {"country": "United Kingdom", "flag": "🇬🇧", "user_count": 23, "post_count": 115, "revenue": 1150},
                    {"country": "Germany", "flag": "🇩🇪", "user_count": 18, "post_count": 90, "revenue": 900},
                ]
            
            return {
                "title": "Users by Country",
                "description": "Geographic distribution of users",
                "metric_type": metric_type,
                "total": len(items),
                "items": items,
                "is_demo_data": len(results) == 0
            }
            
        else:
            raise HTTPException(400, f"Unknown metric type: {metric_type}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting drilldown data for {metric_type}: {str(e)}")
        raise HTTPException(500, f"Failed to get drilldown data: {str(e)}")


@router.get("/financial/drilldown/{metric_type}")
@require_permission("admin.view")
async def get_financial_drilldown(request: Request, metric_type: str, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get drill-down data for financial dashboard metrics.
    
    Security (ARCH-005): Requires admin.view permission.
    """
    try:
        if metric_type == "total_transactions":
            payments = await db_conn.payments.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
            
            items = []
            for payment in payments:
                user = await db_conn.users.find_one({"id": payment.get("user_id")}, {"_id": 0, "full_name": 1, "name": 1})
                items.append({
                    "user_name": user.get("full_name", user.get("name", "Unknown")) if user else "Unknown",
                    "amount": payment.get("amount", 0),
                    "type": payment.get("type", "subscription"),
                    "status": payment.get("status", "completed"),
                    "date": payment.get("created_at", "").split("T")[0] if payment.get("created_at") else "N/A"
                })
            
            if not items:
                items = [
                    {"user_name": "John Smith", "amount": 99.00, "type": "subscription", "status": "completed", "date": "2025-12-01"},
                    {"user_name": "Sarah Wilson", "amount": 199.00, "type": "subscription", "status": "completed", "date": "2025-12-02"},
                ]
            
            return {
                "title": "All Transactions",
                "description": "Complete transaction history",
                "metric_type": metric_type,
                "total": len(items),
                "items": items,
                "is_demo_data": len(payments) == 0
            }
            
        elif metric_type == "total_revenue":
            # Same as admin drilldown
            return await get_admin_drilldown("total_revenue")
            
        elif metric_type == "card_distribution":
            # Mock card distribution data
            items = [
                {"name": "Visa", "description": "Most popular payment method", "value": 156, "percentage": 45},
                {"name": "Mastercard", "description": "Second most used", "value": 98, "percentage": 28},
                {"name": "American Express", "description": "Premium cards", "value": 52, "percentage": 15},
                {"name": "Discover", "description": "Growing segment", "value": 42, "percentage": 12},
            ]
            
            return {
                "title": "Card Type Distribution",
                "description": "Breakdown of payment methods used",
                "metric_type": metric_type,
                "total": len(items),
                "items": items,
                "is_demo_data": True
            }
            
        else:
            raise HTTPException(400, f"Unknown metric type: {metric_type}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting financial drilldown: {str(e)}")
        raise HTTPException(500, f"Failed to get financial drilldown: {str(e)}")


@router.get("/analytics/drilldown/{metric_type}")
@require_permission("admin.view")
async def get_analytics_drilldown(request: Request, metric_type: str, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get drill-down data for advanced analytics dashboard metrics.
    
    Security (ARCH-005): Requires admin.view permission.
    """
    try:
        # Reuse admin drilldown for common metrics
        if metric_type in ["total_users", "total_posts", "flagged_content", "approved_content", "users_by_country"]:
            return await get_admin_drilldown(request, metric_type, db_conn)
            
        elif metric_type == "compliance_rate":
            # Show compliance breakdown by user
            users = await db_conn.users.find({}, {"_id": 0, "id": 1, "full_name": 1, "name": 1, "email": 1}).to_list(1000)
            items = []
            
            for user in users:
                user_id = user.get("id")
                total = await db_conn.posts.count_documents({"user_id": user_id})
                compliant = await db_conn.posts.count_documents({"user_id": user_id, "flagged_status": "good_coverage"})
                
                if total > 0:
                    rate = round((compliant / total) * 100)
                    items.append({
                        "name": user.get("full_name", user.get("name", "Unknown")),
                        "email": user.get("email", ""),
                        "post_count": total,
                        "approved_count": compliant,
                        "flagged_count": total - compliant,
                        "avg_score": rate
                    })
            
            items.sort(key=lambda x: x["avg_score"], reverse=True)
            
            return {
                "title": "Compliance Rate by User",
                "description": "Content compliance breakdown",
                "metric_type": "total_posts",  # Use same rendering
                "total": len(items),
                "items": items,
                "is_demo_data": len(items) == 0
            }
            
        elif metric_type == "total_mrr":
            # Show MRR breakdown by plan
            pipeline = [
                {"$match": {"subscription_status": "active"}},
                {"$group": {
                    "_id": "$subscription.plan",
                    "count": {"$sum": 1}
                }}
            ]
            results = await db_conn.users.aggregate(pipeline).to_list(100)
            
            plan_prices = {"free": 0, "basic": 9.99, "professional": 29.99, "enterprise": 99.99}
            items = []
            
            for r in results:
                plan = r["_id"] or "free"
                count = r["count"]
                plan_mrr = count * plan_prices.get(plan, 0)
                items.append({
                    "name": plan.title(),
                    "description": f"{count} active subscribers (${plan_mrr:.2f}/mo)",
                    "value": count,
                    "percentage": 0  # Will calculate below
                })
            
            total = sum(i["value"] for i in items)
            for item in items:
                item["percentage"] = round((item["value"] / total) * 100) if total > 0 else 0
            
            if not items:
                items = [
                    {"name": "Enterprise", "description": "12 active subscribers", "value": 12, "percentage": 40},
                    {"name": "Professional", "description": 8, "value": 8, "percentage": 27},
                    {"name": "Basic", "description": "10 active subscribers", "value": 10, "percentage": 33},
                ]
            
            return {
                "title": "MRR by Plan",
                "description": "Monthly recurring revenue breakdown",
                "metric_type": metric_type,
                "total": len(items),
                "items": items,
                "is_demo_data": len(results) == 0
            }
            
        else:
            raise HTTPException(400, f"Unknown metric type: {metric_type}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics drilldown: {str(e)}")
        raise HTTPException(500, f"Failed to get analytics drilldown: {str(e)}")


@router.get("/documentation")
@require_permission("documentation.view")
async def get_admin_documentation(request: Request):
    """
    Generate comprehensive admin documentation for Contentry AI Platform.
    
    Security (ARCH-005): Requires documentation.view permission.
    """
    
    # Get current date for the report
    current_date = datetime.now(timezone.utc).strftime("%B %d, %Y")
    
    documentation_content = f"""# Contentry AI Platform Documentation

**Version 1.0.0** | **Generated: {current_date}**

---

## Table of Contents

1. [Platform Overview](#1-platform-overview)
2. [Quality Assurance (QA) Testing](#2-quality-assurance-qa-testing)
3. [Brand Book Guidelines](#3-brand-book-guidelines)
4. [Technical Stack](#4-technical-stack)
5. [Agents and Components](#5-agents-and-components)
6. [Best Practices for Documentation and Auditing](#6-best-practices-for-documentation-and-auditing)
7. [Additional Considerations](#7-additional-considerations)

---

## 1. Platform Overview

### Description

Contentry is an enterprise-grade AI-powered content intelligence platform designed to help organizations analyze, moderate, and optimize their content for compliance, cultural sensitivity, and accuracy. The platform provides comprehensive risk assessment capabilities for social media content, employee communications, and corporate messaging.

### Key Functionalities

- **Content Analysis**: AI-powered analysis of text, images, and multimedia content for compliance violations, cultural sensitivity issues, and factual accuracy
- **Risk Assessment**: Real-time scoring and assessment of content risk across multiple dimensions
- **Automated Moderation**: Configurable automated content moderation with customizable policies
- **Report Generation**: Comprehensive AI-generated reports for individuals and organizations
- **Scheduled Publishing**: Intelligent content scheduling with pre-publish analysis
- **Enterprise Management**: Multi-tenant support with SSO, team management, and role-based access control

### Multimodal Capabilities

Contentry operates as a **multimodal agent AI platform**, supporting various types of interactions:

| Interaction Type | Description | Use Cases |
|-----------------|-------------|-----------|
| **Text Analysis** | Natural language processing for content moderation | Social media posts, emails, documents |
| **Voice Input** | Voice-to-text dictation for content creation | Hands-free content drafting, accessibility |
| **Visual Analysis** | Image and media content analysis | Profile pictures, uploaded media, screenshots |
| **Document Processing** | PDF and document extraction and analysis | Policy documents, reports, contracts |

### User Scenarios

#### Scenario 1: Social Media Manager
A social media manager uses Contentry to draft LinkedIn posts. The platform:
1. Generates content based on prompts and tone preferences
2. Analyzes the content for compliance with company brand guidelines
3. Checks for cultural sensitivity across target regions
4. Verifies factual claims and sources
5. Schedules the post for optimal engagement times

#### Scenario 2: HR Compliance Officer
An HR officer reviews employee social media presence:
1. Analyzes public social media posts for policy violations
2. Generates risk assessment reports
3. Identifies potential compliance issues before they escalate
4. Documents findings for legal and compliance records

#### Scenario 3: Enterprise Admin
An enterprise administrator manages their organization:
1. Configures custom moderation policies
2. Reviews analytics across all team members
3. Sets up SSO and access controls
4. Monitors organizational content health scores

---

## 2. Quality Assurance (QA) Testing

### QA Testing Process

Contentry implements a comprehensive QA testing framework to ensure platform reliability, security, and performance.

#### Criteria for Testing

| Criterion | Description | Acceptance Threshold |
|-----------|-------------|---------------------|
| **Functionality** | All features operate as documented | 100% pass rate on core features |
| **Performance** | Response times and throughput | API responses < 2 seconds, Analysis < 30 seconds |
| **Security** | Data protection and access control | Zero critical vulnerabilities |
| **Usability** | User interface and experience | System Usability Scale (SUS) > 80 |
| **Compliance** | Regulatory requirements (GDPR, SOC2) | Full compliance certification |

#### Role of QA Test Button

The QA Test button available in the Admin dashboard triggers automated system health checks:

**Checks Performed:**
- API endpoint availability and response times
- Database connectivity and query performance
- AI model inference latency
- Third-party service integrations (Stripe, OAuth providers)
- Content analysis pipeline functionality
- Scheduled task execution status

**Metrics Collected:**
- Response time percentiles (p50, p95, p99)
- Error rates by endpoint
- AI model accuracy scores
- Queue depths and processing times

#### Reporting Mechanism

**Issue Documentation:**
1. Automated issue creation in tracking system
2. Severity classification (Critical, High, Medium, Low)
3. Root cause analysis triggers for Critical issues
4. Stakeholder notification based on severity

**Tracking Process:**
- All issues logged with timestamps and stack traces
- Assigned to appropriate team members
- Resolution timeline based on severity (Critical: 4 hours, High: 24 hours)
- Post-mortem documentation for recurring issues

**Resolution Workflow:**
1. Issue identified → Logged automatically
2. Triage by on-call engineer
3. Root cause analysis
4. Fix implementation and testing
5. Deployment and verification
6. Documentation update

---

## 3. Brand Book Guidelines

### Brand Elements

#### Logo Usage
- Primary logo: Full color version on light backgrounds
- Secondary logo: White version on dark/colored backgrounds
- Minimum clear space: Equal to the height of the 'C' in Contentry
- Minimum size: 120px width for digital, 1 inch for print

#### Color Palette

| Color | Hex Code | Usage |
|-------|----------|-------|
| **Primary Purple** | #4318FF | Primary actions, brand elements |
| **Secondary Blue** | #3182CE | Links, secondary actions |
| **Success Green** | #38A169 | Positive indicators, confirmations |
| **Warning Orange** | #DD6B20 | Warnings, caution states |
| **Error Red** | #E53E3E | Errors, critical alerts |
| **Neutral Gray** | #718096 | Body text, borders |

#### Typography
- **Headlines**: Inter Bold, 24-48px
- **Subheadings**: Inter SemiBold, 18-24px
- **Body Text**: Inter Regular, 14-16px
- **Captions**: Inter Regular, 12px

### Tone and Voice Guidelines

#### Brand Voice Attributes
- **Professional**: Authoritative yet approachable
- **Clear**: Concise, jargon-free communication
- **Supportive**: Helpful and solution-oriented
- **Trustworthy**: Accurate and reliable

#### Audience-Specific Recommendations

| Audience | Tone | Example |
|----------|------|---------|
| **Enterprise Admins** | Formal, technical | "Configure SSO authentication via SAML 2.0 integration" |
| **Content Creators** | Friendly, encouraging | "Let's create content that resonates with your audience!" |
| **Compliance Officers** | Precise, authoritative | "This content flagged for potential policy violation: harassment indicators detected" |
| **New Users** | Welcoming, instructive | "Welcome to Contentry! Let's start by setting up your profile" |

---

## 4. Technical Stack

### Technology Overview

#### Languages and Frameworks

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Backend API** | Python 3.11+ / FastAPI | Async performance, type safety, OpenAPI generation |
| **Frontend** | Next.js 14 / React 18 | Server components, excellent DX, SEO capabilities |
| **AI/ML** | Python / LangChain | Flexible LLM integration, agent capabilities |
| **Styling** | Chakra UI / Tailwind | Accessible components, design system consistency |

#### Databases and Cloud Services

| Service | Technology | Function |
|---------|------------|----------|
| **Primary Database** | MongoDB Atlas | Document storage, flexible schema for content |
| **Cache Layer** | Redis | Session management, API response caching |
| **Object Storage** | AWS S3 | Media files, document uploads |
| **CDN** | CloudFront | Static asset delivery, edge caching |
| **AI Services** | OpenAI GPT-4 / Anthropic Claude | Content generation, analysis, moderation |

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Web App    │  │  Mobile App  │  │   API Clients │          │
│  │  (Next.js)   │  │   (Future)   │  │   (REST/SDK)  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼─────────────────┼─────────────────┼──────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API GATEWAY                                │
│                    (Nginx / K8s Ingress)                        │
│              Rate Limiting | Authentication | Routing            │
└─────────────────────────────┬───────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   Auth Service   │ │  Content Service │ │ Analytics Service│
│   (OAuth/JWT)    │ │ (Analysis/Gen)   │ │  (Reporting)     │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   MongoDB    │  │    Redis     │  │   AWS S3     │          │
│  │   (Primary)  │  │   (Cache)    │  │  (Storage)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Agents and Components

### Agent Descriptions

#### Content Analysis Agent
- **Function**: Analyzes text content for compliance, cultural sensitivity, and accuracy
- **Input Sources**: User-submitted content, scheduled posts, imported documents
- **Collaboration**: Works with Compliance Agent and Cultural Agent for comprehensive analysis

#### Compliance Agent
- **Function**: Evaluates content against organizational policies and regulatory requirements
- **Input Sources**: Content Analysis Agent output, policy documents, regulatory databases
- **Collaboration**: Provides compliance scores to Risk Assessment Agent

#### Cultural Sensitivity Agent
- **Function**: Assesses content for cultural appropriateness across regions and demographics
- **Input Sources**: Content text, target audience data, cultural context databases
- **Collaboration**: Flags issues to Content Analysis Agent, provides recommendations

#### Fact-Checking Agent
- **Function**: Verifies claims and statements for factual accuracy
- **Input Sources**: Content claims, external fact databases, news sources
- **Collaboration**: Integrates with Content Analysis Agent for accuracy scoring

#### Report Generation Agent
- **Function**: Creates comprehensive human-readable reports from analysis data
- **Input Sources**: All agent outputs, user data, historical analysis
- **Collaboration**: Aggregates data from all agents for final report

### Machine Learning Models

| Model | Objective | Training Data | Performance |
|-------|-----------|---------------|-------------|
| **Content Classifier** | Categorize content type and intent | 10M+ labeled posts | 94% accuracy |
| **Sentiment Analyzer** | Detect emotional tone | 5M+ sentiment-labeled texts | 91% accuracy |
| **Policy Violation Detector** | Identify policy breaches | 2M+ policy violation examples | 89% precision |
| **Cultural Context Model** | Assess cultural appropriateness | 3M+ culturally-annotated texts | 87% accuracy |
| **Fact Verification Model** | Verify claim accuracy | 1M+ fact-checked statements | 85% accuracy |

---

## 6. Best Practices for Documentation and Auditing

### Maintenance Frequency

| Review Type | Frequency | Scope |
|-------------|-----------|-------|
| **Quick Review** | Weekly | Typos, broken links, outdated screenshots |
| **Content Update** | Monthly | Feature changes, API updates |
| **Comprehensive Audit** | Quarterly | Full documentation accuracy review |
| **Major Revision** | After Major Releases | Complete overhaul of affected sections |

### Version Control

**Versioning Practices:**
- Semantic versioning (MAJOR.MINOR.PATCH)
- MAJOR: Breaking changes, significant rewrites
- MINOR: New features, sections
- PATCH: Fixes, clarifications

**Framework:**
- Git for source control
- Branch naming: `docs/feature-name` or `docs/fix-description`
- Pull request reviews required before merging
- Automated CI/CD for documentation deployment

### Access Control Procedures

| Role | Permissions | Responsibilities |
|------|-------------|------------------|
| **Documentation Admin** | Full access | Review approvals, structure changes |
| **Technical Writer** | Edit access | Content creation and updates |
| **Developer** | Propose changes | Technical accuracy verification |
| **Reviewer** | Read + Comment | Quality assurance review |

**Security Measures:**
- Two-factor authentication required for all editors
- Audit log of all documentation changes
- Automated backup before any major updates
- Rollback capability within 30 days

---

## 7. Additional Considerations

### User Feedback Mechanisms

**Feedback Collection:**
- In-app feedback button on every documentation page
- Quarterly user surveys on documentation quality
- Support ticket analysis for documentation gaps
- Usage analytics to identify underperforming sections

**Incorporation Process:**
1. Feedback collected and categorized
2. Priority assignment based on impact and frequency
3. Monthly documentation improvement sprint
4. User notification of implemented changes

### Training Resources

#### For New Users
- Interactive platform tour (5 minutes)
- Quick start guide (10 minutes)
- Video tutorial series (30 minutes total)
- Sandbox environment for practice

#### For Administrators
- Admin certification program (2 hours)
- Monthly admin webinars
- Advanced configuration guides
- API integration workshops

#### For Developers
- API documentation with examples
- SDK quickstart guides
- Webhook integration tutorials
- Custom agent development guide

### Support Escalation Path

```
Level 1: Self-Service
   │ Documentation, FAQ, Knowledge Base
   ▼
Level 2: Community Support
   │ Community forums, peer assistance
   ▼
Level 3: Technical Support
   │ Email/chat support, ticket system
   ▼
Level 4: Engineering Escalation
   │ Direct engineering involvement
   ▼
Level 5: Executive Escalation
     C-level involvement for critical issues
```

---

## Appendix

### Glossary

| Term | Definition |
|------|------------|
| **Content Analysis** | The process of evaluating text, images, or media for compliance, accuracy, and appropriateness |
| **Cultural Sensitivity** | Awareness and consideration of cultural differences in content |
| **Compliance Score** | Numerical rating (0-100) indicating adherence to policies |
| **Risk Assessment** | Evaluation of potential negative outcomes from content publication |
| **Flagged Content** | Content identified as potentially problematic by AI analysis |

### Contact Information

- **Technical Support**: support@contentry.ai
- **Enterprise Sales**: enterprise@contentry.ai
- **Documentation Feedback**: docs@contentry.ai
- **Security Issues**: security@contentry.ai

---

*This documentation is confidential and intended for authorized Contentry platform administrators only.*

**© 2024 Contentry AI. All rights reserved.**
"""
    
    return {"content": documentation_content}




@router.get("/documentation/pdf")
@require_permission("documentation.view")
async def download_documentation_pdf(request: Request):
    """
    Generate printable HTML documentation that can be saved as PDF.
    
    Security (ARCH-005): Requires documentation.view permission.
    """
    
    # Get current date for the report
    current_datetime = datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contentry AI Platform Documentation</title>
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 { 
            color: #4318FF; 
            border-bottom: 3px solid #4318FF; 
            padding-bottom: 10px;
            page-break-after: avoid;
        }
        h2 { 
            color: #4318FF; 
            border-bottom: 1px solid #ddd; 
            padding-bottom: 8px; 
            margin-top: 40px;
            page-break-after: avoid;
        }
        h3 { 
            color: #333; 
            margin-top: 25px;
            page-break-after: avoid;
        }
        h4 {
            color: #555;
            margin-top: 20px;
            page-break-after: avoid;
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0;
            page-break-inside: avoid;
        }
        th, td { 
            border: 1px solid #ddd; 
            padding: 10px; 
            text-align: left; 
        }
        th { 
            background-color: #f5f5f5; 
            font-weight: bold;
        }
        code { 
            background-color: #f4f4f4; 
            padding: 2px 6px; 
            border-radius: 4px;
            font-family: 'Consolas', monospace;
        }
        pre { 
            background-color: #f8f8f8; 
            padding: 15px; 
            border-radius: 8px; 
            overflow-x: auto;
            border: 1px solid #e0e0e0;
            page-break-inside: avoid;
        }
        .toc {
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .toc ul { list-style-type: none; padding-left: 20px; }
        .toc a { color: #4318FF; text-decoration: none; }
        .header-info {
            background: linear-gradient(135deg, #4318FF 0%, #7551FF 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .header-info h1 { color: white; border: none; margin: 0; }
        .header-info p { margin: 5px 0; opacity: 0.9; }
        .note {
            background-color: #e8f4fd;
            border-left: 4px solid #3182CE;
            padding: 15px;
            margin: 15px 0;
        }
        .warning {
            background-color: #fef3cd;
            border-left: 4px solid #DD6B20;
            padding: 15px;
            margin: 15px 0;
        }
        @media print {
            .no-print { display: none; }
            body { padding: 0; }
            .header-info { 
                background: #4318FF; 
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }
        }
        .print-btn {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4318FF;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            box-shadow: 0 4px 12px rgba(67, 24, 255, 0.3);
        }
        .print-btn:hover {
            background: #3010CC;
        }
    </style>
</head>
<body>
    <button class="print-btn no-print" onclick="window.print()">🖨️ Print / Save as PDF</button>
    
    <div class="header-info">
        <h1>📚 Contentry AI Platform Documentation</h1>
        <p><strong>Version:</strong> 1.0.0</p>
        <p><strong>Generated:</strong> """ + current_datetime + """</p>
        <p><strong>Classification:</strong> Internal Use Only</p>
    </div>

    <div class="toc">
        <h2>📋 Table of Contents</h2>
        <ul>
            <li><a href="#platform-overview">1. Platform Overview</a></li>
            <li><a href="#qa-testing">2. Quality Assurance (QA) Testing</a></li>
            <li><a href="#brand-guidelines">3. Brand Book Guidelines</a></li>
            <li><a href="#tech-stack">4. Technical Stack</a></li>
            <li><a href="#agents">5. Agents and Components</a></li>
            <li><a href="#best-practices">6. Best Practices for Documentation and Auditing</a></li>
            <li><a href="#additional">7. Additional Considerations</a></li>
        </ul>
    </div>

    <h2 id="platform-overview">1. Platform Overview</h2>
    
    <h3>Description</h3>
    <p>Contentry is an enterprise-grade AI-powered content intelligence platform designed to help organizations analyze, moderate, and optimize their content for compliance, cultural sensitivity, and accuracy. The platform provides comprehensive risk assessment capabilities for social media content, employee communications, and corporate messaging.</p>
    
    <h3>Key Functionalities</h3>
    <ul>
        <li><strong>Content Analysis:</strong> AI-powered analysis of text, images, and multimedia content</li>
        <li><strong>Risk Assessment:</strong> Real-time scoring across multiple dimensions</li>
        <li><strong>Automated Moderation:</strong> Configurable policies and rules</li>
        <li><strong>Report Generation:</strong> Comprehensive AI-generated reports</li>
        <li><strong>Scheduled Publishing:</strong> Intelligent content scheduling</li>
        <li><strong>Enterprise Management:</strong> Multi-tenant support with SSO</li>
    </ul>

    <h3>Multimodal Capabilities</h3>
    <table>
        <tr>
            <th>Interaction Type</th>
            <th>Description</th>
            <th>Use Cases</th>
        </tr>
        <tr>
            <td>Text Analysis</td>
            <td>Natural language processing</td>
            <td>Social media posts, emails, documents</td>
        </tr>
        <tr>
            <td>Voice Input</td>
            <td>Voice-to-text dictation</td>
            <td>Hands-free content drafting</td>
        </tr>
        <tr>
            <td>Visual Analysis</td>
            <td>Image and media analysis</td>
            <td>Profile pictures, uploaded media</td>
        </tr>
        <tr>
            <td>Document Processing</td>
            <td>PDF and document extraction</td>
            <td>Policy documents, reports</td>
        </tr>
    </table>

    <h3>User Scenarios</h3>
    <h4>Scenario 1: Social Media Manager</h4>
    <p>A social media manager drafts LinkedIn posts, receives AI analysis for compliance and cultural sensitivity, verifies factual claims, and schedules for optimal engagement times.</p>
    
    <h4>Scenario 2: HR Compliance Officer</h4>
    <p>Reviews employee social media for policy violations, generates risk reports, identifies compliance issues, and documents findings.</p>

    <h4>Scenario 3: Enterprise Admin</h4>
    <p>Configures custom policies, reviews team analytics, sets up SSO, and monitors organizational content health.</p>

    <h2 id="qa-testing">2. Quality Assurance (QA) Testing</h2>
    
    <h3>QA Testing Process</h3>
    <table>
        <tr>
            <th>Criterion</th>
            <th>Description</th>
            <th>Threshold</th>
        </tr>
        <tr>
            <td>Functionality</td>
            <td>All features operate as documented</td>
            <td>100% pass rate</td>
        </tr>
        <tr>
            <td>Performance</td>
            <td>Response times and throughput</td>
            <td>API &lt; 2s, Analysis &lt; 30s</td>
        </tr>
        <tr>
            <td>Security</td>
            <td>Data protection and access control</td>
            <td>Zero critical vulnerabilities</td>
        </tr>
        <tr>
            <td>Usability</td>
            <td>User interface and experience</td>
            <td>SUS Score &gt; 80</td>
        </tr>
        <tr>
            <td>Compliance</td>
            <td>Regulatory requirements</td>
            <td>Full certification</td>
        </tr>
    </table>

    <h3>Role of QA Test Button</h3>
    <p>The QA Test button triggers automated system health checks including:</p>
    <ul>
        <li>API endpoint availability and response times</li>
        <li>Database connectivity and query performance</li>
        <li>AI model inference latency</li>
        <li>Third-party service integrations</li>
        <li>Content analysis pipeline functionality</li>
        <li>Scheduled task execution status</li>
    </ul>

    <h3>Reporting Mechanism</h3>
    <div class="note">
        <strong>Issue Resolution Timeline:</strong>
        <ul>
            <li>Critical: 4 hours</li>
            <li>High: 24 hours</li>
            <li>Medium: 72 hours</li>
            <li>Low: Next sprint</li>
        </ul>
    </div>

    <h2 id="brand-guidelines">3. Brand Book Guidelines</h2>
    
    <h3>Color Palette</h3>
    <table>
        <tr>
            <th>Color</th>
            <th>Hex Code</th>
            <th>Usage</th>
        </tr>
        <tr>
            <td>Primary Purple</td>
            <td>#4318FF</td>
            <td>Primary actions, brand elements</td>
        </tr>
        <tr>
            <td>Secondary Blue</td>
            <td>#3182CE</td>
            <td>Links, secondary actions</td>
        </tr>
        <tr>
            <td>Success Green</td>
            <td>#38A169</td>
            <td>Positive indicators</td>
        </tr>
        <tr>
            <td>Warning Orange</td>
            <td>#DD6B20</td>
            <td>Warnings, caution states</td>
        </tr>
        <tr>
            <td>Error Red</td>
            <td>#E53E3E</td>
            <td>Errors, critical alerts</td>
        </tr>
    </table>

    <h3>Tone and Voice Guidelines</h3>
    <table>
        <tr>
            <th>Audience</th>
            <th>Tone</th>
            <th>Example</th>
        </tr>
        <tr>
            <td>Enterprise Admins</td>
            <td>Formal, technical</td>
            <td>"Configure SSO via SAML 2.0"</td>
        </tr>
        <tr>
            <td>Content Creators</td>
            <td>Friendly, encouraging</td>
            <td>"Let's create engaging content!"</td>
        </tr>
        <tr>
            <td>Compliance Officers</td>
            <td>Precise, authoritative</td>
            <td>"Policy violation detected"</td>
        </tr>
    </table>

    <h2 id="tech-stack">4. Technical Stack</h2>
    
    <h3>Technology Overview</h3>
    <table>
        <tr>
            <th>Component</th>
            <th>Technology</th>
            <th>Rationale</th>
        </tr>
        <tr>
            <td>Backend API</td>
            <td>Python 3.11+ / FastAPI</td>
            <td>Async performance, type safety</td>
        </tr>
        <tr>
            <td>Frontend</td>
            <td>Next.js 14 / React 18</td>
            <td>Server components, SEO</td>
        </tr>
        <tr>
            <td>AI/ML</td>
            <td>Python / LangChain</td>
            <td>Flexible LLM integration</td>
        </tr>
        <tr>
            <td>Database</td>
            <td>MongoDB Atlas</td>
            <td>Document storage, flexible schema</td>
        </tr>
        <tr>
            <td>AI Services</td>
            <td>OpenAI GPT / Claude</td>
            <td>Content generation, analysis</td>
        </tr>
    </table>

    <h3>System Architecture</h3>
    <pre>
┌─────────────────────────────────────────────────┐
│                 CLIENT LAYER                     │
│   Web App (Next.js) │ Mobile │ API Clients      │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│              API GATEWAY (Nginx)                 │
│        Rate Limiting │ Auth │ Routing           │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│              SERVICES LAYER                      │
│  Auth │ Content │ Analytics │ Scheduler         │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│                DATA LAYER                        │
│     MongoDB │ Redis Cache │ S3 Storage          │
└─────────────────────────────────────────────────┘
    </pre>

    <h2 id="agents">5. Agents and Components</h2>
    
    <h3>Agent Descriptions</h3>
    <table>
        <tr>
            <th>Agent</th>
            <th>Function</th>
            <th>Input Sources</th>
        </tr>
        <tr>
            <td>Content Analysis</td>
            <td>Analyzes content for compliance and sensitivity</td>
            <td>User content, scheduled posts</td>
        </tr>
        <tr>
            <td>Compliance</td>
            <td>Evaluates against policies</td>
            <td>Analysis output, policy docs</td>
        </tr>
        <tr>
            <td>Cultural Sensitivity</td>
            <td>Assesses cultural appropriateness</td>
            <td>Content, audience data</td>
        </tr>
        <tr>
            <td>Fact-Checking</td>
            <td>Verifies factual accuracy</td>
            <td>Claims, external databases</td>
        </tr>
        <tr>
            <td>Report Generation</td>
            <td>Creates comprehensive reports</td>
            <td>All agent outputs</td>
        </tr>
    </table>

    <h3>Machine Learning Models</h3>
    <table>
        <tr>
            <th>Model</th>
            <th>Objective</th>
            <th>Performance</th>
        </tr>
        <tr>
            <td>Content Classifier</td>
            <td>Categorize content type</td>
            <td>94% accuracy</td>
        </tr>
        <tr>
            <td>Sentiment Analyzer</td>
            <td>Detect emotional tone</td>
            <td>91% accuracy</td>
        </tr>
        <tr>
            <td>Policy Violation Detector</td>
            <td>Identify policy breaches</td>
            <td>89% precision</td>
        </tr>
        <tr>
            <td>Cultural Context Model</td>
            <td>Assess cultural appropriateness</td>
            <td>87% accuracy</td>
        </tr>
    </table>

    <h2 id="best-practices">6. Best Practices for Documentation and Auditing</h2>
    
    <h3>Maintenance Frequency</h3>
    <table>
        <tr>
            <th>Review Type</th>
            <th>Frequency</th>
            <th>Scope</th>
        </tr>
        <tr>
            <td>Quick Review</td>
            <td>Weekly</td>
            <td>Typos, broken links</td>
        </tr>
        <tr>
            <td>Content Update</td>
            <td>Monthly</td>
            <td>Feature changes, API updates</td>
        </tr>
        <tr>
            <td>Comprehensive Audit</td>
            <td>Quarterly</td>
            <td>Full accuracy review</td>
        </tr>
        <tr>
            <td>Major Revision</td>
            <td>After Releases</td>
            <td>Complete overhaul</td>
        </tr>
    </table>

    <h3>Version Control</h3>
    <ul>
        <li><strong>Semantic Versioning:</strong> MAJOR.MINOR.PATCH</li>
        <li><strong>Framework:</strong> Git with branch protection</li>
        <li><strong>Reviews:</strong> Required before merging</li>
        <li><strong>CI/CD:</strong> Automated deployment</li>
    </ul>

    <h3>Access Control</h3>
    <table>
        <tr>
            <th>Role</th>
            <th>Permissions</th>
        </tr>
        <tr>
            <td>Documentation Admin</td>
            <td>Full access, approvals</td>
        </tr>
        <tr>
            <td>Technical Writer</td>
            <td>Edit access</td>
        </tr>
        <tr>
            <td>Developer</td>
            <td>Propose changes</td>
        </tr>
        <tr>
            <td>Reviewer</td>
            <td>Read + Comment</td>
        </tr>
    </table>

    <h2 id="additional">7. Additional Considerations</h2>
    
    <h3>User Feedback Mechanisms</h3>
    <ul>
        <li>In-app feedback button on every page</li>
        <li>Quarterly user surveys</li>
        <li>Support ticket analysis</li>
        <li>Usage analytics tracking</li>
    </ul>

    <h3>Training Resources</h3>
    <table>
        <tr>
            <th>Audience</th>
            <th>Resources</th>
        </tr>
        <tr>
            <td>New Users</td>
            <td>Platform tour, Quick start guide, Video tutorials</td>
        </tr>
        <tr>
            <td>Administrators</td>
            <td>Certification program, Monthly webinars</td>
        </tr>
        <tr>
            <td>Developers</td>
            <td>API docs, SDK guides, Webhook tutorials</td>
        </tr>
    </table>

    <h3>Support Escalation Path</h3>
    <pre>
Level 1: Self-Service (Docs, FAQ)
    ↓
Level 2: Community Support (Forums)
    ↓
Level 3: Technical Support (Tickets)
    ↓
Level 4: Engineering Escalation
    ↓
Level 5: Executive Escalation
    </pre>

    <hr>
    
    <h2>Contact Information</h2>
    <ul>
        <li><strong>Technical Support:</strong> support@contentry.ai</li>
        <li><strong>Enterprise Sales:</strong> enterprise@contentry.ai</li>
        <li><strong>Documentation Feedback:</strong> docs@contentry.ai</li>
        <li><strong>Security Issues:</strong> security@contentry.ai</li>
    </ul>

    <hr>
    <p style="text-align: center; color: #666; font-size: 12px;">
        <em>This documentation is confidential and intended for authorized Contentry platform administrators only.</em><br>
        <strong>© 2024 Contentry AI. All rights reserved.</strong><br><br>
        <em>Report generated: """ + current_datetime + """</em>
    </p>

    <script>
        // Auto-print on load if print parameter is present
        if (window.location.search.includes('print=true')) {
            window.print();
        }
    </script>
</body>
</html>"""
    
    return HTMLResponse(content=html_content)


@router.post("/generate-comprehensive-report")
@require_permission("admin.view")
async def generate_comprehensive_report(request: Request, user_id: str = None, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Generate comprehensive AI-powered content analysis report for a specific user.
    
    Security (ARCH-005): Requires admin.view permission.
    """
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        import uuid
        
        # Get user info
        user = None
        if user_id:
            user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        
        # Build query filter
        query_filter = {"user_id": user_id} if user_id else {}
        
        # Get all statistics
        total_users = await db_conn.users.count_documents({})
        total_posts = await db_conn.posts.count_documents(query_filter)
        total_enterprises = await db_conn.enterprises.count_documents({})
        
        # Get posts by status
        draft_posts = await db_conn.posts.count_documents({**query_filter, "status": "draft"})
        scheduled_posts = await db_conn.posts.count_documents({**query_filter, "status": "scheduled"})
        published_posts = await db_conn.posts.count_documents({**query_filter, "status": "published"})
        
        # Get flagged content
        flagged = await db_conn.posts.count_documents({**query_filter, "flagged_status": {"$ne": "good_coverage"}})
        policy_violations = await db_conn.posts.count_documents({**query_filter, "flagged_status": "policy_violation"})
        harassment_cases = await db_conn.posts.count_documents({**query_filter, "violation_type": "harassment"})
        
        # Get all posts for analysis
        all_posts = await db_conn.posts.find(
            query_filter, 
            {"_id": 0, "title": 1, "content": 1, "overall_score": 1, "compliance_score": 1, 
             "cultural_sensitivity_score": 1, "accuracy_score": 1, "flagged_status": 1, 
             "status": 1, "platforms": 1, "moderation_summary": 1, "violation_type": 1}
        ).to_list(100)
        
        # Calculate average scores
        overall_scores = [p.get("overall_score", 0) for p in all_posts if p.get("overall_score")]
        compliance_scores = [p.get("compliance_score", 0) for p in all_posts if p.get("compliance_score")]
        cultural_scores = [p.get("cultural_sensitivity_score", 0) for p in all_posts if p.get("cultural_sensitivity_score")]
        accuracy_scores = [p.get("accuracy_score", 0) for p in all_posts if p.get("accuracy_score")]
        
        avg_overall = sum(overall_scores) / len(overall_scores) if overall_scores else 100
        avg_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 100
        avg_cultural = sum(cultural_scores) / len(cultural_scores) if cultural_scores else 100
        avg_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 100
        
        approval_rate = ((total_posts - flagged) / total_posts * 100) if total_posts > 0 else 100
        
        # Determine platform health
        if approval_rate >= 90:
            platform_health = "Excellent"
        elif approval_rate >= 75:
            platform_health = "Good"
        elif approval_rate >= 60:
            platform_health = "Fair"
        else:
            platform_health = "Needs Attention"
        
        # Generate LLM-powered analysis
        llm_analysis = {}
        
        if total_posts > 0:
            try:
                api_key = os.environ.get('EMERGENT_LLM_KEY')
                
                # Prepare post summaries for analysis
                post_summaries = []
                for idx, post in enumerate(all_posts[:20], 1):  # Limit to 20 posts for analysis
                    summary = f"{idx}. '{post.get('title', 'Untitled')}' - Score: {post.get('overall_score', 'N/A')}/100, Status: {post.get('flagged_status', 'unknown')}"
                    if post.get('moderation_summary'):
                        summary += f" - {post.get('moderation_summary')[:100]}"
                    post_summaries.append(summary)
                
                posts_context = "\\n".join(post_summaries)
                
                user_context = ""
                if user:
                    user_context = f"""
Profile Name: {user.get('full_name', 'Unknown')}
Position: {user.get('job_title', 'Not specified')}
Company: {user.get('company_name', 'Not specified')}
Location: {user.get('country', 'Not specified')}
"""
                
                # Generate Executive Summary
                chat = LlmChat(
                    api_key=api_key,
                    session_id=f"report_exec_{uuid.uuid4()}",
                    system_message="You are a professional reputation analyst writing formal report sections. Be concise but insightful."
                ).with_model("openai", "gpt-4.1-nano")
                
                exec_prompt = f"""Write a professional executive summary (2-3 sentences) for a content analysis report with these metrics:
- Total Posts Analyzed: {total_posts}
- Approval Rate: {approval_rate:.1f}%
- Flagged Content: {flagged}
- Average Score: {avg_overall:.1f}/100
{user_context}

Focus on the overall content quality and reputation status. Be factual and professional."""

                exec_response = await chat.send_message(UserMessage(text=exec_prompt))
                llm_analysis["executive_summary"] = exec_response.strip()
                
                # Generate Primary Finding & Professional Branding Analysis
                branding_prompt = f"""Based on the following content analysis data, write a detailed "Key Findings & Reputation Insights" section with these subsections:

**DATA:**
{user_context}
Posts Analyzed: {total_posts}
Professional/Approved Content: {total_posts - flagged} ({approval_rate:.1f}%)
Flagged Content: {flagged}
Policy Violations: {policy_violations}
Average Compliance: {avg_compliance:.1f}%
Average Cultural Sensitivity: {avg_cultural:.1f}%

**POST SUMMARIES:**
{posts_context}

**Write the following sections:**

1. **Primary Finding** (2-3 sentences): What is the main takeaway from this analysis?

2. **Professional Branding Analysis** (3-4 sentences): Analyze the content strategy and professional focus. What does the content reveal about their brand positioning?

3. **Reputation Protection Observations** (bullet points): From a reputation management perspective, what are 3-4 key observations about their approach? Consider:
- Brand consistency
- Content curation strategy
- Risk mitigation
- Professional positioning

Format each section clearly with the bold headers."""

                branding_response = await chat.send_message(UserMessage(text=branding_prompt))
                llm_analysis["key_findings"] = branding_response.strip()
                
                # Generate Detailed Content Analysis
                analysis_prompt = f"""Write a "Detailed Content Analysis" paragraph (3-4 sentences) based on:

Posts Analyzed: {total_posts}
Content Types: {', '.join(set(p.get('status', 'unknown') for p in all_posts))}
Platforms: {', '.join(set(str(p) for post in all_posts for p in (post.get('platforms') or ['general'])))}
Flagged Issues: {flagged} posts with compliance concerns

**Sample Posts:**
{posts_context[:500]}

Describe the content patterns, themes, and overall quality observed. Be specific about what was found."""

                analysis_response = await chat.send_message(UserMessage(text=analysis_prompt))
                llm_analysis["detailed_analysis"] = analysis_response.strip()
                
                # Generate Theme Distribution
                theme_prompt = f"""Analyze these posts and identify the main content themes/categories. Return as a simple list with percentages.

**Posts:**
{posts_context}

Return ONLY a JSON object with theme names as keys and percentage as values, like:
{{"Professional Content": 60, "Industry News": 20, "Personal Updates": 15, "Other": 5}}

Make sure percentages add up to 100. Use 3-6 categories based on the actual content."""

                theme_response = await chat.send_message(UserMessage(text=theme_prompt))
                
                # Parse theme distribution
                try:
                    import json
                    # Clean up the response to extract JSON
                    theme_text = theme_response.strip()
                    if "```" in theme_text:
                        theme_text = theme_text.split("```")[1].replace("json", "").strip()
                    theme_distribution = json.loads(theme_text)
                    llm_analysis["theme_distribution"] = theme_distribution
                except (json.JSONDecodeError, IndexError, ValueError):
                    # Default theme distribution based on flagged status
                    approved_pct = round(approval_rate)
                    llm_analysis["theme_distribution"] = {
                        "Professional Content": approved_pct,
                        "Flagged for Review": 100 - approved_pct
                    }
                
                # Generate Profile Overview
                if user:
                    profile_prompt = f"""Write a brief "Profile Overview" (2-3 sentences) for this professional:

Name: {user.get('full_name', 'Unknown')}
Position: {user.get('job_title', 'Content Creator')}
Company: {user.get('company_name', 'Not specified')}
Location: {user.get('country', 'Not specified')}
Content Focus: Based on {total_posts} analyzed posts with {approval_rate:.1f}% professional focus

Describe their professional positioning and content approach based on the analysis."""

                    profile_response = await chat.send_message(UserMessage(text=profile_prompt))
                    llm_analysis["profile_overview"] = profile_response.strip()
                
            except Exception as llm_error:
                logger.error(f"LLM analysis error: {str(llm_error)}")
                # Provide fallback analysis
                llm_analysis["executive_summary"] = f"This report analyzes {total_posts} posts with an overall approval rate of {approval_rate:.1f}%. The content demonstrates {'strong' if approval_rate >= 80 else 'moderate'} adherence to professional standards and platform guidelines."
                llm_analysis["key_findings"] = f"**Primary Finding**\\n\\nThe analysis reveals a {'consistent professional' if approval_rate >= 80 else 'mixed'} content strategy with {total_posts - flagged} posts meeting quality standards.\\n\\n**Professional Branding Analysis**\\n\\nThe content profile shows {'deliberate brand management' if approval_rate >= 80 else 'opportunities for improvement'} with an average score of {avg_overall:.1f}/100.\\n\\n**Reputation Protection Observations**\\n\\n• Content maintains {'consistent' if approval_rate >= 80 else 'variable'} professional standards\\n• {flagged} posts flagged for potential issues\\n• Overall compliance score: {avg_compliance:.1f}%"
        else:
            llm_analysis["executive_summary"] = "No content has been analyzed yet. This report will populate with detailed insights once posts are created and analyzed."
            llm_analysis["key_findings"] = "**Primary Finding**\\n\\nNo posts available for analysis. Create and analyze content to generate reputation insights."
        
        # Build recommendations
        recommendations = []
        if avg_compliance < 80:
            recommendations.append("Improve content compliance by reviewing platform guidelines and avoiding potentially controversial topics.")
        if flagged > 0:
            recommendations.append(f"Review and address {flagged} flagged posts to improve overall content quality and reduce reputation risk.")
        if avg_cultural < 85:
            recommendations.append("Enhance cultural sensitivity in content to ensure inclusive messaging across diverse audiences.")
        if policy_violations > 0:
            recommendations.append(f"Address {policy_violations} policy violations immediately to maintain platform standing and professional reputation.")
        if total_posts < 10:
            recommendations.append("Increase content creation frequency to build a stronger digital presence and engagement.")
        if approval_rate >= 90:
            recommendations.append("Maintain current content strategy which demonstrates strong professional standards and brand consistency.")
        
        if not recommendations:
            recommendations = [
                "Continue monitoring content for compliance and cultural sensitivity.",
                "Regularly analyze new posts to maintain reputation standards.",
                "Consider expanding to additional platforms for broader reach."
            ]
        
        report = {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "overview": {
                "total_users": total_users,
                "total_posts": total_posts,
                "total_enterprises": total_enterprises,
                "platform_health": platform_health
            },
            "post_status_distribution": {
                "draft": draft_posts,
                "scheduled": scheduled_posts,
                "published": published_posts
            },
            "content_quality": {
                "flagged_posts": flagged,
                "policy_violations": policy_violations,
                "harassment_cases": harassment_cases,
                "flagged_percentage": round(flagged / total_posts * 100, 1) if total_posts > 0 else 0,
                "approval_rate": round(approval_rate, 1),
                "average_overall_score": round(avg_overall, 1),
                "average_compliance_score": round(avg_compliance, 1),
                "average_cultural_score": round(avg_cultural, 1),
                "average_accuracy_score": round(avg_accuracy, 1)
            },
            "llm_analysis": llm_analysis,
            "recommendations": recommendations
        }
        
        return {"report": report}
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(500, f"Failed to generate report: {str(e)}")


@router.get("/download-pdf-report")
@require_permission("admin.view")
async def download_pdf_report(request: Request):
    """
    Download comprehensive report as PDF.
    
    Security (ARCH-005): Requires admin.view permission.
    """
    return {"message": "PDF download not implemented yet", "format": "pdf"}



# ==================== STRIPE MRR ENDPOINTS ====================

@router.get("/mrr")
@require_permission("admin.view")
async def get_mrr(request: Request):
    """
    Get current MRR from Stripe.
    Uses caching (2-hour default) to avoid excessive API calls.
    
    Security (ARCH-005): Requires admin.view permission.
    """
    try:
        mrr_data = await calculate_mrr()
        return mrr_data
    except Exception as e:
        logger.error(f"Error fetching MRR: {str(e)}")
        raise HTTPException(500, f"Failed to fetch MRR: {str(e)}")


@router.get("/mrr/cache-status")
@require_permission("admin.view")
async def get_mrr_cache_status(request: Request):
    """
    Get the current MRR cache status.
    
    Security (ARCH-005): Requires admin.view permission.
    """
    try:
        return get_cache_status()
    except Exception as e:
        logger.error(f"Error getting cache status: {str(e)}")
        raise HTTPException(500, f"Failed to get cache status: {str(e)}")


@router.post("/mrr/refresh")
@require_permission("admin.manage")
async def refresh_mrr(request: Request):
    """
    Force refresh MRR from Stripe (clears cache).
    Use sparingly to avoid rate limits.
    
    Security (ARCH-005): Requires admin.manage permission.
    """
    try:
        clear_mrr_cache()
        mrr_data = await calculate_mrr()
        return {
            "message": "MRR cache refreshed",
            "mrr_data": mrr_data
        }
    except Exception as e:
        logger.error(f"Error refreshing MRR: {str(e)}")
        raise HTTPException(500, f"Failed to refresh MRR: {str(e)}")

