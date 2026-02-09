"""
Content Generation Background Task

Uses the Multi-Agent System for content generation:
- Orchestrator Agent: Plans and coordinates
- Research Agent: Finds news and data
- Writer Agent: Creates content
- Compliance Agent: Checks policies
- Cultural Agent: Ensures global sensitivity

This replaces the previous hardcoded pipeline with a true multi-agent approach.
"""

import logging
from typing import Dict, Any, Callable, Coroutine
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

from services.job_queue_service import Job, JobProgress
from services.multi_agent_content_service import MultiAgentContentService

logger = logging.getLogger(__name__)


async def content_generation_handler(
    job: Job,
    db: AsyncIOMotorDatabase,
    progress_callback: Callable[[JobProgress], Coroutine]
) -> Dict[str, Any]:
    """
    Execute content generation using the Multi-Agent System.
    
    Agents involved:
    1. Orchestrator - Plans workflow
    2. Research Agent - Gathers news/data
    3. Writer Agent - Creates draft
    4. Compliance Agent - Reviews compliance
    5. Cultural Agent - Reviews cultural sensitivity
    
    Args:
        job: Job containing input data
        db: Database connection
        progress_callback: Callback to report progress
        
    Returns:
        Generated content with quality scores and agent workflow details
    """
    input_data = job.input_data
    user_id = job.user_id
    
    # Extract parameters
    prompt = input_data.get("prompt", "")
    language = input_data.get("language", "en")
    profile_id = input_data.get("profile_id")
    platforms = input_data.get("platforms", [])
    tone = input_data.get("tone", "professional")
    hashtag_count = input_data.get("hashtag_count", 3)
    
    logger.info(f"[ContentGenTask] Starting multi-agent generation for job {job.job_id}")
    
    # Step 1: Initialize
    await progress_callback(JobProgress(
        current_step="Initializing multi-agent system",
        total_steps=6,
        current_step_num=1,
        percentage=5,
        message="Starting Orchestrator Agent..."
    ))
    
    # Create progress wrapper for the multi-agent service
    async def agent_progress_callback(progress: Dict):
        step = progress.get("step", "Processing")
        percentage = progress.get("percentage", 50)
        agents = progress.get("agents", [])
        
        await progress_callback(JobProgress(
            current_step=step,
            total_steps=6,
            current_step_num=2,
            percentage=percentage,
            message=f"Agents: {', '.join(agents)}" if agents else step
        ))
    
    # Step 2: Research Phase
    await progress_callback(JobProgress(
        current_step="Research Agent gathering news",
        total_steps=6,
        current_step_num=2,
        percentage=15,
        message="Detecting industry, searching for relevant news..."
    ))
    
    # Step 3-5: Multi-agent execution
    await progress_callback(JobProgress(
        current_step="Multi-agent workflow in progress",
        total_steps=6,
        current_step_num=3,
        percentage=30,
        message="Research → Writer → Compliance → Cultural..."
    ))
    
    # Execute multi-agent workflow
    service = MultiAgentContentService(db)
    result = await service.generate_content(
        user_id=user_id,
        prompt=prompt,
        language=language,
        tone=tone,
        platforms=platforms,
        hashtag_count=hashtag_count,
        profile_id=profile_id,
        progress_callback=agent_progress_callback
    )
    
    if not result.get("success"):
        raise Exception(result.get("error", "Multi-agent generation failed"))
    
    # Step 6: Finalize
    await progress_callback(JobProgress(
        current_step="Finalizing content",
        total_steps=6,
        current_step_num=6,
        percentage=95,
        message="Multi-agent workflow complete"
    ))
    
    # Format result for job response
    final_result = {
        "content": result.get("content"),
        "generated_content": result.get("content"),
        "prompt": prompt,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "job_id": job.job_id,
        "tone": tone,
        "platforms": platforms,
        "hashtag_count": hashtag_count,
        "language": language,
        
        # Multi-agent specific data
        "multi_agent": True,
        "workflow_summary": result.get("workflow_summary", {}),
        "research": result.get("research", {}),
        "quality_scores": result.get("quality_scores", {}),
        
        # News context for compatibility
        "news_context": {
            "used": len(result.get("research", {}).get("sources", [])) > 0,
            "industry": result.get("research", {}).get("industry", "general"),
            "articles": result.get("research", {}).get("sources", [])
        }
    }
    
    logger.info(
        f"[ContentGenTask] Job {job.job_id} complete: "
        f"cultural={result.get('quality_scores', {}).get('cultural_score', 0)}, "
        f"agents={result.get('workflow_summary', {}).get('agents_used', [])}"
    )
    
    return final_result
