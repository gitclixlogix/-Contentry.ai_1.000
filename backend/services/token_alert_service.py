"""
Token Alert Service for Contentry.ai

Manages alerts and notifications for token usage thresholds and anomalies.
Super Admin only feature.
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    """Types of token alerts"""
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    DAILY_LIMIT = "daily_limit"
    ANOMALY_DETECTED = "anomaly_detected"
    BUDGET_WARNING = "budget_warning"
    BUDGET_CRITICAL = "budget_critical"
    HIGH_COST_MODEL = "high_cost_model"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class TokenAlertService:
    """
    Service for managing token usage alerts.
    """
    
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db
        self.email_recipient = "contact@contentry.ai"
    
    def set_db(self, db: AsyncIOMotorDatabase):
        """Set database connection"""
        self.db = db
    
    async def get_alert_config(self) -> Dict[str, Any]:
        """Get current alert configuration"""
        if self.db is None:
            return self._default_config()
        
        config = await self.db.token_alert_config.find_one({"_id": "default"})
        if not config:
            config = self._default_config()
            await self.db.token_alert_config.insert_one({**config, "_id": "default"})
        
        # Remove MongoDB _id
        config.pop("_id", None)
        return config
    
    def _default_config(self) -> Dict[str, Any]:
        """Default alert configuration"""
        return {
            "enabled": True,
            "email_notifications": True,
            "email_recipient": self.email_recipient,
            "thresholds": {
                "daily_tokens": 100000,       # Alert if >100K tokens/day
                "daily_cost_usd": 10.00,      # Alert if >$10/day
                "hourly_tokens": 20000,       # Alert if >20K tokens/hour
                "monthly_budget_usd": 500.00, # Monthly budget
                "warning_percent": 80,        # Warning at 80% of budget
                "critical_percent": 95,       # Critical at 95% of budget
            },
            "anomaly_detection": {
                "enabled": True,
                "std_deviation_threshold": 2.5,  # Alert if >2.5 std dev from mean
                "min_data_points": 7,            # Need 7 days of data for anomaly detection
            },
            "notification_cooldown_minutes": 60,  # Don't spam - 1 alert per hour per type
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
    
    async def update_alert_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update alert configuration"""
        if self.db is None:
            return {"error": "Database not connected"}
        
        updates["updated_at"] = datetime.now(timezone.utc)
        
        await self.db.token_alert_config.update_one(
            {"_id": "default"},
            {"$set": updates},
            upsert=True
        )
        
        return await self.get_alert_config()
    
    async def check_and_create_alerts(self) -> List[Dict[str, Any]]:
        """
        Check all alert conditions and create alerts if needed.
        Called periodically by scheduler.
        """
        if self.db is None:
            return []
        
        config = await self.get_alert_config()
        if not config.get("enabled"):
            return []
        
        alerts = []
        now = datetime.now(timezone.utc)
        
        # Check daily token threshold
        daily_alert = await self._check_daily_threshold(config)
        if daily_alert:
            alerts.append(daily_alert)
        
        # Check hourly threshold
        hourly_alert = await self._check_hourly_threshold(config)
        if hourly_alert:
            alerts.append(hourly_alert)
        
        # Check monthly budget
        budget_alert = await self._check_budget(config)
        if budget_alert:
            alerts.append(budget_alert)
        
        # Check for anomalies
        if config.get("anomaly_detection", {}).get("enabled"):
            anomaly_alert = await self._check_anomaly(config)
            if anomaly_alert:
                alerts.append(anomaly_alert)
        
        # Send email notifications for new alerts
        if config.get("email_notifications") and alerts:
            await self._send_alert_emails(alerts, config)
        
        return alerts
    
    async def _check_daily_threshold(self, config: Dict) -> Optional[Dict]:
        """Check if daily token usage exceeds threshold"""
        thresholds = config.get("thresholds", {})
        daily_limit = thresholds.get("daily_tokens", 100000)
        
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        pipeline = [
            {"$match": {"timestamp": {"$gte": today_start}}},
            {"$group": {"_id": None, "total_tokens": {"$sum": "$total_tokens"}, "api_cost": {"$sum": "$api_cost_usd"}}}
        ]
        
        result = await self.db.token_usage_logs.aggregate(pipeline).to_list(1)
        
        if result and result[0]["total_tokens"] > daily_limit:
            # Check cooldown
            if await self._should_send_alert(AlertType.DAILY_LIMIT):
                alert = await self._create_alert(
                    alert_type=AlertType.DAILY_LIMIT,
                    severity=AlertSeverity.WARNING,
                    title="Daily Token Limit Exceeded",
                    message=f"Daily token usage ({result[0]['total_tokens']:,}) exceeded threshold ({daily_limit:,})",
                    data={
                        "current_tokens": result[0]["total_tokens"],
                        "threshold": daily_limit,
                        "current_cost_usd": round(result[0]["api_cost"], 4)
                    }
                )
                return alert
        
        return None
    
    async def _check_hourly_threshold(self, config: Dict) -> Optional[Dict]:
        """Check if hourly token usage exceeds threshold"""
        thresholds = config.get("thresholds", {})
        hourly_limit = thresholds.get("hourly_tokens", 20000)
        
        hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        
        pipeline = [
            {"$match": {"timestamp": {"$gte": hour_ago}}},
            {"$group": {"_id": None, "total_tokens": {"$sum": "$total_tokens"}}}
        ]
        
        result = await self.db.token_usage_logs.aggregate(pipeline).to_list(1)
        
        if result and result[0]["total_tokens"] > hourly_limit:
            if await self._should_send_alert(AlertType.THRESHOLD_EXCEEDED):
                alert = await self._create_alert(
                    alert_type=AlertType.THRESHOLD_EXCEEDED,
                    severity=AlertSeverity.WARNING,
                    title="Hourly Token Spike Detected",
                    message=f"Hourly token usage ({result[0]['total_tokens']:,}) exceeded threshold ({hourly_limit:,})",
                    data={
                        "current_tokens": result[0]["total_tokens"],
                        "threshold": hourly_limit
                    }
                )
                return alert
        
        return None
    
    async def _check_budget(self, config: Dict) -> Optional[Dict]:
        """Check monthly budget usage"""
        thresholds = config.get("thresholds", {})
        monthly_budget = thresholds.get("monthly_budget_usd", 500.00)
        warning_percent = thresholds.get("warning_percent", 80)
        critical_percent = thresholds.get("critical_percent", 95)
        
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        pipeline = [
            {"$match": {"timestamp": {"$gte": month_start}}},
            {"$group": {"_id": None, "total_cost": {"$sum": "$api_cost_usd"}}}
        ]
        
        result = await self.db.token_usage_logs.aggregate(pipeline).to_list(1)
        
        if result:
            current_cost = result[0]["total_cost"]
            percent_used = (current_cost / monthly_budget) * 100
            
            if percent_used >= critical_percent:
                if await self._should_send_alert(AlertType.BUDGET_CRITICAL):
                    return await self._create_alert(
                        alert_type=AlertType.BUDGET_CRITICAL,
                        severity=AlertSeverity.CRITICAL,
                        title="CRITICAL: Monthly Budget Nearly Exhausted",
                        message=f"Monthly AI cost (${current_cost:.2f}) has reached {percent_used:.1f}% of budget (${monthly_budget:.2f})",
                        data={
                            "current_cost_usd": round(current_cost, 2),
                            "budget_usd": monthly_budget,
                            "percent_used": round(percent_used, 1)
                        }
                    )
            elif percent_used >= warning_percent:
                if await self._should_send_alert(AlertType.BUDGET_WARNING):
                    return await self._create_alert(
                        alert_type=AlertType.BUDGET_WARNING,
                        severity=AlertSeverity.WARNING,
                        title="Monthly Budget Warning",
                        message=f"Monthly AI cost (${current_cost:.2f}) has reached {percent_used:.1f}% of budget (${monthly_budget:.2f})",
                        data={
                            "current_cost_usd": round(current_cost, 2),
                            "budget_usd": monthly_budget,
                            "percent_used": round(percent_used, 1)
                        }
                    )
        
        return None
    
    async def _check_anomaly(self, config: Dict) -> Optional[Dict]:
        """Detect usage anomalies using statistical analysis"""
        anomaly_config = config.get("anomaly_detection", {})
        std_threshold = anomaly_config.get("std_deviation_threshold", 2.5)
        min_points = anomaly_config.get("min_data_points", 7)
        
        # Get daily totals for past 30 days
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        pipeline = [
            {"$match": {"period_type": "daily", "updated_at": {"$gte": thirty_days_ago}}},
            {"$group": {
                "_id": "$period",
                "total_tokens": {"$sum": "$total_tokens"}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        results = await self.db.token_usage_aggregates.aggregate(pipeline).to_list(None)
        
        if len(results) < min_points:
            return None
        
        # Calculate statistics
        daily_tokens = [r["total_tokens"] for r in results[:-1]]  # Exclude today
        today_tokens = results[-1]["total_tokens"] if results else 0
        
        if not daily_tokens:
            return None
        
        mean = statistics.mean(daily_tokens)
        std_dev = statistics.stdev(daily_tokens) if len(daily_tokens) > 1 else 0
        
        if std_dev > 0:
            z_score = (today_tokens - mean) / std_dev
            
            if abs(z_score) > std_threshold:
                if await self._should_send_alert(AlertType.ANOMALY_DETECTED):
                    direction = "higher" if z_score > 0 else "lower"
                    return await self._create_alert(
                        alert_type=AlertType.ANOMALY_DETECTED,
                        severity=AlertSeverity.WARNING if abs(z_score) < 3 else AlertSeverity.CRITICAL,
                        title="Token Usage Anomaly Detected",
                        message=f"Today's token usage ({today_tokens:,}) is {abs(z_score):.1f} standard deviations {direction} than average ({mean:,.0f})",
                        data={
                            "current_tokens": today_tokens,
                            "mean": round(mean, 0),
                            "std_deviation": round(std_dev, 0),
                            "z_score": round(z_score, 2)
                        }
                    )
        
        return None
    
    async def _should_send_alert(self, alert_type: AlertType) -> bool:
        """Check if we should send an alert (cooldown check)"""
        if self.db is None:
            return False
        
        config = await self.get_alert_config()
        cooldown_minutes = config.get("notification_cooldown_minutes", 60)
        cooldown_time = datetime.now(timezone.utc) - timedelta(minutes=cooldown_minutes)
        
        # Check for recent alert of same type
        recent = await self.db.token_alerts.find_one({
            "alert_type": alert_type,
            "created_at": {"$gte": cooldown_time}
        })
        
        return recent is None
    
    async def _create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create and store an alert"""
        import uuid
        
        alert = {
            "id": str(uuid.uuid4()),
            "alert_type": alert_type.value,
            "severity": severity.value,
            "title": title,
            "message": message,
            "data": data,
            "acknowledged": False,
            "acknowledged_by": None,
            "acknowledged_at": None,
            "created_at": datetime.now(timezone.utc),
        }
        
        if self.db is not None:
            await self.db.token_alerts.insert_one(alert)
        
        logger.warning(f"[TokenAlert] {severity.value.upper()}: {title}")
        
        # Remove _id for response
        alert.pop("_id", None)
        return alert
    
    async def _send_alert_emails(self, alerts: List[Dict], config: Dict):
        """Send email notifications for alerts"""
        from email_service import send_email
        
        recipient = config.get("email_recipient", self.email_recipient)
        
        for alert in alerts:
            try:
                subject = f"[Contentry.ai] {alert['severity'].upper()}: {alert['title']}"
                
                html_content = f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: {'#dc2626' if alert['severity'] == 'critical' else '#f59e0b'}; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                        <h1 style="margin: 0; font-size: 24px;">⚠️ Token Usage Alert</h1>
                    </div>
                    <div style="background: #f3f4f6; padding: 20px; border-radius: 0 0 8px 8px;">
                        <h2 style="color: #1f2937; margin-top: 0;">{alert['title']}</h2>
                        <p style="color: #4b5563; font-size: 16px;">{alert['message']}</p>
                        
                        <div style="background: white; padding: 15px; border-radius: 6px; margin-top: 15px;">
                            <h3 style="margin: 0 0 10px 0; color: #374151;">Details</h3>
                            <table style="width: 100%; border-collapse: collapse;">
                                {''.join(f'<tr><td style="padding: 5px 0; color: #6b7280;">{k.replace("_", " ").title()}</td><td style="padding: 5px 0; color: #1f2937; font-weight: 600; text-align: right;">{v}</td></tr>' for k, v in alert['data'].items())}
                            </table>
                        </div>
                        
                        <p style="color: #6b7280; font-size: 12px; margin-top: 20px;">
                            This is an automated alert from Contentry.ai Token Management System.<br>
                            Time: {alert['created_at'].strftime('%Y-%m-%d %H:%M:%S UTC')}
                        </p>
                        
                        <a href="https://contentry.ai/superadmin/token-management" 
                           style="display: inline-block; background: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; margin-top: 15px;">
                            View Dashboard
                        </a>
                    </div>
                </body>
                </html>
                """
                
                await send_email(
                    to_email=recipient,
                    subject=subject,
                    html_content=html_content
                )
                
                logger.info(f"[TokenAlert] Email sent to {recipient}: {alert['title']}")
                
            except Exception as e:
                logger.error(f"[TokenAlert] Failed to send email: {e}")
    
    async def get_alerts(
        self,
        limit: int = 50,
        include_acknowledged: bool = False,
        severity: Optional[AlertSeverity] = None
    ) -> List[Dict[str, Any]]:
        """Get alerts for dashboard"""
        if self.db is None:
            return []
        
        query = {}
        if not include_acknowledged:
            query["acknowledged"] = False
        if severity:
            query["severity"] = severity.value
        
        alerts = await self.db.token_alerts.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(None)
        
        return alerts
    
    async def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Acknowledge an alert"""
        if self.db is None:
            return False
        
        result = await self.db.token_alerts.update_one(
            {"id": alert_id},
            {"$set": {
                "acknowledged": True,
                "acknowledged_by": user_id,
                "acknowledged_at": datetime.now(timezone.utc)
            }}
        )
        
        return result.modified_count > 0
    
    async def get_cost_projection(self) -> Dict[str, Any]:
        """Project monthly costs based on current usage patterns"""
        if self.db is None:
            return {}
        
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        days_elapsed = (now - month_start).days + 1
        days_in_month = 30  # Approximate
        
        # Get current month's cost
        pipeline = [
            {"$match": {"timestamp": {"$gte": month_start}}},
            {"$group": {
                "_id": None,
                "total_cost": {"$sum": "$api_cost_usd"},
                "total_tokens": {"$sum": "$total_tokens"},
                "request_count": {"$sum": 1}
            }}
        ]
        
        result = await self.db.token_usage_logs.aggregate(pipeline).to_list(1)
        
        if not result:
            return {
                "current_cost_usd": 0,
                "projected_cost_usd": 0,
                "days_elapsed": days_elapsed,
                "days_remaining": days_in_month - days_elapsed,
                "daily_avg_cost_usd": 0
            }
        
        current_cost = result[0]["total_cost"]
        daily_avg = current_cost / days_elapsed
        projected = daily_avg * days_in_month
        
        return {
            "current_cost_usd": round(current_cost, 2),
            "projected_cost_usd": round(projected, 2),
            "days_elapsed": days_elapsed,
            "days_remaining": days_in_month - days_elapsed,
            "daily_avg_cost_usd": round(daily_avg, 2),
            "total_tokens_mtd": result[0]["total_tokens"],
            "total_requests_mtd": result[0]["request_count"]
        }


# Singleton instance
_alert_service = None


def get_token_alert_service(db: Optional[AsyncIOMotorDatabase] = None) -> TokenAlertService:
    """Get the token alert service instance"""
    global _alert_service
    if _alert_service is None:
        _alert_service = TokenAlertService(db)
    elif db is not None:
        _alert_service.set_db(db)
    return _alert_service
