"""
Credit Service for Contentry.ai
Handles credit balance tracking, consumption, and plan enforcement.

Based on Pricing Strategy v3.0:
- Free: 25 credits/month
- Creator: 750 credits/month, $0.05/credit overage
- Pro: 1,500 credits/month, $0.04/credit overage
- Team: 5,000 credits/month, $0.035/credit overage
- Business: 15,000 credits/month, $0.03/credit overage
"""

import logging
import os
import functools
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from enum import Enum
from fastapi import Header, HTTPException, Depends

# Import database dependency
from services.database import get_db

logger = logging.getLogger(__name__)


class PlanTier(str, Enum):
    FREE = "free"
    STARTER = "starter"  # New tier between Free and Creator
    CREATOR = "creator"
    PRO = "pro"
    TEAM = "team"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class CreditAction(str, Enum):
    """Credit consumption actions with their costs"""
    # Core Content Features
    CONTENT_ANALYSIS = "content_analysis"  # 5 credits
    QUICK_ANALYSIS = "quick_analysis"  # 2 credits
    CONTENT_GENERATION = "content_generation"  # 10 credits
    AI_REWRITE = "ai_rewrite"  # 8 credits
    ITERATIVE_REWRITE = "iterative_rewrite"  # 15 credits
    
    # Image & Media Features
    IMAGE_GENERATION = "image_generation"  # 20 credits
    IMAGE_ANALYSIS = "image_analysis"  # 5 credits
    IMAGE_REGENERATION = "image_regeneration"  # 15 credits
    
    # Voice & Audio (Olivia Agent)
    VOICE_DICTATION = "voice_dictation"  # 3 credits/minute
    VOICE_COMMANDS = "voice_commands"  # 5 credits
    AI_VOICE_ASSISTANT = "ai_voice_assistant"  # 10 credits/interaction
    VOICE_CONTENT_GENERATION = "voice_content_generation"  # 15 credits
    
    # Sentiment Analysis
    URL_SENTIMENT_ANALYSIS = "url_sentiment_analysis"  # 8 credits
    BRAND_MENTION_TRACKING = "brand_mention_tracking"  # 5 credits/query
    COMPETITOR_ANALYSIS = "competitor_analysis"  # 12 credits
    
    # Publishing & Scheduling
    DIRECT_PUBLISH = "direct_publish"  # 2 credits/platform
    SCHEDULED_POST = "scheduled_post"  # 3 credits/platform
    PRE_PUBLISH_REANALYSIS = "pre_publish_reanalysis"  # 3 credits
    
    # Advanced Features
    KNOWLEDGE_BASE_UPLOAD = "knowledge_base_upload"  # 5 credits/document
    STRATEGIC_PROFILE_CREATION = "strategic_profile_creation"  # 10 credits
    EXPORT_TO_PDF = "export_to_pdf"  # 1 credit
    
    # Admin/Free actions
    APPROVAL_WORKFLOW = "approval_workflow"  # 0 credits (free)
    CREDIT_PURCHASE = "credit_purchase"  # Adds credits


# Credit costs per action - Updated per Final Pricing Strategy v1.0
CREDIT_COSTS: Dict[CreditAction, int] = {
    # Core Content Features
    CreditAction.CONTENT_ANALYSIS: 10,      # Was 5, now 10 per strategy
    CreditAction.QUICK_ANALYSIS: 5,         # Basic analysis (half of full)
    CreditAction.CONTENT_GENERATION: 50,    # Was 10, now 50 per strategy
    CreditAction.AI_REWRITE: 25,            # Half of generation
    CreditAction.ITERATIVE_REWRITE: 50,     # Same as generation (multiple passes)
    
    # Image & Media Features
    CreditAction.IMAGE_GENERATION: 20,      # Unchanged
    CreditAction.IMAGE_ANALYSIS: 10,        # Same as content analysis
    CreditAction.IMAGE_REGENERATION: 20,    # Same as generation
    
    # Voice & Audio
    CreditAction.VOICE_DICTATION: 5,        # per minute
    CreditAction.VOICE_COMMANDS: 10,        
    CreditAction.AI_VOICE_ASSISTANT: 100,   # Was 10, now 100 per strategy (Olivia)
    CreditAction.VOICE_CONTENT_GENERATION: 50,  # Same as content generation
    
    # Sentiment Analysis
    CreditAction.URL_SENTIMENT_ANALYSIS: 15,    # Was 8, now 15 per strategy
    CreditAction.BRAND_MENTION_TRACKING: 15,    # Same as sentiment
    CreditAction.COMPETITOR_ANALYSIS: 15,       # Same as sentiment
    
    # Publishing & Scheduling
    CreditAction.DIRECT_PUBLISH: 2,         # per platform
    CreditAction.SCHEDULED_POST: 3,         # per platform
    CreditAction.PRE_PUBLISH_REANALYSIS: 5, # Quick reanalysis
    
    # Advanced Features
    CreditAction.KNOWLEDGE_BASE_UPLOAD: 5,
    CreditAction.STRATEGIC_PROFILE_CREATION: 10,
    CreditAction.EXPORT_TO_PDF: 1,
    
    # Free actions
    CreditAction.APPROVAL_WORKFLOW: 0,
    CreditAction.CREDIT_PURCHASE: 0,
}


