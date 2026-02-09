"""
Token Management Routes for Super Admin

Provides API endpoints for token usage monitoring, alerts, and analytics.
Only accessible to users with super_admin role.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from services.database import get_db
from services.token_tracking_service import get_token_tracker, TokenTrackingService
from services.token_alert_service import get_token_alert_service, TokenAlertService, AlertSeverity
from routes.superadmin import verify_super_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/superadmin/tokens", tags=["Super Admin - Token Management"])


# ============================================
# Pydantic Models
# ============================================

class AlertConfigUpdate(BaseModel):
    """Model for updating alert configuration"""
    enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    email_recipient: Optional[str] = None
    thresholds: Optional[dict] = None
    anomaly_detection: Optional[dict] = None
    notification_cooldown_minutes: Optional[int] = None


class AlertAcknowledge(BaseModel):
    """Model for acknowledging an alert"""
    alert_id: str


# ============================================
# Real-Time Stats & Overview
# ============================================

@router.get("/realtime")
async def get_realtime_stats(
    user_id: str = Depends(verify_super_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get real-time token usage statistics.
    Shows today's usage, last hour, and current rate.
    """
    try:
        tracker = get_token_tracker()
        tracker.set_db(db)
        
        stats = await tracker.get_real_time_stats()
        
        # Add cost comparison
        alert_service = get_token_alert_service(db)
        projection = await alert_service.get_cost_projection()
        
        return {
            "success": True,
            "data": {
                **stats,
                "projection": projection
            }
        }
    except Exception as e:
        logger.error(f"Error fetching realtime stats: {e}")
        raise HTTPException(500, f"Failed to fetch realtime stats: {str(e)}")


@router.get("/usage/summary")
async def get_usage_summary(
    user_id: str = Depends(verify_super_admin),
    db: AsyncIOMotorDatabase = Depends(get_db),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    group_by: str = Query("daily", description="Grouping: hourly, daily, weekly, monthly")
):
    """
    Get token usage summary with trend data.
    """
    try:
        tracker = get_token_tracker()
        tracker.set_db(db)
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        summary = await tracker.get_usage_summary(
            start_date=start_date,
            group_by=group_by
        )
        
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        logger.error(f"Error fetching usage summary: {e}")
        raise HTTPException(500, f"Failed to fetch usage summary: {str(e)}")


# ============================================
# Breakdown by Agent & Model
# ============================================

@router.get("/usage/by-agent")
async def get_usage_by_agent(
    user_id: str = Depends(verify_super_admin),
    db: AsyncIOMotorDatabase = Depends(get_db),
    days: int = Query(30, ge=1, le=365)
):
    """
    Get token usage breakdown by AI agent type.
    """
    try:
        tracker = get_token_tracker()
        tracker.set_db(db)
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        breakdown = await tracker.get_usage_by_agent(start_date=start_date)
        
        return {
            "success": True,
            "data": breakdown
        }
    except Exception as e:
        logger.error(f"Error fetching agent breakdown: {e}")
        raise HTTPException(500, f"Failed to fetch agent breakdown: {str(e)}")


@router.get("/usage/by-model")
async def get_usage_by_model(
    user_id: str = Depends(verify_super_admin),
    db: AsyncIOMotorDatabase = Depends(get_db),
    days: int = Query(30, ge=1, le=365)
):
    """
    Get token usage breakdown by AI model.
    Shows both API cost and credit cost for comparison.
    """
    try:
        tracker = get_token_tracker()
        tracker.set_db(db)
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        breakdown = await tracker.get_usage_by_model(start_date=start_date)
        
        return {
            "success": True,
            "data": breakdown
        }
    except Exception as e:
        logger.error(f"Error fetching model breakdown: {e}")
        raise HTTPException(500, f"Failed to fetch model breakdown: {str(e)}")


