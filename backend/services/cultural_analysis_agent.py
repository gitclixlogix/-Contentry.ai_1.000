"""
Cultural Analysis Agent - Wrapper for 51 Cultural Lenses

This module provides a simplified interface to the CulturalAgent
for standalone cultural analysis without the full orchestration pipeline.

For the full multi-agent content generation workflow, use the OrchestratorAgent
which automatically includes the CulturalAgent.
"""

import logging
from typing import Dict, Any, Optional

from services.agents.cultural_agent import CulturalAgent
from services.agents.base_agent import AgentContext

logger = logging.getLogger(__name__)


async def analyze_cultural_sensitivity(
    content: str,
    target_region: Optional[str] = None,
    target_audience: Optional[str] = None,
    content_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to run 51 Cultural Lenses analysis.
    
    This is a simplified wrapper around the CulturalAgent for standalone use.
    For full content generation workflows, use the OrchestratorAgent instead.
    
    Args:
        content: Text content to analyze
        target_region: Optional target region (defaults to USA)
        target_audience: Optional target audience description
        content_type: Optional content type hint
        
    Returns:
        Comprehensive cultural analysis results using 51 Cultural Lenses
    """
    agent = CulturalAgent()
    
    # Create a minimal context for the agent
    context = AgentContext(
        original_request=content,
        draft_content=content,
        compliance_feedback={},
        metadata={
            "target_region": target_region or "USA",
            "target_audience": target_audience,
            "content_type": content_type
        }
    )
    
    task = {
        "target_region": target_region or "USA"
    }
    
    try:
        result = await agent.execute(context, task)
        return result
    except Exception as e:
        logger.error(f"Cultural analysis failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "passes_threshold": False,
            "overall_score": 0
        }


def get_cultural_lenses_info() -> Dict[str, Any]:
    """Get information about the 51 Cultural Lenses framework."""
    from services.cultural_lenses_service import get_lenses_summary
    return get_lenses_summary()


# For backwards compatibility - the CulturalAnalysisAgent class
class CulturalAnalysisAgent:
    """
    Wrapper class for backwards compatibility.
    
    Use CulturalAgent directly for new implementations.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self._agent = CulturalAgent()
    
    async def analyze(
        self,
        content: str,
        target_region: Optional[str] = None,
        target_audience: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run 51 Cultural Lenses analysis."""
        return await analyze_cultural_sensitivity(
            content=content,
            target_region=target_region,
            target_audience=target_audience,
            content_type=content_type
        )