# Plan configurations
PLAN_CONFIGS: Dict[PlanTier, Dict] = {
    PlanTier.FREE: {
        "name": "Free",
        "monthly_credits": 100,  # Updated from 25 to 100
        "overage_rate": 0.06,  # $0.06/credit (must buy packs)
        "can_purchase_overage": False,  # Must buy credit packs
        "features": {
            # All features enabled (same as Creator)
            "content_analysis": True,
            "content_generation": True,
            "ai_rewrite": True,
            "image_generation": True,
            "voice_assistant": True,
            "sentiment_analysis": True,
            "api_access": False,  # API access still restricted
        },
        "limits": {
            "strategic_profiles": 1,
            "team_members": 1,
            "storage_gb": 1,
        }
    },
    PlanTier.STARTER: {
        "name": "Starter",
        "monthly_credits": 400,
        "overage_rate": 0.055,  # $0.055/credit
        "can_purchase_overage": True,
        "features": {
            # Same functionality as Creator
            "content_analysis": True,
            "content_generation": True,
            "ai_rewrite": True,
            "image_generation": True,
            "voice_assistant": True,
            "sentiment_analysis": True,
            "api_access": False,
        },
        "limits": {
            "strategic_profiles": 1,
            "team_members": 1,
            "content_items_per_month": 500,
            "storage_gb": 5,
        }
    },
    PlanTier.CREATOR: {
        "name": "Creator",
        "monthly_credits": 750,
        "overage_rate": 0.05,
        "can_purchase_overage": True,
        "features": {
            "content_analysis": True,
            "content_generation": True,
            "ai_rewrite": True,
            "image_generation": True,
            "voice_assistant": True,  # Updated: now included
            "sentiment_analysis": True,
            "api_access": False,
        },
        "limits": {
            "strategic_profiles": 3,
            "team_members": 1,
            "content_items_per_month": 500,
            "storage_gb": 10,
        }
    },
    PlanTier.PRO: {
        "name": "Pro",
        "monthly_credits": 1500,
        "overage_rate": 0.04,
        "can_purchase_overage": True,
        "features": {
            "content_analysis": True,
            "content_generation": True,
            "ai_rewrite": True,
            "image_generation": True,
            "voice_assistant": True,
            "sentiment_analysis": True,
            "api_access": True,
        },
        "limits": {
            "strategic_profiles": 10,
            "team_members": 1,
            "content_items_per_month": 2000,
            "storage_gb": 50,
            "api_rate_limit": 100,  # requests/min
        }
    },
    PlanTier.TEAM: {
        "name": "Team",
        "monthly_credits": 5000,
        "overage_rate": 0.035,
        "can_purchase_overage": True,
        "features": {
            "content_analysis": True,
            "content_generation": True,
            "ai_rewrite": True,
            "image_generation": True,
            "voice_assistant": True,
            "sentiment_analysis": True,
            "api_access": True,
            "approval_workflows": True,
            "shared_credit_pool": True,
        },
        "limits": {
            "strategic_profiles": -1,  # Unlimited
            "team_members": 10,
            "content_items_per_month": 10000,
            "storage_gb": 500,
            "api_rate_limit": 500,
        }
    },
    PlanTier.BUSINESS: {
        "name": "Business",
        "monthly_credits": 15000,
        "overage_rate": 0.03,
        "can_purchase_overage": True,
        "features": {
            "content_analysis": True,
            "content_generation": True,
            "ai_rewrite": True,
            "image_generation": True,
            "voice_assistant": True,
            "sentiment_analysis": True,
            "api_access": True,
            "approval_workflows": True,
            "shared_credit_pool": True,
            "sso": True,
            "custom_roles": True,
        },
        "limits": {
            "strategic_profiles": -1,
            "team_members": -1,  # Unlimited
            "content_items_per_month": 50000,
            "storage_gb": 2048,  # 2TB
            "api_rate_limit": 2000,
        }
    },
    PlanTier.ENTERPRISE: {
        "name": "Enterprise",
        "monthly_credits": -1,  # Custom
        "overage_rate": 0.025,  # Volume discount
        "can_purchase_overage": True,
        "features": {
            "content_analysis": True,
            "content_generation": True,
            "ai_rewrite": True,
            "image_generation": True,
            "voice_assistant": True,
            "sentiment_analysis": True,
            "api_access": True,
            "approval_workflows": True,
            "shared_credit_pool": True,
            "sso": True,
            "custom_roles": True,
            "custom_integrations": True,
            "dedicated_support": True,
        },
        "limits": {
            "strategic_profiles": -1,
            "team_members": -1,
            "content_items_per_month": -1,
            "storage_gb": -1,  # Custom
            "api_rate_limit": -1,  # Custom
        }
    },
}


# Credit pack configurations - Updated with Stripe Price IDs (January 2026)
CREDIT_PACKS = {
    "starter": {
        "id": "starter",
        "name": "Starter Pack",
        "credits": 100,
        "price_usd": 6.00,
        "per_credit_rate": 0.06,
        "savings_percent": 0,
        "stripe_price_id": os.getenv("STRIPE_PRICE_PACK_STARTER"),
        "stripe_product_id": os.getenv("STRIPE_PRODUCT_PACK_STARTER"),
    },
    "standard": {
        "id": "standard",
        "name": "Standard Pack",
        "credits": 500,
        "price_usd": 22.50,
        "per_credit_rate": 0.045,
        "savings_percent": 25,  # Updated per pricing strategy
        "stripe_price_id": os.getenv("STRIPE_PRICE_PACK_STANDARD"),
        "stripe_product_id": os.getenv("STRIPE_PRODUCT_PACK_STANDARD"),
    },
    "growth": {
        "id": "growth",
        "name": "Growth Pack",
        "credits": 1000,
        "price_usd": 40.00,
        "per_credit_rate": 0.04,
        "savings_percent": 33,  # Updated per pricing strategy
        "stripe_price_id": os.getenv("STRIPE_PRICE_PACK_GROWTH"),
        "stripe_product_id": os.getenv("STRIPE_PRODUCT_PACK_GROWTH"),
    },
    "scale": {
        "id": "scale",
        "name": "Scale Pack",
        "credits": 5000,
        "price_usd": 175.00,
        "per_credit_rate": 0.035,
        "savings_percent": 42,  # Updated per pricing strategy
        "stripe_price_id": os.getenv("STRIPE_PRICE_PACK_SCALE"),
        "stripe_product_id": os.getenv("STRIPE_PRODUCT_PACK_SCALE"),
    },
}