@router.get("/usage/top-users")
async def get_top_users_by_tokens(
    user_id: str = Depends(verify_super_admin),
    db: AsyncIOMotorDatabase = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get top users by token consumption.
    """
    try:
        tracker = get_token_tracker()
        tracker.set_db(db)
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        top_users = await tracker.get_top_users_by_tokens(
            limit=limit,
            start_date=start_date
        )
        
        return {
            "success": True,
            "data": top_users
        }
    except Exception as e:
        logger.error(f"Error fetching top users: {e}")
        raise HTTPException(500, f"Failed to fetch top users: {str(e)}")


# ============================================
# Alerts Management
# ============================================

@router.get("/alerts")
async def get_alerts(
    user_id: str = Depends(verify_super_admin),
    db: AsyncIOMotorDatabase = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    include_acknowledged: bool = Query(False),
    severity: Optional[str] = Query(None, description="Filter by severity: info, warning, critical")
):
    """
    Get token usage alerts.
    """
    try:
        alert_service = get_token_alert_service(db)
        
        sev = AlertSeverity(severity) if severity else None
        alerts = await alert_service.get_alerts(
            limit=limit,
            include_acknowledged=include_acknowledged,
            severity=sev
        )
        
        return {
            "success": True,
            "data": alerts,
            "count": len(alerts)
        }
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(500, f"Failed to fetch alerts: {str(e)}")


@router.post("/alerts/acknowledge")
async def acknowledge_alert(
    data: AlertAcknowledge,
    user_id: str = Depends(verify_super_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Acknowledge an alert.
    """
    try:
        alert_service = get_token_alert_service(db)
        success = await alert_service.acknowledge_alert(data.alert_id, user_id)
        
        if not success:
            raise HTTPException(404, "Alert not found")
        
        return {
            "success": True,
            "message": "Alert acknowledged"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(500, f"Failed to acknowledge alert: {str(e)}")


@router.post("/alerts/check")
async def trigger_alert_check(
    user_id: str = Depends(verify_super_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Manually trigger alert check (for testing).
    """
    try:
        alert_service = get_token_alert_service(db)
        alerts = await alert_service.check_and_create_alerts()
        
        return {
            "success": True,
            "alerts_created": len(alerts),
            "alerts": alerts
        }
    except Exception as e:
        logger.error(f"Error checking alerts: {e}")
        raise HTTPException(500, f"Failed to check alerts: {str(e)}")


# ============================================
# Alert Configuration
# ============================================

@router.get("/alerts/config")
async def get_alert_config(
    user_id: str = Depends(verify_super_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get current alert configuration.
    """
    try:
        alert_service = get_token_alert_service(db)
        config = await alert_service.get_alert_config()
        
        return {
            "success": True,
            "data": config
        }
    except Exception as e:
        logger.error(f"Error fetching alert config: {e}")
        raise HTTPException(500, f"Failed to fetch alert config: {str(e)}")


@router.put("/alerts/config")
async def update_alert_config(
    updates: AlertConfigUpdate,
    user_id: str = Depends(verify_super_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Update alert configuration.
    """
    try:
        alert_service = get_token_alert_service(db)
        
        # Convert to dict and remove None values
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
        
        config = await alert_service.update_alert_config(update_data)
        
        return {
            "success": True,
            "data": config
        }
    except Exception as e:
        logger.error(f"Error updating alert config: {e}")
        raise HTTPException(500, f"Failed to update alert config: {str(e)}")


# ============================================
# Cost Analysis & Comparison
# ============================================

@router.get("/cost/comparison")
async def get_cost_comparison(
    user_id: str = Depends(verify_super_admin),
    db: AsyncIOMotorDatabase = Depends(get_db),
    days: int = Query(30, ge=1, le=365)
):
    """
    Get cost comparison between API costs and credit system revenue.
    Shows profit/loss margin for each model and agent type.
    """
    try:
        tracker = get_token_tracker()
        tracker.set_db(db)
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get breakdown by model
        model_breakdown = await tracker.get_usage_by_model(start_date=start_date)
        agent_breakdown = await tracker.get_usage_by_agent(start_date=start_date)
        
        # Calculate totals and margins
        total_api_cost = sum(m.get("api_cost_usd", 0) for m in model_breakdown)
        total_credit_cost = sum(a.get("credit_cost", 0) for a in agent_breakdown)
        
        # Assuming $0.04 per credit as revenue
        revenue_per_credit = 0.04
        total_credit_revenue = total_credit_cost * revenue_per_credit
        
        margin = total_credit_revenue - total_api_cost
        margin_percent = (margin / total_api_cost * 100) if total_api_cost > 0 else 0
        
        return {
            "success": True,
            "data": {
                "period_days": days,
                "totals": {
                    "api_cost_usd": round(total_api_cost, 2),
                    "credit_cost": total_credit_cost,
                    "credit_revenue_usd": round(total_credit_revenue, 2),
                    "margin_usd": round(margin, 2),
                    "margin_percent": round(margin_percent, 1)
                },
                "by_model": model_breakdown,
                "by_agent": agent_breakdown
            }
        }
    except Exception as e:
        logger.error(f"Error fetching cost comparison: {e}")
        raise HTTPException(500, f"Failed to fetch cost comparison: {str(e)}")


@router.get("/cost/projection")
async def get_cost_projection(
    user_id: str = Depends(verify_super_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get monthly cost projection based on current usage patterns.
    """
    try:
        alert_service = get_token_alert_service(db)
        projection = await alert_service.get_cost_projection()
        
        return {
            "success": True,
            "data": projection
        }
    except Exception as e:
        logger.error(f"Error fetching projection: {e}")
        raise HTTPException(500, f"Failed to fetch projection: {str(e)}")


# ============================================
# Optimization Recommendations
# ============================================

@router.get("/recommendations")
async def get_optimization_recommendations(
    user_id: str = Depends(verify_super_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get AI-powered optimization recommendations based on usage patterns.
    """
    try:
        tracker = get_token_tracker()
        tracker.set_db(db)
        
        # Get usage data
        model_breakdown = await tracker.get_usage_by_model()
        agent_breakdown = await tracker.get_usage_by_agent()
        
        recommendations = []
        
        # Check for expensive model usage
        for model in model_breakdown:
            if model["model"] == "gpt-4o" and model["request_count"] > 100:
                recommendations.append({
                    "type": "cost_optimization",
                    "priority": "high",
                    "title": "High GPT-4o Usage Detected",
                    "description": f"GPT-4o is being used for {model['request_count']} requests. Consider using gpt-4.1-mini for simpler tasks to reduce costs by up to 90%.",
                    "potential_savings_usd": round(model["api_cost_usd"] * 0.8, 2),
                    "affected_model": "gpt-4o"
                })
        
        # Check for inefficient patterns
        for agent in agent_breakdown:
            avg_tokens = agent.get("avg_tokens_per_request", 0)
            if avg_tokens > 3000:
                recommendations.append({
                    "type": "efficiency",
                    "priority": "medium",
                    "title": f"High Token Usage in {agent['agent_type'].replace('_', ' ').title()}",
                    "description": f"Average {avg_tokens:.0f} tokens per request. Consider optimizing prompts or implementing caching.",
                    "affected_agent": agent["agent_type"]
                })
        
        # Check for high-cost users (potential abuse)
        top_users = await tracker.get_top_users_by_tokens(limit=5)
        total_tokens = sum(u["total_tokens"] for u in top_users)
        if top_users and top_users[0]["total_tokens"] > total_tokens * 0.5:
            recommendations.append({
                "type": "usage_concentration",
                "priority": "medium",
                "title": "Usage Concentration Warning",
                "description": f"User '{top_users[0]['email']}' accounts for >50% of token usage. Consider implementing rate limits.",
                "user_email": top_users[0]["email"]
            })
        
        # Default recommendation if none found
        if not recommendations:
            recommendations.append({
                "type": "general",
                "priority": "low",
                "title": "No Immediate Optimizations Found",
                "description": "Token usage patterns appear healthy. Continue monitoring for changes."
            })
        
        return {
            "success": True,
            "data": recommendations
        }
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(500, f"Failed to generate recommendations: {str(e)}")
