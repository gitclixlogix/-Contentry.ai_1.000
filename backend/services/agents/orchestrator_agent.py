"""
Orchestrator Agent

The central coordinator for the multi-agent content generation system.
Plans workflows, delegates tasks, and synthesizes results from all agents.

Workflow:
1. Analyze request → Plan approach
2. Delegate to Research Agent → Get news/data
3. Delegate to Writer Agent → Get draft
4. Delegate to Compliance Agent → Get compliance review
5. Delegate to Cultural Agent → Get cultural review
6. If issues found → Request revisions
7. Synthesize final output
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .base_agent import BaseAgent, AgentRole, AgentContext, AgentMessage
from .research_agent import ResearchAgent
from .writer_agent import WriterAgent
from .compliance_agent import ComplianceAgent
from .cultural_agent import CulturalAgent

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent - Coordinates the multi-agent workflow.
    
    This agent:
    - Plans the overall approach
    - Delegates to specialized agents
    - Handles revisions and feedback loops
    - Synthesizes final output
    """
    
    MAX_REVISION_CYCLES = 2
    
    def __init__(self, db=None):
        super().__init__(
            role=AgentRole.ORCHESTRATOR,
            name="Orchestrator Agent",
            expertise="Planning and coordinating multi-agent workflows for content generation",
            model="gpt-4.1-mini"
        )
        self.db = db
        
        # Initialize specialized agents
        self.research_agent = ResearchAgent(db=db)
        self.writer_agent = WriterAgent()
        self.compliance_agent = ComplianceAgent(db=db)
        self.cultural_agent = CulturalAgent()
        
        self._register_tools()
    
    def _get_role_specific_prompt(self) -> str:
        return """
AS THE ORCHESTRATOR AGENT, YOUR RESPONSIBILITIES ARE:

1. PLANNING:
   - Analyze user requests
   - Determine which agents are needed
   - Plan the workflow sequence

2. DELEGATION:
   - Assign clear tasks to specialized agents
   - Provide necessary context
   - Set success criteria

3. QUALITY CONTROL:
   - Review agent outputs
   - Decide if revisions are needed
   - Manage revision cycles (max 2)

4. SYNTHESIS:
   - Combine agent outputs
   - Resolve conflicts between agent recommendations
   - Produce final deliverable

WORKFLOW:
1. Research → Writer → Compliance → Cultural → (Revise if needed) → Final

DECISION CRITERIA FOR REVISIONS:
- Cultural score < 90: Request revision from Writer with Cultural feedback
- Compliance score < 90: Request revision with Compliance feedback
- Accuracy issues: Request revision to preserve facts correctly
- Missing requirements: Request specific additions

QUALITY THRESHOLDS (ALL MUST BE MET):
- Compliance: >= 90
- Cultural: >= 90
- Accuracy: 100%
"""
    
    def _register_tools(self):
        """Register orchestration tools"""
        pass  # Orchestrator primarily uses agent delegation
    
    async def _plan_workflow(self, context: AgentContext) -> Dict[str, Any]:
        """Plan the workflow based on the request"""
        prompt = context.original_prompt
        
        planning_prompt = f"""Analyze this content request and plan the workflow:

REQUEST: {prompt}
LANGUAGE: {context.language}
TONE: {context.tone}
PLATFORMS: {context.platforms}
HASHTAGS REQUIRED: {context.hashtag_count}

Create a workflow plan:
1. What information does Research Agent need to find?
2. What should Writer Agent focus on?
3. What compliance concerns should be checked?
4. What cultural considerations are important?

Return JSON:
{{
    "request_analysis": {{
        "main_topic": "...",
        "requires_news": true/false,
        "industry_hint": "detected industry or 'general'",
        "key_requirements": ["req1", "req2"]
    }},
    "agent_tasks": {{
        "research": "specific research instructions",
        "writer": "specific writing instructions",
        "compliance": "specific compliance focus areas",
        "cultural": "specific cultural considerations"
    }},
    "success_criteria": {{
        "must_have": ["requirement1", "requirement2"],
        "nice_to_have": ["optional1"]
    }}
}}"""
        
        response = await self._call_llm(planning_prompt)
        return self._parse_json_response(response)
    
    async def _request_revision(
        self, 
        context: AgentContext, 
        feedback: Dict[str, Any],
        revision_type: str
    ) -> str:
        """Request a revision from the Writer Agent"""
        current_draft = context.draft_content
        
        revision_prompt = f"""The current draft needs revision based on {revision_type} feedback.

CURRENT DRAFT:
{current_draft}

FEEDBACK TO ADDRESS:
{feedback}

ORIGINAL REQUEST: {context.original_prompt}

Create a revised version that addresses ALL feedback while maintaining:
- The news references and sources
- The required {context.hashtag_count} hashtags at the end
- The {context.tone} tone
- Source citations

Return ONLY the revised content (no explanations):"""
        
        revised = await self._call_llm(revision_prompt)
        return revised.strip()
    
    async def execute(self, context: AgentContext, task: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the full multi-agent workflow.
        
        Steps:
        1. Plan workflow
        2. Research Agent: Gather information
        3. Writer Agent: Create draft
        4. Compliance Agent: Review compliance
        5. Cultural Agent: Review cultural sensitivity
        6. Revise if needed (up to MAX_REVISION_CYCLES)
        7. Return final result
        """
        start_time = datetime.now(timezone.utc)
        workflow_log = []
        
        logger.info(f"[Orchestrator] Starting multi-agent workflow")
        workflow_log.append({"step": "start", "timestamp": start_time.isoformat()})
        
        # === STEP 1: Plan Workflow ===
        logger.info("[Orchestrator] Step 1: Planning workflow")
        plan = await self._plan_workflow(context)
        workflow_log.append({"step": "planning", "result": "complete", "plan": plan})
        
        # === STEP 2: Research Agent ===
        logger.info("[Orchestrator] Step 2: Delegating to Research Agent")
        research_result = await self.research_agent.execute(
            context=context,
            task={"instructions": plan.get("agent_tasks", {}).get("research", "")}
        )
        context.research_data = research_result
        workflow_log.append({
            "step": "research",
            "agent": "ResearchAgent",
            "articles_found": len(research_result.get("news_articles", [])),
            "industry": research_result.get("industry", {}).get("detected", "general")
        })
        
        # === STEP 3: Writer Agent ===
        logger.info("[Orchestrator] Step 3: Delegating to Writer Agent")
        writer_result = await self.writer_agent.execute(
            context=context,
            task={"instructions": plan.get("agent_tasks", {}).get("writer", "")}
        )
        context.draft_content = writer_result.get("draft", "")
        workflow_log.append({
            "step": "writing",
            "agent": "WriterAgent",
            "char_count": writer_result.get("metadata", {}).get("char_count", 0),
            "has_hashtags": writer_result.get("metadata", {}).get("has_hashtags", False)
        })
        
        # === REVISION LOOP ===
        revision_cycle = 0
        final_content = context.draft_content
        
        while revision_cycle < self.MAX_REVISION_CYCLES:
            revision_cycle += 1
            needs_revision = False
            revision_feedback = {}
            
            # === STEP 4: Compliance Agent ===
            logger.info(f"[Orchestrator] Step 4 (cycle {revision_cycle}): Delegating to Compliance Agent")
            compliance_result = await self.compliance_agent.execute(
                context=context,
                task={"instructions": plan.get("agent_tasks", {}).get("compliance", "")}
            )
            context.compliance_feedback = compliance_result
            workflow_log.append({
                "step": f"compliance_cycle_{revision_cycle}",
                "agent": "ComplianceAgent",
                "compliant": compliance_result.get("compliant", False),
                "score": compliance_result.get("score", 0),
                "issues": compliance_result.get("review_summary", {}).get("total_issues", 0)
            })
            
            # Check for high-severity compliance issues
            high_severity = [i for i in compliance_result.get("issues", []) if i.get("severity") == "high"]
            if high_severity:
                needs_revision = True
                revision_feedback["compliance"] = high_severity
            
            # === STEP 5: Cultural Agent ===
            logger.info(f"[Orchestrator] Step 5 (cycle {revision_cycle}): Delegating to Cultural Agent")
            cultural_result = await self.cultural_agent.execute(
                context=context,
                task={"instructions": plan.get("agent_tasks", {}).get("cultural", "")}
            )
            context.cultural_feedback = cultural_result
            workflow_log.append({
                "step": f"cultural_cycle_{revision_cycle}",
                "agent": "CulturalAgent",
                "passes_threshold": cultural_result.get("passes_threshold", False),
                "score": cultural_result.get("overall_score", 0),
                "issues": cultural_result.get("analysis_summary", {}).get("total_issues", 0)
            })
            
            # Check cultural score
            if not cultural_result.get("passes_threshold", False):
                needs_revision = True
                revision_feedback["cultural"] = {
                    "score": cultural_result.get("overall_score", 0),
                    "critical_fixes": cultural_result.get("critical_fixes", []),
                    "issues": cultural_result.get("issues", [])[:3]  # Top 3 issues
                }
            
            # === REVISION IF NEEDED ===
            if needs_revision and revision_cycle < self.MAX_REVISION_CYCLES:
                logger.info(f"[Orchestrator] Requesting revision (cycle {revision_cycle})")
                revised_content = await self._request_revision(
                    context=context,
                    feedback=revision_feedback,
                    revision_type="compliance and cultural"
                )
                context.draft_content = revised_content
                final_content = revised_content
                workflow_log.append({
                    "step": f"revision_cycle_{revision_cycle}",
                    "feedback_addressed": list(revision_feedback.keys())
                })
            else:
                final_content = context.draft_content
                break
        
        # === FINAL SYNTHESIS ===
        end_time = datetime.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Determine final status
        final_cultural_score = context.cultural_feedback.get("overall_score", 0)
        final_compliance_score = context.compliance_feedback.get("score", 0)
        is_compliant = context.compliance_feedback.get("compliant", False)
        passes_cultural = context.cultural_feedback.get("passes_threshold", False)
        
        result = {
            "status": "success",
            "content": final_content,
            "prompt": context.original_prompt,
            "workflow": {
                "revision_cycles": revision_cycle,
                "agents_involved": ["Orchestrator", "Research", "Writer", "Compliance", "Cultural"],
                "duration_ms": round(duration_ms, 2),
                "log": workflow_log
            },
            "research": {
                "industry": context.research_data.get("industry", {}).get("detected", "general"),
                "articles_used": len(context.research_data.get("news_articles", [])),
                "sources": [
                    {"title": a["title"], "source": a["source"], "url": a["url"]}
                    for a in context.research_data.get("news_articles", [])[:3]
                ]
            },
            "quality": {
                "compliance": {
                    "score": final_compliance_score,
                    "compliant": is_compliant,
                    "issues_remaining": len(context.compliance_feedback.get("issues", []))
                },
                "cultural": {
                    "score": final_cultural_score,
                    "passes_threshold": passes_cultural,
                    "dimensions": context.cultural_feedback.get("dimensions", {})
                }
            },
            "metadata": {
                "tone": context.tone,
                "language": context.language,
                "platforms": context.platforms,
                "hashtag_count": context.hashtag_count
            }
        }
        
        logger.info(
            f"[Orchestrator] Workflow complete: "
            f"cultural={final_cultural_score}, compliance={final_compliance_score}, "
            f"cycles={revision_cycle}, duration={duration_ms:.0f}ms"
        )
        
        return result
