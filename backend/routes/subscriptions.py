"""
Subscription and Payment Routes
Handles Stripe subscriptions and payment validation

SECURITY (ARCH-002): All webhook events and subscription operations use idempotency
protection with distributed locks to prevent:
- Double-charging customers from replay attacks
- Duplicate subscription activations
- Race conditions in payment processing

RBAC Protected: Phase 5.1b Week 5
All endpoints require appropriate settings.* or admin.* permissions
"""
from fastapi import APIRouter, HTTPException, Request, Depends, Header
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime, timezone
import os
import logging
import stripe
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db
# Import RBAC decorator
from services.authorization_decorator import require_permission

# Import idempotency service (ARCH-002)
from services.idempotency_service import (
    get_idempotency_service,
    init_idempotency_service,
    generate_idempotency_key,
    OperationType
)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])
logger = logging.getLogger(__name__)

# Database instance (set by main app)
db = None

# Cache for Stripe prices
_stripe_prices_cache = {}
_stripe_prices_cache_time = None
CACHE_TTL_SECONDS = 3600  # Cache for 1 hour

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    """Set the database instance for this router"""
    global db
    db = database
    # Initialize idempotency service with database connection
    init_idempotency_service(database)


async def fetch_stripe_prices() -> Dict:
    """Fetch current prices from Stripe for all products"""
    global _stripe_prices_cache, _stripe_prices_cache_time
    
    # Check cache
    if _stripe_prices_cache_time and (datetime.now(timezone.utc) - _stripe_prices_cache_time).seconds < CACHE_TTL_SECONDS:
        return _stripe_prices_cache
    
    stripe.api_key = os.environ.get("STRIPE_API_KEY")
    if not stripe.api_key:
        logger.warning("Stripe API key not configured, using fallback prices")
        return {}
    
    try:
        prices = {}
        
        # Fetch all active prices
        stripe_prices = stripe.Price.list(active=True, limit=100)
        
        for price in stripe_prices.data:
            price_id = price.id
            product_id = price.product
            
            # Get price amount in appropriate currency
            amount = price.unit_amount / 100 if price.unit_amount else 0
            currency = price.currency.upper()
            recurring = price.recurring
            interval = recurring.interval if recurring else "one_time"
            
            # Store by price ID
            prices[price_id] = {
                "price_id": price_id,
                "product_id": product_id,
                "amount": amount,
                "currency": currency,
                "interval": interval,
                "interval_count": recurring.interval_count if recurring else None,
            }
        
        _stripe_prices_cache = prices
        _stripe_prices_cache_time = datetime.now(timezone.utc)
        logger.info(f"Fetched {len(prices)} prices from Stripe")
        
        return prices
    except Exception as e:
        logger.error(f"Failed to fetch Stripe prices: {e}")
        return _stripe_prices_cache or {}


