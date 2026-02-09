"""
Multi-Agent Content Generation Service

High-level service that provides a clean interface to the multi-agent system.
Used by API routes and background tasks.

Usage:
    from services.multi_agent_content_service import MultiAgentContentService
    
    service = MultiAgentContentService(db)
    result = await service.generate_content(
        user_id="user123",
        prompt="Create a post about maritime news",
        tone="professional",
        hashtag_count=5
    )
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

from services.agents import OrchestratorAgent
from services.agents.base_agent import AgentContext

logger = logging.getLogger(__name__)


class MultiAgentContentService:
    """
    High-level service for multi-agent content generation.
    
    Provides:
    - Simple interface for content generation
    - Context building from user data
    - Result formatting for API responses
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.orchestrator = OrchestratorAgent(db=db)
    
    async def _build_context(
        self,
        user_id: str,
        prompt: str,
        language: str = "en",
        tone: str = "professional",
        platforms: List[str] = None,
        hashtag_count: int = 3,
        profile_id: str = None
    ) -> AgentContext:
        """Build the shared context for agents"""
        
        # Load user policies
        policies = await self.db.policies.find(
            {"user_id": user_id},
            {"_id": 0}
        ).to_list(5)
        
        # Load profile if specified
        profile_data = {}
        if profile_id:
            profile = await self.db.strategic_profiles.find_one(
                {"id": profile_id},
                {"_id": 0}
            )
            if profile:
                profile_data = profile
                # Override tone from profile if set
                if profile.get("writing_tone"):
                    tone = profile["writing_tone"]
        
        return AgentContext(
            user_id=user_id,
            original_prompt=prompt,
            language=language,
            tone=tone,
            platforms=platforms or ["linkedin"],
            hashtag_count=hashtag_count,
            profile_data=profile_data,
            policies=policies
        )
    
    async def generate_content(
        self,
        user_id: str,
        prompt: str,
        language: str = "en",
        tone: str = "professional",
        platforms: List[str] = None,
        hashtag_count: int = 3,
        profile_id: str = None,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Generate content using the multi-agent system.
        
        Args:
            user_id: User ID for context loading
            prompt: User's content request
            language: Target language
            tone: Writing tone
            platforms: Target platforms
            hashtag_count: Number of hashtags
            profile_id: Optional profile for brand voice
            progress_callback: Optional async callback for progress updates
            
        Returns:
            Generated content with quality scores and metadata
        """
        logger.info(f"[MultiAgentService] Starting content generation for user {user_id}")
        
        # Build context
        context = await self._build_context(
            user_id=user_id,
            prompt=prompt,
            language=language,
            tone=tone,
            platforms=platforms,
            hashtag_count=hashtag_count,
            profile_id=profile_id
        )
        
        # Report progress if callback provided
        if progress_callback:
            await progress_callback({
                "step": "Initializing multi-agent system",
                "percentage": 5,
                "agents": ["Orchestrator", "Research", "Writer", "Compliance", "Cultural"]
            })
        
        # Execute multi-agent workflow
        try:
            result = await self.orchestrator.execute(context=context)
            
            # Store result in database
            await self.db.generated_content.insert_one({
                "user_id": user_id,
                "prompt": prompt,
                "content": result.get("content"),
                "workflow": result.get("workflow"),
                "quality": result.get("quality"),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "generation_method": "multi_agent"
            })
            
            # Format response for API
            return {
                "success": True,
                "content": result.get("content"),
                "generated_content": result.get("content"),  # Alias for compatibility
                "prompt": prompt,
                "multi_agent": True,
                "workflow_summary": {
                    "agents_used": result.get("workflow", {}).get("agents_involved", []),
                    "revision_cycles": result.get("workflow", {}).get("revision_cycles", 0),
                    "duration_ms": result.get("workflow", {}).get("duration_ms", 0)
                },
                "research": result.get("research", {}),
                "quality_scores": {
                    "cultural_score": result.get("quality", {}).get("cultural", {}).get("score", 0),
                    "compliance_score": result.get("quality", {}).get("compliance", {}).get("score", 0),
                    "cultural_passes": result.get("quality", {}).get("cultural", {}).get("passes_threshold", False),
                    "is_compliant": result.get("quality", {}).get("compliance", {}).get("compliant", False)
                },
                "metadata": result.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"[MultiAgentService] Error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
    
    async def get_agent_capabilities(self) -> Dict[str, Any]:
        """Return information about available agents and their capabilities"""
        return {
            "system": "Multi-Agent Content Generation",
            "version": "1.0.0",
            "agents": [
                {
                    "name": "Orchestrator Agent",
                    "role": "orchestrator",
                    "description": "Plans and coordinates the multi-agent workflow",
                    "capabilities": ["workflow planning", "task delegation", "quality control", "synthesis"]
                },
                {
                    "name": "Research Agent",
                    "role": "research",
                    "description": "Gathers news, trends, and relevant data",
                    "capabilities": ["news search", "industry detection", "trend analysis", "source evaluation"]
                },
                {
                    "name": "Writer Agent",
                    "role": "writer",
                    "description": "Creates engaging content drafts",
                    "capabilities": ["content creation", "tone matching", "platform optimization", "source citation"]
                },
                {
                    "name": "Compliance Agent",
                    "role": "compliance",
                    "description": "Ensures policy and legal compliance",
                    "capabilities": ["policy checking", "legal review", "brand alignment", "term screening"]
                },
                {
                    "name": "Cultural Sensitivity Agent",
                    "role": "cultural",
                    "description": "Ensures global cultural appropriateness",
                    "capabilities": ["Hofstede analysis", "idiom detection", "bias identification", "global readiness scoring"]
                }
            ],
            "workflow": {
                "description": "Orchestrator → Research → Writer → Compliance → Cultural → (Revise) → Final",
                "max_revision_cycles": 2,
                "quality_thresholds": {
                    "cultural_score_minimum": 80,
                    "compliance_required": True
                }
            }
        }


# Singleton instance
_service_instance: Optional[MultiAgentContentService] = None


def get_multi_agent_service(db: AsyncIOMotorDatabase) -> MultiAgentContentService:
    """Get or create the multi-agent service singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = MultiAgentContentService(db)
    return _service_instance
