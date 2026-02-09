"""
Compliance Agent

Specialized agent for checking content against policies, brand guidelines,
and legal requirements.

Checks:
- Brand voice alignment
- Policy compliance
- Legal considerations (employment law, disclaimers)
- Prohibited content detection
"""

import logging
from typing import Dict, Any, List, Optional

from .base_agent import BaseAgent, AgentRole, AgentContext, Tool

logger = logging.getLogger(__name__)


class ComplianceAgent(BaseAgent):
    """
    Compliance Agent - Ensures content meets all requirements.
    
    This agent autonomously:
    - Reviews content against policies
    - Flags potential legal issues
    - Checks brand voice alignment
    - Suggests corrections when needed
    """
    
    def __init__(self, db=None):
        super().__init__(
            role=AgentRole.COMPLIANCE,
            name="Compliance Agent",
            expertise="Reviewing content for policy compliance, legal requirements, and brand alignment",
            model="gpt-4.1-mini"
        )
        self.db = db
        self._register_tools()
    
    def _get_role_specific_prompt(self) -> str:
        return """
AS THE COMPLIANCE AGENT, YOUR RESPONSIBILITIES ARE:

1. LEGAL COMPLIANCE:
   - Employment law: No age discrimination (avoid "young", "energetic", "digital native")
   - Gender neutrality: Use inclusive language
   - Disclaimers: Flag content needing legal disclaimers
   - Defamation: No unsubstantiated claims about companies/individuals

2. BRAND COMPLIANCE:
   - Voice consistency with brand guidelines
   - Terminology usage (preferred terms)
   - Tone appropriateness

3. CONTENT POLICY:
   - No hate speech or discrimination
   - No misleading claims
   - Proper attribution of sources
   - Privacy considerations

4. INDUSTRY-SPECIFIC:
   - Financial: Investment disclaimers
   - Healthcare: Medical advice disclaimers
   - Legal: Not legal advice disclaimers

OUTPUT FORMAT:
Return JSON with:
{
    "compliant": true/false,
    "score": 0-100,
    "issues": [{"type": "...", "severity": "high/medium/low", "description": "...", "suggestion": "..."}],
    "passed_checks": ["check1", "check2"],
    "recommendations": ["suggestion1", "suggestion2"]
}
"""
    
    def _register_tools(self):
        """Register compliance tools"""
        self.register_tool(Tool(
            name="check_prohibited_terms",
            description="Check for prohibited or problematic terms",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to check"}
                },
                "required": ["text"]
            },
            handler=self._check_prohibited_terms
        ))
    
    async def _check_prohibited_terms(self, text: str) -> Dict[str, Any]:
        """Check for prohibited or problematic terms"""
        text_lower = text.lower()
        
        issues = []
        
        # Age-related terms (employment law)
        age_terms = ["young professional", "digital native", "recent graduate", "energetic", "fresh talent", "youthful"]
        for term in age_terms:
            if term in text_lower:
                issues.append({
                    "type": "age_discrimination",
                    "term": term,
                    "severity": "high",
                    "suggestion": f"Remove '{term}' - potential age discrimination"
                })
        
        # Gender-specific terms
        gender_terms = {"manpower": "workforce", "chairman": "chairperson", "mankind": "humanity", "man-made": "artificial"}
        for term, replacement in gender_terms.items():
            if term in text_lower:
                issues.append({
                    "type": "gender_bias",
                    "term": term,
                    "severity": "medium",
                    "suggestion": f"Replace '{term}' with '{replacement}'"
                })
        
        # Unsubstantiated claims
        claim_indicators = ["guaranteed", "proven to", "will definitely", "100%", "always works"]
        for indicator in claim_indicators:
            if indicator in text_lower:
                issues.append({
                    "type": "unsubstantiated_claim",
                    "term": indicator,
                    "severity": "medium",
                    "suggestion": f"Soften claim '{indicator}' - use 'may', 'can', 'designed to'"
                })
        
        return {
            "issues_found": len(issues),
            "issues": issues,
            "clean": len(issues) == 0
        }
    
    async def execute(self, context: AgentContext, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute compliance review.
        
        The agent will:
        1. Run automated term checks
        2. Review against policies
        3. Check legal requirements
        4. Provide detailed feedback
        """
        content = context.draft_content
        policies = context.policies
        industry = context.research_data.get("industry", {}).get("detected", "general")
        
        logger.info(f"[ComplianceAgent] Starting compliance review for {industry} content")
        
        # Step 1: Automated term checking
        term_check = await self._check_prohibited_terms(content)
        
        # Step 2: Build policy context
        policy_context = ""
        if policies:
            policy_items = [f"- {p.get('filename', 'Policy')}: {p.get('summary', 'Follow guidelines')}" for p in policies[:5]]
            policy_context = f"\nBRAND POLICIES:\n{chr(10).join(policy_items)}"
        
        # Step 3: LLM-based comprehensive review
        review_prompt = f"""Review this content for compliance issues:

CONTENT TO REVIEW:
{content}

INDUSTRY: {industry}
{policy_context}

AUTOMATED CHECKS FOUND:
{term_check['issues'] if term_check['issues'] else 'No issues found'}

Perform a comprehensive compliance review checking:
1. Employment law compliance (age, gender, disability language)
2. Brand voice alignment
3. Legal disclaimer requirements (especially for {industry})
4. Factual accuracy of claims
5. Source attribution
6. Inclusive language

Return JSON:
{{
    "compliant": true/false (false if any high-severity issues),
    "score": 0-100,
    "issues": [
        {{"type": "category", "severity": "high/medium/low", "description": "what's wrong", "location": "quote from text", "suggestion": "how to fix"}}
    ],
    "passed_checks": ["list of passed compliance areas"],
    "recommendations": ["optional improvements"],
    "needs_disclaimer": true/false,
    "disclaimer_text": "suggested disclaimer if needed"
}}"""
        
        review_response = await self._call_llm(review_prompt)
        review = self._parse_json_response(review_response)
        
        # Merge automated and LLM findings
        all_issues = term_check.get('issues', []) + review.get('issues', [])
        
        # Calculate final compliance status
        high_severity_issues = [i for i in all_issues if i.get('severity') == 'high']
        is_compliant = len(high_severity_issues) == 0
        
        result = {
            "status": "success",
            "compliant": is_compliant,
            "score": review.get('score', 100 - len(all_issues) * 10),
            "issues": all_issues,
            "passed_checks": review.get('passed_checks', []),
            "recommendations": review.get('recommendations', []),
            "needs_disclaimer": review.get('needs_disclaimer', False),
            "disclaimer_text": review.get('disclaimer_text', ''),
            "review_summary": {
                "total_issues": len(all_issues),
                "high_severity": len(high_severity_issues),
                "medium_severity": len([i for i in all_issues if i.get('severity') == 'medium']),
                "low_severity": len([i for i in all_issues if i.get('severity') == 'low'])
            }
        }
        
        logger.info(f"[ComplianceAgent] Review complete: compliant={is_compliant}, issues={len(all_issues)}")
        
        return result
