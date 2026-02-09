"""
Employment Law Compliance Agent Service

An agentic multi-model system that analyzes content for employment law violations
using multiple LLM models (gpt-4.1-mini, gpt-4.1-nano, gemini-2.5-flash) in an
ensemble approach.

This service detects subtle violations including:
- Age discrimination (ADEA)
- Gender bias and gendered language (Title VII)
- Disability discrimination (ADA)
- Benevolent sexism and unequal treatment
- Culture of exclusion / disparate impact
- Religious discrimination

The agent uses three models working together:
1. Classifier (gpt-4.1-nano): Quick classification of content type
2. Compliance Analyst (gpt-4.1-mini): Deep employment law analysis
3. Validator (gemini-2.5-flash): Cross-verification and final assessment
"""

import logging
import json
import os
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from services.token_tracking_utils import log_llm_call
from services.token_tracking_service import AgentType

logger = logging.getLogger(__name__)


class EmploymentLawAgent:
    """
    Agentic multi-model system for employment law compliance analysis.
    
    Uses ensemble of LLMs to detect subtle employment law violations that
    single models might miss due to their tendency to interpret language positively.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the agent with API key."""
        self.api_key = api_key or os.environ.get('EMERGENT_LLM_KEY')
        if not self.api_key:
            logger.warning("No API key provided for EmploymentLawAgent")
    
    async def analyze_content(
        self,
        content: str,
        company_policies: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze content for employment law violations using multi-model ensemble.
        
        Args:
            content: The content to analyze
            company_policies: Optional company policy context (Title IX, etc.)
            context: Optional additional context
            
        Returns:
            Dict containing analysis results with violations, severity, and recommendations
        """
        if not self.api_key:
            return self._empty_result("API key not configured")
        
        try:
            # Step 1: Classify content type with fast model
            classification = await self._classify_content(content)
            
            if not classification.get("is_workplace_content", False):
                return self._empty_result("Content is not workplace/employment related")
            
            # Step 2: Deep compliance analysis with primary model
            compliance_analysis = await self._analyze_compliance(
                content=content,
                content_type=classification.get("content_type", "unknown"),
                company_policies=company_policies
            )
            
            # Step 3: Cross-validate with secondary model if violations found
            if compliance_analysis.get("violations_detected", False):
                validated_analysis = await self._validate_analysis(
                    content=content,
                    initial_analysis=compliance_analysis,
                    company_policies=company_policies
                )
                return validated_analysis
            
            return compliance_analysis
            
        except Exception as e:
            logger.error(f"Employment law analysis error: {str(e)}")
            return self._empty_result(f"Analysis error: {str(e)}")
    
    async def _classify_content(self, content: str) -> Dict[str, Any]:
        """
        Quick classification of content type using gpt-4.1-nano.
        
        Determines if content is:
        - Hiring/recruitment related
        - Employee recognition/praise
        - Job requirements/descriptions
        - General workplace communication
        """
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        session_id = f"classify_{datetime.now(timezone.utc).timestamp()}"
        
        system_message = """You are an expert content classifier specializing in workplace and employment content.
        
Your task is to quickly classify content and determine if it requires employment law compliance analysis.

Respond ONLY with a JSON object, no other text."""
        
        prompt = f"""Classify this content:

CONTENT:
{content}

Respond with this exact JSON structure:
{{
  "is_workplace_content": true/false,
  "content_type": "hiring_post|employee_recognition|job_requirements|workplace_communication|other",
  "requires_compliance_check": true/false,
  "detected_topics": ["list", "of", "relevant", "topics"],
  "confidence": 0.0-1.0
}}

Content types that REQUIRE compliance check:
- Hiring posts, job listings, recruitment content
- Employee recognition, praise, awards
- Job requirements, qualifications
- Team culture descriptions
- Workplace policies"""

        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message=system_message
            ).with_model("openai", "gpt-4.1-nano")
            
            response = await chat.send_message(UserMessage(text=prompt))
            
            # Track token usage
            await log_llm_call(
                user_id="system",
                agent_type=AgentType.EMPLOYMENT_LAW,
                model="gpt-4.1-nano",
                provider="openai",
                input_text=prompt,
                output_text=response,
                credit_cost=0  # Part of content analysis
            )
            
            # Parse response
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            cleaned = cleaned.strip()
            
            result = json.loads(cleaned)
            logger.info(f"Content classified as: {result.get('content_type')}, requires_check: {result.get('requires_compliance_check')}")
            return result
            
        except Exception as e:
            logger.warning(f"Classification failed: {str(e)}, defaulting to require check")
            return {
                "is_workplace_content": True,
                "content_type": "unknown",
                "requires_compliance_check": True,
                "detected_topics": [],
                "confidence": 0.5
            }
    
    async def _analyze_compliance(
        self,
        content: str,
        content_type: str,
        company_policies: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deep employment law compliance analysis using gpt-4.1-mini.
        
        Analyzes for:
        - Age discrimination (ADEA)
        - Gender bias / gendered language (Title VII)
        - Disability discrimination (ADA)
        - Benevolent sexism
        - Culture of exclusion / disparate impact
        - Religious discrimination
        """
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        session_id = f"compliance_{datetime.now(timezone.utc).timestamp()}"
        
        system_message = """You are an expert Employment Law Compliance Analyst with deep knowledge of:
- Age Discrimination in Employment Act (ADEA)
- Title VII of the Civil Rights Act (gender, race, religion, national origin)
- Americans with Disabilities Act (ADA)
- Equal Employment Opportunity (EEO) regulations
- Hostile work environment laws
- Disparate impact theory

Your role is to identify SUBTLE violations that may not be obvious but could expose an organization to legal liability.

CRITICAL: You must look beyond surface positivity. Content can seem friendly while containing discriminatory language.

Examples of subtle violations:
1. "Recent grad" - Age discrimination (ADEA) - discourages 40+ applicants
2. "Brother-in-arms" - Gendered language making women feel excluded
3. "Happy hours and ski trips" - Culture of exclusion affecting parents, non-drinkers, disabled
4. "Sweetheart", "brightening up the office" - Benevolent sexism focusing on personality over skills
5. "Handle high-stress" - ADA concern, screening out mental health conditions
6. "Must have own car" - Disparate impact on disabled who cannot drive

Respond ONLY with a JSON object."""

        policy_context = ""
        if company_policies:
            policy_context = f"""
COMPANY POLICIES (violations against these are SEVERE):
{company_policies[:3000]}
"""

        prompt = f"""Analyze this {content_type} content for employment law compliance violations:

CONTENT:
{content}
{policy_context}

ANALYZE FOR THESE VIOLATION CATEGORIES:

1. **AGE DISCRIMINATION (ADEA)**
   - Language implying preference for younger workers
   - Terms like "recent grad", "digital native", "Gen Z", "young and energetic"
   - Requirements that indirectly exclude older workers

2. **GENDERED LANGUAGE (Title VII)**
   - Masculine-coded terms: "brother-in-arms", "ninja", "rockstar", "manpower"
   - Benevolent sexism: praising women for demeanor over skills ("sweetheart", "brightening the office")
   - Different standards applied to men vs women

3. **DISABILITY DISCRIMINATION (ADA)**
   - "Handle high-stress" - may screen out anxiety/mental health conditions
   - Physical requirements not essential to job function
   - "Must have own car" instead of "reliable transportation"
   - Language discouraging accommodation requests

4. **CULTURE OF EXCLUSION / DISPARATE IMPACT**
   - Alcohol-centric activities: "happy hours", "Friday beers", "wine tastings"
   - Mandatory social activities excluding parents/caregivers: "ski trips", "weekend retreats"
   - "Work hard, play hard" culture signaling
   - "Work family" rhetoric creating inappropriate expectations

5. **RELIGIOUS DISCRIMINATION**
   - Activities conflicting with religious practices
   - Work schedule requirements affecting religious observance

Provide your analysis as JSON:
{{
  "violations_detected": true/false,
  "severity": "critical|severe|high|moderate|low|none",
  "compliance_score": 0-100 (100 = fully compliant, 0 = severe violations),
  "overall_rating": "excellent|good|needs_improvement|poor|critical",
  "violations": [
    {{
      "type": "age_discrimination|gendered_language|disability_discrimination|culture_exclusion|benevolent_sexism|religious_discrimination",
      "severity": "critical|severe|high|moderate",
      "law_reference": "ADEA|Title VII|ADA|EEOC Guidelines",
      "problematic_text": "exact text that is problematic",
      "explanation": "detailed explanation of why this is a violation",
      "legal_risk": "description of potential legal consequences",
      "recommendation": "specific suggestion for compliant alternative"
    }}
  ],
  "summary": "Overall summary of compliance issues found",
  "rewrite_suggestions": ["list of specific rewrites for problematic phrases"],
  "positive_elements": ["any compliant/positive aspects of the content"]
}}

IMPORTANT:
- Be thorough - subtle violations are often the most damaging legally
- Explain WHY each item is a violation, not just that it is one
- Provide actionable recommendations
- Consider the cumulative effect of multiple minor issues"""

        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message=system_message
            ).with_model("openai", "gpt-4.1-mini")
            
            response = await chat.send_message(UserMessage(text=prompt))
            
            # Track token usage
            await log_llm_call(
                user_id="system",
                agent_type=AgentType.EMPLOYMENT_LAW,
                model="gpt-4.1-mini",
                provider="openai",
                input_text=prompt,
                output_text=response,
                credit_cost=0  # Part of content analysis
            )
            
            # Parse response
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            cleaned = cleaned.strip()
            
            result = json.loads(cleaned)
            
            # Ensure required fields
            result.setdefault("violations_detected", len(result.get("violations", [])) > 0)
            result.setdefault("severity", "none")
            result.setdefault("compliance_score", 100)
            result.setdefault("overall_rating", "good")
            result.setdefault("violations", [])
            result.setdefault("summary", "No violations detected.")
            result.setdefault("rewrite_suggestions", [])
            result.setdefault("positive_elements", [])
            result["model_used"] = "gpt-4.1-mini"
            result["analysis_type"] = "primary_compliance"
            
            logger.info(f"Compliance analysis: violations_detected={result['violations_detected']}, score={result['compliance_score']}")
            return result
            
        except Exception as e:
            logger.error(f"Compliance analysis failed: {str(e)}")
            return self._empty_result(f"Analysis failed: {str(e)}")
    
    async def _validate_analysis(
        self,
        content: str,
        initial_analysis: Dict[str, Any],
        company_policies: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cross-validate and potentially refine analysis using gemini-2.5-flash.
        
        This provides a second opinion and may catch additional issues or
        refine severity assessments.
        """
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        session_id = f"validate_{datetime.now(timezone.utc).timestamp()}"
        
        system_message = """You are an independent Employment Law Compliance Validator.

Your role is to review an initial compliance analysis and:
1. Validate or challenge each violation identified
2. Check for any violations that may have been missed
3. Refine severity assessments based on legal precedent
4. Provide final compliance score

Be critical and thorough. Your validation is the final check before content goes live.

Respond ONLY with a JSON object."""

        initial_violations = json.dumps(initial_analysis.get("violations", []), indent=2)
        
        policy_context = ""
        if company_policies:
            policy_context = f"""
COMPANY POLICIES TO ENFORCE:
{company_policies[:2000]}
"""

        prompt = f"""Review and validate this employment law compliance analysis:

ORIGINAL CONTENT:
{content}
{policy_context}

INITIAL ANALYSIS FINDINGS:
{initial_violations}

Initial Compliance Score: {initial_analysis.get('compliance_score', 'N/A')}
Initial Severity: {initial_analysis.get('severity', 'N/A')}

YOUR TASK:
1. Validate each violation - is it correctly identified? Is severity accurate?
2. Check for MISSED violations - did the initial analysis overlook anything?
3. Consider cumulative impact of multiple violations
4. Provide your final assessment

Provide your validation as JSON:
{{
  "validation_status": "confirmed|modified|challenged",
  "violations_detected": true/false,
  "severity": "critical|severe|high|moderate|low|none",
  "compliance_score": 0-100,
  "overall_rating": "excellent|good|needs_improvement|poor|critical",
  "validated_violations": [
    {{
      "type": "violation type",
      "severity": "severity level",
      "law_reference": "relevant law",
      "problematic_text": "exact problematic text",
      "explanation": "explanation of violation",
      "legal_risk": "potential legal consequences",
      "recommendation": "suggested fix",
      "validation_note": "why you confirmed/modified/added this violation"
    }}
  ],
  "missed_violations": [
    {{
      "type": "violation type missed by initial analysis",
      "severity": "severity level",
      "law_reference": "relevant law",
      "problematic_text": "exact text",
      "explanation": "why this is a violation",
      "recommendation": "suggested fix"
    }}
  ],
  "summary": "Final validation summary",
  "rewrite_suggestions": ["final recommended rewrites"],
  "validation_confidence": 0.0-1.0
}}"""

        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message=system_message
            ).with_model("openai", "gpt-4.1-nano")
            
            response = await chat.send_message(UserMessage(text=prompt))
            
            # Track token usage
            await log_llm_call(
                user_id="system",
                agent_type=AgentType.EMPLOYMENT_LAW,
                model="gpt-4.1-nano",
                provider="openai",
                input_text=prompt,
                output_text=response,
                credit_cost=0  # Part of content analysis
            )
            
            # Parse response
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            cleaned = cleaned.strip()
            
            result = json.loads(cleaned)
            
            # Merge validated violations with missed violations
            all_violations = result.get("validated_violations", []) + result.get("missed_violations", [])
            
            # Build final result
            final_result = {
                "violations_detected": len(all_violations) > 0,
                "severity": result.get("severity", initial_analysis.get("severity", "none")),
                "compliance_score": result.get("compliance_score", initial_analysis.get("compliance_score", 100)),
                "overall_rating": result.get("overall_rating", initial_analysis.get("overall_rating", "good")),
                "violations": all_violations,
                "summary": result.get("summary", initial_analysis.get("summary", "")),
                "rewrite_suggestions": result.get("rewrite_suggestions", initial_analysis.get("rewrite_suggestions", [])),
                "positive_elements": initial_analysis.get("positive_elements", []),
                "validation_status": result.get("validation_status", "confirmed"),
                "validation_confidence": result.get("validation_confidence", 0.8),
                "models_used": ["gpt-4.1-mini", "gpt-4.1-nano"],
                "analysis_type": "validated_ensemble"
            }
            
            logger.info(f"Validation complete: status={final_result['validation_status']}, final_score={final_result['compliance_score']}")
            return final_result
            
        except Exception as e:
            logger.warning(f"Validation failed: {str(e)}, returning initial analysis")
            initial_analysis["validation_status"] = "validation_failed"
            initial_analysis["validation_error"] = str(e)
            return initial_analysis
    
    def _empty_result(self, reason: str) -> Dict[str, Any]:
        """Return empty result when analysis cannot be performed."""
        return {
            "violations_detected": False,
            "severity": "none",
            "compliance_score": 100,
            "overall_rating": "good",
            "violations": [],
            "summary": reason,
            "rewrite_suggestions": [],
            "positive_elements": [],
            "analysis_type": "skipped",
            "skip_reason": reason
        }


# Singleton instance
_agent_instance: Optional[EmploymentLawAgent] = None


def get_employment_law_agent() -> EmploymentLawAgent:
    """Get or create the singleton Employment Law Agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = EmploymentLawAgent()
    return _agent_instance


async def analyze_employment_compliance(
    content: str,
    company_policies: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to analyze content for employment law compliance.
    
    Args:
        content: Content to analyze
        company_policies: Optional company policy context
        context: Optional additional context
        
    Returns:
        Analysis results
    """
    agent = get_employment_law_agent()
    return await agent.analyze_content(content, company_policies, context)
