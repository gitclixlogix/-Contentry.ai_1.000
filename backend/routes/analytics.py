"""
Analytics Routes
Handles all analytics endpoints for admin dashboard

Security Update (ARCH-005 Phase 5.1b):
- Added @require_permission decorators for RBAC enforcement
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone, timedelta
import logging
from collections import Counter
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db

# ARCH-005: Authorization decorator
from services.authorization_decorator import require_permission

router = APIRouter(prefix="/admin/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)

# Will be set by server.py
db = None

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    """Set database instance"""
    global db
    db = database


@router.get("/payments")
@require_permission("analytics.view")
async def get_payment_analytics(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get payment analytics using aggregation pipeline.
    
    Security (ARCH-005): Requires analytics.view permission.
    """
    try:
        # Use aggregation pipeline for efficient calculation
        doc_count = await db_conn.transactions.count_documents({})
        
        if doc_count == 0:
            # Return mock data
            return {
                "total_revenue": 125430.50,
                "total_transactions": 1247,
                "average_transaction": 100.58,
                "growth_rate": 12.5,
                "currency": "USD",
                "period": "all_time",
                "monthly_revenue": [
                    {"month": "Jan", "revenue": 10234},
                    {"month": "Feb", "revenue": 11450},
                    {"month": "Mar", "revenue": 12876},
                ],
                "is_mock_data": True
            }
        
        # Use aggregation for totals
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": "$amount"},
                    "total_transactions": {"$sum": 1},
                    "average_transaction": {"$avg": "$amount"}
                }
            }
        ]
        result = await db_conn.transactions.aggregate(pipeline).to_list(1)
        
        if result:
            totals = result[0]
            total_revenue = totals.get("total_revenue", 0)
            total_transactions = totals.get("total_transactions", 0)
        else:
            total_revenue = 0
            total_transactions = 0
        
        return {
            "total_revenue": round(total_revenue, 2),
            "total_transactions": total_transactions,
            "average_transaction": round(total_revenue / total_transactions, 2) if total_transactions > 0 else 0,
            "growth_rate": 0.0,  # Would need historical data to calculate real growth
            "currency": "USD"
        }
        
    except Exception as e:
        logger.error(f"Payment analytics error: {str(e)}")
        raise HTTPException(500, "Failed to get analytics")


