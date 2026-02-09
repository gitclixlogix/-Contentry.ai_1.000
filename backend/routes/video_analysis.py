"""
Video Analysis Routes for Contentry.ai
API endpoints for video content moderation using visual analysis.

Endpoints:
- POST /video/analyze - Analyze video for harmful visual content
- GET /video/analysis/{analysis_id} - Get analysis result
- GET /video/analyses - List user's video analyses
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Header, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import os
import logging
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorDatabase

from services.database import get_db
from services.authorization_decorator import require_permission
from services.video_analysis_agent import get_video_analysis_agent
# Credit consumption service (Pricing v3.0)
from services.credit_service import consume_credits_util, CreditAction

router = APIRouter(prefix="/video", tags=["video-analysis"])
logger = logging.getLogger(__name__)


# =============================================================================
# HELPER: Fetch Profile & Policy Context
# =============================================================================

async def get_profile_and_policy_context(
    db: AsyncIOMotorDatabase,
    user_id: str,
    profile_id: Optional[str] = None,
    enterprise_id: Optional[str] = None
) -> Dict:
    """
    Fetch profile context, documents, and policies for contextual media analysis.
    
    Returns a dict with:
    - profile: Strategic profile details (brand voice, industry, guidelines)
    - profile_documents: Knowledge base documents attached to the profile
    - policies: Universal and profile-specific compliance policies
    """
    context = {
        "profile": None,
        "profile_documents": [],
        "policies": [],
        "brand_guidelines": [],
        "industry": None,
        "target_audience": None
    }
    
    try:
        # Get user's enterprise if not provided
        if not enterprise_id:
            user = await db.users.find_one({"id": user_id}, {"enterprise_id": 1, "_id": 0})
            enterprise_id = user.get("enterprise_id") if user else None
        
        # 1. Fetch Strategic Profile
        if profile_id:
            profile = await db.strategic_profiles.find_one(
                {"id": profile_id},
                {"_id": 0, "name": 1, "description": 1, "industry": 1, "tone": 1, 
                 "brand_voice": 1, "target_audience": 1, "content_guidelines": 1,
                 "prohibited_topics": 1, "required_disclosures": 1, "hashtag_strategy": 1,
                 "seo_keywords": 1, "compliance_requirements": 1, "language": 1}
            )
            if profile:
                context["profile"] = profile
                context["industry"] = profile.get("industry")
                context["target_audience"] = profile.get("target_audience")
                logger.info(f"[VideoAnalysis] Loaded profile context: {profile.get('name')}")
        
        # 2. Fetch Profile Knowledge Base Documents
        if profile_id:
            profile_docs = await db.knowledge_documents.find(
                {"profile_id": profile_id, "status": "processed"},
                {"_id": 0, "title": 1, "summary": 1, "content_preview": 1, "document_type": 1}
            ).to_list(10)  # Top 10 documents
            context["profile_documents"] = profile_docs
            logger.info(f"[VideoAnalysis] Loaded {len(profile_docs)} profile documents")
        
        # 3. Fetch Universal/Company Policies
        policy_filter = {"$or": [{"is_universal": True}]}
        if enterprise_id:
            policy_filter["$or"].append({"enterprise_id": enterprise_id})
        if profile_id:
            policy_filter["$or"].append({"profile_id": profile_id})
        
        policies = await db.policies.find(
            policy_filter,
            {"_id": 0, "name": 1, "description": 1, "policy_type": 1, "rules": 1,
             "prohibited_content": 1, "required_disclosures": 1, "compliance_standards": 1}
        ).to_list(20)  # Top 20 policies
        context["policies"] = policies
        logger.info(f"[VideoAnalysis] Loaded {len(policies)} policies")
        
        # 4. Fetch Brand Guidelines (if any)
        if enterprise_id:
            brand_docs = await db.knowledge_documents.find(
                {"enterprise_id": enterprise_id, "document_type": "brand_guidelines", "status": "processed"},
                {"_id": 0, "title": 1, "summary": 1, "content_preview": 1}
            ).to_list(5)
            context["brand_guidelines"] = brand_docs
        
    except Exception as e:
        logger.error(f"[VideoAnalysis] Error fetching profile/policy context: {e}")
    
    return context


def format_context_for_analysis(context: Dict) -> str:
    """Format the profile and policy context into a string for GPT-4o analysis."""
    parts = []
    
    # Profile context
    if context.get("profile"):
        profile = context["profile"]
        parts.append("=== BRAND/PROFILE CONTEXT ===")
        if profile.get("name"):
            parts.append(f"Profile: {profile['name']}")
        if profile.get("industry"):
            parts.append(f"Industry: {profile['industry']}")
        if profile.get("target_audience"):
            parts.append(f"Target Audience: {profile['target_audience']}")
        if profile.get("brand_voice"):
            parts.append(f"Brand Voice: {profile['brand_voice']}")
        if profile.get("content_guidelines"):
            parts.append(f"Content Guidelines: {profile['content_guidelines']}")
        if profile.get("prohibited_topics"):
            parts.append(f"Prohibited Topics: {', '.join(profile['prohibited_topics']) if isinstance(profile['prohibited_topics'], list) else profile['prohibited_topics']}")
        if profile.get("compliance_requirements"):
            parts.append(f"Compliance Requirements: {profile['compliance_requirements']}")
    
    # Policies
    if context.get("policies"):
        parts.append("\n=== COMPLIANCE POLICIES ===")
        for policy in context["policies"][:5]:  # Top 5
            parts.append(f"- {policy.get('name', 'Policy')}: {policy.get('description', '')[:200]}")
            if policy.get("prohibited_content"):
                prohibited = policy["prohibited_content"]
                if isinstance(prohibited, list):
                    parts.append(f"  Prohibited: {', '.join(prohibited[:5])}")
                else:
                    parts.append(f"  Prohibited: {str(prohibited)[:200]}")
    
    # Brand guidelines summary
    if context.get("brand_guidelines"):
        parts.append("\n=== BRAND GUIDELINES ===")
        for doc in context["brand_guidelines"][:3]:
            parts.append(f"- {doc.get('title', 'Document')}: {doc.get('summary', '')[:150]}")
    
    return "\n".join(parts) if parts else ""


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class VideoAnalysisRequest(BaseModel):
    """Request model for video analysis"""
    video_url: str = Field(..., description="URL to the video file")
    context: Optional[Dict] = Field(None, description="Additional context (post text, platform, etc.)")
    profile_id: Optional[str] = Field(None, description="Strategic Profile ID for contextual analysis")
    async_mode: bool = Field(default=False, description="Run analysis in background")
    use_multi_agent: bool = Field(default=True, description="Use multi-agent analysis system")
    caption: Optional[str] = Field(None, description="Video caption or description")
    platform: Optional[str] = Field("general", description="Target platform")


class VideoAnalysisResponse(BaseModel):
    """Response model for video analysis"""
    analysis_id: str
    success: bool
    risk_level: str  # low, medium, high, critical
    risk_score: int  # 0-100
    recommendation: str
    suspicious_objects: Optional[List[Dict]] = None
    risk_indicators: Optional[List[str]] = None
    gpt_concerns: Optional[List[str]] = None
    processing_time_ms: Optional[float] = None


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post("/analyze")
@require_permission("content.create")
async def analyze_video(
    request: Request,
    data: VideoAnalysisRequest,
    background_tasks: BackgroundTasks,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Analyze video for harmful visual content with profile and policy context.
    
    This endpoint:
    1. Fetches profile context, documents, and policies
    2. Extracts frames from the video
    3. Analyzes each frame with Google Vision API
    4. Uses GPT-4o Vision for complex reasoning with full context
    5. Returns a risk assessment with specific findings
    
    Security (ARCH-005): Requires content.create permission.
    """
    try:
        # === CREDIT CONSUMPTION (Pricing v3.0) ===
        # Video analysis consumes credits like image analysis
        credit_success, credit_result = await consume_credits_util(
            action=CreditAction.IMAGE_ANALYSIS,  # Using image analysis cost for video (per video)
            user_id=x_user_id,
            db=db_conn,
            quantity=1,
            metadata={"video_url": data.video_url[:100], "async_mode": data.async_mode},
            raise_on_insufficient=True  # Will raise 402 if insufficient
        )
        logger.info(f"Credits consumed for user {x_user_id}: {credit_result.get('credits_consumed', 0)} for video analysis")
        
        # === FETCH PROFILE & POLICY CONTEXT ===
        profile_policy_context = await get_profile_and_policy_context(
            db=db_conn,
            user_id=x_user_id,
            profile_id=data.profile_id
        )
        
        # Format context for GPT analysis
        formatted_context = format_context_for_analysis(profile_policy_context)
        
        # Merge with provided context
        analysis_context = data.context or {}
        if formatted_context:
            analysis_context["profile_policy_context"] = formatted_context
        if profile_policy_context.get("profile"):
            analysis_context["profile_name"] = profile_policy_context["profile"].get("name")
            analysis_context["industry"] = profile_policy_context.get("industry")
        if profile_policy_context.get("policies"):
            analysis_context["policy_count"] = len(profile_policy_context["policies"])
        
        logger.info(f"[VideoAnalysis] Context prepared - Profile: {data.profile_id}, Policies: {len(profile_policy_context.get('policies', []))}")
        
        # === MULTI-AGENT ANALYSIS (Default) ===
        if data.use_multi_agent:
            from services.multi_agent_analysis_service import get_multi_agent_analysis_service
            
            multi_agent_service = get_multi_agent_analysis_service(db_conn)
            
            # For multi-agent, we need to extract frames first
            agent = get_video_analysis_agent(db_conn)
            frames = await agent.extract_frames(data.video_url)
            
            if data.async_mode:
                # Run in background
                analysis_id = str(uuid4())
                
                # Create pending record
                await db_conn.video_analyses.insert_one({
                    "id": analysis_id,
                    "user_id": x_user_id,
                    "video_source": data.video_url,
                    "profile_id": data.profile_id,
                    "status": "processing",
                    "multi_agent": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                
                # Queue background task
                background_tasks.add_task(
                    run_multi_agent_video_analysis_background,
                    multi_agent_service, data.video_url, frames, x_user_id, 
                    data.caption or "", data.profile_id, data.platform or "general",
                    analysis_id, db_conn
                )
                
                return {
                    "success": True,
                    "analysis_id": analysis_id,
                    "status": "processing",
                    "multi_agent": True,
                    "message": "Multi-agent video analysis started. Check status using the analysis ID."
                }
            else:
                # Run synchronously with multi-agent
                result = await multi_agent_service.analyze_video(
                    user_id=x_user_id,
                    video_url=data.video_url,
                    frames=frames,
                    caption=data.caption or "",
                    profile_id=data.profile_id,
                    platform=data.platform or "general"
                )
                
                return {
                    "success": result.get("success", False),
                    "multi_agent": True,
                    "risk_level": result.get("risk_level", "unknown"),
                    "risk_score": result.get("risk_score", 0),
                    "recommended_action": result.get("recommended_action", "FLAG_FOR_REVIEW"),
                    "confidence": result.get("confidence", "medium"),
                    "executive_summary": result.get("executive_summary", ""),
                    "priority_issues": result.get("priority_issues", []),
                    "recommendations": result.get("recommendations", []),
                    "agent_results": result.get("agent_results", {}),
                    "workflow": result.get("workflow", {}),
                    "profile_context_used": bool(data.profile_id)
                }
        
        # === LEGACY SINGLE-AGENT ANALYSIS ===
        agent = get_video_analysis_agent(db_conn)
        
        if data.async_mode:
            # Run in background
            analysis_id = str(uuid4())
            
            # Create pending record
            await db_conn.video_analyses.insert_one({
                "id": analysis_id,
                "user_id": x_user_id,
                "video_source": data.video_url,
                "profile_id": data.profile_id,
                "status": "processing",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            
            # Queue background task with enhanced context
            background_tasks.add_task(
                run_video_analysis_background,
                agent, data.video_url, x_user_id, analysis_context, analysis_id, db_conn
            )
            
            return {
                "success": True,
                "analysis_id": analysis_id,
                "status": "processing",
                "message": "Video analysis started. Check status using the analysis ID."
            }
        
        else:
            # Run synchronously with enhanced context
            result = await agent.analyze_video(
                video_source=data.video_url,
                user_id=x_user_id,
                context=analysis_context
            )
            
            return {
                "success": result.get("success", False),
                "analysis_id": result.get("analysis_id"),
                "risk_level": result.get("risk_level", "unknown"),
                "risk_score": result.get("risk_score", 0),
                "recommendation": result.get("recommendation", "Manual review required"),
                "suspicious_objects": result.get("suspicious_objects", []),
                "risk_indicators": result.get("risk_indicators", []),
                "gpt_analysis": result.get("gpt_analysis", {}),
                "safe_search_issues": result.get("safe_search_issues", []),
                "frame_statistics": result.get("frame_statistics", {}),
                "processing_time_ms": result.get("processing_time_ms"),
                "profile_context_used": bool(formatted_context),
                "error": result.get("error")
            }
            
    except Exception as e:
        logger.error(f"[VideoAPI] Analysis error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Video analysis failed: {str(e)}"
        )


async def run_video_analysis_background(
    agent,
    video_url: str,
    user_id: str,
    context: Optional[Dict],
    analysis_id: str,
    db_conn
):
    """Background task for video analysis"""
    try:
        result = await agent.analyze_video(
            video_source=video_url,
            user_id=user_id,
            context=context
        )
        
        # Update record with results
        await db_conn.video_analyses.update_one(
            {"id": analysis_id},
            {"$set": {
                "status": "completed",
                "risk_level": result.get("risk_level"),
                "risk_score": result.get("risk_score"),
                "recommendation": result.get("recommendation"),
                "result": result,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
    except Exception as e:
        logger.error(f"[VideoAPI] Background analysis error: {e}")
        await db_conn.video_analyses.update_one(
            {"id": analysis_id},
            {"$set": {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }}
        )


async def run_multi_agent_video_analysis_background(
    service,
    video_url: str,
    frames: List[Dict],
    user_id: str,
    caption: str,
    profile_id: str,
    platform: str,
    analysis_id: str,
    db_conn
):
    """Background task for multi-agent video analysis"""
    try:
        result = await service.analyze_video(
            user_id=user_id,
            video_url=video_url,
            frames=frames,
            caption=caption,
            profile_id=profile_id,
            platform=platform
        )
        
        # Update record with results
        await db_conn.video_analyses.update_one(
            {"id": analysis_id},
            {"$set": {
                "status": "completed",
                "multi_agent": True,
                "risk_level": result.get("risk_level"),
                "risk_score": result.get("risk_score"),
                "recommended_action": result.get("recommended_action"),
                "confidence": result.get("confidence"),
                "executive_summary": result.get("executive_summary"),
                "result": result,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
    except Exception as e:
        logger.error(f"[VideoAPI] Multi-agent background analysis error: {e}")
        await db_conn.video_analyses.update_one(
            {"id": analysis_id},
            {"$set": {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }}
        )


@router.get("/analysis/{analysis_id}")
@require_permission("content.view_own")
async def get_analysis(
    request: Request,
    analysis_id: str,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get video analysis result by ID.
    """
    try:
        analysis = await db_conn.video_analyses.find_one(
            {"id": analysis_id, "user_id": x_user_id},
            {"_id": 0}
        )
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            "success": True,
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[VideoAPI] Get analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyses")
@require_permission("content.view_own")
async def list_analyses(
    request: Request,
    limit: int = 20,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    List user's video analyses.
    """
    try:
        cursor = db_conn.video_analyses.find(
            {"user_id": x_user_id},
            {"_id": 0, "result": 0}  # Exclude large result field
        ).sort("created_at", -1).limit(limit)
        
        analyses = await cursor.to_list(length=limit)
        
        return {
            "success": True,
            "analyses": analyses,
            "count": len(analyses)
        }
        
    except Exception as e:
        logger.error(f"[VideoAPI] List analyses error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def get_analysis_agents_info(
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get information about the multi-agent analysis system.
    
    Returns details about all analysis agents and their capabilities.
    """
    from services.multi_agent_analysis_service import get_multi_agent_analysis_service
    
    service = get_multi_agent_analysis_service(db_conn)
    return await service.get_analysis_capabilities()


@router.post("/analyze-for-post")
@require_permission("content.create")
async def analyze_video_for_post(
    request: Request,
    data: Dict,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Analyze video attached to a post.
    Called automatically when video is detected in content.
    
    Input:
    - video_url: URL to video
    - post_text: Text content of the post
    - platform: Target platform
    - post_id: Optional post ID to associate
    """
    try:
        video_url = data.get("video_url")
        if not video_url:
            raise HTTPException(status_code=400, detail="video_url is required")
        
        context = {
            "text": data.get("post_text", ""),
            "platform": data.get("platform", "unknown"),
            "post_id": data.get("post_id")
        }
        
        agent = get_video_analysis_agent(db_conn)
        
        result = await agent.analyze_video(
            video_source=video_url,
            user_id=x_user_id,
            context=context
        )
        
        # If post_id provided, update post with video analysis
        if data.get("post_id"):
            await db_conn.posts.update_one(
                {"id": data["post_id"]},
                {"$set": {
                    "video_analysis": {
                        "analysis_id": result.get("analysis_id"),
                        "risk_level": result.get("risk_level"),
                        "risk_score": result.get("risk_score"),
                        "recommendation": result.get("recommendation"),
                        "analyzed_at": datetime.now(timezone.utc).isoformat()
                    }
                }}
            )
        
        return {
            "success": result.get("success", False),
            "analysis_id": result.get("analysis_id"),
            "risk_level": result.get("risk_level", "unknown"),
            "risk_score": result.get("risk_score", 0),
            "recommendation": result.get("recommendation"),
            "should_block": result.get("risk_level") in ["critical", "high"],
            "requires_review": result.get("risk_level") == "medium",
            "gpt_concerns": result.get("gpt_analysis", {}).get("specific_concerns", []),
            "suspicious_objects": result.get("suspicious_objects", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[VideoAPI] Post video analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
