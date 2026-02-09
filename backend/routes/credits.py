"""
Credit Routes for Contentry.ai
Handles credit balance, consumption history, and credit pack purchases.

API Endpoints:
- GET /credits/balance - Get current credit balance and plan info
- GET /credits/history - Get credit transaction history
- GET /credits/usage - Get usage summary
- GET /credits/packs - Get available credit packs
- POST /credits/purchase - Purchase a credit pack
- GET /credits/costs - Get credit costs for all actions
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Header, Query
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime, timezone
import os
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db
# Import RBAC decorator
from services.authorization_decorator import require_permission
# Import credit service
from services.credit_service import (
    CreditService,
    CreditAction,
    CREDIT_COSTS,
    CREDIT_PACKS,
    PLAN_CONFIGS,
    PlanTier,
    get_credit_service,
)
# Import caching
from middleware.api_cache import cached_response, invalidate_user_cache

# Stripe integration
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
)

router = APIRouter(prefix="/credits", tags=["credits"])
logger = logging.getLogger(__name__)


class CreditPackPurchaseRequest(BaseModel):
    pack_id: str
    origin_url: str
    currency: str = "USD"
    region: Optional[str] = None


class CreditConsumptionRequest(BaseModel):
    action: str
    quantity: int = 1
    metadata: Optional[Dict] = None


@router.get("/balance")
@require_permission("settings.view")
async def get_credit_balance(
    request: Request,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get user's current credit balance and plan information.
    
    Returns:
    - credits_balance: Current available credits
    - credits_used_this_month: Credits consumed this billing cycle
    - monthly_allowance: Credits included in plan
    - plan: Current plan tier
    - billing_cycle_start/end: Current billing cycle dates
    - features: Available features for this plan
    - limits: Plan limits (profiles, team members, etc.)
    """
    credit_service = get_credit_service(db_conn)
    credits = await credit_service.get_user_credits(x_user_id)
    
    return {
        "success": True,
        "data": credits
    }


