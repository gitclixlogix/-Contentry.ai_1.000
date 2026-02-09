"""
Token Tracking Service for Contentry.ai

Tracks and monitors token usage across all AI agents.
Provides real-time monitoring, cost calculation, and alerting.

Super Admin only feature.
"""

import os
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from enum import Enum
from dataclasses import dataclass, asdict
import tiktoken

logger = logging.getLogger(__name__)


class AIProvider(str, Enum):
    """AI Provider types"""
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    GOOGLE_VISION = "google_vision"
    ELEVENLABS = "elevenlabs"


class AIModel(str, Enum):
    """AI Models used in the platform"""
    # OpenAI Models
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_4_1_NANO = "gpt-4.1-nano"
    GPT_4O = "gpt-4o"
    GPT_IMAGE_1 = "gpt-image-1"
    
    # Gemini Models
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_3_PRO_IMAGE = "gemini-3-pro-image-preview"
    
    # Google Vision
    GOOGLE_VISION_SAFE_SEARCH = "google-vision-safesearch"
    GOOGLE_VISION_LABELS = "google-vision-labels"
    
    # ElevenLabs
    ELEVENLABS_CONVAI = "elevenlabs-convai"


class AgentType(str, Enum):
    """Types of AI agents in the system"""
    CONTENT_ANALYSIS = "content_analysis"
    CONTENT_GENERATION = "content_generation"
    CULTURAL_ANALYSIS = "cultural_analysis"
    EMPLOYMENT_LAW = "employment_law"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    VIDEO_ANALYSIS = "video_analysis"
    IMAGE_GENERATION = "image_generation"
    IMAGE_ANALYSIS = "image_analysis"
    CONTENT_REWRITE = "content_rewrite"
    VOICE_ASSISTANT = "voice_assistant"


# Pricing per 1K tokens (in USD) - Updated Dec 2025
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # OpenAI pricing
    "gpt-4.1-mini": {"input": 0.00015, "output": 0.0006},  # $0.15/$0.60 per 1M
    "gpt-4.1-nano": {"input": 0.0001, "output": 0.0004},   # $0.10/$0.40 per 1M
    "gpt-4o": {"input": 0.005, "output": 0.015},           # $5/$15 per 1M
    "gpt-image-1": {"per_image": 0.04},                    # $0.04 per image
    
    # Gemini pricing
    "gemini-2.5-flash": {"input": 0.000075, "output": 0.0003},  # $0.075/$0.30 per 1M
    "gemini-3-pro-image-preview": {"per_image": 0.04},
    
    # Google Vision
    "google-vision-safesearch": {"per_request": 0.0015},
    "google-vision-labels": {"per_request": 0.0015},
    
    # ElevenLabs
    "elevenlabs-convai": {"per_character": 0.00003},  # ~$30 per 1M chars
}


