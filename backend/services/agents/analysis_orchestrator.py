"""
Analysis Orchestrator Agent

The central coordinator for the multi-agent content analysis system.
Plans analysis workflows, delegates to specialized agents, and synthesizes results.

Workflow:
1. Analyze content type → Plan approach
2. Delegate to Visual Agent (if media present)
3. Delegate to Text Agent (if text present)
4. Delegate to Compliance Agent → Policy check
5. Delegate to Risk Assessment Agent → Final assessment
6. Synthesize and return results
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field

from .base_agent import BaseAgent, AgentRole, AgentMessage
from .visual_agent import VisualAnalysisAgent
from .text_agent import TextAnalysisAgent
from .compliance_agent import ComplianceAgent
from .risk_agent import RiskAssessmentAgent

logger = logging.getLogger(__name__)


@dataclass
class AnalysisContext:
    """Shared context for analysis agents"""
    user_id: str
    content_type: str  # "image", "video", "text", "mixed"
    platform: str = "general"
    
    # Input content
    media_url: str = ""
    media_frames: List[Dict] = field(default_factory=list)
    text_content: str = ""
    caption: str = ""
    transcript: str = ""
    
    # User context
    profile_data: Dict[str, Any] = field(default_factory=dict)
    policies: List[Dict] = field(default_factory=list)
    
    # Agent results
    visual_results: Dict[str, Any] = field(default_factory=dict)
    text_results: Dict[str, Any] = field(default_factory=dict)
    compliance_results: Dict[str, Any] = field(default_factory=dict)
    risk_results: Dict[str, Any] = field(default_factory=dict)


class AnalysisOrchestratorAgent(BaseAgent):
    """
    Analysis Orchestrator Agent - Coordinates multi-agent analysis workflow.
    
    This agent:
    - Determines which agents are needed based on content type
    - Coordinates parallel and sequential analysis tasks
    - Manages data flow between agents
    - Synthesizes final analysis results
    """
    
    def __init__(self, db=None):
        super().__init__(
            role=AgentRole.ORCHESTRATOR,
            name="Analysis Orchestrator",
            expertise="Coordinating multi-agent content analysis workflows",
            model="gpt-4.1-mini"
        )
        self.db = db
        
        # Initialize specialized agents
        self.visual_agent = VisualAnalysisAgent(db=db)
        self.text_agent = TextAnalysisAgent()
        self.compliance_agent = ComplianceAgent(db=db)
        self.risk_agent = RiskAssessmentAgent(db=db)
    
    def _get_role_specific_prompt(self) -> str:
        return """
AS THE ANALYSIS ORCHESTRATOR, YOUR RESPONSIBILITIES ARE:

1. CONTENT ASSESSMENT:
   - Determine content type (image, video, text, mixed)
   - Identify which agents are needed
   - Plan optimal analysis workflow

2. AGENT COORDINATION:
   - Delegate to Visual Agent for images/video
   - Delegate to Text Agent for captions/transcripts
   - Delegate to Compliance Agent for policy checks
   - Delegate to Risk Agent for final assessment

3. WORKFLOW MANAGEMENT:
   - Run independent analyses in parallel where possible
   - Ensure proper data flow between agents
   - Handle agent failures gracefully

4. RESULT SYNTHESIS:
   - Combine all agent outputs
   - Resolve any conflicts
   - Produce unified analysis report