class CreditService:
    """Service for managing user credits"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def _get_user_enterprise(self, user_id: str) -> Optional[Dict]:
        """Check if user belongs to an enterprise with shared credits"""
        user = await self.db.users.find_one(
            {"id": user_id},
            {"_id": 0, "enterprise_id": 1, "uses_enterprise_credits": 1}
        )
        
        if user and user.get("enterprise_id") and user.get("uses_enterprise_credits"):
            enterprise_credits = await self.db.enterprise_credits.find_one(
                {"enterprise_id": user["enterprise_id"]},
                {"_id": 0}
            )
            if enterprise_credits:
                return {
                    "enterprise_id": user["enterprise_id"],
                    "credits": enterprise_credits
                }
        return None
    
    async def get_user_credits(self, user_id: str) -> Dict:
        """Get user's credit balance and plan info"""
        # Check for enterprise shared credits first
        enterprise_info = await self._get_user_enterprise(user_id)
        
        if enterprise_info:
            # User uses enterprise shared credit pool
            enterprise_credits = enterprise_info["credits"]
            plan_tier = PlanTier(enterprise_credits.get("plan", "business"))
            plan_config = PLAN_CONFIGS.get(plan_tier, PLAN_CONFIGS[PlanTier.BUSINESS])
            
            return {
                "user_id": user_id,
                "plan": enterprise_credits.get("plan", "business"),
                "plan_name": f"{plan_config['name']} (Enterprise)",
                "credits_balance": enterprise_credits.get("credits", 0),
                "credits_used_this_month": enterprise_credits.get("credits_used_this_month", 0),
                "monthly_allowance": enterprise_credits.get("monthly_limit", plan_config["monthly_credits"]),
                "overage_credits": enterprise_credits.get("overage_credits", 0),
                "overage_rate": plan_config["overage_rate"],
                "billing_cycle_start": enterprise_credits.get("billing_cycle_start"),
                "billing_cycle_end": enterprise_credits.get("billing_cycle_end"),
                "features": plan_config["features"],
                "limits": plan_config["limits"],
                "is_enterprise": True,
                "enterprise_id": enterprise_info["enterprise_id"],
                "shared_pool": True,
            }
        
        # Get or create individual credit record
        credit_record = await self.db.user_credits.find_one(
            {"user_id": user_id},
            {"_id": 0}
        )
        
        if not credit_record:
            # Initialize new user with Free plan
            credit_record = await self._initialize_user_credits(user_id)
        
        # Check if we need to reset monthly credits
        credit_record = await self._check_monthly_reset(user_id, credit_record)
        
        # Get plan config
        plan_tier = PlanTier(credit_record.get("plan", "free"))
        plan_config = PLAN_CONFIGS.get(plan_tier, PLAN_CONFIGS[PlanTier.FREE])
        
        return {
            "user_id": user_id,
            "plan": credit_record.get("plan", "free"),
            "plan_name": plan_config["name"],
            "credits_balance": credit_record.get("credits_balance", 0),
            "credits_used_this_month": credit_record.get("credits_used_this_month", 0),
            "monthly_allowance": plan_config["monthly_credits"],
            "overage_credits": credit_record.get("overage_credits", 0),
            "overage_rate": plan_config["overage_rate"],
            "billing_cycle_start": credit_record.get("billing_cycle_start"),
            "billing_cycle_end": credit_record.get("billing_cycle_end"),
            "features": plan_config["features"],
            "limits": plan_config["limits"],
            "is_enterprise": False,
        }
    
    async def _initialize_user_credits(self, user_id: str, plan: str = "free") -> Dict:
        """Initialize or update credit record for user (upsert)"""
        now = datetime.now(timezone.utc)
        
        # Calculate billing cycle (monthly)
        billing_cycle_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            billing_cycle_end = billing_cycle_start.replace(year=now.year + 1, month=1)
        else:
            billing_cycle_end = billing_cycle_start.replace(month=now.month + 1)
        
        plan_tier = PlanTier(plan)
        plan_config = PLAN_CONFIGS.get(plan_tier, PLAN_CONFIGS[PlanTier.FREE])
        
        credit_record = {
            "user_id": user_id,
            "plan": plan,
            "credits_balance": plan_config["monthly_credits"],
            "credits_used_this_month": 0,
            "overage_credits": 0,
            "billing_cycle_start": billing_cycle_start.isoformat(),
            "billing_cycle_end": billing_cycle_end.isoformat(),
            "updated_at": now.isoformat(),
        }
        
        # Use upsert to handle both new and existing users
        await self.db.user_credits.update_one(
            {"user_id": user_id},
            {
                "$set": credit_record,
                "$setOnInsert": {"created_at": now.isoformat()}
            },
            upsert=True
        )
        
        logger.info(f"Initialized/updated credits for user {user_id} with plan {plan}")
        return credit_record
    
    async def _check_monthly_reset(self, user_id: str, credit_record: Dict) -> Dict:
        """Check if monthly credits need to be reset"""
        now = datetime.now(timezone.utc)
        billing_cycle_end = credit_record.get("billing_cycle_end")
        
        if billing_cycle_end:
            cycle_end = datetime.fromisoformat(billing_cycle_end.replace('Z', '+00:00'))
            
            if now >= cycle_end:
                # Reset monthly credits
                plan_tier = PlanTier(credit_record.get("plan", "free"))
                plan_config = PLAN_CONFIGS.get(plan_tier, PLAN_CONFIGS[PlanTier.FREE])
                
                # Calculate new billing cycle
                new_cycle_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if now.month == 12:
                    new_cycle_end = new_cycle_start.replace(year=now.year + 1, month=1)
                else:
                    new_cycle_end = new_cycle_start.replace(month=now.month + 1)
                
                # Update record - monthly allowance resets, but purchased credits carry over
                purchased_credits = credit_record.get("overage_credits", 0)
                new_balance = plan_config["monthly_credits"] + purchased_credits
                
                await self.db.user_credits.update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "credits_balance": new_balance,
                        "credits_used_this_month": 0,
                        "billing_cycle_start": new_cycle_start.isoformat(),
                        "billing_cycle_end": new_cycle_end.isoformat(),
                        "updated_at": now.isoformat(),
                    }}
                )
                
                credit_record["credits_balance"] = new_balance
                credit_record["credits_used_this_month"] = 0
                credit_record["billing_cycle_start"] = new_cycle_start.isoformat()
                credit_record["billing_cycle_end"] = new_cycle_end.isoformat()
                
                logger.info(f"Reset monthly credits for user {user_id}")
        
        return credit_record
    
    async def consume_credits(
        self,
        user_id: str,
        action: CreditAction,
        quantity: int = 1,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, Dict]:
        """
        Consume credits for an action.
        
        Returns: (success, result_dict)
        - If success: result contains transaction details
        - If failure: result contains error message
        
        Supports both individual user credits and enterprise shared credit pools.
        """
        # Get credit cost for action
        credit_cost = CREDIT_COSTS.get(action, 0) * quantity
        
        if credit_cost == 0:
            # Free action
            return True, {"credits_consumed": 0, "action": action.value}
        
        # Get user's current credits (handles enterprise check internally)
        user_credits = await self.get_user_credits(user_id)
        current_balance = user_credits.get("credits_balance", 0)
        is_enterprise = user_credits.get("is_enterprise", False)
        enterprise_id = user_credits.get("enterprise_id")
        
        if current_balance < credit_cost:
            # Insufficient credits
            pool_type = "enterprise" if is_enterprise else "personal"
            return False, {
                "error": "insufficient_credits",
                "message": f"Insufficient {pool_type} credits. Required: {credit_cost}, Available: {current_balance}",
                "credits_required": credit_cost,
                "credits_available": current_balance,
                "action": action.value,
                "is_enterprise": is_enterprise,
            }
        
        # Deduct credits
        now = datetime.now(timezone.utc)
        new_balance = current_balance - credit_cost
        
        if is_enterprise and enterprise_id:
            # Deduct from enterprise shared pool
            await self.db.enterprise_credits.update_one(
                {"enterprise_id": enterprise_id},
                {
                    "$set": {
                        "credits": new_balance,
                        "updated_at": now.isoformat(),
                    },
                    "$inc": {
                        "credits_used_this_month": credit_cost,
                    }
                }
            )
            logger.info(f"Enterprise {enterprise_id} consumed {credit_cost} credits for {action.value} (user: {user_id})")
        else:
            # Deduct from individual user credits
            await self.db.user_credits.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "credits_balance": new_balance,
                        "updated_at": now.isoformat(),
                    },
                    "$inc": {
                        "credits_used_this_month": credit_cost,
                    }
                }
            )
            logger.info(f"User {user_id} consumed {credit_cost} credits for {action.value}")
        
        # Log transaction (includes enterprise info if applicable)
        transaction = {
            "user_id": user_id,
            "enterprise_id": enterprise_id if is_enterprise else None,
            "is_enterprise_credit": is_enterprise,
            "action": action.value,
            "credits_consumed": credit_cost,
            "quantity": quantity,
            "balance_before": current_balance,
            "balance_after": new_balance,
            "metadata": metadata or {},
            "created_at": now.isoformat(),
        }
        
        await self.db.credit_transactions.insert_one(transaction)
        transaction.pop("_id", None)
        
        return True, {
            "credits_consumed": credit_cost,
            "balance_before": current_balance,
            "balance_after": new_balance,
            "action": action.value,
            "transaction": transaction,
        }
    
    async def check_credits(
        self,
        user_id: str,
        action: CreditAction,
        quantity: int = 1
    ) -> Tuple[bool, int, int]:
        """
        Check if user has enough credits for an action (without consuming).
        
        Returns: (has_enough, credits_required, credits_available)
        """
        credit_cost = CREDIT_COSTS.get(action, 0) * quantity
        user_credits = await self.get_user_credits(user_id)
        current_balance = user_credits.get("credits_balance", 0)
        
        return current_balance >= credit_cost, credit_cost, current_balance
    
    async def add_credits(
        self,
        user_id: str,
        credits: int,
        reason: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Add credits to user's account (purchase, bonus, refund, etc.)"""
        now = datetime.now(timezone.utc)
        
        # Ensure user has credit record
        user_credits = await self.get_user_credits(user_id)
        current_balance = user_credits.get("credits_balance", 0)
        new_balance = current_balance + credits
        
        await self.db.user_credits.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "credits_balance": new_balance,
                    "updated_at": now.isoformat(),
                },
                "$inc": {
                    "overage_credits": credits,  # Track purchased/bonus credits
                }
            }
        )
        
        # Log transaction
        transaction = {
            "user_id": user_id,
            "action": CreditAction.CREDIT_PURCHASE.value,
            "credits_added": credits,
            "reason": reason,
            "balance_before": current_balance,
            "balance_after": new_balance,
            "metadata": metadata or {},
            "created_at": now.isoformat(),
        }
        
        await self.db.credit_transactions.insert_one(transaction)
        transaction.pop("_id", None)
        
        logger.info(f"Added {credits} credits to user {user_id}: {reason}")
        
        return {
            "credits_added": credits,
            "balance_before": current_balance,
            "balance_after": new_balance,
            "reason": reason,
            "transaction": transaction,
        }
    
    async def update_plan(self, user_id: str, new_plan: str) -> Dict:
        """Update user's subscription plan"""
        now = datetime.now(timezone.utc)
        
        # Get current credits
        user_credits = await self.get_user_credits(user_id)
        old_plan = user_credits.get("plan", "free")
        
        # Get new plan config
        plan_tier = PlanTier(new_plan)
        plan_config = PLAN_CONFIGS.get(plan_tier, PLAN_CONFIGS[PlanTier.FREE])
        
        # Calculate new balance
        # If upgrading, add the difference in monthly allowance
        # If downgrading, keep current balance (don't remove credits)
        old_monthly = PLAN_CONFIGS.get(PlanTier(old_plan), PLAN_CONFIGS[PlanTier.FREE])["monthly_credits"]
        new_monthly = plan_config["monthly_credits"]
        
        current_balance = user_credits.get("credits_balance", 0)
        
        if new_monthly > old_monthly:
            # Upgrading - add the difference
            credit_diff = new_monthly - old_monthly
            new_balance = current_balance + credit_diff
        else:
            # Downgrading - keep current balance
            new_balance = current_balance
        
        await self.db.user_credits.update_one(
            {"user_id": user_id},
            {"$set": {
                "plan": new_plan,
                "credits_balance": new_balance,
                "updated_at": now.isoformat(),
            }}
        )
        
        # Log plan change
        await self.db.credit_transactions.insert_one({
            "user_id": user_id,
            "action": "plan_change",
            "old_plan": old_plan,
            "new_plan": new_plan,
            "balance_before": current_balance,
            "balance_after": new_balance,
            "created_at": now.isoformat(),
        })
        
        logger.info(f"Updated plan for user {user_id}: {old_plan} -> {new_plan}")
        
        return {
            "old_plan": old_plan,
            "new_plan": new_plan,
            "balance_before": current_balance,
            "balance_after": new_balance,
            "monthly_allowance": new_monthly,
        }
    
    async def get_credit_history(
        self,
        user_id: str,
        limit: int = 50,
        skip: int = 0,
        action_filter: Optional[str] = None
    ) -> List[Dict]:
        """Get user's credit transaction history"""
        query = {"user_id": user_id}
        
        if action_filter:
            query["action"] = action_filter
        
        transactions = await self.db.credit_transactions.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        return transactions
    
    async def get_usage_summary(self, user_id: str, days: int = 30) -> Dict:
        """Get credit usage summary for the specified period"""
        from datetime import timedelta
        
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days)
        
        # Aggregate usage by action type
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "created_at": {"$gte": start_date.isoformat()},
                    "credits_consumed": {"$exists": True},
                }
            },
            {
                "$group": {
                    "_id": "$action",
                    "total_credits": {"$sum": "$credits_consumed"},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"total_credits": -1}}
        ]
        
        usage_by_action = await self.db.credit_transactions.aggregate(pipeline).to_list(100)
        
        # Daily usage for charts
        daily_pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "created_at": {"$gte": start_date.isoformat()},
                    "credits_consumed": {"$exists": True},
                }
            },
            {
                "$addFields": {
                    "date": {"$substr": ["$created_at", 0, 10]}
                }
            },
            {
                "$group": {
                    "_id": "$date",
                    "total_credits": {"$sum": "$credits_consumed"},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        daily_usage = await self.db.credit_transactions.aggregate(daily_pipeline).to_list(100)
        
        # Calculate totals
        total_used = sum(u.get("total_credits", 0) for u in usage_by_action)
        total_transactions = sum(u.get("count", 0) for u in usage_by_action)
        
        return {
            "period_days": days,
            "total_credits_used": total_used,
            "total_transactions": total_transactions,
            "usage_by_action": [
                {
                    "action": u["_id"],
                    "credits": u["total_credits"],
                    "count": u["count"],
                }
                for u in usage_by_action
            ],
            "daily_usage": [
                {
                    "date": u["_id"],
                    "credits": u["total_credits"],
                    "count": u["count"],
                }
                for u in daily_usage
            ],
        }
    
    # =========================================================================
    # AUTO-REFILL FEATURE
    # =========================================================================
    
    async def get_auto_refill_settings(self, user_id: str) -> Dict:
        """Get user's auto-refill settings"""
        settings = await self.db.auto_refill_settings.find_one(
            {"user_id": user_id},
            {"_id": 0}
        )
        
        if not settings:
            # Return default settings
            return {
                "user_id": user_id,
                "enabled": False,
                "threshold_credits": 100,
                "refill_pack_id": "standard",
                "max_refills_per_month": 3,
                "refills_this_month": 0,
                "payment_method_id": None,
                "last_refill_at": None,
                "created_at": None,
            }
        
        return settings
    
    async def update_auto_refill_settings(
        self,
        user_id: str,
        enabled: bool,
        threshold_credits: int,
        refill_pack_id: str,
        max_refills_per_month: int = 3,
        payment_method_id: Optional[str] = None
    ) -> Dict:
        """Update user's auto-refill settings"""
        now = datetime.now(timezone.utc)
        
        # Validate pack exists
        if refill_pack_id not in CREDIT_PACKS:
            raise ValueError(f"Invalid pack ID: {refill_pack_id}")
        
        # Validate threshold
        if threshold_credits < 10:
            raise ValueError("Threshold must be at least 10 credits")
        
        if threshold_credits > 5000:
            raise ValueError("Threshold cannot exceed 5000 credits")
        
        # Validate max refills
        if max_refills_per_month < 1 or max_refills_per_month > 10:
            raise ValueError("Max refills per month must be between 1 and 10")
        
        settings = {
            "user_id": user_id,
            "enabled": enabled,
            "threshold_credits": threshold_credits,
            "refill_pack_id": refill_pack_id,
            "max_refills_per_month": max_refills_per_month,
            "payment_method_id": payment_method_id,
            "updated_at": now.isoformat(),
        }
        
        # Check if settings exist
        existing = await self.db.auto_refill_settings.find_one({"user_id": user_id})
        
        if existing:
            await self.db.auto_refill_settings.update_one(
                {"user_id": user_id},
                {"$set": settings}
            )
        else:
            settings["created_at"] = now.isoformat()
            settings["refills_this_month"] = 0
            settings["last_refill_at"] = None
            await self.db.auto_refill_settings.insert_one(settings)
        
        # Remove _id if present
        settings.pop("_id", None)
        
        logger.info(f"Updated auto-refill settings for user {user_id}: enabled={enabled}")
        
        return settings
    
    async def check_and_trigger_auto_refill(self, user_id: str, force_charge: bool = False) -> Optional[Dict]:
        """
        Check if auto-refill should be triggered and process it with Stripe payment.
        
        Args:
            user_id: The user to check
            force_charge: If True, actually charge via Stripe. If False, just create pending record.
        
        Returns refill result if triggered, None otherwise.
        """
        import stripe
        from email_service import (
            send_auto_refill_success_email,
            send_auto_refill_failed_email,
        )
        
        # Get auto-refill settings
        settings = await self.get_auto_refill_settings(user_id)
        
        if not settings.get("enabled"):
            return None
        
        # Get current credit balance
        user_credits = await self.get_user_credits(user_id)
        current_balance = user_credits.get("credits_balance", 0)
        threshold = settings.get("threshold_credits", 100)
        
        # Check if below threshold
        if current_balance >= threshold:
            return None
        
        # Check monthly limit
        refills_this_month = settings.get("refills_this_month", 0)
        max_refills = settings.get("max_refills_per_month", 3)
        
        if refills_this_month >= max_refills:
            logger.info(f"Auto-refill skipped for {user_id}: monthly limit reached ({refills_this_month}/{max_refills})")
            return {
                "triggered": False,
                "reason": "monthly_limit_reached",
                "refills_this_month": refills_this_month,
                "max_refills_per_month": max_refills,
            }
        
        # Get the pack to refill
        pack_id = settings.get("refill_pack_id", "standard")
        pack = CREDIT_PACKS.get(pack_id)
        
        if not pack:
            logger.error(f"Auto-refill failed: invalid pack {pack_id}")
            return {
                "triggered": False,
                "reason": "invalid_pack",
            }
        
        now = datetime.now(timezone.utc)
        
        # Get user info for email
        user = await self.db.users.find_one({"id": user_id}, {"_id": 0, "email": 1, "full_name": 1, "stripe_customer_id": 1})
        user_email = user.get("email") if user else None
        user_name = user.get("full_name", "User") if user else "User"
        stripe_customer_id = user.get("stripe_customer_id") if user else None
        
        # Create initial refill record
        refill_record = {
            "user_id": user_id,
            "pack_id": pack_id,
            "credits": pack["credits"],
            "amount_usd": pack["price_usd"],
            "status": "pending",
            "trigger_balance": current_balance,
            "threshold": threshold,
            "created_at": now.isoformat(),
        }
        
        result = await self.db.auto_refill_history.insert_one(refill_record)
        refill_id = str(result.inserted_id)
        refill_record["id"] = refill_id
        refill_record.pop("_id", None)
        
        logger.info(f"Auto-refill triggered for user {user_id}: {pack['credits']} credits, ${pack['price_usd']}")
        
        # If force_charge is True and we have Stripe configured, process payment
        stripe_api_key = os.environ.get("STRIPE_API_KEY")
        payment_method_id = settings.get("payment_method_id")
        
        if force_charge and stripe_api_key and stripe_customer_id:
            try:
                stripe.api_key = stripe_api_key
                
                # Create PaymentIntent with saved payment method
                amount_cents = int(pack["price_usd"] * 100)
                
                payment_intent = stripe.PaymentIntent.create(
                    amount=amount_cents,
                    currency="usd",
                    customer=stripe_customer_id,
                    payment_method=payment_method_id,
                    off_session=True,
                    confirm=True,
                    metadata={
                        "type": "auto_refill",
                        "user_id": user_id,
                        "pack_id": pack_id,
                        "credits": str(pack["credits"]),
                        "refill_id": refill_id,
                    },
                    description=f"Auto-refill: {pack['name']} ({pack['credits']} credits)"
                )
                
                if payment_intent.status == "succeeded":
                    # Payment successful - add credits
                    await self.add_credits(
                        user_id,
                        pack["credits"],
                        "auto_refill",
                        {"pack_id": pack_id, "payment_intent_id": payment_intent.id}
                    )
                    
                    # Update refill record
                    await self.db.auto_refill_history.update_one(
                        {"_id": result.inserted_id},
                        {"$set": {
                            "status": "completed",
                            "payment_intent_id": payment_intent.id,
                            "completed_at": datetime.now(timezone.utc).isoformat(),
                        }}
                    )
                    
                    # Increment refills this month
                    await self.db.auto_refill_settings.update_one(
                        {"user_id": user_id},
                        {
                            "$inc": {"refills_this_month": 1},
                            "$set": {"last_refill_at": datetime.now(timezone.utc).isoformat()}
                        }
                    )
                    
                    # Get new balance
                    new_credits = await self.get_user_credits(user_id)
                    new_balance = new_credits.get("credits_balance", 0)
                    
                    # Send success email
                    if user_email:
                        try:
                            await send_auto_refill_success_email(
                                email=user_email,
                                user_name=user_name,
                                pack_name=pack["name"],
                                credits_added=pack["credits"],
                                amount_charged=pack["price_usd"],
                                new_balance=new_balance,
                                transaction_id=payment_intent.id
                            )
                        except Exception as email_error:
                            logger.error(f"Failed to send auto-refill success email: {email_error}")
                    
                    return {
                        "triggered": True,
                        "status": "completed",
                        "pack_id": pack_id,
                        "credits": pack["credits"],
                        "amount_usd": pack["price_usd"],
                        "current_balance": current_balance,
                        "new_balance": new_balance,
                        "threshold": threshold,
                        "payment_intent_id": payment_intent.id,
                    }
                else:
                    # Payment requires additional action or failed
                    await self.db.auto_refill_history.update_one(
                        {"_id": result.inserted_id},
                        {"$set": {
                            "status": "requires_action",
                            "payment_intent_id": payment_intent.id,
                            "payment_status": payment_intent.status,
                        }}
                    )
                    
                    return {
                        "triggered": True,
                        "status": "requires_action",
                        "payment_status": payment_intent.status,
                        "pack_id": pack_id,
                        "credits": pack["credits"],
                        "amount_usd": pack["price_usd"],
                    }
                    
            except stripe.error.CardError as e:
                # Card was declined
                error_message = e.user_message if hasattr(e, 'user_message') else str(e)
                
                await self.db.auto_refill_history.update_one(
                    {"_id": result.inserted_id},
                    {"$set": {
                        "status": "failed",
                        "error": error_message,
                        "failed_at": datetime.now(timezone.utc).isoformat(),
                    }}
                )
                
                # Send failure email
                if user_email:
                    try:
                        await send_auto_refill_failed_email(
                            email=user_email,
                            user_name=user_name,
                            pack_name=pack["name"],
                            amount=pack["price_usd"],
                            error_reason=error_message
                        )
                    except Exception as email_error:
                        logger.error(f"Failed to send auto-refill failed email: {email_error}")
                
                logger.error(f"Auto-refill card error for {user_id}: {error_message}")
                
                return {
                    "triggered": True,
                    "status": "failed",
                    "reason": "card_declined",
                    "error": error_message,
                    "pack_id": pack_id,
                }
                
            except stripe.error.StripeError as e:
                error_message = str(e)
                
                await self.db.auto_refill_history.update_one(
                    {"_id": result.inserted_id},
                    {"$set": {
                        "status": "failed",
                        "error": error_message,
                        "failed_at": datetime.now(timezone.utc).isoformat(),
                    }}
                )
                
                # Send failure email
                if user_email:
                    try:
                        await send_auto_refill_failed_email(
                            email=user_email,
                            user_name=user_name,
                            pack_name=pack["name"],
                            amount=pack["price_usd"],
                            error_reason="Payment processing error"
                        )
                    except Exception as email_error:
                        logger.error(f"Failed to send auto-refill failed email: {email_error}")
                
                logger.error(f"Auto-refill Stripe error for {user_id}: {error_message}")
                
                return {
                    "triggered": True,
                    "status": "failed",
                    "reason": "payment_error",
                    "error": error_message,
                    "pack_id": pack_id,
                }
        
        # No Stripe configured or no customer ID - return pending status
        return {
            "triggered": True,
            "status": "pending",
            "pack_id": pack_id,
            "credits": pack["credits"],
            "amount_usd": pack["price_usd"],
            "current_balance": current_balance,
            "threshold": threshold,
            "refill_record": refill_record,
            "message": "Auto-refill pending. Set up a payment method to enable automatic charging.",
        }
    
    async def check_low_balance_warning(self, user_id: str) -> Optional[Dict]:
        """
        Check if user's balance is low and send warning email.
        This should be called periodically or after credit consumption.
        
        Returns warning info if sent, None if no warning needed.
        """
        from email_service import send_auto_refill_warning_email
        
        # Get auto-refill settings
        settings = await self.get_auto_refill_settings(user_id)
        
        if not settings.get("enabled"):
            return None
        
        # Get current credit balance
        user_credits = await self.get_user_credits(user_id)
        current_balance = user_credits.get("credits_balance", 0)
        threshold = settings.get("threshold_credits", 100)
        
        # Warning zone: balance is between threshold and 2x threshold
        warning_threshold = threshold * 2
        
        if current_balance >= warning_threshold or current_balance < threshold:
            # Either above warning zone or already below threshold (auto-refill will trigger)
            return None
        
        # Check if we already sent a warning recently (within 24 hours)
        last_warning = await self.db.auto_refill_warnings.find_one(
            {"user_id": user_id},
            sort=[("sent_at", -1)]
        )
        
        if last_warning:
            from datetime import timedelta
            last_sent = datetime.fromisoformat(last_warning.get("sent_at", "2000-01-01"))
            if datetime.now(timezone.utc) - last_sent < timedelta(hours=24):
                return None
        
        # Get user info and pack details
        user = await self.db.users.find_one({"id": user_id}, {"_id": 0, "email": 1, "full_name": 1})
        if not user or not user.get("email"):
            return None
        
        pack_id = settings.get("refill_pack_id", "standard")
        pack = CREDIT_PACKS.get(pack_id, CREDIT_PACKS["standard"])
        
        # Send warning email
        try:
            await send_auto_refill_warning_email(
                email=user["email"],
                user_name=user.get("full_name", "User"),
                current_balance=current_balance,
                threshold=threshold,
                pack_name=pack["name"],
                pack_credits=pack["credits"],
                pack_price=pack["price_usd"]
            )
            
            # Record that we sent a warning
            await self.db.auto_refill_warnings.insert_one({
                "user_id": user_id,
                "balance_at_warning": current_balance,
                "threshold": threshold,
                "sent_at": datetime.now(timezone.utc).isoformat(),
            })
            
            logger.info(f"Sent low balance warning email to {user_id} (balance: {current_balance})")
            
            return {
                "warning_sent": True,
                "current_balance": current_balance,
                "threshold": threshold,
            }
            
        except Exception as e:
            logger.error(f"Failed to send low balance warning: {e}")
            return None
    
    async def process_auto_refill_payment(
        self,
        user_id: str,
        refill_id: str,
        payment_intent_id: str,
        success: bool
    ) -> Dict:
        """Process the result of an auto-refill payment"""
        now = datetime.now(timezone.utc)
        
        if success:
            # Get the refill record
            refill = await self.db.auto_refill_history.find_one(
                {"_id": refill_id, "user_id": user_id}
            )
            
            if refill:
                # Add credits to user account
                credits_to_add = refill.get("credits", 0)
                await self.add_credits(
                    user_id,
                    credits_to_add,
                    "auto_refill",
                    {"pack_id": refill.get("pack_id"), "payment_intent_id": payment_intent_id}
                )
                
                # Update refill status
                await self.db.auto_refill_history.update_one(
                    {"_id": refill_id},
                    {"$set": {
                        "status": "completed",
                        "payment_intent_id": payment_intent_id,
                        "completed_at": now.isoformat(),
                    }}
                )
                
                # Increment refills this month
                await self.db.auto_refill_settings.update_one(
                    {"user_id": user_id},
                    {
                        "$inc": {"refills_this_month": 1},
                        "$set": {"last_refill_at": now.isoformat()}
                    }
                )
                
                return {
                    "success": True,
                    "credits_added": credits_to_add,
                    "message": f"Auto-refill completed: {credits_to_add} credits added",
                }
        
        # Payment failed
        await self.db.auto_refill_history.update_one(
            {"_id": refill_id},
            {"$set": {
                "status": "failed",
                "payment_intent_id": payment_intent_id,
                "failed_at": now.isoformat(),
            }}
        )
        
        return {
            "success": False,
            "message": "Auto-refill payment failed",
        }
    
    async def get_auto_refill_history(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict]:
        """Get auto-refill history for a user"""
        history = await self.db.auto_refill_history.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return history
    
    async def reset_monthly_refill_count(self, user_id: str) -> None:
        """Reset the monthly refill counter (called at start of billing cycle)"""
        await self.db.auto_refill_settings.update_one(
            {"user_id": user_id},
            {"$set": {"refills_this_month": 0}}
        )


# Helper function to get credit service instance
def get_credit_service(db: AsyncIOMotorDatabase) -> CreditService:
    """Get a CreditService instance"""
    return CreditService(db)


# =============================================================================
# FASTAPI DEPENDENCY FOR CREDIT CONSUMPTION
# =============================================================================


async def consume_credits_dependency(
    action: CreditAction,
    quantity: int = 1
):
    """
    Factory function to create a FastAPI dependency for credit consumption.
    
    Usage:
        from services.credit_service import consume_credits_for, CreditAction
        
        @router.post("/content/generate")
        async def generate_content(
            ...,
            credits_consumed: dict = Depends(consume_credits_for(CreditAction.CONTENT_GENERATION))
        ):
            # Credits automatically consumed, or 402 raised if insufficient
            ...
    """
    async def _consume_credits(
        x_user_id: str = Header(..., alias="X-User-ID"),
        db_conn: AsyncIOMotorDatabase = Depends(get_db)
    ) -> Dict:
        """Consume credits for the specified action"""
        credit_service = CreditService(db_conn)
        
        success, result = await credit_service.consume_credits(
            user_id=x_user_id,
            action=action,
            quantity=quantity
        )
        
        if not success:
            raise HTTPException(
                status_code=402,  # Payment Required
                detail={
                    "error": "insufficient_credits",
                    "message": result.get("message", "Insufficient credits"),
                    "credits_required": result.get("credits_required", 0),
                    "credits_available": result.get("credits_available", 0),
                    "action": action.value,
                    "upgrade_url": "/pricing"
                }
            )
        
        return result
    
    return _consume_credits


def consume_credits_for(action: CreditAction, quantity: int = 1):
    """
    Create a FastAPI dependency that consumes credits for an action.
    
    Usage in route:
        @router.post("/content/generate")
        async def generate_content(
            data: dict,
            request: Request,
            x_user_id: str = Header(..., alias="X-User-ID"),
            db_conn: AsyncIOMotorDatabase = Depends(get_db),
            credits: dict = Depends(consume_credits_for(CreditAction.CONTENT_GENERATION))
        ):
            # Credits automatically consumed
            ...
    """
    async def _consume(
        x_user_id: str = Header(..., alias="X-User-ID"),
        db_conn: AsyncIOMotorDatabase = Depends(get_db)
    ) -> Dict:
        credit_service = CreditService(db_conn)
        
        success, result = await credit_service.consume_credits(
            user_id=x_user_id,
            action=action,
            quantity=quantity
        )
        
        if not success:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "insufficient_credits",
                    "message": result.get("message", "Insufficient credits for this action"),
                    "credits_required": result.get("credits_required", 0),
                    "credits_available": result.get("credits_available", 0),
                    "action": action.value,
                    "upgrade_url": "/pricing"
                }
            )
        
        return result
    
    return _consume