@dataclass
class TokenUsageRecord:
    """Record of a single token usage event"""
    id: str
    timestamp: datetime
    user_id: str
    agent_type: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    api_cost_usd: float
    credit_cost: int
    session_id: Optional[str] = None
    content_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TokenTrackingService:
    """
    Service for tracking token usage across all AI agents.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not TokenTrackingService._initialized:
            self.db: Optional[AsyncIOMotorDatabase] = None
            self._buffer: List[TokenUsageRecord] = []
            self._buffer_size = 10  # Flush after 10 records
            self._flush_interval = 60  # Flush every 60 seconds
            self._last_flush = datetime.now(timezone.utc)
            TokenTrackingService._initialized = True
    
    def set_db(self, db: AsyncIOMotorDatabase):
        """Set database connection"""
        self.db = db
    
    async def log_token_usage(
        self,
        user_id: str,
        agent_type: AgentType,
        model: str,
        provider: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        session_id: Optional[str] = None,
        content_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        credit_cost: int = 0
    ) -> TokenUsageRecord:
        """
        Log a token usage event.
        
        Args:
            user_id: User who triggered the AI call
            agent_type: Type of agent (content_analysis, generation, etc.)
            model: Model used (gpt-4.1-mini, etc.)
            provider: Provider (openai, gemini, etc.)
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            session_id: Optional session/conversation ID
            content_id: Optional content ID being processed
            metadata: Additional metadata
            credit_cost: Platform credit cost for this action
            
        Returns:
            TokenUsageRecord
        """
        import uuid
        
        total_tokens = input_tokens + output_tokens
        api_cost = self._calculate_api_cost(model, input_tokens, output_tokens)
        
        record = TokenUsageRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            agent_type=agent_type.value if isinstance(agent_type, AgentType) else agent_type,
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            api_cost_usd=api_cost,
            credit_cost=credit_cost,
            session_id=session_id,
            content_id=content_id,
            metadata=metadata
        )
        
        self._buffer.append(record)
        
        # Flush if buffer is full or time elapsed
        if len(self._buffer) >= self._buffer_size or \
           (datetime.now(timezone.utc) - self._last_flush).seconds > self._flush_interval:
            await self._flush_buffer()
        
        logger.info(f"[TokenTracker] Logged: {agent_type} - {model} - {total_tokens} tokens - ${api_cost:.6f}")
        
        return record
    
    async def log_image_generation(
        self,
        user_id: str,
        model: str,
        provider: str,
        image_count: int = 1,
        session_id: Optional[str] = None,
        content_id: Optional[str] = None,
        credit_cost: int = 20
    ) -> TokenUsageRecord:
        """Log image generation (no tokens, per-image pricing)"""
        import uuid
        
        api_cost = self._calculate_image_cost(model, image_count)
        
        record = TokenUsageRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            agent_type=AgentType.IMAGE_GENERATION.value,
            model=model,
            provider=provider,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            api_cost_usd=api_cost,
            credit_cost=credit_cost,
            session_id=session_id,
            content_id=content_id,
            metadata={"image_count": image_count}
        )
        
        self._buffer.append(record)
        await self._flush_buffer()
        
        return record
    
    def _calculate_api_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate API cost based on model and token counts"""
        pricing = MODEL_PRICING.get(model, {"input": 0.001, "output": 0.002})
        
        if "input" in pricing and "output" in pricing:
            input_cost = (input_tokens / 1000) * pricing["input"]
            output_cost = (output_tokens / 1000) * pricing["output"]
            return round(input_cost + output_cost, 8)
        elif "per_request" in pricing:
            return pricing["per_request"]
        else:
            return 0.0
    
    def _calculate_image_cost(self, model: str, image_count: int) -> float:
        """Calculate cost for image generation"""
        pricing = MODEL_PRICING.get(model, {"per_image": 0.04})
        return round(image_count * pricing.get("per_image", 0.04), 6)
    
    async def _flush_buffer(self):
        """Flush buffered records to database"""
        if not self._buffer or self.db is None:
            return
        
        try:
            records = [r.to_dict() for r in self._buffer]
            await self.db.token_usage_logs.insert_many(records)
            
            # Update aggregates
            await self._update_aggregates(records)
            
            self._buffer.clear()
            self._last_flush = datetime.now(timezone.utc)
            logger.debug(f"[TokenTracker] Flushed {len(records)} records")
        except Exception as e:
            logger.error(f"[TokenTracker] Failed to flush buffer: {e}")
    
    async def _update_aggregates(self, records: List[Dict]):
        """Update hourly and daily aggregates"""
        if self.db is None:
            return
        
        now = datetime.now(timezone.utc)
        hour_key = now.strftime("%Y-%m-%d-%H")
        day_key = now.strftime("%Y-%m-%d")
        
        # Aggregate by hour
        hourly_totals: Dict[str, Dict] = {}
        daily_totals: Dict[str, Dict] = {}
        
        for record in records:
            # Hourly aggregate
            h_key = f"{hour_key}_{record['agent_type']}_{record['model']}"
            if h_key not in hourly_totals:
                hourly_totals[h_key] = {
                    "period": hour_key,
                    "period_type": "hourly",
                    "agent_type": record["agent_type"],
                    "model": record["model"],
                    "provider": record["provider"],
                    "total_tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "api_cost_usd": 0,
                    "credit_cost": 0,
                    "request_count": 0,
                }
            hourly_totals[h_key]["total_tokens"] += record["total_tokens"]
            hourly_totals[h_key]["input_tokens"] += record["input_tokens"]
            hourly_totals[h_key]["output_tokens"] += record["output_tokens"]
            hourly_totals[h_key]["api_cost_usd"] += record["api_cost_usd"]
            hourly_totals[h_key]["credit_cost"] += record["credit_cost"]
            hourly_totals[h_key]["request_count"] += 1
            
            # Daily aggregate
            d_key = f"{day_key}_{record['agent_type']}_{record['model']}"
            if d_key not in daily_totals:
                daily_totals[d_key] = {
                    "period": day_key,
                    "period_type": "daily",
                    "agent_type": record["agent_type"],
                    "model": record["model"],
                    "provider": record["provider"],
                    "total_tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "api_cost_usd": 0,
                    "credit_cost": 0,
                    "request_count": 0,
                }
            daily_totals[d_key]["total_tokens"] += record["total_tokens"]
            daily_totals[d_key]["input_tokens"] += record["input_tokens"]
            daily_totals[d_key]["output_tokens"] += record["output_tokens"]
            daily_totals[d_key]["api_cost_usd"] += record["api_cost_usd"]
            daily_totals[d_key]["credit_cost"] += record["credit_cost"]
            daily_totals[d_key]["request_count"] += 1
        
        # Upsert aggregates
        for key, data in hourly_totals.items():
            await self.db.token_usage_aggregates.update_one(
                {"_id": key},
                {"$inc": {
                    "total_tokens": data["total_tokens"],
                    "input_tokens": data["input_tokens"],
                    "output_tokens": data["output_tokens"],
                    "api_cost_usd": data["api_cost_usd"],
                    "credit_cost": data["credit_cost"],
                    "request_count": data["request_count"],
                }, "$set": {
                    "period": data["period"],
                    "period_type": data["period_type"],
                    "agent_type": data["agent_type"],
                    "model": data["model"],
                    "provider": data["provider"],
                    "updated_at": now,
                }},
                upsert=True
            )
        
        for key, data in daily_totals.items():
            await self.db.token_usage_aggregates.update_one(
                {"_id": key},
                {"$inc": {
                    "total_tokens": data["total_tokens"],
                    "input_tokens": data["input_tokens"],
                    "output_tokens": data["output_tokens"],
                    "api_cost_usd": data["api_cost_usd"],
                    "credit_cost": data["credit_cost"],
                    "request_count": data["request_count"],
                }, "$set": {
                    "period": data["period"],
                    "period_type": data["period_type"],
                    "agent_type": data["agent_type"],
                    "model": data["model"],
                    "provider": data["provider"],
                    "updated_at": now,
                }},
                upsert=True
            )
    
    async def get_usage_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "daily"  # hourly, daily, weekly, monthly
    ) -> Dict[str, Any]:
        """
        Get token usage summary for Super Admin dashboard.
        """
        if self.db is None:
            return {"error": "Database not connected"}
        
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        # Query aggregates
        period_type = "daily" if group_by in ["daily", "weekly", "monthly"] else "hourly"
        
        pipeline = [
            {
                "$match": {
                    "period_type": period_type,
                    "updated_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$period",
                    "total_tokens": {"$sum": "$total_tokens"},
                    "input_tokens": {"$sum": "$input_tokens"},
                    "output_tokens": {"$sum": "$output_tokens"},
                    "api_cost_usd": {"$sum": "$api_cost_usd"},
                    "credit_cost": {"$sum": "$credit_cost"},
                    "request_count": {"$sum": "$request_count"},
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        results = await self.db.token_usage_aggregates.aggregate(pipeline).to_list(None)
        
        # Calculate totals
        total_tokens = sum(r["total_tokens"] for r in results)
        total_api_cost = sum(r["api_cost_usd"] for r in results)
        total_requests = sum(r["request_count"] for r in results)
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "group_by": group_by
            },
            "totals": {
                "total_tokens": total_tokens,
                "total_api_cost_usd": round(total_api_cost, 4),
                "total_requests": total_requests,
                "avg_tokens_per_request": round(total_tokens / max(total_requests, 1), 2)
            },
            "trend_data": [
                {
                    "period": r["_id"],
                    "total_tokens": r["total_tokens"],
                    "api_cost_usd": round(r["api_cost_usd"], 4),
                    "request_count": r["request_count"]
                }
                for r in results
            ]
        }
    
    async def get_usage_by_agent(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get token usage breakdown by agent type"""
        if self.db is None:
            return []
        
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$agent_type",
                    "total_tokens": {"$sum": "$total_tokens"},
                    "input_tokens": {"$sum": "$input_tokens"},
                    "output_tokens": {"$sum": "$output_tokens"},
                    "api_cost_usd": {"$sum": "$api_cost_usd"},
                    "credit_cost": {"$sum": "$credit_cost"},
                    "request_count": {"$sum": 1},
                }
            },
            {"$sort": {"total_tokens": -1}}
        ]
        
        results = await self.db.token_usage_logs.aggregate(pipeline).to_list(None)
        
        return [
            {
                "agent_type": r["_id"],
                "total_tokens": r["total_tokens"],
                "input_tokens": r["input_tokens"],
                "output_tokens": r["output_tokens"],
                "api_cost_usd": round(r["api_cost_usd"], 4),
                "credit_cost": r["credit_cost"],
                "request_count": r["request_count"],
                "avg_tokens_per_request": round(r["total_tokens"] / max(r["request_count"], 1), 2)
            }
            for r in results
        ]
    
    async def get_usage_by_model(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get token usage breakdown by model"""
        if self.db is None:
            return []
        
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {"model": "$model", "provider": "$provider"},
                    "total_tokens": {"$sum": "$total_tokens"},
                    "input_tokens": {"$sum": "$input_tokens"},
                    "output_tokens": {"$sum": "$output_tokens"},
                    "api_cost_usd": {"$sum": "$api_cost_usd"},
                    "request_count": {"$sum": 1},
                }
            },
            {"$sort": {"api_cost_usd": -1}}
        ]
        
        results = await self.db.token_usage_logs.aggregate(pipeline).to_list(None)
        
        return [
            {
                "model": r["_id"]["model"],
                "provider": r["_id"]["provider"],
                "total_tokens": r["total_tokens"],
                "input_tokens": r["input_tokens"],
                "output_tokens": r["output_tokens"],
                "api_cost_usd": round(r["api_cost_usd"], 4),
                "request_count": r["request_count"],
            }
            for r in results
        ]
    
    async def get_top_users_by_tokens(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get top users by token consumption"""
        if self.db is None:
            return []
        
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$user_id",
                    "total_tokens": {"$sum": "$total_tokens"},
                    "api_cost_usd": {"$sum": "$api_cost_usd"},
                    "credit_cost": {"$sum": "$credit_cost"},
                    "request_count": {"$sum": 1},
                }
            },
            {"$sort": {"total_tokens": -1}},
            {"$limit": limit}
        ]
        
        results = await self.db.token_usage_logs.aggregate(pipeline).to_list(None)
        
        # Fetch user details
        enriched = []
        for r in results:
            user = await self.db.users.find_one(
                {"id": r["_id"]},
                {"_id": 0, "id": 1, "name": 1, "email": 1, "subscription_plan": 1}
            )
            enriched.append({
                "user_id": r["_id"],
                "name": user.get("name", "Unknown") if user else "Unknown",
                "email": user.get("email", "") if user else "",
                "plan": user.get("subscription_plan", "free") if user else "free",
                "total_tokens": r["total_tokens"],
                "api_cost_usd": round(r["api_cost_usd"], 4),
                "credit_cost": r["credit_cost"],
                "request_count": r["request_count"],
            })
        
        return enriched
    
    async def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time token usage stats for dashboard"""
        if self.db is None:
            return {}
        
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        hour_ago = now - timedelta(hours=1)
        
        # Today's stats
        today_pipeline = [
            {"$match": {"timestamp": {"$gte": today_start}}},
            {"$group": {
                "_id": None,
                "total_tokens": {"$sum": "$total_tokens"},
                "api_cost_usd": {"$sum": "$api_cost_usd"},
                "request_count": {"$sum": 1},
            }}
        ]
        
        # Last hour stats
        hour_pipeline = [
            {"$match": {"timestamp": {"$gte": hour_ago}}},
            {"$group": {
                "_id": None,
                "total_tokens": {"$sum": "$total_tokens"},
                "api_cost_usd": {"$sum": "$api_cost_usd"},
                "request_count": {"$sum": 1},
            }}
        ]
        
        today_results = await self.db.token_usage_logs.aggregate(today_pipeline).to_list(1)
        hour_results = await self.db.token_usage_logs.aggregate(hour_pipeline).to_list(1)
        
        today_data = today_results[0] if today_results else {"total_tokens": 0, "api_cost_usd": 0, "request_count": 0}
        hour_data = hour_results[0] if hour_results else {"total_tokens": 0, "api_cost_usd": 0, "request_count": 0}
        
        return {
            "today": {
                "total_tokens": today_data["total_tokens"],
                "api_cost_usd": round(today_data["api_cost_usd"], 4),
                "request_count": today_data["request_count"],
            },
            "last_hour": {
                "total_tokens": hour_data["total_tokens"],
                "api_cost_usd": round(hour_data["api_cost_usd"], 4),
                "request_count": hour_data["request_count"],
            },
            "tokens_per_minute": round(hour_data["total_tokens"] / 60, 2),
            "requests_per_minute": round(hour_data["request_count"] / 60, 2),
            "timestamp": now.isoformat(),
        }


# Singleton instance
token_tracker = TokenTrackingService()


def get_token_tracker() -> TokenTrackingService:
    """Get the singleton token tracker instance"""
    return token_tracker


# Helper function to estimate tokens using tiktoken
def estimate_tokens(text: str, model: str = "gpt-4") -> int:
    """Estimate token count for text"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback: rough estimate (4 chars per token)
        return len(text) // 4