# Subscription packages v3.0 (server-side only - never from frontend!)
# Prices match Stripe setup - multi-regional pricing handled via Stripe Price IDs
# Updated January 2026 - Final Pricing Strategy v1.0
SUBSCRIPTION_PACKAGES = {
    "free": {
        "name": "Free Trial",
        "tagline": "14-day free trial",
        "price_monthly": 0,
        "price_annual": 0,
        "currency": "usd",
        "credits_monthly": 100,
        "trial_period_days": 14,
        "stripe_price_id_monthly": None,
        "stripe_price_id_annual": None,
        "features": [
            "100 credits for 14 days",
            "All features included",
            "Content analysis & generation",
            "AI rewrite & image generation",
            "Voice assistant",
            "1 strategic profile",
        ],
        "limits": {
            "team_members": 1,
            "strategic_profiles": 1,
        },
        "is_trial": True,
    },
    "starter": {
        "name": "Starter",
        "tagline": "For hobbyists",
        "price_monthly": 9.99,
        "price_annual": 95.90,  # 20% discount
        "currency": "usd",
        "credits_monthly": 400,
        "overage_rate": 0.055,
        "trial_period_days": 14,
        "stripe_price_id_monthly": os.getenv("STRIPE_PRICE_STARTER_MONTHLY"),
        "stripe_price_id_annual": os.getenv("STRIPE_PRICE_STARTER_ANNUAL"),
        "features": [
            "400 credits/month",
            "All features included",
            "1 strategic profile",
            "Email support (72h)",
        ],
        "limits": {
            "team_members": 1,
            "strategic_profiles": 1,
            "content_items_per_month": 500,
        }
    },
    "creator": {
        "name": "Creator",
        "tagline": "For individual creators",
        "price_monthly": 19.00,
        "price_annual": 182.40,  # 20% discount
        "currency": "usd",
        "credits_monthly": 750,
        "overage_rate": 0.05,
        "trial_period_days": 14,
        "stripe_price_id_monthly": os.getenv("STRIPE_PRICE_CREATOR_MONTHLY"),
        "stripe_price_id_annual": os.getenv("STRIPE_PRICE_CREATOR_ANNUAL"),
        "features": [
            "750 credits/month",
            "All features included",
            "3 strategic profiles",
            "Priority content analysis",
            "Email support (48h)",
        ],
        "limits": {
            "team_members": 1,
            "strategic_profiles": 3,
            "content_items_per_month": 500,
        },
        "popular": True,
    },
    "pro": {
        "name": "Pro",
        "tagline": "For power users",
        "price_monthly": 49.00,
        "price_annual": 470.40,  # 20% discount
        "currency": "usd",
        "credits_monthly": 1500,
        "overage_rate": 0.04,
        "trial_period_days": 0,  # No trial for Pro and above
        "stripe_price_id_monthly": os.getenv("STRIPE_PRICE_PRO_MONTHLY"),
        "stripe_price_id_annual": os.getenv("STRIPE_PRICE_PRO_ANNUAL"),
        "features": [
            "1,500 credits/month",
            "Everything in Creator",
            "Olivia Voice Agent",
            "API access (100 req/min)",
            "10 strategic profiles",
            "Priority support (24h)",
        ],
        "limits": {
            "team_members": 1,
            "strategic_profiles": 10,
            "content_items_per_month": 2000,
            "api_rate_limit": 100,
        }
    },
    "team": {
        "name": "Team",
        "tagline": "For small teams",
        "price_monthly": 249.00,
        "price_annual": 2390.40,  # 20% discount
        "currency": "usd",
        "credits_monthly": 5000,
        "overage_rate": 0.035,
        "trial_period_days": 0,
        "stripe_price_id_monthly": os.getenv("STRIPE_PRICE_TEAM_MONTHLY"),
        "stripe_price_id_annual": os.getenv("STRIPE_PRICE_TEAM_ANNUAL"),
        "features": [
            "5,000 credits/month",
            "Everything in Pro",
            "Up to 10 team members",
            "Approval workflows",
            "Shared credit pool",
            "Priority support (4h)",
        ],
        "limits": {
            "team_members": 10,
            "strategic_profiles": -1,  # Unlimited
            "content_items_per_month": 10000,
            "api_rate_limit": 500,
        }
    },
    "business": {
        "name": "Business",
        "tagline": "For growing businesses",
        "price_monthly": 499.00,
        "price_annual": 4790.40,  # 20% discount
        "currency": "usd",
        "credits_monthly": 15000,
        "overage_rate": 0.03,
        "trial_period_days": 0,
        "stripe_price_id_monthly": os.getenv("STRIPE_PRICE_BUSINESS_MONTHLY"),
        "stripe_price_id_annual": os.getenv("STRIPE_PRICE_BUSINESS_ANNUAL"),
        "features": [
            "15,000 credits/month",
            "Everything in Team",
            "Unlimited team members",
            "SSO (SAML/OAuth)",
            "Custom roles",
            "Dedicated CSM",
            "Priority support (2h)",
        ],
        "limits": {
            "team_members": -1,  # Unlimited
            "strategic_profiles": -1,
            "content_items_per_month": 50000,
            "api_rate_limit": 2000,
        }
    },
    "enterprise": {
        "name": "Enterprise",
        "tagline": "Custom solutions",
        "price_monthly": None,  # Custom pricing
        "price_annual": None,
        "currency": "usd",
        "credits_monthly": -1,  # Custom
        "overage_rate": 0.025,  # Volume discount
        "trial_period_days": 0,
        "stripe_price_id_monthly": None,  # Contact sales
        "stripe_price_id_annual": None,
        "features": [
            "Custom credits",
            "Everything in Business",
            "Custom integrations",
            "Dedicated support",
            "SLA guarantee",
            "24/7 support",
        ],
        "limits": {
            "team_members": -1,
            "strategic_profiles": -1,
            "content_items_per_month": -1,
            "api_rate_limit": -1,
        },
        "contact_sales": True,
    }
}