async def check_credits_for(
    action: CreditAction,
    quantity: int,
    user_id: str,
    db: AsyncIOMotorDatabase
) -> Tuple[bool, int, int]:
    """
    Utility function to check if user has enough credits without consuming.
    
    Returns: (has_enough, credits_required, credits_available)
    """
    credit_service = CreditService(db)
    return await credit_service.check_credits(user_id, action, quantity)


async def consume_credits_util(
    action: CreditAction,
    user_id: str,
    db: AsyncIOMotorDatabase,
    quantity: int = 1,
    metadata: Optional[Dict] = None,
    raise_on_insufficient: bool = True
) -> Tuple[bool, Dict]:
    """
    Utility function to consume credits programmatically.
    
    Use this when you need more control than the dependency provides,
    or when consuming credits outside of a route handler.
    
    Args:
        action: The credit action type
        user_id: The user ID
        db: Database connection
        quantity: Number of units (default 1)
        metadata: Optional metadata to store with transaction
        raise_on_insufficient: If True, raises HTTPException on insufficient credits
        
    Returns: (success, result_dict)
    """
    credit_service = CreditService(db)
    success, result = await credit_service.consume_credits(
        user_id=user_id,
        action=action,
        quantity=quantity,
        metadata=metadata
    )
    
    if not success and raise_on_insufficient:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "insufficient_credits",
                "message": result.get("message", "Insufficient credits for this action"),
                "credits_required": result.get("credits_required", 0),
                "credits_available": result.get("credits_available", 0),
                "action": action.value,
                "upgrade_url": "/pricing"
            }
        )
    
    return success, result