@router.get("/card-distribution")
@require_permission("analytics.view")
async def get_card_analytics(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get card type distribution for payments.
    
    Security (ARCH-005): Requires analytics.view permission.
    """
    try:
        # Mock data for card distribution in the format expected by frontend
        card_data = {
            "total_transactions": 620,
            "total_revenue": 56636.5,
            "top_card": "visa",
            "avg_transaction_value": {
                "visa": 91.45,
                "mastercard": 91.30,
                "amex": 91.40,
                "discover": 91.39,
                "other": 90.14
            },
            "card_types": {
                "visa": {
                    "count": 280,
                    "percentage": 45.2,
                    "revenue": 25605.42,
                    "avg_value": 91.45
                },
                "mastercard": {
                    "count": 190,
                    "percentage": 30.6,
                    "revenue": 17346.89,
                    "avg_value": 91.30
                },
                "amex": {
                    "count": 95,
                    "percentage": 15.3,
                    "revenue": 8682.76,
                    "avg_value": 91.40
                },
                "discover": {
                    "count": 35,
                    "percentage": 5.6,
                    "revenue": 3198.54,
                    "avg_value": 91.39
                },
                "other": {
                    "count": 20,
                    "percentage": 3.2,
                    "revenue": 1802.89,
                    "avg_value": 90.14
                }
            },
            "is_mock_data": True
        }
        
        return card_data
        
    except Exception as e:
        logger.error(f"Card analytics error: {str(e)}")
        raise HTTPException(500, "Failed to get card analytics")


@router.get("/users-by-country")
@require_permission("analytics.view")
async def get_users_by_country(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get user distribution by country with gender breakdown for map.
    
    Security (ARCH-005): Requires analytics.view permission.
    """
    try:
        # Use aggregation pipeline for efficient country/gender grouping
        pipeline = [
            # Match only users with valid country
            {"$match": {
                "country": {"$exists": True, "$nin": [None, ""]}
            }},
            # Group by country and gender
            {"$group": {
                "_id": {"country": "$country", "gender": "$gender"},
                "count": {"$sum": 1}
            }},
            # Limit results for performance
            {"$limit": 1000}
        ]
        
        results = await db_conn.users.aggregate(pipeline).to_list(1000)
        
        # Check if we have meaningful data
        if not results or len(results) < 3:
            # Return mock data with gender breakdown for map
            countries_list = ["United States", "United Kingdom", "Canada", "Germany", "France", "Australia", "India", "Japan", "Brazil", "Spain"]
            user_counts_list = [450, 320, 180, 150, 90, 100, 80, 60, 70, 50]
            
            # Generate gender breakdown for each country (roughly 52% male, 45% female, 3% other)
            country_details = {}
            for i, country in enumerate(countries_list):
                total = user_counts_list[i]
                male = int(total * 0.52)
                female = int(total * 0.45)
                other = total - male - female
                country_details[country] = {
                    "total": total,
                    "male": male,
                    "female": female,
                    "other": other,
                    "count": total,
                    "percentage": round(total / sum(user_counts_list) * 100, 1)
                }
            
            return {
                "countries": countries_list,
                "user_counts": user_counts_list,
                "country_details": country_details,
                "total_users": sum(user_counts_list),
                "total_countries": len(countries_list),
                "is_mock_data": True
            }
        
        # Process aggregation results into country_data
        country_data = {}
        for item in results:
            country = item["_id"]["country"]
            gender = item["_id"].get("gender", "other") or "other"
            count = item["count"]
            
            if country not in country_data:
                country_data[country] = {"total": 0, "male": 0, "female": 0, "other": 0}
            
            country_data[country]["total"] += count
            if gender.lower() in ["male", "m"]:
                country_data[country]["male"] += count
            elif gender.lower() in ["female", "f"]:
                country_data[country]["female"] += count
            else:
                country_data[country]["other"] += count
        
        total = sum(d["total"] for d in country_data.values())
        
        # Sort by count and take top 10
        sorted_countries = sorted(country_data.items(), key=lambda x: x[1]["total"], reverse=True)[:10]
        
        countries_list = []
        user_counts_list = []
        country_details = {}
        
        for country, data in sorted_countries:
            countries_list.append(country)
            user_counts_list.append(data["total"])
            country_details[country] = {
                "total": data["total"],
                "male": data["male"],
                "female": data["female"],
                "other": data["other"],
                "count": data["total"],
                "percentage": round(data["total"] / total * 100, 1) if total > 0 else 0
            }
        
        return {
            "countries": countries_list,
            "user_counts": user_counts_list,
            "country_details": country_details,
            "total_users": total,
            "total_countries": len(country_data)
        }
        
    except Exception as e:
        logger.error(f"Country analytics error: {str(e)}")
        raise HTTPException(500, "Failed to get country analytics")


@router.get("/subscriptions")
@require_permission("analytics.view")
async def get_subscription_analytics(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get subscription analytics.
    
    Security (ARCH-005): Requires analytics.view permission.
    """
    try:
        # Get users by subscription status
        active = await db_conn.users.count_documents({"subscription_status": "active"})
        inactive = await db_conn.users.count_documents({"subscription_status": {"$ne": "active"}})
        
        # Mock data for subscription plans
        plan_data = [
            {"name": "Basic", "count": 450, "mrr": 4500},
            {"name": "Pro", "count": 280, "mrr": 8400},
            {"name": "Enterprise", "count": 85, "mrr": 8500}
        ]
        
        return {
            "total_subscribers": active,
            "active_subscriptions": active,
            "inactive_subscriptions": inactive,
            "plans": [p["name"] for p in plan_data],
            "user_counts": [p["count"] for p in plan_data],
            "plan_details": plan_data,
            "total_mrr": 21400,
            "churn_rate": 2.3,
            "is_partial_mock": True,
            "is_mock_data": True
        }
        
    except Exception as e:
        logger.error(f"Subscription analytics error: {str(e)}")
        raise HTTPException(500, "Failed to get subscription analytics")


@router.get("/user-table")
@require_permission("analytics.view")
async def get_user_table_data(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get detailed user table data.
    
    Security (ARCH-005): Requires analytics.view permission.
    """
    try:
        users = await db_conn.users.find(
            {},
            {"_id": 0, "id": 1, "full_name": 1, "email": 1, "created_at": 1, "subscription_status": 1, "enterprise_id": 1}
        ).sort("created_at", -1).limit(100).to_list(100)
        
        # Get post counts for each user
        for user in users:
            user["post_count"] = await db_conn.posts.count_documents({"user_id": user["id"]})
        
        return {"users": users, "total": len(users)}
        
    except Exception as e:
        logger.error(f"User table error: {str(e)}")
        raise HTTPException(500, "Failed to get user table data")


@router.get("/user-demographics")
@require_permission("analytics.view")
async def get_user_demographics(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get user demographic analytics.
    
    Security (ARCH-005): Requires analytics.view permission.
    """
    try:
        # Mock demographic data
        return {
            "age_groups": [
                {"range": "18-24", "count": 234, "percentage": 12.5},
                {"range": "25-34", "count": 678, "percentage": 36.2},
                {"range": "35-44", "count": 542, "percentage": 28.9},
                {"range": "45-54", "count": 298, "percentage": 15.9},
                {"range": "55+", "count": 121, "percentage": 6.5}
            ],
            "gender_distribution": [
                {"gender": "Male", "count": 987, "percentage": 52.7},
                {"gender": "Female", "count": 856, "percentage": 45.7},
                {"gender": "Other/Undisclosed", "count": 30, "percentage": 1.6}
            ],
            "total_users": 1873,
            "is_mock_data": True
        }
        
    except Exception as e:
        logger.error(f"Demographics error: {str(e)}")
        raise HTTPException(500, "Failed to get demographics")


@router.get("/posting-patterns")
@require_permission("analytics.view")
async def get_posting_patterns(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get posting pattern analytics.
    
    Security (ARCH-005): Requires analytics.view permission.
    """
    try:
        # Get all posts
        posts = await db_conn.posts.find({}, {"_id": 0, "created_at": 1, "post_time": 1}).to_list(10000)
        
        if not posts:
            # Return mock data
            return {
                "hourly_distribution": [
                    {"hour": i, "count": 30 + (i * 5) % 50} for i in range(24)
                ],
                "daily_distribution": [
                    {"day": "Monday", "count": 145},
                    {"day": "Tuesday", "count": 167},
                    {"day": "Wednesday", "count": 189},
                    {"day": "Thursday", "count": 178},
                    {"day": "Friday", "count": 156},
                    {"day": "Saturday", "count": 98},
                    {"day": "Sunday", "count": 87}
                ],
                "is_mock_data": True
            }
        
        # Calculate real posting patterns - handle both datetime objects and ISO strings
        from datetime import datetime as dt
        hours = []
        for p in posts:
            if p.get("created_at"):
                created_at = p["created_at"]
                # Convert string to datetime if needed
                if isinstance(created_at, str):
                    try:
                        created_at = dt.fromisoformat(created_at.replace('Z', '+00:00'))
                    except (ValueError, TypeError) as e:
                        logging.debug(f"Skipping post with invalid date: {e}")
                        continue
                hours.append(created_at.hour)
        
        hour_counts = Counter(hours)
        
        return {
            "hourly_distribution": [
                {"hour": hour, "count": hour_counts.get(hour, 0)} for hour in range(24)
            ],
            "is_mock_data": len(hours) == 0
        }
        
    except Exception as e:
        logger.error(f"Posting patterns error: {str(e)}")
        raise HTTPException(500, "Failed to get posting patterns")


@router.get("/content-quality")
@require_permission("analytics.view")
async def get_content_quality_analytics(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get content quality analytics.
    
    Security (ARCH-005): Requires analytics.view permission.
    """
    try:
        # Get all posts with scores
        posts = await db_conn.posts.find({}, {"_id": 0, "overall_score": 1, "compliance_score": 1, "cultural_sensitivity_score": 1, "flagged_status": 1}).to_list(10000)
        
        if not posts:
            return {
                "average_scores": {
                    "overall": 78.5,
                    "compliance": 82.3,
                    "cultural_sensitivity": 75.8
                },
                "score_distribution": {
                    "90-100": 234,
                    "80-89": 456,
                    "70-79": 342,
                    "60-69": 123,
                    "below-60": 45
                },
                "is_mock_data": True
            }
        
        # Calculate averages
        overall_scores = [p.get("overall_score", 0) for p in posts if p.get("overall_score")]
        compliance_scores = [p.get("compliance_score", 0) for p in posts if p.get("compliance_score")]
        cultural_scores = [p.get("cultural_sensitivity_score", 0) for p in posts if p.get("cultural_sensitivity_score")]
        
        avg_overall = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        avg_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0
        avg_cultural = sum(cultural_scores) / len(cultural_scores) if cultural_scores else 0
        
        # Count by score ranges
        score_dist = {
            "90-100": len([s for s in overall_scores if s >= 90]),
            "80-89": len([s for s in overall_scores if 80 <= s < 90]),
            "70-79": len([s for s in overall_scores if 70 <= s < 80]),
            "60-69": len([s for s in overall_scores if 60 <= s < 70]),
            "below-60": len([s for s in overall_scores if s < 60])
        }
        
        return {
            "average_scores": {
                "overall": round(avg_overall, 1),
                "compliance": round(avg_compliance, 1),
                "cultural_sensitivity": round(avg_cultural, 1)
            },
            "score_distribution": score_dist,
            "total_analyzed": len(posts)
        }
        
    except Exception as e:
        logger.error(f"Content quality error: {str(e)}")
        raise HTTPException(500, "Failed to get content quality")


@router.get("/cost-metrics")
@require_permission("analytics.view")
async def get_cost_metrics(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get cost and usage metrics.
    
    Security (ARCH-005): Requires analytics.view permission.
    """
    try:
        # Get all posts
        total_posts = await db_conn.posts.count_documents({})
        
        # Mock cost data
        return {
            "total_api_calls": total_posts,
            "estimated_costs": {
                "llm_calls": round(total_posts * 0.002, 2),
                "storage": 45.67,
                "bandwidth": 23.45,
                "total": round(total_posts * 0.002 + 45.67 + 23.45, 2)
            },
            "cost_per_user": 2.34,
            "is_partial_mock": True
        }
        
    except Exception as e:
        logger.error(f"Cost metrics error: {str(e)}")
        raise HTTPException(500, "Failed to get cost metrics")


@router.get("/language-distribution")
@require_permission("analytics.view")
async def get_language_distribution(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get language usage distribution.
    
    Security (ARCH-005): Requires analytics.view permission.
    """
    try:
        # Mock language data
        languages = {
            "English": 1456,
            "Spanish": 342,
            "French": 234,
            "German": 189,
            "Chinese": 156,
            "Japanese": 98,
            "Portuguese": 87,
            "Arabic": 65,
            "Russian": 54,
            "Hindi": 43
        }
        
        total = sum(languages.values())
        
        return {
            "languages": [
                {"language": lang, "count": count, "percentage": round(count / total * 100, 1)}
                for lang, count in languages.items()
            ],
            "total_languages": len(languages),
            "dominant_language": "English",
            "is_mock_data": True
        }
        
    except Exception as e:
        logger.error(f"Language distribution error: {str(e)}")
        raise HTTPException(500, "Failed to get language distribution")
