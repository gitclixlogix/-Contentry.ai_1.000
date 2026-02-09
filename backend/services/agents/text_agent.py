"""
Text Analysis Agent

Specialized agent for analyzing text content including captions,
comments, transcripts, and text overlays.

Capabilities:
- Sentiment analysis
- Tone detection
- Claim verification
- Harmful language detection
- Context understanding
"""

import logging
from typing import Dict, Any, List, Optional

from .base_agent import BaseAgent, AgentRole, AgentContext, Tool

logger = logging.getLogger(__name__)


class TextAnalysisAgent(BaseAgent):
    """
    Text Analysis Agent - Analyzes text content.
    
    This agent autonomously:
    - Analyzes sentiment and emotional tone
    - Detects potentially harmful language
    - Identifies claims that need verification
    - Checks for compliance issues in text
    - Extracts key themes and topics
    """
    
    def __init__(self):
        super().__init__(
            role=AgentRole.WRITER,  # Using WRITER role for text expertise
            name="Text Analysis Agent",
            expertise="Analyzing text for sentiment, tone, claims, and compliance issues",
            model="gpt-4.1-mini"
        )
        self._register_tools()
    
    def _get_role_specific_prompt(self) -> str:
        return """
AS THE TEXT ANALYSIS AGENT, YOUR RESPONSIBILITIES ARE:

1. SENTIMENT ANALYSIS:
   - Determine overall sentiment (positive/negative/neutral)
   - Identify emotional undertones
   - Detect sarcasm or irony
   - Note intensity of sentiment

2. TONE DETECTION:
   - Professional vs casual
   - Aggressive vs passive
   - Authoritative vs tentative
   - Inclusive vs exclusive

3. CLAIM ANALYSIS:
   - Identify factual claims made
   - Flag unsubstantiated claims
   - Note misleading statements
   - Detect exaggerations

4. HARMFUL LANGUAGE DETECTION:
   - Hate speech or discrimination
   - Harassment or bullying
   - Misinformation
   - Inappropriate content
   - Profanity or offensive language

5. COMPLIANCE CHECKING:
   - Employment law violations (age, gender bias)
   - Misleading advertising claims
   - Required disclaimers missing
   - Privacy violations

OUTPUT FORMAT: Return structured JSON with analysis.
"""
    
    def _register_tools(self):
        """Register text analysis tools"""
        self.register_tool(Tool(
            name="detect_harmful_terms",
            description="Detect harmful or problematic terms in text",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to analyze"}
                },
                "required": ["text"]
            },
            handler=self._detect_harmful_terms
        ))
    
    async def _detect_harmful_terms(self, text: str) -> Dict[str, Any]:
        """Detect harmful terms using pattern matching"""
        text_lower = text.lower()
        
        findings = []
        
        # Discriminatory language
        discriminatory_patterns = {
            "age": ["old people", "young people", "millennials are", "boomers are", "too old", "too young"],
            "gender": ["like a girl", "man up", "boys will be", "women always", "men always"],
            "race": ["those people", "you people", "they all"],
        }
        
        for category, patterns in discriminatory_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    findings.append({
                        "type": "discriminatory",
                        "category": category,
                        "pattern": pattern,
                        "severity": "high"
                    })
        
        # Aggressive language
        aggressive_terms = ["idiot", "stupid", "moron", "loser", "pathetic", "disgusting"]
        for term in aggressive_terms:
            if term in text_lower:
                findings.append({
                    "type": "aggressive",
                    "term": term,
                    "severity": "medium"
                })
        
        # Misleading claims
        misleading_indicators = ["guaranteed", "100%", "proven", "scientifically proven", "doctors agree", "everyone knows"]
        for indicator in misleading_indicators:
            if indicator in text_lower:
                findings.append({
                    "type": "potentially_misleading",
                    "indicator": indicator,
                    "severity": "medium"
                })
        
        return {
            "findings": findings,
            "total_issues": len(findings),
            "has_harmful_content": len(findings) > 0
        }
    
    async def execute(self, context: 'AnalysisContext', task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute text analysis.
        
        Args:
            context: Analysis context
            task: Task parameters with text to analyze
        """
        text = task.get("text", "")
        text_type = task.get("text_type", "general")  # caption, transcript, comment, etc.
        
        if not text:
            return {
                "status": "skipped",
                "reason": "No text provided",
                "risk_score": 0
            }
        
        logger.info(f"[TextAgent] Starting analysis: {len(text)} chars, type={text_type}")
        
        # Step 1: Automated term detection
        term_check = await self._detect_harmful_terms(text)
        
        # Step 2: Comprehensive LLM analysis
        analysis_prompt = f"""Analyze this {text_type} text for content moderation:

TEXT TO ANALYZE:
"{text}"

AUTOMATED FINDINGS:
{term_check['findings'] if term_check['findings'] else 'No automated issues found'}

Perform comprehensive analysis:

1. SENTIMENT:
   - Overall sentiment (positive/negative/neutral/mixed)
   - Sentiment score (-100 to +100)
   - Emotional undertones

2. TONE:
   - Primary tone (professional/casual/aggressive/friendly/etc.)
   - Appropriateness for business context

3. CLAIMS:
   - List any factual claims made
   - Flag claims that need verification
   - Note any misleading statements

4. HARMFUL CONTENT:
   - Discrimination or bias
   - Harassment or bullying
   - Misinformation
   - Inappropriate content

5. RISK ASSESSMENT:
   - Overall risk score (0-100)
   - Risk level (LOW/MEDIUM/HIGH/CRITICAL)

Return JSON:
{{
    "sentiment": {{
        "overall": "positive/negative/neutral/mixed",
        "score": -100 to +100,
        "emotions": ["emotion1", "emotion2"]
    }},
    "tone": {{
        "primary": "...",
        "secondary": "...",
        "appropriate_for_business": true/false
    }},
    "claims": {{
        "factual_claims": ["claim1", "claim2"],
        "unverified_claims": ["claim"],
        "misleading_statements": ["statement"]
    }},
    "harmful_content": {{
        "detected": true/false,
        "categories": ["category1"],
        "specific_issues": ["issue1"]
    }},
    "topics": ["topic1", "topic2"],
    "risk_score": 0-100,
    "risk_level": "LOW/MEDIUM/HIGH/CRITICAL",
    "recommendations": ["recommendation1"]
}}"""
        
        analysis_response = await self._call_llm(analysis_prompt)
        analysis = self._parse_json_response(analysis_response)
        
        # Merge automated and LLM findings
        if term_check['findings']:
            if 'harmful_content' not in analysis:
                analysis['harmful_content'] = {}
            analysis['harmful_content']['automated_findings'] = term_check['findings']
        
        # Ensure risk score exists
        if 'risk_score' not in analysis:
            # Calculate based on findings
            base_score = 0
            if term_check['has_harmful_content']:
                base_score += 30
            if analysis.get('harmful_content', {}).get('detected'):
                base_score += 30
            if analysis.get('claims', {}).get('misleading_statements'):
                base_score += 20
            analysis['risk_score'] = min(base_score, 100)
            analysis['risk_level'] = (
                "CRITICAL" if base_score >= 80 else
                "HIGH" if base_score >= 60 else
                "MEDIUM" if base_score >= 40 else
                "LOW"
            )
        
        result = {
            "status": "success",
            "text_type": text_type,
            "text_length": len(text),
            "analysis": analysis,
            "automated_check": term_check,
            "summary": {
                "sentiment": analysis.get("sentiment", {}).get("overall", "unknown"),
                "tone": analysis.get("tone", {}).get("primary", "unknown"),
                "risk_score": analysis.get("risk_score", 0),
                "risk_level": analysis.get("risk_level", "UNKNOWN"),
                "issues_found": term_check['total_issues'] + len(analysis.get('harmful_content', {}).get('specific_issues', []))
            }
        }
        
        logger.info(f"[TextAgent] Analysis complete: risk={result['summary']['risk_level']}, score={result['summary']['risk_score']}")
        
        return result
