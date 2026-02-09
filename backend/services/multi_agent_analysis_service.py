"""
Multi-Agent Content Analysis Service

High-level service that provides a clean interface to the multi-agent
analysis system for images, videos, and text content.

Usage:
    from services.multi_agent_analysis_service import MultiAgentAnalysisService
    
    service = MultiAgentAnalysisService(db)
    result = await service.analyze_content(
        user_id="user123",
        content_type="video",
        media_url="https://example.com/video.mp4",
        frames=[...],
        caption="Video caption here"
    )
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

from services.agents import AnalysisOrchestratorAgent, AnalysisContext

logger = logging.getLogger(__name__)


class MultiAgentAnalysisService:
    """
    High-level service for multi-agent content analysis.
    
    Provides:
    - Simple interface for analyzing various content types
    - Context building from user data and policies
    - Result formatting for API responses
    - Support for images, videos, and text
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.orchestrator = AnalysisOrchestratorAgent(db=db)
    
    async def _load_user_context(self, user_id: str, profile_id: str = None) -> Dict[str, Any]:
        """Load user context including policies and profile"""
        context = {
            "policies": [],
            "profile": {}
        }
        
        # Load policies
        policies = await self.db.policies.find(
            {"user_id": user_id},
            {"_id": 0}
        ).to_list(10)
        context["policies"] = policies
        
        # Load profile if specified
        if profile_id:
            profile = await self.db.strategic_profiles.find_one(
                {"id": profile_id},
                {"_id": 0}
            )
            if profile:
                context["profile"] = profile
        
        return context
    
    async def analyze_image(
        self,
        user_id: str,
        image_url: str,
        caption: str = "",
        profile_id: str = None,
        platform: str = "general",
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Analyze an image using the multi-agent system.
        
        Args:
            user_id: User ID for context
            image_url: URL of the image to analyze
            caption: Optional caption/text associated with image
            profile_id: Optional profile for brand context
            platform: Target platform
            progress_callback: Optional progress callback
        """
        logger.info(f"[MultiAgentAnalysis] Starting image analysis for user {user_id}")
        
        # Load user context
        user_context = await self._load_user_context(user_id, profile_id)
        
        # Build analysis context
        context = AnalysisContext(
            user_id=user_id,
            content_type="image",
            platform=platform,
            media_url=image_url,
            media_frames=[{"url": image_url, "timestamp": 0}],
            caption=caption,
            policies=user_context["policies"],
            profile_data=user_context["profile"]
        )
        
        # Execute analysis
        result = await self.orchestrator.execute(context=context)
        
        # Store result
        await self._store_analysis_result(user_id, "image", result)
        
        return self._format_response(result)
    
    async def analyze_video(
        self,
        user_id: str,
        video_url: str = "",
        frames: List[Dict] = None,
        caption: str = "",
        transcript: str = "",
        profile_id: str = None,
        platform: str = "general",
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Analyze a video using the multi-agent system.
        
        Args:
            user_id: User ID for context
            video_url: URL of the video
            frames: List of extracted frames with URLs and timestamps
            caption: Optional caption
            transcript: Optional audio transcript
            profile_id: Optional profile for brand context
            platform: Target platform
            progress_callback: Optional progress callback
        """
        logger.info(f"[MultiAgentAnalysis] Starting video analysis for user {user_id}")
        
        # Load user context
        user_context = await self._load_user_context(user_id, profile_id)
        
        # Build analysis context
        context = AnalysisContext(
            user_id=user_id,
            content_type="video",
            platform=platform,
            media_url=video_url,
            media_frames=frames or [],
            caption=caption,
            transcript=transcript,
            policies=user_context["policies"],
            profile_data=user_context["profile"]
        )
        
        # Execute analysis
        result = await self.orchestrator.execute(context=context)
        
        # Store result
        await self._store_analysis_result(user_id, "video", result)
        
        return self._format_response(result)
    
    async def analyze_text(
        self,
        user_id: str,
        text: str,
        text_type: str = "post",  # post, comment, article, etc.
        profile_id: str = None,
        platform: str = "general",
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Analyze text content using the multi-agent system.
        
        Args:
            user_id: User ID for context
            text: Text content to analyze
            text_type: Type of text content
            profile_id: Optional profile for brand context
            platform: Target platform
            progress_callback: Optional progress callback
        """
        logger.info(f"[MultiAgentAnalysis] Starting text analysis for user {user_id}")
        
        # Load user context
        user_context = await self._load_user_context(user_id, profile_id)
        
        # Build analysis context
        context = AnalysisContext(
            user_id=user_id,
            content_type="text",
            platform=platform,
            text_content=text,
            policies=user_context["policies"],
            profile_data=user_context["profile"]
        )
        
        # Execute analysis
        result = await self.orchestrator.execute(context=context)
        
        # Store result
        await self._store_analysis_result(user_id, "text", result)
        
        return self._format_response(result)
    
    async def _store_analysis_result(
        self, 
        user_id: str, 
        content_type: str, 
        result: Dict[str, Any]
    ):
        """Store analysis result in database"""
        try:
            await self.db.content_analyses.insert_one({
                "user_id": user_id,
                "content_type": content_type,
                "result": result,
                "risk_score": result.get("final_assessment", {}).get("risk_score", 0),
                "risk_level": result.get("final_assessment", {}).get("risk_level", "UNKNOWN"),
                "action": result.get("final_assessment", {}).get("recommended_action", "FLAG_FOR_REVIEW"),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "analysis_method": "multi_agent"
            })
        except Exception as e:
            logger.warning(f"Failed to store analysis result: {e}")
    
    def _format_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format result for API response"""
        return {
            "success": True,
            "multi_agent": True,
            
            # Main assessment
            "risk_score": result.get("final_assessment", {}).get("risk_score", 0),
            "risk_level": result.get("final_assessment", {}).get("risk_level", "UNKNOWN"),
            "recommended_action": result.get("final_assessment", {}).get("recommended_action", "FLAG_FOR_REVIEW"),
            "confidence": result.get("final_assessment", {}).get("confidence", "medium"),
            
            # Summary
            "executive_summary": result.get("executive_summary", ""),
            "priority_issues": result.get("priority_issues", []),
            "recommendations": result.get("recommendations", []),
            
            # Agent details
            "agent_results": result.get("agent_results", {}),
            
            # Workflow info
            "workflow": {
                "agents_used": result.get("workflow", {}).get("agents_used", []),
                "duration_ms": result.get("workflow", {}).get("duration_ms", 0)
            },
            
            # Full result for detailed view
            "detailed_result": result
        }
    
    async def get_analysis_capabilities(self) -> Dict[str, Any]:
        """Return information about analysis capabilities"""
        return {
            "system": "Multi-Agent Content Analysis",
            "version": "1.0.0",
            "supported_content_types": ["image", "video", "text"],
            "agents": [
                {
                    "name": "Analysis Orchestrator",
                    "role": "orchestrator",
                    "description": "Coordinates the multi-agent analysis workflow",
                    "capabilities": ["workflow planning", "agent coordination", "result synthesis"]
                },
                {
                    "name": "Visual Analysis Agent",
                    "role": "visual",
                    "description": "Analyzes images and video frames",
                    "capabilities": ["object detection", "scene understanding", "safety analysis", "visual compliance"]
                },
                {
                    "name": "Text Analysis Agent",
                    "role": "text",
                    "description": "Analyzes text content",
                    "capabilities": ["sentiment analysis", "tone detection", "claim verification", "harmful language detection"]
                },
                {
                    "name": "Compliance Agent",
                    "role": "compliance",
                    "description": "Checks policy and legal compliance",
                    "capabilities": ["policy checking", "legal review", "brand alignment", "term screening"]
                },
                {
                    "name": "Risk Assessment Agent",
                    "role": "risk",
                    "description": "Aggregates findings into final risk assessment",
                    "capabilities": ["multi-source aggregation", "priority ranking", "action recommendation", "confidence scoring"]
                }
            ],
            "workflow": {
                "description": "Orchestrator → [Visual + Text (parallel)] → Compliance → Risk Assessment → Final Report",
                "risk_thresholds": {
                    "auto_approve": 30,
                    "review_required": 60,
                    "auto_reject": 85
                }
            }
        }


# Singleton instance
_analysis_service_instance: Optional[MultiAgentAnalysisService] = None


def get_multi_agent_analysis_service(db: AsyncIOMotorDatabase) -> MultiAgentAnalysisService:
    """Get or create the multi-agent analysis service singleton"""
    global _analysis_service_instance
    if _analysis_service_instance is None:
        _analysis_service_instance = MultiAgentAnalysisService(db)
    return _analysis_service_instance