ANALYSIS WORKFLOW:
Content → [Visual + Text (parallel)] → Compliance → Risk Assessment → Final Report
"""
    
    async def _plan_analysis(self, context: AnalysisContext) -> Dict[str, Any]:
        """Plan the analysis workflow based on content"""
        needs_visual = bool(context.media_url or context.media_frames)
        needs_text = bool(context.text_content or context.caption or context.transcript)
        
        return {
            "content_type": context.content_type,
            "agents_required": {
                "visual": needs_visual,
                "text": needs_text,
                "compliance": True,  # Always run compliance
                "risk": True  # Always run risk assessment
            },
            "workflow": [
                "visual_analysis" if needs_visual else None,
                "text_analysis" if needs_text else None,
                "compliance_check",
                "risk_assessment"
            ],
            "parallel_tasks": ["visual_analysis", "text_analysis"] if needs_visual and needs_text else []
        }
    
    async def execute(self, context: AnalysisContext, task: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the full multi-agent analysis workflow.
        
        Steps:
        1. Plan analysis based on content type
        2. Visual Agent: Analyze media (if present)
        3. Text Agent: Analyze text (if present)
        4. Compliance Agent: Check policies
        5. Risk Agent: Aggregate and assess
        6. Return comprehensive report
        """
        start_time = datetime.now(timezone.utc)
        workflow_log = []
        
        logger.info(f"[AnalysisOrchestrator] Starting analysis for {context.content_type}")
        workflow_log.append({"step": "start", "timestamp": start_time.isoformat()})
        
        # === STEP 1: Plan Analysis ===
        plan = await self._plan_analysis(context)
        workflow_log.append({"step": "planning", "plan": plan})
        logger.info(f"[AnalysisOrchestrator] Plan: {plan['agents_required']}")
        
        # === STEP 2: Visual Analysis (if needed) ===
        if plan["agents_required"]["visual"]:
            logger.info("[AnalysisOrchestrator] Running Visual Agent")
            try:
                visual_result = await self.visual_agent.execute(
                    context=context,
                    task={
                        "frames": context.media_frames,
                        "media_url": context.media_url,
                        "media_type": context.content_type
                    }
                )
                context.visual_results = visual_result
                workflow_log.append({
                    "step": "visual_analysis",
                    "agent": "VisualAnalysisAgent",
                    "status": "success",
                    "risk_score": visual_result.get("aggregate", {}).get("average_risk_score", 0)
                })
            except Exception as e:
                logger.error(f"[AnalysisOrchestrator] Visual analysis failed: {e}")
                context.visual_results = {"status": "error", "error": str(e)}
                workflow_log.append({
                    "step": "visual_analysis",
                    "status": "error",
                    "error": str(e)
                })
        
        # === STEP 3: Text Analysis (if needed) ===
        if plan["agents_required"]["text"]:
            logger.info("[AnalysisOrchestrator] Running Text Agent")
            
            # Combine all text sources
            combined_text = " ".join(filter(None, [
                context.text_content,
                context.caption,
                context.transcript
            ]))
            
            try:
                text_result = await self.text_agent.execute(
                    context=context,
                    task={
                        "text": combined_text,
                        "text_type": "mixed" if context.transcript else "caption"
                    }
                )
                context.text_results = text_result
                workflow_log.append({
                    "step": "text_analysis",
                    "agent": "TextAnalysisAgent",
                    "status": "success",
                    "risk_score": text_result.get("summary", {}).get("risk_score", 0)
                })
            except Exception as e:
                logger.error(f"[AnalysisOrchestrator] Text analysis failed: {e}")
                context.text_results = {"status": "error", "error": str(e)}
                workflow_log.append({
                    "step": "text_analysis",
                    "status": "error",
                    "error": str(e)
                })
        
        # === STEP 4: Compliance Check ===
        logger.info("[AnalysisOrchestrator] Running Compliance Agent")
        
        # Create a minimal context for compliance agent
        from .base_agent import AgentContext as BaseContext
        compliance_context = BaseContext(
            user_id=context.user_id,
            original_prompt="",
            policies=context.policies
        )
        # Set draft content for compliance check
        compliance_context.draft_content = context.text_content or context.caption or ""
        compliance_context.research_data = {"industry": {"detected": "general"}}
        
        try:
            compliance_result = await self.compliance_agent.execute(
                context=compliance_context,
                task={"content_type": context.content_type}
            )
            context.compliance_results = compliance_result
            workflow_log.append({
                "step": "compliance_check",
                "agent": "ComplianceAgent",
                "status": "success",
                "compliant": compliance_result.get("compliant", False),
                "score": compliance_result.get("score", 0)
            })
        except Exception as e:
            logger.error(f"[AnalysisOrchestrator] Compliance check failed: {e}")
            context.compliance_results = {"status": "error", "error": str(e), "compliant": False, "score": 0}
            workflow_log.append({
                "step": "compliance_check",
                "status": "error",
                "error": str(e)
            })
        
        # === STEP 5: Risk Assessment ===
        logger.info("[AnalysisOrchestrator] Running Risk Assessment Agent")
        try:
            risk_result = await self.risk_agent.execute(
                context=context,
                task={
                    "visual_analysis": context.visual_results,
                    "text_analysis": context.text_results,
                    "compliance_analysis": context.compliance_results,
                    "policies": context.policies,
                    "content_type": context.content_type,
                    "platform": context.platform
                }
            )
            context.risk_results = risk_result
            workflow_log.append({
                "step": "risk_assessment",
                "agent": "RiskAssessmentAgent",
                "status": "success",
                "final_score": risk_result.get("final_assessment", {}).get("risk_score", 0),
                "action": risk_result.get("final_assessment", {}).get("recommended_action", "UNKNOWN")
            })
        except Exception as e:
            logger.error(f"[AnalysisOrchestrator] Risk assessment failed: {e}")
            context.risk_results = {"status": "error", "error": str(e)}
            workflow_log.append({
                "step": "risk_assessment",
                "status": "error",
                "error": str(e)
            })
        
        # === STEP 6: Synthesize Results ===
        end_time = datetime.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Get final assessment
        final_assessment = context.risk_results.get("final_assessment", {})
        
        result = {
            "status": "success",
            "content_type": context.content_type,
            "platform": context.platform,
            
            # Final assessment from Risk Agent
            "final_assessment": {
                "risk_score": final_assessment.get("risk_score", 0),
                "risk_level": final_assessment.get("risk_level", "UNKNOWN"),
                "recommended_action": final_assessment.get("recommended_action", "FLAG_FOR_REVIEW"),
                "action_reason": final_assessment.get("action_reason", "Analysis incomplete"),
                "confidence": final_assessment.get("confidence", "low")
            },
            
            # Executive summary
            "executive_summary": context.risk_results.get("executive_summary", ""),
            
            # Priority issues
            "priority_issues": context.risk_results.get("priority_issues", []),
            
            # Detailed results from each agent
            "agent_results": {
                "visual": {
                    "analyzed": plan["agents_required"]["visual"],
                    "risk_score": context.visual_results.get("aggregate", {}).get("average_risk_score", 0),
                    "risk_level": context.visual_results.get("aggregate", {}).get("overall_risk_level", "N/A"),
                    "frames_analyzed": context.visual_results.get("frames_analyzed", 0),
                    "concerns": context.visual_results.get("aggregate", {}).get("unique_concerns", [])
                },
                "text": {
                    "analyzed": plan["agents_required"]["text"],
                    "risk_score": context.text_results.get("summary", {}).get("risk_score", 0),
                    "risk_level": context.text_results.get("summary", {}).get("risk_level", "N/A"),
                    "sentiment": context.text_results.get("summary", {}).get("sentiment", "N/A"),
                    "issues": context.text_results.get("analysis", {}).get("harmful_content", {}).get("specific_issues", [])
                },
                "compliance": {
                    "analyzed": True,
                    "compliant": context.compliance_results.get("compliant", False),
                    "score": context.compliance_results.get("score", 0),
                    "issues": len(context.compliance_results.get("issues", []))
                }
            },
            
            # Recommendations
            "recommendations": context.risk_results.get("recommendations", []),
            
            # Workflow metadata
            "workflow": {
                "agents_used": [
                    "AnalysisOrchestrator",
                    "VisualAnalysisAgent" if plan["agents_required"]["visual"] else None,
                    "TextAnalysisAgent" if plan["agents_required"]["text"] else None,
                    "ComplianceAgent",
                    "RiskAssessmentAgent"
                ],
                "duration_ms": round(duration_ms, 2),
                "log": workflow_log
            },
            
            # Multi-agent flag
            "multi_agent": True,
            "analysis_method": "multi_agent_v1"
        }
        
        # Remove None values from agents list
        result["workflow"]["agents_used"] = [a for a in result["workflow"]["agents_used"] if a]
        
        logger.info(
            f"[AnalysisOrchestrator] Analysis complete: "
            f"score={final_assessment.get('risk_score', 0)}, "
            f"action={final_assessment.get('recommended_action', 'UNKNOWN')}, "
            f"duration={duration_ms:.0f}ms"
        )
        
        return result
