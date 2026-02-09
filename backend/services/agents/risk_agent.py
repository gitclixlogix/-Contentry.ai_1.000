"""
Risk Assessment Agent

Specialized agent for aggregating findings from all analysis agents
and producing final risk scores, recommendations, and action items.

Capabilities:
- Multi-source risk aggregation
- Priority ranking of issues
- Contextual risk adjustment
- Actionable recommendations
- Policy-based decisions
"""

import logging
from typing import Dict, Any, List, Optional

from .base_agent import BaseAgent, AgentRole, AgentContext, Tool

logger = logging.getLogger(__name__)


class RiskAssessmentAgent(BaseAgent):
    """
    Risk Assessment Agent - Synthesizes analysis into actionable risk assessment.
    
    This agent:
    - Aggregates findings from Visual, Text, and Compliance agents
    - Weighs different risk factors
    - Considers context and policies
    - Produces final risk scores and recommendations
    - Determines required actions (approve/flag/reject)
    """
    
    # Risk thresholds for decisions
    THRESHOLDS = {
        "auto_approve": 30,    # Below this: safe to auto-approve
        "review_required": 60,  # Above this: requires human review
        "auto_reject": 85       # Above this: auto-reject recommended
    }
    
    def __init__(self, db=None):
        super().__init__(
            role=AgentRole.COMPLIANCE,
            name="Risk Assessment Agent",
            expertise="Aggregating multi-agent analysis into actionable risk assessments and recommendations",
            model="gpt-4.1-mini"
        )
        self.db = db
        self._register_tools()
    
    def _get_role_specific_prompt(self) -> str:
        return """
AS THE RISK ASSESSMENT AGENT, YOUR RESPONSIBILITIES ARE:

1. AGGREGATE FINDINGS:
   - Combine results from Visual, Text, and Compliance agents
   - Identify overlapping concerns
   - Note contradictions between agents
   - Weight findings by severity and confidence

2. CONTEXTUAL ANALYSIS:
   - Consider the content type and platform
   - Apply relevant policies
   - Account for industry-specific requirements
   - Consider cultural context

3. RISK SCORING:
   - Calculate weighted risk score (0-100)
   - Determine risk level (LOW/MEDIUM/HIGH/CRITICAL)
   - Identify primary risk drivers
   - Assess confidence in assessment

4. RECOMMENDATIONS:
   - Determine action: APPROVE / FLAG_FOR_REVIEW / REJECT
   - Prioritize issues to address
   - Provide specific remediation steps
   - Estimate impact of issues

5. DECISION SUPPORT:
   - Explain reasoning clearly
   - Highlight most critical findings
   - Suggest alternatives if content is rejected
   - Note any limitations in analysis

OUTPUT FORMAT: Return comprehensive JSON with final assessment.
"""
    
    def _register_tools(self):
        """Register risk assessment tools"""
        self.register_tool(Tool(
            name="calculate_weighted_risk",
            description="Calculate weighted risk score from multiple inputs",
            parameters={
                "type": "object",
                "properties": {
                    "visual_score": {"type": "number"},
                    "text_score": {"type": "number"},
                    "compliance_score": {"type": "number"}
                },
                "required": []
            },
            handler=self._calculate_weighted_risk
        ))
    
    async def _calculate_weighted_risk(
        self, 
        visual_score: float = 0, 
        text_score: float = 0, 
        compliance_score: float = 0
    ) -> Dict[str, Any]:
        """Calculate weighted risk score"""
        # Weights for different analysis types
        weights = {
            "visual": 0.40,    # Visual issues are often most impactful
            "text": 0.30,      # Text issues are important
            "compliance": 0.30 # Compliance is critical
        }
        
        # Handle missing scores
        scores = []
        total_weight = 0
        
        if visual_score > 0:
            scores.append(visual_score * weights["visual"])
            total_weight += weights["visual"]
        if text_score > 0:
            scores.append(text_score * weights["text"])
            total_weight += weights["text"]
        if compliance_score > 0:
            scores.append(compliance_score * weights["compliance"])
            total_weight += weights["compliance"]
        
        if total_weight > 0:
            weighted_score = sum(scores) / total_weight
        else:
            weighted_score = 0
        
        # Take maximum for critical issues (any critical = overall critical)
        max_score = max(visual_score, text_score, compliance_score)
        
        # Final score: weighted average, but bump up if any single score is critical
        final_score = weighted_score
        if max_score >= 80:
            final_score = max(final_score, max_score * 0.9)  # Don't let average hide critical issues
        
        return {
            "weighted_score": round(weighted_score, 1),
            "max_score": max_score,
            "final_score": round(final_score, 1),
            "components": {
                "visual": visual_score,
                "text": text_score,
                "compliance": compliance_score
            }
        }
    
    async def execute(self, context: 'AnalysisContext', task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute risk assessment by aggregating all agent findings.
        
        Args:
            context: Analysis context with all agent results
            task: Task parameters
        """
        visual_results = task.get("visual_analysis", {})
        text_results = task.get("text_analysis", {})
        compliance_results = task.get("compliance_analysis", {})
        policies = task.get("policies", [])
        content_type = task.get("content_type", "general")
        platform = task.get("platform", "unknown")
        
        logger.info(f"[RiskAgent] Starting risk assessment for {content_type} on {platform}")
        
        # Extract scores from each analysis
        visual_score = visual_results.get("aggregate", {}).get("average_risk_score", 0)
        text_score = text_results.get("summary", {}).get("risk_score", 0)
        compliance_score = 100 - compliance_results.get("score", 100)  # Convert compliance to risk
        
        # Calculate weighted risk
        risk_calculation = await self._calculate_weighted_risk(
            visual_score=visual_score,
            text_score=text_score,
            compliance_score=compliance_score
        )
        
        final_score = risk_calculation["final_score"]
        
        # Collect all issues
        all_issues = []
        
        # Visual issues
        if visual_results.get("aggregate", {}).get("unique_concerns"):
            for concern in visual_results["aggregate"]["unique_concerns"]:
                all_issues.append({
                    "source": "visual",
                    "issue": concern,
                    "severity": "high" if visual_score >= 60 else "medium"
                })
        
        # Text issues
        if text_results.get("analysis", {}).get("harmful_content", {}).get("specific_issues"):
            for issue in text_results["analysis"]["harmful_content"]["specific_issues"]:
                all_issues.append({
                    "source": "text",
                    "issue": issue,
                    "severity": "high" if text_score >= 60 else "medium"
                })
        
        # Compliance issues
        if compliance_results.get("issues"):
            for issue in compliance_results["issues"]:
                all_issues.append({
                    "source": "compliance",
                    "issue": issue.get("description", str(issue)),
                    "severity": issue.get("severity", "medium")
                })
        
        # Determine action
        if final_score >= self.THRESHOLDS["auto_reject"]:
            recommended_action = "REJECT"
            action_reason = "Content contains critical issues that violate policies"
        elif final_score >= self.THRESHOLDS["review_required"]:
            recommended_action = "FLAG_FOR_REVIEW"
            action_reason = "Content requires human review before approval"
        else:
            recommended_action = "APPROVE"
            action_reason = "Content passes automated checks"
        
        # Determine risk level
        if final_score >= 80:
            risk_level = "CRITICAL"
        elif final_score >= 60:
            risk_level = "HIGH"
        elif final_score >= 40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Build comprehensive assessment prompt
        assessment_prompt = f"""Synthesize this multi-agent content analysis into a final risk assessment:

CONTENT TYPE: {content_type}
PLATFORM: {platform}

VISUAL ANALYSIS RESULTS:
- Risk Score: {visual_score}
- Risk Level: {visual_results.get('aggregate', {}).get('overall_risk_level', 'N/A')}
- Concerns: {visual_results.get('aggregate', {}).get('unique_concerns', [])}

TEXT ANALYSIS RESULTS:
- Risk Score: {text_score}
- Risk Level: {text_results.get('summary', {}).get('risk_level', 'N/A')}
- Sentiment: {text_results.get('summary', {}).get('sentiment', 'N/A')}
- Issues: {text_results.get('analysis', {}).get('harmful_content', {}).get('specific_issues', [])}

COMPLIANCE ANALYSIS RESULTS:
- Compliant: {compliance_results.get('compliant', 'N/A')}
- Score: {compliance_results.get('score', 'N/A')}
- Issues: {[i.get('description', str(i)) for i in compliance_results.get('issues', [])]}

CALCULATED RISK:
- Final Score: {final_score}
- Preliminary Action: {recommended_action}

POLICIES TO CONSIDER:
{[p.get('filename', 'Policy') for p in policies] if policies else 'No specific policies'}

Provide final assessment with:
1. Executive summary (2-3 sentences)
2. Top 3 priority issues (ranked)
3. Specific recommendations
4. Confidence level in assessment

Return JSON:
{{
    "executive_summary": "...",
    "priority_issues": [
        {{"rank": 1, "issue": "...", "source": "visual/text/compliance", "impact": "high/medium/low", "remediation": "..."}}
    ],
    "detailed_findings": {{
        "visual": "summary of visual findings",
        "text": "summary of text findings",
        "compliance": "summary of compliance findings"
    }},
    "recommendations": ["recommendation1", "recommendation2"],
    "confidence": "high/medium/low",
    "confidence_reasoning": "...",
    "additional_context_needed": ["what else would help"],
    "false_positive_likelihood": "low/medium/high"
}}"""
        
        assessment_response = await self._call_llm(assessment_prompt)
        llm_assessment = self._parse_json_response(assessment_response)
        
        result = {
            "status": "success",
            "final_assessment": {
                "risk_score": final_score,
                "risk_level": risk_level,
                "recommended_action": recommended_action,
                "action_reason": action_reason,
                "confidence": llm_assessment.get("confidence", "medium")
            },
            "score_breakdown": risk_calculation,
            "all_issues": all_issues,
            "priority_issues": llm_assessment.get("priority_issues", []),
            "executive_summary": llm_assessment.get("executive_summary", ""),
            "detailed_findings": llm_assessment.get("detailed_findings", {}),
            "recommendations": llm_assessment.get("recommendations", []),
            "thresholds_used": self.THRESHOLDS,
            "metadata": {
                "content_type": content_type,
                "platform": platform,
                "agents_consulted": ["visual", "text", "compliance"],
                "policies_applied": len(policies)
            }
        }
        
        logger.info(
            f"[RiskAgent] Assessment complete: score={final_score}, "
            f"level={risk_level}, action={recommended_action}"
        )
        
        return result