@router.get("/history")
@require_permission("settings.view")
async def get_credit_history(
    request: Request,
    x_user_id: str = Header(..., alias="X-User-ID"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    action: Optional[str] = Query(None, description="Filter by action type"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get user's credit transaction history.
    
    Query params:
    - limit: Max records to return (1-100, default 50)
    - skip: Records to skip for pagination
    - action: Filter by action type (e.g., "content_analysis", "content_generation")
    """
    credit_service = get_credit_service(db_conn)
    transactions = await credit_service.get_credit_history(
        x_user_id, limit, skip, action
    )
    
    return {
        "success": True,
        "data": {
            "transactions": transactions,
            "limit": limit,
            "skip": skip,
            "count": len(transactions),
        }
    }


@router.get("/usage")
@require_permission("settings.view")
async def get_usage_summary(
    request: Request,
    x_user_id: str = Header(..., alias="X-User-ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get credit usage summary for the specified period.
    
    Returns:
    - total_credits_used: Total credits consumed in period
    - usage_by_action: Breakdown by action type
    - daily_usage: Daily usage for charts
    """
    credit_service = get_credit_service(db_conn)
    summary = await credit_service.get_usage_summary(x_user_id, days)
    
    return {
        "success": True,
        "data": summary
    }


import stripe

# Cache for Stripe credit pack prices
_stripe_pack_price_cache = {}
_stripe_pack_price_cache_time = None
STRIPE_PACK_CACHE_TTL = 300  # 5 minutes


async def fetch_stripe_pack_prices():
    """Fetch credit pack prices from Stripe"""
    global _stripe_pack_price_cache, _stripe_pack_price_cache_time
    
    # Check cache
    if _stripe_pack_price_cache_time:
        cache_age = (datetime.now(timezone.utc) - _stripe_pack_price_cache_time).total_seconds()
        if cache_age < STRIPE_PACK_CACHE_TTL:
            return _stripe_pack_price_cache
    
    stripe.api_key = os.environ.get("STRIPE_API_KEY")
    if not stripe.api_key:
        logger.warning("Stripe API key not configured for credit packs")
        return {}
    
    try:
        prices = {}
        # Fetch prices for each pack
        for pack_id, pack in CREDIT_PACKS.items():
            stripe_price_id = pack.get("stripe_price_id")
            if stripe_price_id:
                try:
                    price = stripe.Price.retrieve(stripe_price_id)
                    prices[pack_id] = {
                        "amount": price.unit_amount / 100 if price.unit_amount else 0,
                        "currency": price.currency.upper(),
                    }
                except Exception as e:
                    logger.warning(f"Could not fetch Stripe price for pack {pack_id}: {e}")
        
        _stripe_pack_price_cache = prices
        _stripe_pack_price_cache_time = datetime.now(timezone.utc)
        logger.info(f"Fetched {len(prices)} credit pack prices from Stripe")
        return prices
        
    except Exception as e:
        logger.error(f"Failed to fetch Stripe credit pack prices: {e}")
        return _stripe_pack_price_cache or {}


@router.get("/packs")
@cached_response(ttl=300, key_prefix="packs", vary_on=["currency"], skip_user_specific=True)
async def get_credit_packs(
    request: Request,
    currency: str = Query("USD", description="Currency code for pricing"),
):
    """
    Get available credit packs for purchase.
    
    Prices are fetched from Stripe (single source of truth).
    Returns list of credit packs with pricing in specified currency.
    """
    # Fetch prices from Stripe
    stripe_prices = await fetch_stripe_pack_prices()
    
    # Currency symbols
    currency_symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "NOK": "kr",
    }
    
    packs = []
    for pack_id, pack in CREDIT_PACKS.items():
        # Get price from Stripe, fallback to hardcoded
        stripe_data = stripe_prices.get(pack_id, {})
        price = stripe_data.get("amount", pack["price_usd"])
        pack_currency = stripe_data.get("currency", "USD")
        
        # Calculate per-credit rate and savings
        per_credit_rate = round(price / pack["credits"], 4) if pack["credits"] > 0 else 0
        
        # Calculate savings compared to base rate ($0.06/credit)
        base_rate = 0.06
        savings_percent = round((1 - (per_credit_rate / base_rate)) * 100) if per_credit_rate < base_rate else 0
        
        packs.append({
            "id": pack_id,
            "name": pack["name"],
            "credits": pack["credits"],
            "price": price,
            "currency": pack_currency,
            "currency_symbol": currency_symbols.get(pack_currency, "$"),
            "price_usd": price if pack_currency == "USD" else pack["price_usd"],
            "per_credit_rate": per_credit_rate,
            "savings_percent": max(0, savings_percent),
            "source": "stripe" if stripe_data else "fallback",
        })
    
    # Sort by credits ascending
    packs.sort(key=lambda x: x["credits"])
    
    return {
        "success": True,
        "data": {
            "packs": packs,
            "currency": packs[0]["currency"] if packs else "USD",
            "source": "stripe" if stripe_prices else "fallback",
        }
    }


@router.get("/costs")
@cached_response(ttl=86400, key_prefix="credit_costs", skip_user_specific=True)
async def get_credit_costs(request: Request):
    """
    Get credit costs for all actions.
    
    Returns a dictionary of action -> credit cost.
    """
    costs = {
        action.value: cost 
        for action, cost in CREDIT_COSTS.items()
    }
    
    # Group by category for frontend display
    categorized = {
        "core_content": {
            "content_analysis": {"cost": 5, "description": "Full compliance, cultural, and accuracy analysis"},
            "quick_analysis": {"cost": 2, "description": "Basic compliance check only"},
            "content_generation": {"cost": 10, "description": "AI-powered content creation"},
            "ai_rewrite": {"cost": 8, "description": "Compliance-focused content improvement"},
            "iterative_rewrite": {"cost": 15, "description": "Multiple passes until score >= 80"},
        },
        "image_media": {
            "image_generation": {"cost": 20, "description": "OpenAI/Gemini image generation"},
            "image_analysis": {"cost": 5, "description": "Safety and brand compliance check"},
            "image_regeneration": {"cost": 15, "description": "Regenerate with feedback"},
        },
        "voice_audio": {
            "voice_dictation": {"cost": 3, "description": "Speech-to-text (per minute)"},
            "voice_commands": {"cost": 5, "description": "Voice-activated content actions"},
            "ai_voice_assistant": {"cost": 10, "description": "Olivia AI (per interaction)"},
            "voice_content_generation": {"cost": 15, "description": "Generate content via voice"},
        },
        "sentiment_analysis": {
            "url_sentiment_analysis": {"cost": 8, "description": "Analyze external content sentiment"},
            "brand_mention_tracking": {"cost": 5, "description": "Track brand sentiment (per query)"},
            "competitor_analysis": {"cost": 12, "description": "Comparative sentiment analysis"},
        },
        "publishing": {
            "direct_publish": {"cost": 2, "description": "Publish to social media (per platform)"},
            "scheduled_post": {"cost": 3, "description": "Schedule future posts (per platform)"},
            "pre_publish_reanalysis": {"cost": 3, "description": "Automatic compliance check before publish"},
        },
        "advanced": {
            "knowledge_base_upload": {"cost": 5, "description": "Upload brand guidelines (per document)"},
            "strategic_profile_creation": {"cost": 10, "description": "Create new brand profile"},
            "export_to_pdf": {"cost": 1, "description": "Export analysis reports"},
        },
        "free_actions": {
            "approval_workflow": {"cost": 0, "description": "Submit for team approval"},
        }
    }
    
    return {
        "success": True,
        "data": {
            "costs": costs,
            "categorized": categorized,
        }
    }


@router.get("/plans")
@cached_response(ttl=86400, key_prefix="plans", skip_user_specific=True)
async def get_subscription_plans(request: Request):
    """
    Get all available subscription plans with features and limits.
    """
    plans = []
    for tier, config in PLAN_CONFIGS.items():
        plans.append({
            "id": tier.value,
            "name": config["name"],
            "monthly_credits": config["monthly_credits"],
            "overage_rate": config["overage_rate"],
            "features": config["features"],
            "limits": config["limits"],
        })
    
    return {
        "success": True,
        "data": {"plans": plans}
    }


@router.post("/purchase")
@require_permission("settings.edit_billing")
async def purchase_credit_pack(
    request: Request,
    purchase_request: CreditPackPurchaseRequest,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Purchase a credit pack via Stripe checkout.
    
    Returns Stripe checkout URL to redirect user.
    """
    # Validate pack
    pack = CREDIT_PACKS.get(purchase_request.pack_id)
    if not pack:
        raise HTTPException(400, f"Invalid pack ID: {purchase_request.pack_id}")
    
    # Get Stripe API key
    stripe_api_key = os.getenv("STRIPE_API_KEY")
    if not stripe_api_key:
        raise HTTPException(500, "Stripe not configured")
    
    # Get Stripe price ID for this pack (from env or use custom amount)
    stripe_price_id = os.getenv(f"STRIPE_CREDIT_PACK_{purchase_request.pack_id.upper()}_PRICE_ID")
    
    # Build success and cancel URLs
    success_url = f"{purchase_request.origin_url}/contentry/settings/billing?purchase=success&pack={purchase_request.pack_id}&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{purchase_request.origin_url}/contentry/settings/billing?purchase=cancelled"
    
    # Metadata for webhook processing
    metadata = {
        "type": "credit_pack",
        "pack_id": purchase_request.pack_id,
        "credits": str(pack["credits"]),
        "user_id": x_user_id,
    }
    
    try:
        # Initialize Stripe
        webhook_url = f"{purchase_request.origin_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(
            api_key=stripe_api_key,
            webhook_url=webhook_url
        )
        
        # Create checkout session
        if stripe_price_id:
            checkout_request = CheckoutSessionRequest(
                stripe_price_id=stripe_price_id,
                quantity=1,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
                mode="payment",  # One-time payment, not subscription
            )
        else:
            # Use custom amount if no price ID configured
            checkout_request = CheckoutSessionRequest(
                amount=pack["price_usd"],
                currency="usd",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
                mode="payment",
            )
        
        session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(
            checkout_request
        )
        
        # Store pending transaction
        transaction = {
            "session_id": session.session_id,
            "user_id": x_user_id,
            "type": "credit_pack",
            "pack_id": purchase_request.pack_id,
            "credits": pack["credits"],
            "amount": pack["price_usd"],
            "currency": "usd",
            "status": "pending",
            "metadata": metadata,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        await db_conn.credit_purchases.insert_one(transaction)
        
        logger.info(f"Created credit pack checkout session for user {x_user_id}: {session.session_id}")
        
        return {
            "success": True,
            "data": {
                "checkout_url": session.url,
                "session_id": session.session_id,
            }
        }
        
    except Exception as e:
        logger.error(f"Credit pack checkout error: {e}")
        raise HTTPException(500, f"Failed to create checkout session: {str(e)}")


@router.post("/consume")
@require_permission("content.create")
async def consume_credits(
    request: Request,
    consumption_request: CreditConsumptionRequest,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Internal endpoint to consume credits for an action.
    
    Note: This is typically called internally by other routes,
    but exposed for testing and manual consumption.
    """
    try:
        action = CreditAction(consumption_request.action)
    except ValueError:
        raise HTTPException(400, f"Invalid action: {consumption_request.action}")
    
    credit_service = get_credit_service(db_conn)
    success, result = await credit_service.consume_credits(
        x_user_id,
        action,
        consumption_request.quantity,
        consumption_request.metadata
    )
    
    if not success:
        raise HTTPException(402, result)  # 402 Payment Required
    
    return {
        "success": True,
        "data": result
    }


@router.get("/check/{action}")
@require_permission("settings.view")
async def check_credits_available(
    request: Request,
    action: str,
    x_user_id: str = Header(..., alias="X-User-ID"),
    quantity: int = Query(1, ge=1),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Check if user has enough credits for an action (without consuming).
    
    Useful for UI to show warnings before expensive operations.
    """
    try:
        credit_action = CreditAction(action)
    except ValueError:
        raise HTTPException(400, f"Invalid action: {action}")
    
    credit_service = get_credit_service(db_conn)
    has_enough, credits_required, credits_available = await credit_service.check_credits(
        x_user_id, credit_action, quantity
    )
    
    return {
        "success": True,
        "data": {
            "has_enough": has_enough,
            "credits_required": credits_required,
            "credits_available": credits_available,
            "action": action,
            "quantity": quantity,
        }
    }


# Webhook handler for credit pack purchases
async def handle_credit_pack_purchase(
    session_id: str,
    user_id: str,
    pack_id: str,
    credits: int,
    db: AsyncIOMotorDatabase
):
    """
    Process successful credit pack purchase.
    Called from Stripe webhook handler.
    """
    # Update purchase record
    await db.credit_purchases.update_one(
        {"session_id": session_id},
        {"$set": {
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    
    # Add credits to user account
    credit_service = get_credit_service(db)
    await credit_service.add_credits(
        user_id,
        credits,
        f"Credit pack purchase: {pack_id}",
        metadata={"session_id": session_id, "pack_id": pack_id}
    )
    
    logger.info(f"Processed credit pack purchase for user {user_id}: {credits} credits")


# =============================================================================
# AUTO-REFILL ENDPOINTS
# =============================================================================

class AutoRefillSettingsRequest(BaseModel):
    """Request model for updating auto-refill settings"""
    enabled: bool
    threshold_credits: int = 100
    refill_pack_id: str = "standard"
    max_refills_per_month: int = 3
    payment_method_id: Optional[str] = None


@router.get("/auto-refill/settings")
@require_permission("settings.view")
async def get_auto_refill_settings(
    request: Request,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get user's auto-refill configuration.
    
    Returns:
    - enabled: Whether auto-refill is active
    - threshold_credits: Credit balance that triggers refill
    - refill_pack_id: Which credit pack to purchase
    - max_refills_per_month: Safety limit on monthly auto-refills
    - refills_this_month: Number of auto-refills triggered this month
    - payment_method_id: Saved payment method for charging
    - last_refill_at: Last auto-refill timestamp
    """
    credit_service = get_credit_service(db_conn)
    settings = await credit_service.get_auto_refill_settings(x_user_id)
    
    # Add pack details for display
    pack_id = settings.get("refill_pack_id", "standard")
    pack = CREDIT_PACKS.get(pack_id, CREDIT_PACKS["standard"])
    
    return {
        "success": True,
        "data": {
            **settings,
            "pack_details": {
                "id": pack_id,
                "name": pack["name"],
                "credits": pack["credits"],
                "price_usd": pack["price_usd"],
                "per_credit_rate": pack["per_credit_rate"],
            }
        }
    }


@router.put("/auto-refill/settings")
@require_permission("settings.edit_billing")
async def update_auto_refill_settings(
    request: Request,
    settings_request: AutoRefillSettingsRequest,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Update user's auto-refill configuration.
    
    Settings:
    - enabled: Turn auto-refill on/off
    - threshold_credits: Trigger refill when balance drops below this (min: 10, max: 5000)
    - refill_pack_id: Credit pack to purchase (starter, standard, growth, scale)
    - max_refills_per_month: Safety limit (1-10 per month)
    - payment_method_id: Stripe payment method ID (optional, uses default if not set)
    
    Note: Auto-refill requires an active subscription (Creator plan or higher).
    """
    # Validate pack exists
    if settings_request.refill_pack_id not in CREDIT_PACKS:
        raise HTTPException(400, f"Invalid pack ID. Available: {list(CREDIT_PACKS.keys())}")
    
    credit_service = get_credit_service(db_conn)
    
    try:
        settings = await credit_service.update_auto_refill_settings(
            user_id=x_user_id,
            enabled=settings_request.enabled,
            threshold_credits=settings_request.threshold_credits,
            refill_pack_id=settings_request.refill_pack_id,
            max_refills_per_month=settings_request.max_refills_per_month,
            payment_method_id=settings_request.payment_method_id
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    
    # Add pack details for display
    pack = CREDIT_PACKS.get(settings_request.refill_pack_id)
    
    # Invalidate cache
    invalidate_user_cache(x_user_id)
    
    return {
        "success": True,
        "message": f"Auto-refill {'enabled' if settings_request.enabled else 'disabled'} successfully",
        "data": {
            **settings,
            "pack_details": {
                "id": settings_request.refill_pack_id,
                "name": pack["name"],
                "credits": pack["credits"],
                "price_usd": pack["price_usd"],
            }
        }
    }


@router.get("/auto-refill/history")
@require_permission("settings.view")
async def get_auto_refill_history(
    request: Request,
    x_user_id: str = Header(..., alias="X-User-ID"),
    limit: int = Query(20, ge=1, le=100),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get auto-refill transaction history.
    
    Shows past auto-refill triggers with status (pending, completed, failed).
    """
    credit_service = get_credit_service(db_conn)
    history = await credit_service.get_auto_refill_history(x_user_id, limit)
    
    return {
        "success": True,
        "data": {
            "history": history,
            "count": len(history),
        }
    }


@router.post("/auto-refill/trigger")
@require_permission("settings.edit_billing")
async def trigger_auto_refill_check(
    request: Request,
    x_user_id: str = Header(..., alias="X-User-ID"),
    force_charge: bool = Query(False, description="If True, attempt to charge via Stripe immediately"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Manually trigger an auto-refill check.
    
    This checks if the user's credit balance is below the threshold
    and triggers a refill if auto-refill is enabled.
    
    Query params:
    - force_charge: If True, actually process payment via Stripe
    
    Primarily used for testing or when user wants to force a refill.
    """
    credit_service = get_credit_service(db_conn)
    result = await credit_service.check_and_trigger_auto_refill(x_user_id, force_charge=force_charge)
    
    if result is None:
        # Get current settings and balance for response
        settings = await credit_service.get_auto_refill_settings(x_user_id)
        credits = await credit_service.get_user_credits(x_user_id)
        
        return {
            "success": True,
            "triggered": False,
            "message": "Auto-refill not triggered",
            "reason": "disabled" if not settings.get("enabled") else "above_threshold",
            "data": {
                "current_balance": credits.get("credits_balance", 0),
                "threshold": settings.get("threshold_credits", 100),
                "enabled": settings.get("enabled", False),
            }
        }
    
    return {
        "success": True,
        **result
    }


@router.post("/auto-refill/check-warning")
@require_permission("settings.view_billing")
async def check_low_balance_warning(
    request: Request,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Check if user's balance is low and send warning email if needed.
    
    This sends a warning email when balance is between threshold and 2x threshold.
    Only sends one warning per 24 hours.
    """
    credit_service = get_credit_service(db_conn)
    result = await credit_service.check_low_balance_warning(x_user_id)
    
    if result is None:
        return {
            "success": True,
            "warning_sent": False,
            "message": "No warning needed or auto-refill not enabled"
        }
    
    return {
        "success": True,
        **result
    }


@router.get("/auto-refill/packs")
async def get_auto_refill_packs(request: Request):
    """
    Get available credit packs for auto-refill configuration.
    
    Returns all available packs with pricing info for the auto-refill dropdown.
    """
    packs = []
    for pack_id, pack in CREDIT_PACKS.items():
        packs.append({
            "id": pack_id,
            "name": pack["name"],
            "credits": pack["credits"],
            "price_usd": pack["price_usd"],
            "per_credit_rate": pack["per_credit_rate"],
            "savings_percent": pack["savings_percent"],
        })
    
    return {
        "success": True,
        "data": {
            "packs": sorted(packs, key=lambda x: x["credits"]),
        }
    }