class CheckoutRequest(BaseModel):
    package_id: str
    origin_url: str
    user_id: Optional[str] = None
    billing_cycle: str = "monthly"  # monthly or annual


@router.get("/packages")
async def get_packages(request: Request):
    """Get available subscription packages with prices from Stripe - Public endpoint"""
    # Fetch current prices from Stripe
    stripe_prices = await fetch_stripe_prices()
    
    # Merge Stripe prices into packages
    packages_with_prices = {}
    for pkg_id, pkg in SUBSCRIPTION_PACKAGES.items():
        pkg_copy = dict(pkg)
        
        # Get price from Stripe if available
        monthly_price_id = pkg.get("stripe_price_id_monthly")
        annual_price_id = pkg.get("stripe_price_id_annual")
        
        if monthly_price_id and monthly_price_id in stripe_prices:
            pkg_copy["price_monthly"] = stripe_prices[monthly_price_id]["amount"]
            pkg_copy["currency"] = stripe_prices[monthly_price_id]["currency"].lower()
        
        if annual_price_id and annual_price_id in stripe_prices:
            pkg_copy["price_annual"] = stripe_prices[annual_price_id]["amount"]
        
        packages_with_prices[pkg_id] = pkg_copy
    
    return {"packages": packages_with_prices}


@router.post("/checkout")
@require_permission("settings.edit_billing")
async def create_checkout_session(request: Request, checkout_request: CheckoutRequest, db_conn: AsyncIOMotorDatabase = Depends(get_db), user_id: str = Header(None, alias="X-User-ID")):
    """
    Create Stripe checkout session for subscription
    Security: Amount is NEVER from frontend, always from server-side package definition
    
    Supports monthly and annual billing cycles with v3.0 pricing.
    """
    # Validate package
    if checkout_request.package_id not in SUBSCRIPTION_PACKAGES:
        raise HTTPException(400, f"Invalid package: {checkout_request.package_id}")
    
    package = SUBSCRIPTION_PACKAGES[checkout_request.package_id]
    
    # Enterprise requires contact sales
    if package.get("contact_sales"):
        raise HTTPException(400, "Enterprise plan requires contacting sales")
    
    # Free plan doesn't need checkout
    if checkout_request.package_id == "free":
        # Just update user plan directly
        if user_id or checkout_request.user_id:
            uid = user_id or checkout_request.user_id
            await db_conn.users.update_one(
                {"id": uid},
                {"$set": {
                    "subscription_plan": "free",
                    "subscription_status": "active",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            # Initialize credits for free plan
            from services.credit_service import get_credit_service
            credit_service = get_credit_service(db_conn)
            await credit_service._initialize_user_credits(uid, "free")
            
        return {
            "success": True,
            "message": "Free plan activated",
            "redirect": f"{checkout_request.origin_url}/contentry/settings/billing?plan=free"
        }
    
    # Get Stripe API key
    stripe_api_key = os.getenv("STRIPE_API_KEY")
    if not stripe_api_key:
        raise HTTPException(500, "Stripe not configured")
    
    # Build webhook URL
    webhook_url = f"{checkout_request.origin_url}/api/webhook/stripe"
    
    # Initialize Stripe
    stripe_checkout = StripeCheckout(
        api_key=stripe_api_key,
        webhook_url=webhook_url
    )
    
    # Build success and cancel URLs (dynamic from frontend origin)
    success_url = f"{checkout_request.origin_url}/contentry/settings/billing?purchase=success&plan={checkout_request.package_id}&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{checkout_request.origin_url}/contentry/subscription/cancel"
    
    # Get price based on billing cycle
    billing_cycle = checkout_request.billing_cycle or "monthly"
    if billing_cycle == "annual":
        stripe_price_id = package.get("stripe_price_id_annual")
        price = package.get("price_annual")
    else:
        stripe_price_id = package.get("stripe_price_id_monthly")
        price = package.get("price_monthly")
    
    # Prepare metadata
    metadata = {
        "package_id": checkout_request.package_id,
        "package_name": package["name"],
        "billing_cycle": billing_cycle,
        "credits_monthly": str(package.get("credits_monthly", 0)),
        "type": "subscription",
    }
    if checkout_request.user_id:
        metadata["user_id"] = checkout_request.user_id
    
    # Get trial period if applicable (per Stripe guide: set at subscription level)
    trial_period_days = package.get("trial_period_days", 0)
    
    try:
        # Create checkout session using Stripe directly for subscriptions
        if stripe_price_id:
            # Use Stripe directly for subscription mode
            stripe.api_key = stripe_api_key
            
            session_params = {
                "mode": "subscription",  # Subscription mode for recurring prices
                "payment_method_types": ["card"],
                "line_items": [{
                    "price": stripe_price_id,
                    "quantity": 1,
                }],
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": metadata,
            }
            
            # Add trial period if applicable
            if trial_period_days and trial_period_days > 0:
                session_params["subscription_data"] = {
                    "trial_period_days": trial_period_days
                }
            
            # Add customer email if available
            if checkout_request.user_id:
                user = await db_conn.users.find_one({"id": checkout_request.user_id})
                if user and user.get("email"):
                    session_params["customer_email"] = user["email"]
            
            session = stripe.checkout.Session.create(**session_params)
            session_id = session.id
            session_url = session.url
        else:
            # Custom amount - create using emergentintegrations
            session_request = CheckoutSessionRequest(
                amount=price,
                currency=package["currency"],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
                trial_period_days=trial_period_days if trial_period_days > 0 else None,
            )
            session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(session_request)
            session_id = session.session_id
            session_url = session.url
        
        # Store payment transaction in database (MANDATORY)
        transaction = {
            "session_id": session_id,
            "user_id": checkout_request.user_id,
            "package_id": checkout_request.package_id,
            "amount": price,
            "currency": package["currency"],
            "billing_cycle": billing_cycle,
            "trial_period_days": trial_period_days,
            "payment_status": "initiated",
            "status": "pending",
            "metadata": metadata,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db_conn.payment_transactions.insert_one(transaction)
        
        return {
            "url": session_url,
            "session_id": session_id
        }
        
    except Exception as e:
        logging.error(f"Stripe checkout error: {e}")
        raise HTTPException(500, f"Failed to create checkout session: {str(e)}")


@router.get("/checkout/status/{session_id}")
async def get_checkout_status(request: Request, session_id: str, db_conn: AsyncIOMotorDatabase = Depends(get_db), user_id: str = Header(None, alias="X-User-ID")):
    """
    Get checkout session status from Stripe
    Called by frontend to poll payment status
    
    SECURITY NOTE: This endpoint does NOT require authentication because:
    1. Users are redirected here from Stripe after payment
    2. The session_id acts as a secure, unguessable token from Stripe
    3. No sensitive data is exposed - only payment status
    """
    stripe_api_key = os.getenv("STRIPE_API_KEY")
    if not stripe_api_key:
        raise HTTPException(500, "Stripe not configured")
    
    # Initialize Stripe
    stripe_checkout = StripeCheckout(
        api_key=stripe_api_key,
        webhook_url="dummy"  # Not needed for status check
    )
    
    try:
        # Get status from Stripe
        status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
        
        # Update local transaction record (only if not already processed)
        transaction = await db_conn.payment_transactions.find_one(
            {"session_id": session_id},
            {"_id": 0}
        )
        
        if transaction and transaction["payment_status"] != "paid":
            # Update payment status
            update_data = {
                "payment_status": status.payment_status,
                "status": status.status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # If payment is complete, activate subscription
            if status.payment_status == "paid" and transaction.get("user_id"):
                user_id = transaction["user_id"]
                package_id = transaction.get("package_id", "basic")
                
                # Update user subscription
                await db_conn.users.update_one(
                    {"id": user_id},
                    {"$set": {
                        "subscription.plan": package_id,
                        "subscription.status": "active",
                        "subscription.stripe_customer_id": status.metadata.get("customer_id"),
                        "subscription.stripe_subscription_id": status.metadata.get("subscription_id"),
                        "subscription.current_period_start": datetime.now(timezone.utc).isoformat(),
                        "subscription.current_period_end": (datetime.now(timezone.utc).replace(day=1, month=datetime.now(timezone.utc).month + 1) if datetime.now(timezone.utc).month < 12 else datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year + 1, month=1, day=1)).isoformat()
                    }}
                )
                
                update_data["subscription_activated"] = True
            
            await db_conn.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
        
        return {
            "session_id": session_id,
            "status": status.status,
            "payment_status": status.payment_status,
            "amount_total": status.amount_total,
            "currency": status.currency,
            "metadata": status.metadata
        }
        
    except Exception as e:
        logging.error(f"Stripe status check error: {e}")
        raise HTTPException(500, f"Failed to check status: {str(e)}")


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Handle Stripe webhooks with proper signature verification and idempotency.
    
    SECURITY (ARCH-002 & ARCH-007):
    - Verifies webhook signature to prevent forged requests
    - Implements event deduplication to prevent replay attacks
    - Uses distributed locks to prevent race conditions
    - Logs all webhook attempts for audit trail
    
    Args:
        request: The incoming webhook request
        db_conn: Database connection (injected)
    
    Returns:
        Success response if webhook is valid and processed
        
    Raises:
        HTTPException 400: Invalid payload
        HTTPException 403: Invalid signature (security violation)
        HTTPException 409: Duplicate event (already processed)
        HTTPException 500: Processing error
    """
    import stripe
    
    # Initialize idempotency service
    from services.idempotency_service import IdempotencyService
    idempotency_service = IdempotencyService(db_conn)
    
    # Get configuration
    stripe_api_key = os.getenv("STRIPE_API_KEY")
    stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    if not stripe_api_key:
        logging.error("SECURITY: Stripe webhook received but STRIPE_API_KEY not configured")
        raise HTTPException(500, "Stripe not configured")
    
    # Initialize Stripe
    stripe.api_key = stripe_api_key
    
    # Get request details for logging
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")
    
    try:
        # Get raw body and signature
        payload = await request.body()
        sig_header = request.headers.get("Stripe-Signature")
        
        # Log webhook attempt
        logging.info(f"Stripe webhook received: IP={client_ip}, UA={user_agent[:50]}")
        
        # SECURITY: Verify signature if webhook secret is configured
        if stripe_webhook_secret:
            if not sig_header:
                logging.warning(f"SECURITY: Stripe webhook missing signature header from IP={client_ip}")
                raise HTTPException(403, "Missing Stripe signature")
            
            try:
                # Verify the webhook signature
                event = stripe.Webhook.construct_event(
                    payload,
                    sig_header,
                    stripe_webhook_secret
                )
                logging.info(f"Stripe webhook signature verified: event_id={event.get('id')}, type={event.get('type')}")
                
            except ValueError as e:
                # Invalid payload
                logging.error(f"SECURITY: Invalid Stripe webhook payload from IP={client_ip}: {str(e)}")
                raise HTTPException(400, "Invalid payload")
                
            except stripe.error.SignatureVerificationError as e:
                # Invalid signature - potential attack
                logging.error(f"SECURITY ALERT: Invalid Stripe webhook signature from IP={client_ip}: {str(e)}")
                raise HTTPException(403, "Invalid signature - request rejected")
        else:
            # No webhook secret configured - parse payload without verification
            # This is less secure but allows webhook processing during development
            logging.warning("SECURITY: STRIPE_WEBHOOK_SECRET not configured - webhook signature not verified")
            import json
            try:
                event = json.loads(payload)
            except (json.JSONDecodeError, ValueError) as e:
                logging.error(f"SECURITY: Invalid JSON payload from IP={client_ip}: {str(e)}")
                raise HTTPException(400, "Invalid payload")
        
        # Extract event details
        event_id = event.get("id")
        event_type = event.get("type")
        event_data = event.get("data", {}).get("object", {})
        
        # SECURITY (ARCH-002): ATOMIC check-and-lock for webhook deduplication
        # This prevents the race condition where two webhooks both check "not processed"
        # before either writes. Uses MongoDB's findOneAndUpdate with upsert.
        should_process, previous_result = await idempotency_service.check_and_lock_webhook(
            event_id=event_id,
            event_type=event_type,
            metadata={"source_ip": client_ip}
        )
        
        if not should_process:
            logging.warning(f"IDEMPOTENCY ATOMIC: Duplicate Stripe webhook event ignored: event_id={event_id}, type={event_type}")
            # Return 200 to acknowledge (Stripe expects this) but don't process again
            return {"success": True, "message": "Event already processed", "duplicate": True}
        
        # At this point, we have atomically acquired the lock for this event_id
        # No other request can process this event
        try:
            # Process webhook based on event type
            processing_result = await _process_stripe_event(event_type, event_data, db_conn, idempotency_service)
            
            # Record webhook as processed using idempotency service
            await idempotency_service.record_webhook_event(
                event_id=event_id,
                event_type=event_type,
                processed=True,
                result=processing_result,
                metadata={"source_ip": client_ip}
            )
            
            logging.info(f"IDEMPOTENCY ATOMIC: Stripe webhook processed successfully: event_id={event_id}, type={event_type}")
            return {"success": True, "event_id": event_id, "event_type": event_type}
            
        except Exception as e:
            # Record failed processing
            await idempotency_service.record_webhook_event(
                event_id=event_id,
                event_type=event_type,
                processed=False,
                error=str(e),
                metadata={"source_ip": client_ip}
            )
            raise
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Stripe webhook processing error: {str(e)}")
        raise HTTPException(500, f"Webhook processing failed: {str(e)}")


async def _process_stripe_event(event_type: str, event_data: dict, db_conn: AsyncIOMotorDatabase, idempotency_service) -> dict:
    """
    Process different Stripe webhook event types with idempotency protection.
    
    SECURITY (ARCH-002): All credit grants and subscription activations use
    idempotency to prevent duplicate financial operations.
    
    Args:
        event_type: The Stripe event type
        event_data: The event data object
        db_conn: Database connection
        idempotency_service: Idempotency service instance
        
    Returns:
        dict with processing result details
    """
    result = {"action": None, "details": None}
    
    if event_type == "checkout.session.completed":
        # Payment successful
        session_id = event_data.get("id")
        customer_id = event_data.get("customer")
        subscription_id = event_data.get("subscription")
        payment_status = event_data.get("payment_status")
        customer_email = event_data.get("customer_email") or event_data.get("customer_details", {}).get("email")  # noqa: F841
        metadata = event_data.get("metadata", {})
        
        # Generate idempotency key for this fulfillment
        fulfillment_key = f"fulfill_webhook_{session_id}"
        
        # Use distributed lock to prevent race conditions
        async with idempotency_service.get_lock(fulfillment_key):
            # Update payment transaction
            await db_conn.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {
                    "payment_status": payment_status,
                    "stripe_customer_id": customer_id,
                    "stripe_subscription_id": subscription_id,
                    "webhook_received": True,
                    "webhook_event_type": event_type,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Get the transaction to find user_id
            transaction = await db_conn.payment_transactions.find_one({"session_id": session_id})
            if transaction and transaction.get("user_id"):
                user_id = transaction["user_id"]
                payment_type = metadata.get("type") or transaction.get("type")
                credits = int(metadata.get("credits", 0) or transaction.get("credits", 0))
                
                # Handle credit purchase with idempotency
                if payment_type == "credit_purchase" and credits > 0:
                    credit_key = generate_idempotency_key(
                        OperationType.CREDIT_GRANT,
                        user_id,
                        {"session_id": session_id, "credits": credits}
                    )
                    
                    success, new_balance, error = await idempotency_service.grant_credits_idempotent(
                        user_id=user_id,
                        credits=credits,
                        reason=f"Webhook credit grant (session: {session_id})",
                        idempotency_key=credit_key,
                        source_event_id=session_id
                    )
                    
                    if success:
                        logging.info(f"IDEMPOTENCY: Webhook granted {credits} credits to {user_id}")
                    else:
                        logging.info(f"IDEMPOTENCY: Credit grant skipped for {user_id}: {error}")
                
                # Handle subscription with idempotency
                elif payment_type == "subscription":
                    sub_key = generate_idempotency_key(
                        OperationType.SUBSCRIPTION_CREATE,
                        user_id,
                        {"session_id": session_id}
                    )
                    
                    should_proceed, _, _ = await idempotency_service.start_payment_operation(
                        idempotency_key=sub_key,
                        operation_type=OperationType.SUBSCRIPTION_CREATE,
                        user_id=user_id,
                        request_data={"session_id": session_id}
                    )
                    
                    if should_proceed:
                        await db_conn.users.update_one(
                            {"id": user_id},
                            {"$set": {
                                "subscription.status": "active",
                                "subscription.stripe_customer_id": customer_id,
                                "subscription.stripe_subscription_id": subscription_id,
                                "subscription.activated_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                        
                        # Grant subscription credits
                        if credits > 0:
                            credit_key = generate_idempotency_key(
                                OperationType.CREDIT_GRANT,
                                user_id,
                                {"session_id": session_id, "type": "subscription", "credits": credits}
                            )
                            await idempotency_service.grant_credits_idempotent(
                                user_id=user_id,
                                credits=credits,
                                reason=f"Subscription activation (session: {session_id})",
                                idempotency_key=credit_key,
                                source_event_id=session_id
                            )
                        
                        await idempotency_service.complete_payment_operation(sub_key, {"status": "active"}, success=True)
                        logging.info(f"IDEMPOTENCY: Webhook activated subscription for {user_id}")
                    else:
                        logging.info(f"IDEMPOTENCY: Subscription already activated for {user_id}")
                
                else:
                    # Legacy subscription activation
                    await db_conn.users.update_one(
                        {"id": user_id},
                        {"$set": {
                            "subscription.status": "active",
                            "subscription.stripe_customer_id": customer_id,
                            "subscription.stripe_subscription_id": subscription_id,
                            "subscription.activated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
        
        result = {
            "action": "subscription_activated",
            "details": {
                "session_id": session_id,
                "customer_id": customer_id,
                "payment_status": payment_status
            }
        }
        
    elif event_type == "customer.subscription.created":
        subscription_id = event_data.get("id")
        customer_id = event_data.get("customer")
        status = event_data.get("status")
        
        logging.info(f"Subscription created: subscription_id={subscription_id}, customer_id={customer_id}")
        result = {"action": "subscription_created", "details": {"subscription_id": subscription_id, "status": status}}
        
    elif event_type == "customer.subscription.updated":
        subscription_id = event_data.get("id")
        customer_id = event_data.get("customer")
        status = event_data.get("status")
        cancel_at_period_end = event_data.get("cancel_at_period_end", False)
        
        # Update user subscription status
        await db_conn.users.update_one(
            {"subscription.stripe_subscription_id": subscription_id},
            {"$set": {
                "subscription.status": status,
                "subscription.cancel_at_period_end": cancel_at_period_end,
                "subscription.updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        result = {"action": "subscription_updated", "details": {"subscription_id": subscription_id, "status": status}}
        
    elif event_type == "customer.subscription.deleted":
        subscription_id = event_data.get("id")
        customer_id = event_data.get("customer")
        
        # Mark subscription as cancelled
        await db_conn.users.update_one(
            {"subscription.stripe_subscription_id": subscription_id},
            {"$set": {
                "subscription.status": "cancelled",
                "subscription.cancelled_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logging.info(f"Subscription cancelled: subscription_id={subscription_id}")
        result = {"action": "subscription_cancelled", "details": {"subscription_id": subscription_id}}
        
    elif event_type == "invoice.payment_succeeded":
        invoice_id = event_data.get("id")
        subscription_id = event_data.get("subscription")
        amount_paid = event_data.get("amount_paid", 0) / 100  # Convert from cents
        
        logging.info(f"Invoice paid: invoice_id={invoice_id}, amount=${amount_paid}")
        result = {"action": "invoice_paid", "details": {"invoice_id": invoice_id, "amount": amount_paid}}
        
    elif event_type == "invoice.payment_failed":
        invoice_id = event_data.get("id")
        subscription_id = event_data.get("subscription")
        
        # Update subscription status to past_due
        await db_conn.users.update_one(
            {"subscription.stripe_subscription_id": subscription_id},
            {"$set": {
                "subscription.status": "past_due",
                "subscription.payment_failed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logging.warning(f"Invoice payment failed: invoice_id={invoice_id}, subscription_id={subscription_id}")
        result = {"action": "payment_failed", "details": {"invoice_id": invoice_id, "subscription_id": subscription_id}}
        
    else:
        # Unhandled event type - log but don't error
        logging.info(f"Unhandled Stripe event type: {event_type}")
        result = {"action": "unhandled", "details": {"event_type": event_type}}
    
    return result


@router.get("/user/{user_id}")
@require_permission("settings.view")
async def get_user_subscription(request: Request, user_id: str, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Get user's subscription details"""
    user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(404, "User not found")
    
    subscription = user.get("subscription", {})
    return {
        "user_id": user_id,
        "subscription": subscription,
        "has_active_subscription": subscription.get("status") in ["active", "trialing"]
    }


@router.post("/cancel/{user_id}")
@require_permission("settings.edit_billing")
async def cancel_subscription(request: Request, user_id: str, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Cancel user subscription (admin only)"""
    
    await db_conn.users.update_one(
        {"id": user_id},
        {"$set": {
            "subscription.status": "cancelled",
            "subscription.cancelled_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"success": True, "message": "Subscription cancelled"}
