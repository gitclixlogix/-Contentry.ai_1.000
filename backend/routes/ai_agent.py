"""
AI Content Agent Routes
API endpoints for the Master AI Content Agent

RBAC Protected: Phase 5.1c Week 7
All endpoints require appropriate content.* permissions
"""

from fastapi import APIRouter, HTTPException, Header, Depends, Request
from typing import Optional, List
import logging
from datetime import datetime, timezone, timedelta
from services.ai_content_agent import (
    get_content_agent, 
    TaskType, 
    ModelTier,
    MODEL_CONFIG
)
from services.usage_tracking import get_usage_tracker
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db
# ARCH-005: Authorization decorator
from services.authorization_decorator import require_permission

router = APIRouter(prefix="/agent", tags=["ai-agent"])
logger = logging.getLogger(__name__)

db = None

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    global db
    db = database


@router.post("/generate")
@require_permission("content.create")
async def agent_generate_content(request: Request, data: dict, x_user_id: str = Header(..., alias="X-User-ID"), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Generate content using the AI Content Agent with intelligent model selection.
    
    The agent automatically selects the optimal model based on:
    - Task complexity
    - Content requirements
    - Cost optimization
    
    New Pipeline (January 2026):
    1. Domain Classification (nano)
    2. Compliance Requirements Check (mini) 
    3. Content Generation with Constraints (GPT-4o-mini)
    4. Cultural Analysis (mini)
    5. Quality Score Check with auto-regeneration
    """
    try:
        agent = get_content_agent()
        
        # Get user's subscription plan for quality threshold
        user_plan = "free"
        try:
            user = await db_conn.users.find_one({"id": x_user_id}, {"_id": 0, "subscription": 1})
            if user and user.get("subscription"):
                user_plan = user["subscription"].get("plan", "free")
            # Also check user_credits for plan info
            if user_plan == "free":
                credit_info = await db_conn.user_credits.find_one({"user_id": x_user_id}, {"_id": 0, "plan": 1})
                if credit_info:
                    user_plan = credit_info.get("plan", "free")
        except Exception as e:
            logger.warning(f"Could not fetch user plan: {e}")
        
        # Check usage limits
        try:
            usage_tracker = get_usage_tracker()
            usage_check = await usage_tracker.check_usage_limit(x_user_id, "content_generation")
            
            if not usage_check["allowed"]:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Usage limit exceeded",
                        "message": usage_check["reason"],
                        "tier": usage_check["tier"],
                        "upgrade_url": "/contentry/subscription/plans"
                    }
                )
        except RuntimeError:
            logging.warning("Usage tracker not initialized")
        
        # Extract parameters
        prompt = data.get("prompt", "")
        tone = data.get("tone", "professional")
        platforms = data.get("platforms", [])
        language = data.get("language", "en")
        hashtag_count = data.get("hashtag_count", 3)
        job_title = data.get("job_title")
        
        # Optional: force a specific model tier
        override_tier = None
        if data.get("force_tier"):
            tier_map = {
                "top_tier": ModelTier.TOP_TIER,
                "balanced": ModelTier.BALANCED,
                "fast": ModelTier.FAST
            }
            override_tier = tier_map.get(data["force_tier"])
        
        if not prompt:
            raise HTTPException(400, "Prompt is required")
        
        result = await agent.generate_content(
            prompt=prompt,
            user_id=x_user_id,
            task_type=TaskType.CONTENT_GENERATION,
            tone=tone,
            platforms=platforms,
            language=language,
            hashtag_count=hashtag_count,
            job_title=job_title,
            override_tier=override_tier,
            user_plan=user_plan
        )
        
        # Record usage with existing tracker
        try:
            usage_tracker = get_usage_tracker()
            await usage_tracker.record_usage(
                user_id=x_user_id,
                operation="content_generation",
                tokens_used=result["metrics"]["tokens_used"],
                model=result["model_selection"]["model"],
                metadata={
                    "agent_tier": result["model_selection"]["tier"],
                    "platforms": platforms
                }
            )
        except Exception as e:
            logging.warning(f"Failed to record usage: {str(e)}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent generation error: {str(e)}")
        raise HTTPException(500, f"Content generation failed: {str(e)}")


@router.post("/rewrite")
@require_permission("content.create")
async def agent_rewrite_content(request: Request, data: dict, x_user_id: str = Header(..., alias="X-User-ID")):
    """
    Rewrite content using the AI Content Agent.
    
    Always uses TOP_TIER model for maximum quality improvement.
    """
    try:
        agent = get_content_agent()
        
        original_content = data.get("content", "")
        improvement_focus = data.get("improvement_focus", [])
        target_tone = data.get("target_tone")
        language = data.get("language", "en")
        
        if not original_content:
            raise HTTPException(400, "Content is required")
        
        result = await agent.rewrite_content(
            original_content=original_content,
            user_id=x_user_id,
            improvement_focus=improvement_focus,
            target_tone=target_tone,
            language=language
        )
        
        # Record usage
        try:
            usage_tracker = get_usage_tracker()
            await usage_tracker.record_usage(
                user_id=x_user_id,
                operation="content_rewrite",
                tokens_used=result["metrics"]["tokens_used"],
                model=result["model_selection"]["model"],
                metadata={"agent_tier": result["model_selection"]["tier"]}
            )
        except Exception as e:
            logging.warning(f"Failed to record usage: {str(e)}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent rewrite error: {str(e)}")
        raise HTTPException(500, f"Content rewrite failed: {str(e)}")


@router.post("/analyze")
@require_permission("content.analyze")
async def agent_analyze_content(request: Request, data: dict, x_user_id: str = Header(..., alias="X-User-ID")):
    """
    Analyze content using the AI Content Agent.
    
    Uses appropriate model tier based on analysis depth required.
    """
    try:
        agent = get_content_agent()
        
        content = data.get("content", "")
        analysis_type = data.get("analysis_type", "standard")
        language = data.get("language", "en")
        policies = data.get("policies", [])
        
        if not content:
            raise HTTPException(400, "Content is required")
        
        result = await agent.analyze_content(
            content=content,
            user_id=x_user_id,
            analysis_type=analysis_type,
            language=language,
            policies=policies
        )
        
        # Record usage
        try:
            usage_tracker = get_usage_tracker()
            await usage_tracker.record_usage(
                user_id=x_user_id,
                operation="content_analysis",
                tokens_used=result["metrics"]["tokens_used"],
                model=result["model_selection"]["model"],
                metadata={"agent_tier": result["model_selection"]["tier"]}
            )
        except Exception as e:
            logging.warning(f"Failed to record usage: {str(e)}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent analysis error: {str(e)}")
        raise HTTPException(500, f"Content analysis failed: {str(e)}")


@router.post("/ideate")
@require_permission("content.create")
async def agent_ideate_content(request: Request, data: dict, x_user_id: str = Header(..., alias="X-User-ID")):
    """
    Brainstorm content ideas using the AI Content Agent.
    
    Uses BALANCED tier for creative ideation.
    """
    try:
        agent = get_content_agent()
        
        topic = data.get("topic", "")
        industry = data.get("industry")
        content_types = data.get("content_types", [])
        count = data.get("count", 5)
        
        if not topic:
            raise HTTPException(400, "Topic is required")
        
        result = await agent.ideate_content(
            topic=topic,
            user_id=x_user_id,
            industry=industry,
            content_types=content_types,
            count=min(count, 10)  # Cap at 10 ideas
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent ideation error: {str(e)}")
        raise HTTPException(500, f"Content ideation failed: {str(e)}")


@router.post("/repurpose")
@require_permission("content.create")
async def agent_repurpose_content(request: Request, data: dict, x_user_id: str = Header(..., alias="X-User-ID")):
    """
    Repurpose content into multiple formats using the AI Content Agent.
    
    Uses BALANCED tier for creative transformation.
    """
    try:
        agent = get_content_agent()
        
        source_content = data.get("content", "")
        source_type = data.get("source_type", "article")
        target_formats = data.get("target_formats", [])
        
        if not source_content:
            raise HTTPException(400, "Content is required")
        
        result = await agent.repurpose_content(
            source_content=source_content,
            user_id=x_user_id,
            source_type=source_type,
            target_formats=target_formats if target_formats else None
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent repurpose error: {str(e)}")
        raise HTTPException(500, f"Content repurpose failed: {str(e)}")


@router.post("/optimize")
@require_permission("content.create")
async def agent_optimize_content(request: Request, data: dict, x_user_id: str = Header(..., alias="X-User-ID")):
    """
    Analyze and optimize content using the AI Content Agent.
    
    Uses TOP_TIER for comprehensive optimization analysis.
    """
    try:
        agent = get_content_agent()
        
        content = data.get("content", "")
        optimization_goals = data.get("optimization_goals", [])
        
        if not content:
            raise HTTPException(400, "Content is required")
        
        result = await agent.optimize_content(
            content=content,
            user_id=x_user_id,
            optimization_goals=optimization_goals if optimization_goals else None
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent optimization error: {str(e)}")
        raise HTTPException(500, f"Content optimization failed: {str(e)}")


@router.get("/model-info")
@require_permission("content.view_own")
async def get_model_info(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get information about available model tiers and their capabilities.
    
    Security (ARCH-005): Requires content.view_own permission.
    """
    try:
        model_info = {}
        for tier in ModelTier:
            config = MODEL_CONFIG[tier]
            model_info[tier.value] = {
                "name": tier.value.replace("_", " ").title(),
                "provider": config["provider"],
                "model": config["model"],
                "description": config["description"],
                "strengths": config["strengths"],
                "cost_per_1k_tokens": {
                    "input": config["cost_per_1k_input"],
                    "output": config["cost_per_1k_output"]
                }
            }
        
        return {
            "tiers": model_info,
            "selection_logic": {
                "top_tier": "Complex reasoning, rewrites, optimization, in-depth analysis",
                "balanced": "Creative content, ideation, repurposing, standard generation",
                "fast": "Quick tasks, formatting, sentiment analysis, simple operations"
            }
        }
        
    except Exception as e:
        logger.error(f"Model info error: {str(e)}")
        raise HTTPException(500, "Failed to get model info")


@router.get("/usage-analytics")
@require_permission("analytics.view_enterprise")
async def get_agent_usage_analytics(
    request: Request,
    x_user_id: str = Header(..., alias="X-User-ID"),
    days: int = 30,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get agent usage analytics for admin dashboard.
    """
    try:
        if not db:
            raise HTTPException(500, "Database not initialized")
        
        # Check if user is admin
        user = await db_conn.users.find_one({"id": x_user_id}, {"_id": 0})
        if not user or user.get("role") not in ["admin", "enterprise_admin"]:
            raise HTTPException(403, "Admin access required")
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Get usage records
        usage_records = await db_conn.agent_usage.find({
            "timestamp": {"$gte": start_date.isoformat()}
        }, {"_id": 0}).to_list(10000)
        
        # Aggregate statistics
        total_requests = len(usage_records)
        total_tokens = sum(r.get("tokens_used", 0) for r in usage_records)
        total_cost = sum(r.get("estimated_cost", 0) for r in usage_records)
        
        # By tier breakdown
        tier_breakdown = {}
        for tier in ["top_tier", "balanced", "fast"]:
            tier_records = [r for r in usage_records if r.get("agent_tier") == tier]
            tier_breakdown[tier] = {
                "requests": len(tier_records),
                "tokens": sum(r.get("tokens_used", 0) for r in tier_records),
                "cost": sum(r.get("estimated_cost", 0) for r in tier_records)
            }
        
        # By operation breakdown
        operation_breakdown = {}
        operations = set(r.get("operation") for r in usage_records if r.get("operation"))
        for op in operations:
            op_records = [r for r in usage_records if r.get("operation") == op]
            operation_breakdown[op] = {
                "requests": len(op_records),
                "tokens": sum(r.get("tokens_used", 0) for r in op_records),
                "cost": sum(r.get("estimated_cost", 0) for r in op_records)
            }
        
        # Average metrics
        avg_tokens = total_tokens / total_requests if total_requests > 0 else 0
        avg_cost = total_cost / total_requests if total_requests > 0 else 0
        avg_duration = sum(r.get("duration_ms", 0) for r in usage_records) / total_requests if total_requests > 0 else 0
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "totals": {
                "requests": total_requests,
                "tokens": total_tokens,
                "cost": round(total_cost, 4)
            },
            "averages": {
                "tokens_per_request": round(avg_tokens, 2),
                "cost_per_request": round(avg_cost, 6),
                "duration_ms": round(avg_duration, 2)
            },
            "by_tier": tier_breakdown,
            "by_operation": operation_breakdown,
            "cost_savings_estimate": {
                "description": "Estimated savings from intelligent model selection vs always using top-tier",
                "potential_top_tier_cost": round(total_tokens * 0.015 / 1000, 4),
                "actual_cost": round(total_cost, 4),
                "savings": round((total_tokens * 0.015 / 1000) - total_cost, 4)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Usage analytics error: {str(e)}")
        raise HTTPException(500, f"Failed to get usage analytics: {str(e)}")


@router.get("/explain-selection")
@require_permission("settings.view")
async def explain_model_selection(
    request: Request,
    prompt: str,
    task_type: Optional[str] = None
):
    """
    Explain which model would be selected for a given prompt.
    Useful for understanding the agent's decision-making.
    """
    try:
        agent = get_content_agent()
        
        tt = None
        if task_type:
            try:
                tt = TaskType(task_type)
            except ValueError:
                pass
        
        tier, selection_info = await agent.select_model(prompt, tt)
        justification = agent.get_model_justification(tier)
        
        return {
            "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
            "selection": selection_info,
            "justification": justification,
            "model_capabilities": MODEL_CONFIG[tier]["strengths"]
        }
        
    except Exception as e:
        logger.error(f"Selection explanation error: {str(e)}")
        raise HTTPException(500, f"Failed to explain selection: {str(e)}")