# Legacy decorator (kept for backward compatibility)
def require_credits(action: CreditAction, quantity: int = 1):
    """
    Decorator to automatically consume credits for an endpoint.
    
    NOTE: For new code, prefer using the consume_credits_for() dependency.
    This decorator is kept for backward compatibility.
    
    Example:
        @router.post("/analyze")
        @require_credits(CreditAction.CONTENT_ANALYSIS)
        async def analyze_content(...):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user_id and db from kwargs
            user_id = kwargs.get("user_id") or kwargs.get("x_user_id")
            db = kwargs.get("db") or kwargs.get("db_conn")
            
            if not user_id or not db:
                # Try to get from request
                request = kwargs.get("request")
                if request:
                    user_id = request.headers.get("X-User-ID")
            
            if user_id and db:
                credit_service = CreditService(db)
                success, result = await credit_service.consume_credits(
                    user_id, action, quantity
                )
                
                if not success:
                    raise HTTPException(
                        status_code=402,
                        detail={
                            "error": "insufficient_credits",
                            "message": result.get("message", "Insufficient credits"),
                            "credits_required": result.get("credits_required", 0),
                            "credits_available": result.get("credits_available", 0),
                            "action": action.value,
                            "upgrade_url": "/pricing"
                        }
                    )
                
                # Add credit info to kwargs for potential use
                kwargs["_credit_consumption"] = result
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
